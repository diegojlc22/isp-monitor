import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog
from backend.app.services.mikrotik_api import get_mikrotik_live_traffic
from backend.app.services.snmp import get_snmp_interface_traffic
from backend.app.services.wireless_snmp import get_wireless_stats, get_health_stats, get_connected_clients_count
from backend.app.services.notifier import send_notification
from loguru import logger

# Config
SNMP_INTERVAL = 10 # Check SNMP every 10s (Balanced for CPU/Responsiveness)

# ✅ SPRINT 3: Smart Logging - Tracking de estado
# Armazena último valor salvo para evitar logs duplicados
snmp_last_logged = {}  # eq_id -> {"in": mbps, "out": mbps, "signal": dbm, "ccq": %, "time": timestamp}

async def snmp_monitor_job():
    """
    Dedicated job for Traffic polling (SNMP + Mikrotik API) AND Wireless Stats.
    Parallelized for high performance (Semaphore limited).
    """
    import time
    logger.info("[TRAFFIC] Traffic/Wireless Monitor started (Interval: 10s)...")
    
    # Limit Concurrency to avoid network flood and CPU spikes
    sem = asyncio.Semaphore(25) # Reduced from 100 to 25 
    
    # Cache for bandwidth calculation (SNMP only): eq_id -> (timestamp, in_bytes, out_bytes)
    previous_counters = {} 
    
    async def fetch_device_data(eq_data):
        """
        Independent task to fetch data for one device.
        Returns a dict of updates to be applied to DB, or None.
        eq_data is a dictionary copy of the object to avoid detached instance issues.
        """
        async with sem:
            result = {"id": eq_data["id"], "updates": {}, "log": None}
            
            try:
                ip = eq_data["ip"]
                brand = eq_data.get("brand")
                community = eq_data.get("snmp_community")
                port = eq_data.get("snmp_port") or 161
                
                # --- WIRELESS / FIBER STATS ---
                if brand in ['ubiquiti', 'intelbras', 'mikrotik', 'mimosa']:
                    try:
                        w_stats = await get_wireless_stats(
                            ip, brand, community, port, 
                            interface_index=eq_data.get("snmp_interface_index"),
                            equipment_type=eq_data.get("equipment_type")
                        )
                        if w_stats['signal_dbm'] is not None:
                            result["updates"]["signal_dbm"] = w_stats['signal_dbm']
                            result["updates"]["ccq"] = w_stats['ccq']
                        
                        if eq_data.get("equipment_type") == 'transmitter': 
                            clients = await get_connected_clients_count(ip, brand, community, port)
                            if clients is not None:
                                 result["updates"]["connected_clients"] = clients
                        
                        # --- HEALTH STATS (CPU, Temp, Voltage) ---
                        if brand in ['mikrotik', 'ubiquiti', 'intelbras']:
                            try:
                                h_stats = await get_health_stats(ip, brand, community, port)
                                if h_stats['cpu_usage'] is not None:
                                    result["updates"]["cpu_usage"] = h_stats['cpu_usage']
                                if h_stats.get('memory_usage') is not None:
                                    result["updates"]["memory_usage"] = h_stats['memory_usage']
                                if h_stats.get('disk_usage') is not None:
                                    result["updates"]["disk_usage"] = h_stats['disk_usage']
                                if h_stats['temperature'] is not None:
                                    result["updates"]["temperature"] = h_stats['temperature']
                                if h_stats['voltage'] is not None:
                                    result["updates"]["voltage"] = h_stats['voltage']
                            except Exception as e:
                                pass
                    except Exception as e:
                        # Falha silenciosa para wireless não travar tráfego
                        pass

                # --- TRAFFIC ---
                # A) Mikrotik API
                if eq_data.get("is_mikrotik") and eq_data.get("mikrotik_interface"):
                    traffic_data = await get_mikrotik_live_traffic(
                        ip=ip,
                        user=eq_data.get("ssh_user"),
                        password=eq_data.get("ssh_password"),
                        interface=eq_data.get("mikrotik_interface"),
                        port=eq_data.get("api_port") or 8728
                    )
                    if traffic_data:
                        in_mbps, out_mbps = traffic_data
                        result["updates"]["last_traffic_in"] = in_mbps
                        result["updates"]["last_traffic_out"] = out_mbps
                        result["log"] = (in_mbps, out_mbps)
                        return result # Done for this device
                
                # B) SNMP
                interface_idx = eq_data.get("snmp_traffic_interface_index") or eq_data.get("snmp_interface_index") or 1
                traffic = await get_snmp_interface_traffic(ip, community, port, interface_idx, brand=brand)
                
                if traffic:
                    in_bytes, out_bytes = traffic
                    current_time_ts = time.time()
                    
                    # Cache Key: (Equipment ID, Interface Index)
                    # This allows monitoring multiple interfaces for the same equipment if needed in future,
                    # and prevents conflicts if user changes the interface index.
                    cache_key = (eq_data["id"], interface_idx)

                    if cache_key in previous_counters:
                        last_time, last_in, last_out = previous_counters[cache_key]
                        dt = current_time_ts - last_time
                        
                        if dt > 0:
                            delta_in = max(0, in_bytes - last_in)
                            delta_out = max(0, out_bytes - last_out)
                            
                            # Mbps
                            mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                            mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                            
                            result["updates"]["last_traffic_in"] = mbps_in
                            result["updates"]["last_traffic_out"] = mbps_out
                            result["log"] = (mbps_in, mbps_out, interface_idx)
                    
                    # Store for next run (in memory side-effect, safe here as single threaded event loop)
                    previous_counters[cache_key] = (current_time_ts, in_bytes, out_bytes)

                return result

            except Exception as e:
                import logging
                logging.warning(f"[SNMP] Error fetching {eq_data['ip']}: {e}")
                return None

    while True:
        try:
            # 1. Fetch Candidates and Notif Config
            equipments_data = [] # List of dicts
            async with AsyncSessionLocal() as session:
                from backend.app.models import Parameters
                # Notification Config
                params_res = await session.execute(
                    select(Parameters).where(Parameters.key.in_([
                        'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                        'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group',
                        'telegram_template_traffic'
                    ]))
                )
                notif_config = {p.key: p.value for p in params_res.scalars().all()}

                # Equipments with Tower names
                res = await session.execute(
                    select(Equipment, models.Tower.name.label("tower_name"))
                    .outerjoin(models.Tower, Equipment.tower_id == models.Tower.id)
                    .where(Equipment.is_online == True)
                )
                rows = res.all()
                for row in rows:
                    eq = row.Equipment
                    tower_name = row.tower_name or "Desconhecida"
                    if not eq.ip: continue
                    # Copy data to dict to avoid session detach issues during async gather
                    equipments_data.append({
                        "id": eq.id, "name": eq.name, "ip": eq.ip, "brand": eq.brand, 
                        "snmp_community": eq.snmp_community, "snmp_port": eq.snmp_port,
                        "ssh_user": eq.ssh_user, "ssh_password": eq.ssh_password,
                        "is_mikrotik": eq.is_mikrotik, "mikrotik_interface": eq.mikrotik_interface,
                        "api_port": eq.api_port, 
                        "snmp_interface_index": eq.snmp_interface_index,
                        "snmp_traffic_interface_index": eq.snmp_traffic_interface_index,
                        "equipment_type": eq.equipment_type,
                        "max_traffic_in": eq.max_traffic_in,
                        "max_traffic_out": eq.max_traffic_out,
                        "traffic_alert_interval": eq.traffic_alert_interval,
                        "last_traffic_alert_sent": eq.last_traffic_alert_sent,
                        "min_voltage_threshold": eq.min_voltage_threshold,
                        "voltage_alert_interval": eq.voltage_alert_interval,
                        "last_voltage_alert_sent": eq.last_voltage_alert_sent,
                        "tower_name": tower_name
                    })
            
            
            if not equipments_data:
                await asyncio.sleep(5)
                continue
            
            logger.info(f"[SNMP] 🔄 Processando {len(equipments_data)} equipamentos online...")

            # 2. Run Parallel Fetching (With 15s timeout per device)
            async def fetch_with_timeout(eq_dict):
                try:
                    return await asyncio.wait_for(fetch_device_data(eq_dict), timeout=15.0)
                except asyncio.TimeoutError:
                    import logging
                    logging.warning(f"[SNMP] Timeout polling {eq_dict['ip']} (exceeded 15s)")
                    return None
                except Exception as e:
                    import logging
                    logging.error(f"[SNMP] Crash polling {eq_dict['ip']}: {e}")
                    return None

            tasks = [fetch_with_timeout(eq) for eq in equipments_data]
            
            # 🔥 WORKAROUND: Timeout global para evitar travamento
            try:
                results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=300.0)  # 5 min max
                logger.info(f"[SNMP] ✅ Processamento concluído: {len([r for r in results if r])} sucessos de {len(equipments_data)}")
            except asyncio.TimeoutError:
                logger.error(f"[SNMP] ⏰ TIMEOUT GLOBAL! Processamento de {len(equipments_data)} equipamentos excedeu 5 minutos. Reiniciando loop...")
                await asyncio.sleep(10)
                continue
            except Exception as e:
                logger.error(f"[SNMP] 💥 ERRO CRÍTICO no gather: {e}")
                import traceback
                logger.error(traceback.format_exc())
                await asyncio.sleep(10)
                continue
            
            # 3. Batch Update DB (Optimized)
            from sqlalchemy import update, insert
            
            async with AsyncSessionLocal() as session:
                updates_buffer = []      # List of dicts for Table Equipment
                traffic_logs_buffer = [] # List of dicts for Table TrafficLog
                
                updates_count = 0
                
                for res in results:
                    if not res or not res["updates"]: continue
                    
                    # Prepare Equipment Update
                    upd_data = res["updates"]
                    
                    # Sanitize Signal fields to prevent DataError ('' instead of None/Float)
                    if "signal_dbm" in upd_data:
                        val = upd_data["signal_dbm"]
                        if val == '' or val is None:
                            upd_data["signal_dbm"] = None
                        else:
                            try:
                                upd_data["signal_dbm"] = float(val)
                            except:
                                upd_data["signal_dbm"] = None

                    if "ccq" in upd_data:
                        val = upd_data["ccq"]
                        if val == '' or val is None:
                            upd_data["ccq"] = None
                        else:
                            try:
                                upd_data["ccq"] = int(val)
                            except:
                                upd_data["ccq"] = None

                    upd_data["id"] = res["id"] # PK for bind
                    updates_buffer.append(upd_data)
                    
                    # ✅ SPRINT 3: Smart Logging para Traffic (Memory based, no DB read needed)
                    if res["log"]:
                        # Unpack log tuple (was 2, now 3 items)
                        if len(res["log"]) == 3:
                            in_mbps, out_mbps, if_idx = res["log"]
                        else:
                            in_mbps, out_mbps = res["log"]
                            if_idx = 1 # Fallback for Mikrotik API or old format

                        eq_id = res["id"]
                        current_time = time.time()
                        
                        should_log_traffic = False
                        
                        # Verificar se deve logar (Lógica puramente em memória)
                        if eq_id not in snmp_last_logged:
                            should_log_traffic = True
                        else:
                            last_log = snmp_last_logged[eq_id]
                            time_since_last = current_time - last_log.get("time", 0)
                            
                            # 1. Periodo de 10 min
                            if time_since_last > 600:
                                should_log_traffic = True
                            # 2. Variação > 10%
                            elif last_log.get("in") is not None:
                                in_variation = abs(in_mbps - last_log["in"]) / max(last_log["in"], 0.1)
                                out_variation = abs(out_mbps - last_log["out"]) / max(last_log["out"], 0.1)
                                if in_variation > 0.1 or out_variation > 0.1:
                                    should_log_traffic = True
                         
                        if should_log_traffic:
                            traffic_logs_buffer.append({
                                "equipment_id": eq_id,
                                "in_mbps": in_mbps,
                                "out_mbps": out_mbps,
                                "interface_index": if_idx,
                                "signal_dbm": res["updates"].get("signal_dbm"),
                                "cpu_usage": res["updates"].get("cpu_usage"),
                                "memory_usage": res["updates"].get("memory_usage"),
                                "disk_usage": res["updates"].get("disk_usage"),
                                "temperature": res["updates"].get("temperature"),
                                "voltage": res["updates"].get("voltage"),
                                "timestamp": datetime.now()  # Sem timezone para compatibilidade
                            })
                            # Atualizar tracking
                            snmp_last_logged[eq_id] = {
                                "in": in_mbps,
                                "out": out_mbps,
                                "time": current_time,
                                "signal": res["updates"].get("signal_dbm")
                            }


                        # ✅ ALERTAS DE TRÁFEGO
                        # Find equipment data from original list
                        eq_data = next((e for e in equipments_data if e["id"] == eq_id), None)
                        if not eq_data:
                            continue
                            
                        max_in = eq_data.get("max_traffic_in")
                        max_out = eq_data.get("max_traffic_out")
                        
                        if (max_in or max_out):
                            is_over = False
                            alert_lines = []
                            
                            if max_in and in_mbps > max_in:
                                is_over = True
                                alert_lines.append(f"⬇️ Download: *{in_mbps}* Mbps (Limite: {max_in} Mbps)")
                            if max_out and out_mbps > max_out:
                                is_over = True
                                alert_lines.append(f"⬆️ Upload: *{out_mbps}* Mbps (Limite: {max_out} Mbps)")
                                
                            if is_over:
                                # Cooldown check (Dynamic per equipment, default 6h)
                                last_alert = eq_data.get("last_traffic_alert_sent")
                                interval_min = eq_data.get("traffic_alert_interval") or 360
                                can_send = False
                                
                                if not last_alert:
                                    can_send = True
                                else:
                                    # Ensure last_alert is naive for comparison with datetime.now()
                                    if last_alert.tzinfo:
                                        last_alert = last_alert.replace(tzinfo=None)
                                    
                                    if (datetime.now() - last_alert).total_seconds() > (interval_min * 60):
                                        can_send = True
                                
                                if can_send:
                                    template = notif_config.get('telegram_template_traffic')
                                    if template:
                                        alert_msg = template.replace("[Device.Name]", eq_data['name']).replace("[Device.IP]", eq_data['ip']).replace("[Alert.Lines]", "\n".join(alert_lines))
                                    else:
                                        alert_msg = f"🚨 *TRÁFEGO INTENSO DETECTADO*\n\n📟 *{eq_data['name']}*\n🌐 IP: {eq_data['ip']}\n\n" + "\n".join(alert_lines) + "\n\n🔔 Verifique a carga do link."
                                    
                                    # Enviar notificação (background task para não travar loop)
                                    asyncio.create_task(send_notification(
                                        message=alert_msg,
                                        telegram_token=notif_config.get('telegram_token'),
                                        telegram_chat_id=notif_config.get('telegram_chat_id'),
                                        telegram_enabled=notif_config.get('telegram_enabled', 'true').lower() == 'true',
                                        whatsapp_enabled=notif_config.get('whatsapp_enabled', 'false').lower() == 'true',
                                        whatsapp_target=notif_config.get('whatsapp_target'),
                                        whatsapp_target_group=notif_config.get('whatsapp_target_group')
                                    ))
                                    
                                    # Atualizar no DB via buffer
                                    upd_data["last_traffic_alert_sent"] = datetime.now()

                        # ✅ ALERTAS DE VOLTAGEM
                        cv = res["updates"].get("voltage")
                        threshold = eq_data.get("min_voltage_threshold")
                        
                        if cv is not None and threshold is not None and cv <= threshold:
                            # Cooldown check
                            last_alert_v = eq_data.get("last_voltage_alert_sent")
                            interval_v = eq_data.get("voltage_alert_interval") or 360
                            can_send_v = False
                            
                            if not last_alert_v:
                                can_send_v = True
                            else:
                                if last_alert_v.tzinfo:
                                    last_alert_v = last_alert_v.replace(tzinfo=None)
                                if (datetime.now() - last_alert_v).total_seconds() > (interval_v * 60):
                                    can_send_v = True
                                    
                            if can_send_v:
                                now_str = datetime.now().strftime("%H:%M do dia %d/%m/%Y")
                                alert_msg = f"🪫 *ALERTA DE BAIXA VOLTAGEM*\n\n📍 *{eq_data['tower_name']}*\n📟 Rádio: {eq_data['name']}\n🌐 IP: {eq_data['ip']}\n\n⚠️ Voltagem Atual: *{cv}V*\n🛑 Limite Crítico: {threshold}V\n\n🕒 Horário: {now_str}\n\n🔔 *Ação Preventiva Necessária!*"
                                
                                asyncio.create_task(send_notification(
                                    message=alert_msg,
                                    telegram_token=notif_config.get('telegram_token'),
                                    telegram_chat_id=notif_config.get('telegram_chat_id'),
                                    telegram_enabled=notif_config.get('telegram_enabled', 'true').lower() == 'true',
                                    whatsapp_enabled=notif_config.get('whatsapp_enabled', 'false').lower() == 'true',
                                    whatsapp_target=notif_config.get('whatsapp_target'),
                                    whatsapp_target_group=notif_config.get('whatsapp_target_group')
                                ))
                                
                                # Atualizar no DB via buffer
                                upd_data["last_voltage_alert_sent"] = datetime.now()
                
                # Execute Batch Operations
                if updates_buffer:
                    await session.execute(update(Equipment), updates_buffer)
                    updates_count = len(updates_buffer)
                    
                if traffic_logs_buffer:
                    await session.execute(insert(TrafficLog), traffic_logs_buffer)
                
                # --- UPDATE HEARTBEAT FOR HEALTH CHECK ---
                from sqlalchemy import text
                await session.execute(text("""
                    INSERT INTO parameters (key, value) 
                    VALUES ('snmp_monitor_last_run', :now) 
                    ON CONFLICT (key) DO UPDATE SET value = :now
                """), {"now": datetime.now().isoformat()})

                await session.commit()
                if updates_count > 0:
                    logger.info(f"[SNMP] Updated {updates_count} devices and inserted {len(traffic_logs_buffer)} logs.")

            if updates_count > 0 or traffic_logs_buffer:
                # Basic GC for memory cache (Run every 10 cycles roughly, or just here)
                active_ids = {eq["id"] for eq in equipments_data}
                keys_to_remove = [k for k in snmp_last_logged.keys() if k not in active_ids]
                for k in keys_to_remove:
                    del snmp_last_logged[k]

        except Exception as e:
            import logging
            logging.error(f"[SNMP] Batch update error: {e}")
        
        # Read interval from database (with fallback)
        try:
            async with AsyncSessionLocal() as session:
                from backend.app.models import Parameters
                res = await session.execute(select(Parameters).where(Parameters.key == "snmp_interval"))
                param = res.scalar_one_or_none()
                interval = int(param.value) if param else SNMP_INTERVAL
        except:
            interval = SNMP_INTERVAL
        
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(snmp_monitor_job())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Global SNMP Error: {e}")

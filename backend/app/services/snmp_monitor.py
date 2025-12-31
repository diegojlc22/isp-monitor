import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog
from backend.app.services.mikrotik_api import get_mikrotik_live_traffic
from backend.app.services.snmp import get_snmp_interface_traffic
from backend.app.services.wireless_snmp import get_wireless_stats

# Config
SNMP_INTERVAL = 60 # Check SNMP every 60s

# ✅ SPRINT 3: Smart Logging - Tracking de estado
# Armazena último valor salvo para evitar logs duplicados
snmp_last_logged = {}  # eq_id -> {"in": mbps, "out": mbps, "signal": dbm, "ccq": %, "time": timestamp}

async def snmp_monitor_job():
    """
    Dedicated job for Traffic polling (SNMP + Mikrotik API) AND Wireless Stats.
    Parallelized for high performance (Semaphore limited).
    """
    import time
    print("[INFO] Traffic/Wireless Monitor started (Interval: 60s)...")
    
    # Limit Concurrency to avoid network flood
    sem = asyncio.Semaphore(100) 
    
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
                            from backend.app.services.wireless_snmp import get_connected_clients_count
                            clients = await get_connected_clients_count(ip, brand, community, port)
                            if clients is not None:
                                 result["updates"]["connected_clients"] = clients
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
                traffic = await get_snmp_interface_traffic(ip, community, port, interface_idx)
                
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
                # print(f"Error fetching {eq_data['ip']}: {e}")
                return None

    while True:
        try:
            # 1. Fetch Candidates from DB
            equipments_data = [] # List of dicts
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Equipment).where(Equipment.is_online == True))
                equipments = res.scalars().all()
                for eq in equipments:
                    if not eq.ip: continue
                    # Copy data to dict to avoid session detach issues during async gather
                    equipments_data.append({
                        "id": eq.id, "ip": eq.ip, "brand": eq.brand, 
                        "snmp_community": eq.snmp_community, "snmp_port": eq.snmp_port,
                        "ssh_user": eq.ssh_user, "ssh_password": eq.ssh_password,
                        "is_mikrotik": eq.is_mikrotik, "mikrotik_interface": eq.mikrotik_interface,
                        "api_port": eq.api_port, 
                        "snmp_interface_index": eq.snmp_interface_index,
                        "snmp_traffic_interface_index": eq.snmp_traffic_interface_index,
                        "equipment_type": eq.equipment_type
                    })
            
            if not equipments_data:
                await asyncio.sleep(5)
                continue

            # 2. Run Parallel Fetching
            tasks = [fetch_device_data(eq) for eq in equipments_data]
            results = await asyncio.gather(*tasks)
            
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
                                "timestamp": datetime.now(timezone.utc)
                            })
                            # Atualizar tracking
                            snmp_last_logged[eq_id] = {
                                "in": in_mbps,
                                "out": out_mbps,
                                "time": current_time
                            }
                
                # Execute Batch Operations
                if updates_buffer:
                    await session.execute(update(Equipment), updates_buffer)
                    updates_count = len(updates_buffer)
                    
                if traffic_logs_buffer:
                    await session.execute(insert(TrafficLog), traffic_logs_buffer)
                
                await session.commit()
                # print(f"[SNMP] Updated {updates_count} devices and inserted {len(traffic_logs_buffer)} logs.")

        except Exception as e:
            print(f"Errors in SNMP loop: {e}")
            
        await asyncio.sleep(SNMP_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(snmp_monitor_job())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Global SNMP Error: {e}")

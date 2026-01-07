import os
import sys
import asyncio
import time
import tempfile
from datetime import datetime
from typing import List, Dict
from icmplib import async_multiping
from sqlalchemy import text, select, insert
from loguru import logger
from backend.app.database import async_session_factory
from backend.app.config import settings
from backend.app.models import Equipment, Tower, Alert, Parameters
from backend.app.services.notifier import send_notification

# Configurações Dinâmicas (Serão atualizadas pelo load_configs)
BATCH_SIZE = 50 
WRITE_BUFFER_SIZE = 500 
WRITE_INTERVAL = 3.0    
PING_TIMEOUT = settings.ping_timeout_seconds
PING_INTERVAL = settings.ping_interval_seconds
DOWN_COUNT = 3

class PingerService:
    def __init__(self):
        self.targets: Dict[str, Dict] = {} # IP -> {id, name, status, fail_count}
        self.config: Dict[str, str] = {}
        self.results_queue = asyncio.Queue()
        self.id_to_ip = {}
        self.running = True

    async def load_targets(self):
        while self.running:
            try:
                new_targets = {}
                id_to_ip = {} # Maps (type, id) -> ip for lookups
                
                async with async_session_factory() as session:
                    # Carregar Equipamentos
                    res_eq = await session.execute(
                        select(Equipment.ip, Equipment.id, Equipment.name, Equipment.is_online, Equipment.parent_id, Equipment.tower_id)
                        .where(Equipment.ip != None)
                    )
                    eqs = res_eq.all()
                    for row in eqs:
                        ip, eid, name, is_online, parent_id, tower_id = row
                        prev = self.targets.get(ip, {})
                        new_targets[ip] = {
                            "type": "equipment",
                            "id": eid, 
                            "name": name, 
                            "status": is_online,
                            "fail_count": prev.get("fail_count", 0),
                            "parent_id": parent_id,
                            "tower_id": tower_id
                        }
                        id_to_ip[("equipment", eid)] = ip
                    
                    # Carregar Torres
                    res_tw = await session.execute(
                        select(Tower.ip, Tower.id, Tower.name, Tower.is_online, Tower.parent_id)
                        .where(Tower.ip != None)
                    )
                    tws = res_tw.all()
                    for row in tws:
                        ip, tid, name, is_online, parent_id = row
                        prev = self.targets.get(ip, {})
                        new_targets[ip] = {
                            "type": "tower",
                            "id": tid, 
                            "name": name, 
                            "status": is_online,
                            "fail_count": prev.get("fail_count", 0),
                            "parent_id": parent_id
                        }
                        id_to_ip[("tower", tid)] = ip

                self.targets = new_targets # Swap (Atomic)
                self.id_to_ip = id_to_ip
                logger.debug(f"Targets synchronized: {len(eqs)} equipments, {len(tws)} towers.")
            except Exception as e:
                if "no such table" in str(e).lower():
                    logger.warning("⏳ Aguardando inicialização do Banco de Dados...")
                else:
                    logger.error(f"Error loading targets: {e}")
                    await asyncio.sleep(5)
                    continue
            
            await asyncio.sleep(60) # Recarregar a cada 1 minuto

    async def load_configs(self):
        """Carrega configurações de alerta e templates periodicamente."""
        while self.running:
            try:
                async with async_session_factory() as session:
                    res = await session.execute(select(Parameters))
                    params = {p.key: p.value for p in res.scalars().all()}
                    self.config = params
                    
                    # Atualizar variáveis globais do serviço
                    global PING_INTERVAL, PING_TIMEOUT, DOWN_COUNT
                    if "ping_interval" in params:
                        PING_INTERVAL = int(params["ping_interval"])
                    if "ping_timeout" in params:
                        PING_TIMEOUT = int(params["ping_timeout"])
                    if "ping_down_count" in params:
                        DOWN_COUNT = int(params["ping_down_count"])
            except Exception as e:
                logger.error(f"Error loading configs: {e}")
                await asyncio.sleep(5) # Retry faster if failed
                continue
            await asyncio.sleep(60)

    async def ping_worker(self):
        logger.info("Ping Worker Started (Zabbix-Style Engine)")
        
        # Zabbix Architecture: Fixed Pool of Pingers (Workers)
        # We simulate this using a Semaphore to limit concurrent "multiping" batches.
        # Window's socket limit is strict, so we stay well below.
        
        MAX_CONCURRENT_PINGS = 50 # Equivalent to "StartPingers"
        pool_sem = asyncio.Semaphore(5) # Allow 5 batches parallel (5 * 10 IPs = 50 inflight)

        async def worker_task(targets_chunk):
            async with pool_sem:
                try:
                    # Using RAW Sockets (privileged=True) for real ICMP RTT
                    # Count=2, Interval=0.05s for stability
                    results = await async_multiping(
                        targets_chunk, 
                        count=3,        
                        interval=0.05,  
                        timeout=float(PING_TIMEOUT), 
                        payload_size=32,
                        privileged=True 
                    )
                    
                    # Calibração V4: Estabilização de "Piso"
                    OVERHEAD_COMPENSATION = 2.8
                    
                    for host in results:
                        raw_lat = host.min_rtt
                        clean_lat = max(0.0, raw_lat - OVERHEAD_COMPENSATION) if host.is_alive else 0
                        
                        # ANTI-JITTER: Se for muito baixo (<2ms), crava em 1ms para parar de oscilar no gráfico
                        if host.is_alive and clean_lat < 2.0: 
                            clean_lat = 1.0

                        await self.results_queue.put({
                            "ip": host.address,
                            "is_online": host.is_alive,
                            "latency": round(clean_lat, 1),
                            "packet_loss": host.packet_loss,
                            "timestamp": time.time()
                        })
                except Exception as e:
                    logger.error(f"Pinger Batch Error (continuing): {e}")

        while self.running:
            cycle_start = time.time()
            
            # Snapshot targets
            all_targets = [ip for ip in self.targets.keys() if self.is_valid_target(ip)]
            
            if not all_targets:
                await asyncio.sleep(2)
                continue

            # Chunk targets into small batches for the "Pool"
            BATCH_SIZE = 10 
            tasks = []
            
            for i in range(0, len(all_targets), BATCH_SIZE):
                chunk = all_targets[i : i + BATCH_SIZE]
                tasks.append(asyncio.create_task(worker_task(chunk)))
            
            if tasks:
                await asyncio.gather(*tasks)

            # Accurate Interval Control (Uses Global Dynamic Interval)
            elapsed = time.time() - cycle_start
            sleep_time = max(0.5, float(PING_INTERVAL) - elapsed) # Respect configured interval
            
            # logger.debug(f"Ping Cycle: {len(all_targets)} hosts in {elapsed:.2f}s. Sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

    def is_valid_target(self, target: str) -> bool:
        """Simple check to avoid passing garbage to pinger"""
        if not target or len(target) < 7: return False
        # Avoid simple names that aren't IPs if we don't have DNS
        # For now, simplistic check: assume IP if it has digits and dots
        # Proper way: try ipaddress.ip_address(target)
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            # Could be a hostname, let it pass if it looks reasonable?
            # For this system, we focus on IPs mostly.
            # If '124124124' is passed, it fails here.
            return False

    async def db_writer(self):
        logger.info("DB Writer Started (Bulk Postgres)")
        buffer = []
        last_flush = time.time()
        while self.running:
            try:
                try:
                    item = await asyncio.wait_for(self.results_queue.get(), timeout=0.5)
                    buffer.append(item)
                    
                    # 🛡️ PROTEÇÃO: Limite de segurança para evitar 10GB de RAM se o banco travar
                    if len(buffer) > 5000:
                        logger.warning("⚠️ Buffer do Pinger saturado! Descartando logs antigos para preservar memória.")
                        buffer = buffer[-2000:] # Mantém apenas os 2000 mais recentes
                except asyncio.TimeoutError:
                    pass 

                current_time = time.time()
                if buffer and (len(buffer) >= WRITE_BUFFER_SIZE or (current_time - last_flush) >= WRITE_INTERVAL):
                    try:
                        await self.flush_buffer(buffer)
                    finally:
                        # ✅ CORREÇÃO CRÍTICA: Limpar buffer mesmo em caso de erro no flush
                        buffer = []
                        last_flush = current_time
            except Exception as e:
                logger.error(f"Writer loop error: {e}")
                await asyncio.sleep(1)

    async def flush_buffer(self, buffer: List[dict]):
        if not buffer: return
        try:
            async with async_session_factory() as session:
                update_list = []
                latency_inserts = []
                alerts_to_send = []
                
                for item in buffer:
                    target_info = self.targets.get(item['ip'])
                    if not target_info: continue
                    
                    eq_id = target_info['id']
                    old_status = target_info['status']
                    raw_new_status = item['is_online']
                    
                    # --- FLAP PROTECTION LOGIC ---
                    if not raw_new_status:
                        # Falhou o ping
                        target_info['fail_count'] = target_info.get('fail_count', 0) + 1
                    else:
                        # Sucesso no ping
                        target_info['fail_count'] = 0

                    # Somente muda para OFFLINE se falhar a quantidade de vezes configurada
                    if target_info['fail_count'] >= DOWN_COUNT:
                        new_status = False
                    elif raw_new_status:
                        # Se deu online uma vez, já considera online (recuperação rápida)
                        new_status = True
                    else:
                        # Ainda em "queda livre" mas não atingiu limite, mantém status anterior
                        new_status = old_status

                    # Detect Change
                    if old_status is not None and old_status != new_status:
                        # Status Mudou Efetivamente!
                        target_info['status'] = new_status # Atualiza memoria IMEDIATAMENTE
                        
                        device_name = target_info['name']
                        msg_type = "OFFLINE 🔴" if not new_status else "ONLINE 🟢"
                        
                        # Prepare Alert message
                        tmpl_key = "telegram_template_down" if not new_status else "telegram_template_up"
                        template = self.config.get(tmpl_key)
                        
                        if template:
                            message = template.replace("{name}", device_name).replace("{ip}", item['ip'])
                            # Suporte para o novo formato de template
                            now_dt = datetime.now()
                            message = message.replace("[Device.Name]", device_name).replace("[Device.IP]", item['ip'])
                            message = message.replace("[Date]", now_dt.strftime("%d/%m/%Y")).replace("[Time]", now_dt.strftime("%H:%M"))
                        else:
                            message = f"Dispositivo {device_name} ({item['ip']}) está {msg_type}"
                        
                        logger.info(f"STATUS CHANGE: {item['ip']} is now {msg_type}. Message: {message}")
                        
                        # --- TOPOLOGY SUPPRESSION ---
                        is_suppressed = False
                        if not new_status: # Only suppress OFFLINE alerts
                            # 1. Check Parent Equipment
                            pid = target_info.get("parent_id")
                            if pid:
                                parent_ip = self.id_to_ip.get(("equipment", pid))
                                if parent_ip and not self.targets.get(parent_ip, {}).get("status", True):
                                    is_suppressed = True
                                    logger.info(f"[SUPPRESSION] Silent alert for {device_name} ({item['ip']}) - Parent Equipment {parent_ip} is down.")

                            # 2. Check Tower
                            tid = target_info.get("tower_id")
                            if tid and not is_suppressed:
                                tower_ip = self.id_to_ip.get(("tower", tid))
                                if tower_ip and not self.targets.get(tower_ip, {}).get("status", True):
                                    is_suppressed = True
                                    logger.info(f"[SUPPRESSION] Silent alert for {device_name} ({item['ip']}) - Tower {tower_ip} is down.")
                            
                            # 3. Check Tower Parent (Backbone)
                            if target_info["type"] == "tower" and target_info.get("parent_id") and not is_suppressed:
                                t_pid = target_info["parent_id"]
                                t_parent_ip = self.id_to_ip.get(("tower", t_pid))
                                if t_parent_ip and not self.targets.get(t_parent_ip, {}).get("status", True):
                                    is_suppressed = True
                                    logger.info(f"[SUPPRESSION] Silent alert for Tower {device_name} - Backbone Tower {t_parent_ip} is down.")

                        if not is_suppressed:
                            alerts_to_send.append({
                                "device_type": "equipment",
                                "device_name": device_name,
                                "device_ip": item['ip'],
                                "message": message
                            })
                        
                        # Add to DB Alert table (Always log to DB for history, but maybe mark as suppressed?)
                        await session.execute(
                            insert(Alert).values(
                                device_type=target_info["type"],
                                device_name=device_name,
                                device_ip=item['ip'],
                                message=message + (" (Silenciado por topologia)" if is_suppressed else ""),
                                timestamp=datetime.utcnow()
                            )
                        )

                    update_list.append({
                        "p_id": eq_id,
                        "p_online": item['is_online'],
                        "p_last_ping": item['timestamp'],
                        "p_latency": None
                    })
                    if item['is_online']:
                        latency_val = round(item['latency'])
                        latency_inserts.append({
                            "eid": eq_id,
                            "lat": latency_val,
                            "loss": item['packet_loss'],
                            "ts": item['timestamp']
                        })
                        update_list[-1]["p_latency"] = latency_val
                
                if update_list:
                    await session.execute(
                        text("UPDATE equipments SET is_online = :p_online, last_ping = :p_last_ping, last_latency = :p_latency WHERE id = :p_id"),
                        update_list
                    )
                if latency_inserts:
                     # 🛡️ PROTEÇÃO CONTRA FOREIGN KEY VIOLATION: Só insere se o equipamento ainda existir no banco
                     await session.execute(
                        text("""
                            INSERT INTO latency_history (equipment_id, latency, packet_loss, timestamp) 
                            SELECT :eid, :lat, :loss, :ts
                            WHERE EXISTS (SELECT 1 FROM equipments WHERE id = :eid)
                        """),
                        latency_inserts
                    )
                
                await session.commit()
                
                # Send Out of Session Notifications (Async)
                if alerts_to_send:
                    for alert in alerts_to_send:
                        asyncio.create_task(send_notification(
                            message=alert['message'],
                            telegram_token=self.config.get("telegram_token"),
                            telegram_chat_id=self.config.get("telegram_chat_id"),
                            telegram_enabled=(self.config.get("telegram_enabled") != "false"),
                            whatsapp_enabled=(self.config.get("whatsapp_enabled") == "true"),
                            whatsapp_target=self.config.get("whatsapp_target"),
                            whatsapp_target_group=self.config.get("whatsapp_target_group")
                        ))
                    logger.info(f"🚨 Enviados {len(alerts_to_send)} alertas!")

                logger.debug(f"Flushed {len(buffer)} records to DB.")
        except Exception as e:
            logger.error(f"Failed to flush to DB: {e}")
            import traceback
            traceback.print_exc()

    async def start(self):
        logger.info("Starting ISP Monitor Pinger Service (Turbo V2)...")
        await asyncio.gather(self.load_targets(), self.load_configs(), self.ping_worker(), self.db_writer())

import ipaddress

# --- Utility Functions (Legacy Compatibility) ---
async def scan_network(ips: List[str], chunk_size: int = 255):
    """
    Realiza ping em uma lista de IPs e gera resultados de forma ultra-rápida.
    """
    # Processamos em pedaços para não explodir a memória se a lista for gigante (ex: /16)
    for i in range(0, len(ips), chunk_size):
        chunk = ips[i : i + chunk_size]
        try:
            # privileged=False usa sockets UDP para ping (padrão no Windows sem root)
            # count=1 e timeout curto para velocidade máxima de descoberta
            results = await async_multiping(
                chunk, 
                count=1, 
                interval=0.01, 
                timeout=0.8, 
                privileged=False
            )
            for host in results:
                yield {
                    "ip": host.address,
                    "is_online": host.is_alive,
                    "latency": host.avg_rtt,
                    "packet_loss": host.packet_loss
                }
        except Exception as e:
            logger.error(f"Rede inacessível ou erro no scan: {e}")
            # Em caso de erro crítico no chunk, assume offline para não travar
            for ip in chunk:
                yield {"ip": ip, "is_online": False, "error": str(e)}


def ensure_singleton():
    """Garante que apenas uma instância do Pinger rode por vez (Windows/Linux Safe)."""
    import psutil
    
    lock_file = os.path.join(tempfile.gettempdir(), "isp_monitor_pinger.lock")
    
    try:
        current_pid = os.getpid()
        
        # Check if lock exists
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r") as f:
                    old_pid = int(f.read().strip())
                
                # Check if process is actually running
                if psutil.pid_exists(old_pid):
                    print(f"⚠️ Erro: Já existe uma instância do Pinger rodando (PID {old_pid})!")
                    sys.exit(0)
                else:
                    print(f"⚠️ Aviso: Lock file encontrado (PID {old_pid}), mas processo não existe. Removendo trava staled.")
                    os.remove(lock_file)
            except (ValueError, OSError):
                # File corrupted or empty, force remove
                print("⚠️ Aviso: Lock file corrompido. Removendo.")
                try: os.remove(lock_file)
                except: pass

        # Create new lock
        with open(lock_file, "w") as f:
            f.write(str(current_pid))
        
        # Cleanup on exit
        import atexit
        def cleanup():
            try:
                # Only remove if it contains OUR pid (safety check)
                if os.path.exists(lock_file):
                    with open(lock_file, "r") as f:
                        if int(f.read().strip()) == current_pid:
                            os.remove(lock_file)
            except: pass
        atexit.register(cleanup)
        
    except Exception as e:
        logger.error(f"Singleton lock error: {e}")
if __name__ == "__main__":
    ensure_singleton()
    
    # ⚡ BOOST DE PRIORIDADE - DESATIVADO PARA TESTE DE CPU ⚡
    # (High priority com loop apertado causa 100% de CPU e trava o sistema, piorando o ping)
    # try:
    #     import psutil
    #     p = psutil.Process(os.getpid())
    #     if os.name == 'nt':
    #         # p.nice(psutil.HIGH_PRIORITY_CLASS)
    #         p.nice(psutil.NORMAL_PRIORITY_CLASS)
    #     else:
    #         p.nice(0)
    #     logger.info("ℹ️ Process Priority reset to NORMAL to prevent CPU starvation.")
    # except Exception as e:
    #     logger.warning(f"Could not adjust process priority: {e}")

    service = PingerService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        pass

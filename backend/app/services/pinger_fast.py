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

# Configuração Otimizada (V2 - Transplanted)
BATCH_SIZE = 50 
WRITE_BUFFER_SIZE = 100
WRITE_INTERVAL = 1.0
PING_TIMEOUT = settings.ping_timeout_seconds
PING_INTERVAL = settings.ping_interval_seconds

class PingerService:
    def __init__(self):
        self.targets: Dict[str, Dict] = {} # IP -> {id, name, status}
        self.config: Dict[str, str] = {}
        self.results_queue = asyncio.Queue()
        self.running = True

    async def load_targets(self):
        while self.running:
            try:
                async with async_session_factory() as session:
                    # Carregar Equipamentos
                    res_eq = await session.execute(select(Equipment.ip, Equipment.id, Equipment.name, Equipment.is_online).where(Equipment.ip != None))
                    eqs = res_eq.all()
                    for row in eqs:
                        self.targets[row[0]] = {"id": row[1], "name": row[2], "status": row[3]}
                    
                    # Carregar Torres
                    res_tw = await session.execute(select(Tower.ip, Tower.id, Tower.name, Tower.is_online).where(Tower.ip != None))
                    tws = res_tw.all()
                    for row in tws:
                        self.targets[row[0]] = {"id": row[1], "name": row[2], "status": row[3]}

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
            except Exception as e:
                logger.error(f"Error loading configs: {e}")
                await asyncio.sleep(5) # Retry faster if failed
                continue
            await asyncio.sleep(60)

    async def ping_worker(self):
        logger.info("Ping Worker Started (Turbo Mode)")
        while self.running:
            start_time = time.time()
            all_targets = list(self.targets.keys())
            
            # Filter valid IPs only
            ips = [ip for ip in all_targets if self.is_valid_target(ip)]
            
            if not ips:
                await asyncio.sleep(5)
                continue
            
            chunk_size = settings.ping_concurrent_limit
            for i in range(0, len(ips), chunk_size):
                chunk = ips[i : i + chunk_size]
                try:
                    # icmplib async_multiping crashes if hostname cannot be resolved.
                    # We double check validation here or rely on the filter above.
                    results = await async_multiping(chunk, count=2, interval=0.1, timeout=PING_TIMEOUT, privileged=False)
                    for host in results:
                        await self.results_queue.put({
                            "ip": host.address,
                            "is_online": host.is_alive,
                            "latency": host.avg_rtt,
                            "packet_loss": host.packet_loss,
                            "timestamp": time.time()
                        })
                except Exception as e:
                    logger.error(f"Ping execution error for chunk {chunk[:3]}...: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(1.0, PING_INTERVAL - elapsed)
            logger.debug(f"Cycle finished in {elapsed:.2f}s. Sleeping {sleep_time:.2f}s")
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
                except asyncio.TimeoutError:
                    pass 
                current_time = time.time()
                if buffer and (len(buffer) >= WRITE_BUFFER_SIZE or (current_time - last_flush) >= WRITE_INTERVAL):
                    await self.flush_buffer(buffer)
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
                    new_status = item['is_online']
                    
                    # Detect Change
                    if old_status is not None and old_status != new_status:
                        # Status Mudou!
                        target_info['status'] = new_status # Atualiza memoria IMEDIATAMENTE
                        
                        device_name = target_info['name']
                        msg_type = "OFFLINE 🔴" if not new_status else "ONLINE 🟢"
                        
                        # Prepare Alert message
                        tmpl_key = "telegram_template_down" if not new_status else "telegram_template_up"
                        template = self.config.get(tmpl_key)
                        
                        if template:
                            message = template.replace("{name}", device_name).replace("{ip}", item['ip'])
                            # Suporte para o novo formato de template
                            message = message.replace("[Device.Name]", device_name).replace("[Device.IP]", item['ip'])
                        else:
                            message = f"Dispositivo {device_name} ({item['ip']}) está {msg_type}"
                        
                        logger.info(f"STATUS CHANGE: {item['ip']} is now {msg_type}. Message: {message}")
                        
                        alerts_to_send.append({
                            "device_type": "equipment",
                            "device_name": device_name,
                            "device_ip": item['ip'],
                            "message": message
                        })
                        
                        # Add to DB Alert table
                        await session.execute(
                            insert(Alert).values(
                                device_type="equipment",
                                device_name=device_name,
                                device_ip=item['ip'],
                                message=message,
                                timestamp=datetime.utcnow()
                            )
                        )

                    update_list.append({
                        "p_id": eq_id,
                        "p_online": item['is_online'],
                        "p_last_ping": item['timestamp']
                    })
                    if item['is_online']:
                        latency_inserts.append({
                            "eid": eq_id,
                            "lat": item['latency'],
                            "loss": item['packet_loss'],
                            "ts": item['timestamp']
                        })
                
                if update_list:
                    await session.execute(
                        text("UPDATE equipments SET is_online = :p_online, last_ping = :p_last_ping WHERE id = :p_id"),
                        update_list
                    )
                if latency_inserts:
                     await session.execute(
                        text("INSERT INTO latency_history (equipment_id, latency, packet_loss, timestamp) VALUES (:eid, :lat, :loss, :ts)"),
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
async def scan_network(ips: List[str]):
    """
    Realiza ping em uma lista de IPs e gera resultados assincronamente.
    """
    chunk_size = 50
    for i in range(0, len(ips), chunk_size):
        chunk = ips[i : i + chunk_size]
        try:
            # Ping rapido para scanner
            results = await async_multiping(chunk, count=1, interval=0.05, timeout=1.5, privileged=False)
            for host in results:
                yield {
                    "ip": host.address,
                    "is_online": host.is_alive,
                    "latency": host.avg_rtt,
                    "packet_loss": host.packet_loss
                }
        except Exception as e:
            logger.error(f"Scan error for chunk {chunk}: {e}")
            # Yield some error or offline status for these ips if needed, 
            # but for now just continue


def ensure_singleton():
    """Garante que apenas uma instância do Pinger rode por vez."""
    lock_file = os.path.join(tempfile.gettempdir(), "isp_monitor_pinger.lock")
    try:
        # No Windows usamos uma tentativa de remover o arquivo ou abrir exclusivo
        if os.path.exists(lock_file):
             try:
                 os.remove(lock_file)
             except OSError:
                 print("⚠️ Erro: Já existe uma instância do Pinger rodando!")
                 sys.exit(0)
        
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        
        # Registrar deleção ao fechar
        import atexit
        def cleanup():
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except: pass
        atexit.register(cleanup)
        
    except Exception as e:
        logger.error(f"Singleton lock error: {e}")

if __name__ == "__main__":
    ensure_singleton()
    service = PingerService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        pass

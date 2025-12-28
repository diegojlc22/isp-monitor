import asyncio
import time
from typing import List, Dict
from icmplib import async_multiping
from sqlalchemy import text, select
from loguru import logger
from backend.app.database import async_session_factory
from backend.app.config import settings
from backend.app.models import Equipment

# Configuração Otimizada (V2 - Transplanted)
BATCH_SIZE = 50 
WRITE_BUFFER_SIZE = 100
WRITE_INTERVAL = 1.0
PING_TIMEOUT = settings.ping_timeout_seconds
PING_INTERVAL = settings.ping_interval_seconds

class PingerService:
    def __init__(self):
        self.targets: Dict[str, int] = {} # IP -> ID
        self.results_queue = asyncio.Queue()
        self.running = True

    async def load_targets(self):
        while self.running:
            try:
                async with async_session_factory() as session:
                    result = await session.execute(select(Equipment.ip, Equipment.id).where(Equipment.ip != None))
                    new_targets = {row[0]: row[1] for row in result.all() if row[0]}
                    if len(new_targets) != len(self.targets):
                        logger.info(f"Targets updated: {len(new_targets)} hosts loaded.")
                    self.targets = new_targets
            except Exception as e:
                if "no such table" in str(e).lower():
                    logger.warning("⏳ Aguardando inicialização do Banco de Dados...")
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Error loading targets: {e}")
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
                for item in buffer:
                    eq_id = self.targets.get(item['ip'])
                    if not eq_id: continue
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
                logger.debug(f"Flushed {len(buffer)} records to DB.")
        except Exception as e:
            logger.error(f"Failed to flush to DB: {e}")

    async def start(self):
        logger.info("Starting ISP Monitor Pinger Service (Turbo V2)...")
        await asyncio.gather(self.load_targets(), self.ping_worker(), self.db_writer())

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


if __name__ == "__main__":
    service = PingerService()
    try:
        if asyncio.get_event_loop().is_closed():
            asyncio.run(service.start())
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(service.start())
    except KeyboardInterrupt:
        pass

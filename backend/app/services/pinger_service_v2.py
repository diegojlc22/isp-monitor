import asyncio
import time
from typing import List, Dict
from icmplib import async_multiping
from sqlalchemy import text, select
from loguru import logger
from backend.app.database import async_session_factory
from backend.app.config import settings
from backend.app.models import Equipment

# Configuração Otimizada
BATCH_SIZE = 50  # Tamanho do lote de pings simultâneos
WRITE_BUFFER_SIZE = 100 # Quantos resultados acumular antes de escrever no banco
WRITE_INTERVAL = 1.0 # Intervalo máximo para buffer flush
PING_TIMEOUT = settings.ping_timeout_seconds
PING_INTERVAL = settings.ping_interval_seconds

class PingerService:
    def __init__(self):
        self.targets: Dict[str, int] = {} # IP -> ID
        self.results_queue = asyncio.Queue()
        self.running = True

    async def load_targets(self):
        """Carrega alvos do banco de dados periodicamente."""
        while self.running:
            try:
                async with async_session_factory() as session:
                    result = await session.execute(select(Equipment.ip, Equipment.id).where(Equipment.ip != None))
                    # Atualiza o dicionário local
                    new_targets = {row[0]: row[1] for row in result.all() if row[0]}
                    
                    if len(new_targets) != len(self.targets):
                        logger.info(f"Targets updated: {len(new_targets)} hosts loaded.")
                    
                    self.targets = new_targets
            except Exception as e:
                logger.error(f"Error loading targets: {e}")
            
            await asyncio.sleep(60) # Recarrega a cada 1 minuto

    async def ping_worker(self):
        """Worker que executa os pings em batches."""
        logger.info("Ping Worker Started")
        
        while self.running:
            start_time = time.time()
            ips = list(self.targets.keys())
            
            if not ips:
                await asyncio.sleep(5)
                continue

            # Dividir em chunks para async_multiping (embora ele suporte muitos, chunks ajudam no controle)
            # No Windows, limite de handles pode ser problema, então chunks de 50-100 são seguros.
            chunk_size = settings.ping_concurrent_limit
            
            for i in range(0, len(ips), chunk_size):
                chunk = ips[i : i + chunk_size]
                try:
                    # Executa Pings
                    results = await async_multiping(chunk, count=2, interval=0.1, timeout=PING_TIMEOUT, privileged=False)
                    
                    # Coloca na fila de escrita
                    for host in results:
                        await self.results_queue.put({
                            "ip": host.address,
                            "is_online": host.is_alive,
                            "latency": host.avg_rtt,
                            "packet_loss": host.packet_loss,
                            "timestamp": time.time()
                        })
                        
                except Exception as e:
                    logger.error(f"Ping execution error: {e}")
            
            # Controle de cadência (evitar 100% CPU)
            elapsed = time.time() - start_time
            sleep_time = max(1.0, PING_INTERVAL - elapsed)
            logger.debug(f"Cycle finished in {elapsed:.2f}s. Sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

    async def db_writer(self):
        """Consome resultados e grava no banco em Batch."""
        logger.info("DB Writer Started")
        buffer = []
        last_flush = time.time()

        while self.running:
            try:
                # Tenta pegar item da fila com timeout curto
                try:
                    item = await asyncio.wait_for(self.results_queue.get(), timeout=0.5)
                    buffer.append(item)
                except asyncio.TimeoutError:
                    pass # Buffer flush check
                
                # Check Flush Conditions
                current_time = time.time()
                if buffer and (len(buffer) >= WRITE_BUFFER_SIZE or (current_time - last_flush) >= WRITE_INTERVAL):
                    await self.flush_buffer(buffer)
                    buffer = []
                    last_flush = current_time
                    
            except Exception as e:
                logger.error(f"Writer loop error: {e}")
                await asyncio.sleep(1)

    async def flush_buffer(self, buffer: List[dict]):
        """Escreve um lote de resultados no banco de dados usando Bulk Update Otimizado para Postgres."""
        if not buffer: return
        
        try:
            async with async_session_factory() as session:
                # Preparar dados para update em massa (Muito mais rápido no Postgres/AsyncPG)
                update_list = []
                latency_inserts = []
                
                for item in buffer:
                    eq_id = self.targets.get(item['ip'])
                    if not eq_id: continue

                    # Dados para Update na tabela Equipment
                    update_list.append({
                        "p_id": eq_id,
                        "p_online": item['is_online'],
                        "p_last_ping": item['timestamp'],
                        # Opcional: Update latência atual na tabela principal também se existir coluna
                        # "p_latency": int(item['latency'] * 1000) if item['latency'] else None 
                    })
                    
                    # Dados para Insert no Histórico (apenas se online)
                    if item['is_online']:
                        latency_inserts.append({
                            "eid": eq_id,
                            "lat": item['latency'],
                            "loss": item['packet_loss'],
                            "ts": item['timestamp']
                        })

                # 1. Bulk Update Equipments (1 Query valida para N rows)
                if update_list:
                    await session.execute(
                        text("UPDATE equipments SET is_online = :p_online, last_ping = :p_last_ping WHERE id = :p_id"),
                        update_list
                    )

                # 2. Bulk Insert History (1 Query)
                if latency_inserts:
                     await session.execute(
                        text("INSERT INTO latency_history (equipment_id, latency, packet_loss, timestamp) VALUES (:eid, :lat, :loss, :ts)"),
                        latency_inserts
                    )

                await session.commit()
                logger.debug(f"Flushed {len(buffer)} records to DB (Postgres Optimized).")
                
        except Exception as e:
            logger.error(f"Failed to flush to DB: {e}")

    async def start(self):
        logger.info("Starting ISP Monitor Pinger Service v2 (Enterprise)...")
        await asyncio.gather(
            self.load_targets(),
            self.ping_worker(),
            self.db_writer()
        )

if __name__ == "__main__":
    service = PingerService()
    try:
        if asyncio.get_event_loop().is_closed():
            asyncio.run(service.start())
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(service.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")

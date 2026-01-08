import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete
from backend.app.database import AsyncSessionLocal
from backend.app.models import TrafficLog, PingLog
from loguru import logger

async def cleanup_old_logs(days_retention: int = 30):
    """
    Remove logs de tráfego e ping mais antigos que X dias para manter o banco leve.
    """
    logger.info(f"[DB CLEANUP] Iniciando limpeza de logs com mais de {days_retention} dias...")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_retention)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Limpar TrafficLog
            stmt_traffic = delete(TrafficLog).where(TrafficLog.timestamp < cutoff_date)
            res_traffic = await session.execute(stmt_traffic)
            rows_traffic = res_traffic.rowcount
            
            # 2. Limpar PingLog
            stmt_ping = delete(PingLog).where(PingLog.timestamp < cutoff_date)
            res_ping = await session.execute(stmt_ping)
            rows_ping = res_ping.rowcount
            
            await session.commit()
            
            if rows_traffic > 0 or rows_ping > 0:
                logger.success(f"[DB CLEANUP] Removidos: {rows_traffic} logs de tráfego, {rows_ping} logs de ping.")
            else:
                logger.info("[DB CLEANUP] Nenhum log antigo para remover.")
                
        except Exception as e:
            logger.error(f"[DB CLEANUP] Erro durante limpeza: {e}")
            await session.rollback()

async def scheduler_cleanup():
    """
    Roda a limpeza uma vez por dia (ou na inicialização).
    """
    while True:
        await cleanup_old_logs(days_retention=30)
        # Espera 24 horas
        await asyncio.sleep(86400)

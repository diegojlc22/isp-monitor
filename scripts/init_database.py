"""
Script de inicialização do banco de dados
Garante que todas as tabelas e colunas existem
"""
import asyncio
from backend.app.database import engine
from backend.app.models import Base
from backend.app.config import settings
from loguru import logger
from sqlalchemy import text

async def init_database():
    """Cria todas as tabelas se não existirem e adiciona colunas faltantes"""
    try:
        logger.info("[DB Init] Verificando schema do banco de dados...")
        
        async with engine.begin() as conn:
            # Cria todas as tabelas definidas nos models
            await conn.run_sync(Base.metadata.create_all)
            
            # Se for PostgreSQL, adicionar colunas faltantes
            if "postgresql" in settings.async_database_url:
                logger.info("[DB Init] Verificando colunas faltantes...")
                
                # SQL para adicionar colunas se não existirem
                migrations = [
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_ping FLOAT",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_latency FLOAT",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_in BIGINT",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS last_traffic_out BIGINT",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS signal_dbm INTEGER",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS ccq INTEGER",
                    "ALTER TABLE equipments ADD COLUMN IF NOT EXISTS connected_clients INTEGER",
                ]
                
                for sql in migrations:
                    try:
                        await conn.execute(text(sql))
                    except Exception as e:
                        logger.warning(f"[DB Init] Migration warning: {e}")
                
                logger.info("[DB Init] ✅ Colunas verificadas/adicionadas!")
            
        logger.info("[DB Init] ✅ Schema do banco verificado/criado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"[DB Init] ❌ Erro ao inicializar banco: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database())
    exit(0 if success else 1)

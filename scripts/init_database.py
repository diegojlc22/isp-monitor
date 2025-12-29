"""
Script de inicialização do banco de dados
Garante que todas as tabelas e colunas existem
"""
import asyncio
from backend.app.database import engine
from backend.app.models import Base
from loguru import logger

async def init_database():
    """Cria todas as tabelas se não existirem"""
    try:
        logger.info("[DB Init] Verificando schema do banco de dados...")
        
        async with engine.begin() as conn:
            # Cria todas as tabelas definidas nos models
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("[DB Init] ✅ Schema do banco verificado/criado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"[DB Init] ❌ Erro ao inicializar banco: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_database())
    exit(0 if success else 1)

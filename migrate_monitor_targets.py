"""
Migração PostgreSQL - Adicionar is_priority em monitor_targets
"""
import asyncio
from sqlalchemy import text
from backend.app.database import AsyncSessionLocal

async def migrate():
    async with AsyncSessionLocal() as session:
        try:
            # Add is_priority column to monitor_targets
            await session.execute(text("""
                ALTER TABLE monitor_targets 
                ADD COLUMN IF NOT EXISTS is_priority BOOLEAN DEFAULT FALSE;
            """))
            
            await session.commit()
            print("✅ Coluna 'is_priority' adicionada à tabela 'monitor_targets'")
        
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            await session.rollback()

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    asyncio.run(migrate())

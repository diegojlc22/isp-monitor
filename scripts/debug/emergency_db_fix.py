import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def emergency_fix():
    async with engine.begin() as conn:
        print("Limpando bloqueios e criando colunas...")
        # Termina todas as outras conexões
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'isp_monitor' 
              AND pid <> pg_backend_pid();
        """))
        
        # Cria as colunas
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_multiplier FLOAT DEFAULT 1.0;"))
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_offset FLOAT DEFAULT 0.0;"))
        print("✅ Colunas criadas com sucesso!")

if __name__ == "__main__":
    asyncio.run(emergency_fix())

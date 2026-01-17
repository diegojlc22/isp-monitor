import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def force_db_update():
    async with engine.begin() as conn:
        print("Destravando banco de dados...")
        # Mata outras conexões que possam estar travando a tabela equipments
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'isp_monitor' 
              AND pid <> pg_backend_pid()
              AND state = 'idle';
        """))
        
        print("Adicionando colunas de calibração...")
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_multiplier FLOAT DEFAULT 1.0;"))
        await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS voltage_offset FLOAT DEFAULT 0.0;"))
        
        print("Aplicando correção de 1.05 para o rádio 192.168.106.62...")
        await conn.execute(text("UPDATE equipments SET voltage_multiplier = 1.05 WHERE ip = '192.168.106.62'"))
        
        print("✅ TUDO PRONTO! Calibração ativa.")

if __name__ == "__main__":
    asyncio.run(force_db_update())

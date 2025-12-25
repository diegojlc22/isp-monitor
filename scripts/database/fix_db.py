
import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Configuração do Banco
DB_URL = "postgresql+asyncpg://postgres:admin@localhost/isp_monitor"

import time

async def fix_database():
    time.sleep(3)
    print("🔧 Iniciando reparo do banco de dados (Tabela Users)...")
    engine = create_async_engine(DB_URL)
    
    async with engine.begin() as conn:
        # Tentar adicionar cada coluna individualmente
        columns = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_latitude FLOAT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_longitude FLOAT;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_location_update TIMESTAMP WITHOUT TIME ZONE;"
        ]
        
        for sql in columns:
            try:
                print(f"Executando: {sql}")
                await conn.execute(text(sql))
                print("   -> Sucesso!")
            except Exception as e:
                print(f"   -> Falha: {e}")

    await engine.dispose()
    print("✅ Reparo concluído! As colunas devem existir agora.")

if __name__ == "__main__":
    asyncio.run(fix_database())

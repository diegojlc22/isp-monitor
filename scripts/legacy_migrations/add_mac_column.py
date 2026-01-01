import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from backend.app.config import DATABASE_URL

async def add_mac_column():
    print("🔌 Conectando ao Banco de Dados...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        try:
            print("📦 Verificando tabela equipments...")
            # Check if column exists
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='equipments' AND column_name='mac_address';"))
            if result.scalar():
                print("✅ Coluna 'mac_address' já existe.")
                return

            print("➕ Adicionando coluna 'mac_address'...")
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN mac_address VARCHAR;"))
            await conn.execute(text("CREATE INDEX ix_equipments_mac_address ON equipments (mac_address);"))
            print("✅ Coluna adicionada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(add_mac_column())

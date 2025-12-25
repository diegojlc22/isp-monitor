
from backend.app.database import engine
from sqlalchemy import text
import asyncio

async def add_columns():
    async with engine.begin() as conn:
        print("Adicionando colunas de rastreamento na tabela users...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_latitude FLOAT"))
            print("- last_latitude adicionada.")
        except Exception:
            print("- last_latitude já existe.")

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_longitude FLOAT"))
            print("- last_longitude adicionada.")
        except Exception:
            print("- last_longitude já existe.")

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_location_update TIMESTAMP"))
            print("- last_location_update adicionada.")
        except Exception:
            print("- last_location_update já existe.")

if __name__ == "__main__":
    asyncio.run(add_columns())

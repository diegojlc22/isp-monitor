import asyncio
from sqlalchemy import text
from backend.app.database import engine

async def check_columns():
    async with engine.connect() as conn:
        # Check equipments table
        print("--- Columns in 'equipments' table ---")
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'equipments'"))
        for row in res:
            print(row[0])
            
        # Check network_links table
        print("\n--- Columns in 'network_links' table ---")
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'network_links'"))
        for row in res:
            print(row[0])
            
        # Check if insights table exists
        print("\n--- Tables ---")
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        for row in res:
            print(row[0])

if __name__ == "__main__":
    asyncio.run(check_columns())

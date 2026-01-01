import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def test_query():
    async with AsyncSessionLocal() as db:
        print("🔍 Testando query direta no banco...")
        
        # Query simples sem joins
        query = select(Equipment).limit(5)
        result = await db.execute(query)
        equipments = result.scalars().all()
        
        print(f"✅ Retornou {len(equipments)} equipamentos")
        for eq in equipments:
            print(f"  - {eq.name} ({eq.ip})")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_query())

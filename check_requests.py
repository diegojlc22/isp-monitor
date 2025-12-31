
import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import TowerRequest
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TowerRequest))
        items = res.scalars().all()
        print(f"Total requests: {len(items)}")
        for item in items:
            print(f"ID: {item.id} | Name: {item.name} | Status: {item.status}")

if __name__ == "__main__":
    asyncio.run(run())

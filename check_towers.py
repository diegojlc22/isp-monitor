
import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Tower))
        items = res.scalars().all()
        print(f"Total towers: {len(items)}")
        for item in items:
            print(f"ID: {item.id} | Name: {item.name} | Lat: {item.latitude} | Lon: {item.longitude}")

if __name__ == "__main__":
    asyncio.run(run())

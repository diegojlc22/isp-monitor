
import asyncio
from sqlalchemy import select
from backend.app.database import async_session_factory
from backend.app.models import Tower

async def check():
    async with async_session_factory() as session:
        result = await session.execute(select(Tower))
        towers = result.scalars().all()
        print(f"Total: {len(towers)}")
        for t in towers[:5]:
            print(f"ID: {t.id}, Name: {t.name}, Lat: {t.latitude}, Lon: {t.longitude}")

if __name__ == "__main__":
    asyncio.run(check())

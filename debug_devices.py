import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment

async def list_devices():
    async with AsyncSessionLocal() as session:
        print("--- TOWERS ---")
        res_t = await session.execute(select(Tower))
        towers = res_t.scalars().all()
        for t in towers:
            print(f"ID: {t.id} | Name: {t.name} | IP: {t.ip} | Online: {t.is_online}")

        print("\n--- EQUIPMENT ---")
        res_e = await session.execute(select(Equipment))
        equips = res_e.scalars().all()
        for e in equips:
            print(f"ID: {e.id} | Name: {e.name} | IP: {e.ip} | Online: {e.is_online}")

if __name__ == "__main__":
    asyncio.run(list_devices())

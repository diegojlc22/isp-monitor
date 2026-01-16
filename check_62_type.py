
import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Equipment).where(Equipment.ip == '192.168.106.62'))
        eq = res.scalar_one_or_none()
        if eq:
            print(f"IP: {eq.ip}")
            print(f"Type: {eq.equipment_type}")
            print(f"Brand: {eq.brand}")
            print(f"Is MikroTik: {eq.is_mikrotik}")

if __name__ == "__main__":
    asyncio.run(check())

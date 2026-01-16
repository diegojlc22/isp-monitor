
import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment

async def check_62():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Equipment).where(Equipment.ip == '192.168.106.62'))
        eq = res.scalar_one_or_none()
        if eq:
            print(f"Community: {eq.snmp_community}")
            print(f"Brand: {eq.brand}")
        else:
            print("Not found")

if __name__ == "__main__":
    asyncio.run(check_62())

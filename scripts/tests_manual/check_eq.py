import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Equipment).where(Equipment.ip == "192.168.103.203"))
        eq = res.scalar_one_or_none()
        if eq:
            print(f"ID: {eq.id}")
            print(f"Name: {eq.name}")
            print(f"IP: {eq.ip}")
            print(f"Type: {eq.equipment_type}")
            print(f"Brand: {eq.brand}")
            print(f"Community: {eq.snmp_community}")
            print(f"Connected Clients: {eq.connected_clients}")
        else:
            print("Equipment not found.")

if __name__ == "__main__":
    asyncio.run(check())

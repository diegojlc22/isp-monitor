
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.app.database import async_session_factory
from backend.app.models import Equipment
from sqlalchemy import select

async def add_device():
    async with async_session_factory() as session:
        # Check if already exists
        result = await session.execute(select(Equipment).where(Equipment.ip == "192.168.103.2"))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Device with IP 192.168.103.2 already exists: {existing.name} (ID: {existing.id})")
            return

        new_eq = Equipment(
            name="TESTE-LATENCIA-103.2",
            ip="192.168.103.2",
            is_online=False,
            brand="generic",
            equipment_type="station",
            snmp_community="public",
            snmp_version=1
        )
        session.add(new_eq)
        await session.commit()
        print("Device added successfully!")

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(add_device())
    except Exception as e:
        print(f"Error: {e}")

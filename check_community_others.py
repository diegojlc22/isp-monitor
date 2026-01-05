import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Equipment).where(Equipment.snmp_community == "publicRadionet", Equipment.is_online == True))
        eqs = res.scalars().all()
        print(f"Found {len(eqs)} online devices with community 'publicRadionet'")
        for eq in eqs:
            print(f"IP: {eq.ip} | Name: {eq.name} | Clients: {eq.connected_clients}")

if __name__ == "__main__":
    asyncio.run(check())

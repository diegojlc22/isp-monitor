import asyncio
import sys
import os
from sqlalchemy import update

# Add root path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment

async def set_default_interfaces():
    print("🛠️ Configurando interfaces padrão de tráfego (eth0) para os rádios...")
    async with AsyncSessionLocal() as session:
        # Ubiquiti (eth0 = 2)
        await session.execute(
            update(Equipment)
            .where(Equipment.ip == "192.168.80.13")
            .values(snmp_traffic_interface_index=2, snmp_interface_index=2)
        )
        # Intelbras (eth0 = 7)
        await session.execute(
            update(Equipment)
            .where(Equipment.ip == "192.168.177.30")
            .values(snmp_traffic_interface_index=7, snmp_interface_index=7)
        )
        # AirFiber (eth0 = 2)
        await session.execute(
            update(Equipment)
            .where(Equipment.ip == "10.50.1.2")
            .values(snmp_traffic_interface_index=2, snmp_interface_index=2)
        )
        await session.commit()
    print("✅ Interfaces configuradas. O tráfego deve aparecer no próximo ciclo (60s).")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(set_default_interfaces())

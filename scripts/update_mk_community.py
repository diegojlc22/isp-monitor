import asyncio
import sys
import os
from sqlalchemy import update

# Add root path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment

async def update_communities():
    print("🛠️ Corrigindo community para 'publicRadionet' no Mikrotik...")
    async with AsyncSessionLocal() as session:
        # Apenas para o Mikrotik 192.168.103.2
        stmt = (
            update(Equipment)
            .where(Equipment.ip == "192.168.103.2")
            .values(snmp_community="publicRadionet")
        )
        await session.execute(stmt)
        await session.commit()
    print("✅ Atualizado com sucesso.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(update_communities())


import asyncio
import os
import sys
from sqlalchemy import select

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import MonitorTarget

async def check_targets():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MonitorTarget))
        targets = result.scalars().all()
        print(f"\nTotal de Alvos: {len(targets)}")
        for t in targets:
            print(f"- {t.name} ({t.target}) | Tipo: {t.type} | Ativo: {t.enabled}")

if __name__ == "__main__":
    asyncio.run(check_targets())

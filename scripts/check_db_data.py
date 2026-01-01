import asyncio
import sys
import os
from sqlalchemy import select, func, text

# Add root path
sys.path.append(os.getcwd())

from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models import Equipment

async def check_data():
    async with AsyncSessionLocal() as db:
        try:
            # 1. Count Equipments
            result = await db.execute(select(func.count(Equipment.id)))
            count = result.scalar()
            print(f"📊 Total de Equipamentos no Banco de Dados: {count}")

            # 2. List some to verify
            result = await db.execute(select(Equipment.name, Equipment.ip).limit(5))
            eqs = result.all()
            for name, ip in eqs:
                print(f"   - {name} ({ip})")

            if count == 0:
                print("⚠️ ALERTA: Tabela de equipamentos está vazia!")
            else:
                print("✅ Os dados estão no banco. O problema é na exibição/API.")
                
        except Exception as e:
            print(f"❌ Erro ao ler banco: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_data())

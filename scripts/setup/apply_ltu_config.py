
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def main():
    target_ip = "10.50.1.3"
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Equipment).where(Equipment.ip == target_ip))
        eq = result.scalar_one_or_none()
        
        if not eq:
            print(f"Equipamento {target_ip} não encontrado!")
            return
            
        print(f"Configurando {eq.name} ({eq.ip}) para usar OIDs LTU (Index 1000)...")
        eq.snmp_traffic_interface_index = 1000
        eq.brand = 'ubiquiti' # Garantir que o brand está certo
        
        await db.commit()
        print("✅ Configuração aplicada com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())

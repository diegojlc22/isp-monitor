
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select, update

async def update_equipment(ip, interface_index, eq_type):
    async with AsyncSessionLocal() as session:
        q = select(Equipment).where(Equipment.ip == ip)
        res = await session.execute(q)
        eq = res.scalar_one_or_none()
        
        if not eq:
            print(f"❌ Equipamento com IP {ip} não encontrado.")
            return

        print(f"⚙️ Atualizando {eq.name} ({ip}):")
        print(f"   Interface Index: {eq.snmp_interface_index} -> {interface_index}")
        print(f"   Tipo: {eq.equipment_type} -> {eq_type}")
        
        eq.snmp_interface_index = interface_index
        eq.equipment_type = eq_type
        
        await session.commit()
        print("✅ Atualização concluída!")

async def main():
    if len(sys.argv) < 4:
        print("Uso: python ferramentas/config_eq.py <IP> <INDEX> <TYPE>")
        print("EX: python ferramentas/config_eq.py 192.168.103.2 10 fiber")
        return
    
    ip = sys.argv[1]
    idx = int(sys.argv[2])
    eq_type = sys.argv[3]
    
    await update_equipment(ip, idx, eq_type)

if __name__ == "__main__":
    asyncio.run(main())

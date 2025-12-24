"""
🔍 DIAGNÓSTICO RÁPIDO - Verificar se SNMP está coletando dados
"""
import asyncio
import sys
sys.path.insert(0, 'c:/diegolima/isp-monitor')

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select

async def check_equipment_data():
    print("="*70)
    print("🔍 VERIFICANDO DADOS DOS EQUIPAMENTOS")
    print("="*70)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Equipment))
        equipments = result.scalars().all()
        
        print(f"\n📊 Total de equipamentos: {len(equipments)}\n")
        
        for eq in equipments:
            print(f"{'='*70}")
            print(f"📌 {eq.name} ({eq.ip})")
            print(f"{'='*70}")
            print(f"  🔌 Online: {'✅ SIM' if eq.is_online else '❌ NÃO'}")
            print(f"  🏷️  Brand: {eq.brand}")
            print(f"  🔧 SNMP Community: {eq.snmp_community}")
            print(f"  📡 SNMP Version: v{eq.snmp_version}")
            print(f"  🔌 SNMP Port: {eq.snmp_port}")
            print(f"  🔢 Interface Index: {eq.snmp_interface_index}")
            print(f"\n  📊 DADOS WIRELESS:")
            print(f"     Signal: {eq.signal_dbm if eq.signal_dbm else '❌ SEM DADOS'}")
            print(f"     CCQ: {eq.ccq if eq.ccq else '❌ SEM DADOS'}")
            print(f"     Clientes: {eq.connected_clients if eq.connected_clients is not None else '❌ SEM DADOS'}")
            print(f"\n  📈 TRÁFEGO:")
            print(f"     In: {eq.last_traffic_in} Mbps")
            print(f"     Out: {eq.last_traffic_out} Mbps")
            print()

if __name__ == "__main__":
    asyncio.run(check_equipment_data())

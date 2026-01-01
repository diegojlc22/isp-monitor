
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from sqlalchemy import select
from backend.app.services.snmp import get_snmp_interface_traffic
from backend.app.services.wireless_snmp import get_wireless_stats

async def test_device(eq):
    print(f"\n--- TESTANDO: {eq.name} ({eq.ip}) ---")
    ip = eq.ip
    community = eq.snmp_community or "publicRadionet"
    brand = eq.brand
    idx = eq.snmp_traffic_interface_index or 1
    
    # Test Traffic
    traffic = await get_snmp_interface_traffic(ip, community, interface_index=idx, brand=brand)
    if traffic:
        print(f"Tráfego: {traffic[0]} bytes (IN), {traffic[1]} bytes (OUT)")
    else:
        print("Tráfego: FALHA")
        
    # Test Wireless
    stats = await get_wireless_stats(ip, brand, community)
    print(f"Sinal: {stats.get('signal_dbm')} dBm | CCQ: {stats.get('ccq')}%")

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Equipment).where(Equipment.brand == 'ubiquiti'))
        equipments = result.scalars().all()
        
        if not equipments:
            print("Nenhum equipamento Ubiquiti encontrado no banco.")
            return
            
        print(f"Encontrados {len(equipments)} equipamentos Ubiquiti. Iniciando validação...")
        
        for eq in equipments:
            try:
                await test_device(eq)
            except Exception as e:
                print(f"Erro ao testar {eq.ip}: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

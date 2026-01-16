
import asyncio
import time
from backend.app.services.wireless_snmp import get_health_stats, get_wireless_stats
from backend.app.services.snmp import get_snmp_interface_traffic

async def debug_device(ip, community):
    print(f"--- Debugging {ip} ---")
    start = time.time()
    
    try:
        print("1. Testing Health Stats (CPU, Voltage, etc)...")
        h_start = time.time()
        # Aumentamos o timeout interno para ver se responde
        h_stats = await get_health_stats(ip, 'ubiquiti', community)
        print(f"   Result: {h_stats}")
        print(f"   Took: {time.time() - h_start:.2f}s")
    except Exception as e:
        print(f"   Health Error: {e}")
        
    try:
        print("2. Testing Wireless Stats...")
        w_start = time.time()
        w_stats = await get_wireless_stats(ip, 'ubiquiti', community)
        print(f"   Result: {w_stats}")
        print(f"   Took: {time.time() - w_start:.2f}s")
    except Exception as e:
        print(f"   Wireless Error: {e}")

    try:
        print("3. Testing Traffic Stats...")
        t_start = time.time()
        traffic = await get_snmp_interface_traffic(ip, community, 161, 1)
        print(f"   Result: {traffic}")
        print(f"   Took: {time.time() - t_start:.2f}s")
    except Exception as e:
        print(f"   Traffic Error: {e}")

    print(f"\nTotal Time: {time.time() - start:.2f}s")

if __name__ == "__main__":
    # Pega community do banco para o IP 62
    from backend.app.database import AsyncSessionLocal
    from backend.app.models import Equipment
    from sqlalchemy import select

    async def run():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Equipment).where(Equipment.ip == '192.168.106.62'))
            eq = res.scalar_one_or_none()
            if not eq:
                print("Equipamento não encontrado.")
                return
            await debug_device(eq.ip, eq.snmp_community)

    asyncio.run(run())

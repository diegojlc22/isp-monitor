
import asyncio
from backend.app.services.wireless_snmp import snmp_walk_list

async def walk_ubnt(ip, community):
    print(f"--- Walking Ubiquiti OIDs for {ip} ---")
    # Ubiquiti AirMAX / Health branch
    root = "1.3.6.1.4.1.41112"
    results = await snmp_walk_list(ip, community, root)
    if not results:
        print("No results found in Ubiquiti branch.")
        return
    
    print(f"Found {len(results)} OIDs.")
    # Search for values that look like voltage (e.g. 24000, 240, 24.5)
    for i, val in enumerate(results):
        try:
            v_float = float(val)
            # Voltage usually between 10 and 60 (or 10000 and 60000 for mV)
            if 10 <= v_float <= 60 or 10000 <= v_float <= 60000 or 100 <= v_float <= 600:
                print(f"Potential Voltage OID found? Value: {val}")
        except: pass

if __name__ == "__main__":
    from backend.app.database import AsyncSessionLocal
    from backend.app.models import Equipment
    from sqlalchemy import select

    async def run():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Equipment).where(Equipment.ip == '192.168.106.62'))
            eq = res.scalar_one_or_none()
            if not eq: return
            await walk_ubnt(eq.ip, eq.snmp_community)

    asyncio.run(run())

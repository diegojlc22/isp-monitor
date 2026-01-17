
import asyncio
from backend.app.services.wireless_snmp import snmp_walk_list

async def full_walk(ip, community):
    print(f"--- Full Enterprise Walk for {ip} ---")
    root = "1.3.6.1.4.1"
    results = await snmp_walk_list(ip, community, root)
    if not results:
        print("No results found in Enterprise branch.")
        return
    
    print(f"Found {len(results)} OIDs.")
    # Search for values that look like voltage (e.g. 24000, 240, 24.5)
    for i, val in enumerate(results):
        try:
            v_float = float(val)
            if 10000 <= v_float <= 60000 or 100 <= v_float <= 600:
                 # Check if it's near 24-26V (240-260 or 24000-26000)
                 if (240 <= v_float <= 280) or (24000 <= v_float <= 28000):
                    print(f"Potential Voltage candidate: {val}")
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
            await full_walk(eq.ip, eq.snmp_community)

    asyncio.run(run())

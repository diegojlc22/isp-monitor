import asyncio
from backend.app.services.snmp import _snmp_get

async def test():
    ip = "192.168.103.203"
    community = "public"
    
    # sysDescr
    res = await _snmp_get(ip, community, ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.5.0"])
    if res:
        print(f"Descr: {res[0][1]}")
        print(f"Name: {res[1][1]}")
    else:
        print("SNMP Failed (No response or wrong community)")

if __name__ == "__main__":
    asyncio.run(test())

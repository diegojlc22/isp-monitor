import asyncio
from pysnmp.hlapi.asyncio import *

async def run():
    ip = "192.168.106.33"
    community = "publicRadionet"
    port = 161
    
    print(f"Deep Scan on {ip}...")
    
    engine = SnmpEngine()
    auth = CommunityData(community, mpModel=1) # v2c
    target = UdpTransportTarget((ip, port), timeout=2, retries=1)
    
    # Try common Ubiquiti Roots
    roots = [
        '1.3.6.1.2.1.1.1',         # sysDescr
        '1.3.6.1.4.1.41112.1.4',   # AirMAX
        '1.3.6.1.4.1.41112.1.10',  # LTU
    ]
    
    for root in roots:
        print(f"\nWalking {root}...")
        errorIndication, errorStatus, errorIndex, varBindTable = await nextCmd(
            engine, auth, target, ContextData(),
            ObjectType(ObjectIdentity(root)),
            lexicographicMode=False
        )
        
        if errorIndication:
            print(f"Error: {errorIndication}")
        elif errorStatus:
            print(f"Status Error: {errorStatus.prettyPrint()}")
        else:
            for varBinds in varBindTable:
                for oid, val in varBinds:
                    print(f"{oid.prettyPrint()} = {val.prettyPrint()}")
                    break # Just show first of each walk to confirm connectivity
                break

if __name__ == "__main__":
    asyncio.run(run())

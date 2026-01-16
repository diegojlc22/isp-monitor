
import asyncio
from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, SnmpEngine

async def walk_with_oids(ip, community):
    print(f"--- Full OID Scan for {ip} ---")
    engine = SnmpEngine()
    auth = CommunityData(community, mpModel=1)
    target = UdpTransportTarget((ip, 161), timeout=2.0, retries=1)
    root = "1.3.6.1.4.1"
    
    try:
        iterator = nextCmd(engine, auth, target, ContextData(), ObjectType(ObjectIdentity(root)), lexicographicMode=False)
        async for errorIndication, errorStatus, errorIndex, varBindTable in iterator:
            if errorIndication:
                print(errorIndication)
                break
            for varBind in varBindTable:
                oid = str(varBind[0])
                val = str(varBind[1])
                try:
                    v_float = float(val)
                    if 200 <= v_float <= 300: # 20.0V - 30.0V range
                        print(f"FOUND: {oid} = {val}")
                except: pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(walk_with_oids('192.168.106.62', 'public_read')) # I'll use public_read for now or get from DB

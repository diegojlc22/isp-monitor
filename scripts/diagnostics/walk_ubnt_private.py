
import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine
from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def main():
    target_ip = "10.50.1.3"
    community = "publicRadionet"
    
    print(f"--- UBIQUITI PRIVATE MIB WALK: {target_ip} ---")
    
    engine = get_shared_engine()
    root_oid = '1.3.6.1.4.1.41112' 
    
    async def get_all():
        results = {}
        curr_oid = ObjectIdentity(root_oid)
        while True:
            # Try v1 and v2c
            error, status, index, varBinds = await nextCmd(
                engine, CommunityData(community, mpModel=0), # v1
                UdpTransportTarget((target_ip, 161), timeout=2, retries=1),
                ContextData(), ObjectType(curr_oid), lexicographicMode=False
            )
            if error or status or not varBinds: break
            
            vb = varBinds[0]
            oid_obj, val_obj = vb[0]
            
            if not str(oid_obj).startswith(root_oid): break
            
            try:
                results[str(oid_obj)] = int(val_obj)
            except:
                results[str(oid_obj)] = str(val_obj)
            curr_oid = oid_obj
        return results

    print("Capturando amostra (Private MIB)...")
    s1 = await get_all()
    if not s1:
        print("Nenhum dado encontrado no Private MIB.")
        return
        
    await asyncio.sleep(5)
    s2 = await get_all()
    
    print("\nAnalisando mudanças...")
    for oid in s2:
        if oid in s1:
            try:
                v1 = int(s1[oid])
                v2 = int(s2[oid])
                diff = v2 - v1
                if diff > 1000000:
                    mbps = (diff * 8) / (5 * 1000000)
                    print(f"OID: {oid} | Diff: {diff} | Approx: {mbps:.2f} Mbps")
            except:
                pass

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

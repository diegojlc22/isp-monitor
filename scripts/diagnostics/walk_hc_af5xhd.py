
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
    
    print(f"--- SNMP COUNTER WALK: {target_ip} ---")
    
    engine = get_shared_engine()
    
    # Tables to walk:
    # 1.3.6.1.2.1.2.2.1.10 (ifInOctets)
    # 1.3.6.1.2.1.2.2.1.16 (ifOutOctets)
    # 1.3.6.1.2.1.31.1.1.1.6 (ifHCInOctets)
    # 1.3.6.1.2.1.31.1.1.1.10 (ifHCOutOctets)
    roots = [
        '1.3.6.1.2.1.2.2.1.10',
        '1.3.6.1.2.1.2.2.1.16',
        '1.3.6.1.2.1.31.1.1.1.6',
        '1.3.6.1.2.1.31.1.1.1.10'
    ]
    
    async def get_counters():
        results = {}
        for root in roots:
            curr_oid = ObjectIdentity(root)
            while True:
                error, status, index, varBinds = await nextCmd(
                    engine, CommunityData(community, mpModel=0), # FORCING v1
                    UdpTransportTarget((target_ip, 161), timeout=2, retries=1),
                    ContextData(), ObjectType(curr_oid), lexicographicMode=False
                )
                if error or status or not varBinds: break
                
                # Correct unpacking for pysnmp varBinds
                vb = varBinds[0]
                oid_obj, val_obj = vb[0]
                
                if not str(oid_obj).startswith(root): break
                
                try:
                    results[str(oid_obj)] = int(val_obj)
                except:
                    pass
                curr_oid = oid_obj
        return results

    print("Capturando primeira amostra...")
    s1 = await get_counters()
    if not s1:
        print("Nenhum contador encontrado. SNMP v2c ativo?")
        return
        
    await asyncio.sleep(5)
    print("Capturando segunda amostra...")
    s2 = await get_counters()
    
    print("\nAnalisando tráfego real (+1MB/s)...")
    found = False
    for oid in s2:
        if oid in s1:
            v1 = s1[oid]
            v2 = s2[oid]
            diff = v2 - v1
            
            # Detect rollover/reset
            if diff < 0:
                if "1.3.6.1.2.1.31" in oid: # 64-bit
                    diff += 2**64
                else: # 32-bit
                    diff += 2**32
            
            if diff > 1000000: # +8Mbps approx
                found = True
                mbps = (diff * 8) / (5 * 1000000)
                # Map OID back to Index for better readability
                idx = oid.split('.')[-1]
                type_label = "IN" if (".10" in oid or ".6" in oid) else "OUT"
                hc_label = "HC" if "1.3.6.1.2.1.31" in oid else "32b"
                print(f"Index: {idx} | {type_label} ({hc_label}) | {mbps:.2f} Mbps | OID: {oid}")
                
    if not found:
        print("⚠️ Nenhum tráfego significativo detectado. Equipamento pode estar usando OIDs proprietários ou SNMP v1 apenas.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

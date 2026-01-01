
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
    
    # Root for ubntAirFIBER
    root = '1.3.6.1.4.1.41112.1.3'
    
    print(f"--- SCANNING AirFiber Tree: {root} ---")
    
    engine = get_shared_engine()
    
    async def scan():
        results = {}
        curr_oid = ObjectIdentity(root)
        while True:
            # errorIndication, errorStatus, errorIndex, varBindTable
            res = await nextCmd(
                engine,
                CommunityData(community, mpModel=1),
                UdpTransportTarget((target_ip, 161), timeout=2, retries=1),
                ContextData(),
                ObjectType(curr_oid),
                lexicographicMode=False
            )
            
            errorIndication, errorStatus, errorIndex, varBindTable = res
            
            if errorIndication or errorStatus or not varBindTable:
                break
            
            # varBindTable is as list of varBinds
            # Since we only passed ONE ObjectType, each element in varBindTable is a list with ONE varBind
            for varBinds in varBindTable:
                for vb in varBinds:
                    oid_obj, val_obj = vb
                    oid_str = str(oid_obj)
                    
                    if not oid_str.startswith(root):
                        return results
                    
                    try:
                        val = int(val_obj)
                        results[oid_str] = val
                    except:
                        pass
                    
                    curr_oid = oid_obj
        return results

    print("Calculando primeira amostra...")
    s1 = await scan()
    if not s1:
        print("Equipamento não respondeu na MIB AirFiber.")
        return
    
    print(f"Lidas {len(s1)} OIDs. Aguardando 5s...")
    await asyncio.sleep(5)
    
    print("Calculando segunda amostra...")
    s2 = await scan()
    
    print("\n--- TRÁFEGO DETECTADO NO PRIVATE MIB ---")
    found = False
    for oid in s2:
        if oid in s1:
            diff = s2[oid] - s1[oid]
            if diff > 1000000: # +8Mbps approx
                found = True
                mbps = (diff * 8) / (5 * 1_000_000)
                print(f"OID: {oid} -> {mbps:.2f} Mbps")
    
    if not found:
        print("⚠️ Nenhum tráfego significativo encontrado no Private MIB.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

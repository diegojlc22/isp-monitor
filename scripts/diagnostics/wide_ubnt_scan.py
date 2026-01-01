
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
    
    # Root for Ubiquiti
    root = '1.3.6.1.4.1.41112'
    
    print(f"--- WIDE SCANNING Ubiquiti Tree: {root} ---")
    
    engine = get_shared_engine()
    
    async def scan():
        results = {}
        curr_oid = ObjectIdentity(root)
        while True:
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
            
            for varBinds in varBindTable:
                for vb in varBinds:
                    oid_obj, val_obj = vb
                    oid_str = str(oid_obj)
                    
                    if not oid_str.startswith(root):
                        return results
                    
                    try:
                        val = int(val_obj)
                        # Store everything for traffic analysis
                        results[oid_str] = val
                        # print(f"Found Value: {oid_str} = {val}")
                    except:
                        # Non-numeric
                        # print(f"Info: {oid_str} = {val_obj}")
                        pass
                    
                    curr_oid = oid_obj
        return results

    print("Calculando primeira amostra...")
    s1 = await scan()
    if not s1:
        print("Equipamento não respondeu ao scan Ubiquiti Private.")
        return
    
    print(f"Lidas {len(s1)} OIDs numéricas. Aguardando 10s para tráfego...")
    await asyncio.sleep(10)
    
    print("Calculando segunda amostra...")
    s2 = await scan()
    
    print("\n--- TRÁFEGO DETECTADO NO UBNT PRIVATE MIB ---")
    found = False
    for oid in s2:
        if oid in s1:
            diff = s2[oid] - s1[oid]
            # AirFiber and AirMax often use Counter64 or big numbers.
            # We are looking for 300Mbps = 37,500,000 Bytes per second.
            if diff > 5000000: # Some threshold for 10s
                found = True
                avg_bps = (diff * 8) / 10
                mbps = avg_bps / 1_000_000
                print(f"OID: {oid} -> {mbps:.2f} Mbps")
    
    if not found:
        print("⚠️ Nenhum tráfego significativo (>4Mbps) encontrado no Private MIB.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

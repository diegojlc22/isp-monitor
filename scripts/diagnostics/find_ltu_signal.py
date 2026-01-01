
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine
from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def main():
    target_ip = "10.50.1.3"
    community = "publicRadionet"
    root = '1.3.6.1.4.1.41112.1.10'
    
    print(f"--- SCANNING SIGNAL/CCQ IN LTU TREE ({target_ip}) ---")
    engine = get_shared_engine()
    
    curr_oid = ObjectIdentity(root)
    while True:
        res = await nextCmd(
            engine, CommunityData(community, mpModel=1),
            UdpTransportTarget((target_ip, 161), timeout=2),
            ContextData(), ObjectType(curr_oid), lexicographicMode=False
        )
        errorIndication, errorStatus, errorIndex, varBindTable = res
        if errorIndication or errorStatus or not varBindTable: break
        
        for varBinds in varBindTable:
            for vb in varBinds:
                oid_obj, val_obj = vb
                oid_str = str(oid_obj)
                if not oid_str.startswith(root): return
                
                try:
                    val = int(val_obj)
                    # Look for signal values (-10 to -90) or CCQ (0-100)
                    if -100 < val < -20:
                        print(f"POSSIBLE SIGNAL: {oid_str} = {val}")
                    elif 80 <= val <= 100 and ".4.1" in oid_str: # Likely CCQ/Capacity % in StaTable
                        print(f"POSSIBLE CCQ/CAP %: {oid_str} = {val}")
                except: pass
                curr_oid = oid_obj

if __name__ == "__main__":
    asyncio.run(main())

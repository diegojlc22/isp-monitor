
import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine
from pysnmp.hlapi.asyncio import getCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def main():
    target_ip = "10.50.1.3"
    community = "publicRadionet"
    port = 161
    
    print(f"--- DEEP DEBUG AIRFIBER 5XHD: {target_ip} ---")
    print("Testando 64-bit (v2c) e 32-bit (v1) em todas as interfaces...")
    
    engine = get_shared_engine()
    
    # Interfaces detectadas anteriormente: 2 (eth0), 4 (ath0), 5 (br0), 6 (br2)
    interfaces = [2, 4, 5, 6]
    
    async def measure(idx, version_label):
        mp_model = 1 if version_label == "v2c" else 0
        
        # OIDs 64-bit (HC)
        oid_in_64 = f'1.3.6.1.2.1.31.1.1.1.6.{idx}'
        oid_out_64 = f'1.3.6.1.2.1.31.1.1.1.10.{idx}'
        
        # OIDs 32-bit
        oid_in_32 = f'1.3.6.1.2.1.2.2.1.10.{idx}'
        oid_out_32 = f'1.3.6.1.2.1.2.2.1.16.{idx}'
        
        oids = (oid_in_64, oid_out_64) if version_label == "v2c" else (oid_in_32, oid_out_32)
        
        try:
            error, status, index, varBinds = await getCmd(
                engine,
                CommunityData(community, mpModel=mp_model),
                UdpTransportTarget((target_ip, port), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oids[0])),
                ObjectType(ObjectIdentity(oids[1]))
            )
            
            if not error and not status:
                return int(varBinds[0][1]), int(varBinds[1][1])
        except:
            pass
        return None

    print(f"{'IF':<5} | {'VER':<5} | {'MBPS TOTAL':<15}")
    print("-" * 35)

    for idx in interfaces:
        for ver in ["v2c", "v1"]:
            # Leitura 1
            t1 = await measure(idx, ver)
            if t1 is None: continue
            
            await asyncio.sleep(5)
            
            # Leitura 2
            t2 = await measure(idx, ver)
            if t2 is None: continue
            
            dt = 5.0
            d_in = t2[0] - t1[0]
            d_out = t2[1] - t1[1]
            
            # Fix rollover for 32-bit
            if ver == "v1":
                if d_in < 0: d_in += 2**32
                if d_out < 0: d_out += 2**32
            else:
                # 64-bit rollover is extremely rare, but possible (2**64)
                if d_in < 0: d_in += 2**64
                if d_out < 0: d_out += 2**64
                
            mbps = ((d_in + d_out) * 8) / (dt * 1_000_000)
            print(f"{idx:<5} | {ver:<5} | {mbps:>10.2f} Mbps")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

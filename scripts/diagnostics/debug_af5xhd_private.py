
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
    
    # AirFiber Statistics Table OIDs (Based on MIB provided)
    # .1.3.6.1.4.1.41112.1.3.3.1.64 -> txoctetsAll (Counter64)
    # .1.3.6.1.4.1.41112.1.3.3.1.66 -> rxoctetsAll (Counter64)
    # Index is likely 1 for these specific radios
    index = 1
    
    oid_tx_all = f'.1.3.6.1.4.1.41112.1.3.3.1.64.{index}'
    oid_rx_all = f'.1.3.6.1.4.1.41112.1.3.3.1.66.{index}'
    
    # Also check ifHCInOctets/ifHCOutOctets for comparison if possible
    # ifHCInOctets.4 -> .1.3.6.1.2.1.31.1.1.1.6.4 (ath0 was index 4)
    
    print(f"--- AIRFIBER PRIVATE MIB MONITOR: {target_ip} ---")
    print(f"Monitorando OIDs Proprietários (Counter64)...")
    
    engine = get_shared_engine()
    
    async def get_vals():
        try:
            error, status, idx, varBinds = await getCmd(
                engine,
                CommunityData(community, mpModel=1), # v2c for Counter64
                UdpTransportTarget((target_ip, port), timeout=3, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid_tx_all)),
                ObjectType(ObjectIdentity(oid_rx_all))
            )
            if not error and not status:
                return int(varBinds[0][1]), int(varBinds[1][1])
        except Exception as e:
            print(f"Erro na leitura: {e}")
        return None

    last_tx = 0
    last_rx = 0
    last_time = 0
    
    print(f"{'SEC':<5} | {'TX RAW':<20} | {'RX RAW':<20} | {'TOTAL Mbps':<15}")
    print("-" * 75)
    
    for i in range(15):
        vals = await get_vals()
        if vals:
            curr_tx, curr_rx = vals
            now = time.time()
            
            if last_time > 0:
                dt = now - last_time
                d_tx = curr_tx - last_tx
                d_rx = curr_rx - last_rx
                
                # Counter64 rollover handling (unlikely but safe)
                if d_tx < 0: d_tx += 2**64
                if d_rx < 0: d_rx += 2**64
                
                mbps = ((d_tx + d_rx) * 8) / (dt * 1_000_000)
                print(f"{i:<5} | {curr_tx:<20} | {curr_rx:<20} | {mbps:>10.2f} Mbps")
            else:
                print(f"{i:<5} | {curr_tx:<20} | {curr_rx:<20} | ...")
            
            last_tx = curr_tx
            last_rx = curr_rx
            last_time = now
        else:
            print(f"{i:<5} | FALHA NA LEITURA")
            
        await asyncio.sleep(2)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

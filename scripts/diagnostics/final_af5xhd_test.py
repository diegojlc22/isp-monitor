
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
    
    # List of OIDs to test based on User JSON and previous Scans
    tests = [
        # LTU Branch (Detected in Scan with 300Mb+)
        ("LTU Rx Bytes", "1.3.6.1.4.1.41112.1.10.1.5.3.0"),
        ("LTU Tx Bytes", "1.3.6.1.4.1.41112.1.10.1.5.1.0"),
        ("LTU Eth Rx", "1.3.6.1.4.1.41112.1.10.1.6.3.0"),
        ("LTU Eth Tx", "1.3.6.1.4.1.41112.1.10.1.6.1.0"),
        
        # Classic AF Branch (From User JSON)
        ("Classic Tx All", "1.3.6.1.4.1.41112.1.3.3.1.64.1"),
        ("Classic Rx All", "1.3.6.1.4.1.41112.1.3.3.1.66.1"),
        ("Classic Uptime", "1.3.6.1.4.1.41112.1.3.2.1.38.1"),
        ("Classic Capacity", "1.3.6.1.4.1.41112.1.3.2.1.5.1"),
        
        # Wireless Status (LTU Station Table)
        ("LTU Sta Rx Power 0", "1.3.6.1.4.1.41112.1.10.1.4.1.5.1"), # Generic index 1 attempt
        ("LTU Sta Rx Capacity", "1.3.6.1.4.1.41112.1.10.1.4.1.4.1"),
    ]
    
    print(f"--- TESTE DE OIDS PARA AF-5XHD ({target_ip}) ---")
    engine = get_shared_engine()
    
    async def probe(name, oid):
        try:
            errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                engine,
                CommunityData(community, mpModel=1),
                UdpTransportTarget((target_ip, 161), timeout=2, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            if errorIndication:
                return f"ERROR: {errorIndication}"
            if errorStatus:
                return f"STATUS: {errorStatus}"
            if varBinds:
                return str(varBinds[0][1])
        except Exception as e:
            return f"EXCEPTION: {e}"
        return "NULL"

    print(f"{'Nome do OID':<25} | {'OID':<40} | {'Valor Inicial'}")
    print("-" * 80)
    
    results_v1 = {}
    for name, oid in tests:
        val = await probe(name, oid)
        results_v1[oid] = val
        print(f"{name:<25} | {oid:<40} | {val}")
        
    print("\nCalculando tráfego real (aguarde 5s)...")
    await asyncio.sleep(5)
    
    print(f"\n{'Nome do OID':<25} | {'Mbps / Variação'}")
    print("-" * 50)
    for name, oid in tests:
        val2 = await probe(name, oid)
        val1 = results_v1[oid]
        
        try:
            v1 = int(val1)
            v2 = int(val2)
            if v2 >= v1:
                diff = v2 - v1
                if "Bytes" in name or "Octets" in name or "All" in name or "Eth" in name:
                    mbps = (diff * 8) / (5 * 1_000_000)
                    print(f"{name:<25} | {mbps:.2f} Mbps")
                else:
                    print(f"{name:<25} | Diff: {diff}")
            else:
                 print(f"{name:<25} | Counter Reset")
        except:
             print(f"{name:<25} | N/A")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine
from pysnmp.hlapi.asyncio import *

TARGET_IP = '192.168.82.5'
COMMUNITY = "publicRadionet"
PORT = 161

async def debug_individual_connect():
    print(f"\nScanning {TARGET_IP} with community: '{COMMUNITY}'")
    
    engine = get_shared_engine()
    
    # Try v1 first (often fixes older firmwares)
    # Then v2c
    
    versions = [0, 1] # 0=v1, 1=v2c
    
    for v in versions:
        ver_name = "v1" if v == 0 else "v2c"
        print(f"\n--- Testing SNMP {ver_name} ---")
        
        auth = CommunityData(COMMUNITY, mpModel=v)
        target = UdpTransportTarget((TARGET_IP, PORT), timeout=3.0, retries=2)
        
        # Try getting System Name (standard OID)
        sysName_oid = '1.3.6.1.2.1.1.5.0'
        sysDescr_oid = '1.3.6.1.2.1.1.1.0'
        
        try:
            errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                engine, auth, target, ContextData(), ObjectType(ObjectIdentity(sysName_oid))
            )
            
            if errorIndication:
                print(f"❌ Error: {errorIndication}")
            elif errorStatus:
                print(f"❌ Error Status: {errorStatus.prettyPrint()}")
            else:
                if varBinds:
                    print(f"✅ SUCCESS! Name: {varBinds[0][1].prettyPrint()}")
                    return # Exit on success
                else:
                    print("❌ No data returned.")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_individual_connect())

import asyncio
import sys
import os

# Add root path
sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine
from pysnmp.hlapi.asyncio import *

TARGET_IP = "192.168.103.2"
COMMUNITY = "publicRadionet"
PORT = 161
INTERFACE_IDX = 10 # sfp-sfpplus1

async def get_oid(oid):
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(COMMUNITY, mpModel=1), # v2c
            UdpTransportTarget((TARGET_IP, PORT), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        if errorIndication:
            return f"Error: {errorIndication}"
        elif errorStatus:
            return f"Error: {errorStatus.prettyPrint()}"
        else:
            return varBinds[0][1]
    except Exception as e:
        return f"Exception: {e}"

async def debug_sfp():
    print(f"🔍 Diagnosticando SFP do Mikrotik {TARGET_IP} (Index: {INTERFACE_IDX})...")
    
    oids = {
        "Rx Power (.10)": f"1.3.6.1.4.1.14988.1.1.19.1.1.10.{INTERFACE_IDX}",
        "Tx Power (.11)": f"1.3.6.1.4.1.14988.1.1.19.1.1.11.{INTERFACE_IDX}",
        "Temperature (.5)": f"1.3.6.1.4.1.14988.1.1.19.1.1.5.{INTERFACE_IDX}",
        "Voltage (.6)": f"1.3.6.1.4.1.14988.1.1.19.1.1.6.{INTERFACE_IDX}",
        "Current (.7)": f"1.3.6.1.4.1.14988.1.1.19.1.1.7.{INTERFACE_IDX}",
    }

    print("-" * 60)
    for name, oid in oids.items():
        val = await get_oid(oid)
        print(f"{name:<20} | OID: {oid:<35} | VAL: {val}")
    print("-" * 60)
    print("Se VAL for inteiro (ex: -4000), a fórmula divide por 1000 (= -4.0 dBm).")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_sfp())


import asyncio
import sys
import os
import math

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.services.wireless_snmp import _snmp_get, detect_brand, detect_equipment_name
from pysnmp.hlapi.asyncio import *

def linear_to_dbm(mw):
    if mw <= 0: return -99.9
    return round(10 * math.log10(mw/1000.0), 3)

async def snmp_walk_full(ip, community, root_oid, port=161):
    results = []
    engine = SnmpEngine()
    target = UdpTransportTarget((ip, port), timeout=3, retries=1)
    auth = CommunityData(community, mpModel=1)
    current_oid = ObjectIdentity(root_oid)
    while True:
        try:
            errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
                engine, auth, target, ContextData(), ObjectType(current_oid), lexicographicMode=False
            )
            if errorIndication or errorStatus or not varBinds: break
            for varBind in varBinds:
                oid, value = varBind[0]
                if not str(oid).startswith(root_oid): return results
                results.append((str(oid), value))
                current_oid = oid
        except: break
    return results

async def run_discovery(ip, community):
    print(f"\n" + "═"*70)
    print(f"🚀 FERRAMENTA DE DESCOBERTA SNMP: {ip}")
    print("═"*70)

    # 1. Basic Info
    name = await detect_equipment_name(ip, community)
    brand = await detect_brand(ip, community)
    if not brand:
        print("❌ Equipamento não respondeu ou Community incorreta.")
        return

    print(f"📍 Nome: {name}")
    print(f"🏷️ Marca: {brand.upper()}")

    # 2. Interfaces
    print("\n🔍 Mapeando Interfaces (ifName/ifDescr)...")
    if_info = {}
    names = await snmp_walk_full(ip, community, '1.3.6.1.2.1.2.2.1.2')
    for oid, val in names:
        idx = oid.split('.')[-1]
        if_info[idx] = str(val)
        print(f"   ID {idx.ljust(3)}: {val}")

    # 3. Fiber/SFP Specifics
    if brand == 'mikrotik':
        print("\n📦 Analisando Hardware Mikrotik (SFP Monitor)...")
        # New SFP monitor table (.19)
        mon_table = await snmp_walk_full(ip, community, '1.3.6.1.4.1.14988.1.1.19.1.1')
        data = {}
        for oid, val in mon_table:
            parts = oid.split('.')
            field, idx = parts[-2], parts[-1]
            if idx not in data: data[idx] = {}
            data[idx][field] = val
        
        for idx, fields in data.items():
            name = if_info.get(idx, f"SFP {idx}")
            print(f"\n✨ {name}:")
            rx_dbm_x1000 = fields.get('10')
            tx_dbm_x1000 = fields.get('9')
            temp_x10 = fields.get('6')
            
            if rx_dbm_x1000 is not None:
                print(f"   📥 RX Power: {round(float(rx_dbm_x1000)/1000.0, 2)} dBm")
            if tx_dbm_x1000 is not None:
                print(f"   📤 TX Power: {round(float(tx_dbm_x1000)/1000.0, 2)} dBm")
            if temp_x10 is not None:
                print(f"   🌡️ Temp: {float(temp_x10)/10.0} C")

    print("\n✅ Descoberta Finalizada.")

async def main():
    if len(sys.argv) < 2:
        print("Uso: python ferramentas/snmp_discovery.py <IP> [COMMUNITY]")
        return
    ip = sys.argv[1]
    community = sys.argv[2] if len(sys.argv) > 2 else "publicRadionet"
    await run_discovery(ip, community)

if __name__ == "__main__":
    asyncio.run(main())

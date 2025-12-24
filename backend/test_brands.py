import asyncio
from pysnmp.hlapi.asyncio import *

# Targets provided by user
TARGETS = [
    {"name": "Ubiquiti Painel", "ip": "192.168.47.35", "brand": "ubiquiti"}
]

COMMUNITIES = ["publicRadionet", "public", "giga"]

# Common OIDs for Wireless Signal
OIDS = {
    "ubiquiti_signal": "1.3.6.1.4.1.41112.1.4.5.1.5.1",      # Ubiquiti AirMax Signal
    "ubiquiti_ccq": "1.3.6.1.4.1.41112.1.4.5.1.7.1",         # Ubiquiti CCQ
    "generic_interface": "1.3.6.1.2.1.2.2.1.2.1",            # Interface Name (generic)
    "mikrotik_signal": "1.3.6.1.4.1.14988.1.1.1.1.1.4.5"     # Just for ref
}

async def get_snmp(ip, community, oid):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if errorIndication:
            return None, str(errorIndication)
        elif errorStatus:
            return None, errorStatus.prettyPrint()
        else:
            for varBind in varBinds:
                return varBind[1], None
    except Exception as e:
        return None, str(e)
    return None, "Unknown"

async def scan():
    print("--- INICIANDO DIAGNOSTICO SNMP ---")
    
    for target in TARGETS:
        print(f"\n[?] Testando {target['name']} ({target['ip']})...")
        alive = False
        valid_community = None
        
        # 1. Discover Community
        for comm in COMMUNITIES:
            print(f"    > Tentando community '{comm}'...", end=" ")
            val, err = await get_snmp(target['ip'], comm, "1.3.6.1.2.1.1.1.0") # SysDescr
            if val:
                print(f"SUCESSO! (Modelo detected: {str(val)[:30]}...)")
                valid_community = comm
                alive = True
                break
            else:
                print(f"Falha.")
        
        if not alive:
            print(f"    [X] Nao respondeu SNMP. Verifique se a porta 161 esta aberta e a community.")
            continue
            
        # 2. Try Specific Signal OIDs
        print(f"    > Buscando Sinal dBm com community '{valid_community}'...")
        
        # Test Ubiquiti OID
        val, err = await get_snmp(target['ip'], valid_community, OIDS['ubiquiti_signal'])
        if val:
            print(f"      [UBIQUITI] Sinal encontrado: {val} dBm")
        else:
             print(f"      [UBIQUITI] OID padrao falhou.")

        # Test Generic/Intelbras methods (often mapped differently)
        # Intelbras WOM often mimics Mikrotik or uses standard Wifi MIBs
        
    print("\n--- FIM ---")

if __name__ == "__main__":
    asyncio.run(scan())

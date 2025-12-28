import asyncio
from pysnmp.hlapi.asyncio import *

IP = "192.168.108.51"
COMMUNITY = "publicRadionet" # User provided

async def test_snmp():
    print(f"Testing connectivity to {IP}...")
    
    # 1. Try generic system description (OID 1.3.6.1.2.1.1.1.0)
    print("- Tentando SNMP Comunit 'public' para Descrição do Sistema...")
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=0), # v1
            UdpTransportTarget((IP, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        )
        if errorIndication:
            print(f"❌ Falha SNMP: {errorIndication}")
        elif errorStatus:
             print(f"❌ Erro SNMP: {errorStatus}")
        else:
             desc = varBinds[0][1]
             print(f"✅ Sucesso! Descrição: {desc}")
             
    except Exception as e:
        print(f"❌ Exceção: {e}")

if __name__ == "__main__":
    asyncio.run(test_snmp())

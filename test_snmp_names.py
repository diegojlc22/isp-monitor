"""
Script para testar detecção de nome via SNMP - Com community correta
"""
import asyncio
from pysnmp.hlapi.asyncio import *

async def get_snmp_info(ip, community='publicRadionet', port=161):
    """Tenta obter informações do equipamento via SNMP"""
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),  # SNMPv1
            UdpTransportTarget((ip, port), timeout=5, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),  # sysName
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))   # sysDescr
        )
        
        if errorIndication:
            print(f"❌ {ip}: {errorIndication}")
            return None
        elif errorStatus:
            print(f"❌ {ip}: {errorStatus.prettyPrint()}")
            return None
        else:
            name = str(varBinds[0][1])
            descr = str(varBinds[1][1])
            print(f"✅ {ip}:")
            print(f"   Nome: '{name}'")
            print(f"   Descrição: {descr[:80]}...")
            return name
            
    except Exception as e:
        print(f"❌ {ip}: {e}")
        return None

async def main():
    ips = [
        "192.168.108.51",
        "192.168.49.70",
        "192.168.103.132",
        "192.168.148.201",
        "192.168.49.81"
    ]

    print("=" * 70)
    print("TESTE DE DETECÇÃO DE NOME VIA SNMP")
    print("Community: publicRadionet")
    print("=" * 70)
    print()

    for ip in ips:
        await get_snmp_info(ip)
        print()

if __name__ == "__main__":
    asyncio.run(main())

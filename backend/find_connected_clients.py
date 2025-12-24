"""
🔍 DESCOBRIR CLIENTES CONECTADOS NO TRANSMISSOR UBIQUITI
Testa OIDs para encontrar número de clientes wireless
"""
import asyncio
from pysnmp.hlapi.asyncio import getCmd, nextCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

TARGET_IP = "192.168.47.35"
COMMUNITY = "publicRadionet"

# OIDs conhecidos para Ubiquiti
OIDS_TO_TEST = {
    # Ubiquiti AirMAX MIB
    'Ubiquiti - Station Count': '1.3.6.1.4.1.41112.1.4.7.1.1.1',  # ubntStaCount
    'Ubiquiti - Wireless Clients': '1.3.6.1.4.1.41112.1.4.5.1.15.1',  # ubntWlStatStaCount
    
    # Generic Wireless MIBs
    'IEEE 802.11 - Associated Stations': '1.3.6.1.2.1.1.1.0',
    
    # Mikrotik MIB (caso seja WOM/APC com firmware Mikrotik)
    'Mikrotik - Registered Clients': '1.3.6.1.4.1.14988.1.1.1.3.1.6',
    
    # Interface Statistics
    'Interface Users Count': '1.3.6.1.2.1.2.2.1.22.5',  # ifSpecific para ath0
}

async def test_oid(name, oid):
    """Testa um OID específico"""
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=0),  # v1
            UdpTransportTarget((TARGET_IP, 161), timeout=3.0, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        
        if not errorIndication and not errorStatus:
            value = varBinds[0][1]
            return {'name': name, 'oid': oid, 'value': str(value), 'success': True}
        else:
            return {'name': name, 'oid': oid, 'value': None, 'success': False, 'error': str(errorIndication or errorStatus)}
    except Exception as e:
        return {'name': name, 'oid': oid, 'value': None, 'success': False, 'error': str(e)}

async def walk_wireless_table():
    """Faz um SNMP Walk na tabela wireless para contar clientes"""
    print("\n[WALK] Explorando tabela de clientes wireless...")
    
    # Base OID para tabela de estações Ubiquiti
    base_oid = '1.3.6.1.4.1.41112.1.4.7.1'  # ubntStaTable
    
    clients = []
    try:
        async for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=0),
            UdpTransportTarget((TARGET_IP, 161), timeout=3.0),
            ContextData(),
            ObjectType(ObjectIdentity(base_oid)),
            lexicographicMode=False
        ):
            if errorIndication or errorStatus:
                break
            
            for varBind in varBinds:
                oid = str(varBind[0])
                value = str(varBind[1])
                
                # Se encontrar MAC address (formato específico)
                if len(value) > 10 and ':' in value:
                    clients.append({'oid': oid, 'mac': value})
                    print(f"    → Cliente encontrado: {value}")
        
        return clients
    except Exception as e:
        print(f"    ✗ Erro no walk: {e}")
        return []

async def get_station_list():
    """Tenta obter lista de estações conectadas via diferentes métodos"""
    print("\n[MÉTODO 2] Tentando obter lista de MACs conectados...")
    
    # OID base para MAC addresses de clientes
    mac_table_oids = [
        '1.3.6.1.4.1.41112.1.4.7.1.2',  # ubntStaMac
        '1.3.6.1.2.1.4.22.1.2',  # ipNetToMediaPhysAddress (ARP table)
    ]
    
    for base_oid in mac_table_oids:
        print(f"\n    Testando OID base: {base_oid}")
        count = 0
        
        try:
            async for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(COMMUNITY, mpModel=0),
                UdpTransportTarget((TARGET_IP, 161), timeout=3.0),
                ContextData(),
                ObjectType(ObjectIdentity(base_oid)),
                lexicographicMode=False,
                maxRows=50  # Limitar para não demorar muito
            ):
                if errorIndication or errorStatus:
                    break
                
                for varBind in varBinds:
                    value = str(varBind[1])
                    # Detectar MAC address (formato hex ou string)
                    if len(value) >= 12:
                        count += 1
                        if count <= 5:  # Mostrar apenas os primeiros 5
                            print(f"      [{count}] {value}")
            
            if count > 0:
                print(f"\n    ✅ Total encontrado: {count} entradas")
                return count
                
        except Exception as e:
            print(f"    ✗ Erro: {e}")
    
    return 0

async def main():
    print("="*70)
    print("🔍 DESCOBRINDO NÚMERO DE CLIENTES CONECTADOS")
    print("="*70)
    print(f"\n📡 Transmissor: {TARGET_IP}")
    print(f"🔑 Community: {COMMUNITY}\n")
    
    # Método 1: Testar OIDs conhecidos
    print("[MÉTODO 1] Testando OIDs conhecidos para contagem de clientes...")
    
    results = []
    for name, oid in OIDS_TO_TEST.items():
        result = await test_oid(name, oid)
        results.append(result)
        
        if result['success']:
            print(f"  ✅ {name}")
            print(f"     OID: {oid}")
            print(f"     Valor: {result['value']}")
        else:
            print(f"  ❌ {name} - {result.get('error', 'Sem resposta')}")
    
    # Método 2: Walk na tabela de clientes
    clients_walk = await walk_wireless_table()
    
    # Método 3: Lista de MACs
    clients_count = await get_station_list()
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    
    if successful:
        print(f"\n✅ {len(successful)} OID(s) funcionando:")
        for r in successful:
            print(f"\n   📌 {r['name']}")
            print(f"      OID: {r['oid']}")
            print(f"      Valor: {r['value']}")
            
            # Tentar interpretar o valor
            try:
                num_value = int(r['value'])
                if num_value > 0:
                    print(f"      🎯 CLIENTES CONECTADOS: {num_value}")
            except:
                pass
    
    if clients_walk:
        print(f"\n✅ Walk encontrou {len(clients_walk)} cliente(s)")
    
    if clients_count > 0:
        print(f"\n✅ Lista de MACs encontrou {clients_count} entrada(s)")
    
    if not successful and not clients_walk and clients_count == 0:
        print("\n⚠️  Nenhum método retornou dados de clientes")
        print("\nPossíveis razões:")
        print("  • Este equipamento pode ser um Cliente (CPE), não um AP")
        print("  • O firmware não expõe essas informações via SNMP")
        print("  • Nenhum cliente conectado no momento")
        print("\n💡 Dica: Acesse a interface web e verifique se há clientes conectados")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

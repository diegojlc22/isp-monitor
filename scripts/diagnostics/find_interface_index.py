"""
🔍 DESCOBRIR INTERFACE INDEX CORRETO
Testa múltiplos índices de interface para encontrar o correto
"""
import asyncio
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

TARGET_IP = "192.168.47.35"
COMMUNITY = "publicRadionet"

async def test_interface(index):
    """Testa um índice de interface específico"""
    try:
        # Testar ifDescr (nome da interface)
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=0),  # v1
            UdpTransportTarget((TARGET_IP, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.2.{index}')),  # ifDescr
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.10.{index}')), # ifInOctets
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.16.{index}'))  # ifOutOctets
        )
        
        if not errorIndication and not errorStatus:
            desc = str(varBinds[0][1])
            in_bytes = int(varBinds[1][1])
            out_bytes = int(varBinds[2][1])
            
            if in_bytes > 0 or out_bytes > 0:
                return {
                    'index': index,
                    'desc': desc,
                    'in': in_bytes,
                    'out': out_bytes,
                    'active': True
                }
            else:
                return {
                    'index': index,
                    'desc': desc,
                    'in': in_bytes,
                    'out': out_bytes,
                    'active': False
                }
    except:
        pass
    
    return None

async def main():
    print("="*70)
    print("🔍 DESCOBRINDO INTERFACES DISPONÍVEIS")
    print("="*70)
    print(f"\n📡 Alvo: {TARGET_IP}")
    print(f"🔑 Community: {COMMUNITY}\n")
    
    print("Testando índices de 1 a 20...\n")
    
    interfaces = []
    for i in range(1, 21):
        result = await test_interface(i)
        if result:
            interfaces.append(result)
            status = "🟢 ATIVA" if result['active'] else "⚪ INATIVA"
            print(f"[{i:2d}] {status} - {result['desc']}")
            print(f"     📥 In:  {result['in']:,} bytes")
            print(f"     📤 Out: {result['out']:,} bytes")
    
    if interfaces:
        print("\n" + "="*70)
        print("📊 RESUMO")
        print("="*70)
        
        active = [i for i in interfaces if i['active']]
        if active:
            print(f"\n✅ {len(active)} interface(s) ativa(s) encontrada(s):")
            for iface in active:
                print(f"   → Index {iface['index']}: {iface['desc']}")
            
            print(f"\n💡 RECOMENDAÇÃO:")
            print(f"   Use snmp_interface_index = {active[0]['index']} no equipamento")
        else:
            print(f"\n⚠️  {len(interfaces)} interface(s) encontrada(s), mas nenhuma com tráfego")
            print(f"   Isso pode ser normal se o equipamento acabou de reiniciar")
    else:
        print("\n❌ Nenhuma interface encontrada")
        print("   Verifique se o SNMP está habilitado corretamente")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

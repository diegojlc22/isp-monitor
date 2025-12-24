"""
🔍 DIAGNÓSTICO COMPLETO DE SNMP
Testa conectividade, portas, versões e fornece soluções
"""
import asyncio
import socket
import subprocess
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

# ===== CONFIGURAÇÃO =====
TARGET_IP = "192.168.47.35"
COMMUNITY = "publicRadionet"
PORT = 161
# ========================

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(num, text):
    print(f"\n[{num}] {text}")

def print_success(text):
    print(f"    ✅ {text}")

def print_error(text):
    print(f"    ❌ {text}")

def print_info(text):
    print(f"    ℹ️  {text}")

# ===== TESTES =====

async def test_ping():
    """Teste 1: Conectividade ICMP"""
    print_step(1, "Testando conectividade ICMP (ping)")
    try:
        result = subprocess.run(
            ["ping", "-n", "2", TARGET_IP],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print_success(f"Ping para {TARGET_IP} funcionando")
            return True
        else:
            print_error(f"Ping falhou para {TARGET_IP}")
            return False
    except Exception as e:
        print_error(f"Erro ao executar ping: {e}")
        return False

async def test_port_open():
    """Teste 2: Porta UDP 161 acessível"""
    print_step(2, f"Testando porta UDP {PORT}")
    print_info("Nota: UDP não garante resposta, mas vamos tentar...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.sendto(b"test", (TARGET_IP, PORT))
        print_info("Pacote UDP enviado (sem confirmação de recebimento)")
        sock.close()
        return True
    except Exception as e:
        print_error(f"Erro ao testar porta UDP: {e}")
        return False

async def test_snmp_version(version_name, mp_model):
    """Teste genérico de versão SNMP"""
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=mp_model),
            UdpTransportTarget((TARGET_IP, PORT), timeout=5.0, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )
        
        if errorIndication:
            error_type = type(errorIndication).__name__
            print_error(f"{version_name} falhou: {errorIndication}")
            
            # Diagnóstico específico
            if "timeout" in str(errorIndication).lower():
                print_info("TIMEOUT = Dispositivo não respondeu")
                print_info("Possíveis causas:")
                print_info("  • SNMP desabilitado no equipamento")
                print_info("  • Firewall bloqueando UDP 161")
                print_info("  • Community string incorreta")
                print_info("  • IP do servidor bloqueado no ACL")
            
            return False
            
        elif errorStatus:
            print_error(f"{version_name} erro de status: {errorStatus.prettyPrint()}")
            return False
        else:
            for varBind in varBinds:
                print_success(f"{version_name} FUNCIONANDO!")
                print_info(f"Descrição do sistema: {varBind[1]}")
            return True
            
    except Exception as e:
        print_error(f"{version_name} exceção: {e}")
        return False

async def test_snmp_v1():
    """Teste 3: SNMP v1"""
    print_step(3, "Testando SNMP v1")
    return await test_snmp_version("SNMPv1", 0)

async def test_snmp_v2c():
    """Teste 4: SNMP v2c"""
    print_step(4, "Testando SNMP v2c")
    return await test_snmp_version("SNMPv2c", 1)

async def test_wireless_oids():
    """Teste 5: OIDs específicos Ubiquiti"""
    print_step(5, "Testando OIDs Ubiquiti (Signal/CCQ)")
    
    oids_to_test = {
        'Signal (dBm)': '1.3.6.1.4.1.41112.1.4.5.1.5.1',
        'CCQ (%)': '1.3.6.1.4.1.41112.1.4.5.1.7.1',
        'Interface Traffic In': '1.3.6.1.2.1.2.2.1.10.1',
        'Interface Traffic Out': '1.3.6.1.2.1.2.2.1.16.1'
    }
    
    success_count = 0
    for name, oid in oids_to_test.items():
        try:
            errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                SnmpEngine(),
                CommunityData(COMMUNITY, mpModel=1),  # v2c
                UdpTransportTarget((TARGET_IP, PORT), timeout=3.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            
            if not errorIndication and not errorStatus:
                value = varBinds[0][1]
                print_success(f"{name}: {value}")
                success_count += 1
            else:
                print_error(f"{name}: Não disponível")
                
        except Exception as e:
            print_error(f"{name}: Erro - {e}")
    
    return success_count > 0

def print_solutions():
    """Imprime soluções baseadas nos resultados"""
    print_header("🔧 SOLUÇÕES RECOMENDADAS")
    
    print("\n📋 CHECKLIST - Execute na ordem:")
    print("\n1️⃣  ACESSAR INTERFACE WEB DO UBIQUITI")
    print(f"    → Abra: http://{TARGET_IP}")
    print("    → Faça login com suas credenciais")
    
    print("\n2️⃣  HABILITAR SNMP")
    print("    → Vá em: Services → SNMP")
    print("    → Marque: ☑ Enable SNMP Agent")
    print(f"    → Community: {COMMUNITY}")
    print("    → SNMP Version: v2c (recomendado)")
    print("    → SNMP Port: 161")
    
    print("\n3️⃣  CONFIGURAR ACESSO")
    print("    → Allowed IPs: (deixe VAZIO para permitir todos)")
    print("    → OU adicione o IP do servidor: 192.168.3.10")
    print("    → SALVE as configurações")
    
    print("\n4️⃣  VERIFICAR FIREWALL DO SERVIDOR")
    print("    → Abra PowerShell como Administrador")
    print("    → Execute:")
    print("      New-NetFirewallRule -DisplayName 'SNMP Monitor' -Direction Inbound -Protocol UDP -LocalPort 161 -Action Allow")
    
    print("\n5️⃣  TESTAR NOVAMENTE")
    print("    → Execute este script novamente")
    print("    → Ou use: python backend/test_snmp_deep.py")
    
    print("\n6️⃣  SE AINDA NÃO FUNCIONAR")
    print("    → Verifique se há roteador/switch entre as redes")
    print("    → Confirme que não há VLAN isolando as redes")
    print("    → Teste com uma community diferente (ex: 'public')")
    print("    → Verifique logs do equipamento Ubiquiti")

async def main():
    print_header("🔍 DIAGNÓSTICO COMPLETO DE SNMP")
    print(f"\n📡 Alvo: {TARGET_IP}")
    print(f"🔑 Community: {COMMUNITY}")
    print(f"🔌 Porta: {PORT}")
    
    results = {}
    
    # Executar testes
    results['ping'] = await test_ping()
    results['port'] = await test_port_open()
    results['snmp_v1'] = await test_snmp_v1()
    results['snmp_v2c'] = await test_snmp_v2c()
    
    # Se algum SNMP funcionou, testar OIDs
    if results['snmp_v1'] or results['snmp_v2c']:
        results['oids'] = await test_wireless_oids()
    
    # Resumo
    print_header("📊 RESUMO DOS TESTES")
    print(f"\n✅ Ping (ICMP):        {'OK' if results['ping'] else 'FALHOU'}")
    print(f"✅ Porta UDP 161:      {'Testada' if results['port'] else 'FALHOU'}")
    print(f"✅ SNMP v1:            {'FUNCIONANDO' if results['snmp_v1'] else 'FALHOU'}")
    print(f"✅ SNMP v2c:           {'FUNCIONANDO' if results['snmp_v2c'] else 'FALHOU'}")
    
    if results['snmp_v1'] or results['snmp_v2c']:
        print(f"✅ OIDs Ubiquiti:      {'FUNCIONANDO' if results.get('oids') else 'PARCIAL'}")
        print("\n🎉 SUCESSO! SNMP está funcionando!")
        print("   Você pode usar o sistema de monitoramento normalmente.")
    else:
        print("\n⚠️  SNMP NÃO ESTÁ FUNCIONANDO")
        print("   Siga as soluções abaixo:")
        print_solutions()
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

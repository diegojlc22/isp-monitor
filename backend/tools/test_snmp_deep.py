import asyncio
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import socket

TARGET_IP = "192.168.47.35"
COMMUNITY = "publicRadionet"

print("=" * 60)
print("DIAGNOSTICO PROFUNDO SNMP")
print("=" * 60)
print()

# 1. Teste de conectividade básica
print("[1] Testando conectividade de rede...")
print(f"    IP Alvo: {TARGET_IP}")
print(f"    Community: {COMMUNITY}")
print()

# 2. Resolver DNS/IP
try:
    ip_resolved = socket.gethostbyname(TARGET_IP)
    print(f"    ✓ IP resolvido: {ip_resolved}")
except Exception as e:
    print(f"    ✗ Erro ao resolver IP: {e}")
print()

# 3. Testar SNMP v1
print("[2] Testando SNMP v1...")
async def test_v1():
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=0),  # v1
            UdpTransportTarget((TARGET_IP, 161), timeout=5.0, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )
        
        if errorIndication:
            print(f"    ✗ Erro: {errorIndication}")
            return False
        elif errorStatus:
            print(f"    ✗ Status: {errorStatus.prettyPrint()}")
            return False
        else:
            for varBind in varBinds:
                print(f"    ✓ SUCESSO! Resposta: {varBind[1]}")
            return True
    except Exception as e:
        print(f"    ✗ Exceção: {e}")
        return False

asyncio.run(test_v1())
print()

# 4. Testar SNMP v2c
print("[3] Testando SNMP v2c...")
async def test_v2c():
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=1),  # v2c
            UdpTransportTarget((TARGET_IP, 161), timeout=5.0, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
        )
        
        if errorIndication:
            print(f"    ✗ Erro: {errorIndication}")
            print(f"    Detalhes: {type(errorIndication).__name__}")
            return False
        elif errorStatus:
            print(f"    ✗ Status: {errorStatus.prettyPrint()}")
            return False
        else:
            for varBind in varBinds:
                print(f"    ✓ SUCESSO! Resposta: {varBind[1]}")
            return True
    except Exception as e:
        print(f"    ✗ Exceção: {e}")
        return False

asyncio.run(test_v2c())
print()

# 5. Diagnóstico de erro comum
print("[4] Possíveis causas do problema:")
print()
print("    Se ambos v1 e v2c falharam com 'Request timed out':")
print("    → O rádio NÃO está respondendo SNMP")
print()
print("    Causas prováveis:")
print("    1. SNMP desabilitado no rádio")
print("    2. Community incorreta (verifique espaços/maiúsculas)")
print("    3. Firewall no rádio bloqueando IP 192.168.3.10")
print("    4. Roteador/switch entre as redes bloqueando UDP 161")
print()
print("    AÇÃO NECESSÁRIA:")
print("    → Acesse http://192.168.47.35")
print("    → Services → SNMP")
print("    → Enable SNMP Agent: ☑")
print("    → Community: publicRadionet")
print("    → Allowed IPs: (vazio) ou adicione 192.168.3.10")
print("    → SAVE")
print()
print("=" * 60)

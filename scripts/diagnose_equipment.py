"""
Diagnóstico específico para 192.168.103.67
Verifica se o tráfego está sendo coletado e salvo corretamente
"""
import requests
import time

IP = "192.168.103.67"

print("="*80)
print(f"🔍 DIAGNÓSTICO: {IP}")
print("="*80)

# 1. Buscar equipamento
print("\n1️⃣ Buscando equipamento...")
r = requests.get('http://localhost:8000/api/equipments/')
equipments = r.json()
eq = [e for e in equipments if e['ip'] == IP]

if not eq:
    print(f"❌ Equipamento {IP} não encontrado!")
    exit(1)

eq = eq[0]
print(f"✅ Encontrado: ID {eq['id']} - {eq['name']}")

# 2. Verificar configuração
print("\n2️⃣ Verificando configuração...")
print(f"   Interface SINAL: {eq.get('snmp_interface_index')}")
print(f"   Interface TRÁFEGO: {eq.get('snmp_traffic_interface_index')}")
print(f"   Community: {eq.get('snmp_community')}")
print(f"   Porta SNMP: {eq.get('snmp_port')}")

if not eq.get('snmp_traffic_interface_index'):
    print("   ⚠️ Interface de tráfego NÃO configurada!")
else:
    print(f"   ✅ Interface {eq['snmp_traffic_interface_index']} configurada")

# 3. Verificar valores atuais
print("\n3️⃣ Valores atuais no banco:")
print(f"   Tráfego IN: {eq.get('last_traffic_in')} Mbps")
print(f"   Tráfego OUT: {eq.get('last_traffic_out')} Mbps")
print(f"   Sinal: {eq.get('signal_dbm')} dBm")
print(f"   Online: {eq.get('is_online')}")

if eq.get('last_traffic_in') is None or eq.get('last_traffic_in') == 0:
    print("   ⚠️ Tráfego está em 0 ou NULL!")

# 4. Aguardar 10 segundos e verificar novamente
print("\n4️⃣ Aguardando 10 segundos para próxima coleta...")
for i in range(10, 0, -1):
    print(f"   {i}...", end='\r')
    time.sleep(1)

print("\n\n5️⃣ Verificando novamente...")
r = requests.get('http://localhost:8000/api/equipments/')
equipments = r.json()
eq_new = [e for e in equipments if e['ip'] == IP][0]

print(f"   Tráfego IN: {eq_new.get('last_traffic_in')} Mbps (antes: {eq.get('last_traffic_in')})")
print(f"   Tráfego OUT: {eq_new.get('last_traffic_out')} Mbps (antes: {eq.get('last_traffic_out')})")

if eq_new.get('last_traffic_in') != eq.get('last_traffic_in'):
    print("   ✅ TRÁFEGO ESTÁ SENDO ATUALIZADO!")
else:
    print("   ❌ Tráfego NÃO está sendo atualizado")
    print("\n   Possíveis causas:")
    print("   - Collector não está rodando")
    print("   - Interface configurada não tem tráfego")
    print("   - Erro de SNMP (community/porta incorreta)")

# 6. Testar auto-configuração
print("\n6️⃣ Quer testar auto-configuração? (Isso pode demorar)")
print(f"   URL: POST http://localhost:8000/api/equipments/{eq['id']}/auto-configure-traffic")
print("\n   Execute manualmente:")
print(f"   curl -X POST http://localhost:8000/api/equipments/{eq['id']}/auto-configure-traffic")

print("\n" + "="*80)
print("✅ DIAGNÓSTICO CONCLUÍDO")
print("="*80)

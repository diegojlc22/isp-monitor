"""
🧪 TESTE MANUAL DO MONITOR SNMP
Executa uma única iteração do monitor para ver se há erros
"""
import asyncio
import sys
sys.path.insert(0, 'c:/diegolima/isp-monitor')

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.wireless_snmp import get_wireless_stats, get_connected_clients_count
from backend.app.services.snmp import get_snmp_interface_traffic
from sqlalchemy import select

async def test_snmp_monitor():
    print("="*70)
    print("🧪 TESTE MANUAL DO MONITOR SNMP")
    print("="*70)
    
    async with AsyncSessionLocal() as session:
        # Buscar apenas o equipamento Ubiquiti
        result = await session.execute(
            select(Equipment).where(Equipment.ip == '192.168.47.35')
        )
        eq = result.scalar_one_or_none()
        
        if not eq:
            print("❌ Equipamento 192.168.47.35 não encontrado!")
            return
        
        print(f"\n📌 Testando: {eq.name} ({eq.ip})")
        print(f"   Brand: {eq.brand}")
        print(f"   Community: {eq.snmp_community}")
        print(f"   SNMP Version: v{eq.snmp_version}")
        print(f"   Interface Index: {eq.snmp_interface_index}")
        print()
        
        # Teste 1: Wireless Stats (Signal/CCQ)
        print("[1] Testando get_wireless_stats...")
        try:
            w_stats = await get_wireless_stats(
                eq.ip,
                eq.brand,
                eq.snmp_community,
                eq.snmp_port or 161
            )
            print(f"    ✅ Resultado: {w_stats}")
            if w_stats['signal_dbm']:
                print(f"       📶 Signal: {w_stats['signal_dbm']} dBm")
                print(f"       📊 CCQ: {w_stats['ccq']}%")
            else:
                print(f"       ⚠️  Sem dados de signal/CCQ")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        
        print()
        
        # Teste 2: Connected Clients
        print("[2] Testando get_connected_clients_count...")
        try:
            clients = await get_connected_clients_count(
                eq.ip,
                eq.brand,
                eq.snmp_community,
                eq.snmp_port or 161
            )
            print(f"    ✅ Resultado: {clients}")
            if clients is not None:
                print(f"       👥 Clientes Conectados: {clients}")
            else:
                print(f"       ⚠️  Sem dados de clientes")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        
        print()
        
        # Teste 3: Traffic
        print(f"[3] Testando get_snmp_interface_traffic (index {eq.snmp_interface_index})...")
        try:
            traffic = await get_snmp_interface_traffic(
                eq.ip,
                community=eq.snmp_community,
                port=eq.snmp_port or 161,
                interface_index=eq.snmp_interface_index
            )
            print(f"    ✅ Resultado: {traffic}")
            if traffic:
                in_bytes, out_bytes = traffic
                print(f"       📥 In: {in_bytes:,} bytes")
                print(f"       📤 Out: {out_bytes:,} bytes")
            else:
                print(f"       ⚠️  Sem dados de tráfego")
                print(f"       💡 Dica: Tente interface_index=5 (ath0 wireless)")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        
        print()
        print("="*70)
        print("📋 DIAGNÓSTICO:")
        print("="*70)
        
        if w_stats.get('signal_dbm'):
            print("✅ Wireless Stats funcionando!")
        else:
            print("❌ Wireless Stats NÃO está funcionando")
            print("   Possíveis causas:")
            print("   - SNMP desabilitado no equipamento")
            print("   - Community string incorreta")
            print("   - Firewall bloqueando")
        
        if clients is not None and clients > 0:
            print("✅ Clientes Conectados funcionando!")
        else:
            print("⚠️  Clientes Conectados retornou 0 ou None")
        
        if traffic:
            print("✅ Tráfego funcionando!")
        else:
            print("❌ Tráfego NÃO está funcionando")
            print(f"   Interface Index atual: {eq.snmp_interface_index}")
            print("   💡 Sugestão: Altere para index 5 (ath0 wireless)")

if __name__ == "__main__":
    asyncio.run(test_snmp_monitor())

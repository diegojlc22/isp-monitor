"""
🔧 FORÇAR ATUALIZAÇÃO DO EQUIPAMENTO UBIQUITI
Atualiza manualmente os dados SNMP no banco de dados
"""
import asyncio
import sys
sys.path.insert(0, 'c:/diegolima/isp-monitor')

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.wireless_snmp import get_wireless_stats, get_connected_clients_count
from backend.app.services.snmp import get_snmp_interface_traffic
from sqlalchemy import select

async def force_update():
    print("="*70)
    print("🔧 FORÇANDO ATUALIZAÇÃO DO EQUIPAMENTO UBIQUITI")
    print("="*70)
    
    async with AsyncSessionLocal() as session:
        # Buscar equipamento Ubiquiti
        result = await session.execute(
            select(Equipment).where(Equipment.ip == '192.168.47.35')
        )
        eq = result.scalar_one_or_none()
        
        if not eq:
            print("❌ Equipamento não encontrado!")
            return
        
        print(f"\n📌 Equipamento: {eq.name} ({eq.ip})")
        print(f"   Brand: {eq.brand}")
        print(f"   Interface Index atual: {eq.snmp_interface_index}")
        print()
        
        # Atualizar Interface Index para 5 (ath0 wireless)
        print("[1] Atualizando Interface Index para 5 (ath0 wireless)...")
        eq.snmp_interface_index = 5
        session.add(eq)
        print("    ✅ Interface Index atualizado para 5")
        print()
        
        # Coletar dados wireless
        print("[2] Coletando dados wireless (Signal/CCQ)...")
        try:
            w_stats = await get_wireless_stats(
                eq.ip,
                eq.brand,
                eq.snmp_community,
                eq.snmp_port or 161
            )
            if w_stats['signal_dbm']:
                eq.signal_dbm = w_stats['signal_dbm']
                eq.ccq = w_stats['ccq']
                session.add(eq)
                print(f"    ✅ Signal: {w_stats['signal_dbm']} dBm")
                print(f"    ✅ CCQ: {w_stats['ccq']}%")
            else:
                print("    ⚠️  Sem dados de signal/CCQ")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        
        print()
        
        # Coletar clientes conectados
        print("[3] Coletando clientes conectados...")
        try:
            clients = await get_connected_clients_count(
                eq.ip,
                eq.brand,
                eq.snmp_community,
                eq.snmp_port or 161
            )
            if clients is not None:
                eq.connected_clients = clients
                session.add(eq)
                print(f"    ✅ Clientes: {clients}")
            else:
                print("    ⚠️  Sem dados de clientes")
        except Exception as e:
            print(f"    ❌ Erro: {e}")
        
        print()
        
        # Salvar no banco
        print("[4] Salvando no banco de dados...")
        await session.commit()
        print("    ✅ Dados salvos com sucesso!")
        
        print()
        print("="*70)
        print("✅ ATUALIZAÇÃO CONCLUÍDA!")
        print("="*70)
        print()
        print("📋 DADOS ATUALIZADOS:")
        print(f"   📶 Signal: {eq.signal_dbm} dBm")
        print(f"   📊 CCQ: {eq.ccq}%")
        print(f"   👥 Clientes: {eq.connected_clients}")
        print(f"   🔢 Interface Index: {eq.snmp_interface_index}")
        print()
        print("⚠️  IMPORTANTE:")
        print("   1. REINICIE o backend para o monitor começar a coletar")
        print("   2. Aguarde 60 segundos para a próxima coleta automática")
        print("   3. Atualize a página do navegador (Ctrl+Shift+R)")

if __name__ == "__main__":
    asyncio.run(force_update())

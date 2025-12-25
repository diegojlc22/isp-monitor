"""
🧪 TESTE RÁPIDO - Validar correção SNMP v1
"""
import asyncio
import sys
sys.path.insert(0, 'c:/diegolima/isp-monitor')

from backend.app.services.snmp import get_snmp_interface_traffic
from backend.app.services.wireless_snmp import get_wireless_stats

TARGET_IP = "192.168.47.35"
COMMUNITY = "publicRadionet"

async def main():
    print("="*60)
    print("🧪 TESTANDO CORREÇÃO SNMP v1")
    print("="*60)
    print(f"\n📡 Alvo: {TARGET_IP}")
    print(f"🔑 Community: {COMMUNITY}\n")
    
    # Teste 1: Traffic Interface
    print("[1] Testando get_snmp_interface_traffic...")
    traffic = await get_snmp_interface_traffic(TARGET_IP, COMMUNITY, 161, 1)
    if traffic:
        in_bytes, out_bytes = traffic
        print(f"    ✅ SUCESSO!")
        print(f"    📥 In:  {in_bytes:,} bytes")
        print(f"    📤 Out: {out_bytes:,} bytes")
    else:
        print(f"    ❌ FALHOU - Sem resposta")
    
    # Teste 2: Wireless Stats (Signal/CCQ)
    print("\n[2] Testando get_wireless_stats (Ubiquiti)...")
    stats = await get_wireless_stats(TARGET_IP, 'ubiquiti', COMMUNITY, 161)
    if stats['signal_dbm'] is not None or stats['ccq'] is not None:
        print(f"    ✅ SUCESSO!")
        print(f"    📶 Signal: {stats['signal_dbm']} dBm")
        print(f"    📊 CCQ: {stats['ccq']}%")
    else:
        print(f"    ⚠️  Sem dados wireless (pode ser normal se não for rádio)")
    
    print("\n" + "="*60)
    print("✅ TESTE CONCLUÍDO!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

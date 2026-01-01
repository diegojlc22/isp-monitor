"""
Teste SNMP específico para Intelbras 192.168.177.30
"""
import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic

async def test_intelbras():
    ip = "192.168.177.30"
    community = "publicRadionet"
    port = 161
    
    print("="*80)
    print(f"🔍 TESTANDO INTELBRAS: {ip}")
    print("="*80)
    
    # Listar interfaces
    print(f"\n📋 Listando interfaces...")
    try:
        interfaces = await get_snmp_interfaces(ip, community, port)
        if not interfaces:
            print(f"❌ Nenhuma interface encontrada")
            return
        
        print(f"✅ Encontradas {len(interfaces)} interfaces:\n")
        for iface in interfaces:
            print(f"   [{iface['index']:>3}] {iface['name']:<30}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return
    
    # Testar tráfego
    print(f"\n🚦 Testando tráfego (aguarde 5 segundos)...")
    print(f"{'Index':<8} {'Nome':<30} {'IN (Mbps)':<12} {'OUT (Mbps)':<12} {'Status'}")
    print("-" * 80)
    
    for iface in interfaces:
        idx = iface['index']
        name = iface['name']
        
        try:
            traffic1 = await get_snmp_interface_traffic(ip, community, port, idx)
            if not traffic1:
                print(f"{idx:<8} {name:<30} {'N/A':<12} {'N/A':<12} ❌ Sem dados")
                continue
            
            in_bytes1, out_bytes1 = traffic1
            time1 = time.time()
            
            await asyncio.sleep(5)
            
            traffic2 = await get_snmp_interface_traffic(ip, community, port, idx)
            if not traffic2:
                print(f"{idx:<8} {name:<30} {'N/A':<12} {'N/A':<12} ❌ Sem dados")
                continue
            
            in_bytes2, out_bytes2 = traffic2
            time2 = time.time()
            
            dt = time2 - time1
            delta_in = max(0, in_bytes2 - in_bytes1)
            delta_out = max(0, out_bytes2 - out_bytes1)
            
            mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
            mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
            
            if mbps_in > 0 or mbps_out > 0:
                status = "✅ TRÁFEGO DETECTADO!"
            else:
                status = "⚠️ Sem tráfego"
            
            print(f"{idx:<8} {name:<30} {mbps_in:<12.2f} {mbps_out:<12.2f} {status}")
            
        except Exception as e:
            print(f"{idx:<8} {name:<30} {'ERROR':<12} {'ERROR':<12} ❌ {str(e)[:30]}")
    
    print("\n" + "="*80)
    print("✅ TESTE CONCLUÍDO")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(test_intelbras())
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido")

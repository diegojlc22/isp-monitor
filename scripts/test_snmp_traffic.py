"""
Diagnóstico SNMP de Tráfego - Testa interfaces e descobre qual tem dados
"""
import asyncio
import sys
import os
from datetime import datetime
import time

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic

async def test_ip(ip, community="publicRadionet", port=161):
    print("\n" + "="*80)
    print(f"🔍 TESTANDO: {ip}")
    print("="*80)
    
    # 1. Listar todas as interfaces
    print(f"\n📋 Listando interfaces disponíveis...")
    try:
        interfaces = await get_snmp_interfaces(ip, community, port)
        if not interfaces:
            print(f"❌ Nenhuma interface encontrada via SNMP")
            print(f"   Possíveis causas:")
            print(f"   - Community incorreta (tentando: {community})")
            print(f"   - SNMP desabilitado no equipamento")
            print(f"   - Firewall bloqueando porta {port}")
            return
        
        print(f"✅ Encontradas {len(interfaces)} interfaces:\n")
        for iface in interfaces:
            print(f"   [{iface['index']:>3}] {iface['name']:<30}")
        
    except Exception as e:
        print(f"❌ Erro ao listar interfaces: {e}")
        return
    
    # 2. Testar tráfego em cada interface
    print(f"\n🚦 Testando tráfego em cada interface (aguarde 5 segundos)...")
    print(f"{'Index':<8} {'Nome':<30} {'IN (Mbps)':<12} {'OUT (Mbps)':<12} {'Status'}")
    print("-" * 80)
    
    results = []
    
    for iface in interfaces:
        idx = iface['index']
        name = iface['name']
        
        try:
            # Primeira leitura
            traffic1 = await get_snmp_interface_traffic(ip, community, port, idx)
            if not traffic1:
                print(f"{idx:<8} {name:<30} {'N/A':<12} {'N/A':<12} ❌ Sem dados")
                continue
            
            in_bytes1, out_bytes1 = traffic1
            time1 = time.time()
            
            # Aguardar 5 segundos
            await asyncio.sleep(5)
            
            # Segunda leitura
            traffic2 = await get_snmp_interface_traffic(ip, community, port, idx)
            if not traffic2:
                print(f"{idx:<8} {name:<30} {'N/A':<12} {'N/A':<12} ❌ Sem dados")
                continue
            
            in_bytes2, out_bytes2 = traffic2
            time2 = time.time()
            
            # Calcular Mbps
            dt = time2 - time1
            delta_in = max(0, in_bytes2 - in_bytes1)
            delta_out = max(0, out_bytes2 - out_bytes1)
            
            mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
            mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
            
            # Status
            if mbps_in > 0 or mbps_out > 0:
                status = "✅ TRÁFEGO DETECTADO!"
                results.append({
                    'index': idx,
                    'name': name,
                    'in': mbps_in,
                    'out': mbps_out
                })
            else:
                status = "⚠️ Sem tráfego"
            
            print(f"{idx:<8} {name:<30} {mbps_in:<12.2f} {mbps_out:<12.2f} {status}")
            
        except Exception as e:
            print(f"{idx:<8} {name:<30} {'ERROR':<12} {'ERROR':<12} ❌ {str(e)[:30]}")
    
    # 3. Resumo
    print("\n" + "="*80)
    if results:
        print(f"✅ INTERFACES COM TRÁFEGO ENCONTRADAS:")
        for r in results:
            print(f"   Interface {r['index']} ({r['name']}): IN={r['in']} Mbps, OUT={r['out']} Mbps")
        print(f"\n💡 Configure o equipamento para usar a interface {results[0]['index']}")
    else:
        print(f"⚠️ NENHUMA INTERFACE COM TRÁFEGO DETECTADA")
        print(f"   Possíveis causas:")
        print(f"   - Equipamento sem tráfego no momento")
        print(f"   - Interfaces em modo bridge/switch (não contam tráfego)")
        print(f"   - OIDs de tráfego customizados (não padrão)")
    print("="*80)

async def main():
    ips_to_test = [
        "192.168.103.2",
        "10.50.1.2",
        "192.168.177.4"
    ]
    
    print("\n" + "="*80)
    print("🔬 DIAGNÓSTICO SNMP DE TRÁFEGO")
    print("="*80)
    print(f"Testando {len(ips_to_test)} equipamentos...")
    print(f"Community: publicRadionet")
    print(f"Porta: 161")
    print(f"Tempo de teste por interface: 5 segundos")
    
    for ip in ips_to_test:
        await test_ip(ip)
        print("\n")
    
    print("\n" + "="*80)
    print("✅ DIAGNÓSTICO CONCLUÍDO")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()

"""
Teste manual de todas as interfaces do equipamento 192.168.103.67
"""
import asyncio
import time
from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic

async def test_all_interfaces():
    ip = "192.168.103.67"
    community = "publicRadionet"
    port = 161
    
    print("="*80)
    print(f"🔍 TESTANDO TODAS AS INTERFACES: {ip}")
    print("="*80)
    
    # 1. Listar interfaces
    print("\n📋 Listando interfaces disponíveis...")
    try:
        interfaces = await get_snmp_interfaces(ip, community, port)
        if not interfaces:
            print("❌ Nenhuma interface encontrada!")
            return
        
        print(f"✅ Encontradas {len(interfaces)} interfaces:\n")
        for iface in interfaces:
            print(f"   [{iface['index']:>3}] {iface['name']:<30}")
        
    except Exception as e:
        print(f"❌ Erro ao listar interfaces: {e}")
        return
    
    # 2. Testar tráfego em cada interface
    print(f"\n🚦 Testando tráfego em cada interface (aguarde 5 segundos por interface)...")
    print(f"{'Index':<8} {'Nome':<30} {'IN (Mbps)':<12} {'OUT (Mbps)':<12} {'Status'}")
    print("-" * 80)
    
    results_with_traffic = []
    
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
                results_with_traffic.append({
                    'index': idx,
                    'name': name,
                    'in': mbps_in,
                    'out': mbps_out,
                    'total': mbps_in + mbps_out
                })
            else:
                status = "⚠️ Sem tráfego"
            
            print(f"{idx:<8} {name:<30} {mbps_in:<12.2f} {mbps_out:<12.2f} {status}")
            
        except Exception as e:
            print(f"{idx:<8} {name:<30} {'ERROR':<12} {'ERROR':<12} ❌ {str(e)[:30]}")
    
    # 3. Resumo
    print("\n" + "="*80)
    if results_with_traffic:
        print(f"✅ INTERFACES COM TRÁFEGO ENCONTRADAS:")
        results_with_traffic.sort(key=lambda x: x['total'], reverse=True)
        for r in results_with_traffic:
            print(f"   Interface {r['index']:>2} ({r['name']}): IN={r['in']:.2f} Mbps, OUT={r['out']:.2f} Mbps, TOTAL={r['total']:.2f} Mbps")
        
        best = results_with_traffic[0]
        print(f"\n💡 RECOMENDAÇÃO: Configure a interface {best['index']} ({best['name']})")
        print(f"   Tráfego total: {best['total']:.2f} Mbps")
        
        print(f"\n📝 Para configurar automaticamente:")
        print(f"   UPDATE equipments SET snmp_traffic_interface_index = {best['index']} WHERE ip = '{ip}';")
        
    else:
        print(f"⚠️ NENHUMA INTERFACE COM TRÁFEGO DETECTADA")
        print(f"   Possíveis causas:")
        print(f"   - Equipamento sem tráfego no momento")
        print(f"   - Interfaces em modo bridge/switch")
        print(f"   - Community SNMP incorreta")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(test_all_interfaces())
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()

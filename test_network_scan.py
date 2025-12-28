"""
Script de teste para scan de rede
"""
import asyncio
import sys
sys.path.insert(0, '.')

from backend.app.services.pinger_fast import scan_network

async def test_scan():
    """Testa o scan de rede na faixa 192.168.108.1/24"""
    import ipaddress
    
    # Parse CIDR
    ip_range = "192.168.108.1/24"
    print(f"🔍 Testando scan na faixa: {ip_range}")
    print("=" * 60)
    
    try:
        net = ipaddress.ip_network(ip_range, strict=False)
        ips_to_scan = [str(ip) for ip in net.hosts()]
        
        print(f"📊 Total de IPs para escanear: {len(ips_to_scan)}")
        print(f"🎯 Primeiro IP: {ips_to_scan[0]}")
        print(f"🎯 Último IP: {ips_to_scan[-1]}")
        print()
        print("⏳ Iniciando scan...")
        print("=" * 60)
        
        count = 0
        online_count = 0
        
        async for result in scan_network(ips_to_scan):
            count += 1
            if result['is_online']:
                online_count += 1
                print(f"✅ {result['ip']} - ONLINE (Latência: {result.get('latency', 'N/A')}ms)")
            else:
                # Mostrar apenas alguns offline para não poluir
                if count <= 5 or count % 50 == 0:
                    print(f"❌ {result['ip']} - OFFLINE")
            
            # Progress
            if count % 10 == 0:
                print(f"   ... {count}/{len(ips_to_scan)} IPs escaneados ({online_count} online)")
        
        print()
        print("=" * 60)
        print(f"✅ Scan concluído!")
        print(f"📊 Total escaneado: {count} IPs")
        print(f"🟢 Online: {online_count}")
        print(f"🔴 Offline: {count - online_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scan())

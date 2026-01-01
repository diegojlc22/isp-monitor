"""
Configura automaticamente a interface de tráfego para os equipamentos
"""
import requests
import sys

equipment_ids = [130, 166, 167]  # CRS-BAIRRO-ALTO, Ubiquiti 247, Mikrotik 245

print("="*80)
print("🔧 AUTO-CONFIGURAÇÃO DE INTERFACES DE TRÁFEGO")
print("="*80)

for eq_id in equipment_ids:
    print(f"\n📡 Configurando equipamento ID {eq_id}...")
    
    try:
        response = requests.post(
            f'http://localhost:8000/api/equipments/{eq_id}/auto-configure-traffic',
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"✅ SUCESSO!")
                print(f"   Nome: {result['equipment_name']}")
                print(f"   IP: {result['equipment_ip']}")
                print(f"   Interface configurada: {result['configured_interface']} ({result['interface_name']})")
                print(f"   Tráfego: IN={result['traffic_in']} Mbps, OUT={result['traffic_out']} Mbps")
                print(f"   Total: {result['total_traffic']} Mbps")
            else:
                print(f"⚠️ {result.get('message', 'Sem tráfego detectado')}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout - Equipamento pode ter muitas interfaces")
    except Exception as e:
        print(f"❌ Erro: {e}")

print("\n" + "="*80)
print("✅ CONFIGURAÇÃO CONCLUÍDA")
print("="*80)
print("\n💡 Aguarde 5-10 segundos e verifique o Live Monitor!")

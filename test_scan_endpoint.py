"""
Teste do endpoint de scan via HTTP
"""
import requests
import json

url = "http://localhost:8000/api/equipments/scan/stream/"
params = {
    "ip_range": "192.168.108.1/24",
    "snmp_community": "publicRadionet",
    "snmp_port": 161
}

print("🔍 Testando endpoint de scan...")
print(f"URL: {url}")
print(f"Parâmetros: {params}")
print("=" * 60)

try:
    # Fazer requisição com stream
    response = requests.get(url, params=params, stream=True, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        print("✅ Conexão estabelecida! Recebendo dados...")
        print("=" * 60)
        
        count = 0
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
                count += 1
                
                # Limitar output para teste
                if count >= 20:
                    print("\n... (limitado a 20 linhas para teste)")
                    break
    else:
        print(f"❌ Erro: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except requests.exceptions.Timeout:
    print("❌ Timeout na requisição")
except requests.exceptions.ConnectionError as e:
    print(f"❌ Erro de conexão: {e}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

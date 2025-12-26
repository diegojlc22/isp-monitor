import requests
import time

TARGET_GROUP = "120363406257973793@g.us"
API_URL = "http://localhost:3001/send"

print(f"--- INICIANDO TESTE DE GRUPO ---")
print(f"Target ID: {TARGET_GROUP}")
print(f"API: {API_URL}")
print("Tentando enviar...")

payload = {
    "number": TARGET_GROUP,
    "message": "🔔 TESTE DE SISTEMA: Verificação de Envio para Grupo (Manual Script) 🚀"
}

try:
    resp = requests.post(API_URL, json=payload, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Resposta: {resp.text}")
    
    if resp.status_code == 200:
        print("\n✅ SUCESSO! O servidor aceitou o envio.")
        print("Se não chegou no celular, verifique se o Bot é admin ou membro do grupo.")
        print("Também verifique se o ID está correto (tente listar os grupos via http://localhost:3001/groups)")
    else:
        print("\n❌ FALHA! O servidor rejeitou.")
        
except Exception as e:
    print(f"\n❌ ERRO DE CONEXÃO: {e}")
    print("O servidor do WhatsApp está rodando? (Abra o Launcher)")

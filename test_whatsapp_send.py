import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_whatsapp():
    url = "http://127.0.0.1:3001/send"
    api_key = os.getenv("MSG_SECRET", "isp-monitor-secret-key-v2")
    
    headers = {"x-api-key": api_key}
    payload = {
        "number": "120363406257973793@g.us",
        "message": "🧪 TESTE DIRETO DO SCRIPT PYTHON"
    }
    
    print(f"[TEST] URL: {url}")
    print(f"[TEST] API Key: {api_key}")
    print(f"[TEST] Payload: {payload}")
    print(f"[TEST] Headers: {headers}")
    print("\n[TEST] Enviando requisição...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                status = resp.status
                text = await resp.text()
                
                print(f"\n[TEST] Status: {status}")
                print(f"[TEST] Resposta: {text}")
                
                if status == 200:
                    print("\n✅ SUCESSO! Mensagem enviada.")
                else:
                    print(f"\n❌ ERRO! Status {status}")
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_whatsapp())

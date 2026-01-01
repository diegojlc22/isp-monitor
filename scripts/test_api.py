import asyncio
import sys
import os
import aiohttp

sys.path.append(os.getcwd())

async def test_api():
    """Testa se a API está respondendo corretamente"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Testando API do Backend...\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. Test Health
        try:
            async with session.get(f"{base_url}/") as resp:
                print(f"✅ Backend Online: {resp.status}")
        except Exception as e:
            print(f"❌ Backend Offline: {e}")
            return
        
        # 2. Test Equipments Endpoint
        try:
            async with session.get(f"{base_url}/api/equipments") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"\n📊 Endpoint /equipments:")
                    print(f"   Status: {resp.status}")
                    print(f"   Equipamentos retornados: {len(data)}")
                    
                    if len(data) > 0:
                        print(f"\n   Primeiros 3 equipamentos:")
                        for eq in data[:3]:
                            print(f"      - {eq.get('name')} ({eq.get('ip')})")
                    else:
                        print("   ⚠️ PROBLEMA: API retornou lista vazia!")
                else:
                    print(f"   ❌ Erro: Status {resp.status}")
                    text = await resp.text()
                    print(f"   Resposta: {text[:200]}")
        except Exception as e:
            print(f"❌ Erro ao testar /equipments: {e}")
        
        # 3. Test Frontend
        try:
            async with session.get("http://localhost:5173/") as resp:
                print(f"\n✅ Frontend Online: {resp.status}")
        except Exception as e:
            print(f"\n❌ Frontend Offline: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_api())

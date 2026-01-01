import asyncio
import sys
import os

# Add root path
sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interfaces

TARGETS = [
    # (IP, Community, Version)
    ("192.168.103.2", "publicRadionet", 1),       # Mikrotik
    ("192.168.80.13", "publicRadionet", 1), 
    ("192.168.177.30", "publicRadionet", 1),
    ("10.50.1.2", "publicRadionet", 1),           # AirFiber
]

async def scan():
    print("📡 Iniciando varredura de interfaces SNMP...")
    print("Isso pode levar alguns segundos por dispositivo.")
    print("-" * 60)

    for ip, community, version in TARGETS:
        print(f"\n🔍 Consultando {ip} (Comm: {community})...")
        try:
            # Tenta primeiro com a community definida
            interfaces = await get_snmp_interfaces(ip, community)
            
            if not interfaces:
                 # Se falhar, tenta fallback comum "public"
                 print(f"   ⚠️ Falha com '{community}'. Tentando 'public'...")
                 interfaces = await get_snmp_interfaces(ip, "public")

            if interfaces:
                print(f"   ✅ [SUCESSO] {len(interfaces)} interfaces encontradas:")
                for iface in interfaces:
                    print(f"      [{iface['index']}] {iface['name']}")
            else:
                print(f"   ❌ [FALHA] Não foi possível listar interfaces (SNMP Offline ou Bloqueado).")
        
        except Exception as e:
            print(f"   ❌ Erro técnico: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(scan())

import asyncio
import sys
import os
import time

# Add root path
sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interface_traffic, get_shared_engine
from pysnmp.hlapi.asyncio import *

TARGETS = [
    # IP, Community, InterfaceIndex, Name
    ("192.168.103.2", "publicRadionet", 1, "Mikrotik"),
    ("192.168.80.13", "publicRadionet", 2, "Ubiquiti"),
    ("192.168.177.30", "publicRadionet", 7, "Intelbras"),
    ("10.50.1.2", "publicRadionet", 2, "AirFiber"),
]

async def stress_test():
    print("🚦 Testando leitura de tráfego SNMP...")
    print(f"Loop de 2 leituras com intervalo de 5s para calcular velocidade.\n")

    initial_counters = {}

    # 1. Primeira Leitura
    print("--- Leitura 1 ---")
    for ip, comm, idx, name in TARGETS:
        try:
            res = await get_snmp_interface_traffic(ip, comm, 161, idx)
            if res:
                in_bytes, out_bytes = res
                initial_counters[ip] = (time.time(), in_bytes, out_bytes)
                print(f"✅ {name} ({ip}) Idx {idx}: In={in_bytes}, Out={out_bytes}")
            else:
                print(f"❌ {name} ({ip}) Idx {idx}: Sem resposta (None)")
        except Exception as e:
             print(f"❌ {name} ({ip}): Erro {e}")
    
    print("\n⏳ Aguardando 5 segundos...\n")
    await asyncio.sleep(5)

    # 2. Segunda Leitura e Cálculo
    print("--- Leitura 2 & Cálculo ---")
    for ip, comm, idx, name in TARGETS:
        if ip not in initial_counters:
            print(f"⚠️ Pulanado {name} (falha na leitura 1)")
            continue
            
        try:
            res = await get_snmp_interface_traffic(ip, comm, 161, idx)
            if res:
                in_bytes, out_bytes = res
                last_time, last_in, last_out = initial_counters[ip]
                
                dt = time.time() - last_time
                delta_in = max(0, in_bytes - last_in)
                delta_out = max(0, out_bytes - last_out)
                
                mbps_in = (delta_in * 8) / (dt * 1_000_000)
                mbps_out = (delta_out * 8) / (dt * 1_000_000)
                
                print(f"🚀 {name} ({ip}):")
                print(f"   Download: {mbps_in:.2f} Mbps")
                print(f"   Upload:   {mbps_out:.2f} Mbps")
            else:
                 print(f"❌ {name} ({ip}): Falha na segunda leitura")
        except Exception as e:
             print(f"❌ {name} ({ip}): Erro {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(stress_test())

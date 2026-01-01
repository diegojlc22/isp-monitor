
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import detect_best_interface

async def main():
    target_ip = "10.50.1.2"
    community = "publicRadionet"
    
    print(f"--- IDENTIFICANDO MELHOR INTERFACE PARA {target_ip} ---")
    print("(Aguardando 3 segundos para medir tráfego...)")
    best = await detect_best_interface(target_ip, community)
    
    if best:
        print(f"Melhor Interface Encontrada: Index {best['index']} ({best['name']})")
        print(f"Tráfego medido: {best['current_mbps']} Mbps")
    else:
        print("Nenhuma interface com tráfego detectada.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

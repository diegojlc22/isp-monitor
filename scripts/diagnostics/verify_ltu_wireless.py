
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.wireless_snmp import get_wireless_stats, get_connected_clients_count

async def main():
    target_ip = "10.50.1.3"
    community = "publicRadionet"
    brand = "ubiquiti"
    
    print(f"--- TESTE FINAL WIRELESS STATS (LTU) ---")
    stats = await get_wireless_stats(target_ip, brand, community)
    clients = await get_connected_clients_count(target_ip, brand, community)
    
    print(f"Sinal (dBm): {stats['signal_dbm']}")
    print(f"CCQ/Qualidade (%): {stats['ccq']}")
    print(f"Clientes Conectados: {clients}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interface_traffic

async def main():
    target_ip = "10.50.1.2"
    community = "publicRadionet"
    
    print(f"--- TESTANDO LTU COUNTERS NO {target_ip} ---")
    traffic = await get_snmp_interface_traffic(target_ip, community, interface_index=1000, brand='ubiquiti')
    if traffic:
        print(f"LTU Respondeu! In: {traffic[0]}, Out: {traffic[1]}")
    else:
        print("LTU NÃO respondeu para este rádio.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

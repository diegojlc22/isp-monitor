
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import get_snmp_interfaces

async def main():
    target_ip = "10.50.1.3"
    community = "publicRadionet"
    
    print(f"--- FULL INTERFACE SCAN: {target_ip} ---")
    interfaces = await get_snmp_interfaces(target_ip, community)
    for iface in interfaces:
        print(f"Index: {iface['index']} | Name: {iface['name']}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

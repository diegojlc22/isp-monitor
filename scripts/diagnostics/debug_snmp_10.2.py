
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import _snmp_get

async def main():
    target_ip = "10.50.1.2"
    community = "publicRadionet"
    
    varBinds = await _snmp_get(target_ip, community, ['1.3.6.1.2.1.1.1.0', '1.3.6.1.2.1.1.2.0'])
    if varBinds:
        print(f"sysDescr: {varBinds[0][1]}")
        print(f"sysObjectID: {varBinds[1][1]}")
    else:
        print("FALHA AO OBTER INFO SNMP")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

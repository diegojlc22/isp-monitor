
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.app.services.snmp import detect_brand

async def main():
    target_ip = "10.50.1.2"
    community = "publicRadionet"
    
    brand = await detect_brand(target_ip, community)
    print(f"Brand detectada para {target_ip}: {brand}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

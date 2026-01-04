
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.services.snmp import get_shared_engine, detect_equipment_name, detect_brand
from backend.app.services.wireless_snmp import get_wireless_stats
from icmplib import async_ping

TARGET_IPS = [
    "192.168.103.106", "192.168.103.203", "192.168.103.21", "192.168.103.244", "192.168.103.69", 
    "192.168.103.8", "192.168.103.82", "192.168.103.93", "192.168.104.18", "192.168.104.41", 
    "192.168.104.50", "192.168.106.144", "192.168.106.154", "192.168.106.155", "192.168.106.43", 
    "192.168.106.50", "192.168.106.51", "192.168.108.122", "192.168.108.19", "192.168.108.65", 
    "192.168.108.66", "192.168.109.10", "192.168.109.11", "192.168.109.251", "192.168.109.7", 
    "192.168.109.72", "192.168.110.19", "192.168.110.2", "192.168.110.20", "192.168.110.21", 
    "192.168.110.31", "192.168.111.3", "192.168.111.4", "192.168.112.3", "192.168.112.4", 
    "192.168.112.6", "192.168.147.19", "192.168.147.5", "192.168.148.12", "192.168.41.3", 
    "192.168.41.5", "192.168.41.7", "192.168.46.11", "192.168.46.18", "192.168.47.24", 
    "192.168.47.61", "192.168.49.41", "192.168.49.42", "192.168.49.58", "192.168.49.59", 
    "192.168.49.72", "192.168.49.74", "192.168.49.8", "192.168.49.89", "192.168.49.92", 
    "192.168.50.21", "192.168.50.25", "192.168.50.28", "192.168.50.30", "192.168.51.4", 
    "192.168.52.22", "192.168.69.10", "192.168.80.8", "192.168.82.12", "192.168.82.13", 
    "192.168.82.5", "192.168.82.6"
]

COMMUNITY = "publicRadionet"

async def check_ip_sequential(ip):
    # Short ping check
    host = await async_ping(ip, count=1, timeout=0.3, privileged=False)
    ping_status = "ONLINE" if host.is_alive else "OFFLINE"
    
    if not host.is_alive:
        return f"{ip.ljust(15)} | {ping_status.ljust(7)} | -"

    # SNMP Check (Name and Signal)
    try:
        brand = await detect_brand(ip, COMMUNITY)
        name = await detect_equipment_name(ip, COMMUNITY)
        
        if name:
            snmp_status = "SNMP OK"
            # Try to get signal based on detected brand
            stats = await get_wireless_stats(ip, brand if brand != 'generic' else 'ubiquiti', COMMUNITY)
            sig = stats.get('signal_dbm')
            signal_str = f"{sig} dBm" if sig is not None else "NO SIGNAL DATA"
            return f"{ip.ljust(15)} | {ping_status.ljust(7)} | {snmp_status.ljust(8)} | {brand.ljust(10)} | {name.ljust(20)} | {signal_str}"
        else:
            return f"{ip.ljust(15)} | {ping_status.ljust(7)} | SNMP FAIL | -"
    except:
        return f"{ip.ljust(15)} | {ping_status.ljust(7)} | ERROR | -"

async def main():
    print(f"{'IP'.ljust(15)} | {'PING'.ljust(7)} | {'SNMP'.ljust(8)} | {'BRAND'.ljust(10)} | {'NAME'.ljust(20)} | {'SIGNAL'}")
    print("-" * 100)
    
    # RUN SEQUENTIALLY to avoid "freezing"
    results = []
    for ip in TARGET_IPS:
        res = await check_ip_sequential(ip)
        print(res)
        results.append(res)
        await asyncio.sleep(0.05) # Tiny sleep to yield

    with open("results_lista_user.txt", "w", encoding="utf-8") as f:
        f.write(f"{'IP'.ljust(15)} | {'PING'.ljust(7)} | {'SNMP'.ljust(8)} | {'BRAND'.ljust(10)} | {'NAME'.ljust(20)} | {'SIGNAL'}\n")
        f.write("-" * 100 + "\n")
        for r in results:
            f.write(r + "\n")

if __name__ == "__main__":
    asyncio.run(main())

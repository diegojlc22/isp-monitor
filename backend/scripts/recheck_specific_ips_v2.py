
import asyncio
import sys
import os
from tabulate import tabulate

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.services.snmp import detect_equipment_name
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

COMMUNITIES = ["publicRadionet", "public", "intelbras", "private"]

async def check_target(ip):
    # 1. Ping
    host = await async_ping(ip, count=1, timeout=0.5, privileged=False)
    
    res = {
        "ip": ip,
        "ping": "UP" if host.is_alive else "DOWN",
        "snmp_status": "FAIL",
        "name": "-",
        "community": "-",
        "signal": "-"
    }

    if not host.is_alive:
        host = await async_ping(ip, count=2, timeout=1.0, privileged=False)
        if not host.is_alive:
            return res

    # 2. Try SNMP
    for comm in COMMUNITIES:
        try:
            name = await detect_equipment_name(ip, comm, 161)
            if name:
                res["snmp_status"] = "OK"
                res["name"] = name
                res["community"] = comm
                
                # Try getting stats (Signal)
                statsU = await get_wireless_stats(ip, "ubiquiti", comm, 161)
                if statsU and statsU.get('signal_dbm'):
                    res["signal"] = f"{statsU.get('signal_dbm')} dBm"
                    break

                statsI = await get_wireless_stats(ip, "intelbras", comm, 161)
                if statsI and statsI.get('signal_dbm'):
                    res["signal"] = f"{statsI.get('signal_dbm')} dBm"
                    break
                    
                break 
        except:
            pass
            
    return res

async def main():
    print(f"--- Re-checking {len(TARGET_IPS)} specific IPs (Timeout=2.0s) ---")
    
    tasks = [check_target(ip) for ip in TARGET_IPS]
    
    batch_size = 20
    results = []
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        print(f"Scanning batch {i}-{i+len(batch)}...")
        batch_res = await asyncio.gather(*batch)
        results.extend(batch_res)
        
    print("\n=== RESULTS ===")
    
    table_data = [[r['ip'], r['name'], r['ping'], r['snmp_status'], r['community'], r['signal']] for r in results]
    headers = ["IP", "Name (SNMP)", "Ping", "SNMP", "Community", "Signal"]
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    with open("recheck_results.txt", "w", encoding="utf-8") as f:
         f.write(tabulate(table_data, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import sys
import os
from sqlalchemy import select
from tabulate import tabulate

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.snmp import detect_brand, detect_equipment_name
from backend.app.services.wireless_snmp import get_wireless_stats, get_connected_clients_count

KNOWN_COMMUNITIES = ["publicRadionet", "public", "intelbras", "private"]

async def audit_network():
    print("--- 📊 Network Audit: Data Completeness Check ---")
    
    async with AsyncSessionLocal() as session:
        # Fetch all online devices first to focus on real data gaps
        result = await session.execute(select(Equipment).order_by(Equipment.brand, Equipment.ip))
        equipments = result.scalars().all()
        
        report_data = []
        summary = {
            "total": len(equipments),
            "online": 0,
            "offline": 0,
            "complete_data": 0,
            "missing_signal": 0,
            "missing_clients": 0, # Only for Transmitters
            "missing_snmp": 0 
        }

        tasks = []
        sem = asyncio.Semaphore(50) 
        
        async def check_one(eq):
            async with sem:
                res = {
                    "ip": eq.ip,
                    "name": eq.name,
                    "brand": eq.brand,
                    "type": eq.equipment_type or "N/A",
                    "status": "OFFLINE",
                    "signal": "N/A",
                    "clients": "N/A",
                    "notes": ""
                }
                
                # Check simple SNMP connectivity (Name)
                comm = eq.snmp_community or "public"
                port = eq.snmp_port or 161
                
                try:
                    # Basic SNMP Check
                    sys_name = await detect_equipment_name(eq.ip, comm, port)
                    
                    if sys_name:
                         res["status"] = "ONLINE"
                         
                         # Check Wireless Data
                         if eq.brand and eq.brand != 'generic':
                             # Clients
                             if eq.equipment_type == 'transmitter':
                                 clients = await get_connected_clients_count(eq.ip, eq.brand, comm, port)
                                 res["clients"] = str(clients) if clients is not None else "❌ MISSING"
                             else:
                                 res["clients"] = "-" # Not applicable
                                 
                             # Signal (for Station or PTP)
                             # Even transmitters might show noise/floor, but Signal is crucial for Stations
                             if eq.equipment_type != 'transmitter' or True: # Check for all for now for audit
                                 stats = await get_wireless_stats(eq.ip, eq.brand, comm, port)
                                 sig = stats.get('signal_dbm')
                                 res["signal"] = f"{sig} dBm" if sig is not None else "❌ MISSING"
                         else:
                             res["notes"] = "Generic/Unknown Brand"
                    else:
                        res["status"] = "SNMP FAIL" # Ping might work but SNMP failed
                except:
                    res["status"] = "UNREACHABLE"
                    
                return res

        for eq in equipments:
            tasks.append(check_one(eq))
            
        print(f"Scanning {len(equipments)} devices... please wait.")
        results = await asyncio.gather(*tasks)
        
        # Process Results
        for r in results:
            # Counters
            if r["status"] == "ONLINE":
                summary["online"] += 1
                
                is_missing = False
                if r["signal"] == "❌ MISSING": 
                    summary["missing_signal"] += 1
                    is_missing = True
                
                if r["clients"] == "❌ MISSING":
                    summary["missing_clients"] += 1
                    is_missing = True
                    
                if not is_missing:
                    summary["complete_data"] += 1
            elif r["status"] == "SNMP FAIL":
                summary["missing_snmp"] += 1
                summary["online"] += 1 # Technically online just no snmp
            else:
                summary["offline"] += 1

            # Add to table if it has issues OR just to list
            # Let's list everything sorted by brand
            report_data.append([r["brand"], r["ip"], r["name"], r["status"], r["signal"], r["clients"], r["notes"]])

        # Sort by Brand then Status
        report_data.sort(key=lambda x: (x[0] or "z", x[3]))

        print(tabulate(report_data, headers=["Brand", "IP", "Name", "Status", "Signal", "Clients", "Notes"], tablefmt="grid"))
        
        print("\n=== SUMMARY ===")
        print(f"Total Devices: {summary['total']}")
        print(f"Online (SNMP OK): {summary['online'] - summary['missing_snmp']}")
        print(f"Online (SNMP FAIL): {summary['missing_snmp']}")
        print(f"Offline: {summary['offline']}")
        print(f"Devices with Full Data: {summary['complete_data']}")
        print(f"Devices Missing Signal: {summary['missing_signal']}")
        print(f"Transmitters Missing Client Count: {summary['missing_clients']}")

if __name__ == "__main__":
    asyncio.run(audit_network())

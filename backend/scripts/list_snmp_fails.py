
import asyncio
import sys
import os
from sqlalchemy import select
from tabulate import tabulate

# Add backend to path
sys.path.append(os.getcwd())

from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.snmp import detect_equipment_name

async def list_snmp_failures():
    print("--- 🔍 Scanning for SNMP Failures ---")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Equipment).order_by(Equipment.brand, Equipment.ip))
        equipments = result.scalars().all()
        
        failures = []
        sem = asyncio.Semaphore(50) 
        
        async def check_snmp(eq):
            async with sem:
                comm = eq.snmp_community or "public"
                port = eq.snmp_port or 161
                
                try:
                    # Basic SNMP Check (Name)
                    sys_name = await detect_equipment_name(eq.ip, comm, port)
                    
                    if not sys_name:
                        # Double check if ping works to confirm it's online but SNMP failed
                        # (Skipping ping here for speed, assuming 'Online' means reachable)
                        return {
                            "brand": eq.brand,
                            "ip": eq.ip,
                            "name": eq.name,
                            "community": comm
                        }
                except:
                    # Exception means likely unreachable or timeout
                     return {
                            "brand": eq.brand,
                            "ip": eq.ip,
                            "name": eq.name,
                            "community": comm,
                            "error": "Timeout/Unreachable"
                        }
                return None

        tasks = [check_snmp(eq) for eq in equipments]
        
        print(f"Checking {len(equipments)} devices...")
        results = await asyncio.gather(*tasks)
        
        failures = [r for r in results if r is not None]
        
        # Sort by Brand
        failures.sort(key=lambda x: (x['brand'] or 'z', x['ip']))
        
        # Print Table
        table_data = [[f['brand'], f['ip'], f['name'], f['community']] for f in failures]
        
        output = "\n=== DEVICES WITH SNMP FAILURE ===\n"
        output += tabulate(table_data, headers=["Brand", "IP", "Name", "Community"], tablefmt="grid")
        output += f"\nTotal Failures: {len(failures)}\n"
        
        print(output)
        
        with open("snmp_failures.txt", "w", encoding="utf-8") as f:
            f.write(output)
        
        print(f"\n✅ Report saved to snmp_failures.txt")

if __name__ == "__main__":
    asyncio.run(list_snmp_failures())

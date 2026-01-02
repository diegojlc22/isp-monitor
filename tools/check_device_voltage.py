
import asyncio
import sys
from backend.app.services.wireless_snmp import get_health_stats

async def probe(ip, community="public"):
    print(f"--- Probing {ip} (Community: {community}) ---")
    try:
        stats = await get_health_stats(ip, "mikrotik", community)
        print("Result:", stats)
        
        if stats.get('voltage'):
            print(f"✅ VOLTAGE FOUND: {stats['voltage']} V")
        else:
            print("❌ No voltage detected.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/check_device_voltage.py <IP_ADDRESS> [COMMUNITY]")
    else:
        ip = sys.argv[1]
        comm = sys.argv[2] if len(sys.argv) > 2 else "public"
        asyncio.run(probe(ip, comm))

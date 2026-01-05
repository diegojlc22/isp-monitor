import asyncio
from backend.app.services.wireless_snmp import get_snmp_value, snmp_walk_list, _snmp_get

async def test():
    ip = "192.168.103.203"
    community = "public"
    port = 161
    
    print(f"Testing {ip}...")
    
    # 1. Standard Client Count OID
    val1 = await get_snmp_value(ip, community, "1.3.6.1.4.1.41112.1.4.5.1.15", port)
    print(f"AirMAX Client Count OID (.1.15): {val1}")
    
    # 2. Try another common UBNT OID for clients (ubntStaCount)
    val2 = await get_snmp_value(ip, community, "1.3.6.1.4.1.41112.1.4.5.1.15.0", port)
    print(f"AirMAX Client Count OID (.1.15.0): {val2}")

    # 3. LTU?
    val3 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.10.1.4', port)
    print(f"LTU Walk Result count: {len(val3)}")
    
    # 4. AirMAX AC Station Table walk?
    val4 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.4.7.1', port)
    print(f"AirMAX AC StaTable Walk result count: {len(val4)}")

    # 5. AirMAX M Station Table?
    val5 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.4.6.1', port)
    print(f"AirMAX M StaTable Walk result count: {len(val5)}")

if __name__ == "__main__":
    asyncio.run(test())

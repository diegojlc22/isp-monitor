import asyncio
from backend.app.services.wireless_snmp import get_snmp_value, snmp_walk_list

async def test():
    ip = "192.168.103.203"
    community = "publicRadionet"
    port = 161
    
    print(f"Testing {ip} with community {community}...")
    
    # 1. Standard Client Count OID
    val1 = await get_snmp_value(ip, community, "1.3.6.1.4.1.41112.1.4.5.1.15", port)
    print(f"AirMAX Client Count OID (.1.15): {val1}")
    
    # 2. LTU Walk Result?
    val3 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.10.1.4', port)
    print(f"LTU Walk Result count: {len(val3)}")
    
    # 3. AirMAX AC Station Table walk?
    val4 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.4.7.1.3', port)
    print(f"AirMAX AC StaTable Signal Walk result count: {len(val4)}")

    # 4. AirMAX M Station Table walk?
    val5 = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.4.5.1.15', port)
    print(f"AirMAX M StaCount result: {val5}")
    
    # 5. Get Interface Table?
    val6 = await snmp_walk_list(ip, community, '1.3.6.1.2.1.2.2.1.2', port)
    print(f"Interfaces: {val6}")

if __name__ == "__main__":
    asyncio.run(test())

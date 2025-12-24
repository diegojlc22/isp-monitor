from pysnmp.hlapi.asyncio import *

# OID Map
OIDS = {
    'ubiquiti': {
        'signal': '1.3.6.1.4.1.41112.1.4.5.1.5.1', # UBNT-AirMAX-MIB
        'ccq': '1.3.6.1.4.1.41112.1.4.5.1.7.1'
    },
    'intelbras': {
        # Intelbras often mimics other MIBs. If running Mikrotik core (APC/WOM), signal is MK-oid.
        # But some are legitimate. Let's try Generic/UBNT/MK fallback logic.
        'signal': '1.3.6.1.4.1.41112.1.4.5.1.5.1', # Try UBNT first (some WOM do match)
        'ccq': '1.3.6.1.4.1.41112.1.4.5.1.7.1'
    }
}

async def get_snmp_value(ip, community, oid, port=161):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, port), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if not errorIndication and not errorStatus:
            for varBind in varBinds:
                # Value is varBind[1]
                val = varBind[1]
                # Convert to int
                try:
                    return int(val)
                except:
                    return str(val)
    except:
        return None
    return None

async def get_wireless_stats(ip, brand, community, port=161):
    """
    Fetches Signal and CCQ based on brand.
    Returns dict: {'signal_dbm': int, 'ccq': int}
    """
    stats = {'signal_dbm': None, 'ccq': None}
    
    brand_key = brand.lower()
    if brand_key not in OIDS:
        return stats
        
    signal_oid = OIDS[brand_key].get('signal')
    ccq_oid = OIDS[brand_key].get('ccq')
    
    # Fetch Signal
    if signal_oid:
        sig = await get_snmp_value(ip, community, signal_oid, port)
        if sig is not None:
             # Ensure it is negative (dBm)
             if isinstance(sig, int) and sig > 0:
                 sig = -sig # Some devices report positive 60 for -60
             stats['signal_dbm'] = sig
             
    # Fetch CCQ
    if ccq_oid:
        ccq = await get_snmp_value(ip, community, ccq_oid, port)
        if ccq is not None and isinstance(ccq, int):
             stats['ccq'] = ccq
             
    return stats

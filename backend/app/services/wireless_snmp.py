from pysnmp.hlapi.asyncio import *
from backend.app.services.snmp import get_shared_engine

async def _snmp_get(ip, community, oids, port=161, timeout=1.0):
    """Internal helper to try SNMP get with v2c then v1"""
    # Try SNMPv2c first
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=1), # v2c
            UdpTransportTarget((ip, port), timeout=timeout, retries=1),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        if not errorIndication and not errorStatus:
            return varBinds
    except:
        pass

    # Try SNMPv1 fallback
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=0), # v1
            UdpTransportTarget((ip, port), timeout=timeout, retries=1),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        if not errorIndication and not errorStatus:
            return varBinds
    except:
        pass
    
    return None

async def _snmp_next(ip, community, root_oid, port=161, timeout=1.0):
    """Internal helper to try SNMP walk/next with v2c then v1"""
    # Try SNMPv2c
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            engine,
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, port), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(root_oid)),
            lexicographicMode=False
        )
        if not errorIndication and not errorStatus and varBinds:
            return varBinds
    except:
        pass

    # Try SNMPv1
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            engine,
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=timeout, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(root_oid)),
            lexicographicMode=False
        )
        if not errorIndication and not errorStatus and varBinds:
            return varBinds
    except:
        pass

    return None

async def detect_equipment_name(ip, community='public', port=161):
    """
    Detects equipment name via SNMP sysName.
    Returns the equipment name or None if detection fails.
    OID: 1.3.6.1.2.1.1.5.0 (sysName)
    """
    # Try with provided community
    varBinds = await _snmp_get(ip, community, ['1.3.6.1.2.1.1.5.0'], port)
    
    # Fallback to 'public' if different
    if not varBinds and community != 'public':
        varBinds = await _snmp_get(ip, 'public', ['1.3.6.1.2.1.1.5.0'], port)

    if not varBinds:
        return None
            
    name = str(varBinds[0][1]).strip()
    
    # Return None if name is empty or default values
    if not name or name.lower() in ['', 'unknown', 'localhost', 'default']:
        return None
        
    return name


async def detect_brand(ip, community, port=161):
    """
    Auto-detects equipment brand via SNMP.
    Returns: 'ubiquiti', 'mikrotik', 'mimosa', 'intelbras', or 'generic'
    """
    # 1. Try with provided community
    varBinds = await _snmp_get(ip, community, ['1.3.6.1.2.1.1.1.0', '1.3.6.1.2.1.1.2.0'], port)
    
    # 2. Fallback to 'public' if different
    if not varBinds and community != 'public':
        varBinds = await _snmp_get(ip, 'public', ['1.3.6.1.2.1.1.1.0', '1.3.6.1.2.1.1.2.0'], port)

    if varBinds:
        sys_descr = str(varBinds[0][1]).lower()
        sys_object_id = str(varBinds[1][1])
        
        # Identification Logic
        if '26138' in sys_object_id or 'intelbras' in sys_descr or 'wom' in sys_descr:
            return 'intelbras'
        if 'mikrotik' in sys_descr or 'routeros' in sys_descr or '14988' in sys_object_id:
            return 'mikrotik'
        if 'mimosa' in sys_descr or '43356' in sys_object_id:
            return 'mimosa'
        if 'ubiquiti' in sys_descr or 'airmax' in sys_descr or 'airfiber' in sys_descr or '41112' in sys_object_id:
            return 'ubiquiti'

    # Fallback to Walk detection for stubborn devices
    # Test Intelbras
    if await _snmp_next(ip, community, '1.3.6.1.4.1.26138', port): return 'intelbras'
    # Test Ubiquiti
    if await _snmp_next(ip, community, '1.3.6.1.4.1.41112', port): return 'ubiquiti'
    # Test Mikrotik
    if await _snmp_next(ip, community, '1.3.6.1.4.1.14988', port): return 'mikrotik'
    
    return 'generic'


async def detect_equipment_type(ip, brand, community, port=161):
    """
    Auto-detects if equipment is a Station (client) or Transmitter (AP).
    Returns: 'station', 'transmitter', or 'other'
    """
    try:
        # Strategy: Check for connected clients
        # If has clients > 0, it's a Transmitter (AP)
        # If has signal data but no clients, it's a Station
        
        from backend.app.services.wireless_snmp import get_connected_clients_count, get_wireless_stats
        
        # Try to get connected clients count
        clients = await get_connected_clients_count(ip, brand, community, port)
        
        if clients is not None and clients > 0:
            return 'transmitter'  # Has clients = AP
            
        # Check if has wireless signal (means it's connected to something)
        stats = await get_wireless_stats(ip, brand, community, port)
        
        if stats['signal_dbm'] is not None:
            return 'station'  # Has signal = Client/Station
            
        # Fallback: Try to detect by checking specific OIDs
        # For Ubiquiti: Check opmode
        if brand.lower() == 'ubiquiti':
            # Try to get wireless mode
            varBinds = await _snmp_get(ip, community, ['1.3.6.1.4.1.41112.1.4.1.1.4.1'], port)
            
            if varBinds:
                mode = str(varBinds[0][1]).lower()
                if 'ap' in mode or 'master' in mode:
                    return 'transmitter'
                elif 'sta' in mode or 'station' in mode or 'client' in mode:
                    return 'station'
                    
        # For Mikrotik: Check interface type
        elif brand.lower() == 'mikrotik':
            # Mikrotik exposes mode in different OIDs depending on version
            # If we got here and no clients, likely a station
            if stats['signal_dbm'] is not None or stats['ccq'] is not None:
                return 'station'
                
    except:
        pass
        
    return 'other'

# OID Map
OIDS = {
    'ubiquiti': {
        'signal': [
            '1.3.6.1.4.1.41112.1.4.5.1.5.1', # M5 Legacy
            '1.3.6.1.4.1.41112.1.4.7.1.3',   # AC Signal Table (Requires Walk)
            '1.3.6.1.4.1.41112.1.4.1.1.5.1'  # Generic
        ],
        'ccq': '1.3.6.1.4.1.41112.1.4.5.1.7.1'
    },
    'mikrotik': {
        'signal': [
            '1.3.6.1.4.1.14988.1.1.1.2.1.19',  # mtxrWlCMRtabStrength (Client/Station Mode) - WALK
            '1.3.6.1.4.1.14988.1.1.1.1.1.4'    # mtxrWlRtabStrength (AP Registration Table) - WALK
        ],
        'ccq': [
            '1.3.6.1.4.1.14988.1.1.1.3.1.10',   # mtxrWlApTxCCQ (AP Mode) - WALK
            '1.3.6.1.4.1.14988.1.1.1.1.1.10'    # mtxrWlRtabRxCCQ (Registration Table)
        ],
        'clients': '1.3.6.1.4.1.14988.1.1.1.3.1.6'  # mtxrWlApClientCount - WALK
    },
    'mimosa': {
        'signal': ['1.3.6.1.4.1.43356.2.1.2.6.2.1.8'],  # mimosaRxPower (Chain table) - WALK
        'snr': '1.3.6.1.4.1.43356.2.1.2.6.3.1.3'        # mimosaSNR - WALK (can use as quality metric)
    },
    'intelbras': {
        # Intelbras often mimics other MIBs. If running Mikrotik core (APC/WOM), signal is MK-oid.
        # But some are legitimate. Let's try Generic/UBNT/MK fallback logic.
        'signal': '1.3.6.1.4.1.41112.1.4.5.1.5.1', # Try UBNT first (some WOM do match)
        'ccq': '1.3.6.1.4.1.41112.1.4.5.1.7.1'
    }
}

async def get_snmp_value(ip, community, oid, port=161):
    varBinds = await _snmp_get(ip, community, [oid], port)
    if not varBinds:
        return None
    val = varBinds[0][1]
    try: return int(val)
    except: return str(val)

async def get_snmp_walk_first(ip, community, root_oid, port=161):
    varBinds = await _snmp_next(ip, community, root_oid, port)
    if not varBinds:
        return None
    # varBinds usually contains the first row of the walk
    for varBind in varBinds:
        if isinstance(varBind, list) and len(varBind) > 0:
            val = varBind[0][1]
        else:
            val = varBind[1]
        try: return int(val)
        except: pass
    return None

async def get_wireless_stats(ip, brand, community, port=161, interface_index=None, equipment_type=None):
    """
    Fetches Signal and CCQ based on brand.
    Supports Wireless and Fiber (SFP).
    Returns dict: {'signal_dbm': int, 'ccq': int}
    """
    stats = {'signal_dbm': None, 'ccq': None}
    brand_key = brand.lower()

    # --- FIBER / SFP CASE ---
    if brand_key == 'mikrotik' and equipment_type == 'fiber' and interface_index:
        try:
            # 1. Try New SFP Monitor Table (OID .1.3.6.1.4.1.14988.1.1.19.1.1)
            # Field 10 is RX Power in dBm * 1000
            val_dbm = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.19.1.1.10.{interface_index}', port)
            if val_dbm is not None:
                try:
                    stats['signal_dbm'] = int(round(float(val_dbm) / 1000.0))
                    return stats
                except: pass

            # 2. Fallback to Linear uW Table (.14)
            val_uw = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.14.1.1.15.{interface_index}', port)
            if val_uw is not None and isinstance(val_uw, (int, float)) and val_uw > 0:
                import math
                dbm = 10 * math.log10(float(val_uw) / 1000.0)
                stats['signal_dbm'] = int(round(dbm))
            
            return stats
        except:
            pass

    if brand_key not in OIDS:
        return stats
        
    signal_oid = OIDS[brand_key].get('signal')
    ccq_oid = OIDS[brand_key].get('ccq')
    
    # Fetch Signal
    if signal_oid:
        # Support list of OIDs for fallback (AC vs M5 vs Mikrotik vs Mimosa)
        if isinstance(signal_oid, list):
            for oid in signal_oid:
                sig = None
                # Special handling for table roots (Ubiquiti AC, Mikrotik, Mimosa)
                if oid in ['1.3.6.1.4.1.41112.1.4.7.1.3', '1.3.6.1.4.1.14988.1.1.1.2.1.19', '1.3.6.1.4.1.14988.1.1.1.1.1.4', '1.3.6.1.4.1.43356.2.1.2.6.2.1.8']:
                    sig = await get_snmp_walk_first(ip, community, oid, port)
                else:
                    sig = await get_snmp_value(ip, community, oid, port)
                    
                if sig is not None:
                     # Validate reasonable range for signal (e.g., -100 to -10, or 10 to 100)
                     if isinstance(sig, int):
                         if sig == 0: continue # Invalid
                         if sig > 0: sig = -sig
                         stats['signal_dbm'] = sig
                         break
        else:
            sig = await get_snmp_value(ip, community, signal_oid, port)
            if sig is not None:
                 if isinstance(sig, int) and sig > 0:
                     sig = -sig
                 stats['signal_dbm'] = sig
             
    # Fetch CCQ (or SNR for Mimosa)
    if ccq_oid:
        # Support list of OIDs for fallback (similar to signal)
        if isinstance(ccq_oid, list):
            for oid in ccq_oid:
                ccq = None
                # Check if this is a Mikrotik Walk OID
                if oid in ['1.3.6.1.4.1.14988.1.1.1.3.1.10', '1.3.6.1.4.1.14988.1.1.1.1.1.10', '1.3.6.1.4.1.14988.1.1.1.2.1.19']:
                    ccq = await get_snmp_walk_first(ip, community, oid, port)
                else:
                    ccq = await get_snmp_value(ip, community, oid, port)
                    
                if ccq is not None and isinstance(ccq, int):
                    stats['ccq'] = ccq
                    break
        else:
            ccq = await get_snmp_value(ip, community, ccq_oid, port)
            if ccq is not None and isinstance(ccq, int):
                stats['ccq'] = ccq
    
    # For Mimosa, try SNR as quality metric if CCQ not found
    if brand_key == 'mimosa' and stats['ccq'] is None:
        snr_oid = OIDS[brand_key].get('snr')
        if snr_oid:
            snr = await get_snmp_walk_first(ip, community, snr_oid, port)
            if snr is not None and isinstance(snr, int):
                stats['ccq'] = snr  # Use SNR as quality metric
              
    return stats

async def get_connected_clients_count(ip, brand, community, port=161):
    """
    Fetches number of connected clients for Access Points.
    Returns int or None.
    """
    brand_key = brand.lower()
    
    if brand_key not in OIDS:
        return None
    
    # Check if brand has a specific clients OID
    clients_oid = OIDS[brand_key].get('clients')
    
    if clients_oid:
        count = await get_snmp_value(ip, community, clients_oid, port)
        if count is not None and isinstance(count, int):
            return count
    
    # Fallback for Ubiquiti (legacy)
    if brand_key == 'ubiquiti':
        client_oid = '1.3.6.1.4.1.41112.1.4.5.1.15.1'
        count = await get_snmp_value(ip, community, client_oid, port)
        if count is not None and isinstance(count, int):
            return count
    
    return None

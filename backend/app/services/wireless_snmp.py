from pysnmp.hlapi.asyncio import *

async def detect_brand(ip, community, port=161):
    """
    Auto-detects equipment brand via SNMP.
    Returns: 'ubiquiti', 'mikrotik', 'mimosa', 'intelbras', or 'generic'
    """
    try:
        # Get sysDescr and sysObjectID
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),  # sysDescr
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.2.0'))   # sysObjectID
        )
        
        if errorIndication or errorStatus:
            return 'generic'
            
        sys_descr = str(varBinds[0][1]).lower()
        sys_object_id = str(varBinds[1][1])
        
        # PRIORITY 1: Check for Intelbras FIRST (before checking Ubiquiti)
        # Intelbras WOM series uses Ubiquiti OIDs but should be identified as Intelbras
        if '26138' in sys_object_id or 'intelbras' in sys_descr or 'wom' in sys_descr:
            return 'intelbras'
        
        # PRIORITY 2: Check sysDescr for other brand keywords
        if 'mikrotik' in sys_descr or 'routeros' in sys_descr:
            return 'mikrotik'
        elif 'mimosa' in sys_descr:
            return 'mimosa'
        elif 'ubiquiti' in sys_descr or 'airmax' in sys_descr or 'airfiber' in sys_descr:
            return 'ubiquiti'
            
        # PRIORITY 3: Check sysObjectID (Enterprise ID)
        if '14988' in sys_object_id:  # Mikrotik
            return 'mikrotik'
        elif '43356' in sys_object_id:  # Mimosa
            return 'mimosa'
        elif '41112' in sys_object_id:  # Ubiquiti
            return 'ubiquiti'
            
        # Fallback: Try to detect by testing OIDs
        # Test Intelbras OID first
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=1.5, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.26138')),
            lexicographicMode=False
        )
        
        if not errorIndication and not errorStatus and varBinds:
            return 'intelbras'
            
        # Test Ubiquiti OID
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=1.5, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.41112')),
            lexicographicMode=False
        )
        
        if not errorIndication and not errorStatus and varBinds:
            return 'ubiquiti'
            
        # Test Mikrotik OID
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=1.5, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.14988')),
            lexicographicMode=False
        )
        
        if not errorIndication and not errorStatus and varBinds:
            return 'mikrotik'
            
        # Test Mimosa OID
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=1.5, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.4.1.43356')),
            lexicographicMode=False
        )
        
        if not errorIndication and not errorStatus and varBinds:
            return 'mimosa'
            
    except:
        pass
        
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
            errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=0),
                UdpTransportTarget((ip, port), timeout=2.0, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity('1.3.6.1.4.1.41112.1.4.5.1.14.1'))  # ubntWlStatOpmode
            )
            
            if not errorIndication and not errorStatus:
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
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),  # v1 for Ubiquiti compatibility
            UdpTransportTarget((ip, port), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if not errorIndication and not errorStatus:
            for varBind in varBinds:
                if isinstance(varBind, list) and len(varBind) > 0: val = varBind[1]
                else: val = varBind[1]
                try: return int(val)
                except: return str(val)
    except:
        return None
    return None

async def get_snmp_walk_first(ip, community, root_oid, port=161):
    """
    Performs a Walk (nextCmd) on the root_oid and returns the FIRST valid integer value found.
    Useful for tables where the index is dynamic (e.g. Ubiquiti AC Signal Strength).
    """
    try:
        # We only want the first valid value in this subtree
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(root_oid)),
            lexicographicMode=False
        )
        
        if not errorIndication and not errorStatus and varBinds:
            # varBinds is a list of rows, usually we get one row with nextCmd unless we loop
            # But nextCmd is an iterator in recent pysnmp, but here we await it (single step)
            # The async iterator logic is tricky across versions, but `await nextCmd` usually fetches one batch (default 1).
            
            # Note: With the fix from debug script, nextCmd might return the result tuple directly in this environment
            for varBind in varBinds: # Iterate the Row
                if isinstance(varBind, list) and len(varBind) > 0: 
                    item = varBind[0]  # Extract ObjectType from list
                    val = item[1]      # Extract value from ObjectType
                else: 
                    val = varBind[1]
                
                try: return int(val)
                except: pass
    except:
        pass
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

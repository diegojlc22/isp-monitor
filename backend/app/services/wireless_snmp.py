from backend.app.services.snmp import get_shared_engine, _snmp_get, _snmp_next, detect_brand, detect_equipment_name

def decode_snmp_ip(val):
    """Decodes SNMP binary IP address or OctetString to dot-decimal string or MAC."""
    if not val:
        return None
        
    # Se já for uma string legível de IP
    if isinstance(val, str) and '.' in val and all(x.isdigit() for x in val.split('.') if x):
        return val

    # Tenta extrair bytes dos tipos do pysnmp (OctetString, IpAddress, etc)
    try:
        if hasattr(val, 'asOctets'):
            b = val.asOctets()
        else:
            b = bytes(val)
            
        # 4 Bytes = IPv4
        if len(b) == 4:
            return ".".join(map(str, b))
        
        # 6 Bytes = MAC Address
        if len(b) == 6:
            return ":".join(f"{x:02X}" for x in b)
            
        # Se for uma string hexadecimal (ex: 0xC0A80101)
        s = str(val)
        if s.startswith('0x'):
            hex_val = s[2:]
            if len(hex_val) == 8: # IP
                parts = [int(hex_val[i:i+2], 16) for i in range(0, 8, 2)]
                return ".".join(map(str, parts))
            if len(hex_val) == 12: # MAC
                parts = [hex_val[i:i+2].upper() for i in range(0, 12, 2)]
                return ":".join(parts)
            
    except:
        pass
        
    return str(val)

async def detect_equipment_type(ip, brand, community, port=161):
    """
    Auto-detects if equipment is a Station (client) or Transmitter (AP).
    Returns: 'station', 'transmitter', or 'other'
    """
    try:
        clients = await get_connected_clients_count(ip, brand, community, port)
        if clients is not None and clients > 0:
            return 'transmitter'
            
        stats = await get_wireless_stats(ip, brand, community, port)
        if stats['signal_dbm'] is not None:
            return 'station'
            
        if brand.lower() == 'ubiquiti':
            varBinds = await _snmp_get(ip, community, ['1.3.6.1.4.1.41112.1.4.1.1.4.1'], port)
            if varBinds:
                mode = str(varBinds[0][1]).lower()
                if 'ap' in mode or 'master' in mode: return 'transmitter'
                elif 'sta' in mode or 'station' in mode or 'client' in mode: return 'station'
                    
        elif brand.lower() == 'mikrotik':
            if stats['signal_dbm'] is not None or stats['ccq'] is not None:
                return 'station'
    except: pass
    return 'other'

# OID Map
OIDS = {
    'ubiquiti': {
        'signal': [
            '1.3.6.1.4.1.41112.1.10.1.4.1.5', # LTU
            '1.3.6.1.4.1.41112.1.4.7.1.3',    # AC Sta
            '1.3.6.1.4.1.41112.1.4.5.1.5',    # AirMAX
            '1.3.6.1.4.1.41112.1.4.1.1.5.1'   # Radio
        ],
        'ccq': [
            '1.3.6.1.4.1.41112.1.10.1.4.1.21', # LTU
            '1.3.6.1.4.1.41112.1.4.6.1.3',    # AC Qual
            '1.3.6.1.4.1.41112.1.4.6.1.4',    # AC Cap
            '1.3.6.1.4.1.41112.1.4.5.1.7',     # CCQ
            '1.3.6.1.4.1.41112.1.4.7.1.6'
        ],
        'clients': [
            '1.3.6.1.4.1.41112.1.10.1.4',      # LTU
            '1.3.6.1.4.1.41112.1.4.5.1.15'     # AC/M5
        ]
    },
    'mikrotik': {
        'signal': ['1.3.6.1.4.1.14988.1.1.1.2.1.19', '1.3.6.1.4.1.14988.1.1.1.1.1.4'],
        'ccq': ['1.3.6.1.4.1.14988.1.1.1.3.1.10', '1.3.6.1.4.1.14988.1.1.1.1.1.10'],
        'clients': '1.3.6.1.4.1.14988.1.1.1.3.1.6'
    },
    'mimosa': {
        'signal': ['1.3.6.1.4.1.43356.2.1.2.6.2.1.8'],
        'snr': '1.3.6.1.4.1.43356.2.1.2.6.3.1.3'
    },
    'intelbras': {
        'signal': ['1.3.6.1.4.1.32750.3.10.1.2.1.1.14.4', '1.3.6.1.4.1.32761.3.5.1.2.1.1.14', '1.3.6.1.4.1.14988.1.1.1.2.1.19'],
        'ccq': ['1.3.6.1.4.1.32761.3.8.1.3.1.1.80', '1.3.6.1.4.1.41112.1.4.5.1.7'],
        'clients': ['1.3.6.1.4.1.32761.3.5.1.2.1.1.16', '1.3.6.1.4.1.41112.1.4.5.1.15']
    }
}

async def get_snmp_value(ip, community, oid, port=161, timeout=2.0):
    varBinds = await _snmp_get(ip, community, [oid], port, timeout=timeout)
    if not varBinds: return None
    val = varBinds[0][1]
    try: return int(val)
    except: return str(val)

async def get_snmp_walk_first(ip, community, root_oid, port=161, timeout=2.0):
    varBinds = await _snmp_next(ip, community, root_oid, port, timeout=timeout)
    if not varBinds: return None
    for varBind in varBinds:
        val = varBind[0][1] if isinstance(varBind, (list, tuple)) else varBind[1]
        try: return int(val)
        except: pass
    return None

async def snmp_walk_list(ip, community, root_oid, port=161, timeout=2.0):
    """Executes a Walk and returns ALL values found as a list of raw objects."""
    results = []
    try:
        from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        engine = get_shared_engine()
        auth = CommunityData(community, mpModel=1)
        target = UdpTransportTarget((ip, port), timeout=timeout, retries=1)
        curr_oid = ObjectIdentity(root_oid)
        safety_counter = 0
        while safety_counter < 1000:
            safety_counter += 1
            try:
                errorIndication, errorStatus, errorIndex, varBindTable = await nextCmd(
                    engine, auth, target, ContextData(), ObjectType(curr_oid), lexicographicMode=False
                )
                if errorIndication or errorStatus or not varBindTable: break
                for varBinds in varBindTable:
                    for oid, val in varBinds:
                        if not str(oid).startswith(root_oid): return results
                        results.append(val) # Store raw object
                        curr_oid = oid
            except: break
    except: pass
    return results

async def get_neighbors_data(ip, brand, community, port=161):
    """Tries to get neighbor IPs/MACs via MNDP or LLDP."""
    neighbors = []
    try:
        if brand.lower() == 'mikrotik':
            ips = await snmp_walk_list(ip, community, '1.3.6.1.4.1.14988.1.1.11.1.1.3', port)
            names = await snmp_walk_list(ip, community, '1.3.6.1.4.1.14988.1.1.11.1.1.6', port)
            for i, raw_ip in enumerate(ips):
                 remote_ip = decode_snmp_ip(raw_ip)
                 if remote_ip and remote_ip != '0.0.0.0':
                     name = str(names[i]) if i < len(names) else None
                     neighbors.append({'ip': remote_ip, 'name': name})
                     
        elif brand.lower() == 'ubiquiti':
            try:
                lldp_ips = await snmp_walk_list(ip, community, '1.0.8802.1.1.2.1.4.2.1.3', port)
                lldp_names = await snmp_walk_list(ip, community, '1.0.8802.1.1.2.1.4.1.1.9', port)
                for i, raw_ip in enumerate(lldp_ips):
                    remote_ip = decode_snmp_ip(raw_ip)
                    if remote_ip and remote_ip != '0.0.0.0':
                        name = str(lldp_names[i]) if i < len(lldp_names) else None
                        neighbors.append({'ip': remote_ip, 'name': name})
            except: pass

        if not neighbors:
             generic_raw = await snmp_walk_list(ip, community, '1.0.8802.1.1.2.1.4.2.1.3', port)
             for raw_ip in generic_raw:
                 remote_ip = decode_snmp_ip(raw_ip)
                 if remote_ip and remote_ip != '0.0.0.0' and remote_ip not in [n['ip'] for n in neighbors]:
                     neighbors.append({'ip': remote_ip, 'name': 'Neighbor'})
    except Exception as e:
        from loguru import logger
        logger.warning(f"Error getting neighbors for {ip}: {e}")
    return neighbors

async def get_wireless_stats(ip, brand, community, port=161, interface_index=None, equipment_type=None):
    stats = {'signal_dbm': None, 'ccq': None}
    brand_key = brand.lower()
    if brand_key == 'mikrotik' and interface_index:
        try:
            val_dbm = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.19.1.1.10.{interface_index}', port)
            if val_dbm:
                stats['signal_dbm'] = round(float(val_dbm) / 1000.0, 2)
                return stats
        except: pass

    if brand_key not in OIDS: return stats
    for oid in OIDS[brand_key].get('signal', []):
        sig = await get_snmp_value(ip, community, oid, port)
        if sig is not None and isinstance(sig, int) and sig != 0:
            stats['signal_dbm'] = sig if sig < 0 else -sig
            break
    for oid in OIDS[brand_key].get('ccq', []):
        ccq = await get_snmp_value(ip, community, oid, port)
        if ccq is not None and isinstance(ccq, int):
            stats['ccq'] = ccq
            break
    return stats

async def get_connected_clients_count(ip, brand, community, port=161):
    brand_key = brand.lower()
    if brand_key not in OIDS: return None
    oids = OIDS[brand_key].get('clients', [])
    if isinstance(oids, str): oids = [oids]
    for oid in oids:
        count = await get_snmp_value(ip, community, oid, port)
        if count is not None and isinstance(count, int): return count
    return None

async def get_health_stats(ip, brand, community, port=161):
    stats = {'cpu_usage': None, 'memory_usage': None, 'disk_usage': None, 'temperature': None, 'voltage': None}
    if brand.lower() == 'mikrotik':
        cpu = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.3.3.1.2.1', port)
        if cpu: stats['cpu_usage'] = int(cpu)
        temp = await get_snmp_value(ip, community, '1.3.6.1.4.1.14988.1.1.3.11.0', port)
        if temp: stats['temperature'] = round(float(temp) / 10.0, 1)
        volt = await get_snmp_value(ip, community, '1.3.6.1.4.1.14988.1.1.3.8.0', port)
        if volt: stats['voltage'] = round(float(volt) / 10.0, 1)
    return stats

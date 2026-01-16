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
            '1.3.6.1.4.1.41112.1.4.5.1.5',    # AirMAX (M5/M2)
            '1.3.6.1.4.1.41112.1.4.7.1.3',    # AC Station Table
            '1.3.6.1.4.1.41112.1.10.1.4.1.5', # LTU
            '1.3.6.1.4.1.41112.1.3.2.1.11.1', # AirFiber Chain 0
            '1.3.6.1.4.1.41112.1.4.1.1.5.1',  # Legacy Radio Signal
        ],
        'ccq': [
            '1.3.6.1.4.1.41112.1.4.5.1.7',    # AirMAX CCQ
            '1.3.6.1.4.1.41112.1.4.7.1.6',    # AC Station CCQ
            '1.3.6.1.4.1.41112.1.4.6.1.3',    # AC Quality
            '1.3.6.1.4.1.41112.1.10.1.4.1.21' # LTU Quality
        ],
        'clients': [
            '1.3.6.1.4.1.41112.1.4.5.1.15',    # AirMAX Clients
            '1.3.6.1.4.1.41112.1.10.1.4'       # LTU Clients
        ]
    },
    'mikrotik': {
        'signal': [
            '1.3.6.1.4.1.14988.1.1.1.2.1.3',    # Strength Average
            '1.3.6.1.4.1.14988.1.1.1.2.1.19',   # Registration Table Signal
            '1.3.6.1.4.1.14988.1.1.1.1.1.4'     # Interface Table Signal
        ],
        'ccq': [
            '1.3.6.1.4.1.14988.1.1.1.3.1.10',   # Overall CCQ
            '1.3.6.1.4.1.14988.1.1.1.1.1.10'    # Wlan Interface CCQ
        ],
        'clients': [
            '1.3.6.1.4.1.14988.1.1.1.3.1.6',    # Stat Registered Clients
            '1.3.6.1.4.1.14988.1.1.1.1.1.6'     # Interface Registered Clients
        ]
    },
    'mimosa': {
        'signal': [
            '1.3.6.1.4.1.43356.2.1.2.6.2.1.8.1', # Rx Power Chain 1
            '1.3.6.1.4.1.43356.2.1.2.6.2.1.8.2'  # Rx Power Chain 2
        ],
        'snr': '1.3.6.1.4.1.43356.2.1.2.6.3.1.3.1'
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
    
    # 1. Tentar busca direta por índice se fornecido (MikroTik Wireless Interface Table)
    if brand_key == 'mikrotik' and interface_index:
        try:
            # mtxrWlStatSignalStrength OID .1.3.6.1.4.1.14988.1.1.1.1.1.4 + index
            val_dbm = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.1.1.1.4.{interface_index}', port)
            if not val_dbm:
                # Tentativa secundária mtxrWlRtabSignalStrength (Tabela de Registro)
                val_dbm = await get_snmp_walk_first(ip, community, f'1.3.6.1.4.1.14988.1.1.1.2.1.19.{interface_index}', port)
                
            if val_dbm:
                try:
                    stats['signal_dbm'] = int(val_dbm) if int(val_dbm) < 0 else -int(val_dbm)
                except: pass
        except: pass

    if brand_key not in OIDS: return stats
    
    # 2. Busca Gerencial por OIDs conhecidas
    if stats['signal_dbm'] is None:
        for oid in OIDS[brand_key].get('signal', []):
            # Tenta Get Direto (.0) ou Walk First (fallback para índices dinâmicos)
            sig = await get_snmp_value(ip, community, f"{oid}.0", port) # Tenta .0 primeiro
            if sig is None:
                sig = await get_snmp_value(ip, community, oid, port) # Tenta puro
            if sig is None:
                # Tenta explicitamente com o índice 1 (comum em Ubiquiti)
                sig = await get_snmp_value(ip, community, f"{oid}.1", port)
            if sig is None:
                sig = await get_snmp_walk_first(ip, community, oid, port) # Tenta walk
                
            if sig is not None and isinstance(sig, (int, float)) and sig != 0:
                # Validação de sinal Realista: -100 a -10 dBm
                # Isso evita que códigos de status (ex: 1, 2, 5) sejam confundidos com sinal
                candidate = int(sig) if sig < 0 else -int(sig)
                if -100 <= candidate <= -10:
                    stats['signal_dbm'] = candidate
                    break
                
    if stats['ccq'] is None:
        for oid in OIDS[brand_key].get('ccq', []):
            ccq = await get_snmp_value(ip, community, f"{oid}.0", port)
            if ccq is None:
                ccq = await get_snmp_value(ip, community, oid, port)
            if ccq is None:
                ccq = await get_snmp_walk_first(ip, community, oid, port)
                
            if ccq is not None and isinstance(ccq, (int, float)):
                stats['ccq'] = int(ccq)
                break
                
    return stats

async def get_connected_clients_count(ip, brand, community, port=161):
    brand_key = brand.lower()
    if brand_key not in OIDS: return None
    oids = OIDS[brand_key].get('clients', [])
    if isinstance(oids, str): oids = [oids]
    
    for oid in oids:
        # Para APs, o total pode ser a soma de múltiplas interfaces ou um OID central
        # Primeiro tentamos o OID direto
        count = await get_snmp_value(ip, community, f"{oid}.0", port)
        if count is None:
            count = await get_snmp_value(ip, community, oid, port)
        
        # Se falhar, tentamos dar um walk para ver se é uma tabela de interfaces
        if count is None:
            vals = await snmp_walk_list(ip, community, oid, port)
            if vals:
                try:
                    return sum(int(v) for v in vals if str(v).isdigit())
                except: pass
        
        if count is not None and isinstance(count, (int, float)): 
            return int(count)
            
    return None

async def get_health_stats(ip, brand, community, port=161):
    stats = {'cpu_usage': None, 'memory_usage': None, 'disk_usage': None, 'temperature': None, 'voltage': None}
    brand_key = brand.lower()
    
    if brand_key == 'mikrotik':
        # Batch Get for Mikrotik Health
        oids = [
            '1.3.6.1.2.1.25.3.3.1.2.1',       # CPU
            '1.3.6.1.4.1.14988.1.1.3.11.0',    # Temp
            '1.3.6.1.4.1.14988.1.1.3.8.0'      # Voltage
        ]
        results = await _snmp_get(ip, community, oids, port)
        if results and len(results) >= 3:
            cpu = results[0][1]
            temp = results[1][1]
            volt = results[2][1]
            
            if cpu is not None and str(cpu) != "": stats['cpu_usage'] = int(cpu)
            if temp is not None and str(temp) != "": stats['temperature'] = round(float(temp) / 10.0, 1)
            if volt is not None and str(volt) != "": stats['voltage'] = round(float(volt) / 10.0, 1)
            
    elif brand_key == 'ubiquiti':
        # Batch Get for UBNT (Attempt common OIDs)
        oids = [
            '1.3.6.1.4.1.41112.1.4.1.1.11.1', # Voltage AC v1
            '1.3.6.1.4.1.41112.1.4.1.1.11.0', # Voltage AC v0
            '1.3.6.1.4.1.41112.1.4.1.1.2.0'   # Temp (Alternative)
        ]
        results = await _snmp_get(ip, community, oids, port)
        if results:
            # Check Voltages
            volt_raw = None
            if len(results) >= 1 and results[0][1] is not None and str(results[0][1]) != "":
                volt_raw = int(results[0][1])
            elif len(results) >= 2 and results[1][1] is not None and str(results[1][1]) != "":
                volt_raw = int(results[1][1])
            
            if volt_raw is not None:
                if volt_raw > 1000: # Probably mV
                    stats['voltage'] = round(float(volt_raw) / 1000.0, 1)
                elif volt_raw > 100: # Probably V*10
                    stats['voltage'] = round(float(volt_raw) / 10.0, 1)
                else:
                    stats['voltage'] = float(volt_raw)
            
            # Temp (Optional)
            if len(results) >= 3 and results[2][1] is not None and str(results[2][1]) != "":
                try: stats['temperature'] = float(results[2][1])
                except: pass

    elif brand_key == 'intelbras':
        # Voltage (APC Series)
        volt_raw = await get_snmp_value(ip, community, '1.3.6.1.4.1.32761.3.1.1.1.2.0', port)
        if volt_raw is not None and isinstance(volt_raw, int):
             stats['voltage'] = round(float(volt_raw) / 10.0, 1) if volt_raw > 100 else float(volt_raw)

    return stats

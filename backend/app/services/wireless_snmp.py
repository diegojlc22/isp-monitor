from pysnmp.hlapi.asyncio import *
from backend.app.services.snmp import get_shared_engine, _snmp_get, _snmp_next, detect_brand, detect_equipment_name

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
            '1.3.6.1.4.1.41112.1.10.1.4.1.5', # LTU Station Table Signal
            '1.3.6.1.4.1.41112.1.4.7.1.3',    # AirMAX AC Station Table Signal
            '1.3.6.1.4.1.41112.1.4.5.1.5.1',  # AirMAX M5/Legacy Generic
            '1.3.6.1.4.1.41112.1.4.1.1.5.1'   # Generic Radio Table
        ],
        'ccq': [
            '1.3.6.1.4.1.41112.1.10.1.4.1.21', # LTU Capacity/Signal Level
            '1.3.6.1.4.1.41112.1.4.6.1.3',    # AirMAX AC Quality (percentage)
            '1.3.6.1.4.1.41112.1.4.6.1.4',    # AirMAX AC Capacity (percentage)
            '1.3.6.1.4.1.41112.1.4.5.1.7.1'    # AirMAX M5/Legacy CCQ
        ],
        'clients': [
            '1.3.6.1.4.1.41112.1.10.1.4',      # LTU Station Table
            '1.3.6.1.4.1.41112.1.4.5.1.15.1'   # AirMAX M5/AC AP Client Count
        ]
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

async def snmp_walk_list(ip, community, root_oid, port=161):
    """
    Executes a Walk and returns ALL values found as a list.
    """
    varBinds = await _snmp_next(ip, community, root_oid, port)
    results = []
    if not varBinds: return results
    
    # Simple recursion or loop needed for full walk with pysnmp high-level nextCmd usually iterates 
    # but our helper _snmp_next only returns ONE batch.
    # We need to loop. Since _snmp_next helper uses nextCmd which is a generator/iterator wrapper...
    # Actually, the pysnmp `nextCmd` is an async generator. 
    # Let's implement a specific walk loop here.
    
    try:
        # Use our working helper _snmp_next to get batches
        # For a full walk, we would need a loop, but for count we can just get the first batch 
        # as most radios return the whole table in one go for small tables.
        # However, let's do it right:
        from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
        engine = get_shared_engine()
        auth = CommunityData(community, mpModel=1)
        
        curr_oid = ObjectIdentity(root_oid)
        while True:
            errorIndication, errorStatus, errorIndex, varBindTable = await nextCmd(
                engine, auth, UdpTransportTarget((ip, port), timeout=1.0, retries=1),
                ContextData(), ObjectType(curr_oid), lexicographicMode=False
            )
            
            if errorIndication or errorStatus or not varBindTable:
                break
                
            for varBinds in varBindTable:
                for vb in varBinds:
                    oid, val = vb
                    if not str(oid).startswith(root_oid):
                        return results
                    results.append(str(val))
                    curr_oid = oid
            
    except Exception as e:
        # print(f"Walk Error: {e}")
        pass
        
    return results


async def get_neighbors_data(ip, brand, community, port=161):
    """
    Tries to get neighbor IPs/MACs via MNDP or LLDP.
    Returns list of {'ip': ..., 'mac': ...}
    """
    neighbors = []
    
    try:
        if brand == 'mikrotik':
            # MNDP IP Address (.1.3.6.1.4.1.14988.1.1.11.1.1.3)
            ips = await snmp_walk_list(ip, community, '1.3.6.1.4.1.14988.1.1.11.1.1.3', port)
            # MNDP Identity (.1.3.6.1.4.1.14988.1.1.11.1.1.6)
            names = await snmp_walk_list(ip, community, '1.3.6.1.4.1.14988.1.1.11.1.1.6', port)
            
            for i, remote_ip in enumerate(ips):
                 # Basic filtering
                 if remote_ip and remote_ip != '0.0.0.0':
                     name = names[i] if i < len(names) else None
                     neighbors.append({'ip': remote_ip, 'name': name})
                     
        # Generic LLDP (Management Address)
        # 1.0.8802.1.1.2.1.4.2.1.3
        # This is complex because index includes specific subtypes.
        
    except Exception as e:
        print(f"Error getting neighbors for {ip}: {e}")
        
    return neighbors

async def get_wireless_stats(ip, brand, community, port=161, interface_index=None, equipment_type=None):
    """
    Fetches Signal and CCQ based on brand.
    Supports Wireless and Fiber (SFP).
    Returns dict: {'signal_dbm': int, 'ccq': int}
    """
    stats = {'signal_dbm': None, 'ccq': None}
    brand_key = brand.lower()

    # --- FIBER / SFP CASE ---
    if brand_key == 'mikrotik' and interface_index:
        try:
            # 1. Try New SFP Monitor Table (OID .1.3.6.1.4.1.14988.1.1.19.1.1)
            # Field 10 is RX Power in dBm * 1000
            val_dbm = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.19.1.1.10.{interface_index}', port)
            if val_dbm is not None:
                try:
                    stats['signal_dbm'] = round(float(val_dbm) / 1000.0, 2)
                    return stats
                except: pass

            # 2. Fallback to Linear uW Table (.14)
            val_uw = await get_snmp_value(ip, community, f'1.3.6.1.4.1.14988.1.1.14.1.1.15.{interface_index}', port)
            if val_uw is not None and isinstance(val_uw, (int, float)) and val_uw > 0:
                import math
                dbm = 10 * math.log10(float(val_uw) / 1000.0)
                stats['signal_dbm'] = round(dbm, 2)
            
            return stats
        except:
            pass

    if brand_key not in OIDS:
        return stats
        
    signal_oid = OIDS[brand_key].get('signal')
    ccq_oid = OIDS[brand_key].get('ccq')
    
    # Fetch Signal
    if signal_oid:
        # Support list of OIDs for fallback
        oids_to_try = signal_oid if isinstance(signal_oid, list) else [signal_oid]
        for oid in oids_to_try:
            sig = None
            # Special handling for table roots (Require WALK)
            walk_roots = [
                '1.3.6.1.4.1.41112.1.10.1.4.1.5', # LTU
                '1.3.6.1.4.1.41112.1.4.7.1.3',    # AirMAX AC StaTable
                '1.3.6.1.4.1.14988.1.1.1.2.1.19', # Mikrotik Sta Signal
                '1.3.6.1.4.1.43356.2.1.2.6.2.1.8' # Mimosa
            ]
            
            if any(oid.startswith(root) for root in walk_roots) or len(oid.split('.')) < 12:
                sig = await get_snmp_walk_first(ip, community, oid, port)
            else:
                sig = await get_snmp_value(ip, community, oid, port)
                
            if sig is not None:
                 if isinstance(sig, int):
                     if sig == 0: continue 
                     if sig > 0: sig = -sig
                     stats['signal_dbm'] = sig
                     break
              
    # Fetch CCQ / Quality
    if ccq_oid:
        oids_to_try = ccq_oid if isinstance(ccq_oid, list) else [ccq_oid]
        for oid in oids_to_try:
            ccq = None
            walk_roots = [
                '1.3.6.1.4.1.41112.1.10.1.4.1.21', # LTU
                '1.3.6.1.4.1.41112.1.4.6.1.3',    # Quality
                '1.3.6.1.4.1.41112.1.4.6.1.4',    # Capacity
                '1.3.6.1.4.1.14988.1.1.1.3.1.10', # Mikrotik
                '1.3.6.1.4.1.14988.1.1.1.1.1.10'
            ]
            if any(oid.startswith(root) for root in walk_roots) or len(oid.split('.')) < 12:
                ccq = await get_snmp_walk_first(ip, community, oid, port)
            else:
                ccq = await get_snmp_value(ip, community, oid, port)
                
            if ccq is not None and isinstance(ccq, int):
                stats['ccq'] = ccq
                break
    
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
    if brand_key not in OIDS: return None
    
    clients_oid_data = OIDS[brand_key].get('clients')
    if not clients_oid_data: return None
    
    oids_to_try = clients_oid_data if isinstance(clients_oid_data, list) else [clients_oid_data]
    
    for oid in oids_to_try:
        # Special case: LTU Table Walk
        if oid == '1.3.6.1.4.1.41112.1.10.1.4':
            try:
                 rows = await snmp_walk_list(ip, community, '1.3.6.1.4.1.41112.1.10.1.4.1.11', port)
                 if rows: return len(set(rows))
            except: continue
        
        # Standard OID Get
        try:
            count = await get_snmp_value(ip, community, oid, port)
            if count is not None and isinstance(count, int):
                return count
        except: continue
            
    return None

async def get_health_stats(ip, brand, community, port=161):
    """
    Fetches Health Stats (CPU, Temperature, Voltage) based on brand.
    Primarily for MikroTik.
    Returns dict: {'cpu_usage': int, 'temperature': float, 'voltage': float}
    """
    stats = {
        'cpu_usage': None, 
        'memory_usage': None, 
        'disk_usage': None, 
        'temperature': None, 
        'voltage': None
    }
    brand_key = brand.lower()

    if brand_key == 'mikrotik':
        # 1. CPU Load
        try:
            cpu = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.3.3.1.2.1', port)
            if cpu is not None:
                stats['cpu_usage'] = int(cpu)
            else:
                cpu_walk = await get_snmp_walk_first(ip, community, '1.3.6.1.2.1.25.3.3.1.2', port)
                if cpu_walk is not None: stats['cpu_usage'] = int(cpu_walk)
        except: pass

        # --- DYNAMIC STORAGE LOOKUP (RAM/DISK) ---
        try:
            # Helper to walk an OID and return dict {index: value_str}
            async def snmp_walk_map(oid_root):
                mapping = {}
                from pysnmp.hlapi.asyncio import nextCmd, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, SnmpEngine
                engine = SnmpEngine()
                auth = CommunityData(community, mpModel=1)
                target = UdpTransportTarget((ip, port), timeout=2, retries=1)
                curr_oid = ObjectIdentity(oid_root)
                
                while True:
                    try:
                        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
                            engine, auth, target, ContextData(), ObjectType(curr_oid), lexicographicMode=False
                        )
                        if errorIndication or errorStatus or not varBinds: break
                        
                        oid, val = varBinds[0]
                        str_oid = str(oid)
                        if not str_oid.startswith(oid_root): break
                        
                        idx = str_oid.split('.')[-1]
                        mapping[idx] = str(val)
                        curr_oid = oid
                    except: break
                return mapping

            # Walk Descriptions: .1.3.6.1.2.1.25.2.3.1.3
            storage_descs = await snmp_walk_map('1.3.6.1.2.1.25.2.3.1.3')
            
            ram_idx = None
            disk_idx = None
            
            for idx, desc in storage_descs.items():
                d_lower = desc.lower()
                if 'main memory' in d_lower or 'ram' in d_lower:
                    ram_idx = idx
                elif 'flash' in d_lower or 'system disk' in d_lower or 'hard disk' in d_lower:
                    # Prefer flash/system over others if multiple, but first found is ok
                    if not disk_idx: disk_idx = idx

            # Get Values if indices found
            if ram_idx:
                try:
                    total = await get_snmp_value(ip, community, f'1.3.6.1.2.1.25.2.3.1.5.{ram_idx}', port)
                    used = await get_snmp_value(ip, community, f'1.3.6.1.2.1.25.2.3.1.6.{ram_idx}', port)
                    if total and used and int(total) > 0:
                        stats['memory_usage'] = round((int(used) / int(total)) * 100)
                except: pass
            else:
                 # Fallback Legacy
                try:
                    total_ram = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.2.3.1.5.65536', port)
                    used_ram = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.2.3.1.6.65536', port)
                    if total_ram and used_ram and int(total_ram) > 0:
                        stats['memory_usage'] = round((int(used_ram) / int(total_ram)) * 100)
                except: pass

            if disk_idx:
                try:
                    total = await get_snmp_value(ip, community, f'1.3.6.1.2.1.25.2.3.1.5.{disk_idx}', port)
                    used = await get_snmp_value(ip, community, f'1.3.6.1.2.1.25.2.3.1.6.{disk_idx}', port)
                    if total and used and int(total) > 0:
                        stats['disk_usage'] = round((int(used) / int(total)) * 100)
                except: pass
            else:
                # Fallback Legacy
                try:
                    total = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.2.3.1.5.131072', port)
                    used = await get_snmp_value(ip, community, '1.3.6.1.2.1.25.2.3.1.6.131072', port)
                    if total and used and int(total) > 0:
                        stats['disk_usage'] = round((int(used) / int(total)) * 100)
                except: pass

        except Exception as e:
            # print(f"Storage Error: {e}")
            pass

        # 4. Temperature
        try:
            # Try OIDs: .11 (Device), .10 (Old Device), .14 (CPU), .6 (Old CPU)
            for oid in ['1.3.6.1.4.1.14988.1.1.3.11.0', '1.3.6.1.4.1.14988.1.1.3.10.0', '1.3.6.1.4.1.14988.1.1.3.14.0', '1.3.6.1.4.1.14988.1.1.3.6.0']:
                temp = await get_snmp_value(ip, community, oid, port)
                if temp is not None:
                    # Mikrotik is usually decidegrees (e.g. 570 = 57.0C)
                    stats['temperature'] = round(float(temp) / 10.0, 1)
                    break
        except: pass

        # 5. Voltage
        voltage_oids = [
            '1.3.6.1.4.1.14988.1.1.3.8.0',  # Standard System Voltage
            '1.3.6.1.4.1.14988.1.1.3.1.0',  # Input Voltage
            '1.3.6.1.4.1.14988.1.1.3.17.0', # PSU1 Voltage (Newer CRS/CCR)
            '1.3.6.1.4.1.14988.1.1.3.18.0'  # PSU2 Voltage
        ]
        
        for oid in voltage_oids:
            try:
                volt = await get_snmp_value(ip, community, oid, port)
                
                # Check for None or empty string
                if volt is None: continue
                volt_str = str(volt).strip()
                if not volt_str: continue
                
                try:
                    raw_val = float(volt_str)
                except ValueError:
                    continue
                    
                if raw_val <= 0: continue
                
                # Smart Scaling
                final_v = raw_val
                
                # Case 1: Decivolts (Most common, e.g. 245 -> 24.5V)
                # Range 10V to 90V (100-900)
                if 100 <= raw_val <= 900: 
                    final_v = raw_val / 10.0
                
                # Case 2: High Values (centi-volts or milli-volts)
                # e.g. 7560 
                elif raw_val > 900:
                    v_cV = raw_val / 100.0   # 7560 -> 75.6V
                    v_mV = raw_val / 1000.0  # 7560 -> 7.56V
                    
                    # Heuristic: Prefer standard telecom/network ranges (10V-60V)
                    if 10 <= v_cV <= 60:
                        final_v = v_cV
                    else:
                        # Fallback to mV (likely internal rail like 3.3V, 5V, 12V, or just modest voltage)
                        final_v = v_mV
                        
                # Case 3: Already Volts (e.g. 24)
                elif 3 <= raw_val <= 100:
                    final_v = raw_val
                    
                stats['voltage'] = round(final_v, 1)
                break 
            except: 
                continue

    return stats

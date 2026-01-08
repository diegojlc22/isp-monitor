import asyncio
import time
from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd, nextCmd, SnmpEngine
from loguru import logger

# Shared engine to avoid overhead
_snmp_engine = None

def get_shared_engine():
    global _snmp_engine
    if _snmp_engine is None:
        _snmp_engine = SnmpEngine()
    return _snmp_engine

async def _snmp_get(ip, community, oids, port=161, timeout=1.0):
    """Internal helper to try SNMP get with v2c then v1"""
    # Try SNMPv2c first
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=1), # v2c
            UdpTransportTarget((ip, port), timeout=timeout, retries=0),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        if not errorIndication and not errorStatus:
            return varBinds
    except Exception as e:
        logger.debug(f"[SNMP] v2c Get Error {ip}: {e}")

    # Try SNMPv1 fallback
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=0), # v1
            UdpTransportTarget((ip, port), timeout=timeout, retries=0),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        if not errorIndication and not errorStatus:
            return varBinds
    except Exception as e:
        logger.debug(f"[SNMP] v1 Get Error {ip}: {e}")
    
    return None

async def _snmp_next(ip, community, root_oid, port=161, timeout=1.0):
    """Internal helper to try SNMP walk/next with v2c then v1"""
    # Try SNMPv2c
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            engine,
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, port), timeout=timeout, retries=0),
            ContextData(),
            ObjectType(ObjectIdentity(root_oid)),
            lexicographicMode=False
        )
        if not errorIndication and not errorStatus and varBinds:
            return varBinds
    except Exception as e:
        logger.debug(f"[SNMP] v2c Next Error {ip}: {e}")

    # Try SNMPv1
    try:
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            engine,
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, port), timeout=timeout, retries=0),
            ContextData(),
            ObjectType(ObjectIdentity(root_oid)),
            lexicographicMode=False
        )
        if not errorIndication and not errorStatus and varBinds:
            return varBinds
    except Exception as e:
        logger.debug(f"[SNMP] v1 Next Error {ip}: {e}")

    return None

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

    # Test Ubiquiti Private MIB root
    if await _snmp_next(ip, community, '1.3.6.1.4.1.41112', port): return 'ubiquiti'
    
    # Test Intelbras
    if await _snmp_next(ip, community, '1.3.6.1.4.1.26138', port): return 'intelbras'
    
    # Test Mikrotik
    if await _snmp_next(ip, community, '1.3.6.1.4.1.14988', port): return 'mikrotik'
    
    return 'generic'

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


async def get_snmp_uptime(ip: str, community: str = "public", port: int = 161) -> int | None:
    """
    Get System Uptime (sysUpTime) via SNMP v2c.
    Returns uptime in ticks (1/100s).
    """
    async def _snmp_get():
        engine = get_shared_engine()
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=0),  # v1
            UdpTransportTarget((ip, port), timeout=4, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.3.0')) # sysUpTime
        )
        
        if errorIndication or errorStatus:
            return None
        
        for varBind in varBinds:
            # Return value
            return int(varBind[1])
        return None

    try:
        # Now natively async
        val = await _snmp_get()
        return val
    except Exception:
        return None

async def get_snmp_interface_traffic(ip: str, community: str = "public", port: int = 161, interface_index: int = 1, brand: str = None):
    """
    Get In/Out Octets for a specific interface.
    Returns (in_bytes, out_bytes) or None.
    
    1. Tries 64-bit counters (ifHCInOctets/ifHCOutOctets) via SNMP v2c (Preferred for Gibabit+).
    2. Fallback to 32-bit counters (ifInOctets/ifOutOctets) via SNMP v1.
    3. Special support for Ubiquiti LTU (AirFiber 5XHD) private OIDs.
    """
    from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
    
    # --- GENERIC UBIQUITI PRIVATE MIB STRATEGY ---
    if brand == 'ubiquiti':
        # List of potential counter pairs (In, Out) for UBNT devices
        ubnt_strategies = []
        
        # 1. LTU / AirFiber 5XHD (Specifically for our virtual index)
        if interface_index == 1000:
            ubnt_strategies.append(('1.3.6.1.4.1.41112.1.10.1.5.3.0', '1.3.6.1.4.1.41112.1.10.1.5.1.0')) # LTU Wireless
        
        # 2. AirFiber Classic (AF24, AF5 - from User MIB)
        ubnt_strategies.append((f'1.3.6.1.4.1.41112.1.3.3.1.66.{interface_index}', f'1.3.6.1.4.1.41112.1.3.3.1.64.{interface_index}'))
        
        # 3. AirMAX AC Station Table (Counter64 from MIB)
        # ubntStaRxBytes: .1.3.6.1.4.1.41112.1.4.7.1.14, ubntStaTxBytes: .1.3.6.1.4.1.41112.1.4.7.1.13
        ubnt_strategies.append((f'1.3.6.1.4.1.41112.1.4.7.1.14.{interface_index}', f'1.3.6.1.4.1.41112.1.4.7.1.13.{interface_index}'))
        
        engine = get_shared_engine()
        for oid_in, oid_out in ubnt_strategies:
            try:
                errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
                    engine,
                    CommunityData(community, mpModel=1), # v2c preferred
                    UdpTransportTarget((ip, port), timeout=3, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid_in)),
                    ObjectType(ObjectIdentity(oid_out))
                )
                if not errorIndication and not errorStatus and varBinds:
                    # Verify they are actual numbers
                    res_in, res_out = varBinds[0][1], varBinds[1][1]
                    if str(res_in) != "" and str(res_out) != "":
                        return (int(res_in), int(res_out))
            except Exception:
                continue

    # Standard OIDs (RFC1213 / IF-MIB)
    # 32-bit
    oid_in_32 = f'1.3.6.1.2.1.2.2.1.10.{interface_index}'
    oid_out_32 = f'1.3.6.1.2.1.2.2.1.16.{interface_index}'
    # 64-bit (High Capacity)
    oid_in_64 = f'1.3.6.1.2.1.31.1.1.1.6.{interface_index}'
    oid_out_64 = f'1.3.6.1.2.1.31.1.1.1.10.{interface_index}'

    engine = get_shared_engine()
    
    # 1. Tentar 64-bit (v2c) - IF-MIB standard
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=1), # v2c
            UdpTransportTarget((ip, port), timeout=4, retries=2),
            ContextData(),
            ObjectType(ObjectIdentity(oid_in_64)),
            ObjectType(ObjectIdentity(oid_out_64))
        )
        
        if not errorIndication and not errorStatus and varBinds:
             return (int(varBinds[0][1]), int(varBinds[1][1]))
    except Exception:
        pass # Fallback

    # 2. Fallback para 32-bit (v1)
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=0), # v1
            UdpTransportTarget((ip, port), timeout=2, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity(oid_in_32)),
            ObjectType(ObjectIdentity(oid_out_32))
        )
        
        if not errorIndication and not errorStatus and varBinds:
             return (int(varBinds[0][1]), int(varBinds[1][1]))
    except Exception:
        pass
        
    return None
async def get_snmp_interfaces(ip: str, community: str = "public", port: int = 161):
    """
    Lists all interfaces (index and description) using SNMP walk on ifDescr.
    """
    interfaces = []
    
    # Check Brand First
    brand = await detect_brand(ip, community, port)
    
    # If Ubiquiti, inject our virtual highly-optimized interface
    if brand == 'ubiquiti':
         interfaces.append({"index": 1000, "name": "Wireless (UBNT AirFiber/LTU)"})

    root_oid = '1.3.6.1.2.1.2.2.1.2' # ifDescr
    
    try:
        engine = get_shared_engine()
        # Try v2c first, fallback to v1
        for version in [1, 0]: # 1=v2c, 0=v1
            auth = CommunityData(community, mpModel=version)
            target = UdpTransportTarget((ip, port), timeout=2, retries=1)
            
            curr_oid = ObjectIdentity(root_oid)
            found_version = False
            
            while True:
                errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
                    engine, auth, target, ContextData(),
                    ObjectType(curr_oid),
                    lexicographicMode=False
                )
                
                if errorIndication or errorStatus or not varBinds:
                    break
                
                found_version = True
                oid, val = varBinds[0][0]
                
                if not str(oid).startswith(root_oid):
                    break
                    
                idx = str(oid).split('.')[-1]
                interfaces.append({"index": int(idx), "name": str(val)})
                curr_oid = oid
                
            if found_version:
                break
    except Exception as e:
        print(f"Error scanning interfaces for {ip}: {e}")
        
    return interfaces

def copy_iface(iface, mbps):
    return {"index": iface['index'], "name": iface['name'], "current_mbps": round(mbps, 2)}

async def measure_interfaces_traffic(ip: str, community: str = "public", port: int = 161, interfaces: list = None, brand: str = None, sample_time: int = 3):
    """
    Measures traffic on a set of interfaces for a given sample time.
    Returns a list of interfaces that have traffic (> 0 Mbps), sorted by total traffic descending.
    """
    if not interfaces:
        return []

    sem = asyncio.Semaphore(15) # Limita concorrência

    async def fetch(idx):
        async with sem:
            try:
                res = await get_snmp_interface_traffic(ip, community, port, idx, brand=brand)
                return idx, res
            except:
                return idx, None

    # 1. First Measurement (Parallel)
    tasks = [fetch(iface['index']) for iface in interfaces]
    results_1 = await asyncio.gather(*tasks)
    
    counters_1 = {}
    timestamp_1 = time.time()
    
    for idx, res in results_1:
        if res:
            counters_1[idx] = {'in': res[0], 'out': res[1]}

    if not counters_1:
        return []

    # Wait
    await asyncio.sleep(sample_time)
    
    # 2. Second Measurement (Parallel)
    # Re-use tasks list logic but create new tasks
    tasks_2 = [fetch(idx) for idx in counters_1.keys()] # Only fetch those that worked first time
    results_2 = await asyncio.gather(*tasks_2)
    
    valid_results = []
    timestamp_2 = time.time()
    dt_base = timestamp_2 - timestamp_1
    if dt_base <= 0: dt_base = 0.001

    for idx, res in results_2:
        if not res: continue
        if idx not in counters_1: continue
        
        c1 = counters_1[idx]
        delta_in =  max(0, res[0] - c1['in'])
        delta_out = max(0, res[1] - c1['out'])
        
        # Total Mbps
        mbps_in = ((delta_in * 8) / (dt_base * 1_000_000))
        mbps_out = ((delta_out * 8) / (dt_base * 1_000_000))
        total_mbps = mbps_in + mbps_out
        
        name = next((i['name'] for i in interfaces if i['index'] == idx), str(idx))

        if total_mbps > 0.001: # Lower threshold to capture low traffic
             valid_results.append({
                'index': idx,
                'name': name,
                    'in_mbps': round(mbps_in, 2),
                    'out_mbps': round(mbps_out, 2),
                    'total_mbps': round(total_mbps, 2)
                })
    
    valid_results.sort(key=lambda x: x['total_mbps'], reverse=True)
    return valid_results

async def detect_best_interface(ip: str, community: str = "public", port: int = 161):
    """
    Measures traffic on all interfaces and returns the one with highest throughput.
    """
    # 1. List Interfaces
    interfaces = await get_snmp_interfaces(ip, community, port)
    if not interfaces:
        return None

    # Determine Brand
    brand = await detect_brand(ip, community, port)
    
    results = await measure_interfaces_traffic(ip, community, port, interfaces, brand=brand)
    
    if not results:
        return None
    
    best = results[0]
    return {"index": best['index'], "name": best['name'], "current_mbps": best['total_mbps']}

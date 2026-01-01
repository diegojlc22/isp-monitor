import asyncio
from pysnmp.hlapi.asyncio import *

# Singleton SnmpEngine to save CPU/RAM
_SHARED_SNMP_ENGINE = None

def get_shared_engine():
    global _SHARED_SNMP_ENGINE
    if _SHARED_SNMP_ENGINE is None:
        _SHARED_SNMP_ENGINE = SnmpEngine()
    return _SHARED_SNMP_ENGINE

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
            UdpTransportTarget((ip, port), timeout=1, retries=1),
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
        
        # 1. LTU / AirFiber 5XHD (Detected earlier)
        if interface_index == 1000 or interface_index == 1:
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
                    UdpTransportTarget((ip, port), timeout=1, retries=0),
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
            UdpTransportTarget((ip, port), timeout=2, retries=1),
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
    from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, nextCmd
    
    interfaces = []
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

async def detect_best_interface(ip: str, community: str = "public", port: int = 161):
    """
    Measures traffic on all interfaces for 3 seconds and returns the one with highest throughput.
    """
    import time
    
    # 1. List Interfaces
    interfaces = await get_snmp_interfaces(ip, community, port)
    if not interfaces:
        return None

    # 2. First Measurement
    counters_1 = {}
    for iface in interfaces:
        res = await get_snmp_interface_traffic(ip, community, port, iface['index'])
        if res:
            counters_1[iface['index']] = {'t': time.time(), 'in': res[0], 'out': res[1]}
    
    # Wait
    await asyncio.sleep(3)
    
    # 3. Second Measurement & Delta
    best_rate = -1.0
    best_iface = None
    
    for iface in interfaces:
        idx = iface['index']
        if idx not in counters_1: continue
        
        c1 = counters_1[idx]
        res = await get_snmp_interface_traffic(ip, community, port, idx)
        
        if res:
            dt = time.time() - c1['t']
            if dt <= 0: dt = 0.001
            
            delta_in =  max(0, res[0] - c1['in'])
            delta_out = max(0, res[1] - c1['out'])
            
            # Total Mbps
            mbps = ((delta_in + delta_out) * 8) / (dt * 1_000_000)
            
            if mbps > best_rate:
                best_rate = mbps
                best_iface = copy_iface(iface, mbps)
                
    return best_iface

def copy_iface(iface, mbps):
    return {"index": iface['index'], "name": iface['name'], "current_mbps": round(mbps, 2)}

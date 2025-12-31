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

async def get_snmp_interface_traffic(ip: str, community: str = "public", port: int = 161, interface_index: int = 1):
    """
    Get In/Out Octets for a specific interface.
    Returns (in_bytes, out_bytes) or None.
    
    1. Tries 64-bit counters (ifHCInOctets/ifHCOutOctets) via SNMP v2c (Preferred for Gibabit+).
    2. Fallback to 32-bit counters (ifInOctets/ifOutOctets) via SNMP v1.
    """
    from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
    
    # OIDs
    # 32-bit
    oid_in_32 = f'1.3.6.1.2.1.2.2.1.10.{interface_index}'
    oid_out_32 = f'1.3.6.1.2.1.2.2.1.16.{interface_index}'
    # 64-bit (High Capacity)
    oid_in_64 = f'1.3.6.1.2.1.31.1.1.1.6.{interface_index}'
    oid_out_64 = f'1.3.6.1.2.1.31.1.1.1.10.{interface_index}'

    engine = get_shared_engine()
    
    # 1. Tentar 64-bit (v2c)
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            CommunityData(community, mpModel=1), # v2c
            UdpTransportTarget((ip, port), timeout=1, retries=1),
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
            UdpTransportTarget((ip, port), timeout=1, retries=1),
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

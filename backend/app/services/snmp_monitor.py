import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog
from backend.app.services.mikrotik_api import get_mikrotik_live_traffic
from backend.app.services.snmp import get_snmp_interface_traffic
from backend.app.services.wireless_snmp import get_wireless_stats

# Config
SNMP_INTERVAL = 60 # Check SNMP every 60s

async def snmp_monitor_job():
    """
    Dedicated job for Traffic polling (SNMP + Mikrotik API) AND Wireless Stats.
    Parallelized for high performance (Semaphore limited).
    """
    import time
    print("[INFO] Traffic/Wireless Monitor started (Interval: 60s)...")
    
    # Limit Concurrency to avoid network flood
    sem = asyncio.Semaphore(20) 
    
    # Cache for bandwidth calculation (SNMP only): eq_id -> (timestamp, in_bytes, out_bytes)
    previous_counters = {} 
    
    async def fetch_device_data(eq_data):
        """
        Independent task to fetch data for one device.
        Returns a dict of updates to be applied to DB, or None.
        eq_data is a dictionary copy of the object to avoid detached instance issues.
        """
        async with sem:
            result = {"id": eq_data["id"], "updates": {}, "log": None}
            
            try:
                ip = eq_data["ip"]
                brand = eq_data.get("brand")
                community = eq_data.get("snmp_community")
                port = eq_data.get("snmp_port") or 161
                
                # --- WIRELESS STATS ---
                if brand in ['ubiquiti', 'intelbras']:
                    w_stats = await get_wireless_stats(ip, brand, community, port)
                    if w_stats['signal_dbm'] is not None:
                        result["updates"]["signal_dbm"] = w_stats['signal_dbm']
                        result["updates"]["ccq"] = w_stats['ccq']
                    
                    if eq_data.get("equipment_type") == 'transmitter': 
                        # This import needs to be inside or top-level. Top level is better but here is fine.
                        from backend.app.services.wireless_snmp import get_connected_clients_count
                        clients = await get_connected_clients_count(ip, brand, community, port)
                        if clients is not None:
                             result["updates"]["connected_clients"] = clients

                # --- TRAFFIC ---
                # A) Mikrotik API
                if eq_data.get("is_mikrotik") and eq_data.get("mikrotik_interface"):
                    traffic_data = await get_mikrotik_live_traffic(
                        ip=ip,
                        user=eq_data.get("ssh_user"),
                        password=eq_data.get("ssh_password"),
                        interface=eq_data.get("mikrotik_interface"),
                        port=eq_data.get("api_port") or 8728
                    )
                    if traffic_data:
                        in_mbps, out_mbps = traffic_data
                        result["updates"]["last_traffic_in"] = in_mbps
                        result["updates"]["last_traffic_out"] = out_mbps
                        result["log"] = (in_mbps, out_mbps)
                        return result # Done for this device
                
                # B) SNMP
                interface_idx = eq_data.get("snmp_interface_index") or 1
                traffic = await get_snmp_interface_traffic(ip, community, port, interface_idx)
                
                if traffic:
                    in_bytes, out_bytes = traffic
                    current_time_ts = time.time()
                    
                    if eq_data["id"] in previous_counters:
                        last_time, last_in, last_out = previous_counters[eq_data["id"]]
                        dt = current_time_ts - last_time
                        
                        if dt > 0:
                            delta_in = max(0, in_bytes - last_in)
                            delta_out = max(0, out_bytes - last_out)
                            
                            # Mbps
                            mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                            mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                            
                            result["updates"]["last_traffic_in"] = mbps_in
                            result["updates"]["last_traffic_out"] = mbps_out
                            result["log"] = (mbps_in, mbps_out)
                    
                    # Store for next run (in memory side-effect, safe here as single threaded event loop)
                    previous_counters[eq_data["id"]] = (current_time_ts, in_bytes, out_bytes)

                return result

            except Exception as e:
                # print(f"Error fetching {eq_data['ip']}: {e}")
                return None

    while True:
        try:
            # 1. Fetch Candidates from DB
            equipments_data = [] # List of dicts
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Equipment).where(Equipment.is_online == True))
                equipments = res.scalars().all()
                for eq in equipments:
                    if not eq.ip: continue
                    # Copy data to dict to avoid session detach issues during async gather
                    equipments_data.append({
                        "id": eq.id, "ip": eq.ip, "brand": eq.brand, 
                        "snmp_community": eq.snmp_community, "snmp_port": eq.snmp_port,
                        "ssh_user": eq.ssh_user, "ssh_password": eq.ssh_password,
                        "is_mikrotik": eq.is_mikrotik, "mikrotik_interface": eq.mikrotik_interface,
                        "api_port": eq.api_port, "snmp_interface_index": eq.snmp_interface_index,
                        "equipment_type": eq.equipment_type
                    })
            
            if not equipments_data:
                await asyncio.sleep(5)
                continue

            # 2. Run Parallel Fetching
            tasks = [fetch_device_data(eq) for eq in equipments_data]
            results = await asyncio.gather(*tasks)
            
            # 3. Batch Update DB
            async with AsyncSessionLocal() as session:
                updates_count = 0
                for res in results:
                    if not res or not res["updates"]: continue
                    
                    # Re-fetch object to attach to this session
                    # Or use update statement. Using get is easier for mix of fields.
                    eq_obj = await session.get(Equipment, res["id"])
                    if not eq_obj: continue
                    
                    # Apply updates
                    for k, v in res["updates"].items():
                        setattr(eq_obj, k, v)
                    
                    # Add Traffic Log
                    if res["log"]:
                        session.add(TrafficLog(
                            equipment_id=res["id"],
                            in_mbps=res["log"][0],
                            out_mbps=res["log"][1]
                        ))
                    
                    session.add(eq_obj)
                    updates_count += 1
                
                if updates_count > 0:
                    await session.commit()
                    # print(f"[SNMP] Updated {updates_count} devices in parallel.")

        except Exception as e:
            print(f"Errors in SNMP loop: {e}")
            
        await asyncio.sleep(SNMP_INTERVAL)

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment
from backend.app.services.snmp import get_snmp_interface_traffic

# Config
SNMP_INTERVAL = 60 # Check SNMP every 60s (Traffic usually doesn't update instantly)

async def snmp_monitor_job():
    """
    Dedicated job for SNMP polling.
    Calculates traffic based on Octet difference.
    """
    import time
    print("🚦 SNMP Monitor started (Interval: 60s)...")
    
    # Cache for bandwidth calculation: eq_id -> (timestamp, in_bytes, out_bytes)
    previous_counters = {} 
    
    while True:
        try:
            current_time = time.time()
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(Equipment))
                equipments = res.scalars().all()
                
                updates = 0
                for eq in equipments:
                    if not eq.ip or not eq.is_online: 
                        continue
                        
                    # Future: Allow selecting interface index properly
                    interface_idx = 1 
                    
                    traffic = await get_snmp_interface_traffic(
                        eq.ip, 
                        community=eq.snmp_community, 
                        port=eq.snmp_port,
                        interface_index=interface_idx
                    )
                    
                    if traffic:
                        in_bytes, out_bytes = traffic
                        
                        # Calculate Speed if we have previous data
                        if eq.id in previous_counters:
                            last_time, last_in, last_out = previous_counters[eq.id]
                            dt = current_time - last_time
                            
                            if dt > 0:
                                delta_in = in_bytes - last_in
                                delta_out = out_bytes - last_out
                                
                                # Handle Counter Wrap-around (simple)
                                if delta_in < 0: delta_in = 0 
                                if delta_out < 0: delta_out = 0
                                
                                # Calculate Mbps
                                mbps_in = (delta_in * 8) / (dt * 1_000_000)
                                mbps_out = (delta_out * 8) / (dt * 1_000_000)
                                
                                eq.last_traffic_in = round(mbps_in, 2)
                                eq.last_traffic_out = round(mbps_out, 2)
                                
                                session.add(eq)
                                updates += 1
                        
                        # Update Cache
                        previous_counters[eq.id] = (current_time, in_bytes, out_bytes)
                
                if updates > 0:
                    await session.commit()
                    # print(f"🚦 SNMP updated traffic for {updates} devices")
                
        except Exception as e:
            print(f"Errors in SNMP loop: {e}")
            
        await asyncio.sleep(SNMP_INTERVAL)

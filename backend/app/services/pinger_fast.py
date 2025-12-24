"""
Ultra-Fast Pinger for Windows using icmplib (similar to The Dude)
Works on Windows, Linux, and Mac - No fping needed!
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment, Parameters, PingLog, Alert


from backend.app.services.telegram import send_telegram_alert
from backend.app.config import PING_TIMEOUT_SECONDS, PING_CONCURRENT_LIMIT

try:
    from icmplib import async_ping, async_multiping
except ImportError:
    # This should not happen given requirements.txt
    print("CRITICAL: icmplib not found!")
    raise



async def ping_ip_fast(ip: str) -> float | None:
    """
    Fast ICMP ping using icmplib (cross-platform, works on Windows!)
    Similar to how The Dude does it - uses raw ICMP sockets
    """
    if not ip:
        return None
    
    try:
        # icmplib async_ping - VERY fast, works on Windows!
        # Requires admin/root on Windows (like The Dude)
        host = await async_ping(ip, count=1, timeout=PING_TIMEOUT_SECONDS, privileged=True)
        
        if host.is_alive:
            return host.avg_rtt / 1000  # Convert ms to seconds
        return None
    except Exception:
        return None

async def ping_multiple_fast(ips: list[str]) -> dict[str, float | None]:
    """
    Ping multiple IPs simultaneously - ULTRA FAST!
    This is the secret sauce of The Dude's speed
    """
    if not ips:
        return {}
    
    try:
        # icmplib async_multiping - pings ALL IPs at once!
        # This is what makes it so fast (like The Dude)
        hosts = await async_multiping(
            ips,
            count=1,
            timeout=PING_TIMEOUT_SECONDS,
            concurrent_tasks=PING_CONCURRENT_LIMIT,
            privileged=True
        )
        
        results = {}
        for host in hosts:
            if host.is_alive:
                results[host.address] = host.avg_rtt / 1000  # ms to seconds
            else:
                results[host.address] = None
        
        return results
    except Exception as e:
        print(f"Multiping error: {e}")
        return {}

async def scan_range_generator(ip_range: list[str]):
    """
    Fast range scanner using multiping
    """
    total = len(ip_range)
    
    # Ping all IPs at once!
    results = await ping_multiple_fast(ip_range)
    
    completed = 0
    for ip, latency in results.items():
        completed += 1
        yield {
            "ip": ip,
            "is_online": latency is not None,
            "progress": int((completed / total) * 100),
            "total": total,
            "completed": completed
        }



async def monitor_job_fast():
    """
    Ultra-fast monitoring loop using batch pinging
    Pings ALL devices at once.
    Optimized: Caches config & Reduces DB writes (Smart Logging).
    """
    from backend.app.config import PING_INTERVAL_SECONDS
    import time
    
    # In-Memory Cache
    config_cache = {
        "last_update": 0,
        "token": "",
        "chat_id": "",
        "tmpl_down": "",
        "tmpl_up": ""
    }
    
    # State tracking for Smart Logging
    # (type, id) -> { 'last_log_time': timestamp, 'last_status': bool, 'last_latency': float }
    device_states = {}

    print("[INFO] Starting High-Performance Pinger Service...")

    while True:
        cycle_start = time.time()
        try:
            async with AsyncSessionLocal() as session:
                # 1. Refresh Config Cache (Every 60s)
                if time.time() - config_cache["last_update"] > 60:
                    try:
                        # Batch Fetch Config (1 Query instead of 4)
                        keys = ["telegram_token", "telegram_chat_id", "telegram_template_down", "telegram_template_up"]
                        res = await session.execute(select(Parameters).where(Parameters.key.in_(keys)))
                        params = {p.key: p.value for p in res.scalars().all()}

                        config_cache["token"] = params.get("telegram_token", "")
                        config_cache["chat_id"] = params.get("telegram_chat_id", "")
                        config_cache["tmpl_down"] = params.get("telegram_template_down", "🔴 [Device.Name] caiu! IP=[Device.IP]")
                        config_cache["tmpl_up"] = params.get("telegram_template_up", "🟢 [Device.Name] voltou! IP=[Device.IP]")
                        config_cache["last_update"] = time.time()
                    except Exception as e:
                        print(f"[WARN] Config refresh failed: {e}")

                # 2. Get All Devices (Optimized SQL Filter)
                # Filter NULL/Empty IPs directly in Database
                towers_res = await session.execute(
                    select(Tower).where(Tower.ip.isnot(None), Tower.ip != "")
                )
                equips_res = await session.execute(
                    select(Equipment).where(Equipment.ip.isnot(None), Equipment.ip != "")
                )
                
                towers = towers_res.scalars().all()
                equipments = equips_res.scalars().all()
                
                all_devices = []
                for t in towers: 
                    all_devices.append(("tower", t))
                for e in equipments: 
                    all_devices.append(("equipment", e))
                
                if not all_devices:
                    await asyncio.sleep(5)
                    continue

                # 3. Ping Batch
                ips = [d[1].ip for d in all_devices]
                ping_results = await ping_multiple_fast(ips)
                
                # 4. Process Results & Smart Log
                current_time = datetime.now(timezone.utc)
                current_ts = current_time.timestamp()
                
                # Map for dependency check
                current_status_map = {} 

                for device_type, device in all_devices:
                    # Parse Result
                    latency_sec = ping_results.get(device.ip)
                    is_online = latency_sec is not None
                    latency_ms = int(latency_sec * 1000) if latency_sec else None
                    
                    # Previous State
                    was_online = device.is_online
                    key = (device_type, device.id)
                    
                    prev_state = device_states.get(key, {
                        'last_log_time': 0, 'last_status': None, 'last_latency': None
                    })

                    # Update DB Object (Always update Real-time View)
                    device.is_online = is_online
                    device.last_checked = current_time
                    if latency_ms is not None:
                        device.last_latency = latency_ms

                    current_status_map[key] = is_online

                    # --- LOGGING DECISION ---
                    # Always log to ensure continuous graphs for Live Monitor
                    should_log = True
                    
                    # Old Smart Logging (Disabled for Live Monitor fidelity)
                    # Rule 1: Status Changed
                    # if is_online != was_online:
                    #    should_log = True
                    # Rule 2: Keepalive (Every 10 minutes)
                    # elif (current_ts - prev_state['last_log_time']) > 600:
                    #    should_log = True
                    # Rule 3: Significant Latency Change
                    # elif is_online and prev_state['last_latency'] is not None:
                    #    if abs(latency_ms - prev_state['last_latency']) > 10:
                    #        should_log = True
                            
                    if should_log:
                        log_entry = PingLog(
                            device_type=device_type,
                            device_id=device.id,
                            status=is_online,
                            latency_ms=latency_ms,
                            timestamp=current_time
                        )
                        session.add(log_entry)
                        
                        # Update State cache
                        device_states[key] = {
                            'last_log_time': current_ts,
                            'last_status': is_online,
                            'last_latency': latency_ms if latency_ms else prev_state['last_latency']
                        }

                    # --- ALERTS ---
                    if is_online != was_online:
                        # Dependency Check
                        suppress = False
                        if not is_online: # Down 
                            if device.parent_id and ('equipment', device.parent_id) in current_status_map:
                                if not current_status_map[('equipment', device.parent_id)]:
                                    # Parent is DOWN, suppress child alert
                                    suppress = True 
                        
                        if not suppress:
                            tmpl = config_cache["tmpl_down"] if not is_online else config_cache["tmpl_up"]
                            msg = tmpl.replace("[Device.Name]", device.name)\
                                      .replace("[Device.IP]", device.ip)\
                                      .replace("[Service.Name]", "Ping")\
                                      .replace("[Device.FirstAddress]", device.ip)
                            
                            await send_telegram_alert(config_cache["token"], config_cache["chat_id"], msg)
                            
                            session.add(Alert(
                                device_type=device_type,
                                device_name=device.name,
                                device_ip=device.ip,
                                message=msg,
                                timestamp=current_time
                            ))

                await session.commit()
                
        except Exception as e:
            print(f"[ERROR] Monitor Loop: {e}")
        
        # Consistent Interval
        elapsed = time.time() - cycle_start
        wait_time = max(0.5, PING_INTERVAL_SECONDS - elapsed)
        await asyncio.sleep(wait_time)

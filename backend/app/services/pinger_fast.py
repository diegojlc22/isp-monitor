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

from backend.app.config import PING_TIMEOUT_SECONDS, PING_CONCURRENT_LIMIT

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
    Pings ALL devices at once (like The Dude)
    """
    from backend.app.config import PING_INTERVAL_SECONDS
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Get Telegram config
                token_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_token"))
                chat_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))
                down_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_template_down"))
                up_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_template_up"))
                
                token = token_res.scalar_one_or_none()
                chat_id = chat_res.scalar_one_or_none()
                down_tmpl = down_res.scalar_one_or_none()
                up_tmpl = up_res.scalar_one_or_none()
                
                token_val = token.value if token else ""
                chat_val = chat_id.value if chat_id else ""
                template_down = down_tmpl.value if down_tmpl else "🔴 O servico Ping no dispositivo [Device.Name] passou para o status down - IP=[Device.IP]"
                template_up = up_tmpl.value if up_tmpl else "🟢 O servico Ping no dispositivo [Device.Name] passou para o status up - IP=[Device.IP]"
                
                # Get all devices
                towers_res = await session.execute(select(Tower))
                towers = towers_res.scalars().all()
                
                equip_res = await session.execute(select(Equipment))
                equipments = equip_res.scalars().all()
                
                # Collect all IPs
                all_devices = []
                for tower in towers:
                    if tower.ip:
                        all_devices.append(("tower", tower))
                
                for eq in equipments:
                    if eq.ip:
                        all_devices.append(("equipment", eq))
                
                # Ping ALL devices at once! (The Dude's secret)
                if all_devices:
                    ips = [device[1].ip for device in all_devices]
                    ping_results = await ping_multiple_fast(ips)
                    
                    # Pass 1: Update statuses & Build Map
                    # Precisamos saber o status ATUAL de todos antes de gerar alertas (para dependencias)
                    current_status_map = {} # (type, id) -> bool
                    
                    # Store previous statuses to check for changes
                    changes = [] 
                    
                    for device_type, device in all_devices:
                        latency_sec = ping_results.get(device.ip)
                        is_online = latency_sec is not None
                        latency_ms = int(latency_sec * 1000) if latency_sec else None
                        
                        was_online = device.is_online
                        
                        # Update DB object
                        device.is_online = is_online
                        device.last_checked = datetime.now(timezone.utc)
                        if latency_ms is not None:
                            device.last_latency = latency_ms
                            
                        # Update Map
                        current_status_map[(device_type, device.id)] = is_online
                        
                        # Record change for Pass 2 if state changed
                        if is_online != was_online:
                            changes.append((device_type, device, is_online, was_online))

                        # Always Log (or maybe only on change? No, keep history)
                        # But logging 50 devices every 5s fills DB fast.
                        # Ideally log ping only if requested or periodically.
                        # For now, keep as is (user requested logs).
                        log_entry = PingLog(
                            device_type=device_type,
                            device_id=device.id,
                            status=is_online,
                            latency_ms=latency_ms,
                            timestamp=datetime.now(timezone.utc)
                        )
                        session.add(log_entry)

                    # Pass 2: Generate Smart Alerts
                    for device_type, device, is_online, was_online in changes:
                        # Check Dependency (Suppress if Parent is DOWN)
                        suppress_alert = False
                        
                        if not is_online: # Only needed for DOWN alerts
                            parent_id = device.parent_id
                            if parent_id:
                                # Assume parent is ALWAYS an Equipment (Router/Switch)
                                # Check parent's status in the current map
                                parent_status = current_status_map.get(('equipment', parent_id))
                                
                                # If parent status is known AND is False (Offline) -> Suppress
                                if parent_status is False:
                                    print(f"🔕 Alert suppressed for {device.name} (Parent {parent_id} is down)")
                                    suppress_alert = True

                        if suppress_alert:
                            continue

                        # Generate Alert
                        if not is_online and was_online:
                            # DOWN
                            msg = template_down.replace("[Device.Name]", device.name)\
                                               .replace("[Device.IP]", device.ip)\
                                               .replace("[Service.Name]", "Ping")\
                                               .replace("[Device.FirstAddress]", device.ip)
                            await send_telegram_alert(token_val, chat_val, msg)
                            
                            alert = Alert(
                                device_type=device_type,
                                device_name=device.name,
                                device_ip=device.ip,
                                message=msg,
                                timestamp=datetime.now(timezone.utc)
                            )
                            session.add(alert)
                            
                        elif is_online and not was_online:
                            # UP
                            msg = template_up.replace("[Device.Name]", device.name)\
                                             .replace("[Device.IP]", device.ip)\
                                             .replace("[Service.Name]", "Ping")\
                                             .replace("[Device.FirstAddress]", device.ip)
                            await send_telegram_alert(token_val, chat_val, msg)
                            
                            alert = Alert(
                                device_type=device_type,
                                device_name=device.name,
                                device_ip=device.ip,
                                message=msg,
                                timestamp=datetime.now(timezone.utc)
                            )
                            session.add(alert)
                
                await session.commit()
                # print(f"✅ Pinged {len(all_devices)} devices in batch mode")
        except Exception as e:
            print(f"Monitor job error: {e}")
        
        await asyncio.sleep(PING_INTERVAL_SECONDS)

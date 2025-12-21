"""
Ultra-Fast Pinger for Windows using icmplib (similar to The Dude)
Works on Windows, Linux, and Mac - No fping needed!
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment, Parameters, PingLog
from backend.app.services.telegram import send_telegram_alert
from backend.app.config import PING_TIMEOUT_SECONDS, PING_CONCURRENT_LIMIT

try:
    from icmplib import async_ping, async_multiping
    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False
    # Fallback to ping3
    from ping3 import ping

async def ping_ip_fast(ip: str) -> float | None:
    """
    Fast ICMP ping using icmplib (cross-platform, works on Windows!)
    Similar to how The Dude does it - uses raw ICMP sockets
    """
    if not ip:
        return None
    
    if not ICMPLIB_AVAILABLE:
        # Fallback to ping3
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: ping(ip, timeout=PING_TIMEOUT_SECONDS))
            if response is False or response is None:
                return None
            return response
        except Exception:
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
    
    if not ICMPLIB_AVAILABLE:
        # Fallback to sequential pings
        results = {}
        for ip in ips:
            results[ip] = await ping_ip_fast(ip)
        return results
    
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
        # Fallback to sequential
        results = {}
        for ip in ips:
            results[ip] = await ping_ip_fast(ip)
        return results

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

async def check_and_alert(session, device, device_type: str, token: str, chat_id: str):
    latency_sec = await ping_ip_fast(device.ip)
    is_online = latency_sec is not None
    latency_ms = int(latency_sec * 1000) if latency_sec else None
    
    # Get latency thresholds
    good_res = await session.execute(select(Parameters).where(Parameters.key == "latency_good"))
    crit_res = await session.execute(select(Parameters).where(Parameters.key == "latency_critical"))
    good_threshold = int(good_res.scalar_one_or_none().value) if good_res.scalar_one_or_none() else 50
    crit_threshold = int(crit_res.scalar_one_or_none().value) if crit_res.scalar_one_or_none() else 200
    
    # Update device status
    was_online = device.is_online
    device.is_online = is_online
    device.last_checked = datetime.now(timezone.utc)
    if latency_ms is not None:
        device.last_latency = latency_ms
    
    # Log ping result
    log_entry = PingLog(
        device_type=device_type,
        device_id=device.id,
        status=is_online,
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(log_entry)
    
    # Alert logic (only on status change)
    if device_type == "tower":
        if not is_online and was_online:
            await send_telegram_alert(token, chat_id, f"🔴 Torre OFFLINE: {device.name} ({device.ip})")
        elif is_online and not was_online:
            await send_telegram_alert(token, chat_id, f"🟢 Torre ONLINE: {device.name} ({device.ip})")
    else:  # equipment
        if not is_online and was_online:
            await send_telegram_alert(token, chat_id, f"🔴 Equipamento OFFLINE: {device.name} ({device.ip})")
        elif is_online and not was_online:
            await send_telegram_alert(token, chat_id, f"🟢 Equipamento ONLINE: {device.name} ({device.ip})")

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
                token = token_res.scalar_one_or_none()
                chat_id = chat_res.scalar_one_or_none()
                token_val = token.value if token else ""
                chat_val = chat_id.value if chat_id else ""
                
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
                if all_devices and ICMPLIB_AVAILABLE:
                    ips = [device[1].ip for device in all_devices]
                    ping_results = await ping_multiple_fast(ips)
                    
                    # Process results
                    for device_type, device in all_devices:
                        latency_sec = ping_results.get(device.ip)
                        is_online = latency_sec is not None
                        latency_ms = int(latency_sec * 1000) if latency_sec else None
                        
                        was_online = device.is_online
                        device.is_online = is_online
                        device.last_checked = datetime.now(timezone.utc)
                        if latency_ms is not None:
                            device.last_latency = latency_ms
                        
                        # Log
                        log_entry = PingLog(
                            device_type=device_type,
                            device_id=device.id,
                            status=is_online,
                            latency_ms=latency_ms,
                            timestamp=datetime.now(timezone.utc)
                        )
                        session.add(log_entry)
                        
                        # Alert on status change
                        if not is_online and was_online:
                            name = "Torre" if device_type == "tower" else "Equipamento"
                            await send_telegram_alert(token_val, chat_val, f"🔴 {name} OFFLINE: {device.name} ({device.ip})")
                        elif is_online and not was_online:
                            name = "Torre" if device_type == "tower" else "Equipamento"
                            await send_telegram_alert(token_val, chat_val, f"🟢 {name} ONLINE: {device.name} ({device.ip})")
                else:
                    # Fallback to sequential (if icmplib not available)
                    for device_type, device in all_devices:
                        await check_and_alert(session, device, device_type, token_val, chat_val)
                
                await session.commit()
                print(f"✅ Pinged {len(all_devices)} devices in batch mode")
        except Exception as e:
            print(f"Monitor job error: {e}")
        
        await asyncio.sleep(PING_INTERVAL_SECONDS)

"""
Optimized Pinger with fping support for production (800+ devices)
"""
import asyncio
import subprocess
import re
from datetime import datetime, timezone
from ping3 import ping
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment, Parameters, PingLog
from backend.app.services.telegram import send_telegram_alert
from backend.app.config import USE_FPING, PING_TIMEOUT_SECONDS, PING_CONCURRENT_LIMIT

async def ping_ip_fping(ip: str) -> float | None:
    """
    Ultra-fast ping using fping (Linux/Unix only)
    Falls back to ping3 if fping not available
    """
    if not ip:
        return None
    
    try:
        loop = asyncio.get_running_loop()
        
        # Try fping first (much faster for multiple IPs)
        def run_fping():
            try:
                # fping -c 1 -t 1000 IP (1 ping, 1000ms timeout)
                result = subprocess.run(
                    ['fping', '-c', '1', '-t', str(PING_TIMEOUT_SECONDS * 1000), ip],
                    capture_output=True,
                    text=True,
                    timeout=PING_TIMEOUT_SECONDS + 1
                )
                # Parse fping output: "IP : xmt/rcv/%loss = 1/1/0%, min/avg/max = 12.3/12.3/12.3"
                if result.returncode == 0:
                    match = re.search(r'min/avg/max = ([\d.]+)/([\d.]+)/([\d.]+)', result.stderr)
                    if match:
                        return float(match.group(2)) / 1000  # Convert ms to seconds
                return None
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                # Fallback to ping3
                return ping(ip, timeout=PING_TIMEOUT_SECONDS)
        
        response = await loop.run_in_executor(None, run_fping)
        
        if response is False or response is None:
            return None
        return response  # seconds
    except Exception:
        return None

async def ping_ip(ip: str) -> float | None:
    """
    Standard ping using ping3 (cross-platform)
    """
    if not ip:
        return None
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: ping(ip, timeout=PING_TIMEOUT_SECONDS))
        
        if response is False or response is None:
            return None
        return response  # seconds
    except Exception:
        return None

# Choose ping method based on config
ping_method = ping_ip_fping if USE_FPING else ping_ip

async def scan_range_generator(ip_range: list[str]):
    sem = asyncio.Semaphore(PING_CONCURRENT_LIMIT)
    total = len(ip_range)
    completed = 0
    
    async def safe_ping(ip):
        async with sem:
            resp = await ping_method(ip)
            return ip, (resp is not None)

    # Create tasks
    tasks = [asyncio.create_task(safe_ping(ip)) for ip in ip_range]
    
    # Process as they complete
    for future in asyncio.as_completed(tasks):
        ip, is_online = await future
        completed += 1
        yield {
            "ip": ip,
            "is_online": is_online,
            "progress": int((completed / total) * 100),
            "total": total,
            "completed": completed
        }

async def check_and_alert(session, device, device_type: str, token: str, chat_id: str):
    latency_sec = await ping_method(device.ip)
    is_online = latency_sec is not None
    latency_ms = int(latency_sec * 1000) if latency_sec else None
    
    # Get latency thresholds
    good_res = await session.execute(select(Parameters).where(Parameters.key == "latency_good"))
    crit_res = await session.execute(select(Parameters).where(Parameters.key == "latency_critical"))
    good_threshold = int(good_res.scalar_one_or_none().value) if good_res.scalar_one_or_none() else 50
    crit_threshold = int(crit_res.scalar_one_or_none().value) if crit_res.scalar_one_or_none() else 200
    
    # Update device status
    device.is_online = is_online
    device.last_checked = datetime.now(timezone.utc)
    if latency_ms is not None:
        device.last_latency = latency_ms
    
    # Log ping result
    log_entry = PingLog(
        device_type=device_type,
        device_id=device.id,
        status="online" if is_online else "offline",
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(log_entry)
    
    # Alert logic (only on status change)
    if device_type == "tower":
        if not is_online and device.is_online:
            await send_telegram_alert(token, chat_id, f"🔴 Torre OFFLINE: {device.name} ({device.ip})")
        elif is_online and not device.is_online:
            await send_telegram_alert(token, chat_id, f"🟢 Torre ONLINE: {device.name} ({device.ip})")
    else:  # equipment
        if not is_online and device.is_online:
            await send_telegram_alert(token, chat_id, f"🔴 Equipamento OFFLINE: {device.name} ({device.ip})")
        elif is_online and not device.is_online:
            await send_telegram_alert(token, chat_id, f"🟢 Equipamento ONLINE: {device.name} ({device.ip})")

async def monitor_job():
    """
    Main monitoring loop - runs continuously
    Uses configurable interval from config.py
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
                
                # Check towers
                towers_res = await session.execute(select(Tower))
                towers = towers_res.scalars().all()
                for tower in towers:
                    if tower.ip:
                        await check_and_alert(session, tower, "tower", token_val, chat_val)
                
                # Check equipments
                equip_res = await session.execute(select(Equipment))
                equipments = equip_res.scalars().all()
                for eq in equipments:
                    if eq.ip:
                        await check_and_alert(session, eq, "equipment", token_val, chat_val)
                
                await session.commit()
        except Exception as e:
            print(f"Monitor job error: {e}")
        
        await asyncio.sleep(PING_INTERVAL_SECONDS)

import asyncio
from datetime import datetime, timezone
from ping3 import ping
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment, Parameters, PingLog
from backend.app.services.telegram import send_telegram_alert

async def ping_ip(ip: str) -> float | None:
    if not ip:
        return None
    try:
        loop = asyncio.get_running_loop()
        # Run synchronous ping in thread pool
        # ping3.ping returns seconds (float) or None/False
        response = await loop.run_in_executor(None, lambda: ping(ip, timeout=1))
        
        if response is False or response is None:
            return None
        return response # seconds
    except Exception:
        return None

async def scan_range_generator(ip_range: list[str]):
    sem = asyncio.Semaphore(50)
    total = len(ip_range)
    completed = 0
    
    async def safe_ping(ip):
        async with sem:
            resp = await ping_ip(ip)
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
    latency_sec = await ping_ip(device.ip)
    is_online = latency_sec is not None
    latency_ms = int(latency_sec * 1000) if is_online else None
    
    # Status Change Logic
    status_changed = device.is_online != is_online
    
    # Update Device State
    device.is_online = is_online
    device.last_checked = datetime.now(timezone.utc)
    device.last_latency = latency_ms
    session.add(device)
    
    # Always Log for Latency History (or at least if online)
    # To support the graph, we need continuous data points.
    log = PingLog(
        device_type=device_type,
        device_id=device.id,
        status=is_online,
        latency_ms=latency_ms,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(log) # We add every check to build history

    if status_changed:
        status_str = "ONLINE" if is_online else "OFFLINE"
        emoji = "🟢" if is_online else "🔴"
        
        # Send Alert
        if token and chat_id:
            msg = (
                f"{emoji} *Alerta de Monitoramento*\n\n"
                f"*Dispositivo:* {device.name}\n"
                f"*Tipo:* {device_type}\n"
                f"*IP:* {device.ip}\n"
                f"*Status:* *{status_str}*"
            )
            await send_telegram_alert(token, chat_id, msg)

async def monitor_job():
    async with AsyncSessionLocal() as session:
        # Get Config
        token_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_token"))
        chat_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))
        
        token_obj = token_res.scalar_one_or_none()
        chat_obj = chat_res.scalar_one_or_none()
        
        token = token_obj.value if token_obj else None
        chat_id = chat_obj.value if chat_obj else None

        # Check Towers
        towers_res = await session.execute(select(Tower))
        towers = towers_res.scalars().all()
        for tower in towers:
            # Skip towers without IP
            if tower.ip:
                await check_and_alert(session, tower, "Torre", token, chat_id)

        # Check Equipment
        equips_res = await session.execute(select(Equipment))
        equipments = equips_res.scalars().all()
        for eq in equipments:
            await check_and_alert(session, eq, "Equipamento", token, chat_id)
            
        await session.commit()

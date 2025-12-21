import asyncio
from datetime import datetime, timezone
from ping3 import ping
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Tower, Equipment, Parameters, PingLog
from backend.app.services.telegram import send_telegram_alert

async def ping_ip(ip: str) -> bool:
    if not ip:
        return False
    try:
        loop = asyncio.get_running_loop()
        # Run synchronous ping in thread pool
        response = await loop.run_in_executor(None, lambda: ping(ip, timeout=1))
        return response is not None and response is not False
    except Exception:
        return False

async def scan_range_generator(ip_range: list[str]):
    sem = asyncio.Semaphore(50)
    total = len(ip_range)
    completed = 0
    
    async def safe_ping(ip):
        async with sem:
            is_online = await ping_ip(ip)
            return ip, is_online

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
    current_status = await ping_ip(device.ip)
    
    # If status changed (or first run check if None, but defaults to False)
    # Actually DB default is False. If it was really online but we think it is offline, we send alert "Online".
    # That's acceptable for first run (system coming up).
    
    if device.is_online != current_status:
        # Status changed
        device.is_online = current_status
        device.last_checked = datetime.now(timezone.utc)
        
        status_str = "ONLINE" if current_status else "OFFLINE"
        emoji = "🟢" if current_status else "🔴"
        
        # Create Log
        log = PingLog(
            device_type=device_type,
            device_id=device.id,
            status=current_status,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(log)
        session.add(device)
        
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
    else:
        # Just update last checked
        device.last_checked = datetime.now(timezone.utc)
        session.add(device)

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
            await check_and_alert(session, tower, "Torre", token, chat_id)

        # Check Equipment
        equips_res = await session.execute(select(Equipment))
        equipments = equips_res.scalars().all()
        for eq in equipments:
            await check_and_alert(session, eq, "Equipamento", token, chat_id)
            
        await session.commit()

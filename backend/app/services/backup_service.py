
import os
import asyncio
import subprocess
from datetime import datetime
from backend.app.database import AsyncSessionLocal
from backend.app.services.notifier import send_notification
from loguru import logger
from sqlalchemy import select
from backend.app.models import Parameters

# Configs
DB_NAME = "isp_monitor"
DB_USER = "postgres"
DB_PASS = "110812" # TODO: Load from env
BACKUP_DIR = "backups"
BACKUP_RETENTION_DAYS = 7

async def run_backup_job():
    """Backup routine to be called by scheduler"""
    logger.info("[BACKUP] Starting automated backup job...")
    
    # 1. Ensure backup dir exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # 2. Generate Filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_auto_{timestamp}.sql")
    
    # 3. Define Command
    # Use PGPASSWORD env var to avoid password prompt
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    
    cmd = f'pg_dump -U {DB_USER} -h localhost -F c -b -v -f "{backup_file}" {DB_NAME}'
    
    # Try to find pg_dump absolute path on Windows
    pg_dump_path = "pg_dump"
    possible_paths = [
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pg_dump_path = f'"{path}"'
            break
            
    cmd = f'{pg_dump_path} -U {DB_USER} -h localhost -F c -b -v -f "{backup_file}" {DB_NAME}'
    
    try:
        # Run pg_dump
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            msg = f"✅ *[BACKUP]* Backup Automático Realizado!\n📁 Arquivo: {os.path.basename(backup_file)}\n💾 Tamanho: {size_mb:.2f} MB"
            logger.info(f"[BACKUP] Success: {backup_file} ({size_mb:.2f} MB)")
            
            # --- SEND NOTIFICATION ---
            async with AsyncSessionLocal() as session:
                # Load configuration
                config_keys = [
                    "notify_backups", "telegram_backup_chat_id", "telegram_token", 
                    "telegram_chat_id", "telegram_enabled", 
                    "whatsapp_target_number", "whatsapp_enabled", 
                    "whatsapp_group_id", "whatsapp_target_group"
                ]
                
                res = await session.execute(select(Parameters).where(Parameters.key.in_(config_keys)))
                params = {p.key: p.value for p in res.scalars().all()}
                
                # Check if notifications are enabled
                if params.get("notify_backups", "true") != "false":
                    tg_token = params.get("telegram_token")
                    tg_chat = params.get("telegram_backup_chat_id") or params.get("telegram_chat_id")
                    tg_enabled = params.get("telegram_enabled") == "true"
                    
                    wa_target = params.get("whatsapp_target_number")
                    wa_group = params.get("whatsapp_target_group") or params.get("whatsapp_group_id")
                    wa_enabled = params.get("whatsapp_enabled") == "true"
                    
                    await send_notification(
                        msg,
                        telegram_token=tg_token,
                        telegram_chat_id=tg_chat,
                        telegram_enabled=tg_enabled,
                        whatsapp_enabled=wa_enabled,
                        whatsapp_target=wa_target,
                        whatsapp_target_group=wa_group
                    )
            # --- UPDATE LAST BACKUP PARAMETER ---
            async with AsyncSessionLocal() as session:
                param = await session.get(Parameters, "last_backup_run")
                if not param:
                    session.add(Parameters(key="last_backup_run", value=datetime.now().isoformat()))
                else:
                    param.value = datetime.now().isoformat()
                await session.commit()
                logger.info("[BACKUP] Updated 'last_backup_run' param in DB.")

            # Cleanup old backups
            cleanup_old_backups()
            
        else:
            try:
                err_msg = stderr.decode('utf-8')
            except UnicodeDecodeError:
                err_msg = stderr.decode('cp1252', errors='replace')
                
            logger.error(f"[BACKUP] Failed: {err_msg}")
            # Try to send error notification anyway (using defaults/fallback logic if needed or just error log)
            await send_notification(f"❌ *[BACKUP]* Falha ao realizar backup.\nErro: {err_msg[:100]}...")
            
    except Exception as e:
        logger.error(f"[BACKUP] Exception: {e}")
        await send_notification(f"❌ *[BACKUP]* Erro crítico no processo de backup: {str(e)}")

def cleanup_old_backups():
    """Remove backups older than retention period"""
    try:
        now = datetime.now().timestamp()
        retention_sec = BACKUP_RETENTION_DAYS * 86400
        
        for f in os.listdir(BACKUP_DIR):
            f_path = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(f_path) and f.startswith("backup_auto_"):
                if os.stat(f_path).st_mtime < (now - retention_sec):
                    os.remove(f_path)
                    logger.info(f"[BACKUP] Removed old backup: {f}")
    except Exception as e:
        logger.warning(f"[BACKUP] Error collecting garbage: {e}")

async def backup_scheduler_loop():
    """
    Robust scheduler for daily backups.
    Checks if a backup was already performed today.
    """
    logger.info("[BACKUP] Scheduler started (Daily at 03:00 AM).")
    
    last_backup_date = None
    
    while True:
        try:
            now = datetime.now()
            current_date = now.date()
            
            # Target window: 03:00 AM - 04:00 AM
            if now.hour == 3 and last_backup_date != current_date:
                logger.info(f"[BACKUP] Window matched (Hour: {now.hour}), triggering daily backup...")
                await run_backup_job()
                last_backup_date = current_date # Mark as done for today
                
            # Internal check every 5 minutes is enough and more efficient
            await asyncio.sleep(300) 
            
        except Exception as e:
            logger.error(f"[BACKUP] Scheduler error: {e}")
            await asyncio.sleep(60)

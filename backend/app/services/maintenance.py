import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from backend.app.database import AsyncSessionLocal
from backend.app.models import PingLog, Alert

async def cleanup_job():
    """
    Periodic job to clean up old logs and alerts.
    Keeps database size manageable.
    """
    DAYS_TO_KEEP = 30
    
    print("[INFO] Iniciando limpeza de logs antigos...")
    try:
        async with AsyncSessionLocal() as session:
            # Calculate updated cutoff date
            cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_KEEP)
            
            # Delete old PingLogs
            # Note: SQLAlchemy delete statement
            stmt = delete(PingLog).where(PingLog.timestamp < cutoff)
            result = await session.execute(stmt)
            deleted_rows = result.rowcount
            
            # Delete old Alerts (Optional, maybe keep them longer?)
            # Let's keep alerts for 60 days
            cutoff_alerts = datetime.now(timezone.utc) - timedelta(days=60)
            stmt_alerts = delete(Alert).where(Alert.timestamp < cutoff_alerts)
            result_alerts = await session.execute(stmt_alerts)
            deleted_alerts = result_alerts.rowcount
            
            await session.commit()
            
            if deleted_rows > 0:
                print(f"[OK] Limpeza: {deleted_rows} logs de ping antigos removidos.")
            if deleted_alerts > 0:
                print(f"[OK] Limpeza: {deleted_alerts} alertas antigos removidos.")
                
    except Exception as e:
        print(f"[ERROR] Erro na limpeza de logs: {e}")

async def backup_database_job():
    """
    Creates a ZIP backup of monitor.db and sends it to Telegram.
    Runs daily.
    """
    import zipfile
    import os
    from backend.app.models import Parameters
    from backend.app.services.telegram import send_telegram_document
    
    DB_FILENAME = "monitor.db"
    
    if not os.path.exists(DB_FILENAME):
        print("[WARN] Backup skipped: monitor.db not found.")
        return

    print("[INFO] Starting daily database backup...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    zip_filename = f"backup_monitor_{timestamp}.zip"
    
    try:
        # 1. Create ZIP
        # Using ZIP_DEFLATED for compression
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_FILENAME, arcname=DB_FILENAME)
        
        print(f"[OK] Database compressed: {zip_filename}")
        
        # 2. Upload to Telegram
        async with AsyncSessionLocal() as session:
            token_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_token"))
            chat_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))
            backup_res = await session.execute(select(Parameters).where(Parameters.key == "telegram_backup_chat_id"))
            
            token = token_res.scalar_one_or_none()
            chat_id = chat_res.scalar_one_or_none()
            backup_chat = backup_res.scalar_one_or_none()
            
            # Determine Target Chat (Prefer Backup Chat, fallback to Main)
            target_chat_id = None
            if backup_chat and backup_chat.value:
                target_chat_id = backup_chat.value
            elif chat_id and chat_id.value:
                target_chat_id = chat_id.value
            
            if token and token.value and target_chat_id:
                caption = f"Backup ISP Monitor - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                await send_telegram_document(token.value, target_chat_id, zip_filename, caption)
            else:
                print("[WARN] Backup not sent: Telegram not configured (Token/Chat missing).")

    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
    finally:
        # 3. Cleanup (Delete zip)
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            # print("Deleted temp backup file.")

if __name__ == "__main__":
    # Test execution
    asyncio.run(cleanup_job())
    # asyncio.run(backup_database_job())

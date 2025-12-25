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

async def rollup_hourly_stats_job():
    """
    Aggregates raw PingLogs into PingStatsHourly.
    Reduces 60*60=3600 rows per device/hour to just 1 row.
    Ideally runs shortly after the hour changes.
    """
    from sqlalchemy import func
    from backend.app.models import PingStatsHourly

    print("[INFO] Starting Hourly Stats Rollup...")
    
    try:
        async with AsyncSessionLocal() as session:
            # 1. Determine last rolled up hour
            # For simplicity, we can look at the latest entry in PingStatsHourly
            # Or just re-calculate the last 2 hours to be safe.
            
            # Let's process the PREVIOUS hour (e.g., if now is 14:10, process 13:00-13:59)
            now = datetime.now(timezone.utc)
            start_of_current_hour = now.replace(minute=0, second=0, microsecond=0)
            target_hour = start_of_current_hour - timedelta(hours=1)
            end_target_hour = start_of_current_hour
            
            # Check if we already have stats for this hour (avoid duplicates)
            # This check is basic, in production might need a "LastProcessed" pointer table.
            # But for now, we can just delete and re-insert (safe idempotency)
            stmt_del = delete(PingStatsHourly).where(PingStatsHourly.timestamp == target_hour)
            await session.execute(stmt_del)
            
            # 2. Aggregation Query
            # SELECT device_type, device_id, AVG(latency), ... FROM ping_logs
            # WHERE timestamp >= target_hour AND timestamp < end_target_hour
            # GROUP BY device_type, device_id
            
            stmt = select(
                PingLog.device_type,
                PingLog.device_id,
                func.avg(PingLog.latency_ms).label('avg_latency'),
                func.count().label('total_pings'),
                func.sum(PingLog.status).label('successful_pings') # status is boolean (0/1)
            ).where(
                PingLog.timestamp >= target_hour,
                PingLog.timestamp < end_target_hour
            ).group_by(PingLog.device_type, PingLog.device_id)
            
            result = await session.execute(stmt)
            rows = result.all()
            
            rollup_buffer = []
            for row in rows:
                total = row.total_pings
                success = row.successful_pings or 0 # Handle None if no pings
                
                # Calculate metrics
                loss_pct = ((total - success) / total) * 100 if total > 0 else 0
                uptime_pct = (success / total) * 100 if total > 0 else 0
                avg_lat = row.avg_latency or 0
                
                rollup_buffer.append(PingStatsHourly(
                    device_type=row.device_type,
                    device_id=row.device_id,
                    avg_latency_ms=round(avg_lat, 2),
                    pkt_loss_percent=round(loss_pct, 2),
                    availability_percent=round(uptime_pct, 2),
                    timestamp=target_hour
                ))
            
            if rollup_buffer:
                session.add_all(rollup_buffer)
                await session.commit()
                print(f"[OK] Rollup: Created stats for {len(rollup_buffer)} devices for hour {target_hour.isoformat()}")
            else:
                print(f"[INFO] Rollup: No data found for hour {target_hour.isoformat()}")

            # 3. Optional: Prune RAW logs older than 7 days immediately to keep DB tiny
            # (Assuming we trust the aggregated data)
            # prune_cutoff = now - timedelta(days=7)
            # await session.execute(delete(PingLog).where(PingLog.timestamp < prune_cutoff))
            # await session.commit()

    except Exception as e:
        print(f"[ERROR] Rollup failed: {e}")

if __name__ == "__main__":
    # Test execution
    asyncio.run(cleanup_job())
    # asyncio.run(backup_database_job())
    # asyncio.run(rollup_hourly_stats_job()) # Test rollup manually

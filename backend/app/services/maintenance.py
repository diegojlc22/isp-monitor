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
    
    print("🧹 Iniciando limpeza de logs antigos...")
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
                print(f"✅ Limpeza: {deleted_rows} logs de ping antigos removidos.")
            if deleted_alerts > 0:
                print(f"✅ Limpeza: {deleted_alerts} alertas antigos removidos.")
                
    except Exception as e:
        print(f"❌ Erro na limpeza de logs: {e}")

if __name__ == "__main__":
    # Test execution
    asyncio.run(cleanup_job())

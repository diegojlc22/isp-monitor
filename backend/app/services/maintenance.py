import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from backend.app.database import async_session_factory
from backend.app.models import PingLog
from backend.app.config import LOG_RETENTION_DAYS

async def cleanup_logs(retention_days=None):
    """Deletes ping logs older than retention_days."""
    if retention_days is None:
        retention_days = LOG_RETENTION_DAYS
    
    try:
        async with async_session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            stmt = delete(PingLog).where(PingLog.timestamp < cutoff)
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount > 0:
                print(f"Maintenance: Deleted {result.rowcount} old ping logs (retention: {retention_days} days).")
    except Exception as e:
        print(f"Maintenance Error: {e}")



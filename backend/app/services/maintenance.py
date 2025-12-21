import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from backend.app.database import async_session_factory
from backend.app.models import PingLog

async def cleanup_logs(retention_days=7):
    """Deletes ping logs older than retention_days."""
    try:
        async with async_session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            # print(f"Running maintenance: Cleanup logs older than {cutoff}...")
            stmt = delete(PingLog).where(PingLog.timestamp < cutoff)
            result = await db.execute(stmt)
            await db.commit()
            if result.rowcount > 0:
                print(f"Maintenance: Deleted {result.rowcount} old ping logs.")
    except Exception as e:
        print(f"Maintenance Error: {e}")

async def maintenance_loop():
    """Runs maintenance tasks perpetually."""
    while True:
        await cleanup_logs(7) # Keep 7 days of logs
        # Run every 24 hours (86400 seconds)
        # We start with a sleep to avoiding hitting DB immediately on restart if not needed, 
        # but for now let's run immediately then sleep.
        await asyncio.sleep(24 * 60 * 60)

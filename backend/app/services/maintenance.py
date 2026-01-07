import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete, func, Integer
from backend.app.database import AsyncSessionLocal
from backend.app.models import PingLog, Alert, TrafficLog, LatencyHistory
from loguru import logger

async def cleanup_job():
    """
    Periodic job to clean up old logs and alerts.
    Keeps database size manageable.
    """
    DAYS_TO_KEEP = 30
    
    logger.info("[MAINTENANCE] Iniciando limpeza de logs antigos...")
    try:
        async with AsyncSessionLocal() as session:
            # Calculate updated cutoff date
            cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_TO_KEEP)
            
            # Delete old PingLogs
            cutoff_naive = datetime.utcnow() - timedelta(days=DAYS_TO_KEEP)
            
            stmt = delete(PingLog).where(PingLog.timestamp < cutoff_naive)
            result = await session.execute(stmt)
            deleted_rows = result.rowcount
            
            # Delete old Alerts
            cutoff_alerts = datetime.utcnow() - timedelta(days=60)
            stmt_alerts = delete(Alert).where(Alert.timestamp < cutoff_alerts)
            result_alerts = await session.execute(stmt_alerts)
            deleted_alerts = result_alerts.rowcount
            
            await session.commit()
            
            if deleted_rows > 0:
                logger.info(f"[OK] Limpeza: {deleted_rows} logs de ping antigos removidos.")
            
            # Delete old TrafficLogs
            stmt_traffic = delete(TrafficLog).where(TrafficLog.timestamp < cutoff_naive)
            res_traffic = await session.execute(stmt_traffic)
            if res_traffic.rowcount > 0:
                logger.info(f"[OK] Limpeza: {res_traffic.rowcount} logs de tráfego antigos removidos.")

            # Delete old LatencyHistory
            # LatencyHistory stores timestamp as Float (Unix)
            cutoff_unix = cutoff_naive.timestamp()
            stmt_latency = delete(LatencyHistory).where(LatencyHistory.timestamp < cutoff_unix)
            res_latency = await session.execute(stmt_latency)
            if res_latency.rowcount > 0:
                logger.info(f"[OK] Limpeza: {res_latency.rowcount} logs de latência antigos removidos.")

            if deleted_alerts > 0:
                logger.info(f"[OK] Limpeza: {deleted_alerts} alertas antigos removidos.")
                
    except Exception as e:
        logger.error(f"[ERROR] Erro na limpeza de logs: {e}")

async def rollup_hourly_stats_job():
    """
    Aggregates raw PingLogs into PingStatsHourly.
    Processes all hours from last recorded stat until previous hour.
    """
    from backend.app.models import PingStatsHourly

    logger.info("[MAINTENANCE] Starting Hourly Stats Rollup...")
    
    try:
        async with AsyncSessionLocal() as session:
            # 1. Determine last rolled up hour
            res_last = await session.execute(select(func.max(PingStatsHourly.timestamp)))
            last_recorded = res_last.scalar()
            
            now = datetime.now(timezone.utc)
            start_of_current_hour = now.replace(minute=0, second=0, microsecond=0, tzinfo=None)
            
            if not last_recorded:
                # If table empty, start from 24h ago
                last_recorded = start_of_current_hour - timedelta(hours=24)
            
            # We process from last_recorded + 1h up to (but not including) CURRENT hour
            current_target = last_recorded + timedelta(hours=1)
            processed_count = 0
            
            while current_target < start_of_current_hour:
                target_hour = current_target
                end_target_hour = target_hour + timedelta(hours=1)
                
                # Delete existing to prevent duplicates (idempotency)
                await session.execute(delete(PingStatsHourly).where(PingStatsHourly.timestamp == target_hour))
                
                # 2. Aggregation Query
                stmt = select(
                    PingLog.device_type,
                    PingLog.device_id,
                    func.avg(PingLog.latency_ms).label('avg_latency'),
                    func.count().label('total_pings'),
                    func.sum(PingLog.status.cast(Integer)).label('successful_pings')
                ).where(
                    PingLog.timestamp >= target_hour,
                    PingLog.timestamp < end_target_hour
                ).group_by(PingLog.device_type, PingLog.device_id)
                
                result = await session.execute(stmt)
                rows = result.all()
                
                rollup_buffer = []
                for row in rows:
                    total = row.total_pings
                    success = row.successful_pings or 0
                    
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
                    processed_count += 1
                
                current_target += timedelta(hours=1)
            
            if processed_count > 0:
                await session.commit()
                logger.info(f"[OK] Rollup: Processed {processed_count} hours of data.")
            else:
                logger.info("[INFO] Rollup: Up to date.")

    except Exception as e:
        logger.error(f"[ERROR] Rollup failed: {e}")

if __name__ == "__main__":
    asyncio.run(rollup_hourly_stats_job())

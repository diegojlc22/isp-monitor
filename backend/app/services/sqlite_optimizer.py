"""
SQLite Optimization Service - Like The Dude
Optimizes SQLite for high-performance monitoring (800+ devices)
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import text
from backend.app.database import engine, AsyncSessionLocal

async def optimize_sqlite():
    """
    Apply SQLite optimizations similar to The Dude
    - WAL mode for better concurrency
    - Optimized cache and page size
    - Auto-vacuum for space management
    """
    async with engine.begin() as conn:
        # Enable WAL (Write-Ahead Logging) mode - CRITICAL for performance
        # This allows reads and writes simultaneously (like The Dude)
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        
        # Set synchronous to NORMAL (faster, still safe)
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        
        # Increase cache size to 64MB (default is 2MB)
        # -64000 = 64MB (negative means KB)
        await conn.execute(text("PRAGMA cache_size=-64000;"))
        
        # Set page size to 4096 (optimal for most systems)
        await conn.execute(text("PRAGMA page_size=4096;"))
        
        # Enable auto-vacuum (incremental)
        # Automatically reclaims space when data is deleted
        await conn.execute(text("PRAGMA auto_vacuum=INCREMENTAL;"))
        
        # Set temp store to memory (faster)
        await conn.execute(text("PRAGMA temp_store=MEMORY;"))
        
        # Increase mmap size to 256MB for better performance
        await conn.execute(text("PRAGMA mmap_size=268435456;"))
        
        print("[OK] SQLite optimized (WAL mode, 64MB cache, auto-vacuum)")

async def vacuum_database():
    """
    Compact database and reclaim space
    Run this periodically (e.g., weekly)
    """
    try:
        async with engine.begin() as conn:
            # Incremental vacuum - reclaim some space without locking
            await conn.execute(text("PRAGMA incremental_vacuum;"))
            
            # Analyze database for query optimization
            await conn.execute(text("ANALYZE;"))
            
            print("[OK] Database vacuumed and analyzed")
    except Exception as e:
        print(f"Vacuum error: {e}")

async def get_database_stats():
    """
    Get database statistics (like The Dude's database info)
    """
    async with AsyncSessionLocal() as session:
        # Get database size
        result = await session.execute(text("PRAGMA page_count;"))
        page_count = result.scalar()
        
        result = await session.execute(text("PRAGMA page_size;"))
        page_size = result.scalar()
        
        db_size_mb = (page_count * page_size) / (1024 * 1024)
        
        # Get WAL size
        result = await session.execute(text("PRAGMA wal_checkpoint(PASSIVE);"))
        
        # Get table info
        result = await session.execute(text("""
            SELECT name, COUNT(*) as count 
            FROM (
                SELECT 'towers' as name FROM towers
                UNION ALL
                SELECT 'equipments' FROM equipments
                UNION ALL
                SELECT 'ping_logs' FROM ping_logs
            )
            GROUP BY name
        """))
        
        stats = {
            "database_size_mb": round(db_size_mb, 2),
            "page_count": page_count,
            "page_size": page_size,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return stats

async def create_performance_indexes():
    """
    Create indexes for better query performance
    Similar to The Dude's database optimization
    """
    async with engine.begin() as conn:
        # Index on ping_logs for faster queries
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ping_logs_timestamp 
            ON ping_logs(timestamp DESC);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ping_logs_device 
            ON ping_logs(device_type, device_id, timestamp DESC);
        """))
        
        # Index on equipments for faster lookups
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_equipments_tower 
            ON equipments(tower_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_equipments_ip 
            ON equipments(ip);
        """))
        
        # Index on towers
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_towers_ip 
            ON towers(ip);
        """))
        
        print("[OK] Performance indexes created")

async def maintenance_job():
    """
    Weekly maintenance job (like The Dude's database maintenance)
    """
    while True:
        try:
            print("[INFO] Running weekly database maintenance...")
            await vacuum_database()
            stats = await get_database_stats()
            print(f"[INFO] Database: {stats['database_size_mb']} MB")
        except Exception as e:
            print(f"Maintenance error: {e}")
        
        # Run every 7 days
        await asyncio.sleep(7 * 24 * 60 * 60)

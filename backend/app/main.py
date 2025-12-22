from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import towers, equipments, settings, auth, users, alerts

from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from backend.app.services.pinger_fast import monitor_job_fast as monitor_job
print("✅ Using ULTRA-FAST pinger (icmplib)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    async with engine.begin() as conn:
        # Create Tables
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed Admin User (from environment variables)
    import os
    admin_email = os.getenv("ADMIN_EMAIL", "diegojlc22@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "110812")
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(models.User).where(models.User.email == admin_email))
        user = res.scalar_one_or_none()
        if not user:
            print(f"Seeding Admin User: {admin_email}")
            admin_user = models.User(
                name="Admin",
                email=admin_email,
                hashed_password=auth_utils.get_password_hash(admin_password),
                role="admin"
            )
            db.add(admin_user)
            await db.commit()
            print("✅ Admin User Seeded.")
        
    # Optimize SQLite database (like The Dude)
    from backend.app.services.sqlite_optimizer import (
        optimize_sqlite, 
        create_performance_indexes,
        maintenance_job,
        get_database_stats
    )
    
    # Apply optimizations on startup
    await optimize_sqlite()
    await create_performance_indexes()
    
    # Get initial stats
    stats = await get_database_stats()
    print(f"📊 Database: {stats['database_size_mb']} MB")
    
    # Get ping interval from config
    from backend.app.config import PING_INTERVAL_SECONDS
    
    scheduler = AsyncIOScheduler()
    # Monitor: Run with configurable interval (default 30s)
    scheduler.add_job(monitor_job, 'interval', seconds=PING_INTERVAL_SECONDS)
    print(f"📡 Ping interval: {PING_INTERVAL_SECONDS}s")
    
    # Maintenance (Cleanup): Run every 24 hours
    from backend.app.services.maintenance import cleanup_logs
    scheduler.add_job(cleanup_logs, 'interval', hours=24) # Run once a day
    
    # Run cleanup once on startup
    import asyncio
    asyncio.create_task(cleanup_logs())
    
    # Weekly database maintenance (vacuum, analyze)
    asyncio.create_task(maintenance_job())

    scheduler.start()
    
    yield
    print("Shutting down...")
    try:
        scheduler.shutdown()
    except:
        pass

app = FastAPI(title="ISP Monitor API", lifespan=lifespan)

# CORS Configuration (from environment or defaults)
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")

# In production, set CORS_ORIGINS to specific domains
# Example: CORS_ORIGINS=https://monitor.yourcompany.com,https://app.yourcompany.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(towers.router)
app.include_router(equipments.router)
app.include_router(settings.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(alerts.router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "ISP Monitor Backend"}

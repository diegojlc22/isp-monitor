from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import towers, equipments, settings, auth, users, alerts

from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from backend.app.services.pinger_fast import monitor_job_fast as monitor_job
print("[INFO] Using ULTRA-FAST pinger (icmplib)")

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
            print("[OK] Admin User Seeded.")

        # Seed Telegram Config (if user requested hardcoded)
        from backend.app.models import Parameters
        telegram_token = os.getenv("TELEGRAM_TOKEN", "8158269697:AAGJGljtEFYy3pvouZrhs1QobIaXYzvrImc")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "-1003601324129")
        
        # Upsert Token
        token_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_token"))).scalar_one_or_none()
        if not token_obj:
            db.add(Parameters(key="telegram_token", value=telegram_token))
        elif token_obj.value != telegram_token: # Force update if hardcoded implies overwrite preference
             # Comment this elif out if you prefer DB value to persist over code default unless missing
             # For now, let's respect what's in DB unless missing, or update if you want to enforce these values
             pass 
        
        # Upsert Chat ID
        chat_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))).scalar_one_or_none()
        if not chat_obj:
            db.add(Parameters(key="telegram_chat_id", value=telegram_chat))
            
        await db.commit()
        print("[OK] Telegram Config Seeded (if missing).")
        
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
    print(f"[INFO] Database: {stats['database_size_mb']} MB")
    
    # Get ping interval from config
    from backend.app.config import PING_INTERVAL_SECONDS
    
    scheduler = AsyncIOScheduler()
    # Monitor: Run with configurable interval (default 30s)
    scheduler.add_job(monitor_job, 'interval', seconds=PING_INTERVAL_SECONDS)
    print(f"[INFO] Ping interval: {PING_INTERVAL_SECONDS}s")
    
    # Maintenance (Cleanup): Run every 24 hours
    from backend.app.services.maintenance import cleanup_job, backup_database_job
    scheduler.add_job(cleanup_job, 'interval', hours=24) # Run once a day
    scheduler.add_job(backup_database_job, 'cron', hour=0, minute=0) # Run at midnight
    
    # Run cleanup once on startup (background task)
    import asyncio
    asyncio.create_task(cleanup_job())
    
    # Weekly database maintenance (vacuum, analyze)
    asyncio.create_task(maintenance_job())

    # SNMP Traffic Monitor (Runs every 60s)
    from backend.app.services.snmp_monitor import snmp_monitor_job
    asyncio.create_task(snmp_monitor_job())

    # IA-AGENT: Synthetic Monitor (Runs every 5 min)
    try:
        from backend.app.services.synthetic_agent import synthetic_agent_job
        asyncio.create_task(synthetic_agent_job())
        print("[INFO] Synthetic Agent Started")
    except ImportError:
        print("[WARN] Synthetic Agent module missing")

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

# Gzip Compression (70-80% redução de tráfego HTTP)
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(towers.router, prefix="/api")
app.include_router(equipments.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")

# Agent (Synthetic Monitor)
from backend.app.routers import agent
app.include_router(agent.router, prefix="/api")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve Static Files (Frontend) - Production Mode
frontend_path = os.path.join(os.getcwd(), 'frontend', 'dist')

if os.path.exists(frontend_path):
    print(f"[INFO] Serving Frontend from {frontend_path}")
    
    # Mount assets folder
    if os.path.exists(os.path.join(frontend_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    # Catch-all for SPA routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if file exists in root (e.g. favicon.ico, manifest.json)
        potential_file = os.path.join(frontend_path, full_path)
        if os.path.exists(potential_file) and os.path.isfile(potential_file):
            return FileResponse(potential_file)

        # Serve index.html for all client-side routes
        # Note: API routes are matched *before* this catch-all because they are included above
        return FileResponse(os.path.join(frontend_path, "index.html"))

else:
    print("[WARN] frontend/dist not found. Running in API-only mode.")
    @app.get("/")
    def read_root():
        return {"status": "ok", "service": "ISP Monitor Backend - Frontend not found (Run deploy.bat)"}

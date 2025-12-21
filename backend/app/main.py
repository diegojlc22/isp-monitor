from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import towers, equipments, settings, auth, users
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

# Try to import fast pinger (icmplib), fallback to standard pinger
try:
    from backend.app.services.pinger_fast import monitor_job_fast as monitor_job
    print("✅ Using ULTRA-FAST pinger (icmplib) - like The Dude!")
except ImportError:
    from backend.app.services.pinger import monitor_job
    print("⚠️ Using standard pinger (ping3) - slower but works")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    async with engine.begin() as conn:
        # Create Tables
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed Admin User
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(models.User).where(models.User.email == "diegojlc22@gmail.com"))
        user = res.scalar_one_or_none()
        if not user:
            print("Seeding Admin User...")
            admin_user = models.User(
                name="Admin",
                email="diegojlc22@gmail.com",
                hashed_password=auth_utils.get_password_hash("110812"),
                role="admin"
            )
            db.add(admin_user)
            await db.commit()
            print("Admin User Seeded.")
        
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

    scheduler.start()
    
    yield
    print("Shutting down...")
    try:
        scheduler.shutdown()
    except:
        pass

app = FastAPI(title="ISP Monitor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(towers.router)
app.include_router(equipments.router)
app.include_router(settings.router)
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "ISP Monitor Backend"}

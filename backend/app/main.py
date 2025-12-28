from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy import select, text
import os
import time
import logging

from backend.app.routers import towers, equipments, settings, auth, users, alerts, agent, mobile, metrics, expo, ngrok
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from backend.app.utils.network_diagnostics import run_diagnostics
from backend.app.config import PING_INTERVAL_SECONDS

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

print("[INFO] Using ULTRA-FAST pinger (icmplib)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up ISP Monitor API...")
    
    # 1. Network Diagnostics
    try:
        run_diagnostics()
    except Exception as e:
        logger.warning(f"⚠️ [NETWORK DIAGNOSTICS] Failed: {e}")

    # 2. Database Init & Migration
    try:
        async with engine.begin() as conn:
            # Create Tables if not exist
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ [DATABASE] Tabelas verificadas.")
            
    except Exception as e:
        logger.error(f"❌ [DATABASE] Critical Startup Error: {e}")
        # We don't exit here to allow API to start and report health error
        
    # 3. Seed Data
    await seed_initial_data()
        
    logger.info("[INFO] API Ready (Collector Running in Separate Process)")
    
    yield
    
    logger.info("Shutting down API...")
    await engine.dispose()

async def seed_initial_data():
    """Seed Admin and Default Configs"""
    admin_email = os.getenv("ADMIN_EMAIL", "diegojlc22@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "110812")
    
    try:
        async with AsyncSessionLocal() as db:
            # Seed Admin
            res = await db.execute(select(models.User).where(models.User.email == admin_email))
            if not res.scalar_one_or_none():
                logger.info(f"Seeding Admin User: {admin_email}")
                admin = models.User(
                    name="Admin",
                    email=admin_email,
                    hashed_password=auth_utils.get_password_hash(admin_password),
                    role="admin"
                )
                db.add(admin)
                await db.commit()
            
            # Seed Telegram defaults if env vars exist
            tg_token = os.getenv("TELEGRAM_TOKEN", "")
            tg_chat = os.getenv("TELEGRAM_CHAT_ID", "-1003601324129")
            
            from backend.app.models import Parameters
            
            # Helper to upsert
            async def upsert_param(k, v):
                if not v: return
                curr = (await db.execute(select(Parameters).where(Parameters.key == k))).scalar_one_or_none()
                if not curr:
                    db.add(Parameters(key=k, value=v))
            
            await upsert_param("telegram_token", tg_token)
            await upsert_param("telegram_chat_id", tg_chat)
            await db.commit()
            
    except Exception as e:
        logger.warning(f"⚠️ Seed Data Warning: {e}")

app = FastAPI(title="ISP Monitor API", lifespan=lifespan)

# Middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# System Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    # Check DB connection
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "timestamp": time.time(),
        "version": "3.2.0-enterprise"
    }

@app.get("/api/setup/migrate")
async def run_manual_migration():
    """Migration endpoint (Legacy support)"""
    return {"status": "deprecated", "message": "Migrations run automatically on startup now"}

# Includes
app.include_router(towers.router, prefix="/api")
app.include_router(equipments.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(mobile.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(expo.router, prefix="/api")
app.include_router(ngrok.router, prefix="/api")

# Static Files
frontend_path = os.path.join(os.getcwd(), 'frontend', 'dist')
if os.path.exists(frontend_path):
    logger.info(f"Serving Frontend from {frontend_path}")
    if os.path.exists(os.path.join(frontend_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"): # Fallback for 404 API routes
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
            
        potential_file = os.path.join(frontend_path, full_path)
        if os.path.exists(potential_file) and os.path.isfile(potential_file):
            return FileResponse(potential_file)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    logger.warning("frontend/dist not found. Running in API-only mode.")
    @app.get("/")
    def read_root():
        return {"status": "ok", "service": "ISP Monitor Backend API"}

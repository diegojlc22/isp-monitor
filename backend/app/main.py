
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import towers, equipments, settings, auth, users, alerts
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from sqlalchemy import select
from contextlib import asynccontextmanager
import os

print("[INFO] Using ULTRA-FAST pinger (icmplib)")

from backend.app.utils.network_diagnostics import run_diagnostics

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    
    # 🧠 NETWORK INTELLIGENCE (Version 3.2)
    # Check for firewall issues and auto-correct if possible
    try:
        run_diagnostics()
    except Exception as e:
        print(f"⚠️ [NETWORK DIAGNOSTICS] Failed to run: {e}")

    async with engine.begin() as conn:
        # Create Tables
        await conn.run_sync(Base.metadata.create_all)
        
        # --- [FIX] FORÇAR MIGRAÇÃO DE COLUNAS FALTANTES ---
        from sqlalchemy import text
        print("🔧 [MIGRATION] Verificando esquema do banco...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_latitude FLOAT;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_longitude FLOAT;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_location_update TIMESTAMP WITHOUT TIME ZONE;"))
            print("✅ [MIGRATION] Colunas de rastreamento (users) aplicadas.")
        except Exception as e:
            print(f"⚠️ [MIGRATION] Falha ao migrar users: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS is_panel BOOLEAN DEFAULT FALSE;"))
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS associated_clients INTEGER DEFAULT 0;"))
            print("✅ [MIGRATION] Colunas de painéis (equipments) aplicadas.")
        except Exception as e:
            print(f"⚠️ [MIGRATION] Falha ao migrar equipments: {e}")
        # --------------------------------------------------
        
    # Seed Admin User (from environment variables)
    admin_email = os.getenv("ADMIN_EMAIL", "diegojlc22@gmail.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "110812")
    
    try:
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
    except Exception as e:
        print(f"⚠️ [WARNING] Falha ao verificar/criar Admin User: {e}")
        # Não abortar startup, permitir API subir para debugging

        # Seed Telegram Config (if user requested hardcoded)
        from backend.app.models import Parameters
        telegram_token = os.getenv("TELEGRAM_TOKEN", "8158269697:AAGJGljtEFYy3pvouZrhs1QobIaXYzvrImc")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "-1003601324129")
        
        # Upsert Token
        token_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_token"))).scalar_one_or_none()
        if not token_obj:
            db.add(Parameters(key="telegram_token", value=telegram_token))
        elif token_obj.value != telegram_token: 
             pass 
        
        # Upsert Chat ID
        chat_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))).scalar_one_or_none()
        if not chat_obj:
            db.add(Parameters(key="telegram_chat_id", value=telegram_chat))
            
        await db.commit()
        print("[OK] Telegram Config Seeded (if missing).")
        
    # Startup Message
    pass

    print("[INFO] API Started (Collector Running in Separate Process)")
    
    yield
    print("Shutting down API...")

app = FastAPI(title="ISP Monitor API", lifespan=lifespan)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip Compression
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/api/setup/migrate")
async def run_manual_migration():
    """Migração manual via API para evitar erros de conexão externa"""
    from sqlalchemy import text
    from backend.app.database import engine
    
    logs = []
    async with engine.begin() as conn:
        try:
            # 1. Towers
            await conn.execute(text("ALTER TABLE towers ADD COLUMN IF NOT EXISTS latitude FLOAT;"))
            await conn.execute(text("ALTER TABLE towers ADD COLUMN IF NOT EXISTS longitude FLOAT;"))
            logs.append("Towers atualizado.")
        except Exception as e:
            logs.append(f"Erro Towers: {e}")

        try:
            # 2. Equipments
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS is_panel BOOLEAN DEFAULT FALSE;"))
            await conn.execute(text("ALTER TABLE equipments ADD COLUMN IF NOT EXISTS associated_clients INTEGER DEFAULT 0;"))
            logs.append("Equipments atualizado.")
        except Exception as e:
            logs.append(f"Erro Equipments: {e}")
            
        try:
            # 3. Tower Requests
            sql = """
            CREATE TABLE IF NOT EXISTS tower_requests (
                id SERIAL PRIMARY KEY,
                name VARCHAR,
                ip VARCHAR,
                latitude FLOAT,
                longitude FLOAT,
                requested_by VARCHAR,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
                status VARCHAR DEFAULT 'pending'
            );
            """
            await conn.execute(text(sql))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tower_requests_id ON tower_requests (id);"))
            logs.append("TowerRequests criado.")
        except Exception as e:
            logs.append(f"Erro Requests: {e}")

        try:
            # 4. Users (Tracking)
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_latitude FLOAT;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_longitude FLOAT;"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_location_update TIMESTAMP WITHOUT TIME ZONE;"))
            logs.append("Users (Tracking) atualizado.")
        except Exception as e:
            logs.append(f"Erro Users: {e}")
            
    return {"status": "done", "logs": logs}

app.include_router(towers.router, prefix="/api")
app.include_router(equipments.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")

# Agent (Synthetic Monitor)
from backend.app.routers import agent
app.include_router(agent.router, prefix="/api")

# Mobile / APK
from backend.app.routers import mobile
app.include_router(mobile.router, prefix="/api")

# ✅ SPRINT 2: Métricas Internas
from backend.app.routers import metrics
app.include_router(metrics.router, prefix="/api")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve Static Files (Frontend)
frontend_path = os.path.join(os.getcwd(), 'frontend', 'dist')

if os.path.exists(frontend_path):
    print(f"[INFO] Serving Frontend from {frontend_path}")
    if os.path.exists(os.path.join(frontend_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        potential_file = os.path.join(frontend_path, full_path)
        if os.path.exists(potential_file) and os.path.isfile(potential_file):
            return FileResponse(potential_file)
        return FileResponse(os.path.join(frontend_path, "index.html"))

else:
    print("[WARN] frontend/dist not found. Running in API-only mode.")
    @app.get("/")
    def read_root():
        return {"status": "ok", "service": "ISP Monitor Backend - Frontend not found (Run deploy.bat)"}

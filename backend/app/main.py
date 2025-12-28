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

from backend.app.routers import towers, equipments, settings, auth, users, alerts, agent, mobile, metrics, expo
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app import models, auth_utils
from backend.app.utils.network_diagnostics import run_diagnostics
from backend.app.config import PING_INTERVAL_SECONDS

# ... (lines 18-141)

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

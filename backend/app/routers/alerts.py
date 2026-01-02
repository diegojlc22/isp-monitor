from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import Alert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime
from backend.app.services.cache import cache  # ✅ Cache para performance

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)

class AlertSchema(BaseModel):
    id: int
    device_type: str | None
    device_name: str | None
    device_ip: str | None
    message: str | None
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertSchema])
async def get_alerts(skip: int = 0, limit: int = 500, db: AsyncSession = Depends(get_db)):
    """Retorna alertas com cache de 10 segundos (alertas mudam rápido)"""
    # ✅ Tentar cache primeiro
    cache_key = f"alerts_list_{skip}_{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Buscar do banco
    result = await db.execute(
        select(Alert)
        .order_by(Alert.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    alerts = result.scalars().all()
    
    # ✅ Salvar no cache por 10 segundos (alertas mudam rápido)
    await cache.set(cache_key, alerts, ttl_seconds=10)
    
    return alerts

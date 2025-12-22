from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import Alert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from datetime import datetime

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
async def get_alerts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(Alert.timestamp.desc()).offset(skip).limit(limit))
    alerts = result.scalars().all()
    return alerts

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from typing import List
from backend.app.database import get_db
from backend.app.models import Insight, Equipment
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/insights", tags=["insights"])

class InsightSchema(BaseModel):
    id: int
    insight_type: str
    severity: str
    equipment_id: Optional[int]
    title: str
    message: str
    recommendation: Optional[str]
    timestamp: datetime
    is_dismissed: bool
    equipment_name: Optional[str]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[InsightSchema])
async def get_insights(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Insight, Equipment.name.label("equipment_name"))
        .outerjoin(Equipment, Insight.equipment_id == Equipment.id)
        .where(Insight.is_dismissed == False)
        .order_by(desc(Insight.timestamp))
        .limit(limit)
    )
    
    insights = []
    for row in result.all():
        insight = row[0]
        eq_name = row[1]
        
        # Manually construct response to include equipment_name
        insights.append({
            "id": insight.id,
            "insight_type": insight.insight_type,
            "severity": insight.severity,
            "equipment_id": insight.equipment_id,
            "title": insight.title,
            "message": insight.message,
            "recommendation": insight.recommendation,
            "timestamp": insight.timestamp,
            "is_dismissed": insight.is_dismissed,
            "equipment_name": eq_name
        })
    return insights

@router.post("/{insight_id}/dismiss")
async def dismiss_insight(insight_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Insight).where(Insight.id == insight_id).values(is_dismissed=True)
    )
    await db.commit()
    return {"status": "success"}

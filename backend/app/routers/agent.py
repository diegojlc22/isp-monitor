from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from backend.app.database import get_db, AsyncSession
from backend.app.models import SyntheticLog, User
from backend.app.auth_utils import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

@router.get("/logs")
async def get_synthetic_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent synthetic monitoring logs (DNS, HTTP).
    """
    stmt = select(SyntheticLog).order_by(desc(SyntheticLog.timestamp)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs

@router.post("/trigger")
async def trigger_manual_test(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger manual synthetic test immediately (for debugging).
    """
    from backend.app.services.synthetic_agent import synthetic_agent_job
    import asyncio
    asyncio.create_task(synthetic_agent_job())
    return {"status": "Test triggered in background"}

from pydantic import BaseModel

class TargetCreate(BaseModel):
    name: str
    target: str
    type: str # 'http', 'dns', 'icmp'

from backend.app.models import MonitorTarget

@router.get("/targets")
async def get_targets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(MonitorTarget))
    return result.scalars().all()

@router.post("/targets")
async def add_target(
    target: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_target = MonitorTarget(name=target.name, target=target.target, type=target.type)
    db.add(new_target)
    try:
        await db.commit()
        await db.refresh(new_target)
        return new_target
    except Exception as e:
        return {"error": str(e)}

@router.delete("/targets/{target_id}")
async def delete_target(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(MonitorTarget).where(MonitorTarget.id == target_id)
    result = await db.execute(stmt)
    target = result.scalar_one_or_none()
    if target:
        await db.delete(target)
        await db.commit()
    return {"status": "deleted"}

# Settings Management
from backend.app.models import Parameters

@router.get("/settings")
async def get_agent_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    keys = ["agent_latency_threshold", "agent_anomaly_cycles", "agent_check_interval"]
    stmt = select(Parameters).where(Parameters.key.in_(keys))
    result = await db.execute(stmt)
    params = result.scalars().all()
    
    # Defaults
    settings = {
        "agent_latency_threshold": "300",
        "agent_anomaly_cycles": "2",
        "agent_check_interval": "300"
    }
    
    for p in params:
        settings[p.key] = p.value
        
    return settings

class AgentSettingsUpdate(BaseModel):
    latency_threshold: int
    anomaly_cycles: int
    check_interval: int

@router.post("/settings")
async def update_agent_settings(
    settings: AgentSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Upsert Logic
    updates = {
        "agent_latency_threshold": str(settings.latency_threshold),
        "agent_anomaly_cycles": str(settings.anomaly_cycles),
        "agent_check_interval": str(settings.check_interval)
    }
    
    for key, value in updates.items():
        stmt = select(Parameters).where(Parameters.key == key)
        result = await db.execute(stmt)
        param = result.scalar_one_or_none()
        
        if param:
            param.value = value
        else:
            db.add(Parameters(key=key, value=value))
            
    await db.commit()
    return {"status": "updated"}

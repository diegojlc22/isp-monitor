from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models import Equipment, Parameters, Alert
from datetime import datetime, timezone, timedelta
import psutil
import time

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
async def get_system_health(db: AsyncSession = Depends(get_db)):
    # 1. Collector Status
    collector_status = "offline"
    res = await db.execute(select(Parameters).where(Parameters.key == "collector_last_seen"))
    last_seen_param = res.scalar_one_or_none()
    
    last_seen_val = None
    if last_seen_param:
        try:
            last_seen_val = last_seen_param.value
            last_seen = datetime.fromisoformat(last_seen_val)
            # Consider online if seen in the last 60 seconds
            if datetime.now(timezone.utc) - last_seen < timedelta(seconds=60):
                collector_status = "online"
        except:
            pass
            
    # 2. SNMP/Equipment Status
    total_equipments = await db.scalar(select(func.count(Equipment.id)))
    online_equipments = await db.scalar(select(func.count(Equipment.id)).where(Equipment.is_online == True))
    
    # 3. Database Stats
    start_time = time.time()
    await db.execute(select(func.now()))
    db_latency = round((time.time() - start_time) * 1000, 2)
    
    # 4. Recent Alerts
    res_alerts = await db.execute(select(Alert).order_by(Alert.timestamp.desc()).limit(10))
    alerts = res_alerts.scalars().all()
    
    # 5. System Resources (CPU/RAM)
    # interval=None to not block
    cpu_usage = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    
    return {
        "status": "ok",
        "collector": {
            "status": collector_status,
            "last_seen": last_seen_val
        },
        "snmp": {
            "total": total_equipments,
            "online": online_equipments,
            "offline": total_equipments - online_equipments
        },
        "database": {
            "status": "connected",
            "latency_ms": db_latency
        },
        "resources": {
            "cpu_percent": cpu_usage,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2)
        },
        "alerts": alerts,
        "version": "2.0.0"
    }

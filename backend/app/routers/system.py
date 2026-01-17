from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models import Equipment, Parameters, Alert
from datetime import datetime, timezone, timedelta
import psutil
import time
from backend.app.services.topology import run_topology_discovery
from backend.app.dependencies import get_current_user
import os

# --- APP RESOURCE TRACKING ---
_proc_cache = {} # pid -> psutil.Process object
_metrics_cache = {
    "data": None,
    "timestamp": 0
}

def get_app_metrics():
    """Calculates CPU and RAM consumption for our app processes with 5s cache."""
    now = time.time()
    if _metrics_cache["data"] and (now - _metrics_cache["timestamp"]) < 5:
        return _metrics_cache["data"]
        
    app_cpu = 0.0
    app_ram_rss = 0
    project_root = os.path.abspath(os.getcwd()).lower()
    
    # Identify our processes
    for proc in psutil.process_iter(['pid', 'cmdline', 'memory_info']):
        try:
            pinfo = proc.info
            cmdline_list = pinfo.get('cmdline')
            if not cmdline_list: continue
            
            cmdline = " ".join(cmdline_list).lower()
            
            # Check if it belongs to our project
            if project_root in cmdline or any(k in cmdline for k in ["backend.app.main", "collector.py", "self_heal.py", "server.js"]):
                app_ram_rss += pinfo.get('memory_info').rss if pinfo.get('memory_info') else 0
                
                pid = pinfo['pid']
                if pid not in _proc_cache:
                    _proc_cache[pid] = proc
                
                app_cpu += _proc_cache[pid].cpu_percent(interval=None)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Cleanup _proc_cache for dead processes
    current_pids = {p.pid for p in psutil.process_iter()}
    for cached_pid in list(_proc_cache.keys()):
        if cached_pid not in current_pids:
            del _proc_cache[cached_pid]

    ram_total = psutil.virtual_memory().total
    cpu_count = psutil.cpu_count() or 1
    
    res = {
        "cpu_percent": round(app_cpu / cpu_count, 1),
        "ram_percent": round((app_ram_rss / ram_total) * 100, 1) if ram_total > 0 else 0,
        "ram_used_gb": round(app_ram_rss / (1024**3), 2),
        "ram_total_gb": round(ram_total / (1024**3), 2),
        "is_app_only": True
    }
    _metrics_cache["data"] = res
    _metrics_cache["timestamp"] = now
    return res

router = APIRouter(prefix="/system", tags=["system"])

@router.post("/topology/discover")
async def trigger_topology_discovery(item: BackgroundTasks, current_user = Depends(get_current_user)):
    """
    Dispara manualmente a descoberta de topologia da rede.
    Rodará em background.
    """
    item.add_task(run_topology_discovery)
    return {"message": "Descoberta de topologia iniciada em background."}

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
    
    # Check SNMP Heartbeat
    snmp_status = "unknown"
    res_snmp = await db.execute(select(Parameters).where(Parameters.key == "snmp_monitor_last_run"))
    snmp_last_val = res_snmp.scalar_one_or_none()
    
    snmp_last_run_iso = None
    if snmp_last_val:
        try:
            snmp_last_run_iso = snmp_last_val.value
            last_run = datetime.fromisoformat(snmp_last_run_iso)
            # SNMP runs every 10s. If > 120s (2 mins), it's stalled.
            if datetime.now() - last_run < timedelta(seconds=120):
                snmp_status = "active"
            else:
                snmp_status = "stalled"
        except: pass
    # 3. Database Stats
    start_time = time.time()
    await db.execute(select(func.now()))
    db_latency = round((time.time() - start_time) * 1000)
    
    # 4. Recent Alerts
    res_alerts = await db.execute(select(Alert).order_by(Alert.timestamp.desc()).limit(10))
    alerts = res_alerts.scalars().all()
    
    # 5. Backup Status
    res_backup = await db.execute(select(Parameters).where(Parameters.key == "last_backup_run"))
    backup_param = res_backup.scalar_one_or_none()
    last_backup_val = backup_param.value if backup_param else None

    # 6. Resources (Cached)
    resources = get_app_metrics()
    
    return {
        "status": "ok",
        "collector": {
            "status": collector_status,
            "last_seen": last_seen_val
        },
        "snmp": {
            "status": snmp_status,
            "last_run": snmp_last_run_iso,
            "total": total_equipments,
            "online": online_equipments,
            "offline": total_equipments - online_equipments
        },
        "database": {
            "status": "connected",
            "latency_ms": db_latency
        },
        "resources": resources,
        "alerts": alerts,
        "backup": {
            "last_run": last_backup_val
        },
        "version": "4.2.0-turbo"
    }

import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from backend.app.database import get_db, AsyncSession
from backend.app.models import SyntheticLog, User
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/agent", tags=["agent"])

@router.get("/logs")
async def get_synthetic_logs(
    limit: int = 20,
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

@router.delete("/logs")
async def clear_agent_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import delete
    await db.execute(delete(SyntheticLog))
    await db.commit()
    return {"message": "Logs limpos com sucesso"}

@router.post("/trigger")
async def trigger_manual_test(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia o loop de monitoramento manual contínuo em background.
    """
    from backend.app.services.synthetic_agent import start_manual_test_loop
    asyncio.create_task(start_manual_test_loop())
    return {"status": "Continuous test loop started in background"}

@router.post("/stop")
async def stop_manual_test(
    current_user: User = Depends(get_current_user)
):
    """
    Para o loop de monitoramento manual.
    """
    from backend.app.services.synthetic_agent import stop_manual_test_loop
    await stop_manual_test_loop()
    return {"status": "Manual test loop stop signal sent"}

@router.get("/status")
async def get_agent_status(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna se o loop manual está rodando.
    """
    from backend.app.services.synthetic_agent import manual_loop_running
    return {"manual_loop_running": manual_loop_running}

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
    keys = ["agent_latency_threshold", "agent_anomaly_cycles", "agent_check_interval", "telegram_token", "telegram_chat_id"]
    stmt = select(Parameters).where(Parameters.key.in_(keys))
    result = await db.execute(stmt)
    params = result.scalars().all()
    
    # Defaults
    settings = {
        "agent_latency_threshold": "300",
        "agent_anomaly_cycles": "2",
        "agent_check_interval": "300",
        "telegram_token": "",
        "telegram_chat_id": ""
    }
    
    for p in params:
        settings[p.key] = p.value
        
    return settings

class AgentSettingsUpdate(BaseModel):
    latency_threshold: int
    anomaly_cycles: int
    check_interval: int
    telegram_token: str | None = None
    telegram_chat_id: str | None = None

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
    
    if settings.telegram_token is not None:
        updates["telegram_token"] = settings.telegram_token
    if settings.telegram_chat_id is not None:
        updates["telegram_chat_id"] = settings.telegram_chat_id
    
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

@router.post("/telegram-test")
async def test_telegram_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from backend.app.services.telegram import send_telegram_alert
    
    # Fetch current settings from DB to test what is saved
    stmt = select(Parameters).where(Parameters.key.in_(["telegram_token", "telegram_chat_id"]))
    result = await db.execute(stmt)
    params = {p.key: p.value for p in result.scalars().all()}
    
    token = params.get("telegram_token")
    chat_id = params.get("telegram_chat_id")
    
    if not token or not chat_id:
        return {"success": False, "message": "Token ou Chat ID não configurados."}
        
    try:
        await send_telegram_alert(token, chat_id, "🔔 **Teste de Configuração**\n\nO sistema de alertas do ISP Monitor está funcionando corretamente! 🚀")
        return {"success": True, "message": "Mensagem enviada! Verifique seu Telegram."}
    except Exception as e:
        return {"success": False, "message": f"Erro ao enviar: {str(e)}"}

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models import Parameters
from backend.app.schemas import TelegramConfig
from backend.app.dependencies import get_current_admin_user

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/system-name")
async def get_system_name(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Parameters).where(Parameters.key == "system_name"))
    param = res.scalar_one_or_none()
    return {"name": param.value if param else "ISP Monitor"}

@router.post("/system-name")
async def update_system_name(data: dict, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    name = data.get("name")
    res = await db.execute(select(Parameters).where(Parameters.key == "system_name"))
    param = res.scalar_one_or_none()
    if not param:
        param = Parameters(key="system_name", value=name)
        db.add(param)
    else:
        param.value = name
    await db.commit()
    return {"name": name}

@router.get("/telegram", response_model=TelegramConfig)
async def get_telegram_config(db: AsyncSession = Depends(get_db)):
    token_res = await db.execute(select(Parameters).where(Parameters.key == "telegram_token"))
    chat_res = await db.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))
    
    token = token_res.scalar_one_or_none()
    chat_id = chat_res.scalar_one_or_none()
    
    return TelegramConfig(
        bot_token=token.value if token else "",
        chat_id=chat_id.value if chat_id else ""
    )

@router.post("/telegram")
async def update_telegram_config(config: TelegramConfig, db: AsyncSession = Depends(get_db)):
    # Upsert Token
    token_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_token"))).scalar_one_or_none()
    if not token_obj:
        token_obj = Parameters(key="telegram_token", value=config.bot_token)
        db.add(token_obj)
    else:
        token_obj.value = config.bot_token
        
    # Upsert Chat ID
    chat_obj = (await db.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))).scalar_one_or_none()
    if not chat_obj:
        chat_obj = Parameters(key="telegram_chat_id", value=config.chat_id)
        db.add(chat_obj)
    else:
        chat_obj.value = config.chat_id
        
    await db.commit()
    return {"message": "Settings updated"}

from backend.app.schemas import LatencyThresholds

@router.get("/latency", response_model=LatencyThresholds)
async def get_latency_config(db: AsyncSession = Depends(get_db)):
    good_res = await db.execute(select(Parameters).where(Parameters.key == "latency_good"))
    crit_res = await db.execute(select(Parameters).where(Parameters.key == "latency_critical"))
    
    good = good_res.scalar_one_or_none()
    crit = crit_res.scalar_one_or_none()
    
    return LatencyThresholds(
        good=int(good.value) if good else 50,
        critical=int(crit.value) if crit else 200
    )

@router.post("/latency")
async def update_latency_config(config: LatencyThresholds, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Upsert Good
    good_obj = (await db.execute(select(Parameters).where(Parameters.key == "latency_good"))).scalar_one_or_none()
    if not good_obj:
        good_obj = Parameters(key="latency_good", value=str(config.good))
        db.add(good_obj)
    else:
        good_obj.value = str(config.good)
        
    # Upsert Critical
    crit_obj = (await db.execute(select(Parameters).where(Parameters.key == "latency_critical"))).scalar_one_or_none()
    if not crit_obj:
        crit_obj = Parameters(key="latency_critical", value=str(config.critical))
        db.add(crit_obj)
    else:
        crit_obj.value = str(config.critical)
        
    await db.commit()
    return {"message": "Latency thresholds updated"}

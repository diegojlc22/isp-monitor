from fastapi import APIRouter, Depends
from typing import Optional
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
    # Helper interno para buscar valor
    async def get_val(key):
        res = await db.execute(select(Parameters).where(Parameters.key == key))
        obj = res.scalar_one_or_none()
        return obj.value if obj else None

    return TelegramConfig(
        bot_token=await get_val("telegram_token") or "",
        chat_id=await get_val("telegram_chat_id") or "",
        backup_chat_id=await get_val("telegram_backup_chat_id") or "",
        template_down=await get_val("telegram_template_down"),
        template_up=await get_val("telegram_template_up"),
        # Multi-Channel
        telegram_enabled=(await get_val("telegram_enabled") != "false"), # Default True
        whatsapp_enabled=(await get_val("whatsapp_enabled") == "true"),  # Default False
        whatsapp_target=await get_val("whatsapp_target") or "",
        whatsapp_target_group=await get_val("whatsapp_target_group") or ""
    )

@router.post("/telegram")
async def update_telegram_config(config: TelegramConfig, db: AsyncSession = Depends(get_db)):
    # Validar WhatsApp Target
    # Pelo menos um target deve existir se estiver ativado, mas frontend valida melhor
    pass

    async def upsert(key, value):
        # Se value for None, nao faz nada, assumindo opcional nao enviado
        # Mas para booleanos e strings vazias, queremos salvar.
        if value is None: return 
        
        obj = (await db.execute(select(Parameters).where(Parameters.key == key))).scalar_one_or_none()
        if not obj:
            db.add(Parameters(key=key, value=str(value)))
        else:
            obj.value = str(value)

    await upsert("telegram_token", config.bot_token)
    await upsert("telegram_chat_id", config.chat_id)
    await upsert("telegram_backup_chat_id", config.backup_chat_id)
    await upsert("telegram_template_down", config.template_down)
    await upsert("telegram_template_up", config.template_up)
    
    # Novos Campos
    await upsert("telegram_enabled", "true" if config.telegram_enabled else "false")
    await upsert("whatsapp_enabled", "true" if config.whatsapp_enabled else "false")
    await upsert("whatsapp_target", config.whatsapp_target)
    await upsert("whatsapp_target_group", config.whatsapp_target_group)

    await db.commit()
    return {"message": "Configurações de alerta atualizadas"}

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

from pydantic import BaseModel
import os

class DatabaseConfig(BaseModel):
    db_type: str = "sqlite" # sqlite, postgresql
    postgres_url: str = "" # postgresql+asyncpg://user:pass@localhost/dbname

@router.get("/database", response_model=DatabaseConfig)
async def get_database_config(current_user = Depends(get_current_admin_user)):
    # Read from env var or .env file manually if needed, but for now just check os.environ
    # In a real app we might read specific .env file content
    current_url = os.getenv("DATABASE_URL", "")
    
    if "postgresql" in current_url:
        return DatabaseConfig(db_type="postgresql", postgres_url=current_url)
    else:
        return DatabaseConfig(db_type="sqlite", postgres_url="")

@router.post("/database")
async def update_database_config(config: DatabaseConfig, current_user = Depends(get_current_admin_user)):
    # Create or update .env file
    env_path = ".env"
    
    new_url = ""
    if config.db_type == "postgresql":
        # Validate minimal structure
        if "postgresql" not in config.postgres_url:
             return {"error": "URL inválida. Deve começar com postgresql..."}
        new_url = config.postgres_url
    
    # Write to .env
    # We read existing lines to preserve other keys if any (though we don't have many yet)
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    # Remove existing DATABASE_URL
    lines = [line for line in lines if not line.startswith("DATABASE_URL=")]
    
    # Add new if not sqlite (sqlite is default when missing)
    if new_url:
        lines.append(f"DATABASE_URL={new_url}\n")
        
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    # Update current os.environ so it affects current process if we were to re-init (though restart is best)
    # The user should restart the backend for this to fully take effect usually
    if new_url:
        os.environ["DATABASE_URL"] = new_url
    else:
         os.environ.pop("DATABASE_URL", None)
         
    return {"message": "Configuração salva. Por favor, reinicie o backend para aplicar as mudanças."}

from backend.app.models import Tower, Equipment, NetworkLink, User, PingLog, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

class MigrateRequest(BaseModel):
    postgres_url: str

@router.post("/migrate-data")
async def migrate_data(request: MigrateRequest, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # 1. Check if current DB is SQLite (or just proceed, reading from 'db')
    # We read from 'db' (Source)
    
    # 2. Connect to Target (Postgres)
    try:
        target_engine = create_async_engine(request.postgres_url)
        TargetSession = async_sessionmaker(target_engine, class_=AsyncSession, expire_on_commit=False)
        
        # 3. Create Tables in Target
        async with target_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # 4. Read & Write Data
        async with TargetSession() as target_db:
            # Users
            users = (await db.execute(select(User))).scalars().all()
            for u in users:
                # We use merge to avoid conflicts if re-running, or make new instances
                # Detaching from source session is automatic when querying usually, but let's be safe by creating new objs
                new_u = User(name=u.name, email=u.email, hashed_password=u.hashed_password, role=u.role, created_at=u.created_at)
                target_db.add(new_u)
            
            # Parameters
            params = (await db.execute(select(Parameters))).scalars().all()
            for p in params:
                 target_db.add(Parameters(key=p.key, value=p.value))
                 
            # Towers (Flush to get IDs if needed, but we copy IDs manually if possible or rely on auto)
            # Better to copy IDs to maintain relationships!
            towers = (await db.execute(select(Tower))).scalars().all()
            for t in towers:
                target_db.add(Tower(id=t.id, name=t.name, ip=t.ip, latitude=t.latitude, longitude=t.longitude, observations=t.observations, is_online=t.is_online, last_checked=t.last_checked))
            
            # Equipments
            equipments = (await db.execute(select(Equipment))).scalars().all()
            for e in equipments:
                # include ssh fields
                target_db.add(Equipment(id=e.id, name=e.name, ip=e.ip, tower_id=e.tower_id, is_online=e.is_online, last_checked=e.last_checked, last_latency=e.last_latency, ssh_user=e.ssh_user, ssh_password=e.ssh_password, ssh_port=e.ssh_port))
                
            # Links
            links = (await db.execute(select(NetworkLink))).scalars().all()
            for l in links:
                target_db.add(NetworkLink(id=l.id, source_tower_id=l.source_tower_id, target_tower_id=l.target_tower_id, type=l.type))
                
            # Ping Logs (Optional/Heavy) - Limit to last 1000 per device or just all if small
            # For this feature, we try all. If it fails, user can start fresh logs.
            # logs = (await db.execute(select(PingLog))).scalars().all()
            # for l in logs:
            #    target_db.add(PingLog(device_type=l.device_type, device_id=l.device_id, status=l.status, latency_ms=l.latency_ms, timestamp=l.timestamp))
            
            await target_db.commit()
            
        await target_engine.dispose()
        return {"message": "Migração de dados (Cadastros) realizada com sucesso!"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Erro na migração: {str(e)}"}

from backend.app.services.telegram import send_telegram_message
@router.post("/telegram/test-message")
async def test_telegram_message(db: AsyncSession = Depends(get_db)):
    try:
        token_res = await db.execute(select(Parameters).where(Parameters.key == "telegram_token"))
        chat_res = await db.execute(select(Parameters).where(Parameters.key == "telegram_chat_id"))
        
        token = token_res.scalar_one_or_none()
        chat_id = chat_res.scalar_one_or_none()
        
        if not token or not token.value:
            return {"error": "Bot Token não configurado."}
        if not chat_id or not chat_id.value:
            return {"error": "Chat ID de Alertas não configurado."}
            
        await send_telegram_message(token.value, chat_id.value, "🔔 Teste de Alerta: O sistema de notificações está funcionando!")
        return {"message": "Mensagem de teste enviada com sucesso!"}
    except Exception as e:
        return {"error": f"Erro ao enviar teste: {str(e)}"}

# Teste WhatsApp
from fastapi import Body

class WhatsAppTestRequest(BaseModel):
    target: Optional[str] = None

@router.post("/whatsapp/test-message")
async def test_whatsapp_message_route(
    req: WhatsAppTestRequest = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    try:
        import aiohttp
        
        target_value = None
        
        # 1. Prioridade: Target informado no Request (Teste rápido)
        if req and req.target:
            target_value = req.target
            
        # 2. Fallback: Target salvo no Banco
        if not target_value:
            res = await db.execute(select(Parameters).where(Parameters.key == "whatsapp_target"))
            target_obj = res.scalar_one_or_none()
            if target_obj:
                target_value = target_obj.value
        
        if not target_value:
             return {"error": "Nenhum destino informado (nem na requisição, nem salvo no banco)."}
             
        alert_msg = "🔔 *[WhatsApp]* Teste de Notificação: *Sucesso!* 🚀"
        
        url = "http://127.0.0.1:3001/send"
        async with aiohttp.ClientSession() as session:
            try:
                # Timeout curto pois é localhost
                async with session.post(url, json={"number": target_value, "message": alert_msg}, timeout=10) as resp:
                    if resp.status == 200:
                        return {"message": f"Mensagem enviada para {target_value}"}
                    elif resp.status == 404:
                         return {"error": "Número não encontrado no WhatsApp."}
                    elif resp.status == 503:
                         return {"error": "WhatsApp sincronizando/carregando. Tente em breve."}
                    else:
                        text = await resp.text()
                        return {"error": f"Erro Gateway: {text}"}
            except Exception as conn_err:
                 return {"error": f"Falha ao conectar no Gateway Zap (Porta 3001): {conn_err}"}

    except Exception as e:
        return {"error": str(e)}

@router.post("/telegram/test-backup")
async def test_telegram_backup():
    return {"error": "Backup via painel desativado para PostgreSQL. Use pg_dump no servidor."}

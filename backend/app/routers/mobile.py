import subprocess
import os
import threading
import time
import math
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models import Tower, TowerRequest
import logging
import socket

logger = logging.getLogger("api")

router = APIRouter(prefix="/mobile", tags=["mobile"])

# --- Models ---
class MobileStatus(BaseModel):
    is_running: bool
    url: str | None = None
    logs: list[str] = []

class GeoLocation(BaseModel):
    latitude: float
    longitude: float

class TowerRequestCreate(BaseModel):
    name: str | None = "Nova Solicitação"
    ip: str | None = None
    latitude: float
    longitude: float
    requested_by: str | None = "Técnico"

class TowerApproval(BaseModel):
    name: str

# --- State ---
expo_process = None
expo_url = None
expo_logs = []
logs_lock = threading.Lock()

# --- Helpers ---
def add_log(msg: str):
    global expo_logs
    with logs_lock:
        expo_logs.append(msg)
        if len(expo_logs) > 50:
            expo_logs.pop(0)

def monitor_expo(proc):
    global expo_url
    try:
        for line in iter(proc.stdout.readline, ''):
            if not line: break
            line = line.strip()
            if not line: continue
            
            if "exp://" in line:
                parts = line.split()
                for p in parts:
                    if "exp://" in p:
                        clean_url = p.replace('│', '').strip()
                        expo_url = clean_url
                        add_log(f"URL DETECTADA: {clean_url}")
            add_log(line)
    except Exception as e:
        add_log(f"Erro no monitor: {e}")

# --- Routes ---
@router.get("/status", response_model=MobileStatus)
def get_status():
    global expo_process, expo_url
    is_running = False
    if expo_process is not None:
        if expo_process.poll() is None:
            is_running = True
        else:
            expo_process = None
    
    return MobileStatus(is_running=is_running, url=expo_url, logs=list(expo_logs))

@router.post("/start")
def start_mobile():
    global expo_process, expo_url, expo_logs
    if expo_process is not None and expo_process.poll() is None:
        return {"message": "Já rodando"}
    
    expo_url = None
    with logs_lock: expo_logs = ["Iniciando..."]

    try:
        cwd = os.getcwd()
        mobile_dir = os.path.join(cwd, "mobile")
        if not os.path.exists(mobile_dir):
             if os.path.exists(os.path.join(cwd, "..", "mobile")):
                mobile_dir = os.path.abspath(os.path.join(cwd, "..", "mobile"))
             else:
                 raise HTTPException(404, "Pasta mobile não achada")

        env = os.environ.copy()
        env["CI"] = "1"
        env["EXPO_NO_TELEMETRY"] = "1"
        env["NO_COLOR"] = "1"

        # --offline --go
        cmd = "npx expo start --offline --go"

        expo_process = subprocess.Popen(
            cmd, shell=True, cwd=mobile_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            text=True, env=env, encoding='utf-8', errors='ignore', bufsize=1
        )
        threading.Thread(target=monitor_expo, args=(expo_process,), daemon=True).start()
        return {"message": "Iniciado"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/stop")
def stop_mobile():
    global expo_process
    if expo_process:
        try:
            subprocess.run(f"taskkill /F /PID {expo_process.pid} /T", shell=True)
        except: pass
        expo_process = None
    return {"message": "Parado"}

@router.get("/ping")
def mobile_ping():
    return {"status": "ok", "message": "Mobile API is reachable"}

@router.post("/nearby-towers")
@router.post("/nearby-towers/")
async def get_nearby_towers(loc: GeoLocation, db: AsyncSession = Depends(get_db)):
    """Busca torres próximas (usado pelo APP Mobile)"""
    print(f"[DEBUG MOBILE] Recebido pedido de torres: {loc}")
    try:
        result = await db.execute(select(Tower))
        towers = result.scalars().all()
        response = []
        for t in towers:
            if t.latitude and t.longitude:
                try:
                    lat_t = float(t.latitude)
                    lon_t = float(t.longitude)
                    # Haversine
                    R = 6371
                    dlat = math.radians(lat_t - loc.latitude)
                    dlon = math.radians(lon_t - loc.longitude)
                    a = math.sin(dlat/2)**2 + math.cos(math.radians(loc.latitude)) * math.cos(math.radians(lat_t)) * math.sin(dlon/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    dist = R * c
                    
                    response.append({
                        "id": t.id,
                        "name": t.name,
                        "latitude": t.latitude,
                        "longitude": t.longitude,
                        "distance": dist
                    })
                except: continue
        response.sort(key=lambda x: x["distance"])
        
        # DEBUG RESPOSTA
        print(f"[DEBUG MOBILE] Retornando {len(response)} torres.")
        if len(response) > 0:
            print(f"[DEBUG MOBILE] Exemplo: {response[0]['name']} -> {response[0]['distance']:.2f} km")
            
        return response
    except Exception as e:
        print(f"Erro Towers: {e}")
        return [] # Retorna vazio em erro para não quebrar app

# State Global para última localização
latest_technician_location = {}

@router.get("/last-location")
def get_last_location():
    """Retorna a última posição conhecida do técnico para o painel Web"""
    return latest_technician_location

@router.get("/config")
def get_mobile_config():
    """Retorna configurações para o App, incluindo IPs locais do servidor"""
    local_ips = []
    try:
        # Pega todos os IPs locais da máquina
        hostname = socket.gethostname()
        addr_info = socket.getaddrinfo(hostname, None)
        for info in addr_info:
            ip = info[4][0]
            if "." in ip and not ip.startswith("127."): # Apenas IPv4 local
                if ip not in local_ips:
                    local_ips.append(ip)
    except Exception as e:
        logger.error(f"Erro ao obter IPs locais: {e}")
    
    logger.info(f"📡 [MOBILE CONFIG] IPs locais enviados ao App: {local_ips}")
    return {
        "local_ips": local_ips,
        "server_time": time.time()
    }

@router.post("/location")
async def receive_location(loc: GeoLocation):
    global latest_technician_location
    """Recebe localização do técnico em tempo real"""
    logger.info(f"📍 [MOBILE LOCATION] Técnico em: {loc.latitude}, {loc.longitude}")
    latest_technician_location = {
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "timestamp": time.time()
    }
    return {"status": "received"}

@router.post("/tower-request")
async def create_tower_request(req: TowerRequestCreate, db: AsyncSession = Depends(get_db)):
    """Recebe pedido de nova torre vindo do APK"""
    final_name = req.name
    if not final_name or final_name == "Nova Solicitação":
        final_name = f"Torre {time.strftime('%H:%M:%S')}"
        
    logger.info(f"📡 [TOWER REQUEST] Nova solicitação: {final_name} em {req.latitude}, {req.longitude}")
    new_req = TowerRequest(
        name=final_name,
        ip=req.ip,
        latitude=req.latitude,
        longitude=req.longitude,
        requested_by=req.requested_by,
        status="pending"
    )
    db.add(new_req)
    await db.commit()
    return {"status": "ok", "message": "Solicitação enviada"}

@router.get("/requests")
async def list_tower_requests(db: AsyncSession = Depends(get_db)):
    """Lista pedidos pendentes para o painel admin"""
    result = await db.execute(select(TowerRequest).where(TowerRequest.status == "pending"))
    rows = result.scalars().all()
    # Mapear para o formato que o frontend (RequestsPage.tsx) espera: {id, name, by, lat, lon}
    return [{
        "id": r.id,
        "name": r.name,
        "by": r.requested_by,
        "lat": r.latitude,
        "lon": r.longitude
    } for r in rows]

@router.post("/requests/{id}/approve")
async def approve_tower_request(id: int, data: TowerApproval, db: AsyncSession = Depends(get_db)):
    """Aprova e cria a torre real"""
    result = await db.execute(select(TowerRequest).where(TowerRequest.id == id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Solicitação não encontrada")
    
    # Criar a torre com o nome fornecido pelo Admin
    new_tower = Tower(
        name=data.name,
        ip=req.ip,
        latitude=req.latitude,
        longitude=req.longitude
    )
    db.add(new_tower)
    
    # Marcar como aprovado
    req.status = "approved"
    await db.commit()
    return {"status": "ok"}

@router.post("/requests/{id}/reject")
async def reject_tower_request(id: int, db: AsyncSession = Depends(get_db)):
    """Rejeita a solicitação"""
    result = await db.execute(select(TowerRequest).where(TowerRequest.id == id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Solicitação não encontrada")
    
    await db.delete(req)
    await db.commit()
    return {"status": "ok"}

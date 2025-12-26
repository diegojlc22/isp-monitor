
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from math import radians, cos, sin, asin, sqrt
from backend.app.database import get_db
from backend.app.models import Tower, TowerRequest, Equipment, User
from backend.app.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/mobile", tags=["mobile"])

# Schemas
class GeoLocation(BaseModel):
    latitude: float
    longitude: float

class TowerDistanceResponse(BaseModel):
    id: int
    name: str
    distance_km: float
    ip: Optional[str] = None
    panel_count: int
    total_clients: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TowerRequestCreate(BaseModel):
    name: str
    ip: Optional[str] = None
    latitude: float
    longitude: float
    requested_by: str

# Helper: Haversine Formula
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    if not lat1 or not lon1 or not lat2 or not lon2:
        return 999999.0 # Infinity

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

@router.post("/nearby-towers", response_model=List[TowerDistanceResponse])
async def get_nearby_towers(location: GeoLocation, db: AsyncSession = Depends(get_db)):
    """
    Retorna torres ordenadas pela proximidade da localização do técnico.
    """
    try:
        # Buscar todas as torres
        result = await db.execute(select(Tower))
        towers = result.scalars().all()
        
        nearby_list = []
        # print(f"[DEBUG] Analisando {len(towers)} torres perto de {location}")
        
        for tower in towers:
            # Proteção extra contra dados inválidos
            try:
                t_lat = float(tower.latitude) if tower.latitude is not None else None
                t_lon = float(tower.longitude) if tower.longitude is not None else None
            except ValueError:
                t_lat = None
                t_lon = None
            
            dist = calculate_distance(location.latitude, location.longitude, t_lat, t_lon)
            
            # Contar stats
            panels = 0
            clients = 0
            
            # Query auxiliar (poderia ser otimizado com join, mas ok pra agora)
            q_stats = await db.execute(
                select(Equipment).where(Equipment.tower_id == tower.id)
            )
            eqs = q_stats.scalars().all()
            
            for e in eqs:
                if e.is_panel: panels += 1
                clients += (e.associated_clients or 0)
                
            nearby_list.append({
                "id": tower.id,
                "name": tower.name,
                "ip": tower.ip,
                "distance_km": round(dist, 2),
                "panel_count": panels,
                "total_clients": clients,
                "latitude": t_lat,
                "longitude": t_lon
            })
            
        nearby_list.sort(key=lambda x: x["distance_km"])
        return nearby_list
        
    except Exception as e:
        print(f"[ERROR] Erro em get_nearby_towers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tower-request", response_model=dict)
async def request_new_tower(request: TowerRequestCreate, db: AsyncSession = Depends(get_db)):
    """
    Cria uma solicitação de nova torre para aprovação.
    """
    new_req = TowerRequest(
        name=request.name,
        ip=request.ip,
        latitude=request.latitude,
        longitude=request.longitude,
        requested_by=request.requested_by,
        status="pending"
    )
    db.add(new_req)
    await db.commit()
    
    return {"message": "Solicitação enviada com sucesso! Aguarde aprovação.", "id": new_req.id}

@router.get("/requests", response_model=List[dict])
async def get_pending_requests(db: AsyncSession = Depends(get_db)):
    """
    Admin: Lista solicitações pendentes
    """
    result = await db.execute(select(TowerRequest).where(TowerRequest.status == "pending"))
    reqs = result.scalars().all()
    return [{"id": r.id, "name": r.name, "by": r.requested_by, "lat": r.latitude, "lon": r.longitude} for r in reqs]

@router.post("/requests/{req_id}/approve")
async def approve_tower_request(req_id: int, db: AsyncSession = Depends(get_db)):
    """
    Admin: Aprova e cria a torre oficial
    """
    req = await db.get(TowerRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Solicitação já processada")
        
    # Criar Torre Oficial
    new_tower = Tower(
        name=req.name,
        ip=req.ip,
        latitude=req.latitude,
        longitude=req.longitude
    )
    db.add(new_tower)
    
    req.status = "approved"
    await db.commit()
    return {"message": f"Torre {new_tower.name} criada com sucesso!"}

@router.post("/requests/{req_id}/reject")
async def reject_tower_request(req_id: int, db: AsyncSession = Depends(get_db)):
    """
    Admin: Rejeita a solicitaçao
    """
    req = await db.get(TowerRequest, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Solicitação já processada")
        
    req.status = "rejected"
    await db.commit()
    return {"message": "Solicitação rejeitada."}

# --- Tracking ---

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

@router.post("/location")
async def update_technician_location(
    loc: LocationUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recebe atualização de GPS do técnico logado.
    """
    print(f"📍 [TRACKING] {current_user.name} enviou localização: {loc.latitude}, {loc.longitude}")
    current_user.last_latitude = loc.latitude
    current_user.last_longitude = loc.longitude
    current_user.last_location_update = datetime.utcnow()
    
    await db.commit()
    return {"status": "ok"}

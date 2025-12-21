from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app.database import get_db
from backend.app.models import Equipment
from backend.app.schemas import Equipment as EquipmentSchema, EquipmentCreate

router = APIRouter(prefix="/equipments", tags=["equipments"])

@router.get("/", response_model=List[EquipmentSchema])
async def read_equipments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Equipment).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=EquipmentSchema)
async def create_equipment(equipment: EquipmentCreate, db: AsyncSession = Depends(get_db)):
    db_eq = Equipment(**equipment.model_dump())
    db.add(db_eq)
    await db.commit()
    await db.refresh(db_eq)
    return db_eq

@router.put("/{eq_id}", response_model=EquipmentSchema)
async def update_equipment(eq_id: int, equipment: EquipmentSchema, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    if equipment.name:
        db_eq.name = equipment.name
    if equipment.ip:
        db_eq.ip = equipment.ip
    # We can handle tower_id being None (unlinked) if needed, but for now assuming valid tower_id or null
    db_eq.tower_id = equipment.tower_id
    
    await db.commit()
    await db.refresh(db_eq)
    return db_eq

@router.delete("/{eq_id}")
async def delete_equipment(eq_id: int, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await db.delete(db_eq)
    await db.commit()
    await db.delete(db_eq)
    await db.commit()
    return {"message": "Equipment deleted"}

from backend.app.services.ssh_commander import reboot_device

@router.post("/{eq_id}/reboot")
async def reboot_equipment(eq_id: int, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    if not db_eq.ip:
        raise HTTPException(status_code=400, detail="Equipamento sem IP configurado")

    # Use stored credentials or defaults
    user = db_eq.ssh_user or "admin"
    password = db_eq.ssh_password
    port = db_eq.ssh_port or 22
    
    if not password:
         raise HTTPException(status_code=400, detail="Senha SSH não configurada para este equipamento")

    success, msg = await reboot_device(db_eq.ip, user, password, port)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Falha no comando de reboot: {msg}")
        
    return {"message": "Comando de reboot enviado com sucesso"}

from pydantic import BaseModel
class ScanRequest(BaseModel):
    ip_range: str # e.g. "192.168.1.1-192.168.1.50"

import ipaddress
from fastapi.responses import StreamingResponse
import json
from backend.app.services.pinger import scan_range_generator

@router.get("/scan/stream/")
async def scan_network_stream(ip_range: str):
    try:
        ips_to_scan = []
        
        # Parse Logic (Duplicated for now, could be refactored)
        if '/' in ip_range:
            net = ipaddress.ip_network(ip_range, strict=False)
            ips_to_scan = [str(ip) for ip in net.hosts()]
        elif '-' in ip_range:
            start_ip, end_ip = ip_range.split('-')
            start = ipaddress.IPv4Address(start_ip.strip())
            end = ipaddress.IPv4Address(end_ip.strip())
            while start <= end:
                ips_to_scan.append(str(start))
                start += 1
        else:
            try:
                ip_str = ip_range.strip()
                net = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                ips_to_scan = [str(ip) for ip in net.hosts()]
            except ValueError:
                 raise HTTPException(status_code=400, detail="IP Inválido")

        async def event_generator():
            async for result in scan_range_generator(ips_to_scan):
                yield f"data: {json.dumps(result)}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        print(f"Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from backend.app.models import PingLog
from datetime import datetime, timedelta, timezone

@router.get("/{eq_id}/latency-history")
async def get_latency_history(eq_id: int, period: str = "24h", db: AsyncSession = Depends(get_db)):
    # Determine lookback
    now = datetime.now(timezone.utc)
    if period == "7d":
        start_time = now - timedelta(days=7)
    else: # default 24h
        start_time = now - timedelta(hours=24)
        
    query = select(PingLog).where(
        PingLog.device_type == "Equipamento",
        PingLog.device_id == eq_id,
        PingLog.timestamp >= start_time
    ).order_by(PingLog.timestamp.asc())
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Return simplified list
    # frontend will handle visualization
    data = []
    for log in logs:
        # Only include logs with latency
        if log.latency_ms is not None:
             data.append({
                 "timestamp": log.timestamp.isoformat(),
                 "latency": log.latency_ms
             })
             
    return data


from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import io
import csv
import json
import ipaddress
from datetime import datetime, timedelta, timezone

from backend.app.database import get_db
from backend.app.models import Equipment, PingLog, TrafficLog, LatencyHistory
from backend.app.schemas import Equipment as EquipmentSchema, EquipmentCreate, EquipmentUpdate
from backend.app.services.cache import cache
from backend.app.services.ssh_commander import reboot_device
from backend.app.services.pinger_fast import scan_network
from backend.app.services.wireless_snmp import detect_brand, detect_equipment_type, detect_equipment_name
from pydantic import BaseModel

router = APIRouter(prefix="/equipments", tags=["equipments"])

# --- Models Helpers ---
class ScanRequest(BaseModel):
    ip_range: str

# --- Endpoints ---

@router.get("/", response_model=List[EquipmentSchema])
async def read_equipments(
    skip: int = 0, 
    limit: int = 100, 
    tower_id: Optional[int] = None,
    is_online: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    # Performance: Otimização de Cache + Eager Loading
    
    # Cache Key inclui filtros para consistência
    cache_key = f"eq_list_{skip}_{limit}_{tower_id}_{is_online}"
    
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Query Otimizada com Eager Loading (Resolve N+1)
    query = select(Equipment).options(
        selectinload(Equipment.tower),
        selectinload(Equipment.parent)
    )
    
    # Filtros
    if tower_id is not None:
        query = query.where(Equipment.tower_id == tower_id)
    if is_online is not None:
        query = query.where(Equipment.is_online == is_online)
        
    query = query.offset(skip).limit(limit).order_by(Equipment.id)
    
    result = await db.execute(query)
    equipments = result.scalars().all()
    
    # Cache valido por 10s
    await cache.set(cache_key, equipments, ttl_seconds=10)
    
    return equipments

@router.post("/", response_model=EquipmentSchema)
async def create_equipment(equipment: EquipmentCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(select(Equipment).where(Equipment.ip == equipment.ip))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"IP {equipment.ip} já está cadastrado")
        
        db_eq = Equipment(**equipment.model_dump())
        db.add(db_eq)
        await db.commit()
        await db.refresh(db_eq)
        
        # Invalida cache abrangente
        await cache.clear() 
        
        return db_eq
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg:
            raise HTTPException(status_code=400, detail=f"IP {equipment.ip} já existe")
        raise HTTPException(status_code=500, detail=f"Erro ao criar: {error_msg}")

class DetectBrandRequest(BaseModel):
    ip: str
    snmp_community: str = "public"
    snmp_port: int = 161

@router.post("/detect-brand")
async def detect_equipment_brand(request: DetectBrandRequest):
    """
    Auto-detects equipment brand, type, and name via SNMP.
    Returns detected brand (ubiquiti, mikrotik, mimosa, intelbras, generic),
    type (station, transmitter, other), and name (from sysName)
    """
    try:
        # Detect brand first
        brand = await detect_brand(request.ip, request.snmp_community, request.snmp_port)
        
        # Then detect type based on brand
        equipment_type = await detect_equipment_type(request.ip, brand, request.snmp_community, request.snmp_port)
        
        # Detect equipment name
        name = await detect_equipment_name(request.ip, request.snmp_community, request.snmp_port)
        
        return {
            "brand": brand,
            "equipment_type": equipment_type,
            "name": name,
            "ip": request.ip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")


@router.put("/{eq_id}", response_model=EquipmentSchema)
async def update_equipment(eq_id: int, equipment: EquipmentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Equipment)
        .options(selectinload(Equipment.tower), selectinload(Equipment.parent))
        .where(Equipment.id == eq_id)
    )
    db_eq = result.scalar_one_or_none()
    
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = equipment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_eq, key, value)
    
    await db.commit()
    await db.refresh(db_eq)
    
    await cache.clear()
    return db_eq

@router.delete("/{eq_id}")
async def delete_equipment(eq_id: int, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await db.delete(db_eq)
    await db.commit()
    
    await cache.clear()
    return {"message": "Equipment deleted"}

@router.post("/{eq_id}/reboot")
async def reboot_equipment_endpoint(eq_id: int, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
        
    if not db_eq.ip:
        raise HTTPException(status_code=400, detail="Equipamento sem IP")

    user = db_eq.ssh_user or "admin"
    password = db_eq.ssh_password
    port = db_eq.ssh_port or 22
    
    if not password:
         raise HTTPException(status_code=400, detail="Senha SSH não configurada")

    success, msg = await reboot_device(db_eq.ip, user, password, port)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Falha no reboot: {msg}")
        
    return {"message": "Comando de reboot enviado com sucesso"}

@router.get("/scan/stream/")
async def scan_network_stream(
    ip_range: str,
    snmp_community: str = Query("public"),
    snmp_port: int = Query(161)
):
    try:
        ips_to_scan = []
        # Parse Logic
        if '/' in ip_range:
            net = ipaddress.ip_network(ip_range, strict=False)
            ips_to_scan = [str(ip) for ip in net.hosts()]
        elif '-' in ip_range:
            start_ip, end_ip = ip_range.split('-')
            start = ipaddress.IPv4Address(start_ip.strip())
            end = ipaddress.IPv4Address(end_ip.strip())
            curr = start
            while curr <= end:
                ips_to_scan.append(str(curr))
                curr += 1
        else:
            try:
                ip_str = ip_range.strip()
                net = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                ips_to_scan = [str(ip) for ip in net.hosts()]
            except ValueError:
                 raise HTTPException(status_code=400, detail="IP Inválido")

        async def event_generator():
            async for result in scan_network(ips_to_scan):
                # Auto-Detect Brand & Type if Online
                if result.get("is_online"):
                    try:
                        # Use a shorter timeout for scan detection if possible, or just standard
                        brand = await detect_brand(result['ip'], snmp_community, snmp_port)
                        eq_type = await detect_equipment_type(result['ip'], brand, snmp_community, snmp_port)
                        
                        result['brand'] = brand
                        result['equipment_type'] = eq_type
                    except Exception as e:
                        # Non-critical, just log
                        print(f"Scan detection error for {result['ip']}: {e}")
                
                yield f"data: {json.dumps(result)}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        print(f"Scan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{eq_id}/latency-history")
async def get_latency_history(
    eq_id: int, 
    hours: int = 2,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    if hours < 1 or hours > 168:
        raise HTTPException(status_code=400, detail="hours deve estar entre 1 e 168")
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit deve estar entre 1 e 5000")
    
    # Calculate start time as timestamp
    now_ts = datetime.now(timezone.utc).timestamp()
    start_ts = now_ts - (hours * 3600)
    
    query = select(LatencyHistory).where(
        LatencyHistory.equipment_id == eq_id,
        LatencyHistory.timestamp >= start_ts
    ).order_by(LatencyHistory.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    data = []
    for log in reversed(logs):
        # Convert float timestamp back to ISO string for frontend
        dt_object = datetime.fromtimestamp(log.timestamp, timezone.utc)
        data.append({
            "timestamp": dt_object.isoformat(),
            "latency": log.latency,
            "packet_loss": log.packet_loss
        })
    
    return {
        "data": data,
        "count": len(data),
        "hours": hours,
        "limit": limit,
        "truncated": len(data) == limit
    }

@router.get("/{eq_id}/traffic-history")
async def get_traffic_history(
    eq_id: int,
    hours: int = 2,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    if hours < 1 or hours > 168:
        raise HTTPException(status_code=400, detail="hours 1-168")
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit 1-5000")
    
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = now - timedelta(hours=hours)
    
    query = select(TrafficLog).where(
        TrafficLog.equipment_id == eq_id,
        TrafficLog.timestamp >= start_time
    ).order_by(TrafficLog.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    data = []
    for log in reversed(logs):
        data.append({
            "timestamp": log.timestamp.isoformat(),
            "in": log.in_mbps,
            "out": log.out_mbps
        })
    
    return {
        "data": data,
        "count": len(data),
        "hours": hours,
        "limit": limit,
        "truncated": len(data) == limit
    }

# --- CSV Import/Export ---
@router.get("/export/csv")
async def export_equipments_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Equipment))
    equipments = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'name', 'ip', 'tower_id', 'parent_id', 'brand', 'equipment_type',
        'ssh_user', 'ssh_port', 'snmp_community', 'snmp_version', 'snmp_port',
        'snmp_interface_index', 'is_mikrotik', 'mikrotik_interface', 'api_port'
    ])
    
    for eq in equipments:
        writer.writerow([
            eq.name, eq.ip, eq.tower_id or '', eq.parent_id or '', eq.brand or 'generic',
            eq.equipment_type or 'station', eq.ssh_user or 'admin', eq.ssh_port or 22,
            eq.snmp_community or 'public', eq.snmp_version or 1, eq.snmp_port or 161,
            eq.snmp_interface_index or 1, eq.is_mikrotik or False,
            eq.mikrotik_interface or '', eq.api_port or 8728
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=equipments_export.csv"}
    )

@router.post("/import/csv")
async def import_equipments_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    results = {'success': [], 'failed': [], 'skipped': []}
    
    to_add = [] # Bulk optimization candidate, but sticking to logic to validate uniqueness first
    
    for row in reader:
        try:
            if not row.get('ip'):
                results['failed'].append({'row': row, 'reason': 'IP obrigatório'})
                continue
            
            # TODO: Otimizar verificacao de duplicatas (ex: carregar todos IPs em memoria)
            # Por agora, mantem logica segura
            existing = await db.execute(select(Equipment).where(Equipment.ip == row['ip']))
            if existing.scalar_one_or_none():
                results['skipped'].append({'ip': row['ip'], 'reason': 'IP já existe'})
                continue
            
            eq_data = {
                'name': row.get('name') or f"Dispositivo {row['ip']}",
                'ip': row['ip'],
                'tower_id': int(row['tower_id']) if row.get('tower_id') and row['tower_id'].strip() else None,
                'parent_id': int(row['parent_id']) if row.get('parent_id') and row['parent_id'].strip() else None,
                'brand': row.get('brand') or 'generic',
                'equipment_type': row.get('equipment_type') or 'station',
                'ssh_user': row.get('ssh_user') or 'admin',
                'ssh_port': int(row.get('ssh_port', 22)),
                'snmp_community': row.get('snmp_community') or 'public',
                'snmp_version': int(row.get('snmp_version', 1)),
                'snmp_port': int(row.get('snmp_port', 161)),
                'snmp_interface_index': int(row.get('snmp_interface_index', 1)),
                'is_mikrotik': row.get('is_mikrotik', '').lower() in ['true', '1', 'yes'],
                'mikrotik_interface': row.get('mikrotik_interface') or '',
                'api_port': int(row.get('api_port', 8728))
            }
            
            db_eq = Equipment(**eq_data)
            db.add(db_eq)
            results['success'].append(row['ip'])
            
        except Exception as e:
            results['failed'].append({'row': row, 'reason': str(e)})
    
    if results['success']:
        await db.commit()
        await cache.clear()
    
    return {
        'imported': len(results['success']),
        'skipped': len(results['skipped']),
        'failed': len(results['failed']),
        'details': results
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app.database import get_db
from backend.app.models import Equipment
from backend.app.schemas import Equipment as EquipmentSchema, EquipmentCreate
from backend.app.services.cache import cache  # Cache para performance

router = APIRouter(prefix="/equipments", tags=["equipments"])

@router.get("/", response_model=List[EquipmentSchema])
async def read_equipments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Tenta buscar do cache
    cache_key = f"equipments_list_{skip}_{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Se não está no cache, busca do banco
    result = await db.execute(select(Equipment).offset(skip).limit(limit))
    equipments = result.scalars().all()
    
    # Salva no cache por 30 segundos
    await cache.set(cache_key, equipments, ttl_seconds=30)
    
    return equipments

@router.post("/", response_model=EquipmentSchema)
async def create_equipment(equipment: EquipmentCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if IP already exists
        existing = await db.execute(select(Equipment).where(Equipment.ip == equipment.ip))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"IP {equipment.ip} já está cadastrado")
        
        db_eq = Equipment(**equipment.model_dump())
        db.add(db_eq)
        await db.commit()
        await db.refresh(db_eq)
        
        # Invalida o cache de equipamentos
        await cache.delete("equipments_list_0_100")
        
        return db_eq
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg or "duplicate key" in error_msg:
            raise HTTPException(status_code=400, detail=f"IP {equipment.ip} já existe no sistema")
        raise HTTPException(status_code=500, detail=f"Erro ao criar equipamento: {error_msg}")

from backend.app.schemas import EquipmentUpdate # Ensure this is imported

@router.put("/{eq_id}", response_model=EquipmentSchema)
async def update_equipment(eq_id: int, equipment: EquipmentUpdate, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = equipment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_eq, key, value)
    
    await db.commit()
    await db.refresh(db_eq)
    
    # Invalida o cache de equipamentos
    await cache.delete("equipments_list_0_100")
    
    return db_eq

@router.delete("/{eq_id}")
async def delete_equipment(eq_id: int, db: AsyncSession = Depends(get_db)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await db.delete(db_eq)
    await db.commit()
    
    # Invalida o cache de equipamentos
    await cache.delete("equipments_list_0_100")
    
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
from backend.app.services.pinger_fast import scan_range_generator

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


from backend.app.models import PingLog, TrafficLog
from datetime import datetime, timedelta, timezone

@router.get("/{eq_id}/latency-history")
async def get_latency_history(
    eq_id: int, 
    hours: int = 2,          # ✅ Padrão: últimas 2 horas
    limit: int = 1000,       # ✅ Máximo 1000 registros
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna histórico de latência com paginação obrigatória.
    
    Args:
        hours: Janela de tempo (1-168h = 1h a 7 dias)
        limit: Máximo de registros (1-5000)
    """
    # Validação
    if hours < 1 or hours > 168:  # Max 7 dias
        raise HTTPException(status_code=400, detail="hours deve estar entre 1 e 168")
    
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit deve estar entre 1 e 5000")
    
    # Calcular janela de tempo
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = now - timedelta(hours=hours)
    
    # Query com LIMIT
    query = select(PingLog).where(
        PingLog.device_type == "equipment",
        PingLog.device_id == eq_id,
        PingLog.timestamp >= start_time
    ).order_by(PingLog.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Retornar em ordem cronológica
    data = []
    for log in reversed(logs):  # Inverter para ordem crescente
        if log.latency_ms is not None:
            data.append({
                "timestamp": log.timestamp.isoformat(),
                "latency": log.latency_ms
            })
    
    return {
        "data": data,
        "count": len(data),
        "hours": hours,
        "limit": limit,
        "truncated": len(data) == limit  # True se atingiu o limite
    }

@router.get("/{eq_id}/traffic-history")
async def get_traffic_history(
    eq_id: int,
    hours: int = 2,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Retorna histórico de tráfego com paginação obrigatória."""
    # Validação
    if hours < 1 or hours > 168:
        raise HTTPException(status_code=400, detail="hours deve estar entre 1 e 168")
    
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit deve estar entre 1 e 5000")
    
    # Calcular janela
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = now - timedelta(hours=hours)
    
    # Query com LIMIT
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


# ===== CSV IMPORT/EXPORT =====
import csv
import io
from fastapi.responses import Response

@router.get("/export/csv")
async def export_equipments_csv(db: AsyncSession = Depends(get_db)):
    """Exporta todos os equipamentos para CSV"""
    result = await db.execute(select(Equipment))
    equipments = result.scalars().all()
    
    # Criar CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'name', 'ip', 'tower_id', 'parent_id', 'brand', 'equipment_type',
        'ssh_user', 'ssh_port', 'snmp_community', 'snmp_version', 'snmp_port',
        'snmp_interface_index', 'is_mikrotik', 'mikrotik_interface', 'api_port'
    ])
    
    # Data
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


from fastapi import UploadFile, File

@router.post("/import/csv")
async def import_equipments_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Importa equipamentos de um arquivo CSV"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(decoded))
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    for row in reader:
        try:
            # Validar IP obrigatório
            if not row.get('ip'):
                results['failed'].append({'row': row, 'reason': 'IP obrigatório'})
                continue
            
            # Verificar se já existe
            existing = await db.execute(select(Equipment).where(Equipment.ip == row['ip']))
            if existing.scalar_one_or_none():
                results['skipped'].append({'ip': row['ip'], 'reason': 'IP já existe'})
                continue
            
            # Criar equipamento
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
    
    # Commit all successful imports
    if results['success']:
        await db.commit()
        await cache.delete("equipments_list_0_100")
    
    return {
        'imported': len(results['success']),
        'skipped': len(results['skipped']),
        'failed': len(results['failed']),
        'details': results
    }


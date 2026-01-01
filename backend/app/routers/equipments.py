from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import io
import csv
import json
import ipaddress
import asyncio
from datetime import datetime, timedelta, timezone

from backend.app.database import get_db
from backend.app.models import Equipment, PingLog, TrafficLog, LatencyHistory
from backend.app.schemas import Equipment as EquipmentSchema, EquipmentCreate, EquipmentUpdate
from backend.app.services.cache import cache
from backend.app.services.ssh_commander import reboot_device
from backend.app.services.pinger_fast import scan_network
from backend.app.services.wireless_snmp import detect_brand, detect_equipment_type, detect_equipment_name
from pydantic import BaseModel
from fastapi import BackgroundTasks

router = APIRouter(prefix="/equipments", tags=["equipments"])

# --- Models Helpers ---
class BatchDetectRequest(BaseModel):
    equipment_ids: List[int]
    community: Optional[str] = None

# --- Security/Task State ---
batch_detection_state = {
    "is_running": False,
    "total": 0,
    "processed": 0,
    "success": 0,
    "errors": 0,
    "start_time": None
}

async def run_batch_detection_task(ids: List[int], db_session_factory, override_community: Optional[str] = None):
    global batch_detection_state
    batch_detection_state["is_running"] = True
    batch_detection_state["total"] = len(ids)
    batch_detection_state["processed"] = 0
    batch_detection_state["success"] = 0
    batch_detection_state["errors"] = 0
    batch_detection_state["start_time"] = datetime.now(timezone.utc).isoformat()

    try:
        for eq_id in ids:
            if not batch_detection_state["is_running"]:
                break
            
            async with db_session_factory() as db:
                try:
                    stmt = select(Equipment).where(Equipment.id == eq_id)
                    res = await db.execute(stmt)
                    eq = res.scalar_one_or_none()
                    
                    if not eq:
                        batch_detection_state["processed"] += 1
                        continue

                    # Auto-detect using SNMP
                    comm = override_community or eq.snmp_community or 'public'
                    brand = await detect_brand(eq.ip, comm, eq.snmp_port)
                    eq_type = await detect_equipment_type(eq.ip, brand, comm, eq.snmp_port)
                    eq_name = await detect_equipment_name(eq.ip, comm, eq.snmp_port)

                    # Update model
                    eq.brand = brand
                    eq.equipment_type = eq_type
                    if eq_name:
                        eq.name = eq_name
                    
                    # Store detected community if it was an override
                    if override_community:
                        eq.snmp_community = override_community
                    
                    # Special for Mikrotik
                    if brand == 'mikrotik':
                        eq.is_mikrotik = True
                    
                    await db.commit()
                    batch_detection_state["success"] += 1
                except Exception as e:
                    print(f"Error detecting {eq_id}: {e}")
                    batch_detection_state["errors"] += 1
                finally:
                    batch_detection_state["processed"] += 1
                    # Small delay to prevent SNMP spam
                    await asyncio.sleep(0.5)
    finally:
        batch_detection_state["is_running"] = False
        await cache.clear() # Invalidate cache after batch update

@router.post("/batch-detect")
async def start_batch_detect(
    request: BatchDetectRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Starts background SNMP detection for a list of equipment IDs"""
    global batch_detection_state
    if batch_detection_state["is_running"]:
        raise HTTPException(status_code=400, detail="Já existe uma detecção em andamento.")
    
    from backend.app.database import AsyncSessionLocal
    background_tasks.add_task(run_batch_detection_task, request.equipment_ids, AsyncSessionLocal, request.community)
    return {"message": "Detecção em lote iniciada em background."}

@router.get("/batch-detect/status")
async def get_batch_detect_status():
    """Returns the current status of the background detection task"""
    return batch_detection_state

@router.post("/batch-detect/stop")
async def stop_batch_detect():
    """Stops the current background detection task"""
    global batch_detection_state
    batch_detection_state["is_running"] = False
    return {"message": "Sinal de parada enviado para a detecção."}

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

@router.post("/batch")
async def create_equipments_batch(equipments: List[EquipmentCreate], db: AsyncSession = Depends(get_db)):
    """Bulk create equipments (used by Network Scanner) - Safely ignores existing IPs"""
    results = {"success": 0, "failed": 0, "errors": []}
    
    # 1. Load all existing IPs at once for fast lookup
    unique_check_stmt = select(Equipment.ip)
    existing_ips_res = await db.execute(unique_check_stmt)
    existing_ips = set(existing_ips_res.scalars().all())

    to_add = []
    
    for eq in equipments:
        if not eq.ip:
            results["failed"] += 1
            results["errors"].append("Missing IP")
            continue
            
        if eq.ip in existing_ips:
            results["failed"] += 1
            # We don't consider this an error anymore, just skip it "successfully"
            continue
            
        # Basic validation passed
        to_add.append(Equipment(**eq.model_dump()))
        existing_ips.add(eq.ip) # Prevent duplicates WITHIN this batch
        
    if to_add:
        try:
            db.add_all(to_add)
            await db.commit()
            results["success"] = len(to_add)
            await cache.clear()
        except Exception as e:
            await db.rollback()
            # If still fails due to race conditions, try to be specific
            raise HTTPException(status_code=500, detail=f"Erro ao salvar lote: {str(e)}")
            
    return results

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

class AutoDetectAllRequest(BaseModel):
    ip: str
    community: str = "public"
    port: int = 161

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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Iniciando detecção para IP: {request.ip}")
        # 1. Detect brand first (fastest and gives context for others)
        brand = await detect_brand(request.ip, request.snmp_community, request.snmp_port)
        logger.info(f"Marca detectada para {request.ip}: {brand}")

        # If brand is generic, the device is likely offline or has no SNMP
        # We can still try name, but it's likely to fail/timeout too.
        # Running name and type concurrently:
        
        async def get_type():
            try:
                return await detect_equipment_type(request.ip, brand, request.snmp_community, request.snmp_port)
            except Exception as e:
                logger.error(f"Erro ao detectar tipo para {request.ip}: {e}")
                return 'other'

        async def get_name():
            try:
                return await detect_equipment_name(request.ip, request.snmp_community, request.snmp_port)
            except Exception as e:
                logger.error(f"Erro ao detectar nome para {request.ip}: {e}")
                return None

        # Run type and name concurrently to save time
        equipment_type, name = await asyncio.gather(get_type(), get_name())
        
        logger.info(f"Detecção concluída para {request.ip}: {brand}, {equipment_type}, {name}")
        
        return {
            "brand": brand,
            "equipment_type": equipment_type,
            "name": name,
            "ip": request.ip
        }
    except Exception as e:
        logger.error(f"Erro fatal na detecção para {request.ip}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")

@router.get("/scan-interfaces")
async def scan_interfaces(
    ip: str = Query(...),
    community: Optional[str] = Query(None),
    port: int = Query(161),
    db: AsyncSession = Depends(get_db)
):
    from backend.app.services.snmp import get_snmp_interfaces
    from backend.app.models import Parameters
    
    final_community = community
    if not final_community:
        res = await db.execute(select(Parameters).where(Parameters.key == "default_snmp_community"))
        param = res.scalar_one_or_none()
        final_community = param.value if param else "public"

    interfaces = await get_snmp_interfaces(ip, final_community, port)
    if not interfaces:
        # Tenta fallback se falhou com a default
        if final_community != "public":
             interfaces = await get_snmp_interfaces(ip, "public", port)
             
        if not interfaces:
            raise HTTPException(status_code=404, detail=f"Não foi possível listar as interfaces via SNMP ({final_community}). Verifique o IP e a Community.")
            
    return interfaces

@router.post("/detect-traffic-interface")
async def detect_traffic_interface(
    ip: str,
    community: Optional[str] = None,
    port: int = 161,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-detecta qual interface tem tráfego real.
    Testa todas as interfaces e retorna a que tem mais tráfego.
    """
    from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic
    from backend.app.models import Parameters
    import time
    
    # Get community from settings if not provided
    final_community = community
    if not final_community:
        res = await db.execute(select(Parameters).where(Parameters.key == "default_snmp_community"))
        param = res.scalar_one_or_none()
        final_community = param.value if param else "public"
    
    try:
        # 1. Listar interfaces
        interfaces = await get_snmp_interfaces(ip, final_community, port)
        if not interfaces:
            raise HTTPException(
                status_code=404, 
                detail="Nenhuma interface encontrada via SNMP. Verifique a community e se o SNMP está habilitado."
            )
        
        # 2. Testar tráfego em cada interface (paralelo)
        async def test_interface(iface):
            idx = iface['index']
            name = iface['name']
            
            try:
                traffic1 = await get_snmp_interface_traffic(ip, final_community, port, idx)
                if not traffic1:
                    return None
                
                in_bytes1, out_bytes1 = traffic1
                time1 = time.time()
                
                await asyncio.sleep(3)  # 3 segundos
                
                traffic2 = await get_snmp_interface_traffic(ip, final_community, port, idx)
                if not traffic2:
                    return None
                
                in_bytes2, out_bytes2 = traffic2
                time2 = time.time()
                
                dt = time2 - time1
                delta_in = max(0, in_bytes2 - in_bytes1)
                delta_out = max(0, out_bytes2 - out_bytes1)
                
                mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                total_mbps = mbps_in + mbps_out
                
                if total_mbps > 0:
                    return {
                        'index': idx,
                        'name': name,
                        'in_mbps': mbps_in,
                        'out_mbps': mbps_out,
                        'total_mbps': total_mbps
                    }
                return None
                
            except Exception:
                return None
        
        # Testar com limite de concorrência
        sem = asyncio.Semaphore(10)
        
        async def test_with_semaphore(iface):
            async with sem:
                return await test_interface(iface)
        
        tasks = [test_with_semaphore(iface) for iface in interfaces]
        results = await asyncio.gather(*tasks)
        
        valid_results = [r for r in results if r is not None]
        
        if not valid_results:
            return {
                "success": False,
                "message": "Nenhuma interface com tráfego detectada no momento",
                "total_interfaces": len(interfaces),
                "suggestion": "Verifique se há tráfego real passando pelo equipamento"
            }
        
        # Ordenar por tráfego total
        valid_results.sort(key=lambda x: x['total_mbps'], reverse=True)
        best = valid_results[0]
        
        return {
            "success": True,
            "recommended_interface": best['index'],
            "interface_name": best['name'],
            "traffic_in": best['in_mbps'],
            "traffic_out": best['out_mbps'],
            "total_traffic": best['total_mbps'],
            "all_interfaces_with_traffic": valid_results,
            "total_interfaces": len(interfaces),
            "interfaces_with_traffic": len(valid_results),
            "message": f"Interface {best['index']} ({best['name']}) detectada com {best['total_mbps']} Mbps total"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")

@router.get("/scan-best-interface")
async def scan_best_interface(
    ip: str = Query(...),
    community: Optional[str] = Query(None),
    port: int = Query(161),
    db: AsyncSession = Depends(get_db)
):
    """
    Detects the interface with the highest traffic usage (Mbps) over a 3s sample.
    """
    from backend.app.services.snmp import detect_best_interface
    from backend.app.models import Parameters
    
    final_community = community
    if not final_community:
        res = await db.execute(select(Parameters).where(Parameters.key == "default_snmp_community"))
        param = res.scalar_one_or_none()
        final_community = param.value if param else "public"
    
    best = await detect_best_interface(ip, final_community, port)
    if not best:
        return {"index": None, "name": "Não detectado", "current_mbps": 0}
    return best


@router.post("/{eq_id}/auto-configure-traffic")
async def auto_configure_traffic_interface(
    eq_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-detecta e configura a interface de tráfego em um único passo.
    """
    from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic
    from backend.app.models import Parameters
    import time
    
    result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    equipment = result.scalar_one_or_none()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    if not equipment.ip:
        raise HTTPException(status_code=400, detail="Equipamento sem IP configurado")
    
    community = equipment.snmp_community
    if not community:
        res = await db.execute(select(Parameters).where(Parameters.key == "default_snmp_community"))
        param = res.scalar_one_or_none()
        community = param.value if param else "public"
    
    port = equipment.snmp_port or 161
    
    try:
        interfaces = await get_snmp_interfaces(equipment.ip, community, port)
        if not interfaces:
            raise HTTPException(status_code=404, detail="Nenhuma interface encontrada via SNMP")
        
        async def test_interface(iface):
            idx = iface['index']
            name = iface['name']
            
            try:
                traffic1 = await get_snmp_interface_traffic(equipment.ip, community, port, idx)
                if not traffic1:
                    return None
                
                in_bytes1, out_bytes1 = traffic1
                time1 = time.time()
                
                await asyncio.sleep(3)
                
                traffic2 = await get_snmp_interface_traffic(equipment.ip, community, port, idx)
                if not traffic2:
                    return None
                
                in_bytes2, out_bytes2 = traffic2
                time2 = time.time()
                
                dt = time2 - time1
                delta_in = max(0, in_bytes2 - in_bytes1)
                delta_out = max(0, out_bytes2 - out_bytes1)
                
                mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                total_mbps = mbps_in + mbps_out
                
                if total_mbps > 0:
                    return {
                        'index': idx,
                        'name': name,
                        'in_mbps': mbps_in,
                        'out_mbps': mbps_out,
                        'total_mbps': total_mbps
                    }
                return None
                
            except Exception:
                return None
        
        sem = asyncio.Semaphore(10)
        
        async def test_with_semaphore(iface):
            async with sem:
                return await test_interface(iface)
        
        tasks = [test_with_semaphore(iface) for iface in interfaces]
        results = await asyncio.gather(*tasks)
        
        valid_results = [r for r in results if r is not None]
        
        if not valid_results:
            return {
                "success": False,
                "message": "Nenhuma interface com tráfego detectada",
                "equipment_id": eq_id,
                "equipment_name": equipment.name,
                "total_interfaces": len(interfaces)
            }
        
        valid_results.sort(key=lambda x: x['total_mbps'], reverse=True)
        best = valid_results[0]
        
        equipment.snmp_traffic_interface_index = best['index']
        await db.commit()
        await db.refresh(equipment)
        
        return {
            "success": True,
            "message": f"Interface {best['index']} configurada automaticamente",
            "equipment_id": eq_id,
            "equipment_name": equipment.name,
            "equipment_ip": equipment.ip,
            "configured_interface": best['index'],
            "interface_name": best['name'],
            "traffic_in": best['in_mbps'],
            "traffic_out": best['out_mbps'],
            "total_traffic": best['total_mbps'],
            "all_interfaces_with_traffic": valid_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na auto-configuração: {str(e)}")

@router.post("/auto-detect-all")
async def auto_detect_all(
    ip: str = Body(...),
    community: str = Body("publicRadionet"),
    port: int = Body(161),
    db: AsyncSession = Depends(get_db)
):
    """
    Auto-detecta TUDO de um equipamento em um único endpoint:
    1. Marca/Tipo do equipamento
    2. Interface de sinal wireless
    3. Interface de tráfego (com mais Mbps)
    
    Retorna todos os dados para preencher o formulário automaticamente.
    """
    from backend.app.services.wireless_snmp import detect_brand, detect_equipment_type, get_wireless_stats
    from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic
    from backend.app.models import Parameters
    import time
    
    result = {
        "success": False,
        "ip": ip,
        "brand": None,
        "equipment_type": None,
        "snmp_interface_index": None,
        "snmp_traffic_interface_index": None,
        "signal_dbm": None,
        "traffic_in": None,
        "traffic_out": None,
        "errors": []
    }
    
    try:
        # STEP 1: Detectar marca e tipo
        try:
            brand = await detect_brand(ip, community, port)
            result["brand"] = brand
            
            if brand != "generic":
                eq_type = await detect_equipment_type(ip, brand, community, port)
                result["equipment_type"] = eq_type
                
                # Try to find signal interface
                stats = await get_wireless_stats(ip, brand, community, port)
                if stats.get("signal_dbm") is not None:
                    result["signal_dbm"] = stats["signal_dbm"]
                    # In some brands, we might want to store which interface gave the signal
                    # But for now, we just indicate we found signal.
        except Exception as e:
            result["errors"].append(f"Erro ao detectar marca/tipo: {str(e)}")
        
        # STEP 2: Detectar interface de tráfego
        try:
            interfaces = await get_snmp_interfaces(ip, community, port)
            if not interfaces:
                result["errors"].append("Nenhuma interface encontrada via SNMP")
            else:
                # Testar tráfego em cada interface
                async def test_interface(iface):
                    idx = iface['index']
                    try:
                        traffic1 = await get_snmp_interface_traffic(ip, community, port, idx)
                        if not traffic1:
                            return None
                        
                        in_bytes1, out_bytes1 = traffic1
                        time1 = time.time()
                        
                        await asyncio.sleep(3)
                        
                        traffic2 = await get_snmp_interface_traffic(ip, community, port, idx)
                        if not traffic2:
                            return None
                        
                        in_bytes2, out_bytes2 = traffic2
                        time2 = time.time()
                        
                        dt = time2 - time1
                        delta_in = max(0, in_bytes2 - in_bytes1)
                        delta_out = max(0, out_bytes2 - out_bytes1)
                        
                        mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                        mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                        total_mbps = mbps_in + mbps_out
                        
                        if total_mbps > 0:
                            return {
                                'index': idx,
                                'name': iface['name'],
                                'in_mbps': mbps_in,
                                'out_mbps': mbps_out,
                                'total_mbps': total_mbps
                            }
                        return None
                    except Exception:
                        return None
                
                # Testar com limite de concorrência
                sem = asyncio.Semaphore(10)
                
                async def test_with_semaphore(iface):
                    async with sem:
                        return await test_interface(iface)
                
                tasks = [test_with_semaphore(iface) for iface in interfaces]
                results = await asyncio.gather(*tasks)
                
                valid_results = [r for r in results if r is not None]
                
                if valid_results:
                    valid_results.sort(key=lambda x: x['total_mbps'], reverse=True)
                    best = valid_results[0]
                    
                    result["snmp_traffic_interface_index"] = best['index']
                    result["traffic_in"] = best['in_mbps']
                    result["traffic_out"] = best['out_mbps']
                else:
                    result["errors"].append("Nenhuma interface com tráfego detectada")
                    
        except Exception as e:
            result["errors"].append(f"Erro ao detectar interface de tráfego: {str(e)}")
        
        # Determinar sucesso
        result["success"] = (
            result["brand"] is not None or 
            result["snmp_traffic_interface_index"] is not None
        )
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Erro geral: {str(e)}")
        return result


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

@router.post("/{eq_id}/test")
async def test_equipment_connection(eq_id: int, db: AsyncSession = Depends(get_db)):
    """Teste manual de conectividade (Ping)"""
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    from icmplib import async_ping
    try:
        host = await async_ping(db_eq.ip, count=4, timeout=1, privileged=False)
        return {
            "ip": db_eq.ip,
            "is_online": host.is_alive,
            "latency": host.avg_rtt,
            "packet_loss": host.packet_loss,
            "details": f"Min: {host.min_rtt}ms, Max: {host.max_rtt}ms"
        }
    except Exception as e:
        return {"is_online": False, "error": str(e), "ip": db_eq.ip}

@router.get("/{eq_id}/wireless-status")
async def get_equipment_wireless_status(eq_id: int, db: AsyncSession = Depends(get_db)):
    """Busca sinal e CCQ em tempo real via SNMP (para o modal)"""
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    
    if not db_eq.ip or not db_eq.brand:
        return {"signal_dbm": None, "ccq": None, "connected_clients": None}
    
    from backend.app.services.wireless_snmp import get_wireless_stats, get_connected_clients_count
    
    try:
        # Busca estatísticas básicas
        stats = await get_wireless_stats(
            db_eq.ip, 
            db_eq.brand, 
            db_eq.snmp_community or 'public', 
            db_eq.snmp_port or 161
        )
        
        # Se for rádio transmissor, busca contagem de clientes também
        if db_eq.equipment_type == 'transmitter':
            clients = await get_connected_clients_count(
                db_eq.ip, 
                db_eq.brand, 
                db_eq.snmp_community or 'public', 
                db_eq.snmp_port or 161
            )
            stats['connected_clients'] = clients
        else:
            stats['connected_clients'] = None
            
        return stats
    except Exception as e:
        return {"error": str(e), "signal_dbm": None, "ccq": None}

@router.get("/scan/stream/")
async def scan_network_stream(
    ip_range: str,
    snmp_community: str = Query("public"),
    snmp_port: int = Query(161)
):
    try:
        ips_to_scan = []
        # Parse Logic - More flexible
        if '/' in ip_range:
            # Accept any IP with CIDR, e.g., 192.168.108.1/24 or 192.168.108.0/24
            try:
                net = ipaddress.ip_network(ip_range, strict=False)
                ips_to_scan = [str(ip) for ip in net.hosts()]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"CIDR inválido: {str(e)}")
        elif '-' in ip_range:
            # Range format: 192.168.1.1-192.168.1.50
            try:
                start_ip, end_ip = ip_range.split('-')
                start = ipaddress.IPv4Address(start_ip.strip())
                end = ipaddress.IPv4Address(end_ip.strip())
                curr = start
                while curr <= end:
                    ips_to_scan.append(str(curr))
                    curr += 1
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Range inválido: {str(e)}")
        else:
            # Single IP - assume /24 network
            try:
                ip_str = ip_range.strip()
                # Validate it's a valid IP first
                ipaddress.IPv4Address(ip_str)
                # Then create /24 network from it
                net = ipaddress.ip_network(f"{ip_str}/24", strict=False)
                ips_to_scan = [str(ip) for ip in net.hosts()]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"IP inválido: {str(e)}")

        async def process_result(result):
            if result.get("is_online"):
                try:
                    # Parallelize brand and type detection
                    brand = await detect_brand(result['ip'], snmp_community, snmp_port)
                    eq_type = await detect_equipment_type(result['ip'], brand, snmp_community, snmp_port)
                    result['brand'] = brand
                    result['equipment_type'] = eq_type
                except Exception as e:
                    print(f"Scan detection error for {result['ip']}: {e}")
            return result

        async def event_generator():
            # Process in small worker chunks to maintain speed and concurrency
            sem = asyncio.Semaphore(20) # Limit concurrent SNMP checks

            async def wrapped_process(res):
                async with sem:
                    return await process_result(res)

            # We iterate over scan_network results
            tasks = []
            async for result in scan_network(ips_to_scan):
                # We want to yield something immediately for the ping result?
                # Actually, to be FAST, we can yield the ping result first, 
                # then yield the SNMP update later? 
                # But the current frontend might expect one object per IP.
                # Let's run SNMP in parallel and yield when done.
                tasks.append(asyncio.create_task(wrapped_process(result)))
                
                # If we have a decent amount of tasks, wait for them
                if len(tasks) >= 10:
                    done_results = await asyncio.gather(*tasks)
                    for r in done_results:
                        yield f"data: {json.dumps(r)}\n\n"
                    tasks = []
            
            # Final tasks
            if tasks:
                done_results = await asyncio.gather(*tasks)
                for r in done_results:
                    yield f"data: {json.dumps(r)}\n\n"

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

    # Buscar configuração atual da interface do equipamento
    eq_result = await db.execute(select(Equipment).where(Equipment.id == eq_id))
    eq = eq_result.scalar_one_or_none()
    
    interface_idx = 1
    if eq:
        # Prioritize dedicated traffic interface, then shared/sfp interface, then default 1
        interface_idx = eq.snmp_traffic_interface_index or eq.snmp_interface_index or 1

    query = select(TrafficLog).where(
        TrafficLog.equipment_id == eq_id,
        TrafficLog.timestamp >= start_time,
        # Filter by current interface index to avoid mixing data from different ports
        # We accept NULL for retro-compatibility if the column wasn't populated before
        (TrafficLog.interface_index == interface_idx) | (TrafficLog.interface_index == None)
    ).order_by(TrafficLog.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    data = []
    for log in reversed(logs):
        data.append({
            "timestamp": log.timestamp.isoformat(),
            "in": log.in_mbps,
            "out": log.out_mbps,
            "signal": log.signal_dbm,
            "if_idx": log.interface_index
        })
    
    return {
        "data": data,
        "count": len(data),
        "hours": hours,
        "limit": limit,
        "current_interface": interface_idx,
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

class LiveStatusRequest(BaseModel):
    ids: List[int]

@router.post("/live-status")
async def get_live_status_batch(req: LiveStatusRequest, db: AsyncSession = Depends(get_db)):
    """Busca status em tempo real (cacheado no DB) para lista de IDs. Extremamente rápido."""
    if not req.ids:
        return {}
    
    query = select(Equipment).where(Equipment.id.in_(req.ids))
    result = await db.execute(query)
    eqs = result.scalars().all()
    
    resp = {}
    for eq in eqs:
        resp[eq.id] = {
            "traffic": {"in": eq.last_traffic_in, "out": eq.last_traffic_out},
            "signal": {"dbm": eq.signal_dbm, "ccq": eq.ccq},
            "clients": eq.connected_clients,
            "latency": eq.last_latency,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    return resp

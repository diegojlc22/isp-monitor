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
from backend.app.dependencies import get_current_user
from pydantic import BaseModel
from fastapi import BackgroundTasks
from backend.app.config import logger

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
    current_user=Depends(get_current_user),
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
async def get_batch_detect_status(current_user=Depends(get_current_user)):
    """Returns the current status of the background detection task"""
    return batch_detection_state

@router.post("/batch-detect/stop")
async def stop_batch_detect(current_user=Depends(get_current_user)):
    """Stops the current background detection task"""
    global batch_detection_state
    batch_detection_state["is_running"] = False
    return {"message": "Sinal de parada enviado para a detecção."}

# --- Endpoints ---

@router.get("/", response_model=List[EquipmentSchema])
async def read_equipments(
    skip: int = 0, 
    limit: int = 10000, 
    tower_id: Optional[int] = None,
    is_online: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
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
async def create_equipments_batch(equipments: List[EquipmentCreate], db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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

class BatchDeleteRequest(BaseModel):
    ids: List[int]

@router.post("/batch/delete")
async def delete_equipments_batch(req: BatchDeleteRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Bulk delete equipments by IDs"""
    try:
        from sqlalchemy import delete
        
        # We can use a single DELETE statement for performance
        # Since we added CASCADE/SET NULL on the DB, this is safe and efficient
        stmt = delete(Equipment).where(Equipment.id.in_(req.ids))
        result = await db.execute(stmt)
        await db.commit()
        
        # Clear cache as many items changed
        await cache.clear()
        
        return {"message": f"{result.rowcount} equipments deleted", "count": result.rowcount}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir em lote: {str(e)}")


@router.post("/", response_model=EquipmentSchema)
async def create_equipment(equipment: EquipmentCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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
async def detect_equipment_brand(request: DetectBrandRequest, current_user=Depends(get_current_user)):
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
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
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
    from backend.app.services.snmp import get_snmp_interfaces, measure_interfaces_traffic
    from backend.app.services.wireless_snmp import detect_brand
    from backend.app.models import Parameters
    
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
        
        # 2. Detectar marca para estratégias específicas
        brand = await detect_brand(ip, final_community, port)
        
        # 3. Medir tráfego
        valid_results = await measure_interfaces_traffic(ip, final_community, port, interfaces, brand=brand)
        
        if not valid_results:
            return {
                "success": False,
                "message": "Nenhuma interface com tráfego detectada no momento",
                "total_interfaces": len(interfaces),
                "suggestion": "Verifique se há tráfego real passando pelo equipamento"
            }
        
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
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Auto-detecta e configura a interface de tráfego em um único passo.
    """
    from backend.app.services.snmp import get_snmp_interfaces, measure_interfaces_traffic
    from backend.app.services.wireless_snmp import detect_brand
    from backend.app.models import Parameters
    
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
        
        brand = await detect_brand(equipment.ip, community, port)
        valid_results = await measure_interfaces_traffic(equipment.ip, community, port, interfaces, brand=brand)
        
        if not valid_results:
            return {
                "success": False,
                "message": "Nenhuma interface com tráfego detectada",
                "equipment_id": eq_id,
                "equipment_name": equipment.name,
                "total_interfaces": len(interfaces)
            }
        
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
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Auto-detecta TUDO de um equipamento em um único endpoint:
    1. Marca/Tipo do equipamento
    2. Interface de sinal wireless
    3. Interface de tráfego (com mais Mbps)
    
    Retorna todos os dados para preencher o formulário automaticamente.
    """
    from backend.app.services.wireless_snmp import detect_brand, detect_equipment_type, get_wireless_stats
    from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic, detect_equipment_name
    from backend.app.models import Parameters
    import time
    
    result = {
        "success": False,
        "ip": ip,
        "name": None,
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
            
            # Detectar Nome (sysName)
            sys_name = await detect_equipment_name(ip, community, port)
            if sys_name:
                result["name"] = sys_name

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
            logger.error(f"[AUTO-DETECT] Step 1 falhou para {ip}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result["errors"].append(f"Erro ao detectar marca/tipo: {str(e)}")
        
        # STEP 2: Detectar interface de tráfego
        try:
            from backend.app.services.snmp import get_snmp_interfaces, measure_interfaces_traffic
            interfaces = await get_snmp_interfaces(ip, community, port)
            if not interfaces:
                result["errors"].append("Nenhuma interface encontrada via SNMP")
            else:
                valid_results = await measure_interfaces_traffic(ip, community, port, interfaces, brand=brand)
                
                if valid_results:
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
async def update_equipment(eq_id: int, equipment: EquipmentUpdate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Equipment)
        .options(selectinload(Equipment.tower), selectinload(Equipment.parent))
        .where(Equipment.id == eq_id)
    )
    db_eq = result.scalar_one_or_none()
    
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = equipment.model_dump(exclude_unset=True)
    
    # Pre-check IP uniqueness to avoid DB transaction error if possible, 
    # but race condition might still happen so try/except is essential.
    if 'ip' in update_data and update_data['ip'] != db_eq.ip:
        existing_check = await db.execute(select(Equipment).where(Equipment.ip == update_data['ip']))
        if existing_check.scalar_one_or_none():
             raise HTTPException(status_code=400, detail=f"O IP {update_data['ip']} já está em uso por outro equipamento.")

    for key, value in update_data.items():
        setattr(db_eq, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_eq)
    except Exception as e:
        await db.rollback()
        error_str = str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
             raise HTTPException(status_code=400, detail=f"O IP {update_data.get('ip')} já está cadastrado em outro equipamento.")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")
    
    await cache.clear()
    return db_eq

@router.delete("/{eq_id}")
async def delete_equipment(eq_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    db_eq = await db.get(Equipment, eq_id)
    if not db_eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    await db.delete(db_eq)
    await db.commit()
    
    await cache.clear()
    return {"message": "Equipment deleted"}

@router.post("/{eq_id}/reboot")
async def reboot_equipment_endpoint(eq_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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
async def test_equipment_connection(eq_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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
            "latency": round(host.avg_rtt) if host.is_alive else 0,
            "packet_loss": host.packet_loss,
            "details": f"Min: {round(host.min_rtt)}ms, Max: {round(host.max_rtt)}ms"
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
    from backend.app.database import AsyncSessionLocal
    """
    Scanner Inteligente e Rápido.
    Suporta: 
    - CIDR: 192.168.1.0/24
    - Range: 192.168.1.10-50
    - Multi: 10.0.0.1, 10.0.0.5, 192.168.0.0/24
    """
    try:
        ips_to_scan = []
        
        # Split by comma to support multiple targets
        targets = [t.strip() for t in ip_range.split(',')]
        
        for target in targets:
            if '/' in target:
                try:
                    net = ipaddress.ip_network(target, strict=False)
                    # Skip network and broadcast for common subnets
                    if net.prefixlen <= 30:
                        ips_to_scan.extend([str(ip) for ip in net.hosts()])
                    else:
                        ips_to_scan.extend([str(ip) for ip in net])
                except ValueError as e:
                    logger.warning(f"CIDR inválido ignorado: {target}")
            elif '-' in target:
                try:
                    if target.count('.') >= 4: # Format 192.168.1.1-192.168.1.10
                        start_ip, end_ip = target.split('-')
                    else: # Format 192.168.1.1-50
                        base = target.rsplit('.', 1)[0]
                        start_part, end_part = target.rsplit('.', 1)[1].split('-')
                        start_ip = f"{base}.{start_part}"
                        end_ip = f"{base}.{end_part}"
                    
                    start = ipaddress.IPv4Address(start_ip.strip())
                    end = ipaddress.IPv4Address(end_ip.strip())
                    curr = start
                    while curr <= end:
                        ips_to_scan.append(str(curr))
                        curr += 1
                except ValueError as e:
                    logger.warning(f"Range inválido ignorado: {target}")
            else:
                # Single IP or assume /24 if looks like base
                try:
                    target_clean = target.strip()
                    if target_clean.endswith('.0'):
                         net = ipaddress.ip_network(f"{target_clean}/24", strict=False)
                         ips_to_scan.extend([str(ip) for ip in net.hosts()])
                    else:
                        ipaddress.IPv4Address(target_clean)
                        ips_to_scan.append(target_clean)
                except ValueError:
                    logger.warning(f"Alvo inválido ignorado: {target}")

        # Unique IPs only and preserve some order
        ips_to_scan = list(dict.fromkeys(ips_to_scan))
        
        # Filter out Gateway IPs (ending in .1) as requested
        ips_to_scan = [ip for ip in ips_to_scan if not ip.endswith('.1')]
        
        if not ips_to_scan:
            raise HTTPException(status_code=400, detail="Nenhum IP válido encontrado para escanear.")

        # Load existing IPs for "smart" identification
        async with AsyncSessionLocal() as db:
            ex_res = await db.execute(select(Equipment.ip))
            existing_ips = {row[0] for row in ex_res.all() if row[0]}

        async def process_item(result):
            # Mark as monitored if already in DB
            result["is_monitored"] = result['ip'] in existing_ips
            
            if result.get("is_online") and not result["is_monitored"]:
                try:
                    # Brand detection with timeout to not block the stream too long
                    brand = await asyncio.wait_for(
                        detect_brand(result['ip'], snmp_community, snmp_port),
                        timeout=3.0
                    )
                    eq_type = await detect_equipment_type(result['ip'], brand, snmp_community, snmp_port)
                    result['brand'] = brand
                    result['equipment_type'] = eq_type
                except Exception:
                    result['brand'] = 'generic'
                    result['equipment_type'] = 'station'
            return result

        async def event_generator():
            sem = asyncio.Semaphore(15)
            total_ips = len(ips_to_scan)
            processed_count = 0
            pending_tasks = set()

            async def detect_worker(res):
                async with sem:
                    return await process_item(res)

            async for ping_res in scan_network(ips_to_scan):
                processed_count += 1
                
                # Check for finished tasks (non-blocking)
                if pending_tasks:
                    done, pending_tasks = await asyncio.wait(
                        pending_tasks, 
                        timeout=0, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for d in done:
                        try:
                            res = d.result()
                            res["progress"] = round((processed_count / total_ips) * 100)
                            yield f"data: {json.dumps(res)}\n\n"
                        except Exception: pass

                if ping_res.get("is_online"):
                    # Start SNMP worker in background
                    task = asyncio.create_task(detect_worker(ping_res))
                    pending_tasks.add(task)
                    
                    # If we have too many concurrent workers, wait for some to finish
                    if len(pending_tasks) >= 30:
                        done, pending_tasks = await asyncio.wait(
                            pending_tasks,
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        for d in done:
                            try:
                                res = d.result()
                                res["progress"] = round((processed_count / total_ips) * 100)
                                yield f"data: {json.dumps(res)}\n\n"
                            except Exception: pass
                else:
                    # Offline: yield every 10 IPs to keep connection alive and show progress
                    if processed_count % 10 == 0 or processed_count == total_ips:
                        ping_res["progress"] = round((processed_count / total_ips) * 100)
                        yield f"data: {json.dumps(ping_res)}\n\n"

            # Finalize remaining background tasks
            if pending_tasks:
                for completed_task in asyncio.as_completed(pending_tasks):
                    try:
                        res = await completed_task
                        res["progress"] = 100
                        yield f"data: {json.dumps(res)}\n\n"
                    except Exception: pass
            
            # Ensure 100% progress and close
            yield f"data: {json.dumps({'progress': 100, 'is_online': False})}\n\n"
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
            "latency": round(log.latency) if log.latency is not None else 0,
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
async def import_equipments_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
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
            "health": {
                "cpu_usage": eq.cpu_usage,
                "memory_usage": eq.memory_usage,
                "disk_usage": eq.disk_usage,
                "temperature": eq.temperature,
                "voltage": eq.voltage
            },
            "clients": eq.connected_clients,
            "latency": round(eq.last_latency) if eq.last_latency is not None else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    return resp

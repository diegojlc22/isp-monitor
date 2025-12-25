"""
Router para métricas internas do sistema
Fornece observabilidade e dados para decisões baseadas em métricas
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from backend.app.database import get_db
from backend.app.models import PingLog, TrafficLog, Alert, Equipment, Tower
from backend.app.services.cache import cache
from datetime import datetime, timedelta, timezone
import psutil
import os

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
)

@router.get("/system")
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    """
    Retorna métricas do sistema com cache de 5 segundos
    
    Métricas incluem:
    - CPU e RAM
    - Contadores de dispositivos
    - Performance do banco
    - Cache hit rate
    """
    # ✅ Cache de 5 segundos (métricas mudam rápido)
    cache_key = "system_metrics"
    cached = await cache.get(cache_key)
    if cached:
        cached["from_cache"] = True
        return cached
    
    # Coletar métricas
    metrics = {}
    
    # 1. Sistema Operacional
    try:
        process = psutil.Process(os.getpid())
        metrics["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "ram_percent": process.memory_percent(),
            "threads": process.num_threads()
        }
    except Exception as e:
        metrics["system"] = {"error": str(e)}
    
    # 2. Dispositivos
    try:
        towers_total = await db.execute(select(func.count(Tower.id)))
        towers_online = await db.execute(select(func.count(Tower.id)).where(Tower.is_online == True))
        
        equips_total = await db.execute(select(func.count(Equipment.id)))
        equips_online = await db.execute(select(func.count(Equipment.id)).where(Equipment.is_online == True))
        
        metrics["devices"] = {
            "towers_total": towers_total.scalar(),
            "towers_online": towers_online.scalar(),
            "equipments_total": equips_total.scalar(),
            "equipments_online": equips_online.scalar()
        }
    except Exception as e:
        metrics["devices"] = {"error": str(e)}
    
    # 3. Banco de Dados (PostgreSQL)
    try:
        # Tamanho do banco
        db_size_query = text("SELECT pg_database_size(current_database())")
        db_size_result = await db.execute(db_size_query)
        db_size_bytes = db_size_result.scalar()
        
        # Número de conexões ativas
        connections_query = text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
        connections_result = await db.execute(connections_query)
        active_connections = connections_result.scalar()
        
        metrics["database"] = {
            "size_mb": round(db_size_bytes / 1024 / 1024, 2) if db_size_bytes else 0,
            "active_connections": active_connections
        }
    except Exception as e:
        metrics["database"] = {"error": str(e)}
    
    # 4. Logs e Alertas
    try:
        # Logs das últimas 24h
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        ping_logs_24h = await db.execute(
            select(func.count(PingLog.id)).where(PingLog.timestamp >= yesterday)
        )
        
        alerts_24h = await db.execute(
            select(func.count(Alert.id)).where(Alert.timestamp >= yesterday)
        )
        
        metrics["logs"] = {
            "ping_logs_24h": ping_logs_24h.scalar(),
            "alerts_24h": alerts_24h.scalar()
        }
    except Exception as e:
        metrics["logs"] = {"error": str(e)}
    
    # 5. Cache
    metrics["cache"] = {
        "size": cache.size(),
        "enabled": True
    }
    
    # 6. Timestamp
    metrics["timestamp"] = datetime.now(timezone.utc).isoformat()
    metrics["from_cache"] = False
    
    # ✅ Salvar no cache por 5 segundos
    await cache.set(cache_key, metrics, ttl_seconds=5)
    
    return metrics

@router.get("/performance")
async def get_performance_metrics():
    """
    Retorna métricas de performance do pinger
    
    NOTA: Estas métricas serão implementadas quando o pinger
    exportar dados de performance (Sprint 2 completo)
    """
    return {
        "status": "not_implemented",
        "message": "Métricas de performance do pinger serão adicionadas em breve",
        "planned_metrics": [
            "ping_cycle_time_ms",
            "ping_avg_latency_ms",
            "concurrent_limit_current",
            "interval_current_seconds",
            "stability_cycles"
        ]
    }

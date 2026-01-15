from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from backend.app.services.cortex_ai import cortex_engine
from backend.app.dependencies import get_current_user
from loguru import logger

print("DEBUG: Loading Cortex Router...", flush=True)

router = APIRouter(prefix="/cortex", tags=["cortex"])

@router.get("/insights")
async def get_cortex_insights(request: Request, current_user=Depends(get_current_user)):
    """
    Retorna os insights gerados pela IA CORTEX.
    """
    host = request.client.host if request.client else "unknown"
    logger.info(f"[{host}] GET /cortex/insights requested")
    
    # Se nunca rodou ou rodou há mais de 2 minutos, roda agora
    should_run = False
    if not cortex_engine.last_run:
        should_run = True
    else:
        delta = datetime.now() - cortex_engine.last_run
        if delta.total_seconds() > 120: # Cache de 2 min
            should_run = True
            
    if should_run and not cortex_engine.is_running:
        logger.info("[CORTEX] Triggering Analysis (On-Demand)")
        await cortex_engine.run_analysis()
        
    return {
        "enabled": cortex_engine.config["enabled"],
        "last_run": cortex_engine.last_run,
        "insights": cortex_engine.insights
    }

@router.post("/config")
async def configure_cortex(enabled: bool, current_user=Depends(get_current_user)):
    """
    Ativa ou Desativa o CORTEX.
    """
    logger.info(f"[CORTEX] Config Changed: Enabled={enabled}")
    result = await cortex_engine.toggle_cortex(enabled)
    return result

@router.post("/force-run")
async def force_run_analysis(current_user=Depends(get_current_user)):
    """
    Força uma nova análise imediata.
    """
    logger.info("[CORTEX] Manual Force Run Initiated")
    insights = await cortex_engine.run_analysis()
    return {"status": "completed", "insights_count": len(insights)}

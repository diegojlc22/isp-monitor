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

@router.post("/teach/{equipment_id}")
async def teach_cortex_pattern(
    equipment_id: int, 
    parameter: str, 
    value: str, # Recebemos como string e tentamos converter
    current_user=Depends(get_current_user)
):
    """
    Ensina o Cortex a aceitar um parâmetro (ex: accepted_rssi) para um rádio específico.
    """
    logger.info(f"[CORTEX] Human Feedback for ID {equipment_id}: {parameter}={value}")
    
    # Tentativa de conversão inteligente
    try:
        processed_value = float(value) if '.' in value or value.startswith('-') else int(value)
    except:
        processed_value = value
        
    result = await cortex_engine.teach_cortex(equipment_id, parameter, processed_value)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/signal-settings")
async def get_signal_settings(current_user=Depends(get_current_user)):
    """Retorna o threshold global de sinal."""
    await cortex_engine.get_config()
    return {"threshold": cortex_engine.config["thresholds"]["default_bad_rssi"]}

@router.post("/signal-settings")
async def update_signal_settings(threshold: int, current_user=Depends(get_current_user)):
    """Atualiza o threshold global de sinal."""
    return await cortex_engine.update_signal_settings(threshold)

@router.get("/signal-pending")
async def get_pending_signals(current_user=Depends(get_current_user)):
    """Lista equipamentos com sinal pior que o threshold que precisam de confirmação."""
    await cortex_engine.get_config()
    return await cortex_engine.get_pending_signals()

@router.post("/signal-confirm/{equipment_id}")
async def confirm_signal(equipment_id: int, normal: bool, current_user=Depends(get_current_user)):
    """
    Confirma se o sinal atual é normal para o equipamento.
    Se normal=True, o Cortex aprende esse sinal como o novo normal.
    Se normal=False, o Cortex mantém o alerta.
    """
    if not normal:
        return {"status": "ignored", "message": "O alerta será mantido para análise humana."}
    
    # Pegar o sinal atual do equipamento para aprender
    from backend.app.database import AsyncSessionLocal
    from backend.app.models import Equipment
    async with AsyncSessionLocal() as session:
        eq = await session.get(Equipment, equipment_id)
        if not eq or eq.signal_dbm is None:
            raise HTTPException(status_code=404, detail="Equipamento ou sinal não encontrado")
        
        current_signal = eq.signal_dbm
        
    return await cortex_engine.teach_cortex(equipment_id, 'accepted_rssi', current_signal)

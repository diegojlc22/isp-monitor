
from fastapi import APIRouter
from backend.app.services.ngrok_manager import NgrokManager

router = APIRouter(prefix="/ngrok", tags=["ngrok"])

manager = NgrokManager()

@router.get("/status")
def get_status():
    """
    Retorna o status do túnel Ngrok.
    """
    return manager.get_status()

@router.post("/start")
def start_ngrok():
    """
    Inicia o túnel Ngrok na porta 8080.
    """
    return manager.start()

@router.post("/stop")
def stop_ngrok():
    """
    Para o túnel Ngrok.
    """
    return manager.stop()

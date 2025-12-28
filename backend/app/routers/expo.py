
from fastapi import APIRouter, Depends
from backend.app.services.expo_manager import ExpoManager
from typing import Dict

router = APIRouter(prefix="/expo", tags=["expo"])

manager = ExpoManager()

@router.get("/status")
def get_status():
    """
    Retorna o status do servidor Expo (Mobile), incluindo QR Code e Logs recentes.
    """
    return manager.get_status()

@router.post("/start")
def start_expo():
    """
    Inicia o servidor Expo.
    """
    return manager.start()

@router.post("/stop")
def stop_expo():
    """
    Para o servidor Expo.
    """
    return manager.stop()

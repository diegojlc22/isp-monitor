import asyncio
import os
import httpx
from dotenv import load_dotenv
from loguru import logger
from backend.app.config import settings

# Configurações globais (fallback)
WHATSAPP_API_URL = settings.whatsapp_api_url
WHATSAPP_NUMBER = settings.whatsapp_target_number

# Global HTTP Client (Lazy loaded)
_client: httpx.AsyncClient = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    return _client

async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None

async def send_notification(
    message: str, 
    telegram_token: str = None, 
    telegram_chat_id: str = None,
    telegram_enabled: bool = True,
    whatsapp_enabled: bool = False,
    whatsapp_target: str = None,
    whatsapp_target_group: str = None
):
    """
    Envia notificação baseada na configuração passada.
    Otimizado para usar HTTPX e reutilizar conexões.
    """
    tasks = []
    
    # 1. Telegram
    token = telegram_token or settings.telegram_token
    chat_id = telegram_chat_id or settings.telegram_chat_id
        
    if telegram_enabled and token and chat_id:
        tasks.append(send_telegram(message, token, chat_id))

    # 2. WhatsApp
    target_1 = whatsapp_target or WHATSAPP_NUMBER
    target_2 = whatsapp_target_group
    
    if whatsapp_enabled:
        # Prioritize group if available (or logic as preferred) - logic kept from original
        if target_2:
             tasks.append(send_whatsapp(message, target_2))
        elif target_1:
            tasks.append(send_whatsapp(message, target_1))
        
    # Execute Async
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def _post_with_retry(url: str, json_data: dict, retries: int = 3):
    client = get_client()
    for attempt in range(retries):
        try:
            response = await client.post(url, json=json_data)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            if attempt == retries - 1:
                raise e
            # Exponential backoff: 1s, 2s, 4s
            await asyncio.sleep(2 ** attempt)

async def send_telegram(message: str, token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        logger.info(f"Enviando Telegram para {chat_id}: {message[:50]}...")
        await _post_with_retry(url, payload)
        logger.info(f"Telegram enviado com sucesso para {chat_id}")
    except Exception as e:
        logger.error(f"Falha ao enviar Telegram para {chat_id}: {e}")

async def send_whatsapp(message: str, target: str):
    payload = {
        "number": target,
        "message": message
    }
    try:
        logger.info(f"Enviando WhatsApp para {target}: {message[:50]}...")
        await _post_with_retry(WHATSAPP_API_URL, payload)
        logger.info(f"WhatsApp enviado com sucesso para {target}")
    except Exception as e:
        logger.error(f"Falha ao enviar WhatsApp para {target}: {e}")

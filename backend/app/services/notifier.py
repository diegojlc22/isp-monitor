import os
import aiohttp
import logging
from dotenv import load_dotenv

# Carregar variaveis do ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

# Configurações
ALERT_TYPE = os.getenv("ALERT_TYPE", "telegram").lower() # telegram, whatsapp, both
TELEGRAM_TOKEN_ENV = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID_ENV = os.getenv("TELEGRAM_CHAT_ID")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:3000/send")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_TARGET_NUMBER", "") # Numero do admin

async def send_notification(message: str, telegram_token: str = None, telegram_chat_id: str = None):
    """
    Envia notificação baseada na configuração ALERT_TYPE.
    Aceita credenciais do Telegram dinamicamente (do banco de dados) ou usa do .env.
    """
    tasks = []
    
    # 1. Telegram
    if ALERT_TYPE in ["telegram", "both"]:
        token = telegram_token or TELEGRAM_TOKEN_ENV
        chat_id = telegram_chat_id or TELEGRAM_CHAT_ID_ENV
        
        if token and chat_id:
            await send_telegram(message, token, chat_id)
        else:
            logger.warning("Telegram ativado mas credenciais não fornecidas (nem DB nem ENV).")

    # 2. WhatsApp
    if ALERT_TYPE in ["whatsapp", "both"]:
        if WHATSAPP_NUMBER:
            await send_whatsapp(message)
        else:
            logger.warning("WhatsApp ativado mas número de destino (WHATSAPP_TARGET_NUMBER) não configurado.")

async def send_telegram(message: str, token: str, chat_id: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Erro Telegram: {await resp.text()}")
    except Exception as e:
        logger.error(f"Falha ao enviar Telegram: {e}")

async def send_whatsapp(message: str):
    payload = {
        "number": WHATSAPP_NUMBER,
        "message": message
    }
    try:
        async with aiohttp.ClientSession() as session:
            # Timeout curto pois é localhost
            async with session.post(WHATSAPP_API_URL, json=payload, timeout=5) as resp:
                if resp.status != 200:
                    logger.error(f"Erro WhatsApp: {await resp.text()}")
    except Exception as e:
        logger.error(f"Falha ao enviar WhatsApp (O servidor do Zap está rodando?): {e}")

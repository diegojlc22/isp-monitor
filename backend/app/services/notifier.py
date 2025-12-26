import asyncio
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
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:3001/send")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_TARGET_NUMBER", "") # Numero do admin

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
    """
    tasks = []
    
    # 1. Telegram
    # Verifica se esta habilitado explicitamente OU se ALERT_TYPE diz "telegram" (fallback legado)
    legacy_alert_type = ALERT_TYPE
    should_send_tg = telegram_enabled
    
    # Se params forem None/Default, tenta fallback para ENV
    token = telegram_token or TELEGRAM_TOKEN_ENV
    chat_id = telegram_chat_id or TELEGRAM_CHAT_ID_ENV
        
    if should_send_tg and token and chat_id:
        tasks.append(send_telegram(message, token, chat_id))

    # 2. WhatsApp
    should_send_wa = whatsapp_enabled
    target_1 = whatsapp_target or WHATSAPP_NUMBER
    target_2 = whatsapp_target_group
    
    if should_send_wa:
        print(f"[DEBUG NOTIFIER] WA Enabled. Target1(Num)={target_1}, Target2(Group)={target_2}")
        if target_2:
             print(f"[DEBUG NOTIFIER] -> Enviando para GRUPO: {target_2}")
             tasks.append(send_whatsapp(message, target_2))
        elif target_1:
            print(f"[DEBUG NOTIFIER] -> Enviando para INDIVIDUAL: {target_1}")
            tasks.append(send_whatsapp(message, target_1))
        
    # Execute Async
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

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

async def send_whatsapp(message: str, target: str):
    # Remove sufixo se tiver duplicado ou garante formato correto se necessario
    # Se o target contiver @g.us ou @c.us, o server.js ja lida
    payload = {
        "number": target,
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

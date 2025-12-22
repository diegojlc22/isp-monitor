import httpx

async def send_telegram_alert(token: str, chat_id: str, message: str):
    if not token or not chat_id:
        print("⚠️ Telegram alert skipped: Missing token or chat_id")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                print(f"❌ Failed to send Telegram message (Status {response.status_code}): {response.text}")
            else:
                print(f"✅ Telegram message sent to {chat_id}")
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")

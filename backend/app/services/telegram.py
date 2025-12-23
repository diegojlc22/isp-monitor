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

async def send_telegram_document(token: str, chat_id: str, file_path: str, caption: str = None):
    """
    Send a file (document) to Telegram.
    Used for Automated Backups.
    """
    if not token or not chat_id:
        print("⚠️ Telegram upload skipped: Missing token or chat_id")
        return

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    try:
        import os
        filename = os.path.basename(file_path)
        
        async with httpx.AsyncClient() as client:
            # Open file in binary mode
            with open(file_path, "rb") as f:
                # httpx handles multipart/form-data for files
                files = {'document': (filename, f)}
                data = {'chat_id': chat_id}
                if caption:
                    data['caption'] = caption
                
                response = await client.post(url, data=data, files=files, timeout=60.0)
                
                if response.status_code != 200:
                    print(f"❌ Failed to send Telegram document (Status {response.status_code}): {response.text}")
                else:
                    print(f"✅ Backup sent to Telegram: {filename}")
                    
    except Exception as e:
        print(f"❌ Error sending Telegram document: {e}")

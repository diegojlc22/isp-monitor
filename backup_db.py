
import os
import datetime
import subprocess
import requests
from dotenv import load_dotenv

# Load config
load_dotenv()

import os
import datetime
import subprocess
import requests
import psycopg2
from dotenv import load_dotenv

# Load config
load_dotenv()

DATABASE_NAME = os.getenv("POSTGRES_DB", "isp_monitor")
DATABASE_URL = os.getenv("DATABASE_URL")
BACKUP_DIR = "backups"

def get_telegram_config_from_db():
    """Fetch Telegram config from Parameters table in DB"""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    # Try fetching from DB if not in Env
    if not token or not chat_id:
        try:
            # Parse DB connection details from env or defaults
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_pass = os.getenv("POSTGRES_PASSWORD", "110812")
            db_host = "localhost"
            
            conn = psycopg2.connect(
                dbname=DATABASE_NAME, 
                user=db_user, 
                password=db_pass, 
                host=db_host
            )
            cur = conn.cursor()
            
            cur.execute("SELECT key, value FROM parameters WHERE key IN ('telegram_token', 'telegram_chat_id', 'telegram_backup_chat_id')")
            rows = cur.fetchall()
            
            params = {row[0]: row[1] for row in rows}
            
            if not token:
                token = params.get('telegram_token')
            
            if not chat_id:
                # Prefer explicit backup channel, fall back to default
                chat_id = params.get('telegram_backup_chat_id') or params.get('telegram_chat_id')
                
            cur.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to fetch config from DB: {e}")
            
    return token, chat_id

def send_telegram_alert(message):
    token, chat_id = get_telegram_config_from_db()
    
    if not token or not chat_id:
        print("⚠️ Telegram not configured (Check DB or .env). Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram notification sent.")
        else:
            print(f"⚠️ Failed to send Telegram: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_pretty = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{DATABASE_NAME}_{timestamp}.sql")
    
    # Using pg_dump
    # Note: Requires pg_dump in PATH or specify full path
    command = f"pg_dump -U postgres -h localhost {DATABASE_NAME} > {backup_file}"
    
    # Set PGPASSWORD environment variable just for this command
    env = os.environ.copy()
    env["PGPASSWORD"] = os.getenv("POSTGRES_PASSWORD", "110812")
    
    try:
        # Use shell=True for redirection to work easily
        subprocess.run(command, shell=True, env=env, check=True)
        
        # Check size
        size_bytes = os.path.getsize(backup_file)
        size_mb = size_bytes / (1024 * 1024)
        
        print(f"✅ Backup created: {backup_file} ({size_mb:.2f} MB)")
        
        # Notify
        msg = (
            f"💾 <b>Backup Realizado!</b>\n\n"
            f"<b>Banco:</b> {DATABASE_NAME}\n"
            f"<b>Data:</b> {timestamp_pretty}\n"
            f"<b>Arquivo:</b> {os.path.basename(backup_file)}\n"
            f"<b>Tamanho:</b> {size_mb:.2f} MB\n\n"
            f"✅ <i>Salvo com sucesso no servidor.</i>"
        )
        send_telegram_alert(msg)
        
    except subprocess.CalledProcessError as e:
        err_msg = f"❌ <b>Falha no Backup!</b>\n\nErro ao executar pg_dump.\n{e}"
        print(f"❌ Backup failed: {e}")
        send_telegram_alert(err_msg)
    except Exception as e:
        err_msg = f"❌ <b>Erro Crítico no Backup!</b>\n\n{e}"
        print(f"❌ Error: {e}")
        send_telegram_alert(err_msg)

if __name__ == "__main__":
    backup_database()

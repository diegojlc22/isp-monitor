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
MSG_SECRET = os.getenv("MSG_SECRET", "isp-monitor-secret-key-v2")

def get_notification_config_from_db():
    """Fetch notification config from Parameters table in DB"""
    config = {
        'telegram_token': os.getenv("TELEGRAM_TOKEN"),
        'telegram_chat_id': os.getenv("TELEGRAM_CHAT_ID"),
        'telegram_backup_chat_id': None,
        'whatsapp_target': None,
        'whatsapp_target_group': None,
        'notify_backups': True,
        'telegram_enabled': True,
        'whatsapp_enabled': False
    }
    
    # Try fetching from DB if not in Env
    try:
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
        
        cur.execute("""
            SELECT key, value FROM parameters 
            WHERE key IN (
                'telegram_token', 'telegram_chat_id', 'telegram_backup_chat_id',
                'whatsapp_target', 'whatsapp_target_group',
                'notify_backups', 'telegram_enabled', 'whatsapp_enabled'
            )
        """)
        rows = cur.fetchall()
        
        params = {row[0]: row[1] for row in rows}
        
        # Update config with DB values
        if not config['telegram_token']:
            config['telegram_token'] = params.get('telegram_token')
        
        if not config['telegram_chat_id']:
            # Prefer explicit backup channel, fall back to default
            config['telegram_chat_id'] = params.get('telegram_backup_chat_id') or params.get('telegram_chat_id')
        
        config['whatsapp_target'] = params.get('whatsapp_target')
        config['whatsapp_target_group'] = params.get('whatsapp_target_group')
        config['notify_backups'] = params.get('notify_backups', 'true') != 'false'
        config['telegram_enabled'] = params.get('telegram_enabled', 'true') != 'false'
        config['whatsapp_enabled'] = params.get('whatsapp_enabled', 'false') == 'true'
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to fetch config from DB: {e}")
        
    return config

def send_telegram_alert(message, config):
    if not config['telegram_enabled'] or not config['notify_backups']:
        print("⚠️ Telegram notifications disabled. Skipping.")
        return
        
    token = config['telegram_token']
    chat_id = config['telegram_chat_id']
    
    if not token or not chat_id:
        print("⚠️ Telegram not configured. Skipping notification.")
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

def send_whatsapp_alert(message, config):
    if not config['whatsapp_enabled'] or not config['notify_backups']:
        print("⚠️ WhatsApp notifications disabled. Skipping.")
        return
    
    # Determine target (prefer group over individual)
    target = config['whatsapp_target_group'] or config['whatsapp_target']
    
    if not target:
        print("⚠️ WhatsApp target not configured. Skipping notification.")
        return
    
    url = "http://127.0.0.1:3001/send"
    headers = {"x-api-key": MSG_SECRET}
    payload = {
        "number": target,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✅ WhatsApp notification sent to {target}")
        else:
            print(f"⚠️ Failed to send WhatsApp: {response.text}")
    except Exception as e:
        print(f"⚠️ WhatsApp Error: {e}")

def find_pg_dump():
    """Try to find pg_dump executable"""
    # Try common paths
    common_paths = [
        r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Try to find in PATH
    import shutil
    pg_dump_path = shutil.which("pg_dump")
    if pg_dump_path:
        return pg_dump_path
    
    # Last resort: try to find recursively (slow)
    try:
        import glob
        results = glob.glob(r"C:\Program Files\PostgreSQL\**\pg_dump.exe", recursive=True)
        if results:
            return results[0]
    except:
        pass
    
    return None

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Find pg_dump
    pg_dump = find_pg_dump()
    if not pg_dump:
        error_msg = "❌ pg_dump não encontrado! Instale o PostgreSQL ou adicione ao PATH."
        print(error_msg)
        
        config = get_notification_config_from_db()
        send_telegram_alert(f"❌ <b>Erro no Backup!</b>\n\n{error_msg}", config)
        send_whatsapp_alert(f"❌ *Erro no Backup!*\n\n{error_msg}", config)
        return
    
    print(f"✅ Using pg_dump: {pg_dump}")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_pretty = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{DATABASE_NAME}_{timestamp}.sql")
    
    # Using pg_dump with full path
    command = f'"{pg_dump}" -U postgres -h localhost {DATABASE_NAME} > "{backup_file}"'
    
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
        
        # Get notification config
        config = get_notification_config_from_db()
        
        # Telegram message (HTML)
        telegram_msg = (
            f"💾 <b>Backup Realizado!</b>\n\n"
            f"<b>Banco:</b> {DATABASE_NAME}\n"
            f"<b>Data:</b> {timestamp_pretty}\n"
            f"<b>Arquivo:</b> {os.path.basename(backup_file)}\n"
            f"<b>Tamanho:</b> {size_mb:.2f} MB\n\n"
            f"✅ <i>Salvo com sucesso no servidor.</i>"
        )
        
        # WhatsApp message (Plain text, no HTML)
        whatsapp_msg = (
            f"💾 *Backup Realizado!*\n\n"
            f"*Banco:* {DATABASE_NAME}\n"
            f"*Data:* {timestamp_pretty}\n"
            f"*Arquivo:* {os.path.basename(backup_file)}\n"
            f"*Tamanho:* {size_mb:.2f} MB\n\n"
            f"✅ _Salvo com sucesso no servidor._"
        )
        
        # Send notifications
        send_telegram_alert(telegram_msg, config)
        send_whatsapp_alert(whatsapp_msg, config)
        
    except subprocess.CalledProcessError as e:
        config = get_notification_config_from_db()
        
        telegram_err = f"❌ <b>Falha no Backup!</b>\n\nErro ao executar pg_dump.\n{e}"
        whatsapp_err = f"❌ *Falha no Backup!*\n\nErro ao executar pg_dump.\n{e}"
        
        print(f"❌ Backup failed: {e}")
        send_telegram_alert(telegram_err, config)
        send_whatsapp_alert(whatsapp_err, config)
        
    except Exception as e:
        config = get_notification_config_from_db()
        
        telegram_err = f"❌ <b>Erro Crítico no Backup!</b>\n\n{e}"
        whatsapp_err = f"❌ *Erro Crítico no Backup!*\n\n{e}"
        
        print(f"❌ Error: {e}")
        send_telegram_alert(telegram_err, config)
        send_whatsapp_alert(whatsapp_err, config)

if __name__ == "__main__":
    backup_database()

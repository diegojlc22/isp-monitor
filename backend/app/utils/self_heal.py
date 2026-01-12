import os
import shutil
import requests
import time
import psutil
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='logs/self_heal.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

API_URL = "http://localhost:8080/api/health"

def kill_process_by_name(name_snippet):
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(proc.info['cmdline'] or [])
            if name_snippet in cmd:
                logging.info(f"Matando processo travado: {proc.info['pid']} ({cmd})")
                proc.kill()
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return count

def clear_pycache():
    logging.info("Limpando cache Python (__pycache__)...")
    target_dir = os.path.join(os.getcwd(), 'backend')
    deleted = 0
    for root, dirs, files in os.walk(target_dir):
        if '__pycache__' in dirs:
            path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(path)
                deleted += 1
            except Exception as e:
                logging.error(f"Erro ao deletar {path}: {e}")
    logging.info(f"Cache limpo: {deleted} pastas removidas.")

def check_api_health():
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            return True, "Healthy"
        else:
            return False, f"Status Code {response.status_code}"
    except Exception as e:
        return False, str(e)

def perform_self_healing():
    logging.warning("⚠️ DETECTADA FALHA NA API. INICIANDO PROTOCOLO DE AUTO-CURA...")
    
    # 1. Kill API
    kill_process_by_name("uvicorn")
    time.sleep(2)
    
    # 2. Clean Cache (Resolves Ghost Rotas)
    clear_pycache()
    
    # 3. Restart is handled by the Supervisor (launcher.pyw) usually, 
    # but here we just ensure the environment is clean for the next restart.
    logging.info("✅ Ambiente limpo. O Launcher deve reiniciar a API em instantes.")

if __name__ == "__main__":
    logging.info("🔍 Diagnosticando Saúde do Sistema...")
    ok, msg = check_api_health()
    if not ok:
        logging.error(f"❌ API Falhou no diagnóstico: {msg}")
        perform_self_healing()
    else:
        logging.info("✅ Sistema Saudável. Nenhuma ação necessária.")

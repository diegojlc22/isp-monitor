import os
import sys
import time
import subprocess
import psutil
from datetime import datetime

# ==========================================================
# DOCTOR V4.0 - O GUARDIÃO SUPREMO (AUTÔNOMO)
# ==========================================================

LOG_FILE = "logs/self_heal.log"
PYTHON_EXE = sys.executable
MAX_LOG_SIZE = 50 * 1024 * 1024  # 50MB
MEMORY_LIMIT_MB = 1000 # 1GB por serviço

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

SERVICES = {
    "whatsapp": {
        "cmd": "node server.js",
        "port": 3001, 
        "health_url": "http://localhost:3001/status",
        "check": ["node", "server.js"],
        "log": "logs/whatsapp.log",
        "cwd": "backend/tools/whatsapp",
        "mem_limit": 1200 # Puppeteer gasta mais
    },
    "api": {
        "cmd": f'"{PYTHON_EXE}" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080',
        "port": 8080,
        "health_url": "http://localhost:8080/api/health",
        "check": ["uvicorn", "backend.app.main:app"],
        "log": "logs/api.log"
    },
    "collector": {
        "cmd": f'"{PYTHON_EXE}" backend/collector.py',
        "check": ["backend/collector.py"],
        "log": "logs/collector.log"
    },
    "frontend": {
        "cmd": "npm run dev",
        "port": 5173,
        "check": ["vite"],
        "log": "logs/frontend.log",
        "cwd": "frontend"
    }
}

PARENT_PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
SPAWNED_PROCS = {} 

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] [{level}] {message}"
    print(msg)
    os.makedirs("logs", exist_ok=True)
    try:
        # Rotação de log simples: se o self_heal.log crescer demais, limpa.
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
             with open(LOG_FILE, "w", encoding="utf-8") as f: f.write(f"--- Log Rotated at {timestamp} ---\n")
             
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except: pass

def rotate_service_logs():
    """Garante que nenhum log de serviço sature o disco"""
    for name, config in SERVICES.items():
        log_path = config.get("log")
        if log_path and os.path.exists(log_path):
            if os.path.getsize(log_path) > MAX_LOG_SIZE:
                log(f"✂️ [MAINTENANCE] Rotacionando log de {name} ({MAX_LOG_SIZE/1024/1024}MB excedidos)", "INFO")
                try:
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(f"--- Log Rotated by Doctor at {datetime.now()} ---\n")
                except: pass

def check_config_integrity():
    """Protege contra arquivos .env duplicados ou conflitantes (Evita erro 403)"""
    redundant_env = "backend/.env"
    if os.path.exists(redundant_env):
        log(f"🛡️ [INTEGRITY] Detectado arquivo .env redundante em {redundant_env}. Removendo para evitar conflitos de configuração.", "WARN")
        try: os.remove(redundant_env)
        except Exception as e: log(f"❌ Erro ao remover env redundante: {e}", "ERROR")

def check_port(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except: return False

def check_health(url):
    """Verifica se o serviço está respondendo logicamente (não apenas porta aberta)"""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except:
        return False

def kill_process_by_port(port):
    killed = False
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                pid = conn.pid
                if pid and pid != os.getpid():
                    proc = psutil.Process(pid)
                    log(f"⚔️ [CLEANUP] Matando processo {proc.name()} (PID {pid}) que ocupava a porta {port}", "WARN")
                    proc.kill()
                    killed = True
            except: pass
    return killed

def kill_duplicates(name, config):
    check_list = config.get("check", [name])
    my_pid = os.getpid()
    killed_any = False
    
    if "port" in config:
        if kill_process_by_port(config["port"]):
            killed_any = True

    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.info['pid'] == my_pid: continue
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            if all(word.lower() in cmdline for word in check_list):
                 if "self_heal.py" not in cmdline:
                     proc.kill()
                     killed_any = True
        except: continue
    return killed_any

def monitor_resources():
    """Verifica uso de memória e mata serviços que excederam o limite (Memory Leaks)"""
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
        try:
            for name, config in SERVICES.items():
                check_list = config.get("check", [name])
                cmdline = " ".join(proc.info['cmdline'] or []).lower()
                if all(word.lower() in cmdline for word in check_list):
                    mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    limit = config.get("mem_limit", MEMORY_LIMIT_MB)
                    if mem_mb > limit:
                        log(f"💥 [RECOVERY] Serviço {name} excedeu limite de memória ({mem_mb:.1f}MB > {limit}MB). Resetando...", "CRITICAL")
                        proc.kill()
        except: continue

def is_running(name, config):
    # Primeiro: Check de porta
    port_up = False
    if "port" in config:
        if check_port(config["port"]):
            port_up = True
            # Se tem porta mas tem URL de health, tenta o health
            if "health_url" in config:
                if not check_health(config["health_url"]):
                    log(f"🤢 [HEALTH] {name.upper()} está na porta {config['port']} mas não responde ao Health Check. Reiniciando...", "WARN")
                    return False
            return True
    
    # Segundo: Check de processo (para serviços sem porta como o Collector)
    check_list = config.get("check", [name])
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            if all(word.lower() in cmdline for word in check_list):
                 if "self_heal.py" not in cmdline: return True
        except: continue
    return False

def kill_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try: child.kill()
            except: pass
        parent.kill()
    except psutil.NoSuchProcess: pass
    except Exception as e: log(f"⚠️ Erro ao matar árvore PID {pid}: {e}", "WARN")

def cleanup_all():
    log("💀 [SHUTDOWN] Iniciando protocolo 'Zombie Hunter'...", "WARN")
    for name, proc in SPAWNED_PROCS.items():
        if proc.poll() is None:
            log(f"🪓 Terminando {name.upper()} (PID {proc.pid})...")
            kill_process_tree(proc.pid)
    log("✅ Todos os serviços foram encerrados.", "INFO")

import atexit
atexit.register(cleanup_all)

import tempfile
def ensure_singleton():
    lock_file = os.path.join(tempfile.gettempdir(), "isp_monitor_doctor.lock")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                log(f"⚡ Outra instância do Doctor já está rodando (PID {pid}). Encerrando esta.", "WARN")
                sys.exit(0)
            else:
                log("♻️ Lock file encontrado, mas processo morreu. Assumindo controle.", "WARN")
                try: os.remove(lock_file)
                except: pass
        except: pass
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        atexit.register(lambda: os.remove(lock_file) if os.path.exists(lock_file) else None)
    except Exception as e: log(f"❌ Erro ao criar lock file: {e}", "ERROR")

def run_doctor():
    ensure_singleton()
    log("🚑 ========================================")
    log("🚑 DOCTOR V4.0 ONLINE - GUARDIÃO SUPREMO")
    log("🚑 ========================================")
    
    first_run = True

    while True:
        if PARENT_PID and not psutil.pid_exists(PARENT_PID):
            log("👋 Launcher fechado. Executando limpeza total...", "WARN")
            cleanup_all()
            sys.exit(0)

        # 1. Integridade de Config (Evita 403)
        check_config_integrity()
        
        # 2. Rotação de Logs (Evita disco cheio)
        rotate_service_logs()

        if first_run:
            log("🩺 [DOCTOR] Verificando se o PostgreSQL está acordado...")
            pg_ready = False
            for i in range(15):
                if check_port(5432):
                    log("✅ [DOCTOR] PostgreSQL detectado na porta 5432.")
                    pg_ready = True
                    break
                log(f"⏳ [DOCTOR] Aguardando PostgreSQL... ({i+1}/15)")
                time.sleep(2)
            
            if not pg_ready:
                log("⚠️ [DOCTOR] PostgreSQL não responde. Tentando reiniciar serviço...", "WARN")
                try:
                    svc_cmd = 'wmic service get name | findstr /i "postgresql-x64-"'
                    result = subprocess.check_output(svc_cmd, shell=True).decode().strip()
                    service_name = result.split('\n')[0].strip()
                    if service_name:
                        log(f"🔧 Reiniciando: {service_name}")
                        subprocess.run(f"net stop {service_name}", shell=True)
                        subprocess.run(f"net start {service_name}", shell=True)
                        time.sleep(5)
                except: pass

        # 3. Monitoramento de Recursos (Memory Leaks)
        if not first_run:
            monitor_resources()

        for name, config in SERVICES.items():
            try:
                should_start = False
                if first_run:
                    log(f"🧹 [CLEANUP] Preparando {name.upper()}...")
                    kill_duplicates(name, config)
                    if name == "whatsapp": 
                        subprocess.run("taskkill /F /IM node.exe /T", shell=True, capture_output=True, creationflags=0x08000000)
                    should_start = True
                    time.sleep(0.5)
                else:
                    if not is_running(name, config):
                        if "port" in config and check_port(config["port"]):
                            log(f"⚠️ [REPAIR] Porta {config['port']} ocupada mas serviço não responde. Limpando...", "WARN")
                            kill_process_by_port(config["port"])
                        
                        if name == "frontend" and os.path.exists("frontend/dist/index.html"):
                            continue 
                        should_start = True

                if should_start:
                    log(f"🚀 [START] Iniciando {name.upper()}...", "INFO")
                    log_path = config["log"]
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    mode = "w" if first_run else "a"
                    
                    if name == "frontend":
                        config["cmd"] = ["node", "node_modules/vite/bin/vite.js"]
                    
                    with open(log_path, mode, encoding="utf-8") as f:
                        f.write(f"\n--- [SYSTEM START] {datetime.now()} ---\n")
                        proc = subprocess.Popen(
                            config["cmd"],
                            cwd=config.get("cwd", "."),
                            creationflags=0x08000000,
                            stdout=f,
                            stderr=f,
                            shell=False if name == "frontend" else True, 
                            env=os.environ.copy()
                        )
                        SPAWNED_PROCS[name] = proc
                        
            except Exception as e:
                log(f"🚨 Erro ao gerenciar {name}: {e}", "CRITICAL")
        
        first_run = False
        time.sleep(15) # Ciclo de 15s

if __name__ == "__main__":
    run_doctor()

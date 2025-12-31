import os
import sys
import time
import subprocess
import psutil
from datetime import datetime

# ==========================================================
# DOCTOR V3.6 - O MESTRE DOS PROCESSOS (ULTRA-FINAL)
# ==========================================================

LOG_FILE = "logs/self_heal.log"
PYTHON_EXE = sys.executable

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

SERVICES = {
    "whatsapp": {
        "cmd": "node server.js",
        # "port": 3001, (Removed to force process check)
        "check": ["node", "server.js"],
        "log": "logs/whatsapp.log",
        "cwd": "tools/whatsapp"
    },
    "api": {
        "cmd": f'"{PYTHON_EXE}" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8080',
        "port": 8080,
        "check": ["uvicorn", "backend.app.main:app"],
        "log": "logs/api.log"
    },
    "pinger": {
        "cmd": f'"{PYTHON_EXE}" -m backend.app.services.pinger_fast',
        "check": ["pinger_fast"],
        "log": "logs/collector.log"
    },
    "snmp": {
        "cmd": f'"{PYTHON_EXE}" -m backend.app.services.snmp_monitor',
        "check": ["snmp_monitor"],
        "log": "logs/snmp.log"
    },
    "frontend": {
        "cmd": "npm run dev",
        "check": ["vite"],
        "log": "logs/frontend.log",
        "cwd": "frontend"
    },
    "ia-agent": {
        "cmd": f'"{PYTHON_EXE}" -m backend.app.services.synthetic_agent',
        "check": ["synthetic_agent"],
        "log": "logs/agent.log"
    }
}

PARENT_PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
SPAWNED_PROCS = {} # Nome -> Popen Object

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] [{level}] {message}"
    print(msg)
    os.makedirs("logs", exist_ok=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except: pass

def check_port(port):
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except: return False

def kill_duplicates(name, config):
    check_list = config.get("check", [name])
    my_pid = os.getpid()
    killed_any = False
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

def is_running(name, config):
    if "port" in config and check_port(config["port"]):
        return True
    
    check_list = config.get("check", [name])
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            if all(word.lower() in cmdline for word in check_list):
                 if "self_heal.py" not in cmdline: return True
        except: continue
    return False

def kill_process_tree(pid):
    """Mata uma árvore de processos inteira (Pai + Filhos)"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Mata filhos primeiro
        for child in children:
            try: child.kill()
            except: pass
            
        # Mata o pai
        parent.kill()
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        log(f"⚠️ Erro ao matar árvore PID {pid}: {e}", "WARN")

def cleanup_all():
    """Limpeza final ao fechar o Doctor"""
    log("💀 [SHUTDOWN] Iniciando protocolo 'Zombie Hunter'...", "WARN")
    
    for name, proc in SPAWNED_PROCS.items():
        if proc.poll() is None: # Se ainda está rodando
            log(f"🪓 Terminando {name.upper()} (PID {proc.pid})...")
            kill_process_tree(proc.pid)
    
    log("✅ Todos os serviços foram encerrados.", "INFO")

import atexit
atexit.register(cleanup_all)

def run_doctor():
    log("🚑 ========================================")
    log("🚑 DOCTOR V3.7 ONLINE - ZOMBIE HUNTER")
    log("🚑 ========================================")
    
    first_run = True

    while True:
        # Check se o Launcher morreu
        if PARENT_PID and not psutil.pid_exists(PARENT_PID):
            log("👋 Launcher fechado. Executando limpeza total...", "WARN")
            cleanup_all()
            sys.exit(0)

        # Anti-Collision: Aguardar Postgres estar PRONTO na primeira execução
        if first_run:
            log("🩺 [DOCTOR] Verificando se o PostgreSQL está acordado...")
            pg_ready = False
            for i in range(15): # Espera até 30 segundos
                if check_port(5432):
                    log("✅ [DOCTOR] PostgreSQL detectado na porta 5432.")
                    pg_ready = True
                    break
                log(f"⏳ [DOCTOR] Aguardando PostgreSQL... ({i+1}/15)")
                time.sleep(2)
            
            if not pg_ready:
                log("⚠️ [DOCTOR] PostgreSQL não responde. Tentando iniciar serviços mesmo assim...", "WARN")

        for name, config in SERVICES.items():
            try:
                # Na primeira rodada, FORÇAMOS o reinício de tudo
                should_start = False
                
                if first_run:
                    log(f"🧹 [CLEANUP] Preparando {name.upper()} para início fresco...")
                    kill_duplicates(name, config)
                    
                    if name == "whatsapp": 
                        subprocess.run("taskkill /F /IM node.exe /T", shell=True, capture_output=True, creationflags=0x08000000)
                    
                    should_start = True
                    time.sleep(0.5)
                else:
                    if not is_running(name, config):
                        # Frontend Optimization: Skip starting dev server if dist exists
                        if name == "frontend" and os.path.exists("frontend/dist/index.html"):
                            # log("⚡ [OPTIMIZATION] Frontend skipped (Using Production Build served by Backend)", "INFO")
                            continue 
                        should_start = True

                if should_start:
                    log(f"🚀 [START] Iniciando {name.upper()}...", "INFO")
                    
                    log_path = config["log"]
                    os.makedirs(os.path.dirname(log_path), exist_ok=True)
                    
                    mode = "w" if first_run else "a"
                    
                    if name == "frontend":
                        # Bypass npm/cmd entirely to avoid hangs
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
        time.sleep(10) # Ciclo mais relaxado (10s) para evitar falsos positivos em carga alta

if __name__ == "__main__":
    run_doctor()

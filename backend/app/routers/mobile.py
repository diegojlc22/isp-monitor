import subprocess
import os
import threading
import time
import shutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/mobile", tags=["mobile"])

class MobileStatus(BaseModel):
    is_running: bool
    url: str | None = None
    logs: list[str] = []

# Estado Global em Memória
# (Como só tem 1 instância do backend, isso funciona bem)
expo_process = None
expo_url = None
expo_logs = []
logs_lock = threading.Lock()

def add_log(msg: str):
    """Adiciona log thread-safe"""
    global expo_logs
    with logs_lock:
        expo_logs.append(msg)
        if len(expo_logs) > 50:
            expo_logs.pop(0)

def monitor_expo(proc):
    """Lê stdout do processo Expo em background"""
    global expo_url
    try:
        # Ler linha a linha
        for line in iter(proc.stdout.readline, ''):
            if not line: break
            line = line.strip()
            if not line: continue
            
            # Detectar URL do Expo (exp://...)
            if "exp://" in line:
                # Tenta isolar a URL
                parts = line.split()
                for p in parts:
                    if "exp://" in p:
                        # Remove caracteres estranhos de terminal se houver
                        clean_url = p.replace('│', '').strip()
                        expo_url = clean_url
                        add_log(f"URL DETECTADA: {clean_url}")
            
            # Adicionar ao log (limpando códigos ANSI de cor se possivel, mas ok deixar)
            add_log(line)
    except Exception as e:
        add_log(f"Erro no monitor: {e}")

@router.get("/status", response_model=MobileStatus)
def get_status():
    global expo_process, expo_url
    is_running = False
    if expo_process:
        if expo_process.poll() is None:
            is_running = True
        else:
            expo_process = None # Morreu
    
    return MobileStatus(is_running=is_running, url=expo_url, logs=list(expo_logs))

@router.post("/start")
def start_mobile():
    global expo_process, expo_url, expo_logs
    
    if expo_process is not None and expo_process.poll() is None:
        return {"message": "Servidor Mobile já está rodando"}
    
    # Reset estado
    expo_url = None
    with logs_lock:
        expo_logs = ["Iniciando servidor Expo..."]

    try:
        # Localizar pasta mobile
        # Assumindo que CWD é a raiz do projeto (onde roda o launcher/main.py)
        cwd = os.getcwd()
        mobile_dir = os.path.join(cwd, "mobile")
        
        if not os.path.exists(mobile_dir):
            # Tenta subir um nível se tiver dentro de backend
            if os.path.exists(os.path.join(cwd, "..", "mobile")):
                mobile_dir = os.path.abspath(os.path.join(cwd, "..", "mobile"))
            else:
                 raise HTTPException(404, "Diretório 'mobile' não encontrado no servidor.")

        # Comando
        # --offline: Evita login 
        # --go: Abre direto no link
        # Usamos shell=True no windows para npx funcionar direto
        cmd = "npx expo start --offline --go"
        
        expo_process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=mobile_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE, # Necessário para não travar esperando input
            text=True, # Python 3.7+ (universal_newlines)
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Iniciar monitor
        threading.Thread(target=monitor_expo, args=(expo_process,), daemon=True).start()
        
        return {"message": "Processo iniciado"}

    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.post("/stop")
def stop_mobile():
    global expo_process
    if expo_process:
        try:
            # Matar arvore de processos no Windows
            subprocess.run(f"taskkill /F /PID {expo_process.pid} /T", shell=True, creationflags=0x08000000)
        except:
            pass
        expo_process = None
    return {"message": "Parado"}

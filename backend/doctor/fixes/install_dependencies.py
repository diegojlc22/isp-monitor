import sys
import subprocess
import re

def run_fix(error_log):
    print("[DOCTOR] 🩺 Diagnóstico: Dependência Python faltando detectada.")
    
    # Extrair nome do modulo usando Regex
    # Padrao: ModuleNotFoundError: No module named 'xyz'
    match = re.search(r"No module named '([^']+)'", error_log)
    if not match:
        print("[DOCTOR] ❌ Não foi possível identificar o nome do módulo no erro.")
        return False
        
    module_name = match.group(1)
    
    # Mapeamento de nomes de import -> nomes de pacote pip (ex: PIL -> Pillow)
    PACKAGE_MAP = {
        "PIL": "Pillow",
        "bs4": "beautifulsoup4",
        "dotenv": "python-dotenv",
        "engineio": "python-engineio",
        "socketio": "python-socketio",
        "serial": "pyserial",
        "win32api": "pywin32",
        "win32con": "pywin32",
        "win32gui": "pywin32",
        "win32ui": "pywin32",
        "win32service": "pywin32",
        "win32serviceutil": "pywin32",
        "win32event": "pywin32",
        "winerror": "pywin32",
        "postgres": "psycopg2", # ou psycopg2-binary
        "asyncpg": "asyncpg",
        "sqlalchemy": "sqlalchemy",
        "alembic": "alembic",
    }
    
    pip_package = PACKAGE_MAP.get(module_name, module_name)
    
    print(f"[DOCTOR] 💊 Instalando pacote faltando: {pip_package}...")
    
    try:
        # Usa o executável do python atual para garantir que instala no ambiente certo
        cmd = [sys.executable, "-m", "pip", "install", pip_package]
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[DOCTOR] ✅ Pacote '{pip_package}' instalado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[DOCTOR] ❌ Falha ao instalar '{pip_package}': {e.stderr.decode(errors='ignore')}")
        return False

if __name__ == "__main__":
    # Teste manual: python install_dependencies.py "ModuleNotFoundError: No module named 'requests'"
    log = sys.argv[1] if len(sys.argv) > 1 else ""
    if log:
        run_fix(log)

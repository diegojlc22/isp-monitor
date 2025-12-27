import sys
import os
import time
import socket
import importlib
import subprocess
from datetime import datetime

# --- CONFIG ---
REQUIRED_VERSION = (3, 11) # Minimo
CRITICAL_LIBS = [
    "fastapi", "uvicorn", "sqlalchemy", "pydantic", 
    "asyncpg", "requests", "PIL", "psutil", 
    "qrcode", "tkinter"
]
CRITICAL_FILES = [
    "launcher.pyw", 
    "ABRIR_SISTEMA.bat", 
    "backend/app/main.py",
    ".project_version"
]

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(step, msg, status="INFO"):
    symbol = "ℹ"
    color = Colors.OKBLUE
    if status == "OK": 
        symbol = "✔"
        color = Colors.OKGREEN
    elif status == "FAIL": 
        symbol = "✖"
        color = Colors.FAIL
    elif status == "WARN":
        symbol = "⚠"
        color = Colors.WARNING

    print(f"{color}[{symbol}] {step}: {msg}{Colors.ENDC}")

def run_audit():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.HEADER}=================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}    ISP MONITOR - AUDITORIA DE SISTEMA (v1.0)     {Colors.ENDC}")
    print(f"{Colors.HEADER}=================================================={Colors.ENDC}")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    errors = 0
    warnings = 0

    # 1. PYTHON VERSION
    print(f"{Colors.BOLD}>>> 1. AMBIENTE DE EXECUCAO{Colors.ENDC}")
    v = sys.version_info
    v_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= REQUIRED_VERSION:
        print_status("Python Version", f"Detectado {v_str} (Compativel)", "OK")
    else:
        print_status("Python Version", f"Detectado {v_str} (INCOMPATIVEL - Requer 3.11+)", "FAIL")
        errors += 1

    # 2. LIBRARIES
    print(f"\n{Colors.BOLD}>>> 2. BIBLIOTECAS CRITICAS{Colors.ENDC}")
    for lib in CRITICAL_LIBS:
        try:
            if lib == "PIL": importlib.import_module("PIL")
            else: importlib.import_module(lib)
            print_status(f"Import {lib}", "Instalado", "OK")
        except ImportError:
            print_status(f"Import {lib}", "AUSENTE", "FAIL")
            errors += 1

    # 3. FILESYSTEM
    print(f"\n{Colors.BOLD}>>> 3. INTEGRIDADE DE ARQUIVOS{Colors.ENDC}")
    base_dir = os.getcwd()
    for f in CRITICAL_FILES:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            print_status(f"File {f}", "Encontrado", "OK")
        else:
            print_status(f"File {f}", "NAO ENCONTRADO", "FAIL")
            errors += 1

    # 4. NETWORK
    print(f"\n{Colors.BOLD}>>> 4. REDE & PORTAS{Colors.ENDC}")
    target_host = "127.0.0.1"
    target_port = 8080
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((target_host, target_port))
    if result == 0:
        print_status("Porta 8080", "Ocupada (Sistema Provavelmente Rodando)", "OK")
    else:
        print_status("Porta 8080", "Livre (Pronta para iniciar)", "INFO")
    sock.close()

    # 5. DATABASE DRIVER
    print(f"\n{Colors.BOLD}>>> 5. DRIVER DE BANCO DE DADOS{Colors.ENDC}")
    try:
        import asyncpg
        print_status("AsyncPG", "OK (Driver PostgreSQL Async)", "OK")
    except:
        print_status("AsyncPG", "FALHA CRITICA", "FAIL")
        errors += 1

    # SUMMARY
    print(f"\n{Colors.HEADER}=================================================={Colors.ENDC}")
    if errors == 0:
        print(f"{Colors.OKGREEN}AUDITORIA APROVADA! O SISTEMA ESTA 100% INTEGRO.{Colors.ENDC}")
        # Criar arquivo de flag de sucesso
        with open(".audit_ok", "w") as f: f.write(str(datetime.now()))
    else:
        print(f"{Colors.FAIL}AUDITORIA REPROVADA. {errors} ERROS ENCONTRADOS.{Colors.ENDC}")
        print("Recomendacao: Execute o REPARAR_TUDO.bat imediatamente.")
    
    print(f"{Colors.HEADER}=================================================={Colors.ENDC}")
    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    run_audit()

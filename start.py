#!/usr/bin/env python3
"""
ISP Monitor - Startup Script
Inicia o backend (FastAPI) e frontend (Vite) em janelas separadas
"""

import subprocess
import sys
import os
import time
import platform
from pathlib import Path

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Exibe o cabeçalho do aplicativo"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}  🌐 ISP Monitor - Sistema de Monitoramento de Rede{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}\n")

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    print(f"{Colors.YELLOW}🔍 Verificando requisitos...{Colors.END}")
    
    # Verifica Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print(f"{Colors.RED}❌ Python 3.9+ é necessário. Versão atual: {sys.version}{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}{Colors.END}")
    
    # Verifica Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Node.js {result.stdout.strip()}{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Node.js não encontrado{Colors.END}")
            return False
    except FileNotFoundError:
        print(f"{Colors.RED}❌ Node.js não encontrado. Instale em https://nodejs.org{Colors.END}")
        return False
    
    return True

def start_backend():
    """Inicia o servidor backend"""
    print(f"\n{Colors.GREEN}🚀 Iniciando Backend (FastAPI)...{Colors.END}")
    
    project_root = Path(__file__).parent
    os.environ['PYTHONPATH'] = str(project_root)
    
    system = platform.system()
    
    if system == "Windows":
        # Windows - abre em nova janela do PowerShell
        cmd = [
            'powershell', '-NoExit', '-Command',
            f"cd '{project_root}'; python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"
        ]
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # Linux/Mac - abre em novo terminal
        if system == "Linux":
            terminals = ['gnome-terminal', 'konsole', 'xterm']
            for term in terminals:
                try:
                    subprocess.Popen([
                        term, '--', 'bash', '-c',
                        f"cd '{project_root}' && python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000; exec bash"
                    ])
                    break
                except FileNotFoundError:
                    continue
        elif system == "Darwin":  # macOS
            subprocess.Popen([
                'osascript', '-e',
                f'tell app "Terminal" to do script "cd {project_root} && python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"'
            ])
    
    print(f"{Colors.BLUE}📡 Backend: http://localhost:8000{Colors.END}")
    print(f"{Colors.BLUE}📚 API Docs: http://localhost:8000/docs{Colors.END}")

def start_frontend():
    """Inicia o servidor frontend"""
    print(f"\n{Colors.GREEN}🚀 Iniciando Frontend (Vite)...{Colors.END}")
    
    project_root = Path(__file__).parent
    frontend_path = project_root / 'frontend'
    
    system = platform.system()
    
    if system == "Windows":
        # Windows - abre em nova janela do PowerShell
        cmd = [
            'powershell', '-NoExit', '-Command',
            f"cd '{frontend_path}'; npm run dev -- --host"
        ]
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # Linux/Mac - abre em novo terminal
        if system == "Linux":
            terminals = ['gnome-terminal', 'konsole', 'xterm']
            for term in terminals:
                try:
                    subprocess.Popen([
                        term, '--', 'bash', '-c',
                        f"cd '{frontend_path}' && npm run dev -- --host; exec bash"
                    ])
                    break
                except FileNotFoundError:
                    continue
        elif system == "Darwin":  # macOS
            subprocess.Popen([
                'osascript', '-e',
                f'tell app "Terminal" to do script "cd {frontend_path} && npm run dev -- --host"'
            ])
    
    print(f"{Colors.BLUE}🌐 Frontend: http://localhost:5173{Colors.END}")

def main():
    """Função principal"""
    print_header()
    
    # Verifica requisitos
    if not check_requirements():
        print(f"\n{Colors.RED}❌ Requisitos não atendidos. Corrija os erros acima.{Colors.END}")
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    # Inicia os serviços
    try:
        start_backend()
        time.sleep(2)  # Aguarda backend iniciar
        start_frontend()
        
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✅ Serviços iniciados com sucesso!{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        
        print(f"\n{Colors.YELLOW}💡 Dica: Duas janelas foram abertas (Backend e Frontend){Colors.END}")
        print(f"{Colors.YELLOW}💡 Acesse: http://localhost:5173{Colors.END}")
        print(f"\n{Colors.YELLOW}Para parar os serviços, feche as janelas ou pressione CTRL+C{Colors.END}\n")
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ Erro ao iniciar serviços: {e}{Colors.END}")
        input("\nPressione ENTER para sair...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Encerrando...{Colors.END}")
        sys.exit(0)

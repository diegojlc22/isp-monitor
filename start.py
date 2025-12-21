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
import requests
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
    
    project_root = Path(__file__).parent.absolute()
    os.environ['PYTHONPATH'] = str(project_root)
    
    system = platform.system()
    python_exe = sys.executable  # Usa o mesmo Python que está executando este script
    
    try:
        if system == "Windows":
            # Windows - abre em nova janela do CMD (mais confiável que PowerShell)
            cmd = f'start "ISP Monitor - Backend" cmd /k "cd /d {project_root} && {python_exe} -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"'
            subprocess.run(cmd, shell=True, check=True)
            print(f"{Colors.GREEN}  ✓ Janela do Backend aberta{Colors.END}")
        else:
            # Linux/Mac - abre em novo terminal
            if system == "Linux":
                terminals = ['gnome-terminal', 'konsole', 'xterm']
                for term in terminals:
                    try:
                        subprocess.Popen([
                            term, '--', 'bash', '-c',
                            f"cd '{project_root}' && {python_exe} -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000; exec bash"
                        ])
                        break
                    except FileNotFoundError:
                        continue
            elif system == "Darwin":  # macOS
                subprocess.Popen([
                    'osascript', '-e',
                    f'tell app "Terminal" to do script "cd {project_root} && {python_exe} -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000"'
                ])
        
        print(f"{Colors.BLUE}📡 Backend: http://localhost:8000{Colors.END}")
        print(f"{Colors.BLUE}📚 API Docs: http://localhost:8000/docs{Colors.END}")
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao abrir Backend: {e}{Colors.END}")
        return False

def start_frontend():
    """Inicia o servidor frontend"""
    print(f"\n{Colors.GREEN}🚀 Iniciando Frontend (Vite)...{Colors.END}")
    
    project_root = Path(__file__).parent.absolute()
    frontend_path = project_root / 'frontend'
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows - abre em nova janela do CMD (mais confiável que PowerShell)
            cmd = f'start "ISP Monitor - Frontend" cmd /k "cd /d {frontend_path} && npm run dev -- --host"'
            subprocess.run(cmd, shell=True, check=True)
            print(f"{Colors.GREEN}  ✓ Janela do Frontend aberta{Colors.END}")
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
        return True
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao abrir Frontend: {e}{Colors.END}")
        return False

def wait_for_backend(max_wait=30):
    """Aguarda o backend estar pronto"""
    print(f"\n{Colors.YELLOW}⏳ Aguardando backend iniciar...{Colors.END}", end="", flush=True)
    
    for i in range(max_wait):
        try:
            # Tenta conectar em 127.0.0.1 (mais confiável que localhost no Windows)
            response = requests.get('http://127.0.0.1:8000/', timeout=2)
            if response.status_code in [200, 404]:  # 404 é ok, significa que está respondendo
                print(f" {Colors.GREEN}✓ Backend pronto!{Colors.END}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 3 == 0:
            print(".", end="", flush=True)
    
    print(f" {Colors.RED}✗ Timeout{Colors.END}")
    return False

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
        backend_ok = start_backend()
        
        if backend_ok:
            # Aguarda backend estar pronto
            backend_ready = wait_for_backend(30)
            
            if backend_ready:
                frontend_ok = start_frontend()
            else:
                print(f"\n{Colors.RED}❌ Backend não respondeu a tempo. Verifique a janela do Backend.{Colors.END}")
                frontend_ok = False
        else:
            frontend_ok = False
        
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        
        if backend_ok and frontend_ok:
            print(f"{Colors.GREEN}✅ Ambos os serviços iniciados com sucesso!{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
            print(f"\n{Colors.YELLOW}💡 Dica: Duas janelas CMD foram abertas:{Colors.END}")
            print(f"{Colors.YELLOW}   • ISP Monitor - Backend (porta 8000){Colors.END}")
            print(f"{Colors.YELLOW}   • ISP Monitor - Frontend (porta 5173){Colors.END}")
            print(f"\n{Colors.YELLOW}💡 Acesse a aplicação: {Colors.BOLD}http://localhost:5173{Colors.END}")
        elif backend_ok:
            print(f"{Colors.YELLOW}⚠️  Backend iniciado, mas Frontend falhou{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        elif frontend_ok:
            print(f"{Colors.YELLOW}⚠️  Frontend iniciado, mas Backend falhou{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        else:
            print(f"{Colors.RED}❌ Ambos os serviços falharam ao iniciar{Colors.END}")
            print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
            
        print(f"\n{Colors.YELLOW}Para parar os serviços, feche as janelas CMD ou pressione CTRL+C{Colors.END}\n")
        
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

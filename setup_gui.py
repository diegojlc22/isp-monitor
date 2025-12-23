import tkinter as tk
from tkinter import ttk
import sys
import os
import subprocess
import threading
import time
import platform
import urllib.request
import queue

# Configurações de Cores (Mesmo tema do launcher)
COLORS = {
    'bg': '#1e1e1e',
    'fg': '#e0e0e0',
    'accent': '#007acc',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'panel_bg': '#252526',
    'border': '#3e3e42'
}

class SetupStep:
    def __init__(self, name, check_func, install_func):
        self.name = name
        self.check_func = check_func
        self.install_func = install_func
        self.status = "PENDING" # PENDING, CHECKING, OK, INSTALLING, ERROR
        self.message = ""

class SetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ISP Monitor - Verificação de Sistema")
        self.root.geometry("600x450")
        self.root.configure(bg=COLORS['bg'])

        self.steps = [
            SetupStep("Python 3.11+", self.check_python, None),
            SetupStep("Node.js Check", self.check_node, self.install_node),
            SetupStep("Ambiente Virtual (.venv)", self.check_venv, self.create_venv),
            SetupStep("Dependências Backend", self.check_backend, self.install_backend),
            SetupStep("Dependências Frontend", self.check_frontend, self.install_frontend),
        ]

        # UI Elements
        self.step_frames = []
        self.status_labels = []
        self.main_queue = queue.Queue()
        
        self.setup_ui()
        
        # Start verification
        self.is_running = True
        self.has_launched = False
        self.worker_thread = threading.Thread(target=self.run_process, daemon=True)
        self.worker_thread.start()
        
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Panel.TFrame', background=COLORS['panel_bg'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'], font=('Segoe UI', 11))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=COLORS['accent'])
        style.configure('Status.TLabel', font=('Segoe UI', 10))

        # Header
        header = ttk.Frame(self.root, padding="20")
        header.pack(fill='x')
        ttk.Label(header, text="Configuração do Ambiente", style='Title.TLabel').pack(side='left')

        # Steps Container
        self.container = ttk.Frame(self.root, padding="20")
        self.container.pack(fill='both', expand=True)

        for step in self.steps:
            frame = ttk.Frame(self.container, style='Panel.TFrame')
            frame.pack(fill='x', pady=5, ipady=5)
            
            # Label Nome
            lbl_name = ttk.Label(frame, text=step.name, background=COLORS['panel_bg'], font=('Segoe UI', 11, 'bold'))
            lbl_name.pack(side='left', padx=10)
            
            # Label Status
            lbl_status = ttk.Label(frame, text="Aguardando...", background=COLORS['panel_bg'], foreground='#888888')
            lbl_status.pack(side='right', padx=10)
            
            self.step_frames.append(frame)
            self.status_labels.append(lbl_status)

        # Footer / Log
        self.footer = ttk.Frame(self.root, padding="10")
        self.footer.pack(fill='x', side='bottom')
        self.lbl_info = ttk.Label(self.footer, text="Iniciando verificações...", font=('Consolas', 9), foreground='#888888')
        self.lbl_info.pack(side='left')

    def update_step_ui(self, index, status, text=None):
        self.main_queue.put(('UPDATE', index, status, text))

    def log_info(self, msg):
        self.main_queue.put(('LOG', msg))

    def process_queue(self):
        try:
            while True:
                msg_type, *args = self.main_queue.get_nowait()
                if msg_type == 'UPDATE':
                    idx, status, text = args
                    lbl = self.status_labels[idx]
                    
                    if status == 'CHECKING':
                        lbl.config(text="Verificando...", foreground=COLORS['warning'])
                    elif status == 'INSTALLING':
                        lbl.config(text=text or "Instalando...", foreground=COLORS['accent'])
                    elif status == 'OK':
                        lbl.config(text="OK", foreground=COLORS['success'])
                    elif status == 'ERROR':
                        lbl.config(text="ERRO", foreground=COLORS['error'])
                elif msg_type == 'LOG':
                    self.lbl_info.config(text=args[0])
                elif msg_type == 'FINISH':
                    self.launch_main()
        except queue.Empty:
            pass
        
        if self.is_running:
            self.root.after(100, self.process_queue)

    def run_process(self):
        all_ok = True
        for i, step in enumerate(self.steps):
            self.update_step_ui(i, 'CHECKING')
            self.log_info(f"Verificando {step.name}...")
            time.sleep(0.5) # UX delay

            try:
                if step.check_func():
                    self.update_step_ui(i, 'OK')
                else:
                    if step.install_func:
                        self.update_step_ui(i, 'INSTALLING')
                        self.log_info(f"Instalando {step.name}...")
                        step.install_func()
                        
                        # Re-check
                        if step.check_func():
                            self.update_step_ui(i, 'OK')
                        else:
                            self.update_step_ui(i, 'ERROR', "Falha na verificação pós-instalação")
                            all_ok = False
                            break
                    else:
                        self.update_step_ui(i, 'ERROR', "Requisito não atendido")
                        all_ok = False
                        break
            except Exception as e:
                self.update_step_ui(i, 'ERROR', str(e))
                print(e)
                all_ok = False
                break
        
        if all_ok:
            self.log_info("Tudo pronto! Iniciando launcher...")
            time.sleep(1)
            self.main_queue.put(('FINISH',))
        else:
            self.log_info("Houve erros. Verifique e reinicie.")

    # --- CHECKS & INSTALLS ---

    def check_python(self):
        # Se este script está rodando, Python existe.
        return True

    def check_node(self):
        try:
            startupinfo = None
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(["npm", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, check=True, startupinfo=startupinfo)
            return True
        except:
            return False

    def install_node(self):
        url = "https://nodejs.org/dist/v18.17.1/node-v18.17.1-x64.msi"
        msi_path = os.path.join(os.environ["TEMP"], "node_install.msi")
        
        self.log_info("Baixando Node.js...")
        urllib.request.urlretrieve(url, msi_path)
        
        self.log_info("Executando instalador Node.js...")
        subprocess.run(f'msiexec.exe /i "{msi_path}" /qn', shell=True, check=True)
        
        # Atualiza PATH para o processo atual
        os.environ["PATH"] += r";C:\Program Files\nodejs"

    def check_venv(self):
        return os.path.exists(".venv") and os.path.exists(os.path.join(".venv", "Scripts", "python.exe"))

    def create_venv(self):
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)

    def check_backend(self):
        # Verifica se requirements está instalado no venv
        if not os.path.exists(".venv"): return False
        
        venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
        try:
            # Verifica apenas um pacote chave para ser rápido
            result = subprocess.run([venv_pip, "show", "fastapi"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def install_backend(self):
        venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
        subprocess.run([venv_pip, "install", "-r", "backend/requirements.txt"], check=True)

    def check_frontend(self):
        return os.path.exists(os.path.join("frontend", "node_modules"))

    def install_frontend(self):
        cwd = os.path.join(os.getcwd(), "frontend")
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        subprocess.run([npm_cmd, "install"], cwd=cwd, shell=True, check=True)

    def launch_main(self):
        if self.has_launched:
            return
        self.has_launched = True
        self.root.destroy()
        
        # Estratégia Prioritária: Usar o pythonw.exe do VENV (Garante ambiente + sem janela)
        venv_pythonw = os.path.join(os.getcwd(), ".venv", "Scripts", "pythonw.exe")
        venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
        
        target_exe = sys.executable
        
        if os.path.exists(venv_pythonw):
            target_exe = venv_pythonw
        elif os.path.exists(venv_python):
            # Fallback para python do venv (pode abrir janela se não tiver w, mas garante ambiente)
            target_exe = venv_python
            
            # Tenta achar pythonw relativo ao sys.executable se o do venv falhou (raro)
            if 'python.exe' in sys.executable:
                sys_w = sys.executable.replace('python.exe', 'pythonw.exe')
                if os.path.exists(sys_w):
                    # Atenção: usar pythonw do sistema global para rodar script que depende do venv pode dar erro de import
                    # O ideal é o venv_pythonw. Se não tiver, vamos de venv_python.
                    pass

        # Configurações extras para garantir ocultação no Windows
        creationflags = 0
        if platform.system() == 'Windows':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        subprocess.Popen([target_exe, "launcher.pyw"], close_fds=True, creationflags=creationflags)
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SetupApp(root)
    root.mainloop()

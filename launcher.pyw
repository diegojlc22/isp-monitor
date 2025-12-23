import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import sys
import os
import threading
import queue
import platform
import signal
from pathlib import Path
import time

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# Configurações de Cores (Tema Escuro Premium)
COLORS = {
    'bg': '#1e1e1e',
    'fg': '#e0e0e0',
    'accent': '#007acc',
    'accent_hover': '#005c99',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'console_bg': '#121212',
    'console_fg': '#cccccc',
    'panel_bg': '#252526',
    'border': '#3e3e42'
}

def create_tray_image():
    # Gera um ícone simples via código se não tiver nenhum
    width = 64
    height = 64
    color1 = "#007acc"
    color2 = "#1e1e1e"
    
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
        fill=color2)
    return image

class ServiceThread(threading.Thread):
    def __init__(self, command, name, log_queue, cwd=None):
        super().__init__()
        self.command = command
        self.name = name
        self.log_queue = log_queue
        self.cwd = cwd
        self.process = None
        self.should_stop = False
        self.daemon = True

    def run(self):
        startupinfo = None
        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'

        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False,
                cwd=self.cwd,
                env=env,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )

            self.log_queue.put(('INFO', f"[{self.name}] Serviço iniciado (PID: {self.process.pid})\n"))

            while not self.should_stop and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    break
                try:
                    decoded = line.decode('utf-8', errors='replace').strip()
                    if decoded:
                        self.log_queue.put(('LOG', f"[{self.name}] {decoded}\n"))
                except:
                    pass
            
            if self.process.returncode != 0 and self.process.returncode is not None:
                self.log_queue.put(('ERROR', f"[{self.name}] Processo encerrou com código {self.process.returncode}\n"))
            else:
                self.log_queue.put(('INFO', f"[{self.name}] Processo finalizado corretamente.\n"))

        except Exception as e:
            self.log_queue.put(('ERROR', f"[{self.name}] Falha ao iniciar: {str(e)}\n"))

    def stop(self):
        self.should_stop = True
        if self.process and self.process.poll() is None:
            self.log_queue.put(('WARN', f"[{self.name}] Parando serviço...\n"))
            if platform.system() == 'Windows':
                # Mata a árvore de processos no Windows
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.process.terminate()

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ISP Monitor - Control Panel")
        self.root.geometry("1000x800")
        self.root.configure(bg=COLORS['bg'])
        
        self.log_queue = queue.Queue()
        self.backend_thread = None
        self.frontend_thread = None
        self.deploy_thread = None
        
        # Mode: 'prod' or 'dev'
        self.mode_var = tk.StringVar(value="prod")
        
        self.setup_styles()
        self.create_widgets()
        
        self.is_running = False
        
        # Setup Tray
        self.tray_icon = None
        if HAS_TRAY:
            self.setup_tray()
        
        # Inicia verificação de logs
        self.root.after(100, self.process_logs)

    # ... (tray methods remain same) ...

    def setup_tray(self):
        image = create_tray_image()
        menu = (
            item('Abrir Painel', self.show_window, default=True),
            item('Parar e Sair', self.quit_app)
        )
        self.tray_icon = pystray.Icon("isp_monitor", image, "ISP Monitor", menu)
        # Rodar tray em thread separada para não travar GUI
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.exit_fully)

    def exit_fully(self):
        if self.is_running:
            self.stop_all()
        
        # Stop tray icon explicitly to remove ghost icon
        if self.tray_icon:
            self.tray_icon.stop()

        self.root.destroy()
        # Force kill to ensure no background threads remain
        os._exit(0)


    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # Base theme clean
        
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Panel.TFrame', background=COLORS['panel_bg'], relief='flat')
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'), foreground=COLORS['accent'])
        style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'), background=COLORS['panel_bg'])

        # Radiobuttons
        style.configure('TRadiobutton', background=COLORS['bg'], foreground=COLORS['fg'], font=('Segoe UI', 10))
        style.map('TRadiobutton', background=[('active', COLORS['bg'])], indicatorcolor=[('selected', COLORS['accent'])])

        # Buttons
        style.configure('TButton', 
            font=('Segoe UI', 11), 
            borderwidth=0, 
            focuscolor=COLORS['bg'],
            padding=(20, 10)
        )
        style.map('TButton',
            background=[('active', COLORS['accent_hover']), ('!active', COLORS['accent'])],
            foreground=[('active', '#ffffff'), ('!active', '#ffffff')]
        )
        
        style.configure('Danger.TButton', background=COLORS['error'])
        style.map('Danger.TButton',
            background=[('active', '#d32f2f'), ('!active', COLORS['error'])],
        )

        style.configure('Success.TButton', background=COLORS['success'])
        style.map('Success.TButton',
            background=[('active', '#388e3c'), ('!active', COLORS['success'])],
        )
        
        style.configure('Neutral.TButton', background='#424242')
        style.map('Neutral.TButton',
            background=[('active', '#616161'), ('!active', '#424242')],
        )

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill='both', expand=True)

        # Header
        header = ttk.Frame(main_container)
        header.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(header, text="🌐 ISP Monitor", style='Header.TLabel')
        title_label.pack(side='left')

        status_container = ttk.Frame(header)
        status_container.pack(side='right')
        
        self.status_indicator = tk.Canvas(status_container, width=15, height=15, bg=COLORS['bg'], highlightthickness=0)
        self.status_indicator_circle = self.status_indicator.create_oval(2, 2, 13, 13, fill=COLORS['error'], outline="")
        self.status_indicator.pack(side='left', padx=5)
        
        self.status_text = ttk.Label(status_container, text="Parado", font=('Segoe UI', 10, 'bold'), foreground=COLORS['error'])
        self.status_text.pack(side='left')

        # Mode Selection
        mode_frame = ttk.Frame(main_container)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(mode_frame, text="Modo de Operação:", font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(0, 10))
        
        rb_prod = ttk.Radiobutton(mode_frame, text="Produção (Recomendado)", variable=self.mode_var, value="prod", command=self.on_mode_change)
        rb_prod.pack(side='left', padx=10)
        
        rb_dev = ttk.Radiobutton(mode_frame, text="Desenvolvimento (Hot-Reload)", variable=self.mode_var, value="dev", command=self.on_mode_change)
        rb_dev.pack(side='left', padx=10)
        
        # Build Button
        self.btn_build = ttk.Button(mode_frame, text="⚡ Criar Build / Deploy", style='Neutral.TButton', command=self.run_deploy)
        self.btn_build.pack(side='right')

        # Control Panel
        control_panel = ttk.Frame(main_container, style='Panel.TFrame', padding="15")
        control_panel.pack(fill='x', pady=(0, 20))

        # Botões
        self.btn_start = ttk.Button(control_panel, text="▶ Iniciar Sistema", style='Success.TButton', command=self.start_all)
        self.btn_start.pack(side='left', padx=(0, 10))

        self.btn_restart_backend = ttk.Button(control_panel, text="⟳ Reiniciar Backend", command=self.restart_backend, state='disabled')
        self.btn_restart_backend.pack(side='left', padx=(0, 10))

        self.btn_stop = ttk.Button(control_panel, text="⏹ Parar Tudo", style='Danger.TButton', command=self.stop_all, state='disabled')
        self.btn_stop.pack(side='left')

        self.btn_open_browser = ttk.Button(control_panel, text="↗ Abrir Navegador", command=self.open_browser)
        self.btn_open_browser.pack(side='right')

        # Links rápidos
        links_panel = ttk.Frame(main_container, height=30)
        links_panel.pack(fill='x', pady=(0, 10))
        ttk.Label(links_panel, text="Acesso: ").pack(side='left')
        
        self.link_url_label = tk.Label(links_panel, text="http://localhost:8080", fg=COLORS['accent'], bg=COLORS['bg'], cursor="hand2", font=('Segoe UI', 10, 'underline'))
        self.link_url_label.pack(side='left', padx=5)
        self.link_url_label.bind("<Button-1>", lambda e: self.open_browser())

        # Console Log
        log_frame = ttk.LabelFrame(main_container, text=" Log do Sistema ", padding="5")
        log_frame.pack(fill='both', expand=True)

        self.console = scrolledtext.ScrolledText(
            log_frame, 
            bg=COLORS['console_bg'], 
            fg=COLORS['console_fg'], 
            font=('Consolas', 10),
            state='disabled',
            insertbackground='white'
        )
        self.console.pack(fill='both', expand=True)
        
        # Tags de cor para o console
        self.console.tag_config('INFO', foreground='#2196f3')
        self.console.tag_config('WARN', foreground='#ffc107')
        self.console.tag_config('ERROR', foreground='#f44336')
        self.console.tag_config('LOG', foreground='#e0e0e0')
        self.console.tag_config('SUCCESS', foreground='#4caf50')

        self.log_message('INFO', "Sistema pronto. Selecione o modo e clique em Iniciar.")
        self.update_url_label()

    def on_mode_change(self):
        self.update_url_label()
        mode = self.mode_var.get()
        if mode == 'prod':
            self.log_message('INFO', "Modo Selecionado: Produção (Leve, Rápido, Estável).")
        else:
            self.log_message('INFO', "Modo Selecionado: Desenvolvimento (Hot-Reload, Debug, Pesado).")

    def update_url_label(self):
        mode = self.mode_var.get()
        url = "http://localhost:8080"
        if mode == 'dev':
            url = "http://localhost:5173"
        self.link_url_label.config(text=url)

    def log_message(self, level, message):
        self.console.configure(state='normal')
        self.console.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] ", 'LOG')
        self.console.insert(tk.END, message + "\n", level)
        self.console.see(tk.END)
        self.console.configure(state='disabled')

    def process_logs(self):
        while not self.log_queue.empty():
            try:
                level, msg = self.log_queue.get_nowait()
                tag = level
                if "ERROR" in msg or "Exception" in msg or "Failed" in msg:
                    tag = 'ERROR'
                elif "WARNING" in msg:
                    tag = 'WARN'
                elif "Deploy concluido" in msg:
                    tag = 'SUCCESS'
                
                self.log_message(tag, msg.rstrip())
            except queue.Empty:
                pass
        self.root.after(50, self.process_logs)

    def run_deploy(self):
        if self.is_running:
            messagebox.showwarning("Aviso", "Pare o sistema antes de fazer deploy.")
            return

        if not messagebox.askyesno("Confirmar Deploy", "Isso vai compilar o Frontend para Produção.\nPode levar alguns minutos. Continuar?"):
            return

        self.log_message('WARN', "Iniciando Deploy... Aguarde.")
        
        project_root = Path(__file__).parent.absolute()
        frontend_path = project_root / 'frontend'
        
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        
        # Chain commands: install + build
        cmd = [npm_cmd, 'run', 'build']
        
        self.deploy_thread = ServiceThread(cmd, "DEPLOY", self.log_queue, cwd=frontend_path)
        self.deploy_thread.start()

    def start_all(self):
        if self.is_running:
            return
        
        mode = self.mode_var.get()
        project_root = Path(__file__).parent.absolute()
        python_exe = sys.executable

        # Check production build if PROD
        if mode == 'prod':
            dist_path = project_root / 'frontend' / 'dist'
            if not dist_path.exists():
                messagebox.showerror("Erro de Deploy", "Arquivos de produção não encontrados!\n\nPor favor, clique em 'Criar Build / Deploy' antes de iniciar em modo produção.")
                return

        self.is_running = True
        self.update_ui_state(running=True)
        self.log_message('INFO', f"Iniciando serviços em modo {mode.upper()}...")

        if mode == 'prod':
            # Single Process
            # --workers 1 is important for SQLite stability
            cmd = [python_exe, '-m', 'uvicorn', 'backend.app.main:app', '--host', '0.0.0.0', '--port', '8080', '--workers', '1']
            self.backend_thread = ServiceThread(cmd, "SERVER", self.log_queue, cwd=project_root)
            self.backend_thread.start()
        
        else: # DEV MODE
            # Backend with Reload
            backend_cmd = [python_exe, '-m', 'uvicorn', 'backend.app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8080']
            self.backend_thread = ServiceThread(backend_cmd, "BACKEND-DEV", self.log_queue, cwd=project_root)
            self.backend_thread.start()

            # Frontend with Vite host
            frontend_path = project_root / 'frontend'
            vite_path = frontend_path / 'node_modules' / 'vite' / 'bin' / 'vite.js'
            
            if vite_path.exists():
                frontend_cmd = ['node', str(vite_path), '--host']
            else:
                npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
                frontend_cmd = [npm_cmd, 'run', 'dev', '--', '--host']

            self.frontend_thread = ServiceThread(frontend_cmd, "FRONTEND-DEV", self.log_queue, cwd=frontend_path)
            self.frontend_thread.start()

    def stop_all(self):
        if self.backend_thread:
            self.backend_thread.stop()
        if self.frontend_thread:
            self.frontend_thread.stop()
        
        self.is_running = False
        self.update_ui_state(running=False)
        self.log_message('WARN', "Todos os serviços foram parados.")

    def restart_backend(self):
        if not self.is_running: return
        
        self.log_message('WARN', "Reiniciando Backend...")
        
        if self.backend_thread:
            self.backend_thread.stop()
        
        time.sleep(1)
        
        # Restart with same logic as start_all
        mode = self.mode_var.get()
        project_root = Path(__file__).parent.absolute()
        python_exe = sys.executable
        
        if mode == 'prod':
             cmd = [python_exe, '-m', 'uvicorn', 'backend.app.main:app', '--host', '0.0.0.0', '--port', '8080', '--workers', '1']
             self.backend_thread = ServiceThread(cmd, "SERVER", self.log_queue, cwd=project_root)
        else:
             cmd = [python_exe, '-m', 'uvicorn', 'backend.app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8080']
             self.backend_thread = ServiceThread(cmd, "BACKEND-DEV", self.log_queue, cwd=project_root)
             
        self.backend_thread.start()

    def open_browser(self):
        mode = self.mode_var.get()
        url = "http://localhost:8080" if mode == 'prod' else "http://localhost:5173"
        subprocess.run(f'start {url}', shell=True)

    def update_ui_state(self, running):
        if running:
            self.status_indicator.itemconfig(self.status_indicator_circle, fill=COLORS['success'])
            self.status_text.config(text="Executando", foreground=COLORS['success'])
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')
            self.btn_restart_backend.config(state='normal')
            # Disable mode switch while running
            # We can't easily disable radiobuttons variable but we can disable widgets? 
            # Simplification: Just trust user or improve later.
        else:
            self.status_indicator.itemconfig(self.status_indicator_circle, fill=COLORS['error'])
            self.status_text.config(text="Parado", foreground=COLORS['error'])
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.btn_restart_backend.config(state='disabled')

    def on_closing(self):
        if HAS_TRAY and self.tray_icon:
            self.root.withdraw()
            # Mostra notificação na bandeja se possível ou apenas esconde
        else:
            if self.is_running:
                if tk.messagebox.askokcancel("Sair", "Os serviços ainda estão rodando. Deseja parar tudo e sair?"):
                    self.stop_all()
                    self.root.destroy()
            else:
                self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

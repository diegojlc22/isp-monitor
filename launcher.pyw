
"""
ISP Monitor - Launcher v3.0 (by: Diego)
Interface gráfica moderna e robusta para gerenciamento do sistema.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import subprocess
import os
import sys
import shutil
import psutil
import time
import threading
import socket
import requests
import qrcode
from PIL import Image, ImageTk

# --- LOGGING SETUP ---
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
       self.log_data = [] # Espelho em memória

   def write(self, data):
       try:
           self.stream.write(data)
           self.stream.flush()
           self.log_data.append(data)
           if len(self.log_data) > 1000: # Limita memória
               self.log_data.pop(0)
       except: pass

   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
       self.log_data.extend(datas)

   def __getattr__(self, attr):
       return getattr(self.stream, attr)

try:
    log_file = open("startup.log", "w", encoding="utf-8")
    logger_instance = Unbuffered(log_file)
    sys.stdout = logger_instance
    sys.stderr = logger_instance # Compartilha o mesmo objeto/buffer
    print("[LAUNCHER] Logging system initialized (Memory Mirror).")
except Exception as e:
    pass 
# ---------------------

# Cores (Tema Dark Moderno)
COLORS = {
    'bg': '#0f172a',           # Slate 950 (Fundo Principal)
    'card': '#1e293b',         # Slate 800 (Fundo de Cartões)
    'text': '#f8fafc',         # Slate 50 (Texto Principal)
    'subtext': '#94a3b8',      # Slate 400 (Texto Secundário)
    'primary': '#38bdf8',      # Sky 400 (Azul Brilhante)
    'success': '#4ade80',      # Green 400 (Online)
    'warning': '#fbbf24',      # Amber 400 (Alerta)
    'danger': '#f87171',       # Red 400 (Erro)
    'terminal': '#020617',     # Deep Navy (Log)
    'terminal_fg': '#4ade80'   # Green 400 (Texto Log)
}

class ModernLauncher:
    def __init__(self, root):
        self.root = root  # <--- CORREÇÃO CRÍTICA
        
        # Carregar Versão do Projeto
        self.project_version = "Unknown"
        self.python_req = "Unknown"
        try:
            with open(".project_version", "r") as f:
                for line in f:
                    if "PROJECT_NAME" in line: self.project_name = line.split('=')[1].strip().strip('"')
                    if "PYTHON_VERSION_REQUIRED" in line: self.python_req = line.split('=')[1].strip().strip('"')
        except: pass

        self.root.title(f"ISP Monitor | by: Diego")
        
        # Configuração de Janela Inteligente
        self.center_window(700, 600)
        self.root.minsize(600, 500)
        self.root.configure(bg=COLORS['bg'])
        
        # Estado
        self.is_running = False
        self.is_starting = False # Flag para evitar falsos positivos no startup
        self.process = None
        self.should_be_running = False # Monitoramento de auto-cura
        self.restart_attempts = 0
        self.child_processes = []  # Rastrear PIDs dos processos criados

        # Estilos Customizados
        self.setup_styles()
        
        # Construir Interface
        self.create_widgets()
        
        # Loop de Verificação de Status
        self.check_status_loop()
        
        # Loop de Auto-Update de Logs
        self.update_logs_loop()

        # Handle Exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 🛡️ Auto-Check: Banco de Dados na inicialização
        self.root.after(1000, self.check_and_recover_postgres)

    def check_and_recover_postgres(self):
        """Verifica se o PostgreSQL está rodando e tenta iniciar se necessário"""
        service_name = "postgresql-x64-17" 
        try:
            # 1. Verifica status via PowerShell
            cmd = f'powershell "Get-Service {service_name} | Select -ExpandProperty Status"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
            status = result.stdout.strip()
            
            if "Running" not in status:
                print(f"[DB WARN] PostgreSQL ({service_name}) não está rodando. Status: {status}")
                
                # 2. Tenta Iniciar (Requer Admin, mas tentamos 'net start')
                subprocess.run(f"net start {service_name}", shell=True, creationflags=0x08000000)
                
                # 3. Re-verifica
                time.sleep(2)
                result_retry = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=0x08000000)
                if "Running" not in result_retry.stdout:
                    messagebox.showerror("ERRO CRÍTICO: Banco de Dados", 
                        f"O serviço de Banco de Dados '{service_name}' está PARADO e não conseguimos iniciar automaticamente.\n\n"
                        "⚠️ O SISTEMA (MOBILE/BACKEND) VAI FALHAR SEM ISSO.\n\n"
                        "COMO RESOLVER:\n"
                        "🔹 Opção A: Abra o 'Menu Iniciar' -> 'Serviços' -> Inicie o '{service_name}'.\n"
                        "🔹 Opção B: Feche este programa e execute-o como ADMINISTRADOR.")
        except Exception as e:
            print(f"[Check DB Error] {e}")

    def on_close(self):
        """Limpa logs e fecha"""
        if self.is_running:
            try:
                self.stop_system()
            except: pass
        
        # Limpar logs ao fechar
        try:
            log_files = [
                "startup.log",
                os.path.join("logs", "api.log"),
                os.path.join("logs", "collector.log"),
                os.path.join("logs", "frontend.log")
            ]
            for lf in log_files:
                if os.path.exists(lf):
                     # Truncate ao invés de delete para evitar lock errors se ainda tiver processo zumbi
                    try: open(lf, 'w').close()
                    except: pass
        except: pass

        self.root.destroy()
        sys.exit(0)

    def center_window(self, width, height):
        """Centraliza janela na tela"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_styles(self):
        """Configura estilos modernos para widgets TTK"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar TNotebook (Abas) - Padding reduzido
        style.configure("TNotebook", background=COLORS['bg'], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS['card'], foreground=COLORS['text'], 
                       padding=[10, 5], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", COLORS['primary'])], 
                 foreground=[("selected", "#ffffff")])
        
        # Configurar Frames
        style.configure("Card.TFrame", background=COLORS['card'], relief="flat")
        
    def create_widgets(self):
        # Container Principal
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cabeçalho
        header = tk.Frame(main_container, bg=COLORS['bg'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        # Título e Subtítulo
        title_frame = tk.Frame(header, bg=COLORS['bg'])
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(
            title_frame, text="ISP MONITOR", font=("Inter", 24, "bold"), 
            bg=COLORS['bg'], fg=COLORS['primary']
        ).pack(anchor="w")
        
        tk.Label(
            title_frame, text="Network Intelligence | by: Diego", font=("Inter", 10, "italic"), 
            bg=COLORS['bg'], fg=COLORS['subtext']
        ).pack(anchor="w", padx=2)
        
        # Status Badge com estilo de pílula
        status_container = tk.Frame(header, bg=COLORS['bg'])
        status_container.pack(side=tk.RIGHT, pady=5)

        self.status_badge = tk.Label(
            status_container, text="● OFFLINE", font=("Inter", 10, "bold"), 
            bg=COLORS['bg'], fg=COLORS['danger'], padx=10, pady=5
        )
        self.status_badge.pack()

        # Sistema de Abas
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 1. Aba Home (Principal)
        self.tab_home = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_home, text="  🏠 PRINCIPAL  ")
        
        # 2. Aba Logs System
        self.tab_logs = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_logs, text="  📝 LOGS  ")
        
        # Construir Conteúdo das Abas
        self.build_home_tab(self.tab_home)
        self.build_logs_tab(self.tab_logs)

        # Rodapé Global
        self.info_label = tk.Label(main_container, text="Sistema pronto.", font=("Inter", 9), bg=COLORS['bg'], fg=COLORS['subtext'])
        self.info_label.pack(side=tk.BOTTOM, pady=5)

    def build_home_tab(self, parent):
        """Aba Principal: Design Otimizado (Grid)"""
        force_frame = tk.Frame(parent, bg=COLORS['bg'])
        force_frame.pack(expand=True, fill=tk.BOTH, padx=25, pady=25)

        # 1. Grid Configuration
        force_frame.columnconfigure(0, weight=1)
        force_frame.columnconfigure(1, weight=1)

        # --- STATUS HEADER ---
        self.frontend_frame = tk.Frame(force_frame, bg=COLORS['card'], padx=10, pady=8)
        self.frontend_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        lbl_fe = tk.Label(self.frontend_frame, text="Status Web:", font=("Inter", 9, "bold"), bg=COLORS['card'], fg=COLORS['text'])
        lbl_fe.pack(side=tk.LEFT)
        
        self.btn_update_front = tk.Button(self.frontend_frame, text="✔ Sistema Atualizado", 
                                          command=self.run_frontend_build_manual,
                                          bg=COLORS['card'], fg=COLORS['success'], relief="flat", state="disabled", font=("Inter", 8))
        self.btn_update_front.pack(side=tk.RIGHT)

        # --- BOTÃO PRINCIPAL (START) ---
        self.btn_start = self.create_button(force_frame, "▶  INICIAR SISTEMA", self.start_system, 
                                          bg=COLORS['success'], fg='#0f172a', height=2, font=("Inter", 13, "bold"))
        self.btn_start.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        self.btn_stop = self.create_button(force_frame, "⏹  PARAR SISTEMA", self.stop_system, 
                                         bg='#334155', fg=COLORS['danger'], height=1)
        self.btn_stop.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        # --- AÇÕES SECUNDÁRIAS (GRID) ---
        
        # Linha 1: Navegador e Atualizar
        btn_dash = self.create_button(force_frame, "🌐 Abrir Site (Produção)", self.open_dashboard, bg=COLORS['primary'], fg='#0f172a')
        btn_dash.grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=5)
        
        self.btn_update = self.create_button(force_frame, "⬇  Atualizar", self.update_system, bg='#0ea5e9', fg='#0f172a')
        self.btn_update.grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=5)
 
        # Linha 2: Mobile e Ngrok
        btn_mobile = self.create_button(force_frame, "📱 Mobile (Expo)", self.start_expo, bg='#a855f7', fg='#ffffff')
        btn_mobile.grid(row=4, column=0, sticky="ew", padx=(0, 5), pady=5)
        
        btn_ngrok = self.create_button(force_frame, "🌍 Acesso Externo", self.start_ngrok, bg='#10b981', fg='#0f172a')
        btn_ngrok.grid(row=4, column=1, sticky="ew", padx=(5, 0), pady=5)

        # Linha 3: Modo Edição
        self.btn_dev_mode = self.create_button(force_frame, "⚡ Modo Edição", self.start_dev_mode, bg='#f59e0b', fg='#0f172a')
        self.btn_dev_mode.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
 
        # Linha 4: Reiniciar
        self.btn_restart = self.create_button(force_frame, "🔄  Reiniciar Serviços", self.restart_system, bg=COLORS['warning'], fg='#0f172a')
        self.btn_restart.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(5, 15))
        
        # --- RODAPÉ: BOTÃO DE EMERGÊNCIA REESTILIZADO ---
        self.btn_kill = self.create_button(force_frame, "💀 Force Kill (Emergência)", self.force_kill, bg='#2d1a1a', fg='#fca5a5', height=1)
        self.btn_kill.config(font=("Inter", 9, "bold"))
        self.btn_kill.grid(row=7, column=0, columnspan=2, pady=(15, 0))
        
        # Start background check
        threading.Thread(target=self.check_frontend_updates_async, daemon=True).start()

    def start_ngrok(self):
        """Inicia Ngrok e mostra QR Code"""
        # Usa domínio fixo para bater com a configuração do App Mobile
        domain = "uniconoclastic-addedly-yareli.ngrok-free.dev"
        cmd = f"npx ngrok http --domain={domain} 8080 --log=stdout"
        self.open_console_window("🌍 Acesso Externo (Ngrok)", cmd, ".", qr_mode=True)

    def start_expo(self):
        """Inicia Expo e mostra QR Code"""
        if not os.path.exists("mobile"): 
             messagebox.showerror("Erro", "Pasta mobile não encontrada.")
             return
        # --no-interactive removido (causa erro), controlado por env CI=1
        self.open_console_window("📱 Mobile Expo", "npx expo start --offline --go", "mobile", qr_mode=True)

    def open_console_window(self, title, cmd, cwd, qr_mode=False):
        """Janela flutuante com Log e QR Code (Gerenciada)"""
        
        # 1. Verifica se já existe janela ativa com este título
        if not hasattr(self, 'active_consoles'): self.active_consoles = {}
        
        if title in self.active_consoles:
            existing_win = self.active_consoles[title]
            if existing_win.winfo_exists():
                existing_win.deiconify() # Traz de volta se estiver oculta
                existing_win.lift()      # Traz para frente
                return
            else:
                del self.active_consoles[title] # Limpa referência morta

        # 2. Cria Nova Janela
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("900x600")
        win.configure(bg=COLORS['bg'])
        
        # Registra janela
        self.active_consoles[title] = win

        # ... (Resto da UI igual) ...

        # Header
        tk.Label(win, text=title, font=("Segoe UI", 14, "bold"), bg=COLORS['bg'], fg="white").pack(pady=10)
        
        if "Ngrok" in title:
            tk.Label(win, text="⚠️ IMPORTANTE: Mantenha a janela 'Mobile (Expo)' aberta!", font=("Segoe UI", 10), bg=COLORS['bg'], fg='#ffcc00').pack(pady=(0, 10))
        
        container = tk.Frame(win, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Log (Esquerda)
        log_frame = tk.Frame(container, bg="#0c0c0c", relief="sunken", bd=1)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_log = tk.Text(log_frame, bg="#0c0c0c", fg="#ccc", font=("Consolas", 10), state="disabled", relief="flat")
        text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        sb = tk.Scrollbar(text_log)
        text_log.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        sb.config(command=text_log.yview)

        # QR Code (Direita)
        lbl_qr_img = None
        lbl_qr_text = None
        
        if qr_mode:
            qr_frame = tk.Frame(container, bg=COLORS['bg'], width=320)
            qr_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
            qr_frame.pack_propagate(False)
            
            tk.Label(qr_frame, text="ESCANEIE PARA CONECTAR", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['primary']).pack(pady=(0, 20))
            
            qr_bg = tk.Frame(qr_frame, bg="white", padx=10, pady=10, bd=2, relief="solid")
            qr_bg.pack()
            
            lbl_qr_img = tk.Label(qr_bg, bg="white")
            lbl_qr_img.pack()
            
            lbl_qr_text = tk.Label(qr_frame, text="Aguardando Link...", bg=COLORS['bg'], fg="#aaa", font=("Consolas", 9), wraplength=280, justify="center")
            lbl_qr_text.pack(pady=20, fill=tk.X)

        def run_thread():
            proc = None
            try:
                env = os.environ.copy()
                # CI=1 quebra o Expo Interativo/QR Code. Remover se for expo.
                if "expo" not in cmd:
                    env["CI"] = "1"
                env["NO_COLOR"] = "1"
                
                creation_flags = 0x08000000 if os.name == 'nt' else 0
                proc = subprocess.Popen(cmd, shell=True, cwd=cwd, 
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                      stdin=subprocess.PIPE, text=True, env=env, bufsize=1,
                                      creationflags=creation_flags)
                win.proc = proc

                for line in iter(proc.stdout.readline, ''):
                    if not line: break
                    line = line.strip()
                    if not line: continue
                    
                    def up_log(l):
                        text_log.config(state="normal")
                        text_log.insert(tk.END, l + "\n")
                        text_log.see(tk.END)
                        text_log.config(state="disabled")
                    
                    try: self.root.after(0, up_log, line)
                    except: pass 

                    # Detect Ngrok Auth Error
                    if "ERR_NGROK_4018" in line:
                         def ask_token():
                             if messagebox.askyesno("Autenticação Necessária", "O Ngrok requer um token gratuito.\nDeseja configurar agora?"):
                                 token = simpledialog.askstring("Ngrok Token", "Cole seu Aunthentication Token aqui:\n(dashboard.ngrok.com)")
                                 if token:
                                     subprocess.run(f"npx ngrok config add-authtoken {token}", shell=True, creationflags=0x08000000)
                                     messagebox.showinfo("Sucesso", "Token salvo! Feche a janela e tente de novo.")
                         self.root.after(0, ask_token)

                    if qr_mode:
                        found = None
                        
                        # Expo Fallback
                        if "Waiting on http://localhost:8081" in line:
                             try:
                                 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                 s.connect(("8.8.8.8", 80))
                                 my_ip = s.getsockname()[0]
                                 s.close()
                                 found = f"exp://{my_ip}:8081"
                                 def log_force(u):
                                     text_log.config(state="normal")
                                     text_log.insert(tk.END, f"\n[AUTO-DETECT] Gerando QR Code para: {u}\n")
                                     text_log.see(tk.END)
                                     text_log.config(state="disabled")
                                 self.root.after(0, log_force, found)
                             except: pass

                        if "exp://" in line:
                            found = "exp://" + line.split("exp://")[1].split()[0]
                        
                        # Detecção Genérica de Ngrok (.app, .dev, etc)
                        elif "ngrok" in line and "https://" in line:
                            parts = line.split()
                            for p in parts: 
                                if "https://" in p and "ngrok" in p: 
                                    # Limpa prefixos 'url=' se houver
                                    clean_url = p.replace("url=", "").strip()
                                    # Converte https:// -> exp:// para o Expo Go abrir direto
                                    found = clean_url.replace("https://", "exp://")
                        
                        if found:
                            found = found.replace('│', '').strip()
                            def up_qr(u):
                                if lbl_qr_img:
                                    try:
                                        img = qrcode.make(u)
                                        img = img.resize((220, 220))
                                        tk_img = ImageTk.PhotoImage(img)
                                        lbl_qr_img.config(image=tk_img)
                                        lbl_qr_img.image = tk_img 
                                        lbl_qr_text.config(text=u, fg="white")
                                    except: pass
                            try: self.root.after(0, up_qr, found)
                            except: pass

            except Exception as e:
                print(e)

        def on_destroy():
            # Pergunta inteligente
            action = messagebox.askyesnocancel("Gerenciador de Janelas", 
                                             "Deseja ENCERRAR este processo?\n\n"
                                             "✅ SIM: Para o processo e fecha a janela.\n"
                                             "🙈 NÃO: Apenas oculta a janela (continua rodando em background).")
            
            if action is None: return # Cancelou

            if action is False: # Clicou em NÃO -> Ocultar
                win.withdraw()
                return

            # Clicou em SIM -> Matar processo
            if hasattr(win, 'proc') and win.proc:
                subprocess.run(f"taskkill /F /PID {win.proc.pid} /T", shell=True)
            
            # Limpa referência da lista
            if hasattr(self, 'active_consoles') and title in self.active_consoles:
                del self.active_consoles[title]
                
            win.destroy()
            
        win.protocol("WM_DELETE_WINDOW", on_destroy)
        threading.Thread(target=run_thread, daemon=True).start() 


    def check_frontend_updates_async(self):
        """Verifica atualizações em background sem travar UI"""
        try:
            current = self.calculate_frontend_hash()
            
            hash_file = os.path.join("frontend", ".build_hash")
            saved = ""
            if os.path.exists(hash_file):
                with open(hash_file, "r") as f: saved = f.read().strip()
            
            if current != saved:
                self.root.after(0, self.notify_update_available)
        except: pass

    def notify_update_available(self):
        """Atualiza UI para avisar que precisa de build"""
        self.btn_update_front.config(text="⚠ Atualização Disponível (Clique p/ Compilar)", 
                                     bg=COLORS['warning'], fg='#1e1e2e', state="normal", cursor="hand2")

    def run_frontend_build_manual(self):
        current = self.calculate_frontend_hash()
        hash_file = os.path.join("frontend", ".build_hash")
        if self.run_frontend_build(current, hash_file):
            self.btn_update_front.config(text="✔ Sistema Atualizado", bg=COLORS['card'], fg=COLORS['success'], state="disabled")

    def update_system(self):
        """Chama o script de atualização externo (SETUP.bat)"""
        # Tenta encontrar o script em locais comuns
        # 1. Pasta pai (Instalação Padrão: C:\ISP-Monitor\SETUP.bat)
        # 2. Pasta atual (Desenvolvimento)
        possible_paths = [
            os.path.abspath(os.path.join(os.getcwd(), "..", "SETUP.bat")),
            os.path.abspath("SETUP.bat")
        ]
        
        update_script = None
        for path in possible_paths:
            if os.path.exists(path):
                update_script = path
                break
        
        if not update_script:
            messagebox.showerror("Erro de Atualização", "O script SETUP.bat não foi encontrado.\n\nVerifique se o sistema foi instalado corretamente.")
            return

        if messagebox.askyesno("Atualizar Sistema", "O sistema será fechado para baixar a nova versão do GitHub.\nIsso preservará seus dados e configurações.\n\nDeseja continuar?"):
            try:
                print(f"[LAUNCHER] Iniciando atualização via: {update_script}")
                # Executa o BAT em uma nova janela e fecha o Launcher
                subprocess.Popen(["start", "cmd", "/c", update_script], shell=True, cwd=os.path.dirname(update_script))
                
                # Para o sistema de forma limpa
                self.stop_system()
                self.root.quit()
            except Exception as e:
                messagebox.showerror("Erro Crítico", f"Falha ao iniciar o atualizador: {e}")

    def start_dev_mode(self):
        """Inicia servidor Vite para desenvolvimento rápido"""
        if self.is_running:
            if not messagebox.askyesno("Servidor Rodando", "O servidor de produção está rodando. Deseja parar ele para rodar o modo DEV?"):
                return
            self.stop_system()
            
        # Iniciar Backend (Sem frontend estático, apenas API)
        script = "iniciar_postgres.bat"
        if os.path.exists(script):
             subprocess.Popen([script], creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Iniciar Vite
        frontend_dir = os.path.join(os.getcwd(), "frontend")
        cmd = "start cmd /k npm run dev"
        subprocess.Popen(cmd, shell=True, cwd=frontend_dir)
        
        self.info_label.config(text="Modo DEV iniciado! API na 8000, Frontend na 5173.")



    def build_logs_tab(self, parent):
        """Constrói a aba de logs com Terminal"""
        # Toolbar
        toolbar = tk.Frame(parent, bg=COLORS['bg'])
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            toolbar, text="🔄 Atualizar Logs", 
            command=self.refresh_logs,
            bg=COLORS['card'], fg=COLORS['text'], relief="flat", padx=15, pady=5
        ).pack(side=tk.RIGHT)
        
        tk.Label(
            toolbar, text="Monitoramento de Processos (startup.log, api.log, collector.log)",
            bg=COLORS['bg'], fg=COLORS['subtext']
        ).pack(side=tk.LEFT, pady=5)
        
        # Terminal
        self.log_text = tk.Text(
            parent, bg=COLORS['terminal'], fg=COLORS['terminal_fg'],
            font=("Consolas", 10), relief="flat", padx=10, pady=10
        )
        scrollbar = tk.Scrollbar(parent, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tags
        self.log_text.tag_config("title", foreground=COLORS['primary'], font=("Consolas", 10, "bold"))
        self.log_text.tag_config("error", foreground=COLORS['danger'])
    


    def create_button(self, parent, text, command, bg, fg, font=("Inter", 11, "bold"), height=2):
        """Helper para criar botões com visual premium"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief=tk.FLAT, cursor="hand2",
            activebackground=bg, activeforeground=fg,
            height=height,
            padx=20,
            borderwidth=0,
            highlightthickness=0
        )
        
        # Armazena a cor base para o hover
        btn.original_bg = bg
        
        def on_enter(e):
            if btn['state'] == tk.NORMAL:
                btn.config(background=self.get_darker_color(btn.original_bg))
        
        def on_leave(e):
            if btn['state'] == tk.NORMAL:
                btn.config(background=btn.original_bg)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def set_button_state(self, btn, state, active_bg=None, active_fg='#0f172a'):
        """Helper para atualizar estado e cor de um botão de forma segura"""
        if state == tk.NORMAL:
            btn.original_bg = active_bg
            btn.config(state=tk.NORMAL, bg=active_bg, fg=active_fg, cursor="hand2")
        else:
            btn.config(state=tk.DISABLED, bg='#1e293b', fg='#475569', cursor="arrow")

    def get_darker_color(self, hex_color):
        """Calcula uma versão ligeiramente mais escura da cor para o hover"""
        try:
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            darker_rgb = tuple(max(0, int(c * 0.85)) for c in rgb)
            return '#%02x%02x%02x' % darker_rgb
        except:
            return hex_color

    # --- LÓGICA DO SISTEMA ---

    def check_status_loop(self):
        self.check_status()
        self.root.after(3000, self.check_status_loop) # Mais frequente (3s)

    def update_logs_loop(self):
        """Auto-atualiza os logs se estiver na aba de logs"""
        try:
            current_tab = self.notebook.index(self.notebook.select())
            if current_tab == 1:
                # Verifica se o tamanho dos arquivos mudou antes de atualizar para evitar flicker
                total_size = 0
                log_paths = ["startup.log", "logs/api.log", "logs/collector.log", "logs/frontend.log", "logs/whatsapp.log", "logs/self_heal.log"]
                for p in log_paths:
                    if os.path.exists(p): total_size += os.path.getsize(p)
                
                # Se mudou o tamanho, ou se é a primeira vez, atualiza
                if not hasattr(self, 'last_log_size') or self.last_log_size != total_size:
                    self.refresh_logs()
                    self.last_log_size = total_size
        except:
            pass
        self.root.after(2000, self.update_logs_loop) # A cada 2 segundos

    def check_status(self):
        """Verifica se API está rodando na porta 8080"""
        try:
            # 1. Check Port 8080
            is_up = False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                result = sock.connect_ex(('127.0.0.1', 8080))
                if result == 0:
                    is_up = True
                sock.close()
            except:
                is_up = False
            
            # Update main status
            if self.is_running != is_up:
                self.is_running = is_up
                if is_up:
                    self.status_badge.config(text=" ● ONLINE ", fg=COLORS['success'], highlightbackground=COLORS['success'])
                    self.set_button_state(self.btn_start, tk.DISABLED)
                    self.set_button_state(self.btn_stop, tk.NORMAL, active_bg=COLORS['danger'], active_fg='#ffffff')
                    self.info_label.config(text="✓ Sistema operando normalmente na porta 8080")
                else:
                    self.status_badge.config(text=" ● OFFLINE ", fg=COLORS['danger'], highlightbackground=COLORS['danger'])
                    self.set_button_state(self.btn_start, tk.NORMAL, active_bg=COLORS['success'])
                    self.set_button_state(self.btn_stop, tk.DISABLED)
                    self.info_label.config(text="⚠ Sistema parado. Clique em INICIAR para começar.")
        except Exception as e:
            pass




    def start_system(self):
        if self.is_running: return
        
        self.should_be_running = True
        self.restart_attempts = 0 # Reset ao iniciar manual
        
        # --- CLEANUP PREVENTIVO (Matar processos zumbis) ---
        print("[LAUNCHER] Executando limpeza de processos órfãos...")
        try:
            my_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == my_pid: continue # Não suicidar
                    
                    name = proc.info.get('name', '').lower()
                    cmd = ' '.join(proc.info.get('cmdline') or []).lower()
                    
                    # Alvos: Collector, API, Self-Heal, ou Launchers antigos
                    targets = ['collector.py', 'uvicorn', 'self_heal.py', 'launcher.py']
                    
                    if ('python' in name or 'pythonw' in name):
                        for target in targets:
                            if target in cmd:
                                logger_instance.write(f"[CLEANUP] Matando processo zumbi {proc.info['pid']}: {target}\n")
                                proc.kill()
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            print(f"[LAUNCHER] Erro no cleanup: {e}")
        time.sleep(1) # Aguardar OS liberar recursos
        
        # --- AUTO-FIX: GARANTIR ESTRUTURA DE LOGS ---
        log_dir = "logs"
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                print(f"[LAUNCHER] Diretório '{log_dir}' recriado automaticamente.")
            except: pass

        # RESET LOGS (Limpar logs antigos fisicamente)
        log_files = [
            "startup.log",
            os.path.join(log_dir, "api.log"),
            os.path.join(log_dir, "collector.log"),
            os.path.join(log_dir, "frontend.log"),
            os.path.join(log_dir, "whatsapp.log"),
            os.path.join(log_dir, "snmp.log"),
            os.path.join(log_dir, "self_heal.log")
        ]
        
        for lf in log_files:
            try:
                if os.path.exists(lf):
                    with open(lf, 'w', encoding='utf-8') as f:
                        f.truncate(0)
            except: pass
        
        # Limpar terminal na UI
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")

        # --- DOCTOR CHECKUP ---
        # Roda verificações proativas (Otimização DB, etc)
        try:
            from backend.doctor import checkup
            # Roda checkup em thread separada para não travar UI? 
            # Como é rápido, pode ser aqui. Mas se precisar de admin, vai aparecer no console.
            # O ideal seria mostrar na UI, mas por enquanto console serve.
            checkup.run_system_checkup()
        except Exception as e:
            print(f"[LAUNCHER] Erro no checkup: {e}")
        # ----------------------
        
        # Verificar Frontend antes de iniciar (Removido - Agora é Async)
        # if not self.check_and_rebuild_frontend():
        #      return

        # Database Init (Direct Python - Silent)
        try:
            # Executa inicialização do banco diretamente via Python (sem janelas .bat)
            db_cmd = [
                sys.executable, "-c", 
                "from backend.app.database import init_db; import asyncio; asyncio.run(init_db())"
            ]
            
            # Garante diretório de logs
            if not os.path.exists("logs"): os.makedirs("logs")
            
            # Redireciona log
            log_f = open("logs/db_init.log", "w")
            proc = subprocess.Popen(db_cmd, creationflags=0x08000000, stdout=log_f, stderr=subprocess.STDOUT)
            self.child_processes.append(proc)  # Rastrear processo
            
            # Switch to logs tab
            self.notebook.select(1)
            self.refresh_logs()
            
            # Feedback
            self.info_label.config(text="Iniciando... (Aguarde 5-10s)")
            self.status_badge.config(text=" ● INICIANDO ", fg=COLORS['warning'])

            # Lançar Doctor V4.0 (O Mestre de Cerimônias)
            my_pid = os.getpid()
            python_exe = sys.executable
            doctor_cmd = [python_exe, "scripts/self_heal.py", str(my_pid)]
            subprocess.Popen(doctor_cmd, creationflags=0x08000000)
            print(f"[LAUNCHER] Doctor V4.0 Guardião Supremo iniciado (Monitorando PID {my_pid}).")
            
            # Pequeno delay para os arquivos de log serem liberados pelo OS
            time.sleep(1)
            
            # Aguardar e verificar com flag de proteção
            self.is_starting = True
            try:
                self.wait_for_start()
            finally:
                self.is_starting = False # Libera monitoramento de crash
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            
    def force_kill(self):
        """Limpeza AGRESSIVA de todos os processos (Botão de Emergência)"""
        if not messagebox.askyesno("⚠ FORCE KILL", 
            "Isso vai MATAR TODOS os processos do sistema:\n\n"
            "• Node.js (WhatsApp)\n"
            "• Python (Backend/Launcher)\n"
            "• PostgreSQL (Banco)\n\n"
            "Use apenas se algo travou.\n\n"
            "Deseja continuar?"):
            return
        
        self.info_label.config(text="🔥 FORCE KILL em andamento...")
        self.root.update()
        
        try:
            print("[FORCE KILL] Executando limpeza agressiva...")
            
            # 1. Taskkill padrão
            creation_flags = 0x08000000
            subprocess.run("taskkill /F /IM node.exe /T", shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run("taskkill /F /IM python.exe /T", shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run("taskkill /F /IM pythonw.exe /T", shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run("taskkill /F /IM postgres.exe /T", shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run("taskkill /F /IM conhost.exe /T", shell=True, capture_output=True, creationflags=creation_flags)
            
            # 2. WMIC para processos órfãos (força bruta)
            subprocess.run('wmic process where "name=\'node.exe\'" delete', shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run('wmic process where "name=\'python.exe\'" delete', shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run('wmic process where "name=\'pythonw.exe\'" delete', shell=True, capture_output=True, creationflags=creation_flags)
            subprocess.run('wmic process where "name=\'conhost.exe\'" delete', shell=True, capture_output=True, creationflags=creation_flags)
            
            print("[FORCE KILL] Limpeza completa.")
            
            self.info_label.config(text="✅ FORCE KILL concluído. Arquivos liberados.")
            self.status_badge.config(text=" ● OFFLINE ", fg=COLORS['danger'])
            self.is_running = False
            self.whatsapp_running = False
            
            messagebox.showinfo("Sucesso", 
                "Todos os processos foram eliminados.\n\n"
                "Você pode iniciar o sistema novamente.")
            
        except Exception as e:
            print(f"[FORCE KILL] Erro: {e}")
            messagebox.showerror("Erro", f"Erro ao executar Force Kill:\n{e}")
            
    # --- SMART BUILD SYSTEM ---
    
    def calculate_frontend_hash(self):
        """Calcula hash do diretório src do frontend"""
        import hashlib
        src_path = os.path.join("frontend", "src")
        total_hash = hashlib.md5()
        
        if not os.path.exists(src_path):
            return "0"
            
        for root, dirs, files in os.walk(src_path):
            files.sort() # Garantir ordem
            for file in files:
                if file.endswith(('.tsx', '.ts', '.css', '.html')):
                    file_path = os.path.join(root, file)
                    try:
                        # Hash do caminho + mtime + size (muito rápido)
                        stat = os.stat(file_path)
                        info = f"{file_path}{stat.st_mtime}{stat.st_size}".encode()
                        total_hash.update(info)
                    except: pass
                    
        return total_hash.hexdigest()

    def check_and_rebuild_frontend(self):
        """Verifica se precisa rebuildar o frontend"""
        # Se nao tiver npm (node), nao tenta
        try:
           subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=0x08000000)
        except:
           return True # Pula se nao tiver node

        hash_file = os.path.join("frontend", ".build_hash")
        current_hash = self.calculate_frontend_hash()
        saved_hash = ""
        
        if os.path.exists(hash_file):
            try:
                with open(hash_file, "r") as f:
                    saved_hash = f.read().strip()
            except: pass
            
        if current_hash != saved_hash:
            # Precisa rebuildar
            msg = "Alterações detectadas no Frontend!\nO sistema precisa atualizar a interface.\n\nIsso levará alguns segundos.\nDeseja atualizar agora?"
            if messagebox.askyesno("Atualização Automática", msg):
                return self.run_frontend_build(current_hash, hash_file)
            else:
                return True # Continua com versao antiga se usuario negar
        return True

    def run_frontend_build(self, new_hash, hash_file):
        """Build inteligente diretamente no botão da interface (sem popup)"""
        
        # Configuração inicial do estado de progresso no botão
        self.btn_update_front.config(state="disabled", text="🔨 Iniciando Build...")
        self.root.update()
        
        success = False
        error_msg = ""
        
        def update_button_progress(percent, message):
            """Atualiza o texto do botão de forma thread-safe"""
            try:
                # Texto resumido para caber no botão
                percent_int = int(percent)
                self.btn_update_front.config(text=f"🔨 {percent_int}% - {message}")
                self.root.update()
            except:
                pass
        
        def run_build():
            nonlocal success, error_msg
            try:
                frontend_dir = os.path.join(os.getcwd(), "frontend")
                
                # Verificar se npm existe
                try:
                    subprocess.run(["npm", "--version"], capture_output=True, shell=True, creationflags=0x08000000)
                except:
                    error_msg = "Node.js/NPM não encontrado no sistema!"
                    return
                
                update_button_progress(5, "Verificando...")
                
                # Executar build
                process = subprocess.Popen(
                    "npm run build", 
                    shell=True, 
                    cwd=frontend_dir,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,
                    universal_newlines=True,
                    bufsize=1
                )
                
                progress = 10
                update_button_progress(progress, "Compilando...")
                output_lines = []
                
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    
                    output_lines.append(line)
                    line_lower = line.lower()
                    
                    # Detectar etapas do Vite e traduzir/simplificar para o botão
                    if 'vite' in line_lower and 'building' in line_lower:
                        progress = 20
                        update_button_progress(progress, "Vite...")
                    elif 'transforming' in line_lower or 'transform' in line_lower:
                        progress = min(progress + 0.5, 70) # Incremento lento para parecer fluido
                        update_button_progress(progress, "Processando...")
                    elif 'rendering' in line_lower or 'render' in line_lower:
                        progress = min(progress + 5, 85)
                        update_button_progress(progress, "Renderizando...")
                    elif 'computing' in line_lower or 'chunk' in line_lower:
                        progress = min(progress + 5, 95)
                        update_button_progress(progress, "Otimizando...")
                
                process.wait()
                
                if process.returncode == 0:
                    update_button_progress(100, "Concluído!")
                    # Salvar novo hash
                    with open(hash_file, "w") as f:
                        f.write(new_hash)
                    success = True
                else:
                    error_msg = f"Build falhou (Erro {process.returncode}).\n\nConfira os logs ou tente novamente."
                    
            except Exception as e:
                error_msg = f"Erro no build:\n{str(e)}"
        
        # Executar build em thread para manter a interface responsiva
        build_thread = threading.Thread(target=run_build, daemon=True)
        build_thread.start()
        
        # Loop de espera na UI principal
        while build_thread.is_alive():
            self.root.update()
            time.sleep(0.1)
        
        # Resultado Final
        if success:
            self.btn_update_front.config(text="✔ Sistema Atualizado", bg=COLORS['card'], fg=COLORS['success'], state="disabled")
            messagebox.showinfo("Sucesso", "Interface do usuário atualizada com sucesso!")
        else:
            # Em caso de erro, permitir tentar novamente
            self.btn_update_front.config(text="❌ Erro (Tentar Novamente)", bg=COLORS['danger'], fg='white', state="normal", cursor="hand2")
            if error_msg:
                messagebox.showerror("Erro de Compilação", error_msg)
        
        return success

        
    def wait_for_start(self):
        """Aguarda inicialização verificando logs"""
        for _ in range(60): # Aumentado para 60s para dar tempo ao Doctor V4.0
            self.refresh_logs()
            self.check_status()
            if self.is_running:
                messagebox.showinfo("Sucesso", "Sistema Iniciado!")
                self.notebook.select(0) # Voltar pro controle
                return
            self.root.update()
            time.sleep(1)
        
        messagebox.showwarning("Timeout", "O sistema demorou a responder.\nIsso é comum se o banco de dados estiver iniciando ou o Doctor estiver limpando processos zumbis.\n\nVerifique a aba de LOGS para acompanhar a evolução.")

    def stop_system(self):
        """Mata API, Coletor e processos relacionados"""
        self.should_be_running = False 
        killed = []
        try:
            my_pid = os.getpid()
            
            # --- PASSO 1: MATAR O DOCTOR PRIMEIRO ---
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline') or []).lower()
                    if 'self_heal.py' in cmdline and proc.info['pid'] != my_pid:
                        proc.kill()
                        killed.append("Doctor")
                except: pass

            time.sleep(0.5)

            # --- PASSO 2: MATAR OS OUTROS SERVIÇOS ---
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == my_pid: continue
                    proc_name = proc.info.get('name', '').lower()
                    cmdline = ' '.join(proc.info.get('cmdline') or []).lower()
                    
                    should_kill = False
                    reason = ""
                    if 'pinger_fast' in cmdline:
                        should_kill = True
                        reason = "Coletor (Pinger)"
                    elif 'snmp_monitor' in cmdline:
                        should_kill = True
                        reason = "SNMP Monitor"
                    elif (proc_name == 'node.exe' or proc_name == 'node') and ('server.js' in cmdline or 'vite' in cmdline):
                        should_kill = True
                        reason = "Frontend/WhatsApp"
                    elif 'uvicorn' in cmdline and '8080' in cmdline:
                        should_kill = True
                        reason = "API (Uvicorn)"
                    elif 'postgres.exe' in cmdline or 'pg_ctl' in cmdline:
                        if 'isp_monitor' in cmdline or 'data' in cmdline:
                            should_kill = True
                            reason = "PostgreSQL"
                    
                    if should_kill:
                        proc.kill()
                        killed.append(reason)
                except: pass
            
            self.child_processes.clear()
            time.sleep(1)
            self.check_status()
        
            if killed:
                # messagebox.showinfo("Sucesso", f"O sistema foi parado.\nEncerramos: {', '.join(set(killed))}")
                self.info_label.config(text=f"Sistema parado. Encerrados: {', '.join(set(killed))}", fg=COLORS['warning'])
            else:
                # messagebox.showinfo("Info", "Nenhum processo ativo encontrado.")
                self.info_label.config(text="Nenhum processo ativo encontrado.", fg=COLORS['subtext'])
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def force_kill(self):
        if messagebox.askyesno("Kill Forçado", "Isso vai encerrar TODOS os processos Python/Postgres relacionados.\nContinuar?"):
            try:
                subprocess.run("taskkill /F /IM python.exe /T", shell=True, capture_output=True, creationflags=0x08000000)
                # os.system("taskkill /F /IM postgres.exe /T") # Opcional, perigoso
                messagebox.showinfo("Kill", "Processos mortos. O launcher também fechará.")
                self.root.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def restart_system(self):
        if messagebox.askyesno("Reiniciar", "Reiniciar o sistema completo?"):
            self.stop_system()
            time.sleep(2)
            self.start_system()

    def open_dashboard(self):
        import webbrowser
        webbrowser.open("http://localhost:8080")



    
    def refresh_logs(self):
        """Atualiza logs do sistema"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        # Mapeamento: Nome Exibido -> Caminho Real
        # startup.log é especial (memória)
        log_files = {
            "STARTUP.LOG": "startup.log",
            "API.LOG": os.path.join("logs", "api.log"),
            "COLLECTOR.LOG": os.path.join("logs", "collector.log"),
            "FRONTEND.LOG": os.path.join("logs", "frontend.log"),
            "WHATSAPP.LOG": os.path.join("logs", "whatsapp.log"),
            "SNMP.LOG": os.path.join("logs", "snmp.log"),
            "SELF_HEAL.LOG": os.path.join("logs", "self_heal.log")
        }
        
        for display_name, real_path in log_files.items():
            self.log_text.insert(tk.END, f"\n┏━━ {display_name} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "title")
            
            if "startup.log" in real_path:
                try:
                    # Ler da memória para evitar conflito de File Lock
                    content = "".join(sys.stdout.log_data)
                    self.log_text.insert(tk.END, content if content else "[Aguardando logs...]\n")
                except:
                    self.log_text.insert(tk.END, "[Erro ao ler memória startup]\n", "error")
                continue

            if os.path.exists(real_path):
                try:
                    # Encoding UTF-8 (ignore errors) para suportar emojis
                    with open(real_path, "r", encoding="utf-8", errors="ignore") as f:
                        # Lê as últimas 1000 chars e pega as ultimas linhas para ser rapido
                        f.seek(0, 2) # Fim
                        size = f.tell()
                        f.seek(max(0, size - 4000), 0) # Ultimos 4KB
                        lines = f.readlines()
                        # Se leu do meio da linha, descarta a primeira
                        if len(lines) > 1 and size > 4000: lines.pop(0)
                        
                        self.log_text.insert(tk.END, "".join(lines) if lines else "[Arquivo Vazio]\n")
                except Exception as e:
                    self.log_text.insert(tk.END, f"[Erro ao ler: {e}]\n", "error")
            else:
                self.log_text.insert(tk.END, "[Aguardando inicio...]\n", "warning")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    



    def on_closing(self):
        """Handler para fechar a janela"""
        if messagebox.askokcancel("Sair", "Deseja realmente sair? O monitoramento será interrompido."):
            # Usar stop_system que já tem a lógica de limpeza
            self.stop_system()
            
            # Aguardar um pouco para garantir que processos morreram
            time.sleep(0.5)
            
            # Limpeza final agressiva (fallback)
            print("[LAUNCHER] Limpeza final...")
            try:
                subprocess.run("taskkill /F /IM node.exe /T", shell=True, capture_output=True, creationflags=0x08000000)
                subprocess.run('taskkill /F /IM conhost.exe /FI "WINDOWTITLE eq *postgres*"', shell=True, capture_output=True, creationflags=0x08000000)
                subprocess.run('taskkill /F /IM conhost.exe /FI "WINDOWTITLE eq *isp-monitor*"', shell=True, capture_output=True, creationflags=0x08000000)
            except:
                pass
            
            self.root.destroy()
            sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

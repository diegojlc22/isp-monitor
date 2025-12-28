
"""
ISP Monitor - Launcher v3.0 (Professional Edition)
Interface gráfica moderna e robusta para gerenciamento do sistema.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
import sys
import shutil
import psutil
import time
import threading
import qrcode
from PIL import Image, ImageTk
import socket
import requests

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
    'bg': '#1e1e2e',           # Fundo Principal
    'card': '#313244',         # Fundo de Cartões/Containers
    'text': '#cdd6f4',         # Texto Principal
    'subtext': '#a6adc8',      # Texto Secundário
    'primary': '#89b4fa',      # Azul (Acentos)
    'success': '#a6e3a1',      # Verde (Online/Start)
    'warning': '#f9e2af',      # Amarelo (Reiniciar)
    'danger': '#f38ba8',       # Vermelho (Parar/Kill)
    'terminal': '#11111b',     # Fundo do Log
    'terminal_fg': '#a6e3a1'   # Texto do Log
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

        self.root.title(f"ISP Monitor | Python {self.python_req} Edition")
        
        # Configuração de Janela Inteligente
        self.center_window(700, 600)
        self.root.minsize(600, 500)
        self.root.configure(bg=COLORS['bg'])
        
        # Estado
        self.is_running = False
        self.is_starting = False # Flag para evitar falsos positivos no startup
        self.should_be_running = False # Monitoramento de auto-cura
        self.process = None
        self.should_be_running = False 
        self.restart_attempts = 0
        self.expo_logs = []  # Armazenar logs do Expo
        self.child_processes = []  # Rastrear PIDs dos processos criados
        self.process_expo = None
        self.expo_running = False

        # Estilos Customizados
        self.setup_styles()
        
        # Construir Interface
        self.create_widgets()
        
        # Loop de Verificação
        self.check_status_loop()

        # Handle Exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
        
        tk.Label(
            header, text="ISP MONITOR", font=("Segoe UI", 20, "bold"), 
            bg=COLORS['bg'], fg=COLORS['primary']
        ).pack(side=tk.LEFT)
        
        self.status_badge = tk.Label(
            header, text="● OFFLINE", font=("Segoe UI", 10), 
            bg=COLORS['bg'], fg=COLORS['danger']
        )
        self.status_badge.pack(side=tk.RIGHT, pady=5)

        # Sistema de Abas
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 1. Aba Home (Principal)
        self.tab_home = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_home, text="  🏠 PRINCIPAL  ")
        
        # 2. Aba Mobile
        self.tab_mobile = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_mobile, text="  📱 MOBILE  ")

        # 3. Aba Logs System
        self.tab_logs = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_logs, text="  📝 LOGS  ")
        
        # 4. Aba Logs Expo
        self.tab_expo_logs = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_expo_logs, text="  DEBUG APP  ")

        # Construir Conteúdo das Abas
        self.build_home_tab(self.tab_home)
        self.build_mobile_tab(self.tab_mobile)
        self.build_logs_tab(self.tab_logs)
        self.build_expo_logs_tab(self.tab_expo_logs)

        # Rodapé Global
        self.info_label = tk.Label(main_container, text="Sistema pronto.", font=("Segoe UI", 9), bg=COLORS['bg'], fg=COLORS['subtext'])
        self.info_label.pack(side=tk.BOTTOM, pady=5)

    def build_home_tab(self, parent):
        """Aba Principal: Controles do Sistema"""
        force_frame = tk.Frame(parent, bg=COLORS['bg'])
        force_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # --- STATUS DO FRONTEND ---
        self.frontend_frame = tk.Frame(force_frame, bg=COLORS['card'], padx=10, pady=5)
        self.frontend_frame.pack(fill=tk.X, pady=(0, 15))
        
        lbl_fe = tk.Label(self.frontend_frame, text="Interface Web:", font=("Segoe UI", 10, "bold"), bg=COLORS['card'], fg=COLORS['text'])
        lbl_fe.pack(side=tk.LEFT)
        
        self.btn_update_front = tk.Button(self.frontend_frame, text="✔ Sistema Atualizado", 
                                          command=self.run_frontend_build_manual,
                                          bg=COLORS['card'], fg=COLORS['success'], relief="flat", state="disabled", font=("Segoe UI", 9))
        self.btn_update_front.pack(side=tk.RIGHT)

        # --- CONTROLES GERAIS ---
        tk.Label(force_frame, text="Controle do Servidor", font=("Segoe UI", 12, "bold"), bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(0,10))

        self.btn_start = self.create_button(force_frame, "▶ INICIAR SERVIDOR (Prod)", self.start_system, bg=COLORS['success'], fg='#1e1e2e', height=2, font=("Segoe UI", 11, "bold"))
        self.btn_start.pack(fill=tk.X, pady=5)
        
        # Botão Modo DEV
        self.btn_dev_mode = self.create_button(force_frame, "⚡ MODO EDIÇÃO (Hot Reload)", self.start_dev_mode, bg='#9b59b6', fg='#ffffff', height=1, font=("Segoe UI", 10))
        self.btn_dev_mode.pack(fill=tk.X, pady=5)

        self.btn_stop = self.create_button(force_frame, "⏹ PARAR SISTEMA", self.stop_system, bg='#45475a', fg=COLORS['danger'], height=2)
        self.btn_stop.pack(fill=tk.X, pady=10)

        self.btn_restart = self.create_button(force_frame, "🔄 REINICIAR TUDO", self.restart_system, bg=COLORS['warning'], fg='#1e1e2e')
        self.btn_restart.pack(fill=tk.X, pady=10)

        tk.Frame(force_frame, bg=COLORS['bg'], height=10).pack() # Spacer

        self.btn_kill = self.create_button(force_frame, "💀 FORCE KILL (Emergência)", self.force_kill, bg='#2a2a2a', fg=COLORS['danger'])
        self.btn_kill.pack(fill=tk.X, pady=10)
        
        btn_dash = self.create_button(force_frame, "🌐 Abrir Navegador (Produção)", self.open_dashboard, bg=COLORS['primary'], fg='#ffffff')
        btn_dash.pack(fill=tk.X, pady=10)
        
        # Start background check
        threading.Thread(target=self.check_frontend_updates_async, daemon=True).start()

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

    def build_mobile_tab(self, parent):
        """Aba Mobile: Controle do App (Expo)"""
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Status Card
        status_card = tk.Frame(container, bg=COLORS['card'], padx=20, pady=20)
        status_card.pack(fill=tk.X, pady=(0, 20))
        
        self.lbl_mobile_status = tk.Label(status_card, text="MOBILE: PARADO", font=("Segoe UI", 12, "bold"), bg=COLORS['card'], fg=COLORS['subtext'])
        self.lbl_mobile_status.pack(side=tk.LEFT)

        # Controls
        controls = tk.Frame(container, bg=COLORS['bg'])
        controls.pack(fill=tk.X)
        
        self.btn_mobile = self.create_button(controls, "📱 Iniciar App Mobile (Expo)", self.toggle_mobile, bg=COLORS['primary'], fg='#1e1e2e')
        self.btn_mobile.pack(side=tk.LEFT, padx=5)
        
        self.btn_qr = self.create_button(controls, "🔳 Ver QR Code", self.toggle_expo_qr, bg=COLORS['card'], fg=COLORS['text'])
        self.btn_qr.pack(side=tk.LEFT, padx=5)

    def toggle_mobile(self):
        if self.process_expo:
            subprocess.call('taskkill /F /IM node.exe /T', shell=True) 
            self.process_expo = None
            self.lbl_mobile_status.config(text="MOBILE: PARADO", fg=COLORS['subtext'])
            self.btn_mobile.config(text="📱 Iniciar App Mobile (Expo)", bg=COLORS['primary'])
        else:
            project_path = os.path.join(os.getcwd(), 'mobile')
            if not os.path.exists(project_path):
                messagebox.showerror("Erro", "Pasta 'mobile' não encontrada.")
                return

            self.lbl_mobile_status.config(text="MOBILE: INICIANDO...", fg=COLORS['warning'])
            
            def run_expo():
                cmd = "npx expo start --clean"
                try:
                    self.process_expo = subprocess.Popen(cmd, cwd=project_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    self.lbl_mobile_status.config(text="MOBILE: RODANDO", fg=COLORS['success'])
                    self.btn_mobile.config(text="⏹ Parar Mobile", bg=COLORS['danger'])
                except Exception as e:
                    self.lbl_mobile_status.config(text="MOBILE: ERRO", fg=COLORS['danger'])
                    
            threading.Thread(target=run_expo, daemon=True).start()

    def toggle_expo_qr(self):
        self.notebook.select(self.tab_expo_logs)

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
    
    def build_expo_logs_tab(self, parent):
        """Constrói a aba de logs do Expo"""
        # Toolbar
        toolbar = tk.Frame(parent, bg=COLORS['bg'])
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            toolbar, text="🔄 Atualizar Logs", 
            command=self.refresh_expo_logs,
            bg=COLORS['card'], fg=COLORS['text'], relief="flat", padx=15, pady=5
        ).pack(side=tk.RIGHT)
        
        tk.Label(
            toolbar, text="Logs do Metro Bundler (Expo)",
            bg=COLORS['bg'], fg=COLORS['subtext']
        ).pack(side=tk.LEFT, pady=5)
        
        # Terminal
        self.expo_log_text = tk.Text(
            parent, bg=COLORS['terminal'], fg=COLORS['terminal_fg'],
            font=("Consolas", 10), relief="flat", padx=10, pady=10
        )
        scrollbar = tk.Scrollbar(parent, command=self.expo_log_text.yview)
        self.expo_log_text.config(yscrollcommand=scrollbar.set)
        
        self.expo_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tags
        self.expo_log_text.tag_config("success", foreground=COLORS['success'])
        self.expo_log_text.tag_config("warning", foreground=COLORS['warning'])
        self.expo_log_text.tag_config("error", foreground=COLORS['danger'])
        
        # Iniciar atualização automática
        self.refresh_expo_logs()

    def create_button(self, parent, text, command, bg, fg, font=("Segoe UI", 12, "bold"), height=2):
        """Helper para criar botões estilizados"""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=font,
            relief=tk.FLAT, cursor="hand2",
            activebackground=bg, activeforeground=fg, # Simples hover
            height=height
        )
        return btn

    # --- LÓGICA DO SISTEMA ---

    def check_status_loop(self):
        self.check_status()
        self.root.after(4000, self.check_status_loop)

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
                    self.btn_start.config(state=tk.DISABLED, bg='#2a2b3c', fg='#555')
                    self.btn_stop.config(state=tk.NORMAL, bg=COLORS['danger'], fg='#1e1e2e')
                    self.info_label.config(text="Sistema operando normalmente na porta 8080")
                else:
                    self.status_badge.config(text=" ● OFFLINE ", fg=COLORS['danger'], highlightbackground=COLORS['danger'])
                    self.btn_start.config(state=tk.NORMAL, bg=COLORS['success'], fg='#1e1e2e')
                    self.btn_stop.config(state=tk.DISABLED, bg='#2a2b3c', fg='#555')
                    self.info_label.config(text="Sistema parado. Clique em INICIAR para começar.")
            
            # 2. Check Processes (Only Expo/Ngrok now)
            if not hasattr(self, '_check_counter'):
                self._check_counter = 0
            
            self._check_counter += 1
            
            if self._check_counter % 3 == 0:
                ngrok_is_running = (self.ngrok_process is not None and self.ngrok_process.poll() is None)
                expo_is_running = (self.expo_process is not None and self.expo_process.poll() is None)
                
                # Check external processes
                for p in psutil.process_iter(['name']):
                    try:
                        name = p.info['name'].lower()
                        if 'ngrok' in name:
                            ngrok_is_running = True
                        elif 'node' in name:
                            try:
                                cmd = ' '.join(p.cmdline()).lower()
                                if 'expo' in cmd:
                                    expo_is_running = True
                            except: pass
                    except: pass

                # Update Ngrok UI
                if ngrok_is_running != self.ngrok_running:
                    self.ngrok_running = ngrok_is_running
                    if ngrok_is_running:
                        self.btn_ngrok.config(text="🌐 NGROK: LIGADO", bg=COLORS['success'], fg='#1e1e2e')
                    else:
                        self.btn_ngrok.config(text="🌐 NGROK: DESLIGADO", bg='#45475a', fg=COLORS['subtext'])
                
                # Update Expo UI
                if expo_is_running != self.expo_running:
                    self.expo_running = expo_is_running
                    if expo_is_running:
                        self.btn_expo.config(text="📱 EXPO: LIGADO (Clique p/ QR)", bg=COLORS['success'], fg='#1e1e2e')
                        self.btn_expo_stop.config(state=tk.NORMAL, bg=COLORS['danger'])
                    else:
                        self.btn_expo.config(text="📱 EXPO: DESLIGADO", bg='#45475a', fg=COLORS['subtext'])
                        self.btn_expo_stop.config(state=tk.DISABLED, bg='#45475a')

        except Exception as e:
            pass




    def start_system(self):
        if self.is_running: return
        
        self.should_be_running = True
        self.restart_attempts = 0 # Reset ao iniciar manual
        
        # --- AUTO-FIX: GARANTIR ESTRUTURA DE LOGS ---
        log_dir = "logs"
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                print(f"[LAUNCHER] Diretório '{log_dir}' recriado automaticamente.")
            except: pass

        # RESET LOGS (Limpar logs antigos dentro da pasta logs)
        # Lista atualizada para o novo padrão
        log_files = [
            os.path.join(log_dir, "api.log"),
            os.path.join(log_dir, "collector.log"),
            os.path.join(log_dir, "frontend.log"),
            # Startup.log muitas vezes fica na raiz pois é gerado antes do launcher saber de tudo,
            # mas vamos tentar limpar o da raiz também por higiene.
            "startup.log" 
        ]
        
        for lf in log_files:
            if os.path.exists(lf):
                try: open(lf, 'w').close()
                except: pass

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

        script = "iniciar_postgres.bat"
        if not os.path.exists(script):
            messagebox.showerror("Erro", f"Script {script} não encontrado!")
            return
            
        try:
            # Launcher silencioso
            proc = subprocess.Popen([script], creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.child_processes.append(proc)  # Rastrear processo
            
            # Switch to logs tab
            self.notebook.select(1)
            self.refresh_logs()
            
            # Feedback
            self.info_label.config(text="Iniciando... (Aguarde 5-10s)")
            self.status_badge.config(text=" ● INICIANDO ", fg=COLORS['warning'])
            
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
            os.system("taskkill /F /IM node.exe /T >nul 2>&1")
            os.system("taskkill /F /IM python.exe /T >nul 2>&1")
            os.system("taskkill /F /IM pythonw.exe /T >nul 2>&1")
            os.system("taskkill /F /IM postgres.exe /T >nul 2>&1")
            os.system("taskkill /F /IM conhost.exe /T >nul 2>&1")
            
            # 2. WMIC para processos órfãos (força bruta)
            os.system('wmic process where "name=\'node.exe\'" delete >nul 2>&1')
            os.system('wmic process where "name=\'python.exe\'" delete >nul 2>&1')
            os.system('wmic process where "name=\'pythonw.exe\'" delete >nul 2>&1')
            os.system('wmic process where "name=\'conhost.exe\'" delete >nul 2>&1')
            
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
           subprocess.run(["npm", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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
        # Janela de Progresso
        build_win = tk.Toplevel(self.root)
        build_win.title("Atualizando Interface...")
        build_win.geometry("400x150")
        build_win.configure(bg=COLORS['bg'])
        
        # Centralizar
        x = (self.root.winfo_screenwidth() - 400) // 2
        y = (self.root.winfo_screenheight() - 150) // 2
        build_win.geometry(f"+{x}+{y}")
        
        tk.Label(build_win, text="Otimizando e Compilando...", 
                fg=COLORS['text'], bg=COLORS['bg'], font=("Segoe UI", 12)).pack(pady=20)
        
        bar = ttk.Progressbar(build_win, mode='indeterminate')
        bar.pack(fill=tk.X, padx=30, pady=10)
        bar.start(10)
        build_win.update()
        
        # Executar npm run build
        success = False
        try:
            frontend_dir = os.path.join(os.getcwd(), "frontend")
            
            # Usar shell=True para 'npm' ser reconhecido
            process = subprocess.Popen("npm run build", shell=True, cwd=frontend_dir, 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            
            while process.poll() is None:
                build_win.update()
                time.sleep(0.1)
            
            if process.returncode == 0:
                # Salvar novo hash
                with open(hash_file, "w") as f:
                    f.write(new_hash)
                success = True
            else:
                out, err = process.communicate()
                messagebox.showerror("Erro no Build", f"Falha ao compilar:\n{err.decode(errors='ignore')}")
                
        except Exception as e:
             messagebox.showerror("Erro Crítico", str(e))
             
        build_win.destroy()
        return success

        build_win.destroy()
        return success
        
    def wait_for_start(self):
        """Aguarda inicialização verificando logs"""
        for _ in range(15):
            self.refresh_logs()
            self.check_status()
            if self.is_running:
                messagebox.showinfo("Sucesso", "Sistema Iniciado!")
                self.notebook.select(0) # Voltar pro controle
                return
            self.root.update()
            time.sleep(1)
        
        messagebox.showwarning("Timeout", "O sistema demorou a responder.\nVerifique a aba de LOGS para detalhes.")

    def stop_system(self):
        """Mata API, Coletor e processos relacionados"""
        self.should_be_running = False # Desativa monitoramento de crash
        killed = []
        try:
            my_pid = os.getpid()
            
            # Matar TODOS os processos relacionados ao projeto
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == my_pid: 
                        continue
                    
                    proc_name = proc.info.get('name', '').lower()
                    # Trata cmdline None para evitar erro 'can only join an iterable'
                    cmdline = ' '.join(proc.info.get('cmdline') or []).lower()
                    
                    # Critérios para matar:
                    # 1. Processos do projeto (python com collector, node com whatsapp, postgres)
                    # 2. Conhost que tenha postgres ou isp-monitor no caminho
                    should_kill = False
                    reason = ""
                    
                    if 'collector.py' in cmdline:
                        should_kill = True
                        reason = "Coletor"
                    elif proc_name == 'node.exe' and 'whatsapp' in cmdline:
                        should_kill = True
                        reason = "WhatsApp Gateway"
                    elif proc_name == 'postgres.exe' and 'isp-monitor' in cmdline:
                        should_kill = True
                        reason = "PostgreSQL"
                    elif proc_name == 'conhost.exe' and ('postgres' in cmdline or 'isp-monitor' in cmdline):
                        should_kill = True
                        reason = "Console Host (Projeto)"
                    elif proc_name == 'python.exe' and 'uvicorn' in cmdline and '8080' in cmdline:
                        should_kill = True
                        reason = "API (Uvicorn)"
                    
                    if should_kill:
                        print(f"[STOP] Matando {reason}: {proc_name} (PID {proc.info['pid']})")
                        proc.kill()
                        killed.append(reason)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                except Exception as e:
                    print(f"[STOP] Erro ao processar {proc.info.get('name', '?')}: {e}")
            
            self.child_processes.clear()
            time.sleep(1)
            self.check_status()
        
            if killed:
                messagebox.showinfo("Parado", f"Processos encerrados: {', '.join(set(killed))}")
            else:
                messagebox.showinfo("Info", "Nenhum processo ativo encontrado.")
            
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def force_kill(self):
        if messagebox.askyesno("Kill Forçado", "Isso vai encerrar TODOS os processos Python/Postgres relacionados.\nContinuar?"):
            try:
                os.system("taskkill /F /IM python.exe /T")
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

    def read_last_lines(self, file_path, n=50):
        """Lê as últimas n linhas de um arquivo de forma eficiente (sem ler tudo)"""
        if not os.path.exists(file_path): return []
        try:
            with open(file_path, 'rb') as f:
                try:
                    # Estima tamanho: 200 chars por linha * n
                    f.seek(-200 * n, 2) 
                except IOError:
                    # Arquivo menor que o seek, vai pro inicio
                    f.seek(0)
                
                lines = f.readlines()
                decoded_lines = [l.decode('utf-8', errors='ignore') for l in lines]
                return decoded_lines[-n:]
        except Exception:
            return []
    def toggle_ngrok(self):
        """Liga/Desliga o Ngrok"""
        if self.ngrok_running:
            # Desligar Ngrok
            try:
                if self.ngrok_process:
                    self.ngrok_process.terminate()
                    self.ngrok_process = None
                
                # Matar qualquer processo ngrok rodando
                for proc in psutil.process_iter(['name']):
                    if 'ngrok' in proc.info['name'].lower():
                        proc.kill()
                
                self.ngrok_running = False
                self.btn_ngrok.config(
                    text="🌐 NGROK: DESLIGADO",
                    bg='#45475a',
                    fg=COLORS['subtext']
                )
                self.info_label.config(text="Ngrok desligado")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao desligar Ngrok: {e}")
        else:
            # Ligar Ngrok
            try:
                ngrok_path = os.path.join(os.getcwd(), "tools", "ngrok", "ngrok.exe")
                domain = "uniconoclastic-addedly-yareli.ngrok-free.dev"
                
                if not os.path.exists(ngrok_path):
                    messagebox.showerror("Erro", f"Ngrok não encontrado em:\n{ngrok_path}")
                    return
                
                # Iniciar Ngrok em background
                self.ngrok_process = subprocess.Popen(
                    [ngrok_path, "http", f"--domain={domain}", "8080"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self.ngrok_running = True
                self.btn_ngrok.config(
                    text="🌐 NGROK: LIGADO",
                    bg=COLORS['success'],
                    fg='#1e1e2e'
                )
                self.info_label.config(text=f"Ngrok iniciado: {domain}")
                
                # Abrir dashboard do Ngrok
                time.sleep(1)
                import webbrowser
                webbrowser.open("http://localhost:4040")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao iniciar Ngrok: {e}")
                self.ngrok_running = False
    
    def toggle_expo(self):
        """Liga/Desliga o Expo Metro Bundler"""
        if self.expo_running:
            # Se já está rodando, mostrar QR code
            self.show_expo_qr()
        else:
            # Ligar Expo
            try:
                mobile_path = os.path.join(os.getcwd(), "mobile")
                
                if not os.path.exists(mobile_path):
                    messagebox.showerror("Erro", f"Pasta mobile não encontrada em:\n{mobile_path}")
                    return
                
                # Auto-Install dependencies se necessário
                # --offline: Evita pedir login na conta Expo e conflitos de host
                cmd = f'cd /d "{mobile_path}" && (if not exist node_modules npm install) && npx expo start --offline'
                
                self.info_label.config(text="Iniciando Expo (Modo Offline)...")
                self.expo_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Iniciar thread para capturar logs
                self.expo_logs = []
                log_thread = threading.Thread(target=self.capture_expo_logs, daemon=True)
                log_thread.start()
                
                self.expo_running = True
                self.btn_expo.config(
                    text="📱 EXPO: LIGADO (Clique p/ QR)",
                    bg=COLORS['success'],
                    fg='#1e1e2e'
                )
                self.info_label.config(text="Expo iniciado! Clique no botão para ver QR code")
                
                # Aguardar Expo iniciar e mostrar QR code
                time.sleep(3)
                self.show_expo_qr()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao iniciar Expo: {e}")
                self.expo_running = False
    
    def get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.0.17"  # Fallback
    
    def show_expo_qr(self):
        """Mostra QR code do Expo em popup"""
        # Obter IP local
        local_ip = self.get_local_ip()
        expo_url = f"exp://{local_ip}:8081"
        
        # Criar janela popup
        popup = tk.Toplevel(self.root)
        popup.title("QR Code - Expo Go")
        popup.configure(bg=COLORS['bg'])
        popup.geometry("400x550")
        popup.resizable(False, False)
        
        # Centralizar
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (400 // 2)
        y = (popup.winfo_screenheight() // 2) - (550 // 2)
        popup.geometry(f"400x550+{x}+{y}")
        
        # Título
        title = tk.Label(
            popup, text="📱 Escaneie com Expo Go",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS['bg'], fg=COLORS['text']
        )
        title.pack(pady=20)
        
        # Gerar QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(expo_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=COLORS['text'], back_color=COLORS['card'])
        
        # Converter para PhotoImage
        qr_photo = ImageTk.PhotoImage(qr_img)
        
        # Frame para QR code
        qr_frame = tk.Frame(popup, bg=COLORS['card'], relief=tk.FLAT, bd=0)
        qr_frame.pack(pady=10, padx=40)
        
        # Label com QR code
        qr_label = tk.Label(qr_frame, image=qr_photo, bg=COLORS['card'])
        qr_label.image = qr_photo  # Manter referência
        qr_label.pack(padx=10, pady=10)
        
        # URL
        url_label = tk.Label(
            popup, text=expo_url,
            font=("Consolas", 10),
            bg=COLORS['bg'], fg=COLORS['subtext']
        )
        url_label.pack(pady=10)
        
        # Instruções
        instructions = tk.Label(
            popup,
            text="1. Abra o Expo Go no celular\n2. Escaneie o QR code acima\n3. Aguarde o app carregar",
            font=("Segoe UI", 10),
            bg=COLORS['bg'], fg=COLORS['subtext'],
            justify=tk.LEFT
        )
        instructions.pack(pady=10)
        
        # Botão fechar
        btn_close = tk.Button(
            popup, text="Fechar",
            command=popup.destroy,
            bg=COLORS['primary'], fg='#1e1e2e',
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, cursor="hand2",
            padx=30, pady=10
        )
        btn_close.pack(pady=20)
    
    def capture_expo_logs(self):
        """Captura logs do processo Expo em tempo real"""
        try:
            with open("expo.log", "w", encoding="utf-8") as f:
                if self.expo_process and self.expo_process.stdout:
                    for line in iter(self.expo_process.stdout.readline, ''):
                        if line:
                            self.expo_logs.append(line)
                            f.write(line)
                            f.flush()
                            
                            # Limitar a 500 linhas na memória
                            if len(self.expo_logs) > 500:
                                self.expo_logs = self.expo_logs[-500:]
        except:
            pass
    
    def stop_expo(self):
        """Para o Expo Metro Bundler"""
        try:
            if self.expo_process:
                self.expo_process.terminate()
                self.expo_process = None
            
            # Matar qualquer processo expo/node rodando
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if 'node' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']).lower()
                        if 'expo' in cmdline or 'metro' in cmdline:
                            proc.kill()
                except:
                    pass
            
            self.expo_running = False
            self.btn_expo.config(
                text="📱 EXPO: DESLIGADO",
                bg='#45475a',
                fg=COLORS['subtext']
            )
            self.btn_expo_stop.config(state=tk.DISABLED, bg='#45475a')
            self.info_label.config(text="Expo desligado")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao desligar Expo: {e}")
    
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
            "EXPO.LOG": os.path.join("logs", "expo.log")
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
    
    def refresh_expo_logs(self):
        """Atualiza logs do Expo"""
        self.expo_log_text.config(state=tk.NORMAL)
        self.expo_log_text.delete(1.0, tk.END)
        
        if not self.process_expo:
            self.expo_log_text.insert(tk.END, "Expo não está rodando.\n\nVá na aba '📱 MOBILE' e clique em iniciar.", "warning")
        elif not self.expo_logs:
            self.expo_log_text.insert(tk.END, "Aguardando logs do Expo...\n\nO Metro Bundler está iniciando.", "warning")
        else:
            # Mostrar últimas 100 linhas
            for log in self.expo_logs[-100:]:
                if "error" in log.lower() or "failed" in log.lower():
                    self.expo_log_text.insert(tk.END, log, "error")
                elif "success" in log.lower() or "bundled" in log.lower():
                    self.expo_log_text.insert(tk.END, log, "success")
                elif "warning" in log.lower():
                    self.expo_log_text.insert(tk.END, log, "warning")
                else:
                    self.expo_log_text.insert(tk.END, log)
        
        self.expo_log_text.see(tk.END)
        self.expo_log_text.config(state=tk.DISABLED)
        
        # Auto-refresh a cada 2 segundos se Expo estiver rodando
        if self.process_expo:
            self.root.after(2000, self.refresh_expo_logs)


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
                os.system("taskkill /F /IM node.exe /T >nul 2>&1")
                os.system("taskkill /F /IM conhost.exe /FI \"WINDOWTITLE eq *postgres*\" >nul 2>&1")
                os.system("taskkill /F /IM conhost.exe /FI \"WINDOWTITLE eq *isp-monitor*\" >nul 2>&1")
            except:
                pass
            
            self.root.destroy()
            sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

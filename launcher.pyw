
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
        self.root = root
        self.root.title("ISP Monitor Enterprise | Launcher v3.0")
        
        # Configuração de Janela Inteligente
        self.center_window(700, 600)
        self.root.minsize(600, 500)
        self.root.configure(bg=COLORS['bg'])
        
        # Estado
        self.is_running = False
        self.should_be_running = False # Monitoramento de auto-cura
        self.process = None
        self.should_be_running = False 
        self.restart_attempts = 0
        self.expo_logs = []  # Armazenar logs do Expo

        # Estilos Customizados
        self.setup_styles()
        
        # Construir Interface
        self.create_widgets()
        
        # Loop de Verificação
        self.check_status_loop()

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
        
        # 2. Aba WhatsApp
        self.tab_whatsapp = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_whatsapp, text="  💚 WHATSAPP  ")

        # 3. Aba Mobile
        self.tab_mobile = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_mobile, text="  📱 MOBILE  ")

        # 4. Aba Logs System
        self.tab_logs = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_logs, text="  📝 LOGS  ")
        
        # 5. Aba Logs Expo
        self.tab_expo_logs = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.tab_expo_logs, text="  DEBUG APP  ")

        # Construir Conteúdo das Abas
        self.build_home_tab(self.tab_home)
        self.build_whatsapp_tab(self.tab_whatsapp)
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


    def build_whatsapp_tab(self, parent):
        """Aba WhatsApp Gateway"""
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(container, text="WhatsApp Gateway", font=("Segoe UI", 14, "bold"), bg=COLORS['bg'], fg=COLORS['success']).pack(pady=(0,20))

        self.btn_whatsapp = self.create_button(container, "ZEP: DESLIGADO", self.toggle_whatsapp, bg='#45475a', fg=COLORS['subtext'], height=2, font=("Segoe UI", 11, "bold"))
        self.btn_whatsapp.pack(fill=tk.X, pady=10)
        
        # QR e Reset lado a lado
        row_btns = tk.Frame(container, bg=COLORS['bg'])
        row_btns.pack(fill=tk.X, pady=10)
        
        self.btn_whatsapp_qr = self.create_button(row_btns, "� Ver QR Code", self.open_whatsapp_qr, bg='#45475a', fg=COLORS['text'])
        self.btn_whatsapp_qr.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.btn_whatsapp_qr.config(state=tk.DISABLED)

        self.btn_whatsapp_reset = self.create_button(row_btns, "🔄 Resetar Sessão", self.reset_whatsapp, bg='#45475a', fg=COLORS['text'])
        self.btn_whatsapp_reset.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,0))

        tk.Label(container, text="Testes & Diagnóstico", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(20,10))

        self.btn_whatsapp_test = self.create_button(container, "🔔 Enviar Mensagem de Teste", self.test_whatsapp_msg, bg='#45475a', fg=COLORS['text'])
        self.btn_whatsapp_test.pack(fill=tk.X, pady=5)
        self.btn_whatsapp_test.config(state=tk.DISABLED)

        self.btn_whatsapp_groups = self.create_button(container, "📋 Listar Meus Grupos (Copiar ID)", self.list_whatsapp_groups, bg='#45475a', fg=COLORS['text'])
        self.btn_whatsapp_groups.pack(fill=tk.X, pady=5)
        self.btn_whatsapp_groups.config(state=tk.DISABLED)

        self.whatsapp_process = None
        self.whatsapp_running = False

    def build_mobile_tab(self, parent):
        """Aba Mobile / Acesso Remoto"""
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(container, text="Acesso Remoto (App)", font=("Segoe UI", 12, "bold"), bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(0,20))

        # Ngrok
        self.btn_ngrok = self.create_button(container, "🌐 Ngrok (Túnel)", self.toggle_ngrok, bg='#45475a', fg=COLORS['subtext'])
        self.btn_ngrok.pack(fill=tk.X, pady=10)
        
        # Expo
        tk.Label(container, text="Expo (React Native)", font=("Segoe UI", 10), bg=COLORS['bg'], fg=COLORS['subtext']).pack(pady=(10,5))
        
        self.btn_expo = self.create_button(container, "📱 Iniciar Expo", self.toggle_expo, bg='#45475a', fg=COLORS['subtext'])
        self.btn_expo.pack(fill=tk.X, pady=5)
        
        self.btn_expo_stop = self.create_button(container, "⏹ Parar Expo", self.stop_expo, bg='#45475a', fg=COLORS['danger'])
        self.btn_expo_stop.pack(fill=tk.X, pady=5)
        self.btn_expo_stop.config(state=tk.DISABLED)

        self.ngrok_process = None
        self.ngrok_running = False
        self.expo_process = None
        self.expo_running = False

    def run_doctor(self):
        """Executa o sistema de diagnostico e reparo"""
        script_path = os.path.join(os.getcwd(), "tools", "reparo", "diagnostico.py")
        if os.path.exists(script_path):
            # Executa em nova janela para o usuario ver o processo
            subprocess.Popen(f'start "SISTEMA DE REPARO AUTOMATICO" cmd /c "python {script_path} && pause"', shell=True)
        else:
            messagebox.showerror("Erro", "Modulo de reparo nao encontrado.\nVerifique tools/reparo")

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

        tk.Button(
            toolbar, text="🚑 REPARO INTELIGENTE (IA)", 
            command=self.run_doctor,
            bg=COLORS['warning'], fg='#1e1e2e', relief="flat", padx=15, pady=5, font=("Segoe UI", 9, "bold")
        ).pack(side=tk.RIGHT, padx=10)
        
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
        
        # --- AUTO HEAL ---
        try:
            if getattr(self, 'should_be_running', False) and not self.is_running:
                 self.handle_crash()
        except: pass
        
        self.root.after(4000, self.check_status_loop)

    def check_status(self):
        """Verifica se API está rodando na porta 8080 (Otimizado)"""
        try:
            # 1. Check Port 8080 (Lightweight Socket Check)
            is_up = False
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', 8080))
                if result == 0:
                    is_up = True
                sock.close()
            except:
                is_up = False
            
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
            
            # 2. Check Processes (Single Pass - Low CPU)
            ngrok_is_running = False
            expo_is_running = False
            zap_is_running = False
            
            for p in psutil.process_iter(['name', 'cmdline']):
                try:
                    name = p.info['name'].lower()
                    cmd = ' '.join(p.info['cmdline'] or []).lower()
                    
                    if 'ngrok' in name:
                        ngrok_is_running = True
                    
                    if 'node' in name:
                        if 'expo' in cmd:
                            expo_is_running = True
                        if 'server.js' in cmd:
                            zap_is_running = True
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
                
            # Update WhatsApp UI
            # Logic here is complex because of status text, only update if significant change
            # But we must update if process state changed OR if we see the 'ready' file update
            
            # Check ZAP API Status
            status_text = "💛 ZAP: INICIANDO..."
            is_ready = False
            qr_available = False
            
            if zap_is_running:
                try:
                    # 500ms timeout para não travar a UI
                    resp = requests.get("http://localhost:3001/status", timeout=0.5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ready"):
                            status_text = "💚 ZAP: PRONTO"
                            is_ready = True
                        elif data.get("qr_code_available"):
                            status_text = "📷 ZAP: ESCANEAR QR"
                            qr_available = True
                        else:
                            status_text = "💛 ZAP: CARREGANDO..."
                except:
                    # Se der erro de conexão mas o processo tá rodando, é porque ainda tá subindo o express
                    status_text = "💛 ZAP: CARREGANDO..."

            else:
                 status_text = "💚 ZAP: DESLIGADO"

            # Should update UI?
            should_update_zap_ui = (zap_is_running != self.whatsapp_running) or (self.btn_whatsapp['text'] != status_text)
            
            if should_update_zap_ui:
                self.whatsapp_running = zap_is_running
                
                if not zap_is_running:
                     self.btn_whatsapp.config(text="💚 ZAP: DESLIGADO", bg='#45475a', fg=COLORS['subtext'])
                     self.btn_whatsapp_qr.config(state=tk.DISABLED, bg='#45475a')
                     self.btn_whatsapp_test.config(state=tk.DISABLED)
                     self.btn_whatsapp_groups.config(state=tk.DISABLED)
                else:
                    self.btn_whatsapp.config(text=status_text, bg=COLORS['success'] if is_ready else COLORS['warning'], fg='#1e1e2e')
                    
                    if is_ready:
                        self.btn_whatsapp_qr.config(state=tk.DISABLED, bg='#45475a')
                        self.btn_whatsapp_test.config(state=tk.NORMAL)
                        self.btn_whatsapp_groups.config(state=tk.NORMAL)
                    else:
                        if qr_available:
                            self.btn_whatsapp_qr.config(state=tk.NORMAL, bg=COLORS['danger'])
                        else:
                            self.btn_whatsapp_qr.config(state=tk.DISABLED, bg='#45475a')
                            
                        self.btn_whatsapp_test.config(state=tk.DISABLED)
                        self.btn_whatsapp_groups.config(state=tk.DISABLED)

        except Exception as e:
            # print(f"Status Check Fail: {e}") 
            pass

    def handle_crash(self):
        """Gerencia falhas e aciona o Doctor"""
        if self.restart_attempts >= 3:
            self.should_be_running = False # Desiste
            self.root.after(0, lambda: messagebox.showerror("Erro Crítico", 
                "O sistema falhou repetidamente e o reparo automático não resolveu.\nVerifique os LOGS."))
            return

        print(f"[LAUNCHER] Crash detectado! Tentativa de cura {self.restart_attempts + 1}/3...")
        self.info_label.config(text=f"Autocura em andamento ({self.restart_attempts+1}/3)...")
        
        # Ler logs para diagnóstico
        log_content = ""
        for log_file in ["startup.log", "api.log", "collector.log"]:
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        log_content += f"\n--- {log_file} ---\n"
                        log_content += "".join(f.readlines()[-50:]) # Ultimas 50 linhas
                except: pass
        
        # Chamar Doctor
        try:
            from backend.doctor import healer
            healed = healer.diagnose_and_heal(log_content)
            
            if healed:
                print("[LAUNCHER] Doctor reportou sucesso. Reiniciando...")
                self.restart_attempts += 1
                time.sleep(2)
                self.start_system() 
            else:
                print("[LAUNCHER] Doctor não encontrou cura.")
                self.should_be_running = False # Para de tentar
                self.root.after(0, lambda: messagebox.showwarning("Atenção", "O sistema parou e não há correção automática conhecida."))
                
        except Exception as e:
            print(f"[LAUNCHER] Erro ao chamar Doctor: {e}")
            self.should_be_running = False

    def start_system(self):
        if self.is_running: return
        
        self.should_be_running = True
        self.restart_attempts = 0 # Reset ao iniciar manual
        
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
            subprocess.Popen([script], creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Switch to logs tab
            self.notebook.select(1)
            self.refresh_logs()
            
            # Feedback
            self.info_label.config(text="Iniciando... (Aguarde 5-10s)")
            self.status_badge.config(text=" ● INICIANDO ", fg=COLORS['warning'])
            
            # Aguardar e verificar
            self.wait_for_start()
            
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
            
            # 2. WMIC para processos órfãos (força bruta)
            os.system('wmic process where "name=\'node.exe\'" delete >nul 2>&1')
            os.system('wmic process where "name=\'python.exe\'" delete >nul 2>&1')
            os.system('wmic process where "name=\'pythonw.exe\'" delete >nul 2>&1')
            
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
        
    # --- WHATSAPP CONTROL ---
    def toggle_whatsapp(self):
        """Liga/Desliga o WhatsApp Gateway"""
        if self.whatsapp_running:
            # Desligar
            try:
                # Matar processo node que roda server.js na pasta tools/whatsapp
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if 'node' in proc.info['name'].lower():
                            cmd = ' '.join(proc.info['cmdline'] or [])
                            if 'whatsapp' in cmd and 'server.js' in cmd:
                                proc.kill()
                    except: pass
                
                self.whatsapp_running = False
                self.btn_whatsapp.config(text="💚 ZAP: DESLIGADO", bg='#45475a', fg=COLORS['subtext'])
                self.btn_whatsapp_qr.config(state=tk.DISABLED, bg='#45475a')
                self.btn_whatsapp_test.config(state=tk.DISABLED)
                self.btn_whatsapp_groups.config(state=tk.DISABLED)
                self.info_label.config(text="WhatsApp Gateway desligado")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao desligar Zap: {e}")
        else:
            # Ligar
            try:
                 # 1. Matar Zumbis (Prevenir EADDRINUSE)
                 for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if 'node' in proc.info['name'].lower():
                            cmd = ' '.join(proc.info['cmdline'] or [])
                            if 'whatsapp' in cmd and 'server.js' in cmd:
                                proc.kill()
                    except: pass
                 time.sleep(1) # Dar tempo para liberar porta
            
                 script_path = os.path.join(os.getcwd(), "tools", "whatsapp", "server.js")
                 if not os.path.exists(script_path):
                     messagebox.showerror("Erro", "Gateway não instalado.\nRode INSTALAR_ZAP.bat primeiro.")
                     return
                 
                 # Iniciar Node em background (LOGGING ATIVADO)
                 cwd = os.path.join(os.getcwd(), "tools", "whatsapp")
                 log_file = os.path.join(cwd, "whatsapp.log")
                 
                 # Usar um arquivo para capturar stdout/stderr
                 # Importante: Não usar 'with open' aqui pois o file handle precisa ficar aberto para o subprocesso
                 f_log = open(log_file, "w")
                 
                 subprocess.Popen(["node", "server.js"], cwd=cwd, 
                                  stdout=f_log, stderr=f_log,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                 
                 self.whatsapp_running = True
                 self.btn_whatsapp.config(text="💚 ZAP: INICIANDO...", bg=COLORS['warning'], fg='#1e1e2e')
                 self.btn_whatsapp_qr.config(state=tk.NORMAL, bg=COLORS['primary'])
                 self.btn_whatsapp_test.config(state=tk.NORMAL)
                 self.btn_whatsapp_groups.config(state=tk.NORMAL)
                 self.info_label.config(text="Iniciando WhatsApp... Aguarde QR Code.")
                 
                 # Verificar QR code em loop (via API agora checada no main loop)
                 # self.root.after(2000, self.check_whatsapp_qr)
                 
            except Exception as e:
                 messagebox.showerror("Erro", f"Erro ao ligar Zap: {e}")

    def check_whatsapp_qr(self):
        # Deprecated: Logic moved to check_status API call
        pass

    def open_whatsapp_qr(self):
        qr_path = os.path.join(os.getcwd(), "tools", "whatsapp", "whatsapp-qr.png")
        if os.path.exists(qr_path):
            os.startfile(qr_path)
            self.info_label.config(text="Escaneie o QR Code com seu celular.")
        else:
             messagebox.showinfo("Info", "QR Code ainda não gerado ou já conectado.")

    def reset_whatsapp(self):
        # Janela Customizada para Escolha
        win = tk.Toplevel(self.root)
        win.title("Opções de Reset")
        win.geometry("400x250")
        win.configure(bg=COLORS['bg'])
        
        # Centralizar na tela (aproximado)
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 50
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="O que você deseja fazer?", font=("Segoe UI", 12, "bold"), 
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=(20,15))

        # Variável para armazenar escolha
        self._reset_choice = None
        
        def choose_hard():
            self._reset_choice = 'hard'
            win.destroy()
            
        def choose_soft():
            self._reset_choice = 'soft'
            self._reset_choice = 'soft'
            win.destroy()

        # Botão Hard Reset
        btn_hard = tk.Button(win, text="🧹 APAGAR TUDO (Gerar Novo QR)\n(Logout Completo)", 
                             command=choose_hard, bg=COLORS['danger'], fg='#ffffff', 
                             font=("Segoe UI", 10, "bold"), height=3, relief="flat")
        btn_hard.pack(fill=tk.X, padx=20, pady=5)

        # Botão Soft Reset
        btn_soft = tk.Button(win, text="🔄 APENAS REINICIAR (Manter Login)\n(Destravar Serviço)", 
                             command=choose_soft, bg=COLORS['warning'], fg='#1e1e2e', 
                             font=("Segoe UI", 10, "bold"), height=3, relief="flat")
        btn_soft.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Button(win, text="Cancelar", command=win.destroy, bg=COLORS['card'], fg=COLORS['text']).pack(pady=10)

        win.transient(self.root)
        win.grab_set()
        self.root.wait_window(win)
        
        if not self._reset_choice:
            return # Cancelado

        is_hard_reset = (self._reset_choice == 'hard')

        # 1. Matar Processo Forçadamente
        self.info_label.config(text="Parando WhatsApp...")
        self.root.update()
        
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if 'node' in proc.info['name'].lower():
                        cmd = ' '.join(proc.info['cmdline'] or [])
                        if 'whatsapp' in cmd and 'server.js' in cmd:
                            proc.kill()
                except: pass
        except: pass
        
        self.whatsapp_running = False
        self.btn_whatsapp.config(text="💚 ZAP: DESLIGADO", bg='#45475a', fg=COLORS['subtext'])
        self.btn_whatsapp_qr.config(state=tk.DISABLED, bg='#45475a')
        self.btn_whatsapp_test.config(state=tk.DISABLED)
        self.btn_whatsapp_groups.config(state=tk.DISABLED)
        
        time.sleep(1) 

        if is_hard_reset:
            # 2. Limpar arquivos (Apenas se pediu Hard Reset)
            self.info_label.config(text="Limpando sessão antiga...")
            self.root.update()
            
            try:
                base_dir = os.path.join(os.getcwd(), "tools", "whatsapp")
                targets = ["session", ".wwebjs_auth", ".wwebjs_cache"]
                
                for t in targets:
                    path = os.path.join(base_dir, t)
                    if os.path.exists(path):
                        for attempt in range(3):
                            try:
                                shutil.rmtree(path, ignore_errors=False)
                                break
                            except:
                                time.sleep(1)
                
                qr_file = os.path.join(base_dir, "whatsapp-qr.png")
                if os.path.exists(qr_file):
                    try: os.remove(qr_file)
                    except: pass
            except Exception as e:
                pass # Ignorar erros de delete no reset

        self.info_label.config(text="Reiniciando serviço...")
        # 3. Ligar novamente
        self.root.after(1000, self.toggle_whatsapp)

    def send_test_to_target(self, target, name=None):
        """Envia teste para um alvo específico"""
        try:
            # Salvar número novo
            try:
                last_num_file = os.path.join(os.getcwd(), "tools", "whatsapp", "last_number.txt")
                with open(last_num_file, "w") as f:
                    f.write(target)
            except: pass

            import json
            import urllib.request
            import urllib.error
            
            url = "http://127.0.0.1:3001/send"
            msg = f"🔔 *Teste ISP Monitor*\n\nEnviado para: {name or target}\nStatus: OPERACIONAL! 🚀"
            
            data = json.dumps({
                "number": target,
                "message": msg
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.getcode() == 200:
                    messagebox.showinfo("Sucesso", f"Mensagem enviada para {name or target}!")
                else:
                    messagebox.showerror("Erro", "O servidor retornou erro.")
                    
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode('utf-8')
                error_json = json.loads(error_body)
                error_msg = error_json.get('error', error_body)
            except:
                error_msg = "Detalhes indisponiveis"

            if e.code == 404:
                messagebox.showerror("Erro 404", f"Número nao registrado no WhatsApp:\n{error_msg}")
            elif e.code == 503:
                messagebox.showwarning("Aguarde", f"O WhatsApp ainda está sincronizando.\n{error_msg}")
            else:
                messagebox.showerror("Erro no Servidor", f"Erro {e.code}: {e.reason}\n\nMotivo: {error_msg}")

        except Exception as e:
            messagebox.showerror("Falha no Teste", f"Erro: {e}")

    def test_whatsapp_msg(self):
        # 1. Tentar ler último número salvo
        last_num_file = os.path.join(os.getcwd(), "tools", "whatsapp", "last_number.txt")
        default_val = ""
        
        if os.path.exists(last_num_file):
            try:
                with open(last_num_file, "r") as f:
                    default_val = f.read().strip()
            except: pass

        # 2. Pedir número (com default)
        target = simpledialog.askstring("Teste WhatsApp", 
                                      "Qual número receberá o teste?\nFormatos: 5511999999999 ou 1203...@g.us", 
                                      initialvalue=default_val)
        if target:
            self.send_test_to_target(target)

    def list_whatsapp_groups(self):
        """Busca e exibe grupos do WhatsApp com UI interativa"""
        try:
            import urllib.request
            import json
            from tkinter import ttk
            
            url = "http://127.0.0.1:3001/groups"
            with urllib.request.urlopen(url, timeout=15) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    # Ordenar
                    try: data.sort(key=lambda x: x['name'].lower())
                    except: pass
                    
                    win = tk.Toplevel(self.root)
                    win.title("Selecione um Grupo")
                    win.geometry("750x550")
                    win.configure(bg=COLORS['bg'])
                    
                    tk.Label(win, text="Duplo clique para enviar teste ou selecione para copiar ID", 
                             bg=COLORS['bg'], fg=COLORS['text'], font=("Segoe UI", 11)).pack(pady=10)
                    
                    # Estilo Dark para Treeview
                    style = ttk.Style()
                    try: style.theme_use('clam')
                    except: pass
                    style.configure("Treeview", background="#2a2b3c", fieldbackground="#2a2b3c", foreground="white", rowheight=25)
                    style.configure("Treeview.Heading", background="#4a4b5c", foreground="white", font=("Segoe UI", 10, "bold"))
                    style.map("Treeview", background=[('selected', COLORS['primary'])])
                    
                    columns = ('nome', 'id')
                    tree = ttk.Treeview(win, columns=columns, show='headings')
                    tree.heading('nome', text='Nome do Grupo')
                    tree.heading('id', text='ID (Copiável)')
                    tree.column('nome', width=450)
                    tree.column('id', width=250)
                    
                    # Scrollbar
                    scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
                    tree.configure(yscrollcommand=scrollbar.set)
                    
                    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0,10))
                    
                    for group in data:
                        tree.insert('', tk.END, values=(group['name'], group['id']))
                        
                    def on_action(event=None):
                        sel = tree.selection()
                        if not sel: return
                        item = tree.item(sel[0])
                        target_id = item['values'][1]
                        name = item['values'][0]
                        
                        self.root.clipboard_clear()
                        self.root.clipboard_append(target_id)
                        
                        resp = messagebox.askyesno("Confirmar Envio", 
                                                 f"Grupo: {name}\nID: {target_id}\n\nTudo certo! Deseja enviar o teste agora?")
                        if resp:
                            win.destroy()
                            self.send_test_to_target(target_id, name)
                            
                    tree.bind("<Double-1>", on_action)
                    
                    # Botao inferior
                    btn_agora = tk.Button(win, text="✅ Selecionar e Testar", command=on_action,
                                        bg=COLORS['primary'], fg='white', font=("Segoe UI", 12, "bold"), height=2)
                    btn_agora.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

                else:
                    messagebox.showerror("Erro", "Erro ao buscar grupos (Status != 200).")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível listar grupos.\nO Zap está conectado?\n\nErro: {e}")

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
        """Mata API e Coletor"""
        self.should_be_running = False # Desativa monitoramento de crash
        killed = []
        try:
            # 1. API (Porta 8080)
            for conn in psutil.net_connections():
                if conn.laddr.port == 8080:
                    psutil.Process(conn.pid).terminate()
                    killed.append("API")
            
            # 2. Coletor (Processo python collector.py)
            my_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if proc.info['pid'] == my_pid: continue
                    cmd = str(proc.info['cmdline'])
                    if 'collector.py' in cmd:
                        proc.terminate()
                        killed.append("Coletor")
                except: pass
                
            time.sleep(1)
            self.check_status()
            
            if killed:
                messagebox.showinfo("Parado", f"Processos encerrados: {', '.join(killed)}")
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

    def refresh_logs(self):
        """Carrega logs coloridos (Otimizado)"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        files = ["startup.log", "api.log", "collector.log"]
        
        for fname in files:
            self.log_text.insert(tk.END, f"\n┏━━ {fname.upper()} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "title")
            
            lines = self.read_last_lines(fname, 50)
            if lines:
                self.log_text.insert(tk.END, "".join(lines))
            elif os.path.exists(fname):
                 self.log_text.insert(tk.END, "[Arquivo Vazio ou Erro de Leitura]\n")
            else:
                self.log_text.insert(tk.END, "[Não encontrado]\n", "error")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    
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
                
                # Iniciar Expo em background (sem janela)
                cmd = f'cd /d "{mobile_path}" && npx expo start'
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
            if self.expo_process and self.expo_process.stdout:
                for line in iter(self.expo_process.stdout.readline, ''):
                    if line:
                        self.expo_logs.append(line)
                        # Limitar a 500 linhas
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
        
        files = ["startup.log", "api.log", "collector.log"]
        
        for fname in files:
            self.log_text.insert(tk.END, f"\n┏━━ {fname.upper()} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "title")
            if os.path.exists(fname):
                try:
                    with open(fname, "r") as f:
                        lines = f.readlines()[-30:]  # Last 30 lines
                        self.log_text.insert(tk.END, "".join(lines) if lines else "[Arquivo Vazio]\n")
                except:
                    self.log_text.insert(tk.END, "[Erro ao ler]\n", "error")
            else:
                self.log_text.insert(tk.END, "[Não encontrado]\n", "error")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def refresh_expo_logs(self):
        """Atualiza logs do Expo"""
        self.expo_log_text.config(state=tk.NORMAL)
        self.expo_log_text.delete(1.0, tk.END)
        
        if not self.expo_running:
            self.expo_log_text.insert(tk.END, "Expo não está rodando.\n\nClique em 'EXPO: DESLIGADO' para iniciar.", "warning")
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
        if self.expo_running:
            self.root.after(2000, self.refresh_expo_logs)


    def on_closing(self):
        """Handler para fechar a janela com limpeza agressiva"""
        if messagebox.askokcancel("Sair", "Deseja realmente sair? O monitoramento será interrompido."):
            self.stop_system()
            self.root.destroy()
            
            # Limpeza AGRESSIVA de processos (Force Kill Total)
            print("[LAUNCHER] Executando limpeza agressiva de processos...")
            try:
                # 1. Taskkill padrão
                os.system("taskkill /F /IM node.exe /T >nul 2>&1")
                os.system("taskkill /F /IM python.exe /T >nul 2>&1")
                os.system("taskkill /F /IM pythonw.exe /T >nul 2>&1")
                os.system("taskkill /F /IM postgres.exe /T >nul 2>&1")
                
                # 2. WMIC para processos órfãos (força bruta)
                os.system('wmic process where "name=\'node.exe\'" delete >nul 2>&1')
                os.system('wmic process where "name=\'python.exe\'" delete >nul 2>&1')
                os.system('wmic process where "name=\'pythonw.exe\'" delete >nul 2>&1')
                
                print("[LAUNCHER] Limpeza completa. Arquivos liberados.")
            except Exception as e:
                print(f"[LAUNCHER] Erro na limpeza: {e}")
            
            sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

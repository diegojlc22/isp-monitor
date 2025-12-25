
"""
ISP Monitor - Launcher v3.0 (Professional Edition)
Interface gráfica moderna e robusta para gerenciamento do sistema.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import psutil
import time
import threading
import qrcode
from PIL import Image, ImageTk
import socket

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
        self.expo_logs = []  # Armazenar logs do Expo
        
        # Estilos TTK
        self.setup_styles()
        
        # Interface
        self.build_ui()
        
        # Inicialização
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
        
        # Configuração de Abas (Notebook)
        style.configure('TNotebook', background=COLORS['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
            background=COLORS['card'], 
            foreground=COLORS['text'], 
            padding=[20, 10], 
            font=('Segoe UI', 10)
        )
        style.map('TNotebook.Tab', 
            background=[('selected', COLORS['primary'])], 
            foreground=[('selected', '#1e1e2e')]
        )
        
        # Frames
        style.configure('Card.TFrame', background=COLORS['bg'])
        
    def build_ui(self):
        """Constrói a interface baseada em Grid Layout"""
        # Header
        header = tk.Frame(self.root, bg=COLORS['bg'], height=80)
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(
            header, text="ISP MONITOR", 
            font=("Segoe UI", 24, "bold"), fg=COLORS['text'], bg=COLORS['bg']
        ).pack(side=tk.LEFT)
        
        self.status_badge = tk.Label(
            header, text=" ● OFFLINE ", 
            font=("Segoe UI", 10, "bold"), fg=COLORS['danger'], bg=COLORS['bg'],
            padx=10, pady=5, bd=1, relief="solid"
        )
        self.status_badge.pack(side=tk.RIGHT)
        
        # Sistema de Abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Aba 1: Controle
        self.tab_control = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.tab_control, text=" 🎮 CONTROLE ")
        self.build_control_tab(self.tab_control)
        
        # Aba 2: Logs do Sistema
        self.tab_logs = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.tab_logs, text=" 📝 LOGS DO SISTEMA ")
        self.build_logs_tab(self.tab_logs)
        
        # Aba 3: Logs do Expo
        self.tab_expo_logs = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.tab_expo_logs, text=" 📱 LOGS DO EXPO ")
        self.build_expo_logs_tab(self.tab_expo_logs)

    def build_control_tab(self, parent):
        """Constrói a aba de controle com Grid Layout"""
        # Configurar Grid
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        
        # Container Principal Centralizado
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Botão Principal (Browser) - Row 0 (Full Width)
        btn_browser = self.create_button(
            container, "🌐 ABRIR DASHBOARD", self.open_dashboard, 
            bg=COLORS['primary'], fg='#1e1e2e', font=("Segoe UI", 14, "bold"), height=3
        )
        btn_browser.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 30))
        
        # Ações de Controle - Row 1
        self.btn_start = self.create_button(
            container, "▶ INICIAR", self.start_system, bg=COLORS['success'], fg='#1e1e2e'
        )
        self.btn_start.grid(row=1, column=0, padx=(0, 10), sticky="ew")
        
        self.btn_stop = self.create_button(
            container, "⏹ PARAR", self.stop_system, bg=COLORS['danger'], fg='#1e1e2e'
        )
        self.btn_stop.grid(row=1, column=1, padx=(10, 0), sticky="ew")
        
        # Ações Secundárias - Row 2
        self.btn_restart = self.create_button(
            container, "🔄 REINICIAR", self.restart_system, bg=COLORS['warning'], fg='#1e1e2e'
        )
        self.btn_restart.grid(row=2, column=0, padx=(0, 10), pady=20, sticky="ew")
        
        btn_kill = self.create_button(
            container, "💀 KILL FORÇADO", self.force_kill, bg='#45475a', fg=COLORS['danger']
        )
        btn_kill.grid(row=2, column=1, padx=(10, 0), pady=20, sticky="ew")
        
        # Controle do Ngrok - Row 3
        self.btn_ngrok = self.create_button(
            container, "🌐 NGROK: DESLIGADO", self.toggle_ngrok, bg='#45475a', fg=COLORS['subtext']
        )
        self.btn_ngrok.grid(row=3, column=0, columnspan=2, pady=(0, 20), sticky="ew")
        
        # Estado do Ngrok
        self.ngrok_process = None
        self.ngrok_running = False
        
        # Controle do Expo - Row 4
        self.btn_expo = self.create_button(
            container, "📱 EXPO: DESLIGADO", self.toggle_expo, bg='#45475a', fg=COLORS['subtext']
        )
        self.btn_expo.grid(row=4, column=0, sticky="ew", padx=(0, 5), pady=(0, 20))
        
        # Botão para parar Expo
        self.btn_expo_stop = self.create_button(
            container, "⏹ PARAR", self.stop_expo, bg='#45475a', fg=COLORS['danger'], height=2
        )
        self.btn_expo_stop.grid(row=4, column=1, sticky="ew", padx=(5, 0), pady=(0, 20))
        self.btn_expo_stop.config(state=tk.DISABLED)
        
        # Estado do Expo
        self.expo_process = None
        self.expo_running = False
        
        # Status/Info Area (movido para baixo do Expo)
        self.info_label = tk.Label(
            container, text="Aguardando comando...", 
            font=("Segoe UI", 10), bg=COLORS['bg'], fg=COLORS['subtext']
        )
        self.info_label.grid(row=5, column=0, columnspan=2, pady=10)

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
        self.root.after(2000, self.check_status_loop)

    def check_status(self):
        """Verifica se API está rodando na porta 8080"""
        try:
            is_up = False
            for conn in psutil.net_connections():
                if conn.laddr.port == 8080 and conn.status == 'LISTEN':
                    is_up = True
                    break
            
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
            
            # Verificar status do Ngrok
            ngrok_is_running = any('ngrok' in p.name().lower() for p in psutil.process_iter(['name']))
            if ngrok_is_running != self.ngrok_running:
                self.ngrok_running = ngrok_is_running
                if ngrok_is_running:
                    self.btn_ngrok.config(
                        text="🌐 NGROK: LIGADO",
                        bg=COLORS['success'],
                        fg='#1e1e2e'
                    )
                else:
                    self.btn_ngrok.config(
                        text="🌐 NGROK: DESLIGADO",
                        bg='#45475a',
                        fg=COLORS['subtext']
                    )
            
            # Verificar status do Expo
            expo_is_running = any('node' in p.name().lower() and 'expo' in ' '.join(p.cmdline()).lower() for p in psutil.process_iter(['name', 'cmdline']))
            if expo_is_running != self.expo_running:
                self.expo_running = expo_is_running
                if expo_is_running:
                    self.btn_expo.config(
                        text="📱 EXPO: LIGADO (Clique p/ QR)",
                        bg=COLORS['success'],
                        fg='#1e1e2e'
                    )
                    self.btn_expo_stop.config(state=tk.NORMAL, bg=COLORS['danger'])
                else:
                    self.btn_expo.config(
                        text="📱 EXPO: DESLIGADO",
                        bg='#45475a',
                        fg=COLORS['subtext']
                    )
                    self.btn_expo_stop.config(state=tk.DISABLED, bg='#45475a')
                
        except Exception:
            pass

    def start_system(self):
        if self.is_running: return
        
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

    def refresh_logs(self):
        """Carrega logs coloridos"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        files = ["startup.log", "api.log", "collector.log"]
        
        for fname in files:
            self.log_text.insert(tk.END, f"\n┏━━ {fname.upper()} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", "title")
            if os.path.exists(fname):
                try:
                    with open(fname, "r") as f:
                        lines = f.readlines()[-30:] # Last 30 lines
                        self.log_text.insert(tk.END, "".join(lines) if lines else "[Arquivo Vazio]\n")
                except:
                    self.log_text.insert(tk.END, "[Erro ao ler]\n", "error")
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.mainloop()

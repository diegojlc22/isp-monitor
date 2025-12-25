
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
        
        # Aba 2: Logs
        self.tab_logs = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(self.tab_logs, text=" 📝 LOGS DO SISTEMA ")
        self.build_logs_tab(self.tab_logs)

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
        
        # Status/Info Area
        self.info_label = tk.Label(
            container, text="Aguardando comando...", 
            font=("Segoe UI", 10), bg=COLORS['bg'], fg=COLORS['subtext']
        )
        self.info_label.grid(row=3, column=0, columnspan=2, pady=10)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.mainloop()

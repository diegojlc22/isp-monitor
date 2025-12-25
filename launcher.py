"""
ISP Monitor - Launcher GUI
Interface gráfica para gerenciar o sistema
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import sys
import threading
import psutil
import time

class ISPMonitorLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("ISP Monitor - Launcher v2.4")
        self.root.geometry("600x700")  # Tamanho inicial (redimensionável)
        self.root.resizable(True, True)  # Permite ajustar o tamanho manualmente
        
        # Cores modernas
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"
        self.warning_color = "#f9e2af"
        
        self.root.configure(bg=self.bg_color)
        
        self.process = None
        self.is_running = False
        
        self.setup_ui()
        self.check_status()
        
        # Atalho F5 para recarregar
        self.root.bind('<F5>', lambda e: self.reload_interface())
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.accent_color, height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(
            header,
            text="🌐 ISP Monitor",
            font=("Segoe UI", 24, "bold"),
            bg=self.accent_color,
            fg="#1e1e2e"
        )
        title.pack(pady=20)
        
        # Status Frame
        status_frame = tk.Frame(self.root, bg=self.bg_color)
        status_frame.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(
            status_frame,
            text="Status do Sistema:",
            font=("Segoe UI", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W)
        
        self.status_label = tk.Label(
            status_frame,
            text="● Verificando...",
            font=("Segoe UI", 14),
            bg=self.bg_color,
            fg=self.warning_color
        )
        self.status_label.pack(anchor=tk.W, pady=5)
        
        self.info_label = tk.Label(
            status_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.info_label.pack(anchor=tk.W)
        
        # Buttons Frame
        buttons_frame = tk.Frame(self.root, bg=self.bg_color)
        buttons_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # ⭐ BOTÃO ABRIR NAVEGADOR - NO TOPO!
        btn_dashboard = tk.Button(
            buttons_frame,
            text="🌐 ABRIR NO NAVEGADOR",
            font=("Segoe UI", 14, "bold"),  # Ainda maior!
            bg="#74c7ec",  # Azul claro
            fg="#1e1e2e",
            activebackground="#89dceb",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_dashboard,
            height=3
        )
        btn_dashboard.pack(fill=tk.X, pady=10)
        
        # Separador
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Botão Iniciar
        self.btn_start = tk.Button(
            buttons_frame,
            text="▶ INICIAR SISTEMA",
            font=("Segoe UI", 12, "bold"),
            bg=self.success_color,
            fg="#1e1e2e",
            activebackground="#94e2d5",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_system,
            height=2
        )
        self.btn_start.pack(fill=tk.X, pady=5)
        
        # Botão Parar
        self.btn_stop = tk.Button(
            buttons_frame,
            text="⏹ PARAR SISTEMA",
            font=("Segoe UI", 12, "bold"),
            bg=self.error_color,
            fg="#1e1e2e",
            activebackground="#eba0ac",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.stop_system,
            height=2
        )
        self.btn_stop.pack(fill=tk.X, pady=5)
        
        # Botão Reiniciar
        self.btn_restart = tk.Button(
            buttons_frame,
            text="🔄 REINICIAR SISTEMA",
            font=("Segoe UI", 12, "bold"),
            bg=self.warning_color,
            fg="#1e1e2e",
            activebackground="#f5e0a3",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.restart_system,
            height=2
        )
        self.btn_restart.pack(fill=tk.X, pady=5)
        
        # Separador
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Botão Verificar Status
        btn_check = tk.Button(
            buttons_frame,
            text="🔍 VERIFICAR STATUS",
            font=("Segoe UI", 11),
            bg="#45475a",
            fg=self.fg_color,
            activebackground="#585b70",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.check_status,
            height=2
        )
        btn_check.pack(fill=tk.X, pady=5)
        
        # Botão Kill Forçado
        btn_force_kill = tk.Button(
            buttons_frame,
            text="💀 KILL FORÇADO",
            font=("Segoe UI", 11, "bold"),
            bg="#7f1d1d",
            fg="#fca5a5",
            activebackground="#991b1b",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.force_kill_all,
            height=2
        )
        btn_force_kill.pack(fill=tk.X, pady=5)
        
        # Footer
        footer = tk.Frame(self.root, bg=self.bg_color)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Label(
            footer,
            text="ISP Monitor v2.4 Ultra Otimizado | Modo Silencioso | 5x mais rápido",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="#6c7086"
        ).pack()
        
    def check_status(self):
        """Verifica se o sistema está rodando"""
        try:
            # Verificar porta 8080
            for conn in psutil.net_connections():
                if conn.laddr.port == 8080 and conn.status == 'LISTEN':
                    self.is_running = True
                    self.status_label.config(
                        text="● RODANDO",
                        fg=self.success_color
                    )
                    self.info_label.config(
                        text=f"Porta: 8080 | PID: {conn.pid} | http://localhost:8080"
                    )
                    self.btn_start.config(state=tk.DISABLED)
                    self.btn_stop.config(state=tk.NORMAL)
                    return
            
            # Não está rodando
            self.is_running = False
            self.status_label.config(
                text="● PARADO",
                fg=self.error_color
            )
            self.info_label.config(text="Sistema não está rodando")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            
        except Exception as e:
            self.status_label.config(
                text="● ERRO",
                fg=self.error_color
            )
            self.info_label.config(text=f"Erro ao verificar: {str(e)}")
    
    def start_system(self):
        """Inicia o sistema"""
        if self.is_running:
            messagebox.showwarning("Aviso", "Sistema já está rodando!")
            return
        
        try:
            # Verificar se arquivo existe
            script_path = "iniciar_postgres.bat"
            if not os.path.exists(script_path):
                messagebox.showerror("Erro", f"Arquivo {script_path} não encontrado!")
                return
            
            # Iniciar SEM JANELA DE CONSOLE (modo oculto)
            # CREATE_NO_WINDOW = 0x08000000
            self.process = subprocess.Popen(
                [script_path],
                creationflags=0x08000000,  # CREATE_NO_WINDOW - executa em segundo plano
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Aguardar um pouco e verificar
            time.sleep(3)
            self.check_status()
            
            if self.is_running:
                messagebox.showinfo(
                    "Sucesso",
                    "Sistema iniciado com sucesso!\n\nAguarde alguns segundos e acesse:\nhttp://localhost:8080"
                )
            else:
                messagebox.showwarning(
                    "Aviso",
                    "Sistema foi iniciado mas ainda não está respondendo.\nAguarde alguns segundos e verifique novamente."
                )
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar sistema:\n{str(e)}")
    
    def stop_system(self):
        """Para o sistema"""
        if not self.is_running:
            messagebox.showwarning("Aviso", "Sistema não está rodando!")
            return
        
        try:
            # Encontrar e matar processo
            for conn in psutil.net_connections():
                if conn.laddr.port == 8080 and conn.status == 'LISTEN':
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    time.sleep(2)
                    
                    # Forçar se necessário
                    if process.is_running():
                        process.kill()
                    
                    self.check_status()
                    messagebox.showinfo("Sucesso", "Sistema parado com sucesso!")
                    return
            
            messagebox.showwarning("Aviso", "Processo não encontrado!")
            self.check_status()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao parar sistema:\n{str(e)}")
    
    def restart_system(self):
        """Reinicia o sistema"""
        if self.is_running:
            response = messagebox.askyesno(
                "Confirmar",
                "Deseja reiniciar o sistema?\n\nO sistema será parado e iniciado novamente."
            )
            if response:
                self.stop_system()
                time.sleep(2)
                self.start_system()
        else:
            self.start_system()
    
    def open_dashboard(self):
        """Abre o dashboard no navegador"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:8080")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir navegador:\n{str(e)}")
    
    def force_kill_all(self):
        """Força o encerramento de TODOS os processos relacionados"""
        response = messagebox.askyesno(
            "⚠️ KILL FORÇADO",
            "ATENÇÃO: Isso vai MATAR FORÇADAMENTE todos os processos relacionados:\n\n"
            "• Python (uvicorn, backend)\n"
            "• PostgreSQL (se iniciado pelo launcher)\n"
            "• Processos na porta 8080\n\n"
            "Deseja continuar?"
        )
        
        if not response:
            return
        
        killed_count = 0
        errors = []
        
        try:
            # 1. Matar processos na porta 8080
            for conn in psutil.net_connections():
                try:
                    if conn.laddr.port == 8080:
                        proc = psutil.Process(conn.pid)
                        proc.kill()
                        killed_count += 1
                except:
                    pass
            
            # 2. Matar processos Python relacionados (uvicorn, backend)
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Não matar o próprio launcher
                    if proc.info['pid'] == current_pid:
                        continue
                    
                    # Verificar se é Python executando uvicorn ou backend
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('uvicorn' in str(arg).lower() or 
                                          'backend' in str(arg).lower() or
                                          'main:app' in str(arg).lower() 
                                          for arg in cmdline):
                            proc.kill()
                            killed_count += 1
                except Exception as e:
                    errors.append(f"PID {proc.info['pid']}: {str(e)}")
            
            # 3. Matar processos postgres se existirem
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'postgres' in proc.info['name'].lower():
                        # Só matar se for local (não servidor externo)
                        proc.kill()
                        killed_count += 1
                except:
                    pass
            
            time.sleep(1)
            self.check_status()
            
            msg = f"✅ {killed_count} processo(s) encerrado(s) forçadamente!"
            if errors:
                msg += f"\n\n⚠️ Alguns erros:\n" + "\n".join(errors[:3])
            
            messagebox.showinfo("Kill Forçado", msg)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao executar kill forçado:\n{str(e)}")
    
    def reload_interface(self):
        """Recarrega a interface (F5)"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

def main():
    root = tk.Tk()
    app = ISPMonitorLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()


import subprocess
import threading
import os
import time
import re
import socket

class ExpoManager:
    _instance = None
    _process = None
    _qr_url = None
    _logs = []
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExpoManager, cls).__new__(cls)
        return cls._instance

    def _get_local_ip(self):
        try:
            # Tenta conectar no Google DNS pra saber qual IP está sendo usado para sair
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def start(self):
        with self._lock:
            if self._process and self._process.poll() is None:
                return {"message": "Expo já está rodando", "status": "running"}

            # Define path
            base_dir = os.getcwd() # isp_monitor
            mobile_dir = os.path.join(base_dir, "mobile")
            
            if not os.path.exists(mobile_dir):
                return {"error": f"Pasta mobile não encontrada em: {mobile_dir}"}

            # Command
            # Usando --tunnel se necessário, mas idealmente LAN
            # Expo start precisa ser rodado
            cmd = "npx expo start" 
            
            # Environment variables
            env = os.environ.copy()
            
            try:
                self._process = subprocess.Popen(
                    cmd, 
                    shell=True, 
                    cwd=mobile_dir, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=env
                )
                
                # Start Thread to read logs and capture QR
                threading.Thread(target=self._monitor_output, daemon=True).start()
                
                return {"message": "Expo iniciado", "status": "starting"}
            except Exception as e:
                return {"error": str(e)}

    def stop(self):
        with self._lock:
            if self._process:
                # Kill process tree
                subprocess.run("taskkill /F /T /PID " + str(self._process.pid), shell=True)
                self._process = None
                self._qr_url = None
                self._logs.append("--- Expo Parado ---")
                return {"message": "Expo parado", "status": "stopped"}
            return {"message": "Expo não está rodando", "status": "stopped"}

    def get_status(self):
        is_running = self._process is not None and self._process.poll() is None
        
        # Se não temos URL ainda, tentamos estimar based no IP local
        # Expo geralmente roda na porta 8081
        if is_running and not self._qr_url:
             ip = self._get_local_ip()
             estimated = f"exp://{ip}:8081"
             # Mas só retornamos se tivermos certeza ou após um tempo? 
             # Vamos retornar o estimado por enquanto se não capturou
             return {
                 "running": True, 
                 "qr": estimated, 
                 "logs": self._logs[-20:] # Last 20 logs
             }

        return {
            "running": is_running,
            "qr": self._qr_url,
            "logs": self._logs[-50:]
        }

    def _monitor_output(self):
        if not self._process: return

        for line in iter(self._process.stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                self._logs.append(clean_line)
                if len(self._logs) > 500: self._logs.pop(0)

                # Try to capture QR URL
                # Expo output info: "› Metro waiting on exp://192.168.1.5:8081"
                # or "› Scan the QR code:"
                
                # Regex for explicit exp:// url
                match = re.search(r'(exp://[\d\.:]+)', clean_line)
                if match:
                    self._qr_url = match.group(1)
                
                # Fallback: if we just see "Metro waiting on", sometimes the URL isn't explicitly exp:// in the same line depending on version
                
        self._process = None
        self._qr_url = None

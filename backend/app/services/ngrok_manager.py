
import subprocess
import threading
import os
import time
import requests
import json
import logging

logger = logging.getLogger("api")

class NgrokManager:
    _instance = None
    _process = None
    _public_url = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NgrokManager, cls).__new__(cls)
        return cls._instance

    def _get_ngrok_path(self):
        # Check known paths
        paths = [
            os.path.join(os.getcwd(), "tools", "ngrok", "ngrok.exe"),
            os.path.join(os.getcwd(), "ngrok.exe"),
            "ngrok" # System PATH
        ]
        for p in paths:
            if p == "ngrok":
                # Check if in path
                from shutil import which
                if which("ngrok"): return "ngrok"
            elif os.path.exists(p):
                return p
        return None

    def start(self, port=8080):
        with self._lock:
            if self._process:
                # Check if still running
                if self._process.poll() is None:
                    # Already running, try to fetch URL just in case
                    self._fetch_url()
                    return {"message": "Ngrok já está rodando", "status": "running", "url": self._public_url}
            
            # If standard ngrok is running outside our control, we might be able to hook into it
            if self._check_external_ngrok():
                 return {"message": "Ngrok detectado (Externo)", "status": "running", "url": self._public_url}

            exe_path = self._get_ngrok_path()
            if not exe_path:
                return {"error": "Executável do Ngrok não encontrado em tools/ngrok/ngrok.exe"}

            # Command: ngrok http 8000 --log=stdout
            # We use --log=stdout so we might parse if needed, but the API endpoint 4040 is better
            cmd = [exe_path, "http", str(port)]
            
            try:
                # Start process
                # Creation flag to hide window on Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                self._process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo
                )
                
                # Wait a bit for it to start
                for _ in range(10):
                    time.sleep(1)
                    if self._fetch_url():
                        return {"message": "Ngrok iniciado", "status": "running", "url": self._public_url}
                    if self._process.poll() is not None:
                         return {"error": "Ngrok fechou logo após iniciar. Verifique autenticação (ngrok config add-authtoken)."}

                return {"message": "Ngrok iniciado (URL pendente)", "status": "starting"}
            except Exception as e:
                logger.error(f"Failed to start ngrok: {e}")
                return {"error": str(e)}

    def stop(self):
        with self._lock:
            if self._process:
                # Force kill
                try:
                    subprocess.run(f"taskkill /F /PID {self._process.pid}", shell=True)
                except:
                    self._process.kill()
                self._process = None
            
            # Kill any rogue ngrok process
            try:
                subprocess.run("taskkill /F /IM ngrok.exe", shell=True)
            except: pass

            self._public_url = None
            return {"message": "Ngrok parado", "status": "stopped"}

    def get_status(self):
        # 1. Check valid process object
        is_running = self._process is not None and self._process.poll() is None
        
        # 2. If valid process object not found, check system (maybe restarted manually)
        if not is_running:
             # Try to hit the local API to see if it's alive
             if self._check_external_ngrok():
                 is_running = True

        return {
            "running": is_running,
            "url": self._public_url
        }

    def _fetch_url(self):
        try:
            # Ngrok exposes a local API on port 4040 by default
            res = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            data = res.json()
            tunnels = data.get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    self._public_url = t.get("public_url")
                    return True
        except:
            pass
        return False

    def _check_external_ngrok(self):
        # Try to contact the ngrok API regardless of who started it
        if self._fetch_url():
             return True
        return False


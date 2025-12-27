import sys
import os
import importlib
try:
    import tkinter
    import PIL
    import requests
    import psutil
except ImportError as e:
    print(f"[ERRO] Falta biblioteca: {e.name}")
    sys.exit(1) # Código de erro 1 = Falta Lib

# Verifica integridade básica de sintaxe do launcher
launcher_path = "launcher.pyw"
if not os.path.exists(launcher_path):
    print("[ERRO] Arquivo launcher.pyw desapareceu!")
    sys.exit(2)

try:
    with open(launcher_path, "r", encoding="utf-8") as f:
        content = f.read()
        # Verifica erros estúpidos comuns (como o que tivemos)
        if "self.root = root" not in content and "super().__init__" not in content:
            # Pode ser um falso positivo se o código mudar muito, mas por hora é válido
            # Melhor: apenas compilar para ver se tem erro de sintaxe
            pass
        
        compile(content, launcher_path, 'exec')
        pass
except SyntaxError as e:
    print(f"[ERRO] O Launcher tem erro de sintaxe: {e}")
    sys.exit(3)
except Exception as e:
    print(f"[ERRO] Falha ao ler launcher: {e}")
    sys.exit(4)

print("[OK] Launcher integro.")
sys.exit(0) # Sucesso

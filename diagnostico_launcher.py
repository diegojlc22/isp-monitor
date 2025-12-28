import sys
import os

print("=== DIAGNÓSTICO DO LAUNCHER ===")
print(f"Python: {sys.version}")
print(f"Diretório: {os.getcwd()}")

# Teste 1: Tkinter básico
print("\n[1/3] Testando Tkinter...")
try:
    import tkinter as tk
    print("✅ Tkinter importado com sucesso")
    
    # Tenta criar uma janela simples
    root = tk.Tk()
    root.title("Teste")
    root.geometry("300x100")
    
    label = tk.Label(root, text="✅ Tkinter funciona!", font=("Arial", 14))
    label.pack(pady=20)
    
    button = tk.Button(root, text="Fechar", command=root.destroy)
    button.pack()
    
    print("✅ Janela criada! Deve estar visível agora.")
    print("   Feche a janela para continuar...")
    
    root.mainloop()
    print("✅ Janela fechada normalmente")
    
except Exception as e:
    print(f"❌ ERRO no Tkinter: {e}")
    import traceback
    traceback.print_exc()

# Teste 2: Imports do launcher
print("\n[2/3] Testando imports do launcher...")
try:
    import subprocess
    import webbrowser
    from pathlib import Path
    print("✅ Todos os imports OK")
except Exception as e:
    print(f"❌ ERRO nos imports: {e}")

# Teste 3: Verificar arquivos
print("\n[3/3] Verificando arquivos...")
files_to_check = [
    "scripts/self_heal.py",
    "startup.log",
    ".env"
]

for file in files_to_check:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"{status} {file}")

print("\n=== FIM DO DIAGNÓSTICO ===")
input("\nPressione ENTER para fechar...")

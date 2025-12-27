import tkinter as tk
from tkinter import messagebox
import sys

try:
    print("Iniciando Teste Tkinter...")
    root = tk.Tk()
    root.title("Teste Debug")
    root.geometry("300x200")
    
    label = tk.Label(root, text=f"Python {sys.version}\nTKINTER OK!")
    label.pack(expand=True)
    
    print("Janela criada. Aguardando loop...")
    
    # Fecha sozinho depois de 3 segundos para nao travar o teste
    root.after(3000, root.destroy)
    root.mainloop()
    print("Teste Concluido.")
    
except Exception as e:
    print(f"ERRO FATAL: {e}")

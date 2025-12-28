import tkinter as tk
from tkinter import messagebox

try:
    root = tk.Tk()
    root.title("Teste Tkinter")
    root.geometry("400x200")
    
    label = tk.Label(root, text="Se você está vendo isso, o Tkinter funciona!", font=("Arial", 12))
    label.pack(pady=50)
    
    button = tk.Button(root, text="Fechar", command=root.destroy)
    button.pack()
    
    root.mainloop()
except Exception as e:
    with open("tkinter_error.log", "w") as f:
        f.write(str(e))

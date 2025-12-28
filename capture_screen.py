import os
from PIL import ImageGrab
import time

def capture_burst():
    print("Iniciando captura em rajada...")
    os.makedirs("captures", exist_ok=True)
    for i in range(15):
        screenshot = ImageGrab.grab()
        save_path = f"captures/shoot_{i}.png"
        screenshot.save(save_path)
        print(f"Salvo: {save_path}")
        time.sleep(0.5)

if __name__ == "__main__":
    # Pequeno delay inicial para dar tempo do Launcher abrir
    time.sleep(1)
    capture_burst()

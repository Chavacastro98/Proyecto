import os
import sys
import time
import tkinter as tk
from PIL import ImageGrab

sys.path.insert(0, r"c:\Proyecto\Proyecto\software\telemetria2.0")
from app import TelemetriaApp

def main():
    root = tk.Tk()
    app = TelemetriaApp(root)
    root.update()
    
    # Activar modo demo para poblar datos y gráficas
    app.var_demo.set(True)
    app._on_toggle_demo()
    
    # Dejar que corra unos ciclos para que se dibujen las curvas y tarjetas
    for _ in range(15):
        root.update()
        time.sleep(0.1)
    
    # Obtener geometría y capturar pantalla de la ventana
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    
    bbox = (x, y, x + w, y + h)
    out_path = r"c:\Proyecto\Proyecto\documentos\imagenes\telemetria_gui_actual.png"
    img = ImageGrab.grab(bbox=bbox)
    img.save(out_path)
    print(f"Captured: {out_path} ({os.path.getsize(out_path)} bytes)")
    
    root.destroy()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para capturar las ventanas reales de TelemetriaApp
"""

import os
import sys
import time
import ctypes
from ctypes import windll, wintypes, byref
from PIL import Image

directorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

import tkinter as tk
from telemetria.app import TelemetriaApp

def capturar_ventana(tk_win, filename):
    tk_win.update_idletasks()
    tk_win.update()
    time.sleep(0.1)
    
    frame_str = tk_win.wm_frame()
    frame_id = int(frame_str, 16) if frame_str.startswith('0x') else int(frame_str)
    
    user32 = windll.user32
    gdi32 = windll.gdi32
    
    rect = wintypes.RECT()
    user32.GetWindowRect(frame_id, byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    
    if w <= 0 or h <= 0:
        print(f"Error: tamaño inválido ({w}x{h}) para {filename}")
        return False
        
    hdc_win = user32.GetWindowDC(frame_id)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    SRCCOPY = 0x00CC0020
    b_res = gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_win, 0, 0, SRCCOPY)
    
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)
        ]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    
    buf = (ctypes.c_char * (w * h * 4))()
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, byref(buf), byref(bmi), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    
    img_rgb = img.convert('RGB')
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    img_rgb.save(filename)
    print(f"Capturado exitosamente: {filename} ({w}x{h})")
    
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(frame_id, hdc_win)
    return True

def main():
    root = tk.Tk()
    app = TelemetriaApp(root)
    root.geometry("1280x880+50+30")
    root.update_idletasks()
    root.update()
    
    # Activar modo demo y simular datos
    app.var_demo.set(True)
    app._on_toggle_demo()
    app._toggle_forzar_corriente_demo()
    app.iniciar_grabacion()
    
    # Simular varios ciclos para poblar buffers y gráficas
    print("Simulando ciclos de telemetría...")
    for i in range(25):
        root.update_idletasks()
        root.update()
        time.sleep(0.1)
        
    capturar_ventana(root, "scratch/scada_01_principal_test.png")
    app.detener_grabacion()
    root.destroy()

if __name__ == "__main__":
    main()

import os
import sys
import time
import ctypes
from ctypes import windll, wintypes, byref, sizeof
from PIL import Image

directorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

import tkinter as tk
from telemetria.app import TelemetriaApp

def capturar_printwindow(tk_win, filename):
    tk_win.update_idletasks()
    tk_win.update()
    time.sleep(0.3)
    
    frame_str = tk_win.wm_frame()
    frame_id = int(frame_str, 16) if frame_str.startswith('0x') else int(frame_str)
    
    user32 = windll.user32
    gdi32 = windll.gdi32
    
    rect = wintypes.RECT()
    user32.GetWindowRect(frame_id, byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    user32.PrintWindow(frame_id, hdc_mem, 2)
    
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)
        ]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    
    buf = (ctypes.c_char * (w * h * 4))()
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, byref(buf), byref(bmi), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    img_rgb = img.convert('RGB')
    img_rgb.save(filename, quality=95)
    print("Saved:", filename, w, h)
    
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

root = tk.Tk()
app = TelemetriaApp(root)
root.geometry("1280x880+30+20")
root.update_idletasks()
root.update()

# Simular algunos datos
app._redibujar_grafica_vivo()
capturar_printwindow(root, "scratch/test_scada_printwindow.png")
root.destroy()

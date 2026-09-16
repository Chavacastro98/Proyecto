import os
import sys
import time
import ctypes
from ctypes import windll, wintypes, byref, sizeof
from PIL import Image
import tkinter as tk

root = tk.Tk()
root.title("Test Capture Window")
root.geometry("600x400+100+100")
root.configure(bg="#1e1e2f")
lbl = tk.Label(root, text="TEST WINDOW CAPTURE", font=("Helvetica", 16, "bold"), fg="#ffffff", bg="#1e1e2f")
lbl.pack(pady=40)
btn = tk.Button(root, text="Boton de Prueba", bg="#10b981", fg="white", font=("Helvetica", 12))
btn.pack(pady=20)

root.update_idletasks()
root.update()
time.sleep(0.3)

client_id = root.winfo_id()
frame_str = root.wm_frame()
frame_id = int(frame_str, 16) if frame_str.startswith('0x') else int(frame_str)

user32 = windll.user32
gdi32 = windll.gdi32

# Method A: PrintWindow with PW_RENDERFULLCONTENT (2) on frame_id
rect = wintypes.RECT()
user32.GetWindowRect(frame_id, byref(rect))
w = rect.right - rect.left
h = rect.bottom - rect.top

hdc_screen = user32.GetDC(0)
hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
gdi32.SelectObject(hdc_mem, hbmp)

PW_RENDERFULLCONTENT = 2
res = user32.PrintWindow(frame_id, hdc_mem, PW_RENDERFULLCONTENT)

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
img_a = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
img_a.save("scratch/test_printwindow_frame.png")
print("PrintWindow frame result:", res, w, h)

# Method B: PrintWindow on client_id
cw = root.winfo_width()
ch = root.winfo_height()
hbmp_c = gdi32.CreateCompatibleBitmap(hdc_screen, cw, ch)
gdi32.SelectObject(hdc_mem, hbmp_c)
res_c = user32.PrintWindow(client_id, hdc_mem, PW_RENDERFULLCONTENT)
bmi.biWidth = cw
bmi.biHeight = -ch
buf_c = (ctypes.c_char * (cw * ch * 4))()
gdi32.GetDIBits(hdc_mem, hbmp_c, 0, ch, byref(buf_c), byref(bmi), 0)
img_b = Image.frombuffer('RGBA', (cw, ch), buf_c, 'raw', 'BGRA', 0, 1)
img_b.save("scratch/test_printwindow_client.png")
print("PrintWindow client result:", res_c, cw, ch)

# Method C: BitBlt from client DC (GetDC(client_id))
hdc_client = user32.GetDC(client_id)
gdi32.BitBlt(hdc_mem, 0, 0, cw, ch, hdc_client, 0, 0, 0x00CC0020)
buf_client = (ctypes.c_char * (cw * ch * 4))()
gdi32.GetDIBits(hdc_mem, hbmp_c, 0, ch, byref(buf_client), byref(bmi), 0)
img_c = Image.frombuffer('RGBA', (cw, ch), buf_client, 'raw', 'BGRA', 0, 1)
img_c.save("scratch/test_bitblt_client.png")
print("BitBlt client saved:", cw, ch)

# Method D: Screen BitBlt using exact winfo_rootx/rooty/width/height from desktop DC
rx = root.winfo_rootx()
ry = root.winfo_rooty()
hbmp_d = gdi32.CreateCompatibleBitmap(hdc_screen, cw, ch)
gdi32.SelectObject(hdc_mem, hbmp_d)
gdi32.BitBlt(hdc_mem, 0, 0, cw, ch, hdc_screen, rx, ry, 0x00CC0020)
gdi32.GetDIBits(hdc_mem, hbmp_d, 0, ch, byref(buf_client), byref(bmi), 0)
img_d = Image.frombuffer('RGBA', (cw, ch), buf_client, 'raw', 'BGRA', 0, 1)
img_d.save("scratch/test_desktop_client.png")
print("Desktop BitBlt client saved:", rx, ry, cw, ch)

# Method E: Screen BitBlt including titlebar using DWMWA_EXTENDED_FRAME_BOUNDS from desktop DC
dwmapi = windll.dwmapi
rect_dwm = wintypes.RECT()
dwmapi.DwmGetWindowAttribute(frame_id, 9, byref(rect_dwm), sizeof(rect_dwm))
dw_w = rect_dwm.right - rect_dwm.left
dw_h = rect_dwm.bottom - rect_dwm.top
hbmp_e = gdi32.CreateCompatibleBitmap(hdc_screen, dw_w, dw_h)
gdi32.SelectObject(hdc_mem, hbmp_e)
gdi32.BitBlt(hdc_mem, 0, 0, dw_w, dw_h, hdc_screen, rect_dwm.left, rect_dwm.top, 0x00CC0020)
bmi.biWidth = dw_w
bmi.biHeight = -dw_h
buf_e = (ctypes.c_char * (dw_w * dw_h * 4))()
gdi32.GetDIBits(hdc_mem, hbmp_e, 0, dw_h, byref(buf_e), byref(bmi), 0)
img_e = Image.frombuffer('RGBA', (dw_w, dw_h), buf_e, 'raw', 'BGRA', 0, 1)
img_e.save("scratch/test_dwm_desktop.png")
print("DWM desktop BitBlt saved:", rect_dwm.left, rect_dwm.top, dw_w, dw_h)

root.destroy()

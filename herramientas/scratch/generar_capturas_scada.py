#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script generador de capturas HD de todas las ventanas del SCADA en funcionamiento
"""

import os
import sys
import time
import math
import ctypes
from ctypes import windll, wintypes, byref, sizeof
import numpy as np
from PIL import Image

directorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

import tkinter as tk
from telemetria.app import TelemetriaApp

def capturar_frame(tk_win, filename):
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
    
    if w <= 0 or h <= 0:
        print(f"Error: tamaño inválido ({w}x{h})")
        return False
        
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    
    PW_RENDERFULLCONTENT = 2
    res = user32.PrintWindow(frame_id, hdc_mem, PW_RENDERFULLCONTENT)
    if not res:
        user32.PrintWindow(frame_id, hdc_mem, 0)
        
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
    bmi.biCompression = 0
    
    buf = (ctypes.c_char * (w * h * 4))()
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, byref(buf), byref(bmi), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1)
    
    img_rgb = img.convert('RGB')
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    img_rgb.save(filename, quality=95)
    print(f"-> Guardado con PrintWindow: {filename} ({w}x{h} px)")
    
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    return True

def generar_datos_ricos(app):
    """Simula una trayectoria de telemetría viva de 150 segundos."""
    app.modo_demo = True
    app.var_demo.set(True)
    app.conectado = True
    app.etapa_activa_idx = 2  # Etapa 3: Zincado Celda Hull
    app.etapa_corriendo = True
    app.etapa_segundos_restantes = 85
    app.etapa_duracion_total = 120
    app.etapa_segundos_transcurridos = 35
    app.coulombs_total = 52.5
    app.area_placa_cm2 = 65.0
    app.peso_inicial_g = 42.1524
    app.peso_final_g = 42.1702
    
    # 150 muestras históricas
    for s in range(150):
        app.muestras_count = s + 1
        t_rel = float(s)
        
        # Rampas de temperatura suaves hacia setpoints
        # T1 SP=85, T2 SP=85, T3 SP=25, T4 SP=35
        p1 = min(1.0, s / 90.0)
        t1 = 24.0 + (85.0 - 24.0) * (1.0 - math.exp(-3.5 * p1)) + 0.15 * math.sin(s * 0.2)
        t2 = 24.0 + (85.0 - 24.0) * (1.0 - math.exp(-3.3 * p1)) + 0.12 * math.cos(s * 0.25)
        t3 = 25.0 + 0.1 * math.sin(s * 0.15)
        t4 = 24.0 + (35.0 - 24.0) * (1.0 - math.exp(-2.5 * p1)) + 0.08 * math.sin(s * 0.3)
        
        # Corriente: escalón activo a 1.50 A a partir de s >= 30
        if s >= 30:
            i_real = 1.50 + 0.012 * math.sin(s * 0.4)
            app.coulombs_total += i_real * 1.0
        else:
            i_real = 0.0
            
        d_t = [
            {"t": round(t1, 2), "sp": 85.0, "run": 1, "p": 22.5},
            {"t": round(t2, 2), "sp": 85.0, "run": 1, "p": 20.0},
            {"t": round(t3, 2), "sp": 25.0, "run": 1, "p": 8.0},
            {"t": round(t4, 2), "sp": 35.0, "run": 1, "p": 14.5}
        ]
        
        d_ph = {
            "p1": round(2.85 + 0.02 * math.sin(s * 0.08), 2),
            "p2": round(5.72 + 0.015 * math.cos(s * 0.05), 2),
            "v1": round(2.595 + 0.003 * math.sin(s * 0.08), 3),
            "v2": round(1.948 + 0.002 * math.cos(s * 0.05), 3),
            "on": 1
        }
        
        d_f = {
            "amps": 1.50 if s >= 30 else 0.0,
            "i_real": round(i_real, 2),
            "i1": round(i_real * 0.505, 2),
            "i2": round(i_real * 0.495, 2),
            "vs1": round(i_real * 0.505 * 1.0, 3),
            "vs2": round(i_real * 0.495 * 1.0, 3),
            "rele": 1 if s >= 30 else 0,
            "modo": 0,
            "duty": 20,
            "freq": 10,
            "gm": 1.002,
            "salud": 1
        }
        
        d_env = {
            "t": 24.5,
            "h": 48.5,
            "p": 1013.2
        }
        
        # Actualizar cálculos e historial
        e1 = 85.0 - t1
        e2 = 85.0 - t2
        e3 = 25.0 - t3
        e4 = 35.0 - t4
        app.iae_t1 += abs(e1)
        app.iae_t2 += abs(e2)
        app.iae_t3 += abs(e3)
        app.iae_t4 += abs(e4)
        
        app._actualizar_gui_datos(t_rel, d_t, d_ph, d_f, d_env)
        
    app._redibujar_grafica_vivo()
    app.root.update_idletasks()
    app.root.update()

def main():
    img_dir = os.path.join(directorio_raiz, "documentos", "imagenes")
    os.makedirs(img_dir, exist_ok=True)
    
    print("Iniciando entorno SCADA Tkinter...")
    root = tk.Tk()
    app = TelemetriaApp(root)
    root.geometry("1280x880+30+20")
    root.update_idletasks()
    root.update()
    
    # Poblar con datos de proceso en régimen permanente
    print("Inyectando telemetría realista y sintonía PI...")
    generar_datos_ricos(app)
    
    # 1. Ventana Principal del SCADA
    print("Capturando Ventana Principal del SCADA...")
    capturar_frame(root, os.path.join(img_dir, "scada_01_principal.png"))
    
    # 2. Ventana Modular de Actuadores y Osciloscopio TRIAC
    print("Capturando Ventana de Actuadores y Osciloscopio...")
    app.abrir_ventana_actuadores(canal_idx=0)
    w_act = app.win_actuadores
    w_act.win.geometry("1020x760+100+60")
    w_act.actualizar_datos()
    w_act.win.update_idletasks()
    w_act.win.update()
    capturar_frame(w_act.win, os.path.join(img_dir, "scada_02_actuadores.png"))
    w_act.win.destroy()
    app.win_actuadores = None
    
    # 3. Ventana Modular de Monitor de Errores e Índices IAE + Retrato de Fase
    print("Capturando Ventana de Errores e Índices IAE / Plano de Fase...")
    app.abrir_ventana_errores()
    w_err = app.win_errores
    w_err.win.geometry("1040x780+80+50")
    w_err.actualizar_datos()
    w_err.win.update_idletasks()
    w_err.win.update()
    capturar_frame(w_err.win, os.path.join(img_dir, "scada_03_errores.png"))
    w_err.win.destroy()
    app.win_errores = None
    
    # 4. Ventana Modular de Balanza Gravimétrica y Ley de Faraday
    print("Capturando Ventana de Balanza y Rendimiento Faradaico...")
    app.abrir_ventana_faraday()
    w_far = app.win_faraday
    w_far.win.geometry("1060x780+90+50")
    w_far.var_metal.set("ZN")
    w_far.var_peso_ini.set("42.1524")
    w_far.var_peso_fin.set("42.1702")
    w_far.var_area.set("65.0")
    w_far._recalcular()
    w_far.actualizar_datos()
    w_far.win.update_idletasks()
    w_far.win.update()
    capturar_frame(w_far.win, os.path.join(img_dir, "scada_04_faraday.png"))
    w_far.win.destroy()
    app.win_faraday = None
    
    # 5. Ventana Modular de Metrología y Calibración de pH
    print("Capturando Ventana de Metrología y Calibración de pH...")
    app.abrir_ventana_ph()
    w_ph = app.win_ph
    w_ph.win.geometry("1180x820+60+30")
    # Poblar buffers de oscilación de pH
    t_now = time.time()
    for k in range(50):
        t_k = k * 0.5
        v1_sim = 2.595 + 0.008 * math.sin(k * 0.2)
        v2_sim = 1.948 + 0.005 * math.cos(k * 0.25)
        ph1_sim = 2.85 + 0.02 * math.sin(k * 0.2)
        ph2_sim = 5.72 + 0.015 * math.cos(k * 0.25)
        w_ph.buf_t.append(t_k)
        w_ph.buf_v1.append(v1_sim)
        w_ph.buf_v2.append(v2_sim)
        w_ph.buf_ph1.append(ph1_sim)
        w_ph.buf_ph2.append(ph2_sim)
    w_ph.es_estable = True
    w_ph.duracion_estable = 3.5
    w_ph._actualizar_vista()
    w_ph.win.update_idletasks()
    w_ph.win.update()
    capturar_frame(w_ph.win, os.path.join(img_dir, "scada_05_ph.png"))
    w_ph.win.destroy()
    app.win_ph = None
    
    # 6. Ventana Modular de Diagnóstico de Hardware y Sensores
    print("Capturando Ventana de Diagnóstico de Hardware y Sensores...")
    app.abrir_ventana_diagnostico()
    w_diag = app.win_diag
    w_diag.win.geometry("1000x720+100+60")
    # Simular datos de estado de periféricos
    diag_data = {
        "aht": 1,
        "bmp": 1,
        "ads": 1,
        "dac": 1,
        "tc": [1, 1, 1, 1]
    }
    w_diag._actualizar_ui(diag_data)
    w_diag.agregar_evento_gui({
        "t_rel": 12.4,
        "etapa": "1. Limpieza",
        "severidad": "INFO",
        "sensor": "I2C ADS1115",
        "tipo": "Inicialización",
        "valor": "0x48",
        "desc": "Conversor ADC 16-bit verificado y sincronizado a 860 SPS."
    })
    w_diag.agregar_evento_gui({
        "t_rel": 35.0,
        "etapa": "2. Decapado",
        "severidad": "INFO",
        "sensor": "MAX6675 T2",
        "tipo": "Estabilidad SP",
        "valor": "85.0°C",
        "desc": "Alcanzada consigna isotérmica dentro de tolerancia ±0.5°C."
    })
    w_diag.agregar_evento_gui({
        "t_rel": 68.2,
        "etapa": "3. Zincado Hull",
        "severidad": "ADVERTENCIA",
        "sensor": "Shunts VCSS",
        "tipo": "Asimetría Corriente",
        "valor": "ΔI = 0.02 A",
        "desc": "Balance térmico en transistores N-MOSFET verificado por firmware."
    })
    w_diag.agregar_evento_gui({
        "t_rel": 115.6,
        "etapa": "3. Zincado Hull",
        "severidad": "INFO",
        "sensor": "Carga Faraday",
        "tipo": "Integración Q",
        "valor": "232.6 C",
        "desc": "Acumulación culombimétrica en rango previsto de rendimiento."
    })
    w_diag.win.update_idletasks()
    w_diag.win.update()
    capturar_frame(w_diag.win, os.path.join(img_dir, "scada_06_diagnostico.png"))
    w_diag.win.destroy()
    app.win_diag = None
    
    root.destroy()
    print("¡Todas las capturas se generaron y guardaron con éxito en documentos/imagenes/!")

if __name__ == "__main__":
    main()

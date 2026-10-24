#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
E.L.E.C.T.R.O.D.O-32 — PLANTA PILOTO DE ELECTRODEPOSICIÓN
Panel Maestro de Lanzamiento y Centro de Control (launcher.py)
===============================================================================
Equipo de Laboratorio para Experimentación y Control en Tiempo Real con
Obtención de Datos Operativos (ESP32-S3 RTOS 2.0 / ATmega328P / SCADA PC)
===============================================================================
"""

import sys
import os
import subprocess
import webbrowser

DIR_RAIZ = os.path.dirname(os.path.abspath(__file__))


def lanzar_modulo(cmd, cwd=None):
    """Ejecuta un comando en un subproceso desacoplado."""
    cwd = cwd or DIR_RAIZ
    try:
        if sys.platform == "win32":
            subprocess.Popen(cmd, cwd=cwd, shell=True)
        else:
            subprocess.Popen(cmd, cwd=cwd)
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar el comando '{cmd}': {e}")


def abrir_telemetria_2():
    cmd = f'"{sys.executable}" "{os.path.join(DIR_RAIZ, "software", "telemetria2.0")}"'
    lanzar_modulo(cmd, os.path.join(DIR_RAIZ, "software"))


def abrir_telemetria_1():
    cmd = f'"{sys.executable}" -m telemetria'
    lanzar_modulo(cmd, os.path.join(DIR_RAIZ, "software"))


def abrir_exportador():
    cmd = f'"{sys.executable}" "{os.path.join(DIR_RAIZ, "software", "exportar_graficas_offline.py")}"'
    lanzar_modulo(cmd, os.path.join(DIR_RAIZ, "software"))


def abrir_manual_quimico():
    ruta = os.path.join(DIR_RAIZ, "documentos", "manuales", "MANUAL_DE_OPERACION_QUIMICA.html")
    webbrowser.open(f"file:///{os.path.abspath(ruta).replace(os.sep, '/')}")


def abrir_diagramas():
    ruta_script = os.path.join(DIR_RAIZ, "visualizacion", "diagramas", "visor_diagramas.py")
    if os.path.exists(ruta_script):
        cmd = f'"{sys.executable}" "{ruta_script}"'
        lanzar_modulo(cmd, os.path.dirname(ruta_script))
    else:
        ruta_html = os.path.join(DIR_RAIZ, "visualizacion", "diagramas", "index.html")
        webbrowser.open(f"file:///{os.path.abspath(ruta_html).replace(os.sep, '/')}")


def abrir_previews():
    ruta = os.path.join(DIR_RAIZ, "visualizacion", "preview", "index.html")
    webbrowser.open(f"file:///{os.path.abspath(ruta).replace(os.sep, '/')}")


def abrir_panel_web():
    webbrowser.open("http://192.168.4.1")


def abrir_eventos():
    ruta = os.path.join(DIR_RAIZ, "eventos")
    if sys.platform == "win32":
        os.startfile(ruta)
    else:
        webbrowser.open(f"file:///{os.path.abspath(ruta).replace(os.sep, '/')}")


def abrir_pcb():
    ruta = os.path.join(DIR_RAIZ, "hardware", "pcb", "placa_madre_esp32s3_uno")
    if sys.platform == "win32":
        os.startfile(ruta)
    else:
        webbrowser.open(f"file:///{os.path.abspath(ruta).replace(os.sep, '/')}")


def abrir_academicos():
    ruta = os.path.join(DIR_RAIZ, "documentos", "academicos")
    if sys.platform == "win32":
        os.startfile(ruta)
    else:
        webbrowser.open(f"file:///{os.path.abspath(ruta).replace(os.sep, '/')}")


def iniciar_interfaz_grafica():
    """Lanza la interfaz gráfica de usuario en Tkinter."""
    try:
        import tkinter as tk
    except ImportError:
        iniciar_consola()
        return

    root = tk.Tk()
    root.title("E.L.E.C.T.R.O.D.O-32 — Panel de Control Maestro")
    root.geometry("720x680")
    root.minsize(680, 620)
    root.configure(bg="#0b1120")

    # Estilos y encabezado
    header_frame = tk.Frame(root, bg="#0f172a", pady=15, padx=20)
    header_frame.pack(fill="x")

    lbl_title = tk.Label(
        header_frame,
        text="E.L.E.C.T.R.O.D.O-32 | CONTROL CIBERFÍSICO",
        font=("Segoe UI", 14, "bold"),
        fg="#38bdf8",
        bg="#0f172a"
    )
    lbl_title.pack(anchor="w")

    lbl_sub = tk.Label(
        header_frame,
        text="ESP32-S3 RTOS 2.0 | Placa Madre Rev 5.0 | SCADA Telemetría & Faraday",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#0f172a"
    )
    lbl_sub.pack(anchor="w")

    content_frame = tk.Frame(root, bg="#0b1120", padx=25, pady=12)
    content_frame.pack(fill="both", expand=True)

    botones = [
        ("1. Iniciar Telemetría 2.0 SCADA (Canal A1 - RTOS 2.0) [ACTIVO]", "#0284c7", "#ffffff", abrir_telemetria_2),
        ("2. Iniciar Telemetría 1.0 SCADA (Versión Base de Referencia)", "#1e293b", "#94a3b8", abrir_telemetria_1),
        ("3. Exportador Offline de Gráficas Científicas (300 DPI)", "#1e293b", "#cbd5e1", abrir_exportador),
        ("4. Abrir Manual de Operación Química y Laboratorio (HTML)", "#0d9488", "#ffffff", abrir_manual_quimico),
        ("5. Hardware PCB: Placa Madre Rev 5.0 (KiCad, Gerbers, 3D STEP)", "#7c3aed", "#ffffff", abrir_pcb),
        ("6. Eventos y Expos: Innovafest 2026 y Congreso SMEQ (CTS-C51)", "#d97706", "#ffffff", abrir_eventos),
        ("7. Abrir Visor de Diagramas de Arquitectura (RTOS)", "#1e293b", "#cbd5e1", abrir_diagramas),
        ("8. Abrir Hub de Previews y Simuladores Web", "#1e293b", "#cbd5e1", abrir_previews),
        ("9. Abrir Panel Web ESP32 en Navegador (192.168.4.1)", "#4338ca", "#ffffff", abrir_panel_web),
        ("10. Abrir Protocolos y Documentos Académicos", "#1e293b", "#cbd5e1", abrir_academicos),
    ]

    for texto, bg, fg, accion in botones:
        btn = tk.Button(
            content_frame,
            text=texto,
            command=accion,
            font=("Segoe UI", 10, "bold" if bg not in ("#1e293b", "#4338ca") else "normal"),
            bg=bg,
            fg=fg,
            activebackground="#334155",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            anchor="w"
        )
        btn.pack(fill="x", pady=3)

    footer_frame = tk.Frame(root, bg="#0f172a", pady=8, padx=20)
    footer_frame.pack(fill="x", side="bottom")
    lbl_foot = tk.Label(
        footer_frame,
        text="Universidad de Guadalajara (CUCEI) — Salvador² C Dev Team",
        font=("Segoe UI", 8),
        fg="#64748b",
        bg="#0f172a"
    )
    lbl_foot.pack(anchor="e")

    root.mainloop()


def iniciar_consola():
    """Modo interactivo en consola."""
    print("=" * 70)
    print("  E.L.E.C.T.R.O.D.O-32 — PANEL DE CONTROL INTERACTIVO")
    print("=" * 70)
    print("  [1] Iniciar Telemetria 2.0 SCADA (Canal A1 - RTOS 2.0)")
    print("  [2] Iniciar Telemetria 1.0 SCADA (Version Base)")
    print("  [3] Exportador Offline de Graficas Cientificas (300 DPI)")
    print("  [4] Abrir Manual de Operacion Quimica (HTML)")
    print("  [5] Explorar Hardware PCB (Placa Madre Rev 5.0)")
    print("  [6] Explorar Eventos y Expos (Innovafest y SMEQ)")
    print("  [7] Abrir Visor de Diagramas Tecnicos")
    print("  [8] Abrir Hub de Previews y Simulador Web")
    print("  [9] Abrir Panel Web ESP32 (http://192.168.4.1)")
    print("  [0] Salir")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        iniciar_consola()
    else:
        iniciar_interfaz_grafica()

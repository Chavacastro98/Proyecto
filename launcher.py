#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SISTEMA AUTOMATIZADO DE ELECTRODEPOSICIÓN (ESP32-S3 / ARDUINO NANO)
Panel Maestro de Lanzamiento y Centro de Control (launcher.py)
===============================================================================
Permite iniciar todos los módulos del sistema (SCADA, Manuales, Gráficas,
Visores de Diagramas y Documentación) mediante una interfaz gráfica moderna
o consola interactiva, sin requerir scripts batch complejos ni permisos
especiales de administrador.
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
        from tkinter import ttk
    except ImportError:
        iniciar_consola()
        return

    root = tk.Tk()
    root.title("Panel de Control Maestro — Electrodeposición ESP32-S3")
    root.geometry("680x620")
    root.minsize(620, 560)
    root.configure(bg="#0b1120")

    # Estilos y encabezado
    header_frame = tk.Frame(root, bg="#0f172a", pady=15, padx=20)
    header_frame.pack(fill="x")

    lbl_title = tk.Label(
        header_frame,
        text="SISTEMA AUTOMATIZADO DE ELECTRODEPOSICIÓN",
        font=("Segoe UI", 13, "bold"),
        fg="#38bdf8",
        bg="#0f172a"
    )
    lbl_title.pack(anchor="w")

    lbl_sub = tk.Label(
        header_frame,
        text="ESP32-S3 N16R8 RTOS 2.0 | SCADA Telemetría | Metrología de Faraday",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#0f172a"
    )
    lbl_sub.pack(anchor="w")

    content_frame = tk.Frame(root, bg="#0b1120", padx=25, pady=15)
    content_frame.pack(fill="both", expand=True)

    botones = [
        ("1. Iniciar Telemetría 2.0 SCADA (Canal A1 - RTOS 2.0) [ACTIVO]", "#0284c7", "#ffffff", abrir_telemetria_2),
        ("2. Iniciar Telemetría 1.0 SCADA (Versión Base de Referencia)", "#1e293b", "#94a3b8", abrir_telemetria_1),
        ("3. Exportador Offline de Gráficas Científicas (300 DPI)", "#1e293b", "#cbd5e1", abrir_exportador),
        ("4. Abrir Manual de Operación Química y Laboratorio (HTML)", "#0d9488", "#ffffff", abrir_manual_quimico),
        ("5. Abrir Visor de Diagramas de Arquitectura (RTOS)", "#1e293b", "#cbd5e1", abrir_diagramas),
        ("6. Abrir Hub de Previews y Simuladores Web", "#1e293b", "#cbd5e1", abrir_previews),
        ("7. Abrir Panel Web ESP32 en Navegador (192.168.4.1)", "#4338ca", "#ffffff", abrir_panel_web),
        ("8. Abrir Carpeta de Tesis y Documentación Académica", "#1e293b", "#cbd5e1", abrir_academicos),
    ]

    for texto, bg, fg, accion in botones:
        btn = tk.Button(
            content_frame,
            text=texto,
            command=accion,
            font=("Segoe UI", 10, "bold" if bg != "#1e293b" else "normal"),
            bg=bg,
            fg=fg,
            activebackground="#334155",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            anchor="w"
        )
        btn.pack(fill="x", pady=4)

    footer_frame = tk.Frame(root, bg="#0b1120", pady=10)
    footer_frame.pack(fill="x")

    lbl_foot = tk.Label(
        footer_frame,
        text="Python " + sys.version.split()[0] + " | Directorio: " + DIR_RAIZ,
        font=("Segoe UI", 8),
        fg="#64748b",
        bg="#0b1120"
    )
    lbl_foot.pack()

    root.mainloop()


def iniciar_consola():
    """Menú interactivo en modo texto si no está disponible la interfaz gráfica."""
    while True:
        print("\n" + "=" * 75)
        print("   SISTEMA AUTOMATIZADO DE ELECTRODEPOSICIÓN (ESP32-S3 / ARDUINO NANO)")
        print("   Panel Maestro de Lanzamiento y Centro de Control")
        print("=" * 75)
        print("   [1] Iniciar Telemetría 2.0 SCADA (Canal A1 - RTOS 2.0) [ACTIVO]")
        print("   [2] Iniciar Telemetría 1.0 SCADA (Versión Base)")
        print("   [3] Exportador Offline de Gráficas Científicas (300 DPI)")
        print("   [4] Abrir Manual de Operación Química (HTML)")
        print("   [5] Abrir Visor de Diagramas de Arquitectura")
        print("   [6] Abrir Hub de Previews y Simulador Web")
        print("   [7] Abrir Panel Web ESP32 (http://192.168.4.1)")
        print("   [8] Abrir Carpeta de Tesis y Documentos Académicos")
        print("   [0] Salir")
        print("=" * 75)
        opc = input("Seleccione una opción [0-8]: ").strip()

        if opc == "1":
            abrir_telemetria_2()
        elif opc == "2":
            abrir_telemetria_1()
        elif opc == "3":
            abrir_exportador()
        elif opc == "4":
            abrir_manual_quimico()
        elif opc == "5":
            abrir_diagramas()
        elif opc == "6":
            abrir_previews()
        elif opc == "7":
            abrir_panel_web()
        elif opc == "8":
            abrir_academicos()
        elif opc == "0":
            break
        else:
            print("[!] Opción inválida.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        iniciar_consola()
    else:
        iniciar_interfaz_grafica()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de verificación integral para telemetria2 (v2 SCADA):
- Inicialización limpia de interfaz con arquitectura desacoplada
- Verificación de los 3 paneles de subsistemas (Térmico, Galvánico, Metrología)
- Conmutación dinámica de vistas (3_EN_1, TERMICO, VCSS, TRIAC)
- Ciclos de redibujado Matplotlib en vivo con datos simulados
- Apertura de ventanas hijas (actuadores, errores, faraday, ph, diagnostico)
"""

import sys
import os
import tkinter as tk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from telemetria2.app import TelemetriaApp

def test_telemetria2_full():
    print("=== INICIANDO TEST TELEMETRÍA 2 (SCADA v2) ===")
    root = tk.Tk()
    root.withdraw()

    try:
        app = TelemetriaApp(root)
        print("[OK] TelemetriaApp inicializada correctamente")
        assert app.modo_grafica == "3_EN_1", f"Modo inicial inesperado: {app.modo_grafica}"
        assert len(app.botones_vista) == 4, f"Se esperaban 4 botones de vista, encontrados: {len(app.botones_vista)}"
        print("[OK] Botones de vista verificados:", list(app.botones_vista.keys()))

        # Verificar existencia de tarjetas en los 3 subsistemas
        assert hasattr(app, "card_t1") and hasattr(app, "card_t4")
        assert hasattr(app, "card_amp") and hasattr(app, "card_coulomb")
        assert hasattr(app, "card_ph") and hasattr(app, "card_env")
        print("[OK] Tarjetas de subsistemas (Térmico, Galvánico, Metrología) instanciadas correctamente")

        # Mock de datos de telemetría simulados
        d_t = [
            {"t": 45.2, "sp": 45.0, "p": 35.0, "run": 1},
            {"t": 44.8, "sp": 45.0, "p": 40.0, "run": 1},
            {"t": 18.2, "sp": 18.0, "p": 15.0, "run": 1},
            {"t": 55.1, "sp": 55.0, "p": 50.0, "run": 1},
        ]
        d_ph = {"p1": 7.02, "p2": 4.01, "on": 1}
        d_f = {"a": 1.48, "q": 125.4, "mode": "DC", "f": 0, "pk": 1.48, "avg": 1.48, "i1": 0.74, "i2": 0.74}
        d_env = {"t": 24.5, "h": 55.2}

        # Prueba de ciclo de actualización en modo 3_EN_1
        app.coulombs_total = 125.4
        app.muestras_count = 2
        app._actualizar_gui_datos(120.0, d_t, d_ph, d_f, d_env)
        print("[OK] Actualización de GUI en modo 3_EN_1 exitosa")

        # Probar cada uno de los modos de vista dinámica
        for modo in ["TERMICO", "VCSS", "TRIAC", "3_EN_1"]:
            app.cambiar_modo_grafica(modo)
            assert app.modo_grafica == modo
            # Enviar muestra adicional para forzar redraw
            app.muestras_count += 2
            app._actualizar_gui_datos(122.0, d_t, d_ph, d_f, d_env)
            print(f"[OK] Conmutacion a modo {modo} y redibujado Matplotlib: OK")

        # Verificar apertura de ventanas secundarias modulares
        app.abrir_ventana_actuadores(0)
        assert app.win_actuadores is not None and app.win_actuadores.win.winfo_exists()
        print("[OK] Ventana Actuadores abierta con éxito")

        app.abrir_ventana_faraday()
        assert app.win_faraday is not None and app.win_faraday.win.winfo_exists()
        print("[OK] Ventana Faraday abierta con éxito")

        app.abrir_ventana_errores()
        assert app.win_errores is not None and app.win_errores.win.winfo_exists()
        print("[OK] Ventana Errores abierta con éxito")

        app.abrir_ventana_ph()
        assert app.win_ph is not None and app.win_ph.win.winfo_exists()
        print("[OK] Ventana pH abierta con éxito")

        app.abrir_ventana_diagnostico()
        assert app.win_diag is not None and app.win_diag.win.winfo_exists()
        print("[OK] Ventana Diagnóstico abierta con éxito")

        # Cerrar ventanas
        app.win_actuadores.win.destroy()
        app.win_faraday.win.destroy()
        app.win_errores.win.destroy()
        app.win_ph.win.destroy()
        app.win_diag.win.destroy()

        print("=== TODAS LAS PRUEBAS DE TELEMETRÍA 2 PASARON EXITOSAMENTE ===")
    finally:
        try:
            root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    test_telemetria2_full()

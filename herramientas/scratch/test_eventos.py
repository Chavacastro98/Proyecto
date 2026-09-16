#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Sistema de Detección, Registro y Auditoría de Accidentes de Sensores.
"""

import os
import sys
import time
import tkinter as tk
import pandas as pd

# Asegurar path de importación
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telemetria.app import TelemetriaApp


def test_flujo_eventos():
    print("=== TEST DE AUDITORÍA Y REGISTRO DE EVENTOS DE SENSORES ===")
    root = tk.Tk()
    root.withdraw()

    app = TelemetriaApp(root)
    app.var_demo.set(True)
    app._on_toggle_demo()

    print("1. Iniciando grabación de ensayo...")
    app.iniciar_grabacion()

    time.sleep(0.5)

    # 1. Ciclos nominales
    print("2. Simulando 3 ciclos nominales...")
    time.sleep(3.0)

    # 2. Inyectar Salto Térmico EMI en T2 (+16.5°C)
    print("3. Inyectando 'salto_t2' (+16.5°C EMI spike)...")
    app.simular_accidente_sensor("salto_t2")
    time.sleep(3.0)

    # 3. Inyectar Desconexión de Termopar T1 (0.0°C)
    print("4. Inyectando 'desconexion_t1' (0.0°C open circuit)...")
    app.simular_accidente_sensor("desconexion_t1")
    time.sleep(5.0)

    # 4. Inyectar Desbalance de Shunts VCSS
    print("5. Inyectando 'desbalance_vcss' (I1=0.85A, I2=0.15A)...")
    app.simular_accidente_sensor("desbalance_vcss")
    time.sleep(4.0)

    # 5. Detener grabación
    print("6. Deteniendo grabación y consolidando auditoría...")
    app.detener_grabacion()

    print(f"\nEnsayo guardado en: {app.carpeta_ensayo_actual}")

    # Verificar existencia y contenido de registro_eventos_fallos.csv
    csv_ev = app.archivo_csv_eventos
    assert os.path.exists(csv_ev), f"El archivo {csv_ev} no existe"

    df_ev = pd.read_csv(csv_ev)
    print("\n--- CONTENIDO DE registro_eventos_fallos.csv ---")
    print(df_ev.to_string())

    assert len(df_ev) >= 4, f"Se esperaban al menos 4 eventos, se registraron {len(df_ev)}"
    tipos_registrados = df_ev["Tipo_Evento"].unique().tolist()
    print(f"\nTipos de eventos registrados: {tipos_registrados}")
    assert "SALTO_TERMICO_EMI" in tipos_registrados, "Falta SALTO_TERMICO_EMI"
    assert "SONDA_DESCONECTADA" in tipos_registrados, "Falta SONDA_DESCONECTADA"
    assert "RECUPERACION_SENSOR" in tipos_registrados, "Falta RECUPERACION_SENSOR"

    # Verificar resumen_receta.txt
    resumen_path = os.path.join(app.carpeta_ensayo_actual, "resumen_receta.txt")
    assert os.path.exists(resumen_path), f"El archivo {resumen_path} no existe"
    with open(resumen_path, "r", encoding="utf-8") as f:
        txt_res = f.read()

    print("\n--- SECCIÓN FINAL DE resumen_receta.txt ---")
    print(txt_res[-800:])

    assert "AUDITORÍA DE INCIDENCIAS Y ACCIDENTES DE SENSORES EN PROCESO" in txt_res
    assert "SALTO_TERMICO_EMI" in txt_res
    assert "SONDA_DESCONECTADA" in txt_res

    print("\n✅ TEST COMPLETADO CON ÉXITO: Todos los eventos, recuperaciones y auditorías fueron registrados correctamente.")
    root.destroy()
    return app.archivo_csv


if __name__ == "__main__":
    test_flujo_eventos()

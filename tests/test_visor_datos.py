#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS UNITARIAS: TEMA Y VISOR DE DATOS SQLITE (test_visor_datos.py)
=============================================================================
Valida la lógica de temas Día/Noche, las consultas SQL paginadas,
los filtros de etapa y la exportación en memoria/archivo temporal.
=============================================================================
"""

import os
import sys

import pandas as pd
import pytest

# Rutas
DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

from utilidades.gestor_db import GestorDB
from utilidades.tema import TEMA_DIA, TEMA_NOCHE, cargar_tema_preferido, guardar_tema_preferido
from ventanas.visor_datos import VISTAS_COLUMNAS


def test_temas_noche_y_dia(tmp_path, monkeypatch):
    test_json = str(tmp_path / "pref_tema.json")
    monkeypatch.setattr("utilidades.tema.RUTA_PREF_TEMA", test_json)

    # Por defecto debe ser noche
    t1 = cargar_tema_preferido()
    assert t1["nombre"] == "noche"
    assert "bg_app" in t1
    assert "plot_axes_bg" in t1

    # Guardar día y recargar
    guardar_tema_preferido("dia")
    t2 = cargar_tema_preferido()
    assert t2["nombre"] == "dia"
    assert t2["bg_app"] == TEMA_DIA["bg_app"]

    # Guardar noche y recargar
    guardar_tema_preferido("noche")
    t3 = cargar_tema_preferido()
    assert t3["nombre"] == "noche"


def test_vistas_columnas_registradas():
    assert "Resumen de Proceso" in VISTAS_COLUMNAS
    assert "Potencia VCSS" in VISTAS_COLUMNAS
    assert "Control Térmico (4 Tinas)" in VISTAS_COLUMNAS
    assert "Diagnóstico y Ambiente" in VISTAS_COLUMNAS

    cols_resumen = [c[0] for c in VISTAS_COLUMNAS["Resumen de Proceso"]]
    assert "tiempo_relativo_s" in cols_resumen
    assert "etapa_nombre" in cols_resumen
    assert "fuente_corriente_real_a" in cols_resumen


def test_consultas_paginadas_sqlite(tmp_path):
    db_file = str(tmp_path / "test_visor.db")
    gestor = GestorDB(ruta_sqlite=db_file)

    # Crear carpeta de ensayo simulada con 150 filas
    carpeta = tmp_path / "Ensayo_Paginacion_Test"
    carpeta.mkdir()

    filas = []
    for i in range(150):
        filas.append({
            "Timestamp_ISO": f"2026-10-28T12:00:{i%60:02d}",
            "Tiempo_Relativo_s": round(i * 0.1, 2),
            "Placa_ID": 1,
            "Ronda": "Ronda 1",
            "Etapa_Num": 1 if i < 50 else (2 if i < 100 else 3),
            "Etapa_Nombre": "Limpieza" if i < 50 else ("Decapado" if i < 100 else "Zincado"),
            "Etapa_Tiempo_s": i * 0.1,
            "Etapa_Duracion_s": 60.0,
            "Corriente_Target_A": 1.5 if i >= 100 else 0.0,
            "Modo_Corriente": "DC",
            "Fuente_Activa": 1 if i >= 100 else 0,
            "Fuente_Corriente_Real_A": 1.49 if i >= 100 else 0.0
        })

    df = pd.DataFrame(filas)
    df.to_csv(carpeta / "telemetria_completa.csv", index=False)

    ensayo_id = gestor.registrar_o_actualizar_ensayo_local(str(carpeta))
    assert ensayo_id is not None

    # Probar paginación directa en SQL
    with gestor.get_connection() as conn:
        cur = conn.cursor()

        # Total
        cur.execute("SELECT COUNT(*) FROM telemetria_10hz WHERE ensayo_id = ?", (ensayo_id,))
        total = cur.fetchone()[0]
        assert total == 150

        # Página 1 (filas 0..49)
        cur.execute("SELECT tiempo_relativo_s FROM telemetria_10hz WHERE ensayo_id = ? ORDER BY tiempo_relativo_s ASC LIMIT 50 OFFSET 0", (ensayo_id,))
        p1 = cur.fetchall()
        assert len(p1) == 50
        assert p1[0][0] == 0.0

        # Página 2 (filas 50..99)
        cur.execute("SELECT tiempo_relativo_s FROM telemetria_10hz WHERE ensayo_id = ? ORDER BY tiempo_relativo_s ASC LIMIT 50 OFFSET 50", (ensayo_id,))
        p2 = cur.fetchall()
        assert len(p2) == 50
        assert p2[0][0] == 5.0

        # Filtro por etapa Zincado
        cur.execute("SELECT COUNT(*) FROM telemetria_10hz WHERE ensayo_id = ? AND etapa_nombre LIKE '%Zincado%'", (ensayo_id,))
        c_zinc = cur.fetchone()[0]
        assert c_zinc == 50

        # Filtro por corriente > 0.05
        cur.execute("SELECT COUNT(*) FROM telemetria_10hz WHERE ensayo_id = ? AND fuente_corriente_real_a > 0.05", (ensayo_id,))
        c_curr = cur.fetchone()[0]
        assert c_curr == 50


def test_aplicar_tema_a_ventana_generica_y_figura():
    import tkinter as tk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from utilidades.tema import TEMA_DIA, aplicar_estilo_treeview, aplicar_tema_a_ventana_generica, estilizar_figura_matplotlib

    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter no disponible en este entorno: {e}")

    # Probar estilo treeview
    aplicar_estilo_treeview(TEMA_DIA)
    aplicar_estilo_treeview(TEMA_NOCHE)

    # Crear jerarquía de widgets para probar adaptación
    win = tk.Toplevel(root)
    hdr = tk.Frame(win, height=40)
    hdr.pack(fill="x")
    lbl_t = tk.Label(hdr, text="Titulo", fg="#94a3b8")
    lbl_t.pack()
    btn = tk.Button(hdr, text="Boton", bg="#1e293b", fg="#ffffff")
    btn.pack()

    body = tk.LabelFrame(win, text="Panel")
    body.pack(fill="both", expand=True)
    ent = tk.Entry(body)
    ent.pack()
    chk = tk.Checkbutton(body, text="Check")
    chk.pack()

    # Figura y canvas
    fig = Figure(figsize=(3, 2))
    ax = fig.add_subplot(1, 1, 1)
    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.get_tk_widget().pack()

    class ObjetoSimulado:
        def __init__(self, w, f, c):
            self.win = w
            self.fig = f
            self.canvas = c

    sim_obj = ObjetoSimulado(win, fig, canvas)

    # Adaptar a tema día
    aplicar_tema_a_ventana_generica(sim_obj, TEMA_DIA)
    assert win.cget("bg") == TEMA_DIA["bg_app"]
    assert fig.patch.get_facecolor() == (1.0, 1.0, 1.0, 1.0)  # Blanco puro en modo día
    assert ax.get_facecolor() == (1.0, 1.0, 1.0, 1.0)

    # Adaptar a tema noche
    aplicar_tema_a_ventana_generica(sim_obj, TEMA_NOCHE)
    assert win.cget("bg") == TEMA_NOCHE["bg_app"]

    # Probar estilizar figura aislada
    estilizar_figura_matplotlib(fig, canvas, TEMA_DIA)
    estilizar_figura_matplotlib(None, None, TEMA_DIA)

    root.destroy()

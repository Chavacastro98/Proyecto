#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
GENERADOR Y EXPORTADOR OFFLINE DE GRÁFICAS CIENTÍFICAS (300 DPI)
===================================================================================
Planta Piloto de Electrodeposición automatizada con ESP32 (RTOS 1.3 / RTOS 2.0)
Tesis de Licenciatura / SCADA Industrial

Permite inspeccionar carpetas de ensayos previos de:
- Telemetría 1.0 (telemetria/experimentos)
- Telemetría 2.0 (telemetria2.0/experimentos)
- Carpetas externas o archivos CSV arbitrarios

Genera la suite completa de 8 figuras científicas de alta resolución (300 DPI):
1. Perfil Electroquímico y Térmico (4 Tinas + TRIACs + Corriente Galvánica)
2. Seguimiento Dinámico de Errores e Índices IAE
3. Conmutación de TRIACs BTA24 y Potencia Activa en Watts
4. Rendimiento Faradaico, Culombimetría y Plano de Fase (e vs de/dt)
5. Dashboard de Diagnóstico Integral y Balance Térmico
6. Diagrama Gantt de Fases ISA-88 y Registro de Tiempos Muertos
7. Histórico Ambiental de Cabina y Estimación de Evaporación
8. Metrología VCSS: Reconstrucción ETS, Balance de Shunts y Salud de Celda
===================================================================================
"""

import os
import sys
import glob
import time
import csv
import subprocess
import threading
from datetime import datetime

# Soporte UTF-8 en consola de Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.scrolledtext as scrolledtext


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_TEL1 = os.path.join(BASE_DIR, "telemetria")
DIR_TEL2 = os.path.join(BASE_DIR, "telemetria2.0")

# Localizar script graficador base
SCRIPT_GRAF_TEL1 = os.path.join(DIR_TEL1, "graficar_datos.py")
SCRIPT_GRAF_TEL2 = os.path.join(DIR_TEL2, "graficar_datos.py")
SCRIPT_GRAFICADOR = SCRIPT_GRAF_TEL2 if os.path.exists(SCRIPT_GRAF_TEL2) else SCRIPT_GRAF_TEL1


def inspeccionar_ensayo(dir_ensayo):
    """
    Analiza una carpeta de ensayo y retorna un diccionario con metadatos:
    csv_path, muestras, duracion_min, num_graficas, estado, placa, ronda, fecha_str
    """
    info = {
        "dir": dir_ensayo,
        "nombre": os.path.basename(dir_ensayo),
        "csv_path": None,
        "muestras": 0,
        "duracion_min": 0.0,
        "num_graficas": 0,
        "graficas_completas": False,
        "estado_str": "Sin datos",
        "placa": "--",
        "ronda": "--",
        "fecha_str": "--",
        "es_valido": False
    }

    if not os.path.isdir(dir_ensayo):
        return info

    # Buscar CSV de telemetría principal
    csv_candidato = os.path.join(dir_ensayo, "telemetria_completa.csv")
    if not os.path.exists(csv_candidato):
        # Buscar cualquier CSV que no sea complementario
        csvs = [
            f for f in glob.glob(os.path.join(dir_ensayo, "*.csv"))
            if not any(x in os.path.basename(f) for x in ["metricas", "fallos", "tiempos_muertos", "calibraciones", "partitions"])
        ]
        if csvs:
            csv_candidato = max(csvs, key=os.path.getmtime)
        else:
            csv_candidato = None

    if not csv_candidato or not os.path.exists(csv_candidato):
        info["estado_str"] = "❌ Falta CSV"
        return info

    info["csv_path"] = csv_candidato

    # Contar gráficas existentes
    carpeta_graf = os.path.join(dir_ensayo, "graficas")
    pngs = glob.glob(os.path.join(carpeta_graf, "*.png")) if os.path.exists(carpeta_graf) else []
    info["num_graficas"] = len(pngs)
    info["graficas_completas"] = (len(pngs) >= 8)

    # Leer metadatos rápidos del CSV sin cargar librerías pesadas
    try:
        with open(csv_candidato, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                info["estado_str"] = "⚪ CSV Vacío (0 filas)"
                return info

            idx_t = header.index("Tiempo_Relativo_s") if "Tiempo_Relativo_s" in header else -1
            idx_placa = header.index("Placa_ID") if "Placa_ID" in header else -1
            idx_ronda = header.index("Ronda") if "Ronda" in header else -1
            idx_iso = header.index("Timestamp_ISO") if "Timestamp_ISO" in header else -1

            filas = 0
            t_max = 0.0
            primera_fila = None
            ultima_fila = None

            for row in reader:
                if not row or len(row) < 2:
                    continue
                if primera_fila is None:
                    primera_fila = row
                ultima_fila = row
                filas += 1

            info["muestras"] = filas
            if filas < 2:
                info["estado_str"] = "⚪ CSV Incompleto (<2 muestras)"
                return info

            info["es_valido"] = True

            if idx_t != -1 and ultima_fila and len(ultima_fila) > idx_t:
                try:
                    t_max = float(ultima_fila[idx_t])
                    info["duracion_min"] = round(t_max / 60.0, 1)
                except Exception:
                    pass

            if idx_placa != -1 and primera_fila and len(primera_fila) > idx_placa:
                info["placa"] = str(primera_fila[idx_placa]).strip() or "--"

            if idx_ronda != -1 and primera_fila and len(primera_fila) > idx_ronda:
                info["ronda"] = str(primera_fila[idx_ronda]).strip() or "--"

            if idx_iso != -1 and primera_fila and len(primera_fila) > idx_iso:
                iso_val = str(primera_fila[idx_iso]).strip()
                try:
                    # Formatear fecha legible
                    dt = datetime.fromisoformat(iso_val.replace("Z", ""))
                    info["fecha_str"] = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    info["fecha_str"] = iso_val[:16]
            else:
                mtime = os.path.getmtime(csv_candidato)
                info["fecha_str"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

    except Exception as e:
        info["estado_str"] = f"⚠️ Error lectura ({e})"
        return info

    if info["graficas_completas"]:
        info["estado_str"] = f"✅ {info['num_graficas']}/8 Gráficas Listas"
    elif info["num_graficas"] > 0:
        info["estado_str"] = f"⚠️ Parcial ({info['num_graficas']}/8 Gráficas)"
    else:
        info["estado_str"] = "⚡ Sin Gráficas (Pendiente)"

    return info


class ExportadorGraficasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Generador de Gráficas Científicas HD (300 DPI) — Telemetría & Telemetría 2.0")
        self.root.geometry("1120x720")
        self.root.minsize(980, 620)
        self.root.configure(bg="#0b1120")

        # Intentar icono si existe
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self.origen_var = tk.StringVar(value="TEL2")
        self.ensayos_cargados = []
        self.ensayo_seleccionado = None
        self.procesando = False
        self.cancelar_batch = False

        self._crear_interfaz()
        self.cargar_ensayos()

    def _crear_interfaz(self):
        # 1. ENCABEZADO SUPERIOR
        header = tk.Frame(self.root, bg="#0f172a", height=70, bd=0)
        header.pack(fill="x", side="top")

        h_content = tk.Frame(header, bg="#0f172a")
        h_content.pack(fill="both", expand=True, padx=20, pady=12)

        title_lbl = tk.Label(
            h_content,
            text="📊 Exportador y Generador Offline de Gráficas de Telemetría",
            font=("Segoe UI", 14, "bold"),
            fg="#f8fafc",
            bg="#0f172a"
        )
        title_lbl.pack(side="left", anchor="w")

        sub_lbl = tk.Label(
            h_content,
            text="Suite de 8 Figuras Científicas (300 DPI) • Compatible con Telemetría 1.0 y 2.0",
            font=("Segoe UI", 9),
            fg="#38bdf8",
            bg="#0f172a"
        )
        sub_lbl.pack(side="left", padx=15, anchor="w")

        # 2. BARRA DE FUENTE Y SELECTORES
        bar_frame = tk.Frame(self.root, bg="#1e293b", bd=1, relief="solid")
        bar_frame.pack(fill="x", padx=16, pady=10)

        f_inner = tk.Frame(bar_frame, bg="#1e293b")
        f_inner.pack(fill="x", padx=12, pady=8)

        lbl_src = tk.Label(f_inner, text="Explorar Ensayos:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#1e293b")
        lbl_src.pack(side="left", padx=(0, 10))

        rb2 = tk.Radiobutton(
            f_inner, text="⚡ Telemetría 2.0 (RTOS 2.0)", variable=self.origen_var, value="TEL2",
            font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#1e293b", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#38bdf8", command=self.cargar_ensayos
        )
        rb2.pack(side="left", padx=6)

        rb1 = tk.Radiobutton(
            f_inner, text="🧪 Telemetría 1.0 (v3.5)", variable=self.origen_var, value="TEL1",
            font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#1e293b", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#e2e8f0", command=self.cargar_ensayos
        )
        rb1.pack(side="left", padx=6)

        rb_custom = tk.Radiobutton(
            f_inner, text="📁 Carpeta Externa", variable=self.origen_var, value="CUSTOM",
            font=("Segoe UI", 9, "bold"), fg="#cbd5e1", bg="#1e293b", selectcolor="#0f172a",
            activebackground="#1e293b", activeforeground="#e2e8f0", command=self.seleccionar_carpeta_externa
        )
        rb_custom.pack(side="left", padx=6)

        # Separador vertical
        sep = tk.Frame(f_inner, width=1, bg="#475569")
        sep.pack(side="left", fill="y", padx=10, pady=2)

        btn_folder = tk.Button(
            f_inner, text="📁 Seleccionar Carpeta...", font=("Segoe UI", 9),
            bg="#334155", fg="#f8fafc", activebackground="#475569", activeforeground="#ffffff",
            bd=0, padx=10, pady=4, cursor="hand2", command=self.seleccionar_carpeta_externa
        )
        btn_folder.pack(side="left", padx=4)

        btn_csv = tk.Button(
            f_inner, text="📄 Seleccionar Archivo CSV...", font=("Segoe UI", 9),
            bg="#334155", fg="#f8fafc", activebackground="#475569", activeforeground="#ffffff",
            bd=0, padx=10, pady=4, cursor="hand2", command=self.seleccionar_archivo_csv
        )
        btn_csv.pack(side="left", padx=4)

        btn_refresh = tk.Button(
            f_inner, text="🔄 Recargar", font=("Segoe UI", 9),
            bg="#334155", fg="#93c5fd", activebackground="#475569", activeforeground="#ffffff",
            bd=0, padx=8, pady=4, cursor="hand2", command=self.cargar_ensayos
        )
        btn_refresh.pack(side="right", padx=4)

        # 3. CONTENEDOR PRINCIPAL (SPLIT: TABLA Y DETALLES)
        main_split = tk.PanedWindow(self.root, orient="vertical", bg="#0b1120", bd=0, sashwidth=4)
        main_split.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Panel superior: Treeview de Ensayos
        tree_frame = tk.Frame(main_split, bg="#1e293b", bd=1, relief="solid")
        main_split.add(tree_frame, height=270)

        # Filtro de búsqueda rápida
        filter_bar = tk.Frame(tree_frame, bg="#1e293b")
        filter_bar.pack(fill="x", padx=10, pady=(8, 4))

        lbl_filtro = tk.Label(filter_bar, text="🔍 Filtrar:", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b")
        lbl_filtro.pack(side="left", padx=(0, 6))

        self.filtro_entry = tk.Entry(filter_bar, font=("Segoe UI", 9), bg="#0f172a", fg="#f8fafc", insertbackground="#38bdf8", bd=1, relief="solid")
        self.filtro_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.filtro_entry.bind("<KeyRelease>", lambda e: self._filtrar_arbol())

        self.lbl_conteo = tk.Label(filter_bar, text="0 ensayos encontrados", font=("Segoe UI", 9), fg="#38bdf8", bg="#1e293b")
        self.lbl_conteo.pack(side="right", padx=4)

        # Estilo del Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#0f172a",
            foreground="#f8fafc",
            fieldbackground="#0f172a",
            bordercolor="#334155",
            borderwidth=0,
            rowheight=26,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#1e293b",
            foreground="#93c5fd",
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("Custom.Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

        # Scrollbar y Treeview
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("carpeta", "fecha", "placa", "ronda", "muestras", "duracion", "estado"),
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y", padx=(0, 6), pady=(0, 8))
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        self.tree.heading("carpeta", text="Carpeta de Ensayo")
        self.tree.heading("fecha", text="Fecha / Hora")
        self.tree.heading("placa", text="Placa")
        self.tree.heading("ronda", text="Ronda")
        self.tree.heading("muestras", text="Muestras")
        self.tree.heading("duracion", text="Duración")
        self.tree.heading("estado", text="Estado Gráficas")

        self.tree.column("carpeta", width=280, anchor="w")
        self.tree.column("fecha", width=130, anchor="center")
        self.tree.column("placa", width=70, anchor="center")
        self.tree.column("ronda", width=90, anchor="center")
        self.tree.column("muestras", width=80, anchor="center")
        self.tree.column("duracion", width=85, anchor="center")
        self.tree.column("estado", width=190, anchor="center")

        self.tree.bind("<<TreeviewSelect>>", self._on_ensayo_seleccionado)
        self.tree.bind("<Double-1>", lambda e: self.generar_grafica_seleccionada())

        # Panel inferior: Botones de Acción, Progreso y Log
        bottom_frame = tk.Frame(main_split, bg="#0b1120")
        main_split.add(bottom_frame, height=280)

        # BARRA DE ACCIONES PRINCIPALES
        act_bar = tk.Frame(bottom_frame, bg="#0b1120")
        act_bar.pack(fill="x", pady=(4, 8))

        self.btn_generar_uno = tk.Button(
            act_bar,
            text="📊 Generar Gráficas del Ensayo Seleccionado",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            state="disabled",
            command=self.generar_grafica_seleccionada
        )
        self.btn_generar_uno.pack(side="left", padx=(0, 8))

        self.btn_generar_lote = tk.Button(
            act_bar,
            text="⚡ Generar Todas las Pendientes (Lote)",
            font=("Segoe UI", 10, "bold"),
            bg="#d97706",
            fg="#ffffff",
            activebackground="#f59e0b",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            command=self.generar_todas_pendientes
        )
        self.btn_generar_lote.pack(side="left", padx=4)

        self.btn_abrir_carpeta = tk.Button(
            act_bar,
            text="📂 Abrir Carpeta de Gráficas",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            state="disabled",
            command=self.abrir_carpeta_graficas
        )
        self.btn_abrir_carpeta.pack(side="left", padx=4)

        self.btn_cancelar = tk.Button(
            act_bar,
            text="⏹ Cancelar Proceso",
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#ef4444",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            state="disabled",
            command=self.cancelar_operacion
        )
        self.btn_cancelar.pack(side="right", padx=(4, 0))

        # Barra de progreso
        prog_bar_frame = tk.Frame(bottom_frame, bg="#0b1120")
        prog_bar_frame.pack(fill="x", pady=(0, 6))

        self.progreso = ttk.Progressbar(prog_bar_frame, orient="horizontal", mode="determinate")
        self.progreso.pack(fill="x", side="left", expand=True)

        self.lbl_progreso_pct = tk.Label(prog_bar_frame, text="Listo", font=("Segoe UI", 9), fg="#94a3b8", bg="#0b1120", width=18, anchor="e")
        self.lbl_progreso_pct.pack(side="right", padx=(8, 0))

        # Log en tiempo real
        log_frame = tk.Frame(bottom_frame, bg="#1e293b", bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True)

        self.txt_log = scrolledtext.ScrolledText(
            log_frame,
            bg="#030712",
            fg="#a7f3d0",
            insertbackground="#ffffff",
            font=("Consolas", 9),
            bd=0,
            padx=8,
            pady=6
        )
        self.txt_log.pack(fill="both", expand=True)
        self._log(">> Sistema listo. Selecciona un ensayo para inspeccionar o generar sus gráficas.")

    # -------------------------------------------------------------------------
    # GESTIÓN Y CARGA DE ENSAYOS
    # -------------------------------------------------------------------------
    def _log(self, mensaje):
        """Escribe un mensaje en el área de log de la interfaz."""
        def _write():
            self.txt_log.insert(tk.END, mensaje + "\n")
            self.txt_log.see(tk.END)
        self.root.after(0, _write)

    def obtener_directorio_actual(self):
        val = self.origen_var.get()
        if val == "TEL1":
            return os.path.join(DIR_TEL1, "experimentos")
        elif val == "TEL2":
            return os.path.join(DIR_TEL2, "experimentos")
        return getattr(self, "carpeta_personalizada", None)

    def cargar_ensayos(self):
        dir_exp = self.obtener_directorio_actual()
        self.ensayos_cargados.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not dir_exp or not os.path.exists(dir_exp):
            self._log(f">> [AVISO] El directorio no existe o está vacío: {dir_exp}")
            self.lbl_conteo.config(text="0 ensayos encontrados")
            return

        self._log(f">> Escaneando ensayos en: {dir_exp}")

        # Listar subdirectorios que comiencen con Ensayo_ o contengan CSVs
        subcarpetas = []
        try:
            for item in os.listdir(dir_exp):
                sub_path = os.path.join(dir_exp, item)
                if os.path.isdir(sub_path) and not item.startswith("."):
                    subcarpetas.append(sub_path)
        except Exception as e:
            self._log(f">> [ERROR] Error al explorar carpetas: {e}")
            return

        # Ordenar por fecha de modificación más reciente
        subcarpetas.sort(key=lambda p: os.path.getmtime(p), reverse=True)

        for sub in subcarpetas:
            info = inspeccionar_ensayo(sub)
            if info["csv_path"]:
                self.ensayos_cargados.append(info)

        self._poblar_arbol(self.ensayos_cargados)

    def _poblar_arbol(self, lista):
        for row in self.tree.get_children():
            self.tree.delete(row)

        pendientes = 0
        completos = 0

        for info in lista:
            if info["graficas_completas"]:
                completos += 1
            elif info["es_valido"]:
                pendientes += 1

            self.tree.insert(
                "",
                tk.END,
                iid=info["dir"],
                values=(
                    info["nombre"],
                    info["fecha_str"],
                    info["placa"],
                    info["ronda"],
                    f"{info['muestras']} pts",
                    f"{info['duracion_min']} min",
                    info["estado_str"]
                )
            )

        total = len(lista)
        self.lbl_conteo.config(text=f"{total} ensayos ({pendientes} sin gráficas, {completos} listos)")
        self._log(f">> Escaneo finalizado: {total} ensayos encontrados ({pendientes} pendientes de graficar).")

    def _filtrar_arbol(self):
        query = self.filtro_entry.get().strip().lower()
        if not query:
            self._poblar_arbol(self.ensayos_cargados)
            return

        filtrados = [
            e for e in self.ensayos_cargados
            if query in e["nombre"].lower() or query in str(e["placa"]).lower() or query in str(e["ronda"]).lower()
        ]
        self._poblar_arbol(filtrados)

    def seleccionar_carpeta_externa(self):
        initial = getattr(self, "carpeta_personalizada", BASE_DIR)
        dir_sel = filedialog.askdirectory(title="Seleccionar Carpeta de Experimentos o Ensayo", initialdir=initial)
        if not dir_sel:
            return

        self.carpeta_personalizada = dir_sel
        self.origen_var.set("CUSTOM")

        # Verificar si la carpeta seleccionada ES un ensayo individual (tiene telemetria_completa.csv directamente)
        csv_directo = os.path.join(dir_sel, "telemetria_completa.csv")
        if os.path.exists(csv_directo):
            self.ensayos_cargados.clear()
            info = inspeccionar_ensayo(dir_sel)
            self.ensayos_cargados.append(info)
            self._poblar_arbol(self.ensayos_cargados)
            self.tree.selection_set(dir_sel)
            self._log(f">> Ensayo individual seleccionado: {dir_sel}")
        else:
            # Es un contenedor de ensayos
            self.cargar_ensayos()

    def seleccionar_archivo_csv(self):
        initial = getattr(self, "carpeta_personalizada", BASE_DIR)
        f_csv = filedialog.askopenfilename(
            title="Seleccionar archivo CSV de telemetría",
            initialdir=initial,
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not f_csv:
            return

        dir_padre = os.path.dirname(os.path.abspath(f_csv))
        self.carpeta_personalizada = dir_padre
        self.origen_var.set("CUSTOM")

        info = inspeccionar_ensayo(dir_padre)
        info["csv_path"] = f_csv
        self.ensayos_cargados = [info]
        self._poblar_arbol(self.ensayos_cargados)
        self.tree.selection_set(dir_padre)
        self._log(f">> Archivo CSV cargado directamente: {f_csv}")

    def _on_ensayo_seleccionado(self, event):
        sel = self.tree.selection()
        if not sel:
            self.ensayo_seleccionado = None
            self.btn_generar_uno.config(state="disabled")
            self.btn_abrir_carpeta.config(state="disabled")
            return

        dir_sel = sel[0]
        ensayo = next((e for e in self.ensayos_cargados if e["dir"] == dir_sel), None)
        self.ensayo_seleccionado = ensayo

        if ensayo and ensayo["es_valido"]:
            self.btn_generar_uno.config(state="normal")
        else:
            self.btn_generar_uno.config(state="disabled")

        if ensayo and os.path.exists(os.path.join(dir_sel, "graficas")):
            self.btn_abrir_carpeta.config(state="normal")
        else:
            self.btn_abrir_carpeta.config(state="disabled")

    def abrir_carpeta_graficas(self):
        if not self.ensayo_seleccionado:
            return
        c_graf = os.path.join(self.ensayo_seleccionado["dir"], "graficas")
        if not os.path.exists(c_graf):
            os.makedirs(c_graf, exist_ok=True)

        if sys.platform == "win32":
            os.startfile(c_graf)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", c_graf])
        else:
            subprocess.Popen(["xdg-open", c_graf])

    # -------------------------------------------------------------------------
    # EJECUCIÓN DE GENERADOR DE GRÁFICAS (SUBPROCESS AISLADO)
    # -------------------------------------------------------------------------
    def _ejecutar_graficador(self, csv_path):
        """Ejecuta graficar_datos.py de forma aislada y emite el progreso línea a línea."""
        cmd = [sys.executable, SCRIPT_GRAFICADOR, csv_path]
        self._log(f">> Ejecutando: {os.path.basename(csv_path)}")

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        for line in proc.stdout:
            line_str = line.strip()
            if line_str:
                self._log(f"   {line_str}")
                # Extraer avance numérico si está presente
                if ">> [" in line_str and "/8]" in line_str:
                    try:
                        num = int(line_str.split(">> [")[1].split("/8]")[0])
                        self.root.after(0, lambda n=num: self.progreso.config(value=n * 12.5))
                        self.root.after(0, lambda n=num: self.lbl_progreso_pct.config(text=f"Figura {n}/8 ({int(n*12.5)}%)"))
                    except Exception:
                        pass

        proc.wait()
        return proc.returncode == 0

    def generar_grafica_seleccionada(self):
        if not self.ensayo_seleccionado or self.procesando:
            return

        ensayo = self.ensayo_seleccionado
        if not ensayo["es_valido"] or not ensayo["csv_path"]:
            messagebox.showwarning(
                "Ensayo Incompleto",
                f"El ensayo '{ensayo['nombre']}' no contiene muestras suficientes para generar gráficas."
            )
            return

        self._iniciar_proceso()
        threading.Thread(target=self._hilo_generar_uno, args=(ensayo,), daemon=True).start()

    def _hilo_generar_uno(self, ensayo):
        self._log(f"\n=========================================================================")
        self._log(f">> INICIANDO GENERACIÓN DE GRÁFICAS: {ensayo['nombre']}")
        self._log(f"=========================================================================")
        self.progreso.config(value=0)
        self.lbl_progreso_pct.config(text="Procesando...")

        exito = self._ejecutar_graficador(ensayo["csv_path"])

        if exito:
            self._log(f">> ✅ ¡Suite de 8 gráficas científicas HD generada con éxito!")
            # Actualizar metadatos
            nuevo_info = inspeccionar_ensayo(ensayo["dir"])
            for idx, e in enumerate(self.ensayos_cargados):
                if e["dir"] == ensayo["dir"]:
                    self.ensayos_cargados[idx] = nuevo_info
                    break
            self.root.after(0, lambda: self._poblar_arbol(self.ensayos_cargados))
            self.root.after(0, lambda: self.tree.selection_set(ensayo["dir"]))
            self.root.after(0, lambda: self.btn_abrir_carpeta.config(state="normal"))
            self.root.after(0, lambda: messagebox.showinfo(
                "Gráficas Generadas",
                f"✅ Las 8 gráficas científicas (300 DPI) se han generado con éxito para:\n\n{ensayo['nombre']}\n\nGuardadas en:\n{os.path.join(ensayo['dir'], 'graficas')}"
            ))
        else:
            self._log(f">> ❌ Hubo un error al generar las gráficas.")
            self.root.after(0, lambda: messagebox.showerror(
                "Error al Graficar",
                f"Ocurrió un error al procesar el archivo CSV de {ensayo['nombre']}. Revisa el log para más detalles."
            ))

        self.root.after(0, self._finalizar_proceso)

    def generar_todas_pendientes(self):
        if self.procesando:
            return

        pendientes = [e for e in self.ensayos_cargados if e["es_valido"] and not e["graficas_completas"]]
        if not pendientes:
            messagebox.showinfo("Sin Pendientes", "Todos los ensayos válidos ya tienen sus 8 gráficas científicas generadas.")
            return

        resp = messagebox.askyesno(
            "Generar Gráficas en Lote",
            f"Se encontraron {len(pendientes)} ensayos pendientes de gráficas.\n\n¿Deseas procesar todos automáticamente en lote?"
        )
        if not resp:
            return

        self._iniciar_proceso()
        self.cancelar_batch = False
        threading.Thread(target=self._hilo_generar_batch, args=(pendientes,), daemon=True).start()

    def _hilo_generar_batch(self, lista_pendientes):
        total = len(lista_pendientes)
        self._log(f"\n=========================================================================")
        self._log(f">> INICIANDO GENERACIÓN EN LOTE DE {total} ENSAYOS PENDIENTES")
        self._log(f"=========================================================================")

        completados = 0
        for i, ens in enumerate(lista_pendientes):
            if self.cancelar_batch:
                self._log(">> [AVISO] Generación en lote cancelada por el usuario.")
                break

            self._log(f"\n>> [{i+1}/{total}] Procesando: {ens['nombre']}")
            self.root.after(0, lambda idx=i: self.lbl_progreso_pct.config(text=f"Ensayo {idx+1}/{total}"))

            exito = self._ejecutar_graficador(ens["csv_path"])
            if exito:
                completados += 1
                nuevo_info = inspeccionar_ensayo(ens["dir"])
                for idx_c, e in enumerate(self.ensayos_cargados):
                    if e["dir"] == ens["dir"]:
                        self.ensayos_cargados[idx_c] = nuevo_info
                        break

            self.root.after(0, lambda idx=i: self.progreso.config(value=((idx+1)/total)*100))

        self.root.after(0, lambda: self._poblar_arbol(self.ensayos_cargados))
        self._log(f"\n>> ✅ Proceso por lotes finalizado: {completados}/{total} ensayos generados.")
        self.root.after(0, lambda: messagebox.showinfo(
            "Proceso en Lote Terminado",
            f"Se generaron las gráficas para {completados} de {total} ensayos procesados."
        ))
        self.root.after(0, self._finalizar_proceso)

    def cancelar_operacion(self):
        self.cancelar_batch = True
        self._log(">> Solicitud de cancelación enviada...")

    def _iniciar_proceso(self):
        self.procesando = True
        self.btn_generar_uno.config(state="disabled")
        self.btn_generar_lote.config(state="disabled")
        self.btn_cancelar.config(state="normal")

    def _finalizar_proceso(self):
        self.procesando = False
        self.cancelar_batch = False
        self.btn_cancelar.config(state="disabled")
        self.btn_generar_lote.config(state="normal")
        self.lbl_progreso_pct.config(text="Listo")
        if self.ensayo_seleccionado and self.ensayo_seleccionado["es_valido"]:
            self.btn_generar_uno.config(state="normal")


# =============================================================================
# MODO LÍNEA DE COMANDOS (CLI)
# =============================================================================
def modo_consola(ruta_entrada):
    """Permite ejecutar el generador pasando una carpeta o CSV como argumento."""
    print(f">> Analizando ruta: {ruta_entrada}")
    if os.path.isfile(ruta_entrada) and ruta_entrada.endswith(".csv"):
        target_csv = ruta_entrada
    elif os.path.isdir(ruta_entrada):
        info = inspeccionar_ensayo(ruta_entrada)
        target_csv = info.get("csv_path")
        if not target_csv:
            print(f"[ERROR] No se encontró telemetria_completa.csv en: {ruta_entrada}")
            sys.exit(1)
    else:
        print(f"[ERROR] La ruta especificada no existe: {ruta_entrada}")
        sys.exit(1)

    print(f">> Generando gráficas desde: {target_csv}")
    res = subprocess.run([sys.executable, SCRIPT_GRAFICADOR, target_csv])
    sys.exit(res.returncode)


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--gui"):
        modo_consola(sys.argv[1])
    else:
        root = tk.Tk()
        app = ExportadorGraficasApp(root)
        root.mainloop()


if __name__ == "__main__":
    main()

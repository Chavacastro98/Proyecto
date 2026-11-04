#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
EXPLORADOR VISUAL DE BASE DE DATOS LOCAL (visor_datos.py) - RTOS 2.0
=============================================================================
Ventana independiente de inspección de alto rendimiento para telemetría
y registros de ensayos sobre SQLite local (ensayos_local.db).
- Carga paginada instantánea (LIMIT ? OFFSET ?) sin demoras de memoria.
- Filtros rápidos por Etapas ISA-88, Corriente Activa y Vistas de Columnas.
- Búsqueda en tiempo real y exportación de muestras filtradas a CSV ligero.
=============================================================================
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd

from utilidades.gestor_db import GestorDB, RUTA_DB_LOCAL
from utilidades.tema import cargar_tema_preferido, aplicar_tema_a_ventana_generica


VISTAS_COLUMNAS = {
    "Resumen de Proceso": [
        ("tiempo_relativo_s", "Tiempo (s)", 80),
        ("etapa_nombre", "Etapa ISA-88", 120),
        ("fuente_corriente_real_a", "I Real (A)", 90),
        ("fuente_corriente_consigna_a", "I Target (A)", 90),
        ("t1_limpieza_temp_c", "T1 (°C)", 75),
        ("t2_decapado_temp_c", "T2 (°C)", 75),
        ("t3_celdahull_temp_c", "T3 Hull (°C)", 85),
        ("t4_niquelado_temp_c", "T4 Níquel (°C)", 90),
        ("ph_tina1", "pH T1", 70),
        ("carga_acumulada_coulombs", "Carga (C)", 95),
        ("masa_teorica_faraday_mg", "Faraday (mg)", 95)
    ],
    "Potencia VCSS": [
        ("tiempo_relativo_s", "Tiempo (s)", 80),
        ("etapa_nombre", "Etapa", 110),
        ("fuente_activa", "Activa", 65),
        ("fuente_modo_pulsado", "Pulsado", 70),
        ("fuente_corriente_consigna_a", "Consigna (A)", 95),
        ("fuente_corriente_real_a", "Corriente (A)", 95),
        ("fuente_corriente_shunt1_a", "Shunt 1 (A)", 90),
        ("fuente_corriente_shunt2_a", "Shunt 2 (A)", 90),
        ("fuente_voltaje_shunt1_v", "V Shunt 1 (V)", 95),
        ("fuente_voltaje_shunt2_v", "V Shunt 2 (V)", 95),
        ("fuente_amplitud_dac", "DAC Code", 80),
        ("fuente_salud_celda", "Salud Celda", 100)
    ],
    "Control Térmico (4 Tinas)": [
        ("tiempo_relativo_s", "Tiempo (s)", 80),
        ("etapa_nombre", "Etapa", 110),
        ("t1_limpieza_temp_c", "T1 Medida", 80),
        ("t1_limpieza_sp_c", "T1 SP", 75),
        ("t1_triac_potencia_pct", "T1 Pot (%)", 85),
        ("t2_decapado_temp_c", "T2 Medida", 80),
        ("t2_decapado_sp_c", "T2 SP", 75),
        ("t2_triac_potencia_pct", "T2 Pot (%)", 85),
        ("t3_celdahull_temp_c", "T3 Medida", 80),
        ("t3_celdahull_sp_c", "T3 SP", 75),
        ("t3_triac_potencia_pct", "T3 Pot (%)", 85),
        ("t4_niquelado_temp_c", "T4 Medida", 80),
        ("t4_niquelado_sp_c", "T4 SP", 75),
        ("t4_triac_potencia_pct", "T4 Pot (%)", 85),
        ("energia_termica_wh", "Energía (Wh)", 95)
    ],
    "Diagnóstico y Ambiente": [
        ("tiempo_relativo_s", "Tiempo (s)", 80),
        ("timestamp_iso", "Timestamp ISO", 160),
        ("etapa_num", "Etapa #", 65),
        ("etapa_tiempo_s", "Tiempo Etapa (s)", 110),
        ("ambiente_temp_c", "T Amb (°C)", 85),
        ("ambiente_humedad_pct", "Humedad (%)", 90),
        ("ambiente_presion_hpa", "Presión (hPa)", 95),
        ("ph_modulo_activo", "pH ON", 65),
        ("ph_interlock_activo", "Interlock pH", 90)
    ]
}


class VentanaVisorDatos:
    """Ventana de inspección tabular optimizada sobre base SQLite."""

    def __init__(self, parent_app, ruta_sqlite=None):
        self.parent = parent_app
        self.db = GestorDB(ruta_sqlite=ruta_sqlite or RUTA_DB_LOCAL)
        self.tema = getattr(parent_app, "tema_actual", cargar_tema_preferido())

        self.win = tk.Toplevel(parent_app.root if hasattr(parent_app, "root") else None)
        self.win.title("Explorador de Datos de Ensayos — SQLite Local")
        self.win.geometry("1180x680")
        self.win.minsize(900, 500)
        self.win.configure(bg=self.tema["bg_app"])

        # Estado de Paginación y Filtros
        self.ensayo_actual_id = None
        self.nombre_ensayo_actual = ""
        self.pagina_actual = 1
        self.filas_por_pagina = 100
        self.total_paginas = 1
        self.total_filas_filtradas = 0
        self.filtro_etapa_var = tk.StringVar(value="TODAS")
        self.filtro_solo_corriente_var = tk.BooleanVar(value=False)
        self.vista_columnas_var = tk.StringVar(value="Resumen de Proceso")
        self.busqueda_texto_var = tk.StringVar(value="")

        try:
            self._crear_ui()
            self._cargar_lista_ensayos()
            self.aplicar_tema(self.tema)
            self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception as e:
            try:
                self.win.destroy()
            except Exception:
                pass
            raise e

    def _crear_ui(self):
        # 1. ENCABEZADO Y SELECTOR DE ENSAYO
        hdr = tk.Frame(self.win, bg=self.tema["bg_header"], height=54, bd=1, relief="solid")
        hdr.pack(fill="x", side="top", padx=8, pady=(8, 4))

        tk.Label(
            hdr,
            text="📊 EXPLORADOR DE BASE DE DATOS LOCAL",
            font=("Segoe UI", 11, "bold"),
            fg=self.tema["accent_primary"],
            bg=self.tema["bg_header"]
        ).pack(side="left", padx=12, pady=10)

        tk.Label(
            hdr,
            text="Ensayo:",
            font=("Segoe UI", 9, "bold"),
            fg=self.tema["fg_dim"],
            bg=self.tema["bg_header"]
        ).pack(side="left", padx=(10, 4))

        self.combo_ensayos = ttk.Combobox(hdr, width=42, state="readonly", font=("Segoe UI", 9))
        self.combo_ensayos.pack(side="left", padx=4, pady=8)
        self.combo_ensayos.bind("<<ComboboxSelected>>", self._on_ensayo_seleccionado)

        btn_ref = tk.Button(
            hdr,
            text="🔄 Recargar",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema["bg_card_inner"],
            fg=self.tema["fg_text"],
            activebackground=self.tema["border"],
            activeforeground=self.tema["fg_text"],
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._cargar_lista_ensayos
        )
        btn_ref.pack(side="left", padx=6)

        self.btn_exportar = tk.Button(
            hdr,
            text="📥 Exportar Vista Filtrada (CSV)",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema["accent_primary"],
            fg=self.tema["accent_btn_fg"],
            activebackground=self.tema["accent_hover"],
            activeforeground=self.tema["accent_btn_fg"],
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._exportar_csv_filtrado
        )
        self.btn_exportar.pack(side="right", padx=12, pady=8)

        # 2. BARRA DE FILTROS Y VISTAS
        bar_filtros = tk.Frame(self.win, bg=self.tema["bg_panel"], bd=1, relief="solid")
        bar_filtros.pack(fill="x", padx=8, pady=4)

        # Filtro de Vista de Columnas
        tk.Label(
            bar_filtros,
            text="Vista:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema["fg_dim"],
            bg=self.tema["bg_panel"]
        ).pack(side="left", padx=(10, 4), pady=6)

        combo_vistas = ttk.Combobox(
            bar_filtros,
            textvariable=self.vista_columnas_var,
            values=list(VISTAS_COLUMNAS.keys()),
            width=22,
            state="readonly",
            font=("Segoe UI", 8)
        )
        combo_vistas.pack(side="left", padx=4, pady=6)
        combo_vistas.bind("<<ComboboxSelected>>", lambda e: self._on_cambio_vista())

        # Filtro por Etapa
        tk.Label(
            bar_filtros,
            text="Etapa ISA-88:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema["fg_dim"],
            bg=self.tema["bg_panel"]
        ).pack(side="left", padx=(14, 4), pady=6)

        self.combo_etapas = ttk.Combobox(
            bar_filtros,
            textvariable=self.filtro_etapa_var,
            values=["TODAS", "Limpieza", "Decapado", "Zincado", "Niquelado"],
            width=14,
            state="readonly",
            font=("Segoe UI", 8)
        )
        self.combo_etapas.pack(side="left", padx=4, pady=6)
        self.combo_etapas.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtro_reset())

        # Check solo corriente activa
        chk_curr = tk.Checkbutton(
            bar_filtros,
            text="Solo con Corriente (>0.05 A)",
            variable=self.filtro_solo_corriente_var,
            font=("Segoe UI", 8),
            fg=self.tema["fg_text"],
            bg=self.tema["bg_panel"],
            selectcolor=self.tema["bg_card_inner"],
            activebackground=self.tema["bg_panel"],
            activeforeground=self.tema["fg_text"],
            command=self._aplicar_filtro_reset
        )
        chk_curr.pack(side="left", padx=12, pady=6)

        # Búsqueda rápida
        tk.Label(
            bar_filtros,
            text="Buscar:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema["fg_dim"],
            bg=self.tema["bg_panel"]
        ).pack(side="left", padx=(12, 4), pady=6)

        ent_buscar = tk.Entry(
            bar_filtros,
            textvariable=self.busqueda_texto_var,
            width=16,
            font=("Segoe UI", 8),
            bg=self.tema["bg_entry"],
            fg=self.tema["fg_text"],
            insertbackground=self.tema["fg_text"]
        )
        ent_buscar.pack(side="left", padx=4, pady=6)
        ent_buscar.bind("<Return>", lambda e: self._aplicar_filtro_reset())

        btn_buscar = tk.Button(
            bar_filtros,
            text="🔍 Filtrar",
            font=("Segoe UI", 8),
            bg=self.tema["bg_card_inner"],
            fg=self.tema["fg_text"],
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._aplicar_filtro_reset
        )
        btn_buscar.pack(side="left", padx=4, pady=6)

        # 3. TABLA CENTRAL (TREEVIEW OPTIMIZADO)
        f_tree = tk.Frame(self.win, bg=self.tema["bg_panel"])
        f_tree.pack(fill="both", expand=True, padx=8, pady=4)

        self.tree = ttk.Treeview(f_tree, show="headings", selectmode="browse")
        scroll_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        f_tree.grid_rowconfigure(0, weight=1)
        f_tree.grid_columnconfigure(0, weight=1)

        # 4. BARRA DE PAGINACIÓN INFERIOR
        f_pag = tk.Frame(self.win, bg=self.tema["bg_header"], height=38, bd=1, relief="solid")
        f_pag.pack(fill="x", side="bottom", padx=8, pady=(4, 8))

        self.lbl_info_filas = tk.Label(
            f_pag,
            text="Mostrando 0 registros",
            font=("Segoe UI", 8),
            fg=self.tema["fg_dim"],
            bg=self.tema["bg_header"]
        )
        self.lbl_info_filas.pack(side="left", padx=12, pady=6)

        # Controles de navegación de página
        f_nav = tk.Frame(f_pag, bg=self.tema["bg_header"])
        f_nav.pack(side="right", padx=12, pady=4)

        btn_primera = tk.Button(f_nav, text="⏮", font=("Segoe UI", 8), bg=self.tema["bg_card_inner"], fg=self.tema["fg_text"], bd=0, padx=6, command=self._ir_primera_pagina)
        btn_primera.pack(side="left", padx=2)

        btn_ant = tk.Button(f_nav, text="◀ Ant", font=("Segoe UI", 8, "bold"), bg=self.tema["bg_card_inner"], fg=self.tema["fg_text"], bd=0, padx=8, command=self._pagina_anterior)
        btn_ant.pack(side="left", padx=2)

        self.lbl_pag_info = tk.Label(f_nav, text="Página 1 de 1", font=("Segoe UI", 8, "bold"), fg=self.tema["fg_text"], bg=self.tema["bg_header"])
        self.lbl_pag_info.pack(side="left", padx=8)

        btn_sig = tk.Button(f_nav, text="Sig ▶", font=("Segoe UI", 8, "bold"), bg=self.tema["bg_card_inner"], fg=self.tema["fg_text"], bd=0, padx=8, command=self._pagina_siguiente)
        btn_sig.pack(side="left", padx=2)

        btn_ultima = tk.Button(f_nav, text="⏭", font=("Segoe UI", 8), bg=self.tema["bg_card_inner"], fg=self.tema["fg_text"], bd=0, padx=6, command=self._ir_ultima_pagina)
        btn_ultima.pack(side="left", padx=2)

        self._configurar_estilos_treeview()
        self._construir_columnas_treeview()

    def _configurar_estilos_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=self.tema["bg_panel"],
            foreground=self.tema["fg_text"],
            fieldbackground=self.tema["bg_panel"],
            rowheight=24,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background=self.tema["bg_card_inner"],
            foreground=self.tema["fg_text"],
            font=("Segoe UI", 8, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", self.tema["accent_primary"])],
            foreground=[("selected", "#ffffff")]
        )

    def _construir_columnas_treeview(self):
        cols_info = VISTAS_COLUMNAS.get(self.vista_columnas_var.get(), VISTAS_COLUMNAS["Resumen de Proceso"])
        col_names = [c[0] for c in cols_info]
        self.tree["columns"] = col_names

        for col_id, col_label, col_width in cols_info:
            self.tree.heading(col_id, text=col_label, anchor="center")
            self.tree.column(col_id, width=col_width, anchor="center", stretch=True)

    def _cargar_lista_ensayos(self):
        ensayos = self.db.listar_ensayos_locales()
        self.ensayos_map = {f"{e['nombre_carpeta']} (Placa #{e['placa_num']} - {e['fecha_hora'][:10]})": e['id'] for e in ensayos}
        nombres = list(self.ensayos_map.keys())

        self.combo_ensayos["values"] = nombres
        if nombres:
            self.combo_ensayos.current(0)
            self._on_ensayo_seleccionado()
        else:
            self.combo_ensayos.set("No hay ensayos en la base de datos local")
            self._limpiar_tabla()

    def _on_ensayo_seleccionado(self, event=None):
        sel = self.combo_ensayos.get()
        self.ensayo_actual_id = self.ensayos_map.get(sel)
        self.nombre_ensayo_actual = sel.split(" ")[0] if sel else ""
        self.pagina_actual = 1
        self._cargar_datos_paginados()

    def _on_cambio_vista(self):
        self._construir_columnas_treeview()
        self._cargar_datos_paginados()

    def _aplicar_filtro_reset(self):
        self.pagina_actual = 1
        self._cargar_datos_paginados()

    def _construir_clausula_where(self):
        clausulas = ["ensayo_id = ?"]
        params = [self.ensayo_actual_id]

        etapa = self.filtro_etapa_var.get()
        if etapa != "TODAS":
            clausulas.append("etapa_nombre LIKE ?")
            params.append(f"%{etapa}%")

        if self.filtro_solo_corriente_var.get():
            clausulas.append("fuente_corriente_real_a > 0.05")

        txt = self.busqueda_texto_var.get().strip()
        if txt:
            try:
                t_val = float(txt)
                clausulas.append("(tiempo_relativo_s >= ? AND tiempo_relativo_s <= ?)")
                params.extend([t_val - 1.0, t_val + 1.0])
            except ValueError:
                clausulas.append("(etapa_nombre LIKE ? OR timestamp_iso LIKE ?)")
                params.extend([f"%{txt}%", f"%{txt}%"])

        return " WHERE " + " AND ".join(clausulas), params

    def _cargar_datos_paginados(self):
        if not self.ensayo_actual_id:
            self._limpiar_tabla()
            return

        where_clause, params = self._construir_clausula_where()

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Contar total de registros filtrados
            cur.execute(f"SELECT COUNT(*) FROM telemetria_10hz {where_clause}", tuple(params))
            self.total_filas_filtradas = cur.fetchone()[0]

            self.total_paginas = max(1, (self.total_filas_filtradas + self.filas_por_pagina - 1) // self.filas_por_pagina)
            self.pagina_actual = max(1, min(self.pagina_actual, self.total_paginas))

            # 2. Obtener columnas requeridas
            cols_info = VISTAS_COLUMNAS.get(self.vista_columnas_var.get(), VISTAS_COLUMNAS["Resumen de Proceso"])
            col_names = [c[0] for c in cols_info]
            cols_sql = ", ".join(col_names)

            offset = (self.pagina_actual - 1) * self.filas_por_pagina
            sql_data = f"SELECT {cols_sql} FROM telemetria_10hz {where_clause} ORDER BY tiempo_relativo_s ASC LIMIT ? OFFSET ?"
            params_data = list(params) + [self.filas_por_pagina, offset]

            cur.execute(sql_data, tuple(params_data))
            filas = cur.fetchall()

        # Renderizar en Treeview
        self._limpiar_tabla()
        for f in filas:
            vals = []
            for col in col_names:
                v = f[col]
                if v is None:
                    vals.append("--")
                elif isinstance(v, float):
                    vals.append(f"{v:.2f}")
                else:
                    vals.append(str(v))
            self.tree.insert("", "end", values=vals)

        # Actualizar labels de estado
        inicio = offset + 1 if self.total_filas_filtradas > 0 else 0
        fin = min(offset + len(filas), self.total_filas_filtradas)
        self.lbl_info_filas.config(text=f"Filas {inicio}–{fin} de {self.total_filas_filtradas} filtradas")
        self.lbl_pag_info.config(text=f"Página {self.pagina_actual} de {self.total_paginas}")

    def _limpiar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _ir_primera_pagina(self):
        if self.pagina_actual > 1:
            self.pagina_actual = 1
            self._cargar_datos_paginados()

    def _pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self._cargar_datos_paginados()

    def _pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self._cargar_datos_paginados()

    def _ir_ultima_pagina(self):
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual = self.total_paginas
            self._cargar_datos_paginados()

    def _exportar_csv_filtrado(self):
        if not self.ensayo_actual_id or self.total_filas_filtradas == 0:
            messagebox.showwarning("Exportar", "No hay datos para exportar con los filtros actuales.")
            return

        where_clause, params = self._construir_clausula_where()
        cols_info = VISTAS_COLUMNAS.get(self.vista_columnas_var.get(), VISTAS_COLUMNAS["Resumen de Proceso"])
        col_names = [c[0] for c in cols_info]
        cols_sql = ", ".join(col_names)

        ruta = filedialog.asksaveasfilename(
            parent=self.win,
            title="Guardar CSV Filtrado",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            initialfile=f"export_{self.nombre_ensayo_actual}_filtrado.csv"
        )
        if not ruta:
            return

        try:
            with self.db.get_connection() as conn:
                df = pd.read_sql_query(f"SELECT {cols_sql} FROM telemetria_10hz {where_clause} ORDER BY tiempo_relativo_s ASC", conn, params=tuple(params))
            df.to_csv(ruta, index=False, encoding="utf-8")
            messagebox.showinfo("Exportar", f"Se exportaron con éxito {len(df)} filas a:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar datos: {e}")

    def _on_close(self):
        try:
            if hasattr(self.parent, 'win_visor'):
                self.parent.win_visor = None
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass

    def aplicar_tema(self, nuevo_tema):
        """Aplica la paleta temática a la ventana del visor de datos en caliente."""
        self.tema = nuevo_tema
        if not hasattr(self, "win") or not self.win.winfo_exists():
            return
        aplicar_tema_a_ventana_generica(self.win, self.tema)
        if hasattr(self, "btn_exportar") and self.btn_exportar:
            self.btn_exportar.configure(bg=self.tema["accent_primary"], fg="#ffffff")
        from utilidades.tema import aplicar_estilo_treeview
        aplicar_estilo_treeview(self.tema)


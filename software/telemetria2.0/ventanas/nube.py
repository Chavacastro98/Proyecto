#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
VENTANA MODULAR: BASE DE DATOS Y NUBE (VentanaNube) - RTOS 2.0
=============================================================================
Proyecto: E.L.E.C.T.R.O.D.O-32 | Innovafest Guadalajara 2026 & SMEQ 2026
Plataforma: Tkinter / SQLite Local + Supabase (PostgreSQL Cloud)
=============================================================================
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from utilidades.gestor_db import (
    GestorDB,
    SincronizadorSupabase,
    cargar_config_nube,
    guardar_config_nube,
    calcular_sha256
)
from utilidades.tema import cargar_tema_preferido, aplicar_tema_a_ventana_generica


class VentanaNube:
    def __init__(self, parent_app):
        self.app = parent_app
        self.tema = getattr(self.app, "tema_actual", cargar_tema_preferido())
        self.win = tk.Toplevel(self.app.root)
        self.win.title("☁ Base de Datos y Sincronización en la Nube (SQLite / Supabase) — E.L.E.C.T.R.O.D.O-32")
        self.win.geometry("1100x720")
        self.win.minsize(980, 600)
        self.win.configure(bg=self.tema["bg_app"])

        self.db = GestorDB()
        self.sync = SincronizadorSupabase(self.db)

        # Variables de gravimetría
        self.var_peso_ini = tk.StringVar(value=f"{getattr(self.app, 'peso_inicial_g', 0.0):.4f}")
        self.var_peso_fin = tk.StringVar(value=f"{getattr(self.app, 'peso_final_g', 0.0):.4f}")
        self.var_area = tk.StringVar(value=f"{getattr(self.app, 'area_placa_cm2', 65.0):.1f}")
        self.var_delta_m = tk.StringVar(value="0.0000 g")
        self.var_rendimiento = tk.StringVar(value="-- %")
        self.var_ensayo_sel = tk.StringVar(value="")
        self.var_estado_proceso = tk.StringVar(value="Listo.")

        self.var_peso_ini.trace_add("write", self._recalcular_delta)
        self.var_peso_fin.trace_add("write", self._recalcular_delta)

        try:
            self._crear_ui()
            self.aplicar_tema(self.tema)
            self._actualizar_lista_ensayos()
            self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception as e:
            try:
                self.win.destroy()
            except Exception:
                pass
            raise e

    def _crear_ui(self):
        # 1. Header
        hdr = tk.Frame(self.win, bg=self.tema["bg_panel"], height=50)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="☁ BASE DE DATOS Y SINCRONIZACIÓN EN LA NUBE (SQLITE / SUPABASE)",
            font=("Segoe UI", 11, "bold"),
            fg=self.tema["accent_primary"],
            bg=self.tema["bg_panel"]
        )
        lbl_t.pack(side="left", padx=10, pady=8)
        self.lbl_hdr_title = lbl_t

        btn_cfg = tk.Button(
            hdr,
            text="⚙ Configurar Supabase",
            bg="#1e293b",
            fg="#94a3b8",
            activebackground="#334155",
            activeforeground="#f8fafc",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._abrir_modal_config
        )
        btn_cfg.pack(side="right", padx=10, pady=8)

        btn_ref = tk.Button(
            hdr,
            text="🔄 Refrescar Ensayos",
            bg="#1e293b",
            fg=self.tema["accent_primary"],
            activebackground="#334155",
            activeforeground=self.tema["accent_primary"],
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._actualizar_lista_ensayos
        )
        btn_ref.pack(side="right", padx=4, pady=8)

        # Contenedor Principal (Dividido en 2 columnas: Lista a la izquierda, Detalle a la derecha)
        panes = tk.PanedWindow(self.win, orient="horizontal", bg=self.tema["bg_app"], bd=0, sashwidth=4)
        panes.pack(fill="both", expand=True, padx=6, pady=4)

        # ----------------- PANEL IZQUIERDO: LISTA DE ENSAYOS -----------------
        frame_izq = tk.LabelFrame(
            panes,
            text=" 📁 Ensayos Realizados en Disco ",
            bg=self.tema["bg_panel"],
            fg="#94a3b8",
            font=("Segoe UI", 10, "bold"),
            bd=1
        )
        panes.add(frame_izq, minsize=480, width=540)

        # Treeview de Ensayos
        cols = ("carpeta", "placa", "local", "nube")
        self.tree_ensayos = ttk.Treeview(frame_izq, columns=cols, show="headings", selectmode="browse")
        self.tree_ensayos.heading("carpeta", text="Nombre de Ensayo / Carpeta")
        self.tree_ensayos.heading("placa", text="Placa")
        self.tree_ensayos.heading("local", text="SQLite")
        self.tree_ensayos.heading("nube", text="Supabase")

        self.tree_ensayos.column("carpeta", width=260)
        self.tree_ensayos.column("placa", width=60, anchor="center")
        self.tree_ensayos.column("local", width=80, anchor="center")
        self.tree_ensayos.column("nube", width=90, anchor="center")

        scroll_y = ttk.Scrollbar(frame_izq, orient="vertical", command=self.tree_ensayos.yview)
        self.tree_ensayos.configure(yscrollcommand=scroll_y.set)

        self.tree_ensayos.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        scroll_y.pack(side="right", fill="y", pady=6, padx=(0, 6))

        self.tree_ensayos.bind("<<TreeviewSelect>>", self._on_ensayo_selected)

        # ----------------- PANEL DERECHO: DETALLES Y ACCIONES -----------------
        frame_der = tk.LabelFrame(
            panes,
            text=" 🔬 Caracterización Gravimétrica y Carga ",
            bg=self.tema["bg_panel"],
            fg="#94a3b8",
            font=("Segoe UI", 10, "bold"),
            bd=1
        )
        panes.add(frame_der, minsize=420)

        f_det = tk.Frame(frame_der, bg=self.tema["bg_panel"])
        f_det.pack(fill="both", expand=True, padx=12, pady=10)

        # Ensayo Seleccionado
        lbl_sel_tit = tk.Label(f_det, text="Ensayo Activo:", font=("Segoe UI", 9, "bold"), fg="#64748b", bg=self.tema["bg_panel"])
        lbl_sel_tit.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.lbl_ensayo_activo = tk.Label(f_det, textvariable=self.var_ensayo_sel, font=("Segoe UI", 9, "bold"), fg=self.tema["accent_primary"], bg=self.tema["bg_panel"])
        self.lbl_ensayo_activo.grid(row=0, column=1, sticky="w", pady=(0, 2))

        # Separador
        ttk.Separator(f_det, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        # Entradas Gravimétricas
        lbl_pi = tk.Label(f_det, text="Peso Inicial (g):", font=("Segoe UI", 9), fg="#e2e8f0", bg=self.tema["bg_panel"])
        lbl_pi.grid(row=2, column=0, sticky="w", pady=4)
        ent_pi = tk.Entry(f_det, textvariable=self.var_peso_ini, font=("Segoe UI", 10), width=14, bg="#1e293b", fg="#f8fafc", insertbackground="white")
        ent_pi.grid(row=2, column=1, sticky="w", pady=4)

        lbl_pf = tk.Label(f_det, text="Peso Final (g):", font=("Segoe UI", 9), fg="#e2e8f0", bg=self.tema["bg_panel"])
        lbl_pf.grid(row=3, column=0, sticky="w", pady=4)
        ent_pf = tk.Entry(f_det, textvariable=self.var_peso_fin, font=("Segoe UI", 10), width=14, bg="#1e293b", fg="#f8fafc", insertbackground="white")
        ent_pf.grid(row=3, column=1, sticky="w", pady=4)

        lbl_ar = tk.Label(f_det, text="Área de Placa (cm²):", font=("Segoe UI", 9), fg="#e2e8f0", bg=self.tema["bg_panel"])
        lbl_ar.grid(row=4, column=0, sticky="w", pady=4)
        ent_ar = tk.Entry(f_det, textvariable=self.var_area, font=("Segoe UI", 10), width=14, bg="#1e293b", fg="#f8fafc", insertbackground="white")
        ent_ar.grid(row=4, column=1, sticky="w", pady=4)

        lbl_dm = tk.Label(f_det, text="Masa Depositada (Δm):", font=("Segoe UI", 9, "bold"), fg="#34d399", bg=self.tema["bg_panel"])
        lbl_dm.grid(row=5, column=0, sticky="w", pady=4)
        lbl_dm_val = tk.Label(f_det, textvariable=self.var_delta_m, font=("Segoe UI", 10, "bold"), fg="#34d399", bg=self.tema["bg_panel"])
        lbl_dm_val.grid(row=5, column=1, sticky="w", pady=4)

        lbl_rf = tk.Label(f_det, text="Rendimiento Faraday:", font=("Segoe UI", 9, "bold"), fg="#f472b6", bg=self.tema["bg_panel"])
        lbl_rf.grid(row=6, column=0, sticky="w", pady=4)
        lbl_rf_val = tk.Label(f_det, textvariable=self.var_rendimiento, font=("Segoe UI", 10, "bold"), fg="#f472b6", bg=self.tema["bg_panel"])
        lbl_rf_val.grid(row=6, column=1, sticky="w", pady=4)

        # Observaciones
        lbl_obs = tk.Label(f_det, text="Notas / Observaciones:", font=("Segoe UI", 9), fg="#94a3b8", bg=self.tema["bg_panel"])
        lbl_obs.grid(row=7, column=0, sticky="w", pady=(8, 2))
        self.txt_obs = tk.Text(f_det, height=3, width=32, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", insertbackground="white", bd=0)
        self.txt_obs.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Botones de Acción
        f_btns = tk.Frame(f_det, bg=self.tema["bg_panel"])
        f_btns.grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)

        self.btn_guardar_local = tk.Button(
            f_btns,
            text="💾 Guardar en SQLite Local",
            bg="#0369a1",
            fg="#ffffff",
            activebackground="#0284c7",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self._guardar_local
        )
        self.btn_guardar_local.pack(fill="x", pady=3)

        self.btn_subir_nube = tk.Button(
            f_btns,
            text="🚀 Subir a Supabase (Nube)",
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self._subir_nube
        )
        self.btn_subir_nube.pack(fill="x", pady=3)

        self.btn_sync_pendientes = tk.Button(
            f_btns,
            text="☁ Sincronizar Todos los Pendientes",
            bg="#475569",
            fg="#f8fafc",
            activebackground="#64748b",
            activeforeground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._sincronizar_pendientes
        )
        self.btn_sync_pendientes.pack(fill="x", pady=3)

        # ----------------- BARRA INFERIOR DE PROGRESO -----------------
        f_status = tk.Frame(self.win, bg="#020617", height=40)
        f_status.pack(fill="x", side="bottom", padx=6, pady=4)

        self.pbar = ttk.Progressbar(f_status, orient="horizontal", mode="determinate")
        self.pbar.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        self.lbl_status = tk.Label(
            f_status,
            textvariable=self.var_estado_proceso,
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#020617"
        )
        self.lbl_status.pack(side="right", padx=10)

    def _recalcular_delta(self, *args):
        try:
            p_ini = float(self.var_peso_ini.get().strip() or 0.0)
            p_fin = float(self.var_peso_fin.get().strip() or 0.0)
            delta = p_fin - p_ini
            self.var_delta_m.set(f"{delta:+.4f} g ({delta * 1000:+.1f} mg)")
        except ValueError:
            self.var_delta_m.set("-- g")

    def _buscar_carpetas_ensayos(self):
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        candidatos = [
            os.path.join(directorio_actual, "..", "experimentos"),
            os.path.join(directorio_actual, "..", "..", "telemetria", "experimentos"),
            os.path.join(directorio_actual, "..", "..", "telemetria2.0", "experimentos"),
        ]
        rutas_encontradas = {}
        for c in candidatos:
            if os.path.exists(c) and os.path.isdir(c):
                for item in os.listdir(c):
                    ruta_completa = os.path.join(c, item)
                    if os.path.isdir(ruta_completa) and os.path.exists(os.path.join(ruta_completa, "telemetria_completa.csv")):
                        rutas_encontradas[item] = ruta_completa
        return rutas_encontradas

    def _actualizar_lista_ensayos(self):
        self.carpetas_dict = self._buscar_carpetas_ensayos()
        self.tree_ensayos.delete(*self.tree_ensayos.get_children())

        ensayos_db = {r["nombre_carpeta"]: r for r in self.db.listar_ensayos_locales()}

        for nombre, ruta in sorted(self.carpetas_dict.items(), reverse=True):
            placa = "--"
            if "Placa_" in nombre or "P0" in nombre or "P1" in nombre:
                partes = nombre.split("_")
                for p in partes:
                    if p.startswith("P") and len(p) <= 3:
                        placa = p
                        break

            reg = ensayos_db.get(nombre)
            estado_local = "✅ Sí" if reg else "❌ No"
            estado_nube = "☁ Sí" if reg and reg.get("sincronizado_nube") == 1 else "⏳ Pendiente" if reg else "--"

            self.tree_ensayos.insert("", "end", iid=nombre, values=(nombre, placa, estado_local, estado_nube))

        if self.carpetas_dict:
            primer_item = list(sorted(self.carpetas_dict.keys(), reverse=True))[0]
            self.tree_ensayos.selection_set(primer_item)
            self._cargar_detalle_ensayo(primer_item)

    def _on_ensayo_selected(self, event):
        sel = self.tree_ensayos.selection()
        if sel:
            self._cargar_detalle_ensayo(sel[0])

    def _cargar_detalle_ensayo(self, nombre_carpeta):
        self.var_ensayo_sel.set(nombre_carpeta)
        # Buscar en DB local si ya tiene pesos guardados
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM ensayos WHERE nombre_carpeta = ?", (nombre_carpeta,))
            row = cur.fetchone()
            if row:
                d = dict(row)
                if d.get("peso_inicial_g"):
                    self.var_peso_ini.set(f"{d['peso_inicial_g']:.4f}")
                if d.get("peso_final_g"):
                    self.var_peso_fin.set(f"{d['peso_final_g']:.4f}")
                if d.get("area_placa_cm2"):
                    self.var_area.set(f"{d['area_placa_cm2']:.1f}")
                if d.get("rendimiento_faradaico_pct"):
                    self.var_rendimiento.set(f"{d['rendimiento_faradaico_pct']:.2f} %")
                self.txt_obs.delete("1.0", "end")
                if d.get("observaciones"):
                    self.txt_obs.insert("1.0", d["observaciones"])
            else:
                self.txt_obs.delete("1.0", "end")

    def _guardar_local(self):
        sel = self.var_ensayo_sel.get()
        if not sel or sel not in self.carpetas_dict:
            messagebox.showwarning("Aviso", "Selecciona un ensayo de la lista.", parent=self.win)
            return

        ruta = self.carpetas_dict[sel]
        try:
            p_ini = float(self.var_peso_ini.get().strip() or 0.0)
            p_fin = float(self.var_peso_fin.get().strip() or 0.0)
            area = float(self.var_area.get().strip() or 65.0)
            obs = self.txt_obs.get("1.0", "end").strip()

            datos_grav = {
                "peso_inicial_g": p_ini,
                "peso_final_g": p_fin,
                "area_placa_cm2": area,
                "observaciones": obs
            }

            self.var_estado_proceso.set("Guardando en SQLite local...")
            self.win.update_idletasks()

            ensayo_id = self.db.registrar_o_actualizar_ensayo_local(ruta, datos_grav)
            self._actualizar_lista_ensayos()
            self.var_estado_proceso.set(f"✅ Guardado localmente con éxito (ID: {ensayo_id[:8]}...)")
            messagebox.showinfo("Éxito", f"Ensayo registrado en SQLite local exitosamente.\nID: {ensayo_id}", parent=self.win)
        except Exception as e:
            self.var_estado_proceso.set("❌ Error al guardar localmente.")
            messagebox.showerror("Error", f"Error al procesar el ensayo:\n{str(e)}", parent=self.win)

    def _subir_nube(self):
        sel = self.var_ensayo_sel.get()
        if not sel or sel not in self.carpetas_dict:
            messagebox.showwarning("Aviso", "Selecciona un ensayo primero.", parent=self.win)
            return

        cfg = cargar_config_nube()
        if not cfg.get("supabase_url") or not cfg.get("supabase_key"):
            self._abrir_modal_config()
            return

        # Primero guardar localmente
        self._guardar_local()

        # Obtener el ID del ensayo
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM ensayos WHERE nombre_carpeta = ?", (sel,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("Error", "No se encontró el ensayo en la base de datos local.", parent=self.win)
                return
            ensayo_id = row["id"]

        def tarea_subida():
            self.btn_subir_nube.config(state="disabled")
            self.btn_guardar_local.config(state="disabled")
            try:
                def cb_prog(pct, msg):
                    self.pbar["value"] = pct
                    self.var_estado_proceso.set(msg)
                    self.win.update_idletasks()

                self.sync.subir_ensayo(ensayo_id, callback_progreso=cb_prog)
                self.win.after(0, lambda: messagebox.showinfo("Completado", "¡Ensayo y telemetría completa subidos a Supabase con éxito!", parent=self.win))
                self.win.after(0, self._actualizar_lista_ensayos)
            except Exception as e:
                err_msg = str(e)
                self.win.after(0, lambda: messagebox.showerror("Fallo de Subida", f"No se pudo sincronizar con Supabase:\n{err_msg}", parent=self.win))
                self.var_estado_proceso.set("❌ Error en subida a nube.")
            finally:
                self.btn_subir_nube.config(state="normal")
                self.btn_guardar_local.config(state="normal")
                self.pbar["value"] = 0

        threading.Thread(target=tarea_subida, daemon=True).start()

    def _sincronizar_pendientes(self):
        cfg = cargar_config_nube()
        if not cfg.get("supabase_url") or not cfg.get("supabase_key"):
            self._abrir_modal_config()
            return

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre_carpeta FROM ensayos WHERE sincronizado_nube = 0")
            pendientes = cur.fetchall()

        if not pendientes:
            messagebox.showinfo("Al día", "No hay ensayos pendientes por sincronizar en la base local.", parent=self.win)
            return

        if not messagebox.askyesno("Confirmar", f"Se encontraron {len(pendientes)} ensayos pendientes de subir a la nube.\n¿Deseas sincronizarlos ahora?", parent=self.win):
            return

        def tarea_lote():
            self.btn_sync_pendientes.config(state="disabled")
            total = len(pendientes)
            try:
                for idx, r in enumerate(pendientes, 1):
                    e_id = r["id"]
                    nom = r["nombre_carpeta"]
                    self.var_estado_proceso.set(f"Sincronizando {idx}/{total}: {nom}...")
                    self.sync.subir_ensayo(e_id)
                self.win.after(0, lambda: messagebox.showinfo("Éxito", f"Se sincronizaron {total} ensayos a Supabase exitosamente.", parent=self.win))
                self.win.after(0, self._actualizar_lista_ensayos)
            except Exception as e:
                self.win.after(0, lambda: messagebox.showerror("Fallo", f"Ocurrió un error durante la sincronización:\n{str(e)}", parent=self.win))
            finally:
                self.btn_sync_pendientes.config(state="normal")
                self.pbar["value"] = 0
                self.var_estado_proceso.set("Listo.")

        threading.Thread(target=tarea_lote, daemon=True).start()

    def _abrir_modal_config(self):
        """Ventana modal para configurar credenciales de Supabase y carpeta Drive."""
        cfg_win = tk.Toplevel(self.win)
        cfg_win.title("⚙ Configuración de Conexión Nube (Supabase)")
        cfg_win.geometry("560x340")
        cfg_win.configure(bg=self.tema["bg_panel"])
        cfg_win.transient(self.win)
        cfg_win.grab_set()

        cfg = cargar_config_nube()

        lbl_tit = tk.Label(cfg_win, text="PARÁMETROS DE CONEXIÓN SUPABASE (POSTGRESQL)", font=("Segoe UI", 10, "bold"), fg=self.tema["accent_primary"], bg=self.tema["bg_panel"])
        lbl_tit.pack(pady=(16, 10))

        f_inputs = tk.Frame(cfg_win, bg=self.tema["bg_panel"])
        f_inputs.pack(fill="x", padx=20, pady=8)

        tk.Label(f_inputs, text="Project URL:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg=self.tema["bg_panel"]).grid(row=0, column=0, sticky="w", pady=6)
        var_url = tk.StringVar(value=cfg.get("supabase_url", ""))
        ent_url = tk.Entry(f_inputs, textvariable=var_url, width=42, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", insertbackground="white")
        ent_url.grid(row=0, column=1, sticky="w", pady=6, padx=8)

        tk.Label(f_inputs, text="API Anon Key:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg=self.tema["bg_panel"]).grid(row=1, column=0, sticky="w", pady=6)
        var_key = tk.StringVar(value=cfg.get("supabase_key", ""))
        ent_key = tk.Entry(f_inputs, textvariable=var_key, width=42, font=("Segoe UI", 9), show="*", bg="#1e293b", fg="#f8fafc", insertbackground="white")
        ent_key.grid(row=1, column=1, sticky="w", pady=6, padx=8)

        # Mostrar/Ocultar key
        def toggle_key():
            if ent_key.cget("show") == "*":
                ent_key.config(show="")
            else:
                ent_key.config(show="*")

        chk_show = tk.Checkbutton(f_inputs, text="Ver Key", command=toggle_key, bg=self.tema["bg_panel"], fg="#94a3b8", selectcolor=self.tema["bg_entry"], activebackground=self.tema["bg_card_inner"])
        chk_show.grid(row=1, column=2, sticky="w")

        lbl_res = tk.Label(cfg_win, text="", font=("Segoe UI", 8), fg="#94a3b8", bg=self.tema["bg_panel"])
        lbl_res.pack(pady=4)

        def probar_conexion():
            lbl_res.config(text="Probando conexión a Supabase...", fg=self.tema["accent_primary"])
            cfg_win.update_idletasks()
            ok, msg = self.sync.test_conexion(var_url.get().strip(), var_key.get().strip())
            if ok:
                lbl_res.config(text=f"✅ {msg}", fg="#34d399")
            else:
                lbl_res.config(text=f"❌ {msg}", fg="#f87171")

        def guardar_salir():
            nueva_cfg = {
                "supabase_url": var_url.get().strip(),
                "supabase_key": var_key.get().strip(),
                "habilitado": bool(var_url.get().strip() and var_key.get().strip()),
                "carpeta_drive_local": cfg.get("carpeta_drive_local", "")
            }
            guardar_config_nube(nueva_cfg)
            self.sync.recargar_config()
            cfg_win.destroy()
            messagebox.showinfo("Guardado", "Credenciales de Supabase actualizadas correctamente.", parent=self.win)

        f_b = tk.Frame(cfg_win, bg=self.tema["bg_panel"])
        f_b.pack(pady=14)

        tk.Button(f_b, text="🔌 Probar Conexión", font=("Segoe UI", 9), bg="#334155", fg="#f8fafc", padx=10, pady=4, bd=0, cursor="hand2", command=probar_conexion).pack(side="left", padx=6)
        tk.Button(f_b, text="💾 Guardar Cambios", font=("Segoe UI", 9, "bold"), bg="#0284c7", fg="#ffffff", padx=12, pady=4, bd=0, cursor="hand2", command=guardar_salir).pack(side="left", padx=6)

    def _on_close(self):
        try:
            if hasattr(self.app, 'win_nube'):
                self.app.win_nube = None
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass

    def aplicar_tema(self, tema):
        """Aplica la paleta temática en caliente a la ventana de nube."""
        self.tema = tema
        if not hasattr(self, "win") or not self.win.winfo_exists():
            return

        aplicar_tema_a_ventana_generica(self.win, self.tema)

        if hasattr(self, "lbl_hdr_title") and self.lbl_hdr_title:
            self.lbl_hdr_title.configure(bg=tema["bg_header"], fg=tema["accent_primary"])

        if hasattr(self, "btn_guardar_local") and self.btn_guardar_local:
            self.btn_guardar_local.configure(bg=self.tema["accent_primary"], fg="#ffffff")
        if hasattr(self, "btn_subir_nube") and self.btn_subir_nube:
            self.btn_subir_nube.configure(bg=self.tema["success"], fg="#ffffff")
        if hasattr(self, "btn_sync_pendientes") and self.btn_sync_pendientes:
            self.btn_sync_pendientes.configure(bg=self.tema["btn_acc_bg"], fg=self.tema["btn_acc_fg"])

        from utilidades.tema import aplicar_estilo_treeview
        aplicar_estilo_treeview(self.tema)


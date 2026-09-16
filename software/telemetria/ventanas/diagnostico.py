#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana Secundaria 3: Diagnóstico de Sensores, Periféricos I2C/SPI y Auditoría de Incidentes.
"""

import os
import sys
import subprocess
import threading
from datetime import datetime
import requests
import tkinter as tk
from tkinter import ttk, messagebox


class VentanaDiagnostico:
    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Diagnóstico de Hardware & Auditoría de Accidentes de Sensores")
        self.win.geometry("980x700")
        self.win.minsize(860, 580)
        self.win.configure(bg="#0b1120")

        self.running = True
        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Cargar historial existente si ya hubo eventos
        self._cargar_historial_existente()
        self._refrescar_datos()

    def _crear_ui(self):
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="DIAGNÓSTICO DE HARDWARE & REGISTRO DE INCIDENCIAS EN TIEMPO REAL",
            font=("Segoe UI", 10, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        btn_csv = tk.Button(
            hdr,
            text="📄 Abrir CSV de Eventos",
            font=("Segoe UI", 8, "bold"),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._abrir_csv_eventos
        )
        btn_csv.pack(side="right", padx=6)

        btn_rescan = tk.Button(
            hdr,
            text="🔄 Re-escanear Bus",
            font=("Segoe UI", 8, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._forzar_reescaneo
        )
        btn_rescan.pack(side="right", padx=6)

        # Contenedor de Tarjetas
        body = tk.Frame(self.win, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=8, pady=4)

        # Sección 1: Bus I2C (0x38, 0x76/77, 0x48, 0x60)
        lbl_i2c = tk.Label(body, text="Periféricos en Bus I2C (GPIO 8 / 9 — 400 kHz):", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#0b1120")
        lbl_i2c.pack(anchor="w", pady=(2, 2))

        f_i2c = tk.Frame(body, bg="#111827", bd=1, relief="solid")
        f_i2c.pack(fill="x", pady=2)

        self.card_aht = self._crear_card_sensor(f_i2c, "AHT20 (0x38)", "Temp/Hum Ambiente", 0)
        self.card_bmp = self._crear_card_sensor(f_i2c, "BMP280 (0x76/77)", "Presión Barométrica", 1)
        self.card_ads = self._crear_card_sensor(f_i2c, "ADS1115 (0x48)", "pH + Shunts VCSS 16-bit", 2)
        self.card_dac = self._crear_card_sensor(f_i2c, "MCP4725 (0x60)", "DAC Corriente VCSS 12-bit", 3)

        # Sección 2: Bus SPI Termopares (MAX6675 T1..T4)
        lbl_spi = tk.Label(body, text="🔥 Sensores de Temperatura SPI MAX6675 (Termopares K):", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#0b1120")
        lbl_spi.pack(anchor="w", pady=(8, 2))

        f_spi = tk.Frame(body, bg="#111827", bd=1, relief="solid")
        f_spi.pack(fill="x", pady=2)

        self.card_t1 = self._crear_card_sensor(f_spi, "MAX6675 #1 (CS 5)", "Tina 1: Limpieza (450W)", 0)
        self.card_t2 = self._crear_card_sensor(f_spi, "MAX6675 #2 (CS 4)", "Tina 2: Decapado (450W)", 1)
        self.card_t3 = self._crear_card_sensor(f_spi, "MAX6675 #3 (CS 13)", "Tina 3: Celda Hull (18W)", 2)
        self.card_t4 = self._crear_card_sensor(f_spi, "MAX6675 #4 (CS 14)", "Tina 4: Níquel (450W)", 3)

        # Sección 3: Historial y Auditoría de Incidentes en Tiempo Real
        sec_ev = tk.Frame(body, bg="#0b1120")
        sec_ev.pack(fill="both", expand=True, pady=(8, 2))

        hdr_ev = tk.Frame(sec_ev, bg="#0b1120")
        hdr_ev.pack(fill="x", pady=2)

        lbl_ev_title = tk.Label(
            hdr_ev,
            text="📋 AUDITORÍA DE ANOMALÍAS, ACCIDENTES Y EVENTOS (registro_eventos_fallos.csv):",
            font=("Segoe UI", 9, "bold"),
            fg="#f59e0b",
            bg="#0b1120"
        )
        lbl_ev_title.pack(side="left")

        self.lbl_ev_count = tk.Label(
            hdr_ev,
            text="0 eventos registrados",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0b1120"
        )
        self.lbl_ev_count.pack(side="right")

        # Treeview con scrollbar para registro de eventos
        f_tree = tk.Frame(sec_ev, bg="#111827", bd=1, relief="solid")
        f_tree.pack(fill="both", expand=True)

        cols = ("t_rel", "etapa", "severidad", "sensor", "tipo", "valor", "desc")
        self.tree_eventos = ttk.Treeview(f_tree, columns=cols, show="headings", height=6)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#0f172a", foreground="#f8fafc", fieldbackground="#0f172a", borderwidth=0, font=("Segoe UI", 8))
        style.configure("Treeview.Heading", background="#1e293b", foreground="#94a3b8", font=("Segoe UI", 8, "bold"), borderwidth=0)
        style.map("Treeview.Heading", background=[("active", "#334155")])

        self.tree_eventos.heading("t_rel", text="Tiempo")
        self.tree_eventos.heading("etapa", text="Etapa ISA-88")
        self.tree_eventos.heading("severidad", text="Severidad")
        self.tree_eventos.heading("sensor", text="Subsistema / Sonda")
        self.tree_eventos.heading("tipo", text="Tipo Evento")
        self.tree_eventos.heading("valor", text="Lectura")
        self.tree_eventos.heading("desc", text="Descripción Técnica")

        self.tree_eventos.column("t_rel", width=65, anchor="center")
        self.tree_eventos.column("etapa", width=120, anchor="w")
        self.tree_eventos.column("severidad", width=95, anchor="center")
        self.tree_eventos.column("sensor", width=150, anchor="w")
        self.tree_eventos.column("tipo", width=150, anchor="w")
        self.tree_eventos.column("valor", width=105, anchor="w")
        self.tree_eventos.column("desc", width=250, anchor="w")

        self.tree_eventos.tag_configure("CRITICO", foreground="#ef4444")
        self.tree_eventos.tag_configure("ADVERTENCIA", foreground="#fbbf24")
        self.tree_eventos.tag_configure("INFO", foreground="#34d399")

        scroll_y = tk.Scrollbar(f_tree, orient="vertical", command=self.tree_eventos.yview)
        self.tree_eventos.configure(yscrollcommand=scroll_y.set)
        self.tree_eventos.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Barra de Pruebas de Auditoría (Simulación controlada de fallos para tesis/demostración)
        bar_test = tk.Frame(body, bg="#1e293b", padx=6, pady=4)
        bar_test.pack(fill="x", pady=(4, 2))

        lbl_test = tk.Label(
            bar_test,
            text="🧪 Simular Accidente (Validación del Logger):",
            font=("Segoe UI", 8, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        lbl_test.pack(side="left", padx=4)

        def _crear_btn_test(parent, txt, cmd_tipo, bg_c="#334155"):
            b = tk.Button(
                parent,
                text=txt,
                font=("Segoe UI", 7, "bold"),
                bg=bg_c,
                fg="#f8fafc",
                activebackground="#475569",
                activeforeground="#ffffff",
                bd=0,
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda: self._disparar_test_accidente(cmd_tipo)
            )
            b.pack(side="left", padx=3)
            return b

        _crear_btn_test(bar_test, "⚡ Salto Térmico (+16°C)", "salto_t2", "#78350f")
        _crear_btn_test(bar_test, "🔌 Desconexión Sonda T1", "desconexion_t1", "#7f1d1d")
        _crear_btn_test(bar_test, "🔥 Sobretemp T4 (>68°C)", "sobretemp_t4", "#7f1d1d")
        _crear_btn_test(bar_test, "⚖️ Desbalance Shunts VCSS", "desbalance_vcss", "#1e3a5f")
        _crear_btn_test(bar_test, "🧪 Saturación Celda", "saturacion_celda", "#4c1d95")
        _crear_btn_test(bar_test, "📶 Caída Wi-Fi", "caida_wifi", "#334155")

        # Footer informativo
        self.lbl_diag_status = tk.Label(
            self.win,
            text="Consultando estado de sensores...",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0f172a",
            padx=10,
            pady=4
        )
        self.lbl_diag_status.pack(fill="x", side="bottom")

    def _crear_card_sensor(self, parent, nombre, desc, col):
        f = tk.Frame(parent, bg="#1e293b", padx=8, pady=6)
        f.pack(side="left", expand=True, fill="both", padx=4, pady=4)

        lbl_nom = tk.Label(f, text=nombre, font=("Segoe UI", 8, "bold"), fg="#f8fafc", bg="#1e293b")
        lbl_nom.pack(anchor="w")

        lbl_d = tk.Label(f, text=desc, font=("Segoe UI", 7), fg="#94a3b8", bg="#1e293b")
        lbl_d.pack(anchor="w")

        lbl_st = tk.Label(f, text="⏳ Verificando...", font=("Segoe UI", 8, "bold"), fg="#fbbf24", bg="#1e293b")
        lbl_st.pack(anchor="w", pady=(4, 0))
        return lbl_st

    def _forzar_reescaneo(self):
        self._refrescar_datos()

    def _disparar_test_accidente(self, tipo):
        if hasattr(self.app, 'simular_accidente_sensor'):
            self.app.simular_accidente_sensor(tipo)
            if not getattr(self.app, 'grabando', False):
                messagebox.showinfo(
                    "Simulación Registrada",
                    f"Accidente de prueba programado: '{tipo}'.\n\nInicia la grabación para auditar y guardar el evento en CSV."
                )

    def _abrir_csv_eventos(self):
        archivo = getattr(self.app, 'archivo_csv_eventos', None)
        if archivo and os.path.exists(archivo):
            if sys.platform == "win32":
                os.startfile(archivo)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", archivo])
            else:
                subprocess.Popen(["xdg-open", archivo])
        else:
            messagebox.showinfo(
                "Archivo CSV",
                "Aún no se ha iniciado una grabación para generar el archivo 'registro_eventos_fallos.csv'."
            )

    def _cargar_historial_existente(self):
        eventos = getattr(self.app, 'historia_eventos_fallos', [])
        for ev in eventos:
            self.agregar_evento_gui(ev)

    def agregar_evento_gui(self, ev):
        if not self.win.winfo_exists():
            return
        t_fmt = f"{ev.get('t_rel', 0.0):.1f} s"
        sev = ev.get("severidad", "INFO")
        vals = (
            t_fmt,
            ev.get("etapa", "")[:18],
            sev,
            ev.get("sensor", ""),
            ev.get("tipo", ""),
            ev.get("valor", ""),
            ev.get("desc", "")
        )
        tag = sev if sev in ("CRITICO", "ADVERTENCIA", "INFO") else "INFO"
        self.tree_eventos.insert("", "end", values=vals, tags=(tag,))
        # Auto-scroll hacia el final
        children = self.tree_eventos.get_children()
        if children:
            self.tree_eventos.see(children[-1])
        n = len(children)
        self.lbl_ev_count.config(text=f"{n} eventos auditados")

    def _refrescar_datos(self):
        if not self.running or not self.win.winfo_exists():
            return

        def _fetch():
            if self.app.modo_demo:
                res = {"aht": 1, "bmp": 1, "ads": 1, "dac": 1, "tc": [1, 1, 1, 1]}
                # Reflejar falla simulada si aplica
                if getattr(self.app, '_falla_sonda_activa', [False]*4)[0]:
                    res["tc"][0] = 0
            else:
                ip = self.app.entry_ip.get().strip() if hasattr(self.app, 'entry_ip') else "192.168.4.1"
                try:
                    r = requests.get(f"http://{ip}/data_sensors", timeout=1.5)
                    if r.status_code == 200:
                        res = r.json()
                    else:
                        res = None
                except Exception:
                    res = None

            if self.win.winfo_exists():
                self.win.after(0, self._actualizar_ui, res)

        threading.Thread(target=_fetch, daemon=True).start()
        if self.running:
            self.win.after(2500, self._refrescar_datos)

    def _actualizar_ui(self, data):
        if not self.win.winfo_exists():
            return

        if not data:
            self.lbl_diag_status.config(text="🔴 No se pudo obtener diagnóstico del ESP32 (Sin conexión)", fg="#ef4444")
            return

        def set_badge(lbl, ok, ok_text="🟢 OK (Conectado)", err_text="🔴 DESCONECTADO"):
            if ok:
                lbl.config(text=ok_text, fg="#34d399")
            else:
                lbl.config(text=err_text, fg="#ef4444")

        set_badge(self.card_aht, data.get("aht") == 1)
        set_badge(self.card_bmp, data.get("bmp") == 1)
        set_badge(self.card_ads, data.get("ads") == 1)
        set_badge(self.card_dac, data.get("dac") == 1)

        tcs = data.get("tc", [0, 0, 0, 0])
        set_badge(self.card_t1, len(tcs) > 0 and tcs[0] == 1, "🟢 OK (0-150°C)", "🔴 Falla Sonda")
        set_badge(self.card_t2, len(tcs) > 1 and tcs[1] == 1, "🟢 OK (0-150°C)", "🔴 Falla Sonda")
        set_badge(self.card_t3, len(tcs) > 2 and tcs[2] == 1, "🟢 OK (0-150°C)", "🔴 Falla Sonda")
        set_badge(self.card_t4, len(tcs) > 3 and tcs[3] == 1, "🟢 OK (0-150°C)", "🔴 Falla Sonda")

        total_ok = sum([data.get("aht", 0), data.get("bmp", 0), data.get("ads", 0), data.get("dac", 0)] + tcs)
        self.lbl_diag_status.config(
            text=f"✅ Diagnóstico actualizado: {total_ok}/8 Periféricos operativos ({datetime.now().strftime('%H:%M:%S')})",
            fg="#34d399" if total_ok == 8 else "#fbbf24"
        )

    def _on_close(self):
        self.running = False
        self.app.win_diag = None
        self.win.destroy()



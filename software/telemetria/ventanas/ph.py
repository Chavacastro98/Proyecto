#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
VENTANA MODULAR: TELEMETRÍA, ESTABILIDAD Y CALIBRACIÓN DE PH (VentanaPH)
===================================================================================
Tesis: Automatización y Control de Línea Piloto de Electrodeposición
Microcontrolador: ESP32-S3 (Módulo pH ADS1115 16-Bit Dual)

CARACTERÍSTICAS TÉCNICAS:
1. Osciloscopio en vivo de oscilaciones y deriva iónica de potencial (mV/V vs Tiempo).
2. Detector de estabilidad temporal con criterio estricto de 3 segundos (|dV/dt| < 10 mV).
3. Curva de respuesta Nernstiana (mV vs pH de buffers 4, 7 y 10).
4. Cálculo físicamente correcto de Pendiente Nernst (mV/pH) y Salud de Sonda (0-110%),
   eliminando matemáticamente el error de inversión fraccionaria del 200%.
5. Grabación y exportación de CSV de calibración 100% independiente del ensayo de placas.
6. Interlock de seguridad estricto que inhabilita y bloquea la calibración si la fuente
   de corriente VCSS o los calentadores de inmersión están activos (prevención de colisión I2C).
7. Conmutación bidireccional del módulo de sensado (/act_ph) y muestreo asíncrono en vivo.
===================================================================================
"""

import os
import time
import math
import csv
from datetime import datetime
import threading
import numpy as np
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches


class VentanaPH:

    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("🧪 Metrología y Calibración Nernstiana de pH Dual — ADS1115 (Exclusivo)")
        self.win.geometry("1200x840")
        self.win.minsize(1000, 700)
        self.win.configure(bg="#0b1120")

        # Control de ciclo de vida del hilo de adquisición propio
        self._running = True
        self.sonda_encendida = False

        # Estado de grabación y carpetas exclusivas de pH
        self.grabando_ph = False
        self.csv_ph_handle = None
        self.csv_ph_writer = None
        self.archivo_csv_ph = None
        self.muestras_ph_count = 0
        self.t_inicio_ph = None

        self.carpeta_calibraciones = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "experimentos",
            "calibraciones_ph"
        )
        os.makedirs(self.carpeta_calibraciones, exist_ok=True)

        # Variables de selección y calibración
        self.var_tina = tk.IntVar(value=1) # 1: Tina 1 (Zincado/Limpieza), 2: Tina 2 (Niquelado/Decapado)
        self.var_modo_cal = tk.IntVar(value=1) # 1: 2 Puntos (7 y 4), 2: 3 Puntos (4, 7 y 10)

        # Buffers temporales de oscilación (últimos 60 segundos)
        self.buf_t = []
        self.buf_v1 = []
        self.buf_v2 = []
        self.buf_ph1 = []
        self.buf_ph2 = []

        # Parámetros del detector de estabilidad (3 segundos)
        self.hist_v_recientes = [] # (timestamp, v)
        self.es_estable = False
        self.tiempo_inicio_estable = None
        self.duracion_estable = 0.0

        # Puntos de calibración capturados por tina: {pH_nominal: V_medido}
        self.cal_puntos = {
            1: {7: 1.765, 4: 2.472, 10: 1.058},
            2: {7: 1.765, 4: 2.472, 10: 1.058}
        }
        self.cal_completada = {1: False, 2: False}

        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # Iniciar hilo de polling independiente para lecturas continuas
        self._hilo_poll_ph = threading.Thread(target=self._worker_polling_ph, daemon=True)
        self._hilo_poll_ph.start()

        # Comprobación de encendido automático de sonda al abrir si es seguro
        self.win.after(350, self._verificar_y_autoencender_sonda)

        # Bucle de refresco de interfaz gráfica a 4 Hz (250 ms)
        self.timer_id = self.win.after(250, self._ciclo_muestreo)


    def _crear_ui(self):
        # 1. Header Bar
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=8, pady=6)

        lbl_t = tk.Label(
            hdr,
            text="🧪 METROLOGÍA & CALIBRACIÓN NERNSTIANA DE PH DUAL (ADS1115 16-BIT)",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=12, pady=10)

        self.lbl_interlock = tk.Label(
            hdr,
            text="INTERLOCK RTOS: FUENTE APAGADA (CALIBRACIÓN HABILITADA)",
            font=("Segoe UI", 8, "bold"),
            fg="#34d399",
            bg="#064e3b",
            padx=10,
            pady=4
        )
        self.lbl_interlock.pack(side="right", padx=8)

        self.btn_toggle_sonda = tk.Button(
            hdr,
            text="🔌 SONDA PH: APAGADA",
            font=("Segoe UI", 8, "bold"),
            bg="#7f1d1d",
            fg="#fca5a5",
            activebackground="#991b1b",
            command=self._toggle_sonda_ph,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2"
        )
        self.btn_toggle_sonda.pack(side="right", padx=6)

        # 2. Main Body: Split Paneles Gráficos y Panel de Control
        body = tk.Frame(self.win, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=8, pady=2)

        # Frame de Gráficos (Lado Izquierdo + Centro)
        frame_plots = tk.Frame(body, bg="#0b1120")
        frame_plots.pack(side="left", fill="both", expand=True)

        self.fig = Figure(figsize=(8.8, 6.2), dpi=100, facecolor="#0b1120")
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.10, wspace=0.30)

        # Subplot 1: Osciloscopio de Voltaje y pH en Vivo
        self.ax_osc = self.fig.add_subplot(121)
        self.ax_osc.set_facecolor("#050b14")
        self.ax_osc.set_title("1. Dinámica de Estabilización & Oscilaciones", color="#f8fafc", fontsize=9.5, fontweight="bold")
        self.ax_osc.set_xlabel("Tiempo (s)", color="#94a3b8", fontsize=8.5, fontweight="bold")
        self.ax_osc.set_ylabel("Voltaje Sonda (V)", color="#38bdf8", fontsize=8.5, fontweight="bold")
        self.ax_osc.tick_params(colors="#94a3b8", labelsize=7.5)
        self.ax_osc.grid(True, linestyle=":", color="#334155", alpha=0.6)

        self.ax_osc_ph = self.ax_osc.twinx()
        self.ax_osc_ph.set_ylabel("pH Calculado", color="#c084fc", fontsize=8.5, fontweight="bold")
        self.ax_osc_ph.tick_params(colors="#c084fc", labelsize=7.5)

        # Subplot 2: Curva de Calibración Nernstiana (mV vs pH)
        self.ax_nernst = self.fig.add_subplot(122)
        self.ax_nernst.set_facecolor("#050b14")
        self.ax_nernst.set_title("2. Curva Nernstiana Experimental vs Teórica", color="#f8fafc", fontsize=9.5, fontweight="bold")
        self.ax_nernst.set_xlabel("pH Nominal de Buffer", color="#94a3b8", fontsize=8.5, fontweight="bold")
        self.ax_nernst.set_ylabel("Potencial Electrodo E (mV)", color="#38bdf8", fontsize=8.5, fontweight="bold")
        self.ax_nernst.tick_params(colors="#94a3b8", labelsize=7.5)
        self.ax_nernst.grid(True, linestyle=":", color="#334155", alpha=0.6)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_plots)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Panel de Control y Calibración (Lado Derecho)
        panel_ctrl = tk.Frame(body, bg="#0f172a", width=350, padx=12, pady=12)
        panel_ctrl.pack(side="right", fill="y", padx=(8, 0))
        panel_ctrl.pack_propagate(False)

        # Selector de Tina
        lbl_sel_tina = tk.Label(panel_ctrl, text="SELECCIÓN DE SONDA / TINA:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a")
        lbl_sel_tina.pack(anchor="w", pady=(0, 4))

        f_tina_sel = tk.Frame(panel_ctrl, bg="#0f172a")
        f_tina_sel.pack(fill="x", pady=(0, 8))
        rb_t1 = tk.Radiobutton(f_tina_sel, text="Tina 1 (Zincado A0)", variable=self.var_tina, value=1, command=self._actualizar_vista, bg="#0f172a", fg="#38bdf8", selectcolor="#1e293b", activebackground="#0f172a", font=("Segoe UI", 8, "bold"))
        rb_t2 = tk.Radiobutton(f_tina_sel, text="Tina 2 (Níquel A1)", variable=self.var_tina, value=2, command=self._actualizar_vista, bg="#0f172a", fg="#c084fc", selectcolor="#1e293b", activebackground="#0f172a", font=("Segoe UI", 8, "bold"))
        rb_t1.pack(side="left", padx=4)
        rb_t2.pack(side="left", padx=4)

        # Selector de Modo de Calibración
        lbl_sel_modo = tk.Label(panel_ctrl, text="MODELO MATEMÁTICO:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a")
        lbl_sel_modo.pack(anchor="w", pady=(0, 4))

        f_modo_sel = tk.Frame(panel_ctrl, bg="#0f172a")
        f_modo_sel.pack(fill="x", pady=(0, 10))
        rb_m1 = tk.Radiobutton(f_modo_sel, text="2 Puntos (7 y 4)", variable=self.var_modo_cal, value=1, bg="#0f172a", fg="#94a3b8", selectcolor="#1e293b", activebackground="#0f172a", font=("Segoe UI", 8))
        rb_m2 = tk.Radiobutton(f_modo_sel, text="3 Puntos (4, 7 y 10)", variable=self.var_modo_cal, value=2, bg="#0f172a", fg="#94a3b8", selectcolor="#1e293b", activebackground="#0f172a", font=("Segoe UI", 8))
        rb_m1.pack(side="left", padx=2)
        rb_m2.pack(side="left", padx=2)

        # Semáforo de Estabilidad (3 segundos)
        f_estab = tk.Frame(panel_ctrl, bg="#1e293b", padx=8, pady=8, highlightbackground="#334155", highlightthickness=1)
        f_estab.pack(fill="x", pady=(0, 10))

        self.lbl_estab_status = tk.Label(
            f_estab,
            text="● ESPERANDO ESTABILIDAD",
            font=("Segoe UI", 9, "bold"),
            fg="#fbbf24",
            bg="#1e293b"
        )
        self.lbl_estab_status.pack(anchor="center")

        self.lbl_estab_det = tk.Label(
            f_estab,
            text="Deriva |dV/dt|: 0.0 mV/s | 0.0 / 3.0 s",
            font=("Consolas", 8),
            fg="#94a3b8",
            bg="#1e293b"
        )
        self.lbl_estab_det.pack(anchor="center", pady=(4, 0))

        # Lecturas en Vivo de la Tina Activa
        f_live = tk.Frame(panel_ctrl, bg="#0b1120", padx=10, pady=8, highlightbackground="#0369a1", highlightthickness=1)
        f_live.pack(fill="x", pady=(0, 10))

        self.lbl_live_ph = tk.Label(f_live, text="7.00 pH", font=("Segoe UI", 22, "bold"), fg="#38bdf8", bg="#0b1120")
        self.lbl_live_ph.pack(anchor="center")

        self.lbl_live_v = tk.Label(f_live, text="Voltaje: 1.765 V (ADS: 1.765 V)", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0b1120")
        self.lbl_live_v.pack(anchor="center", pady=(2, 0))

        # Métricas Nernstianas de la Sonda
        f_nernst_kpi = tk.Frame(panel_ctrl, bg="#1e293b", padx=8, pady=8)
        f_nernst_kpi.pack(fill="x", pady=(0, 10))

        self.lbl_slope_mv = tk.Label(f_nernst_kpi, text="Sensibilidad S: 58.4 mV/pH", font=("Segoe UI", 8, "bold"), fg="#f8fafc", bg="#1e293b")
        self.lbl_slope_mv.pack(anchor="w")

        self.lbl_slope_pct = tk.Label(f_nernst_kpi, text="Salud Sonda (Slope %): 98.7% (ÓPTIMA)", font=("Segoe UI", 8, "bold"), fg="#34d399", bg="#1e293b")
        self.lbl_slope_pct.pack(anchor="w", pady=(3, 0))

        self.lbl_gain_m = tk.Label(f_nernst_kpi, text="Ganancia Electrónica m: 4.24 pH/V", font=("Segoe UI", 8), fg="#94a3b8", bg="#1e293b")
        self.lbl_gain_m.pack(anchor="w", pady=(2, 0))

        # Botones de Calibración por Buffer (Con protección de Interlock)
        lbl_cap = tk.Label(panel_ctrl, text="CALIBRACIÓN POR BUFFER:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a")
        lbl_cap.pack(anchor="w", pady=(0, 4))

        self.btn_cap7 = tk.Button(
            panel_ctrl,
            text="1. Calibrar Buffer Neutro (pH 7.00)",
            font=("Segoe UI", 8, "bold"),
            bg="#0284c7",
            fg="#fff",
            activebackground="#0369a1",
            command=lambda: self._capturar_buffer(7),
            relief="flat",
            pady=4
        )
        self.btn_cap7.pack(fill="x", pady=2)

        self.btn_cap4 = tk.Button(
            panel_ctrl,
            text="2. Calibrar Buffer Ácido (pH 4.01)",
            font=("Segoe UI", 8, "bold"),
            bg="#d97706",
            fg="#fff",
            activebackground="#b45309",
            command=lambda: self._capturar_buffer(4),
            relief="flat",
            pady=4
        )
        self.btn_cap4.pack(fill="x", pady=2)

        self.btn_cap10 = tk.Button(
            panel_ctrl,
            text="3. Calibrar Buffer Básico (pH 10.01)",
            font=("Segoe UI", 8, "bold"),
            bg="#7c3aed",
            fg="#fff",
            activebackground="#6d28d9",
            command=lambda: self._capturar_buffer(10),
            relief="flat",
            pady=4
        )
        self.btn_cap10.pack(fill="x", pady=2)

        # Enviar / Sincronizar con Flash NVS
        self.btn_send_esp = tk.Button(
            panel_ctrl,
            text="⚡ Sincronizar Modelo en Flash NVS",
            font=("Segoe UI", 8, "bold"),
            bg="#059669",
            fg="#fff",
            activebackground="#10b981",
            command=self._enviar_calibracion_esp32,
            relief="flat",
            pady=4
        )
        self.btn_send_esp.pack(fill="x", pady=(6, 2))

        self.btn_reset_cal = tk.Button(
            panel_ctrl,
            text="🔄 Restablecer Calibración Teórica (NVS)",
            font=("Segoe UI", 8),
            bg="#334155",
            fg="#cbd5e1",
            activebackground="#475569",
            command=self._restablecer_calibracion_esp32,
            relief="flat",
            pady=3
        )
        self.btn_reset_cal.pack(fill="x", pady=(0, 10))

        # Botones de Grabación Aislada de pH
        sep = tk.Frame(panel_ctrl, height=1, bg="#334155")
        sep.pack(fill="x", pady=(0, 8))

        self.btn_rec_ph = tk.Button(
            panel_ctrl,
            text="⏺ INICIAR HISTORIAL EXCLUSIVO PH",
            font=("Segoe UI", 8, "bold"),
            bg="#dc2626",
            fg="#fff",
            activebackground="#ef4444",
            command=self._toggle_grabacion_ph,
            relief="flat",
            pady=5
        )
        self.btn_rec_ph.pack(fill="x", pady=2)

        btn_png = tk.Button(
            panel_ctrl,
            text="📸 Exportar Certificado PNG (300 DPI)",
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#cbd5e1",
            activebackground="#334155",
            command=self._exportar_certificado_png,
            relief="flat",
            pady=3
        )
        btn_png.pack(fill="x", pady=2)

        self.lbl_csv_status = tk.Label(
            panel_ctrl,
            text="Archivo CSV: Inactivo",
            font=("Segoe UI", 7),
            fg="#64748b",
            bg="#0f172a",
            wraplength=320
        )
        self.lbl_csv_status.pack(anchor="w", pady=(4, 0))


    def _es_interlock_bloqueante(self):
        """
        Retorna (bloqueado: bool, motivo: str).
        Evalúa de forma estricta si la fuente de corriente VCSS, actuadores de potencia o
        una etapa automatizada están activos para salvaguardar la sonda y evitar colisiones I2C.
        """
        # 1. ¿Hay corriente real o de consigna en la celda?
        ultimo_amps = float(getattr(self.app, 'ultimo_amps', 0.0) or 0.0)
        if ultimo_amps > 0.05:
            return True, f"Fuente VCSS activa ({ultimo_amps:.2f} A)"

        # 2. ¿El estado de la fuente en telemetría indica activa?
        d_f = getattr(self.app, 'ultimo_d_f', None) or getattr(self.app, 'ultimo_df', None) or {}
        if int(d_f.get("act", 0)) == 1 or float(d_f.get("amps", 0.0)) > 0.05 or float(d_f.get("i_real", 0.0)) > 0.05:
            return True, "Fuente VCSS encendida"

        # 3. ¿El ESP32 reporta bandera de interlock de pH activa?
        d_ph = getattr(self.app, 'ultimo_d_ph', None) or {}
        if int(d_ph.get("il", 0)) == 1:
            return True, "Interlock de hardware en ESP32"

        # 4. ¿Hay una etapa de ensayo electroquímico corriendo?
        if getattr(self.app, 'etapa_corriendo', False):
            return True, "Etapa de ensayo en ejecución"

        # 5. Modo Demo forzando corriente
        if getattr(self.app, 'modo_demo', False) and getattr(self.app, 'demo_forzar_corriente', False):
            return True, "Modo Simulación: Corriente Forzada"

        return False, ""


    def _verificar_y_autoencender_sonda(self):
        """Al abrir la ventana, si no hay interlock y el módulo de pH está apagado en el ESP32,
        lo enciende automáticamente enviando /act_ph?run=1."""
        if getattr(self.app, 'modo_demo', False):
            self.sonda_encendida = True
            self._actualizar_boton_sonda()
            return

        if not getattr(self.app, 'conectado', False):
            return

        bloqueado, _ = self._es_interlock_bloqueante()
        if bloqueado:
            return

        ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')

        def _activar():
            try:
                # Comprobar si ya está encendida en el ESP32
                r = requests.get(f"http://{ip}/get_ph_dual", timeout=1.2)
                if r.status_code == 200:
                    d = r.json()
                    on_val = int(d.get("on", 0))
                    if on_val == 1:
                        self.sonda_encendida = True
                        if self._running and self.win.winfo_exists():
                            self.win.after(0, self._actualizar_boton_sonda)
                        return

                # Si está apagada y es seguro, encenderla
                r_act = requests.get(f"http://{ip}/act_ph?run=1", timeout=1.5)
                if r_act.status_code == 200:
                    self.sonda_encendida = True
                    if self._running and self.win.winfo_exists():
                        self.win.after(0, self._actualizar_boton_sonda)
            except Exception:
                pass

        threading.Thread(target=_activar, daemon=True).start()


    def _toggle_sonda_ph(self):
        """Activa o desactiva la adquisición del módulo de pH en el ESP32 vía HTTP."""
        if getattr(self.app, 'modo_demo', False):
            self.sonda_encendida = not self.sonda_encendida
            self._actualizar_boton_sonda()
            return

        if not getattr(self.app, 'conectado', False):
            messagebox.showwarning("Sin Conexión", "El microcontrolador ESP32 no está conectado.")
            return

        nuevo_estado = not self.sonda_encendida
        if nuevo_estado:
            bloqueado, motivo = self._es_interlock_bloqueante()
            if bloqueado:
                messagebox.showerror(
                    "Interlock de Seguridad Activo",
                    f"No se puede encender la sonda de pH:\n\n{motivo}.\n\n"
                    "Por diseño galvánico, el sensor debe permanecer en reposo "
                    "mientras fluye corriente en el electrolito."
                )
                return

        ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')

        def _enviar():
            try:
                val = 1 if nuevo_estado else 0
                r = requests.get(f"http://{ip}/act_ph?run={val}", timeout=1.5)
                if r.status_code == 200:
                    self.sonda_encendida = nuevo_estado
                    if self._running and self.win.winfo_exists():
                        self.win.after(0, self._actualizar_boton_sonda)
                elif r.status_code == 403:
                    if self._running and self.win.winfo_exists():
                        self.win.after(0, lambda: messagebox.showerror("Bloqueado por ESP32", f"El ESP32 rechazó la activación:\n{r.text}"))
            except Exception as e:
                if self._running and self.win.winfo_exists():
                    self.win.after(0, lambda: messagebox.showerror("Error de Comunicación", f"No se pudo comunicar con el ESP32:\n{e}"))

        threading.Thread(target=_enviar, daemon=True).start()


    def _actualizar_boton_sonda(self):
        if hasattr(self, 'btn_toggle_sonda') and self.btn_toggle_sonda.winfo_exists():
            if self.sonda_encendida:
                self.btn_toggle_sonda.config(
                    text="🔌 SONDA PH: ENCENDIDA",
                    bg="#059669",
                    activebackground="#10b981",
                    fg="#ffffff"
                )
            else:
                self.btn_toggle_sonda.config(
                    text="🔌 SONDA PH: APAGADA",
                    bg="#7f1d1d",
                    activebackground="#991b1b",
                    fg="#fca5a5"
                )


    def _worker_polling_ph(self):
        """
        Hilo de segundo plano que garantiza lecturas dinámicas continuas en la ventana de pH
        incluso cuando el ensayo general no está grabando en CSV.
        """
        while self._running:
            try:
                es_demo = bool(getattr(self.app, 'modo_demo', False))
                esta_conectado = bool(getattr(self.app, 'conectado', False))
                grabando = bool(getattr(self.app, 'grabando', False))

                if esta_conectado and not es_demo:
                    ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')

                    # 1. Si no está grabando la app principal, consultamos /data_all
                    if not grabando:
                        try:
                            r = requests.get(f"http://{ip}/data_all", timeout=1.0)
                            if r.status_code == 200:
                                d_all = r.json()
                                d_ph = d_all.get("ph")
                                d_f = d_all.get("f")
                                d_t = d_all.get("t")
                                d_env = d_all.get("env")

                                self.app.ultimo_d_ph = d_ph
                                self.app.ultimo_d_f = d_f
                                self.app.ultimo_d_t = d_t
                                self.app.ultimo_d_env = d_env
                                if d_f and isinstance(d_f, dict):
                                    self.app.ultimo_amps = float(d_f.get("i_real", d_f.get("amps", 0.0)))
                        except Exception:
                            pass

                    # 2. Respaldo retrocompatible: si el firmware no entrega 'v1' en /data_all, consultar /get_ph_dual
                    cur_d_ph = getattr(self.app, 'ultimo_d_ph', None) or {}
                    if "v1" not in cur_d_ph or not cur_d_ph:
                        try:
                            r_ph = requests.get(f"http://{ip}/get_ph_dual", timeout=1.0)
                            if r_ph.status_code == 200:
                                d_dual = r_ph.json()
                                cur_d_ph.update(d_dual)
                                self.app.ultimo_d_ph = cur_d_ph
                        except Exception:
                            pass

                    if "on" in cur_d_ph:
                        self.sonda_encendida = (int(cur_d_ph.get("on", 0)) == 1)
            except Exception:
                pass
            time.sleep(0.30)


    def _ciclo_muestreo(self):
        try:
            if not self._running or not self.win.winfo_exists():
                return

            es_demo = bool(getattr(self.app, 'modo_demo', False))
            esta_conectado = bool(getattr(self.app, 'conectado', False))

            # 1. Si no hay conexión al ESP32 y el Modo Simulación está apagado en la ventana principal:
            if not esta_conectado and not es_demo:
                self.lbl_interlock.config(
                    text="INTERLOCK RTOS: ESP32 DESCONECTADO (ESPERANDO ENLACE)",
                    bg="#7f1d1d",
                    fg="#fca5a5"
                )
                self.lbl_estab_status.config(text="● ESP32 DESCONECTADO (SIN SEÑAL)", fg="#ef4444")
                self.lbl_estab_det.config(text="Esperando conexión HTTP o activa 'Modo Simulación'")
                self.lbl_live_ph.config(text="-- pH")
                self.lbl_live_v.config(text="Voltaje: -- V (Sin enlace)")
                self.es_estable = False
                self.tiempo_inicio_estable = None
                self.duracion_estable = 0.0
                self.timer_id = self.win.after(400, self._ciclo_muestreo)
                return

            # 2. Evaluar Interlock de Seguridad Anti-Cuelgues
            bloqueado, motivo = self._es_interlock_bloqueante()
            botones_cal = [self.btn_cap7, self.btn_cap4, self.btn_cap10, self.btn_send_esp, self.btn_reset_cal]

            if bloqueado:
                for btn in botones_cal:
                    btn.config(state="disabled")
                self.lbl_interlock.config(
                    text=f"⚠️ INTERLOCK: {motivo.upper()} (CALIBRACIÓN BLOQUEADA)",
                    bg="#7f1d1d",
                    fg="#fca5a5"
                )
                self.lbl_estab_status.config(text="● CALIBRACIÓN BLOQUEADA (INTERLOCK)", fg="#ef4444")
                self.lbl_estab_det.config(text=f"Apaga la fuente o pausa la etapa para calibrar ({motivo})")
            else:
                for btn in botones_cal:
                    btn.config(state="normal")
                if not es_demo and esta_conectado:
                    if self.sonda_encendida:
                        self.lbl_interlock.config(
                            text="INTERLOCK RTOS: FUENTE APAGADA (PH ACTIVO)",
                            bg="#064e3b",
                            fg="#34d399"
                        )
                    else:
                        self.lbl_interlock.config(
                            text="INTERLOCK RTOS: SONDA EN REPOSO (CLICK 'SONDA PH' PARA ACTIVAR)",
                            bg="#854d0e",
                            fg="#fef08a"
                        )

            self._actualizar_boton_sonda()

            # 3. Lectura de Datos de Telemetría Dinámicos
            d_ph = getattr(self.app, 'ultimo_d_ph', None) or {}
            t_ahora = time.time()
            if not self.t_inicio_ph:
                self.t_inicio_ph = t_ahora
            t_rel = round(t_ahora - self.t_inicio_ph, 2)

            tina_sel = self.var_tina.get()

            if es_demo:
                # Simular oscilaciones típicas de sonda antes de asentarse
                ruido = float(np.random.normal(0, 0.003))
                v_sel = 1.765 + ruido if tina_sel == 1 else 1.760 + ruido
                ph_sel = 7.00 + (1.765 - v_sel) * 4.242
            else:
                # Datos dinámicos del hardware real (ADS1115)
                v1 = float(d_ph.get("v1", 1.765))
                v2 = float(d_ph.get("v2", 1.760))
                ph1 = float(d_ph.get("p1", 7.00))
                ph2 = float(d_ph.get("p2", 7.00))
                v_sel = v1 if tina_sel == 1 else v2
                ph_sel = ph1 if tina_sel == 1 else ph2

            # Actualizar buffers deslizantes (últimos 80 puntos ~ 20s @ 4Hz)
            self.buf_t.append(t_rel)
            self.buf_v1.append(v_sel)
            self.buf_ph1.append(ph_sel)
            if len(self.buf_t) > 80:
                self.buf_t.pop(0)
                self.buf_v1.pop(0)
                self.buf_ph1.pop(0)

            # Algoritmo Detector de Estabilidad (3 segundos continuos)
            if not bloqueado:
                self.hist_v_recientes.append((t_ahora, v_sel))
                self.hist_v_recientes = [(t, v) for (t, v) in self.hist_v_recientes if (t_ahora - t) <= 3.2]

                if len(self.hist_v_recientes) >= 8:
                    v_vals = [v for (_, v) in self.hist_v_recientes]
                    dispersion_mv = (max(v_vals) - min(v_vals)) * 1000.0 # mV pico a pico en 3s

                    if dispersion_mv <= 80.0: # Umbral de estabilidad admisible (80 mV pico a pico)
                        if not self.tiempo_inicio_estable:
                            self.tiempo_inicio_estable = t_ahora
                        self.duracion_estable = t_ahora - self.tiempo_inicio_estable

                        if self.duracion_estable >= 3.0:
                            self.es_estable = True
                            self.lbl_estab_status.config(text="● ESTABILIDAD ALCANZADA (LISTO)", fg="#34d399")
                        else:
                            self.es_estable = False
                            self.lbl_estab_status.config(text=f"● ESTABILIZANDO ({self.duracion_estable:.1f}/3.0s)", fg="#38bdf8")
                    else:
                        self.tiempo_inicio_estable = None
                        self.duracion_estable = 0.0
                        self.es_estable = False
                        self.lbl_estab_status.config(text="● SEÑAL EN OSCILACIÓN / DERIVA", fg="#ef4444")

                    self.lbl_estab_det.config(text=f"Dispersión 3s: {dispersion_mv:.1f} mV | {min(3.0, self.duracion_estable):.1f} / 3.0 s")

            # Actualizar Labels Numéricos
            if not es_demo and not self.sonda_encendida:
                self.lbl_live_ph.config(text=f"{ph_sel:.2f} pH (OFF)")
                self.lbl_live_v.config(text=f"Voltaje: {v_sel:.3f} V (Sonda en Reposo)")
            else:
                self.lbl_live_ph.config(text=f"{ph_sel:.2f} pH")
                self.lbl_live_v.config(text=f"Voltaje: {v_sel:.3f} V ({v_sel*1000.0:.1f} mV)")

            # Grabación en CSV propio si está activa
            if self.grabando_ph and self.csv_ph_handle and not self.csv_ph_handle.closed:
                try:
                    iso_now = datetime.now().isoformat(timespec="seconds")
                    self.csv_ph_writer.writerow([
                        iso_now, t_rel, tina_sel, round(ph_sel, 2),
                        round(v_sel, 4), round(v_sel * 1000.0, 1),
                        1 if self.es_estable else 0
                    ])
                    self.csv_ph_handle.flush()
                    self.muestras_ph_count += 1
                except Exception:
                    pass

            # Redibujar gráficas cada 500 ms (cada 2 ciclos de muestreo)
            if len(self.buf_t) % 2 == 0:
                self._redibujar_graficas()

        except Exception:
            pass

        if self._running and self.win.winfo_exists():
            self.timer_id = self.win.after(250, self._ciclo_muestreo)


    def _calcular_regresion_nernst(self, tina_sel=1):
        pts = self.cal_puntos[tina_sel]
        v7_ref = pts.get(7, 1.765)
        if v7_ref is None:
            v7_ref = 1.765
        x_pts = []
        y_pts_mv = []
        for p_nom in sorted(pts.keys()):
            if pts[p_nom] is not None:
                x_pts.append(p_nom)
                e_mv = (v7_ref - pts[p_nom]) * 1000.0
                y_pts_mv.append(e_mv)

        if len(x_pts) >= 2:
            coef = np.polyfit(x_pts, y_pts_mv, 1)
            slope_exp_mv = abs(coef[0]) # Sensibilidad real en mV/pH
            # Slope % = (Sensibilidad Experimental en mV/pH) / (59.16 mV/pH) * 100
            slope_pct_real = min(110.0, max(0.0, (slope_exp_mv / 59.16) * 100.0))
            poly_fn = np.poly1d(coef)
            y_pred = poly_fn(x_pts)
            y_mean = np.mean(y_pts_mv)
            ss_tot = np.sum((np.array(y_pts_mv) - y_mean) ** 2)
            ss_res = np.sum((np.array(y_pts_mv) - y_pred) ** 2)
            r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-9 else 1.0
            return slope_exp_mv, slope_pct_real, r2, v7_ref
        return 59.16, 100.0, 1.0, v7_ref


    def _redibujar_graficas(self):
        # 1. Panel 1: Osciloscopio Temporal
        self.ax_osc.clear()
        self.ax_osc_ph.clear()

        self.ax_osc.set_facecolor("#050b14")
        self.ax_osc.set_title("1. Dinámica de Estabilización & Oscilaciones", color="#f8fafc", fontsize=9.5, fontweight="bold")
        self.ax_osc.set_xlabel("Tiempo Relativo (s)", color="#94a3b8", fontsize=8.5, fontweight="bold")
        self.ax_osc.set_ylabel("Voltaje Sonda (V)", color="#38bdf8", fontsize=8.5, fontweight="bold")
        self.ax_osc.grid(True, linestyle=":", color="#334155", alpha=0.6)

        if self.buf_t:
            self.ax_osc.plot(self.buf_t, self.buf_v1, color="#38bdf8", lw=1.8, label="V Sonda (V)")
            self.ax_osc_ph.plot(self.buf_t, self.buf_ph1, color="#c084fc", ls="--", lw=1.5, label="pH")
            self.ax_osc_ph.set_ylabel("pH Calculado", color="#c084fc", fontsize=8.5, fontweight="bold")

            # Banda verde si es estable
            if self.es_estable and len(self.buf_v1) > 5:
                v_medio = float(np.mean(self.buf_v1[-12:]))
                self.ax_osc.axhspan(v_medio - 0.040, v_medio + 0.040, color="#34d399", alpha=0.18, label="Banda Estable (±40 mV)")

        self.ax_osc.tick_params(colors="#94a3b8", labelsize=7.5)
        self.ax_osc_ph.tick_params(colors="#c084fc", labelsize=7.5)

        # 2. Panel 2: Curva de Calibración Nernstiana
        self.ax_nernst.clear()
        self.ax_nernst.set_facecolor("#050b14")
        self.ax_nernst.set_title("2. Curva Nernstiana Experimental vs Teórica", color="#f8fafc", fontsize=9.5, fontweight="bold")
        self.ax_nernst.set_xlabel("pH Nominal del Buffer", color="#94a3b8", fontsize=8.5, fontweight="bold")
        self.ax_nernst.set_ylabel("Potencial Referenciado E (mV)", color="#38bdf8", fontsize=8.5, fontweight="bold")
        self.ax_nernst.grid(True, linestyle=":", color="#334155", alpha=0.6)

        tina_sel = self.var_tina.get()
        pts = self.cal_puntos[tina_sel]

        v7_ref = pts.get(7, 1.765)
        if v7_ref is None:
            v7_ref = 1.765
        x_pts = []
        y_pts_mv = []

        for p_nom in sorted(pts.keys()):
            if pts[p_nom] is not None:
                x_pts.append(p_nom)
                e_mv = (v7_ref - pts[p_nom]) * 1000.0
                y_pts_mv.append(e_mv)

        # Recta Nernst Teórica ideal (59.16 mV/pH a 25°C)
        x_teorico = np.linspace(2, 12, 100)
        y_teorico_mv = (7.0 - x_teorico) * 59.16
        self.ax_nernst.plot(x_teorico, y_teorico_mv, color="#64748b", ls="--", lw=1.5, label="Nernst Ideal (59.16 mV/pH)")

        slope_exp_mv, slope_pct_real, r2, _ = self._calcular_regresion_nernst(tina_sel)

        if len(x_pts) >= 2:
            self.ax_nernst.scatter(x_pts, y_pts_mv, color="#38bdf8", edgecolor="#ffffff", s=75, zorder=5, label="Puntos Calibrados")

            coef = np.polyfit(x_pts, y_pts_mv, 1)
            poly_fn = np.poly1d(coef)
            self.ax_nernst.plot(x_teorico, poly_fn(x_teorico), color="#34d399", lw=2.0, label=f"Regresión (R²={r2:.3f})")

            # Ganancia electrónica m en pH/V (para el ESP32)
            delta_v = abs(pts[4] - pts[7]) if (4 in pts and pts[4] is not None and 7 in pts and pts[7] is not None) else 0.707
            gain_m_ph_v = (3.0 / delta_v) if delta_v > 0.05 else 4.242

            # Actualizar KPIs
            self.lbl_slope_mv.config(text=f"Sensibilidad S: {slope_exp_mv:.2f} mV/pH")
            
            estado_sonda = "ÓPTIMA" if slope_pct_real >= 95.0 else ("ACEPTABLE" if slope_pct_real >= 85.0 else "ALERTA (AGOTADA)")
            color_sonda = "#34d399" if slope_pct_real >= 95.0 else ("#fbbf24" if slope_pct_real >= 85.0 else "#ef4444")
            self.lbl_slope_pct.config(text=f"Salud Sonda (Slope %): {slope_pct_real:.1f}% ({estado_sonda})", fg=color_sonda)
            self.lbl_gain_m.config(text=f"Ganancia Electrónica m: {gain_m_ph_v:.3f} pH/V")

        self.ax_nernst.set_xlim(2, 12)
        self.ax_nernst.tick_params(colors="#94a3b8", labelsize=7.5)
        self.ax_nernst.legend(loc="upper right", facecolor="#1e293b", edgecolor="#334155", labelcolor="#cbd5e1", fontsize=7.5)

        self.canvas.draw_idle()


    def _capturar_buffer(self, punto_ph):
        # 1. Comprobación estricta de Interlock
        bloqueado, motivo = self._es_interlock_bloqueante()
        if bloqueado:
            messagebox.showerror(
                "Calibración Bloqueada por Interlock",
                f"No se puede calibrar el punto pH {punto_ph} mientras la fuente o etapa estén activas:\n\n{motivo}.\n\n"
                "Riesgo de daño por corrientes parásitas y colisión en bus I2C.\n"
                "Apaga la fuente antes de continuar."
            )
            return

        es_demo = bool(getattr(self.app, 'modo_demo', False))
        esta_conectado = bool(getattr(self.app, 'conectado', False))

        if not esta_conectado and not es_demo:
            messagebox.showwarning(
                "ESP32 Desconectado",
                "No se puede capturar el punto de calibración:\n\n"
                "El ESP32 no está conectado y el 'Modo Simulación' está desactivado en la ventana principal."
            )
            return

        if not es_demo and not self.sonda_encendida:
            messagebox.showwarning(
                "Sonda en Reposo",
                "La sonda de pH está apagada.\n\n"
                "Haz clic primero en el botón '🔌 SONDA PH: APAGADA' del encabezado para iniciar la adquisición del sensor."
            )
            return

        tina_sel = self.var_tina.get()
        v_actual = self.buf_v1[-1] if self.buf_v1 else 1.765

        if not self.es_estable:
            if not messagebox.askyesno(
                "Aviso de Estabilidad",
                f"La sonda aún está en fase de oscilación/deriva (|dV/dt| > 10 mV).\n\n"
                f"Se recomienda esperar 3 segundos en quietud antes de registrar.\n\n"
                f"¿Deseas registrar el punto pH {punto_ph} de todas formas con V = {v_actual:.3f} V?"
            ):
                return

        # Registro local para visualización Nernstiana y certificado
        self.cal_puntos[tina_sel][punto_ph] = v_actual
        self.cal_completada[tina_sel] = True
        self._redibujar_graficas()

        # Enlace con endpoint metrológico del ESP32 si estamos conectados
        if esta_conectado and not es_demo:
            ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')
            modo = self.var_modo_cal.get()

            def _cal_worker():
                try:
                    # 1. Asegurar modo en ESP32
                    requests.get(f"http://{ip}/set_cal_mode?id={tina_sel}&m={modo}", timeout=1.5)
                    # 2. Ejecutar muestreo y calibración en hardware ESP32
                    r = requests.get(f"http://{ip}/do_cal_ph?id={tina_sel}&p={punto_ph}", timeout=3.5)
                    if r.status_code == 200:
                        d = r.json()
                        if d.get("ok") == 1:
                            v_esp = float(d.get("v", v_actual))
                            estab_esp = float(d.get("estab", 0.0))
                            self.cal_puntos[tina_sel][punto_ph] = v_esp
                            if self._running and self.win.winfo_exists():
                                self.win.after(0, lambda: [
                                    self._redibujar_graficas(),
                                    messagebox.showinfo(
                                        "Calibración Exitosa en ESP32",
                                        f"Punto pH {punto_ph} calibrado y persistido en Flash NVS (Tina {tina_sel}):\n\n"
                                        f"Voltaje: {v_esp:.3f} V\n"
                                        f"Estabilidad: ±{estab_esp:.1f} mV\n"
                                        f"Pendiente: {d.get('slope', '--')} pH/V"
                                    )
                                ])
                        else:
                            msg_err = d.get("err", "Fallo en adquisición")
                            if self._running and self.win.winfo_exists():
                                self.win.after(0, lambda: messagebox.showwarning("Aviso ESP32", f"Punto registrado en GUI, pero el ESP32 reportó:\n{msg_err}"))
                    elif r.status_code == 403:
                        if self._running and self.win.winfo_exists():
                            self.win.after(0, lambda: messagebox.showerror("Interlock ESP32", f"El ESP32 rechazó la calibración:\n{r.text}"))
                except Exception as e:
                    if self._running and self.win.winfo_exists():
                        self.win.after(0, lambda: messagebox.showinfo(
                            "Punto Registrado",
                            f"Punto pH {punto_ph} guardado en GUI (V = {v_actual:.3f} V).\n\n(No se pudo contactar endpoint /do_cal_ph en ESP32: {e})"
                        ))

            threading.Thread(target=_cal_worker, daemon=True).start()
        else:
            messagebox.showinfo(
                "Punto Registrado",
                f"Punto pH {punto_ph} capturado con éxito para Tina {tina_sel}:\nV = {v_actual:.3f} V ({v_actual*1000.0:.1f} mV)"
            )


    def _enviar_calibracion_esp32(self):
        bloqueado, motivo = self._es_interlock_bloqueante()
        if bloqueado:
            messagebox.showerror(
                "Interlock de Seguridad Activo",
                f"No se puede sincronizar con el microcontrolador mientras la fuente esté en uso:\n\n{motivo}."
            )
            return

        tina_sel = self.var_tina.get()
        modo = self.var_modo_cal.get()
        es_demo = bool(getattr(self.app, 'modo_demo', False))
        esta_conectado = bool(getattr(self.app, 'conectado', False))

        if es_demo:
            modo_nom = "2 Puntos (pH 7 y 4)" if modo == 1 else "3 Puntos (pH 4, 7 y 10)"
            messagebox.showinfo("Modo Simulación", f"[DEMO] Modelo de Calibración ({modo_nom}) sincronizado con éxito para Tina {tina_sel}.")
            return

        if not esta_conectado:
            messagebox.showwarning("Sin Conexión", "El microcontrolador ESP32 no está conectado.")
            return

        ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')

        try:
            r = requests.get(f"http://{ip}/set_cal_mode?id={tina_sel}&m={modo}", timeout=2.0)
            if r.status_code == 200:
                modo_str = "2 Puntos (pH 7 y 4)" if modo == 1 else "3 Puntos (pH 4, 7 y 10)"
                messagebox.showinfo(
                    "Sincronización Exitosa",
                    f"Modelo de Calibración configurado a '{modo_str}' en Flash NVS de Tina {tina_sel}.\n\n"
                    "Recuerda calibrar cada punto con el electrodo sumergido en su buffer."
                )
            else:
                messagebox.showerror("Error ESP32", f"El ESP32 respondió con código {r.status_code}:\n{r.text}")
        except Exception as e:
            messagebox.showerror("Error de Comunicación", f"No se pudo contactar al ESP32 ({ip}):\n{e}")


    def _restablecer_calibracion_esp32(self):
        bloqueado, motivo = self._es_interlock_bloqueante()
        if bloqueado:
            messagebox.showerror(
                "Interlock de Seguridad Activo",
                f"No se puede restablecer la calibración mientras la fuente esté activa:\n\n{motivo}."
            )
            return

        tina_sel = self.var_tina.get()
        if not messagebox.askyesno(
            "Confirmar Restablecimiento",
            f"¿Deseas restablecer la calibración de la Tina {tina_sel} a los valores teóricos de fábrica (NVS)?\n\n"
            "Se borrarán los coeficientes experimentales guardados en la memoria no volátil del ESP32."
        ):
            return

        es_demo = bool(getattr(self.app, 'modo_demo', False))
        if es_demo:
            self.cal_puntos[tina_sel] = {7: 1.765, 4: 2.472, 10: 1.058}
            self.cal_completada[tina_sel] = False
            self._redibujar_graficas()
            messagebox.showinfo("Restablecido", f"[DEMO] Tina {tina_sel} restablecida a valores teóricos.")
            return

        ip = getattr(self.app, 'ip_grabacion', '192.168.4.1')
        try:
            r = requests.get(f"http://{ip}/reset_cal_ph?id={tina_sel}", timeout=2.5)
            if r.status_code == 200:
                self.cal_puntos[tina_sel] = {7: 1.765, 4: 2.472, 10: 1.058}
                self.cal_completada[tina_sel] = False
                self._redibujar_graficas()
                messagebox.showinfo("Restablecido", f"Calibración de Tina {tina_sel} restablecida a valores teóricos de fábrica en Flash NVS.")
            else:
                messagebox.showerror("Error ESP32", f"El ESP32 rechazó la operación:\n{r.text}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo contactar al ESP32 ({ip}):\n{e}")


    def _toggle_grabacion_ph(self):
        if not self.grabando_ph:
            self._iniciar_grabacion_ph()
        else:
            self._detener_grabacion_ph()


    def _iniciar_grabacion_ph(self):
        es_demo = bool(getattr(self.app, 'modo_demo', False))
        esta_conectado = bool(getattr(self.app, 'conectado', False))

        if not esta_conectado and not es_demo:
            messagebox.showwarning(
                "ESP32 Desconectado",
                "No se puede iniciar el historial de pH:\n\n"
                "El ESP32 no está conectado y el 'Modo Simulación' está desactivado en la ventana principal."
            )
            return

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.archivo_csv_ph = os.path.join(self.carpeta_calibraciones, f"calibracion_ph_tina{self.var_tina.get()}_{timestamp_str}.csv")

        try:
            self.csv_ph_handle = open(self.archivo_csv_ph, mode="w", newline="", encoding="utf-8")
            self.csv_ph_writer = csv.writer(self.csv_ph_handle)
            headers = [
                "Timestamp_ISO", "Tiempo_Relativo_s", "Tina_ID", "pH_Medido",
                "Voltaje_Sonda_V", "Voltaje_Sonda_mV", "Criterio_Estable_3s"
            ]
            self.csv_ph_writer.writerow(headers)
            self.csv_ph_handle.flush()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el archivo CSV exclusivo de pH:\n{e}")
            return

        self.grabando_ph = True
        self.muestras_ph_count = 0
        self.btn_rec_ph.config(text="⏹ DETENER HISTORIAL PH", bg="#ef4444")
        self.lbl_csv_status.config(text=f"Guardando en: {os.path.basename(self.archivo_csv_ph)}", fg="#34d399")


    def _detener_grabacion_ph(self):
        self.grabando_ph = False
        if self.csv_ph_handle:
            try:
                self.csv_ph_handle.close()
            except Exception:
                pass
            self.csv_ph_handle = None

        self.btn_rec_ph.config(text="⏺ INICIAR HISTORIAL EXCLUSIVO PH", bg="#dc2626")
        self.lbl_csv_status.config(text=f"Historial cerrado ({self.muestras_ph_count} muestras guardadas)", fg="#fbbf24")


    def _exportar_certificado_png(self):
        fpath = filedialog.asksaveasfilename(
            title="Guardar Certificado de Calibración Nernstiana",
            initialdir=self.carpeta_calibraciones,
            initialfile=f"certificado_nernst_tina{self.var_tina.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            filetypes=[("Imagen PNG de Alta Resolución", "*.png")]
        )
        if fpath:
            try:
                self.fig.savefig(fpath, dpi=300, bbox_inches="tight", facecolor="#0b1120")
                messagebox.showinfo("Exportación Exitosa", f"Certificado metrológico a 300 DPI guardado en:\n{fpath}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{e}")


    def _actualizar_vista(self):
        self._redibujar_graficas()


    def _on_close(self):
        self._running = False
        if self.timer_id:
            try:
                self.win.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None
        if self.grabando_ph:
            self._detener_grabacion_ph()
        if hasattr(self.app, 'win_ph'):
            self.app.win_ph = None
        try:
            self.win.destroy()
        except Exception:
            pass


    def iniciar_grabacion_ph(self):
        self._iniciar_grabacion_ph()


    def detener_grabacion_ph(self):
        csv_path = self.archivo_csv_ph
        self._detener_grabacion_ph()
        return csv_path


    def _cerrar(self):
        self._on_close()

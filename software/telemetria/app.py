#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
SISTEMA DE TELEMETRÍA EN VIVO, GESTOR DE ENSAYOS Y SUPERVISIÓN SCADA
===================================================================================
Tesis: Automatización y Control de Línea Piloto de Electrodeposición
Microcontrolador: ESP32 Master Node (Firmware v3.1 / v3.5)
===================================================================================
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from telemetria.comunicacion import ComunicacionMixin
from telemetria.grabacion import GrabacionMixin
from telemetria.gestor_ensayos import GestorEnsayosMixin
from telemetria.graficas import GraficasMixin

from telemetria.ventanas.actuadores import VentanaActuadores
from telemetria.ventanas.errores import VentanaErrores
from telemetria.ventanas.faraday import VentanaFaraday
from telemetria.ventanas.diagnostico import VentanaDiagnostico
from telemetria.ventanas.ph import VentanaPH


class TelemetriaApp(ComunicacionMixin, GrabacionMixin, GestorEnsayosMixin, GraficasMixin):

    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Monitor de Telemetría en Vivo y Gestor de Ensayos — ESP32 Electrodeposición")
        self.root.geometry("1260x860")
        self.root.minsize(1050, 720)
        self.root.configure(bg="#0b1120")

        # Protocolo de cierre limpio de la aplicación
        self.root.protocol("WM_DELETE_WINDOW", self._on_app_close)

        # Carpeta dedicada para guardar ensayos CSV
        self.carpeta_experimentos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experimentos")
        os.makedirs(self.carpeta_experimentos, exist_ok=True)

        # Referencias a ventanas modulares secundarias
        self.win_actuadores = None
        self.win_errores = None
        self.win_diag = None
        self.win_faraday = None
        self.win_ph = None

        # Estado interno de telemetría y Culombimetría Faradaica
        self.grabando = False
        self.conectado = False
        self.modo_demo = False
        self.demo_forzar_corriente = False
        self.hilo_muestreo = None
        self.csv_file_handle = None
        self.csv_writer = None
        self.csv_err_handle = None
        self.csv_err_writer = None
        self.csv_eventos_handle = None
        self.csv_eventos_writer = None
        self.archivo_csv = None
        self.archivo_csv_errores = None
        self.archivo_csv_eventos = None
        self.historia_eventos_fallos = []
        self.carpeta_ensayo_actual = ""
        self.carpeta_graficas_actual = ""
        self.ultimo_csv_generado = ""
        self.tiempo_inicio = None
        self.muestras_count = 0

        # Balanza Gravimétrica y Ley de Faraday (m = Q*M / z*F)
        # Soporte Bicapa: Zincado (T3) + Niquelado (T4) con pesaje único al final de Etapa 4
        self.coulombs_total = 0.0
        self.coulombs_etapa = 0.0
        self.coulombs_zn = 0.0
        self.coulombs_ni = 0.0
        self.peso_inicial_g = 0.0
        self.peso_final_g = 0.0
        self.area_placa_cm2 = 65.0

        # Últimos valores calculados de actuadores y corriente
        self.ultimo_u1 = 0.0
        self.ultimo_u2 = 0.0
        self.ultimo_u3 = 0.0
        self.ultimo_u4 = 0.0
        self.ultimo_amps = 0.0
        self.ultimo_d_ph = None
        self.ultimo_d_f = None
        self.ultimo_d_t = None
        self.ultimo_d_env = None

        # Índices de Desempeño Acumulativos IAE (Integral of Absolute Error)
        self.iae_t1 = 0.0
        self.iae_t2 = 0.0
        self.iae_t3 = 0.0
        self.iae_t4 = 0.0
        self.iae_curr = 0.0

        # Buffers para gráficas en vivo (últimas 300 muestras ~ 5 minutos @ 1s)
        self.max_muestras_plot = 300
        self.buf_t = []
        self.buf_t1 = []
        self.buf_t1_sp = []
        self.buf_t2 = []
        self.buf_t2_sp = []
        self.buf_t3 = []
        self.buf_t3_sp = []
        self.buf_t4 = []
        self.buf_t4_sp = []
        self.buf_u1 = []
        self.buf_u2 = []
        self.buf_u3 = []
        self.buf_u4 = []
        self.buf_curr = []
        self.buf_curr_avg = []
        self.buf_q = []
        self.buf_m_teo = []
        self.buf_ph1 = []
        self.buf_ph2 = []
        self.buf_ph_on = []

        # Estado del Gestor de Ensayos / Recetas (ISA-88)
        self.excel_path = self._buscar_excel_defecto()
        self.lista_placas = []
        self.placa_activa = None
        self.etapa_activa_idx = 0  # 0: Limpieza, 1: Decapado, 2: Zincado, 3: Niquelado
        self.etapa_corriendo = False
        self.etapa_segundos_restantes = 0
        self.etapa_duracion_total = 0
        self.etapa_segundos_transcurridos = 0
        self.t_inicio_etapa_real = None
        self.t_acumulado_etapa = 0.0
        self.filtro_actual = "TODOS"
        self.marcadores_etapas = []
        self.hb_phase = 0

        self._cargar_datos_excel()
        self._crear_interfaz()
        self._animar_heartbeat_ui()
        self._probar_conexion_silenciosa()
        self._iniciar_timer_etapa_loop()


    def _crear_interfaz(self):
        # 1. Header / Barra superior
        hdr = tk.Frame(self.root, bg="#0f172a", height=54, bd=0)
        hdr.pack(fill="x", side="top")

        # Borde lateral con indicador de estado (B1)
        self.header_accent = tk.Frame(hdr, bg="#ef4444", width=5)
        self.header_accent.pack(side="left", fill="y")

        lbl_title = tk.Label(
            hdr,
            text="MONITOR DE TELEMETRÍA Y CONTROL DE PROCESO — ESP32",
            font=("Segoe UI", 11, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
        )
        lbl_title.pack(side="left", padx=12, pady=10)

        # Botones de Acceso a Ventanas Modulares
        btn_act = tk.Button(
            hdr,
            text="Oscilogramas",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            activebackground="#38bdf8",
            activeforeground="#0f172a",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_actuadores
        )
        btn_act.pack(side="left", padx=3)

        btn_err = tk.Button(
            hdr,
            text="Errores & Fase",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#34d399",
            activebackground="#34d399",
            activeforeground="#0f172a",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_errores
        )
        btn_err.pack(side="left", padx=3)

        btn_faraday = tk.Button(
            hdr,
            text="⚖️ Faraday / Balanza",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#f472b6",
            activebackground="#f472b6",
            activeforeground="#0f172a",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_faraday
        )
        btn_faraday.pack(side="left", padx=3)

        btn_diag = tk.Button(
            hdr,
            text="Diagnóstico",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#fbbf24",
            activebackground="#fbbf24",
            activeforeground="#0f172a",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_diagnostico
        )
        btn_diag.pack(side="left", padx=3)

        btn_ph = tk.Button(
            hdr,
            text="🧪 Metrología pH",
            font=("Segoe UI", 8, "bold"),
            bg="#1e293b",
            fg="#c084fc",
            activebackground="#c084fc",
            activeforeground="#0f172a",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_ph
        )
        btn_ph.pack(side="left", padx=3)

        # Panel IP y Estado
        frame_ip = tk.Frame(hdr, bg="#0f172a")
        frame_ip.pack(side="right", padx=12, pady=6)

        # Checkbox Demo Mode
        self.var_demo = tk.BooleanVar(value=False)
        chk_demo = tk.Checkbutton(
            frame_ip,
            text="Modo Simulación",
            variable=self.var_demo,
            font=("Segoe UI", 8, "bold"),
            fg="#fbbf24",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#fbbf24",
            command=self._on_toggle_demo
        )
        chk_demo.pack(side="left", padx=3)

        self.btn_demo_curr = tk.Button(
            frame_ip,
            text="Forzar Corriente",
            font=("Segoe UI", 7, "bold"),
            bg="#1e293b",
            fg="#94a3b8",
            activebackground="#22c55e",
            activeforeground="#0f172a",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self._toggle_forzar_corriente_demo
        )
        self.btn_demo_curr.pack(side="left", padx=3)

        tk.Label(frame_ip, text="IP:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(side="left", padx=2)
        self.entry_ip = tk.Entry(frame_ip, font=("Segoe UI", 8), width=11, bg="#1e293b", fg="#f8fafc", insertbackground="#38bdf8")
        self.entry_ip.insert(0, "192.168.4.1")
        self.entry_ip.pack(side="left", padx=3)

        self.btn_ping = tk.Button(
            frame_ip,
            text="Ping",
            font=("Segoe UI", 7, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.probar_conexion_manual
        )
        self.btn_ping.pack(side="left", padx=2)

        # Indicador animado de estado de conexión (B1)
        frame_status_badge = tk.Frame(frame_ip, bg="#0f172a")
        frame_status_badge.pack(side="left", padx=4)

        self.canvas_heartbeat = tk.Canvas(frame_status_badge, width=14, height=14, bg="#0f172a", highlightthickness=0)
        self.canvas_heartbeat.pack(side="left", padx=2)

        self.lbl_status = tk.Label(
            frame_status_badge,
            text="DESCONECTADO",
            font=("Segoe UI", 8, "bold"),
            fg="#ef4444",
            bg="#0f172a",
        )
        self.lbl_status.pack(side="left", padx=2)

        # 2. CUERPO PRINCIPAL DIVIDIDO EN 2 COLUMNAS
        body = tk.Frame(self.root, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=8, pady=4)

        # =========================================================================
        # COLUMNA IZQUIERDA: GESTOR DE MATRIZ DE ENSAYOS & TEMPORIZADOR DE ETAPAS
        # =========================================================================
        panel_recetas = tk.Frame(body, bg="#111827", width=360, bd=1, relief="solid")
        panel_recetas.pack(side="left", fill="y", padx=4, pady=2)
        panel_recetas.pack_propagate(False)

        lbl_sec_rec = tk.Label(
            panel_recetas,
            text="GESTOR DE RECETAS (ISA-88)",
            font=("Segoe UI", 10, "bold"),
            fg="#38bdf8",
            bg="#111827"
        )
        lbl_sec_rec.pack(anchor="w", padx=10, pady=(8, 2))

        frame_xl = tk.Frame(panel_recetas, bg="#111827")
        frame_xl.pack(fill="x", padx=8, pady=2)

        self.lbl_xl_info = tk.Label(
            frame_xl,
            text=f"{len(self.lista_placas)} placas cargadas",
            font=("Segoe UI", 7),
            fg="#94a3b8",
            bg="#111827",
            anchor="w"
        )
        self.lbl_xl_info.pack(side="left", fill="x", expand=True)

        btn_load_xl = tk.Button(
            frame_xl,
            text="Abrir Excel",
            font=("Segoe UI", 7, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.cargar_archivo_excel
        )
        btn_load_xl.pack(side="right")

        lbl_filt = tk.Label(
            panel_recetas,
            text="Filtro por Condición de Baño:",
            font=("Segoe UI", 8, "bold"),
            fg="#cbd5e1",
            bg="#111827"
        )
        lbl_filt.pack(anchor="w", padx=10, pady=(6, 2))

        frame_filtros = tk.Frame(panel_recetas, bg="#111827")
        frame_filtros.pack(fill="x", padx=8, pady=1)

        self.btn_f_all = self._crear_btn_filtro(frame_filtros, "Todos", "TODOS", 0, 0)
        self.btn_f_p2_25 = self._crear_btn_filtro(frame_filtros, "pH 2 • 25°C", "pH 2 — 25°C", 0, 1)
        self.btn_f_p2_40 = self._crear_btn_filtro(frame_filtros, "pH 2 • 40°C", "pH 2 — 40°C", 0, 2)
        self.btn_f_p4_25 = self._crear_btn_filtro(frame_filtros, "pH 4 • 25°C", "pH 4 — 25°C", 1, 0)
        self.btn_f_p4_40 = self._crear_btn_filtro(frame_filtros, "pH 4 • 40°C", "pH 4 — 40°C", 1, 1)

        lbl_sel_placa = tk.Label(
            panel_recetas,
            text="Seleccionar Placa a Ejecutar:",
            font=("Segoe UI", 8, "bold"),
            fg="#cbd5e1",
            bg="#111827"
        )
        lbl_sel_placa.pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_placas = ttk.Combobox(panel_recetas, font=("Segoe UI", 8), state="readonly")
        self.combo_placas.pack(fill="x", padx=10, pady=2)
        self.combo_placas.bind("<<ComboboxSelected>>", self._on_placa_seleccionada)

        self.frame_badges = tk.Frame(panel_recetas, bg="#1e293b", bd=0, padx=6, pady=4)
        self.frame_badges.pack(fill="x", padx=8, pady=4)

        self.lbl_badge_ronda = tk.Label(self.frame_badges, text="Ronda: --", font=("Segoe UI", 7, "bold"), fg="#38bdf8", bg="#1e293b")
        self.lbl_badge_ronda.pack(anchor="w")

        self.lbl_badge_cond = tk.Label(self.frame_badges, text="Baño: pH -- | -- °C", font=("Segoe UI", 7, "bold"), fg="#34d399", bg="#1e293b")
        self.lbl_badge_cond.pack(anchor="w")

        self.lbl_badge_zin = tk.Label(self.frame_badges, text="Zincado: --", font=("Segoe UI", 7, "bold"), fg="#f472b6", bg="#1e293b")
        self.lbl_badge_zin.pack(anchor="w")

        self.lbl_badge_niq = tk.Label(self.frame_badges, text="Níquel: DC 1.13 A (600s)", font=("Segoe UI", 7, "bold"), fg="#a78bfa", bg="#1e293b")
        self.lbl_badge_niq.pack(anchor="w")

        lbl_sec = tk.Label(
            panel_recetas,
            text="Secuencia de Etapas:",
            font=("Segoe UI", 8, "bold"),
            fg="#cbd5e1",
            bg="#111827"
        )
        lbl_sec.pack(anchor="w", padx=10, pady=(6, 2))

        self.frame_etapas = tk.Frame(panel_recetas, bg="#111827")
        self.frame_etapas.pack(fill="x", padx=8, pady=2)

        self.lbl_e1 = self._crear_fila_etapa(self.frame_etapas, 1, "Limpieza Electrolítica (T1)", "240s @ 85°C | 0.00A")
        self.lbl_e2 = self._crear_fila_etapa(self.frame_etapas, 2, "Decapado Ácido (T2)", "120s @ 85°C | 0.00A")
        self.lbl_e3 = self._crear_fila_etapa(self.frame_etapas, 3, "Zincado (T3)", "120s @ 25°C | 1.50A")
        self.lbl_e4 = self._crear_fila_etapa(self.frame_etapas, 4, "Niquelado Watts (T4)", "600s @ 30°C | 1.13A DC (pH 5.5)")

        frame_clock_box = tk.Frame(panel_recetas, bg="#1e293b", bd=0, padx=6, pady=6)
        frame_clock_box.pack(fill="x", padx=8, pady=6)

        self.lbl_etapa_titulo = tk.Label(
            frame_clock_box,
            text="ETAPA 1/4: LIMPIEZA",
            font=("Segoe UI", 8, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        self.lbl_etapa_titulo.pack()

        self.lbl_timer_big = tk.Label(
            frame_clock_box,
            text="04:00",
            font=("Segoe UI", 26, "bold"),
            fg="#38bdf8",
            bg="#1e293b"
        )
        self.lbl_timer_big.pack(pady=1)

        # Canvas con gradiente y marcadores de cuartos (B3)
        self.canvas_prog_etapa = tk.Canvas(frame_clock_box, height=18, bg="#0f172a", bd=0, highlightthickness=1, highlightbackground="#334155")
        self.canvas_prog_etapa.pack(fill="x", padx=6, pady=4)
        self.canvas_prog_etapa.bind("<Configure>", lambda e: self._dibujar_progreso_canvas(getattr(self, '_ultimo_prog_pct', 0)))

        self.lbl_aviso_etapa = tk.Label(
            frame_clock_box,
            text="Listo para iniciar.",
            font=("Segoe UI", 7, "italic"),
            fg="#94a3b8",
            bg="#1e293b"
        )
        self.lbl_aviso_etapa.pack()

        frame_stage_btns = tk.Frame(panel_recetas, bg="#111827")
        frame_stage_btns.pack(fill="x", padx=8, pady=3)

        self.btn_stage_prev = tk.Button(
            frame_stage_btns,
            text="Anterior",
            font=("Segoe UI", 7, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=6,
            pady=5,
            cursor="hand2",
            command=self.retroceder_etapa_anterior
        )
        self.btn_stage_prev.pack(side="left", padx=1)

        self.btn_stage_toggle = tk.Button(
            frame_stage_btns,
            text="Iniciar Etapa",
            font=("Segoe UI", 8, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self.toggle_etapa
        )
        self.btn_stage_toggle.pack(side="left", expand=True, fill="x", padx=1)

        self.btn_stage_next = tk.Button(
            frame_stage_btns,
            text="Siguiente",
            font=("Segoe UI", 7, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=6,
            pady=5,
            cursor="hand2",
            command=self.avanzar_siguiente_etapa
        )
        self.btn_stage_next.pack(side="left", padx=1)

        self.btn_stage_reset = tk.Button(
            frame_stage_btns,
            text="Reiniciar",
            font=("Segoe UI", 7, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            bd=0,
            padx=6,
            pady=5,
            cursor="hand2",
            command=self.reiniciar_etapa_actual
        )
        self.btn_stage_reset.pack(side="left", padx=1)

        # Panel de Sincronización de Setpoints con ESP32 (Automático / Manual)
        frame_hw_box = tk.Frame(panel_recetas, bg="#1e293b", bd=0, padx=6, pady=5)
        frame_hw_box.pack(fill="x", padx=8, pady=3)

        self.var_auto_sync_hw = tk.BooleanVar(value=True)
        chk_auto_sp = tk.Checkbutton(
            frame_hw_box,
            text="Auto-enviar SPs al iniciar etapa",
            variable=self.var_auto_sync_hw,
            font=("Segoe UI", 7, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8"
        )
        chk_auto_sp.pack(anchor="w")

        frame_hw_actions = tk.Frame(frame_hw_box, bg="#1e293b")
        frame_hw_actions.pack(fill="x", pady=2)

        self.btn_send_sp = tk.Button(
            frame_hw_actions,
            text="Cargar en ESP32",
            font=("Segoe UI", 7, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            bd=0,
            padx=6,
            pady=3,
            cursor="hand2",
            command=lambda: self.enviar_setpoints_esp32(feedback_usuario=True)
        )
        self.btn_send_sp.pack(side="left", expand=True, fill="x", padx=1)

        self.btn_test_alarm = tk.Button(
            frame_hw_actions,
            text="Alarma",
            font=("Segoe UI", 7, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=5,
            pady=3,
            cursor="hand2",
            command=self.probar_alarma
        )
        self.btn_test_alarm.pack(side="left", padx=1)

        self.lbl_hw_sync_status = tk.Label(
            frame_hw_box,
            text="ESP32: Listo para sincronizar",
            font=("Segoe UI", 7),
            fg="#94a3b8",
            bg="#1e293b",
            anchor="w"
        )
        self.lbl_hw_sync_status.pack(fill="x", pady=(1, 0))

        frame_stab = tk.Frame(panel_recetas, bg="#1e293b", bd=0, padx=6, pady=4)
        frame_stab.pack(fill="x", padx=8, pady=(4, 8), side="bottom")

        tk.Label(
            frame_stab,
            text="Estabilidad de Corriente (ADS1115):",
            font=("Segoe UI", 7, "bold"),
            fg="#94a3b8",
            bg="#1e293b"
        ).pack(anchor="w")

        self.lbl_stab_val = tk.Label(
            frame_stab,
            text="En reposo (0.00 A)",
            font=("Segoe UI", 8, "bold"),
            fg="#22c55e",
            bg="#1e293b"
        )
        self.lbl_stab_val.pack(anchor="w")

        # =========================================================================
        # COLUMNA DERECHA: TELEMETRÍA EN VIVO, KPIS Y GRÁFICAS MATPLOTLIB
        # =========================================================================
        panel_telemetria = tk.Frame(body, bg="#0b1120")
        panel_telemetria.pack(side="left", fill="both", expand=True, padx=4, pady=0)

        ctrl_frame = tk.Frame(panel_telemetria, bg="#1e293b", bd=0)
        ctrl_frame.pack(fill="x", padx=4, pady=2)

        btn_frame = tk.Frame(ctrl_frame, bg="#1e293b")
        btn_frame.pack(side="left", padx=8, pady=6)

        self.btn_rec = tk.Button(
            btn_frame,
            text="INICIAR GRABACIÓN",
            font=("Segoe UI", 8, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.toggle_grabacion
        )
        self.btn_rec.pack(side="left", padx=3)

        self.btn_plot = tk.Button(
            btn_frame,
            text="Exportar Gráficas (300 DPI)",
            font=("Segoe UI", 8, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.exportar_grafica_hd
        )
        self.btn_plot.pack(side="left", padx=3)

        self.btn_folder = tk.Button(
            btn_frame,
            text="Carpeta Ensayo",
            font=("Segoe UI", 8, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.abrir_carpeta_datos
        )
        self.btn_folder.pack(side="left", padx=3)

        self.btn_offline_mgr = tk.Button(
            btn_frame,
            text="📁 Gestor de Gráficas",
            font=("Segoe UI", 8, "bold"),
            bg="#0f766e",
            fg="#ffffff",
            activebackground="#14b8a6",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.abrir_gestor_graficas_offline
        )
        self.btn_offline_mgr.pack(side="left", padx=3)

        kpi_frame = tk.Frame(ctrl_frame, bg="#1e293b")
        kpi_frame.pack(side="right", padx=10, pady=6)

        self.lbl_time = tk.Label(kpi_frame, text="Tiempo: 00:00", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#1e293b")
        self.lbl_time.pack(side="left", padx=8)

        self.lbl_samples = tk.Label(kpi_frame, text="Muestras: 0", font=("Segoe UI", 9, "bold"), fg="#a78bfa", bg="#1e293b")
        self.lbl_samples.pack(side="left", padx=8)

        self.lbl_incidentes = tk.Label(
            kpi_frame,
            text="⚠️ Incidentes: 0",
            font=("Segoe UI", 9, "bold"),
            fg="#22c55e",
            bg="#1e293b",
            cursor="hand2"
        )
        self.lbl_incidentes.pack(side="left", padx=8)
        self.lbl_incidentes.bind("<Button-1>", lambda e: self.abrir_ventana_diagnostico())

        # 2. Tarjetas Rápidas de Sensores en Vivo con Indicadores de Gate TRIAC
        cards_bar = tk.Frame(panel_telemetria, bg="#0b1120")
        cards_bar.pack(fill="x", padx=2, pady=2)

        self.card_t1 = self._crear_card_tina(cards_bar, "T1: Limpieza", 450.0, "#d95f02", canal_idx=0)
        self.card_t2 = self._crear_card_tina(cards_bar, "T2: Decapado", 450.0, "#e6ab02", canal_idx=1)
        self.card_t3 = self._crear_card_tina(cards_bar, "T3: Celda Hull", 18.0, "#38bdf8", canal_idx=2)
        self.card_t4 = self._crear_card_tina(cards_bar, "T4: Níquel", 450.0, "#a78bfa", canal_idx=3)
        self.card_coulomb = self._crear_kpi_box(cards_bar, "Carga Q (Coulombs)", "0.0 C", "#f472b6", click_cmd=self.abrir_ventana_faraday)
        self.card_amp = self._crear_kpi_box(cards_bar, "Corriente (VCSS)", "0.00 A", "#22c55e", click_cmd=lambda: self.abrir_ventana_actuadores(4))
        self.card_ph = self._crear_kpi_box(cards_bar, "Sondas pH", "-- / --", "#c084fc", click_cmd=self.abrir_ventana_ph)
        self.card_env = self._crear_kpi_box(cards_bar, "Ambiente", "-- °C", "#94a3b8")

        # 3. Área de Gráficas en Vivo con Matplotlib embebido (3 Subplots Amplios: Térmico, TRIACs, Corriente)
        plot_frame = tk.Frame(panel_telemetria, bg="#0b1120")
        plot_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.fig = Figure(figsize=(8.5, 6.0), dpi=100, facecolor="#0f172a")
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        self.ax3 = self.fig.add_subplot(3, 1, 3)

        self._estilizar_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 4. Footer con información de archivo y anotaciones
        self.lbl_csv_info = tk.Label(
            self.root,
            text="Listo para iniciar. Los ensayos se guardarán en subcarpetas dentro de: telemetria/experimentos/",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg="#0b1120",
            anchor="w",
            padx=14,
            pady=3
        )
        self.lbl_csv_info.pack(fill="x", side="bottom")

        self._actualizar_lista_combo()


    def abrir_ventana_actuadores(self, canal_idx=0):
        if self.win_actuadores is None or not self.win_actuadores.win.winfo_exists():
            self.win_actuadores = VentanaActuadores(self, canal_inicial=canal_idx)
        else:
            if canal_idx is not None and canal_idx <= 5:
                self.win_actuadores._seleccionar_canal(canal_idx)
            self.win_actuadores.win.lift()


    def abrir_ventana_errores(self):
        if self.win_errores is None or not self.win_errores.win.winfo_exists():
            self.win_errores = VentanaErrores(self)
        else:
            self.win_errores.win.lift()


    def abrir_ventana_faraday(self):
        if self.win_faraday is None or not self.win_faraday.win.winfo_exists():
            self.win_faraday = VentanaFaraday(self)
        else:
            self.win_faraday.win.lift()


    def abrir_ventana_diagnostico(self):
        if self.win_diag is None or not self.win_diag.win.winfo_exists():
            self.win_diag = VentanaDiagnostico(self)
        else:
            self.win_diag.win.lift()


    def abrir_ventana_ph(self):
        if self.win_ph is None or not self.win_ph.win.winfo_exists():
            self.win_ph = VentanaPH(self)
        else:
            self.win_ph.win.lift()


    def _crear_btn_filtro(self, parent, text, tag, row, col):
        b = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 7, "bold"),
            bg="#1e293b" if tag != "TODOS" else "#2563eb",
            fg="#f8fafc",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=4,
            pady=2,
            cursor="hand2",
            command=lambda: self._aplicar_filtro(tag)
        )
        b.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        parent.grid_columnconfigure(col, weight=1)
        return b


    def _crear_fila_etapa(self, parent, num, nombre, desc_def):
        f = tk.Frame(parent, bg="#111827", pady=1)
        f.pack(fill="x")
        lbl_num = tk.Label(f, text=f"{num}.", font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#111827", width=2)
        lbl_num.pack(side="left")
        lbl_txt = tk.Label(f, text=f"{nombre}: {desc_def}", font=("Segoe UI", 7), fg="#cbd5e1", bg="#111827", anchor="w")
        lbl_txt.pack(side="left", fill="x", expand=True)
        return lbl_txt


    def _crear_kpi_box(self, parent, title, val_def, color, click_cmd=None):
        f = tk.Frame(parent, bg="#1e293b", bd=0, padx=6, pady=3, cursor="hand2" if click_cmd else "arrow")
        f.pack(side="left", expand=True, fill="x", padx=2)
        lbl_t = tk.Label(f, text=title, font=("Segoe UI", 7, "bold"), fg="#64748b", bg="#1e293b", cursor="hand2" if click_cmd else "arrow")
        lbl_t.pack()
        lbl_v = tk.Label(f, text=val_def, font=("Segoe UI", 9, "bold"), fg=color, bg="#1e293b", cursor="hand2" if click_cmd else "arrow")
        lbl_v.pack()
        if click_cmd:
            for w in (f, lbl_t, lbl_v):
                w.bind("<Button-1>", lambda e: click_cmd())
        return lbl_v


    def _crear_card_tina(self, parent, title, max_w, color, canal_idx=0):
        f = tk.Frame(parent, bg="#1e293b", bd=1, relief="solid", highlightthickness=1, highlightbackground="#334155", padx=5, pady=3, cursor="hand2")
        f.pack(side="left", expand=True, fill="both", padx=2)

        hdr_row = tk.Frame(f, bg="#1e293b")
        hdr_row.pack(fill="x")
        lbl_h = tk.Label(hdr_row, text=f"{title} ({max_w:.0f}W)", font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#1e293b", cursor="hand2")
        lbl_h.pack(side="left")

        # Indicador de tendencia térmica (B2)
        lbl_trend = tk.Label(hdr_row, text="→ Est", font=("Segoe UI", 7, "bold"), fg="#34d399", bg="#1e293b", cursor="hand2")
        lbl_trend.pack(side="right")

        lbl_temp = tk.Label(f, text="-- °C / SP --°C", font=("Segoe UI", 8, "bold"), fg=color, bg="#1e293b", cursor="hand2")
        lbl_temp.pack(anchor="w")
        lbl_gate = tk.Label(f, text="Gate: 0% (α=180°)", font=("Segoe UI", 7, "bold"), fg="#64748b", bg="#1e293b", cursor="hand2")
        lbl_gate.pack(anchor="w")
        lbl_w = tk.Label(f, text="0.0 W", font=("Segoe UI", 7), fg="#34d399", bg="#1e293b", cursor="hand2")
        lbl_w.pack(anchor="w")

        # Al hacer clic en cualquier parte de la tarjeta, abrir el osciloscopio en ese canal
        for widget in (f, hdr_row, lbl_h, lbl_trend, lbl_temp, lbl_gate, lbl_w):
            widget.bind("<Button-1>", lambda e, c=canal_idx: self.abrir_ventana_actuadores(c))

        return {
            "frame": f,
            "hdr_row": hdr_row,
            "hdr": lbl_h,
            "trend": lbl_trend,
            "temp": lbl_temp,
            "gate": lbl_gate,
            "watts": lbl_w,
            "last_t": None,
            "default_color": color
        }


    def _animar_heartbeat_ui(self):
        self.hb_phase = (self.hb_phase + 1) % 4
        if self.modo_demo:
            color = "#fbbf24"
            r = 5 if self.hb_phase in (1, 2) else 3
            accent_c = "#fbbf24"
        elif self.conectado:
            color = "#34d399"
            r = 5 if self.hb_phase in (1, 2) else 3
            accent_c = "#34d399"
        else:
            color = "#ef4444"
            r = 4
            accent_c = "#ef4444"
        
        if hasattr(self, 'header_accent'):
            self.header_accent.config(bg=accent_c)

        if hasattr(self, 'canvas_heartbeat'):
            self.canvas_heartbeat.delete("all")
            if (self.conectado or self.modo_demo) and self.hb_phase in (1, 2):
                self.canvas_heartbeat.create_oval(7-r-1, 7-r-1, 7+r+1, 7+r+1, fill="", outline=color, width=1)
            self.canvas_heartbeat.create_oval(7-r, 7-r, 7+r, 7+r, fill=color, outline="")

        self.root.after(350, self._animar_heartbeat_ui)


    def _dibujar_progreso_canvas(self, pct):
        self._ultimo_prog_pct = pct
        if not hasattr(self, 'canvas_prog_etapa'):
            return
        w = self.canvas_prog_etapa.winfo_width()
        if w <= 1:
            w = 320
        h = 18
        self.canvas_prog_etapa.delete("all")
        
        fill_w = max(0, min(w, (pct / 100.0) * w))
        
        if pct < 50:
            bar_color = "#0284c7"
        elif pct < 85:
            bar_color = "#059669"
        else:
            bar_color = "#10b981"
            
        if fill_w > 0:
            self.canvas_prog_etapa.create_rectangle(0, 0, fill_w, h, fill=bar_color, outline="")
        
        # Marcadores de cuartos (25%, 50%, 75%)
        for q in (0.25, 0.50, 0.75):
            qx = w * q
            self.canvas_prog_etapa.create_line(qx, 0, qx, h, fill="#475569", width=1, dash=(2, 2))
        
        pct_txt = f"{pct:.0f}%"
        self.canvas_prog_etapa.create_text(w//2 + 1, h//2 + 1, text=pct_txt, fill="#0b1120", font=("Segoe UI", 8, "bold"))
        self.canvas_prog_etapa.create_text(w//2, h//2, text=pct_txt, fill="#f8fafc", font=("Segoe UI", 8, "bold"))


    def _on_app_close(self):
        try:
            self.apagar_fuente_esp32()
        except Exception:
            pass
        if self.grabando:
            self.detener_grabacion()
        self.root.destroy()



def main():
    root = tk.Tk()
    app = TelemetriaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

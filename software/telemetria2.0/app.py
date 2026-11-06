#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
SISTEMA DE TELEMETRÍA EN VIVO, GESTOR DE ENSAYOS Y SUPERVISIÓN SCADA (Telemetría 2.0)
===================================================================================
Tesis: Automatización y Control de Línea Piloto de Electrodeposición
Microcontrolador: ESP32-S3 N16R8 Master Node (Firmware RTOS 2.0)
Módulos:
  - Adquisición HTTP periódica (/data_all) con resiliencia ante jitter Wi-Fi
  - Culombimetría Faradaica continua e integración gravimétrica asistida
  - Matriz experimental ISA-88 para protocolos de zincado y niquelado sobre aluminio
  - Exportación de telemetría a CSV y suites de figuras científicas a 300 DPI
===================================================================================
"""

import sys
import os

# Asegurar que el directorio propio de telemetria2.0 esté en sys.path
dir_app = os.path.dirname(os.path.abspath(__file__))
if dir_app not in sys.path:
    sys.path.insert(0, dir_app)

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from comunicacion import ComunicacionMixin
from grabacion import GrabacionMixin
from gestor_ensayos import GestorEnsayosMixin
from graficas import GraficasMixin

from ventanas.actuadores import VentanaActuadores
from ventanas.errores import VentanaErrores
from ventanas.faraday import VentanaFaraday
from ventanas.diagnostico import VentanaDiagnostico
from ventanas.ph import VentanaPH
from ventanas.nube import VentanaNube
from ventanas.visor_datos import VentanaVisorDatos
from utilidades.scrollable_frame import ScrollableFrame
from utilidades.tema import cargar_tema_preferido, guardar_tema_preferido, TEMA_DIA, TEMA_NOCHE


class TelemetriaApp(ComunicacionMixin, GrabacionMixin, GestorEnsayosMixin, GraficasMixin):

    def __init__(self, root):
        self.root = root

        # Sistema de Temas y Visibilidad
        self.tema_actual = cargar_tema_preferido()
        self.graficas_visibles = True
        self.root.title("Monitor de Telemetría 2.0 y Gestor de Ensayos — ESP32 Electrodeposición (Sensor Dedicado A1)")
        self.root.geometry("1260x860")
        self.root.minsize(1050, 720)
        self.root.configure(bg=self.tema_actual["bg_app"])

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
        self.win_nube = None
        self.win_visor = None


        # Estado interno de telemetría y Culombimetría Faradaica
        self.grabando = False
        self.conectado = False
        self.modo_demo = False
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
        self.demo_forzar_corriente = False

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
        self.hdr_frame = tk.Frame(self.root, bg=self.tema_actual["bg_header"], height=54, bd=0)
        self.hdr_frame.pack(fill="x", side="top")
        hdr = self.hdr_frame

        # Borde lateral con indicador de estado (B1)
        self.header_accent = tk.Frame(hdr, bg="#ef4444", width=5)
        self.header_accent.pack(side="left", fill="y")

        lbl_title = tk.Label(
            hdr,
            text="MONITOR DE TELEMETRÍA Y CONTROL DE PROCESO — ESP32",
            font=("Segoe UI", 11, "bold"),
            fg=self.tema_actual["accent_primary"],
            bg=self.tema_actual["bg_panel"],
        )
        lbl_title.pack(side="left", padx=12, pady=10)

        # Título y Subtítulo Encabezado
        self.lbl_hdr_title = lbl_title

        # Botones de Acceso a Ventanas Modulares
        btn_act = tk.Button(
            hdr,
            text="Oscilogramas",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg=self.tema_actual["accent_primary"],
            activebackground=self.tema_actual["accent_hover"],
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_actuadores
        )
        btn_act.pack(side="left", padx=2)

        btn_err = tk.Button(
            hdr,
            text="Errores & Fase",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg="#34d399",
            activebackground="#34d399",
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_errores
        )
        btn_err.pack(side="left", padx=2)

        btn_faraday = tk.Button(
            hdr,
            text="Balanza Faraday",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg="#f472b6",
            activebackground="#f472b6",
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_faraday
        )
        btn_faraday.pack(side="left", padx=2)

        btn_ph = tk.Button(
            hdr,
            text="Sensor pH",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg="#c084fc",
            activebackground="#c084fc",
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_ph
        )
        btn_ph.pack(side="left", padx=2)

        btn_visor = tk.Button(
            hdr,
            text="Explorador de Datos",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg="#34d399",
            activebackground="#34d399",
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_visor_datos
        )
        btn_visor.pack(side="left", padx=2)

        btn_nube = tk.Button(
            hdr,
            text="Nube / Supabase",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg=self.tema_actual["accent_primary"],
            activebackground=self.tema_actual["accent_hover"],
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_nube
        )
        btn_nube.pack(side="left", padx=2)

        btn_diag = tk.Button(
            hdr,
            text="Diagnóstico",
            font=("Segoe UI", 8, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg="#fbbf24",
            activebackground="#fbbf24",
            activeforeground=self.tema_actual["bg_panel"],
            bd=0,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.abrir_ventana_diagnostico
        )
        btn_diag.pack(side="left", padx=2)

        self._top_nav_buttons = [btn_act, btn_err, btn_faraday, btn_ph, btn_visor, btn_nube, btn_diag]
        self._nav_btn_definitions = [
            (btn_act, "#2563eb", self.tema_actual["accent_primary"]),      # Oscilogramas (Cobalt / Cian)
            (btn_err, "#059669", "#34d399"),      # Errores & Fase (Esmeralda / Verde)
            (btn_faraday, "#9333ea", "#f472b6"),  # Balanza (Púrpura / Rosa)
            (btn_ph, "#7c3aed", "#c084fc"),       # pH (Violeta / Lavanda)
            (btn_visor, "#0d9488", "#34d399"),    # Explorador (Teal / Verde)
            (btn_nube, "#0284c7", self.tema_actual["accent_primary"]),     # Nube (Azul Técnico / Cian)
            (btn_diag, "#d97706", "#fbbf24"),     # Diagnóstico (Ámbar / Amarillo)
        ]

        # Botón conmutador Modo Día / Noche
        self.btn_tema = tk.Button(
            hdr,
            text="MODO DÍA" if self.tema_actual["nombre"] == "noche" else "MODO NOCHE",
            font=("Segoe UI", 8, "bold"),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.toggle_tema_dia_noche
        )
        self.btn_tema.pack(side="left", padx=6)

        # Panel IP y Estado
        self.frame_ip = tk.Frame(hdr, bg=self.tema_actual["bg_header"])
        self.frame_ip.pack(side="right", padx=12, pady=6)
        frame_ip = self.frame_ip

        # Checkbox Demo Mode
        self.var_demo = tk.BooleanVar(value=False)
        self.chk_demo = tk.Checkbutton(
            frame_ip,
            text="Modo Simulación",
            variable=self.var_demo,
            font=("Segoe UI", 8, "bold"),
            fg=self.tema_actual["warning"],
            bg=self.tema_actual["bg_header"],
            selectcolor=self.tema_actual["bg_entry"],
            activebackground=self.tema_actual["bg_header"],
            activeforeground=self.tema_actual["warning"],
            command=self._on_toggle_demo
        )
        self.chk_demo.pack(side="left", padx=3)

        self.lbl_ip_tag = tk.Label(frame_ip, text="IP:", font=("Segoe UI", 8, "bold"), fg=self.tema_actual["fg_dim"], bg=self.tema_actual["bg_header"])
        self.lbl_ip_tag.pack(side="left", padx=2)
        self.entry_ip = tk.Entry(frame_ip, font=("Segoe UI", 8), width=11, bg=self.tema_actual["bg_entry"], fg=self.tema_actual["fg_text"], insertbackground=self.tema_actual["accent_primary"])
        self.entry_ip.insert(0, "192.168.4.1")
        self.entry_ip.pack(side="left", padx=3)

        self.btn_ping = tk.Button(
            frame_ip,
            text="Ping",
            font=("Segoe UI", 7, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg=self.tema_actual["accent_primary"],
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.probar_conexion_manual
        )
        self.btn_ping.pack(side="left", padx=2)

        # Indicador animado de estado de conexión (B1)
        self.frame_status_badge = tk.Frame(frame_ip, bg=self.tema_actual["bg_header"])
        self.frame_status_badge.pack(side="left", padx=4)

        self.canvas_heartbeat = tk.Canvas(self.frame_status_badge, width=14, height=14, bg=self.tema_actual["bg_header"], highlightthickness=0)
        self.canvas_heartbeat.pack(side="left", padx=2)

        self.lbl_status = tk.Label(
            self.frame_status_badge,
            text="DESCONECTADO",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema_actual["danger"],
            bg=self.tema_actual["bg_header"],
        )
        self.lbl_status.pack(side="left", padx=2)

        # Micro-LEDs de actividad de enlace RX (verde esmeralda) y TX (azul cian)
        self.frame_rxtx = tk.Frame(frame_ip, bg=self.tema_actual["bg_card_inner"], bd=1, relief="solid", highlightthickness=1, highlightbackground=self.tema_actual["border"], padx=5, pady=2)
        self.frame_rxtx.pack(side="left", padx=(6, 2))

        self.lbl_rx = tk.Label(self.frame_rxtx, text="RX", font=("Segoe UI", 6, "bold"), fg=self.tema_actual["fg_dim"], bg=self.tema_actual["bg_card_inner"])
        self.lbl_rx.pack(side="left", padx=(1, 2))
        self.canvas_rx = tk.Canvas(self.frame_rxtx, width=10, height=10, bg=self.tema_actual["bg_card_inner"], highlightthickness=0)
        self.canvas_rx.pack(side="left", padx=(0, 3))
        self._led_rx = self.canvas_rx.create_oval(1, 1, 9, 9, fill=self.tema_actual["bg_panel"], outline="#475569")

        self.lbl_tx = tk.Label(self.frame_rxtx, text="TX", font=("Segoe UI", 6, "bold"), fg=self.tema_actual["fg_dim"], bg=self.tema_actual["bg_card_inner"])
        self.lbl_tx.pack(side="left", padx=(2, 2))
        self.canvas_tx = tk.Canvas(self.frame_rxtx, width=10, height=10, bg=self.tema_actual["bg_card_inner"], highlightthickness=0)
        self.canvas_tx.pack(side="left", padx=(0, 1))
        self._led_tx = self.canvas_tx.create_oval(1, 1, 9, 9, fill=self.tema_actual["bg_panel"], outline="#475569")

        # 2. CUERPO PRINCIPAL DIVIDIDO EN 2 COLUMNAS CON DESPLAZAMIENTO FLUIDO (SCROLLBAR)
        self.body_scroll = ScrollableFrame(self.root, bg=self.tema_actual["bg_app"], fit_width=True, scroll_x=True)
        self.body_scroll.pack(fill="both", expand=True, padx=4, pady=2)
        self.body_frame = self.body_scroll.content
        body = self.body_frame

        # =========================================================================
        # COLUMNA IZQUIERDA: GESTOR DE MATRIZ DE ENSAYOS & TEMPORIZADOR DE ETAPAS
        # =========================================================================
        self.panel_recetas = tk.Frame(body, bg=self.tema_actual["bg_panel"], width=360, bd=1, relief="solid")
        self.panel_recetas.pack(side="left", fill="y", padx=4, pady=2)
        panel_recetas = self.panel_recetas

        self.lbl_sec_rec = tk.Label(
            panel_recetas,
            text="GESTOR DE RECETAS (ISA-88)",
            font=("Segoe UI", 10, "bold"),
            fg=self.tema_actual["accent_primary"],
            bg=self.tema_actual["bg_panel"]
        )
        self.lbl_sec_rec.pack(anchor="w", padx=10, pady=(8, 2))

        self.frame_xl = tk.Frame(panel_recetas, bg=self.tema_actual["bg_panel"])
        self.frame_xl.pack(fill="x", padx=8, pady=2)
        frame_xl = self.frame_xl

        self.lbl_xl_info = tk.Label(
            frame_xl,
            text=f"{len(self.lista_placas)} placas cargadas",
            font=("Segoe UI", 7),
            fg=self.tema_actual["fg_muted"],
            bg=self.tema_actual["bg_panel"],
            anchor="w"
        )
        self.lbl_xl_info.pack(side="left", fill="x", expand=True)

        self.btn_load_xl = tk.Button(
            frame_xl,
            text="Abrir Excel",
            font=("Segoe UI", 7, "bold"),
            bg=self.tema_actual["btn_acc_bg"],
            fg=self.tema_actual["btn_acc_fg"],
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.cargar_archivo_excel
        )
        self.btn_load_xl.pack(side="right")

        self.lbl_filt = tk.Label(
            panel_recetas,
            text="Filtro por Condición de Baño:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema_actual["fg_dim"],
            bg=self.tema_actual["bg_panel"]
        )
        self.lbl_filt.pack(anchor="w", padx=10, pady=(6, 2))

        self.frame_filtros = tk.Frame(panel_recetas, bg=self.tema_actual["bg_panel"])
        self.frame_filtros.pack(fill="x", padx=8, pady=1)
        frame_filtros = self.frame_filtros

        self.btn_f_all = self._crear_btn_filtro(frame_filtros, "Todos", "TODOS", 0, 0)
        self.btn_f_p2_25 = self._crear_btn_filtro(frame_filtros, "pH 2 • 25°C", "pH 2 — 25°C", 0, 1)
        self.btn_f_p2_40 = self._crear_btn_filtro(frame_filtros, "pH 2 • 40°C", "pH 2 — 40°C", 0, 2)
        self.btn_f_p4_25 = self._crear_btn_filtro(frame_filtros, "pH 4 • 25°C", "pH 4 — 25°C", 1, 0)
        self.btn_f_p4_40 = self._crear_btn_filtro(frame_filtros, "pH 4 • 40°C", "pH 4 — 40°C", 1, 1)
        self._btn_filtros = [self.btn_f_all, self.btn_f_p2_25, self.btn_f_p2_40, self.btn_f_p4_25, self.btn_f_p4_40]

        self.lbl_sel_placa = tk.Label(
            panel_recetas,
            text="Seleccionar Placa a Ejecutar:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema_actual["fg_dim"],
            bg=self.tema_actual["bg_panel"]
        )
        self.lbl_sel_placa.pack(anchor="w", padx=10, pady=(8, 2))

        self.combo_placas = ttk.Combobox(panel_recetas, font=("Segoe UI", 8), state="readonly")
        self.combo_placas.pack(fill="x", padx=10, pady=2)
        self.combo_placas.bind("<<ComboboxSelected>>", self._on_placa_seleccionada)

        self.frame_badges = tk.Frame(panel_recetas, bg="#1e293b", bd=0, padx=6, pady=4)
        self.frame_badges.pack(fill="x", padx=8, pady=4)

        self.lbl_badge_ronda = tk.Label(self.frame_badges, text="Ronda: --", font=("Segoe UI", 7, "bold"), fg=self.tema_actual["accent_primary"], bg="#1e293b")
        self.lbl_badge_ronda.pack(anchor="w")

        self.lbl_badge_cond = tk.Label(self.frame_badges, text="Baño: pH -- | -- °C", font=("Segoe UI", 7, "bold"), fg="#34d399", bg="#1e293b")
        self.lbl_badge_cond.pack(anchor="w")

        self.lbl_badge_zin = tk.Label(self.frame_badges, text="Zincado: --", font=("Segoe UI", 7, "bold"), fg="#f472b6", bg="#1e293b")
        self.lbl_badge_zin.pack(anchor="w")

        self.lbl_badge_niq = tk.Label(self.frame_badges, text="Níquel: DC 1.13 A (600s)", font=("Segoe UI", 7, "bold"), fg="#a78bfa", bg="#1e293b")
        self.lbl_badge_niq.pack(anchor="w")

        self.lbl_sec = tk.Label(
            panel_recetas,
            text="Secuencia de Etapas:",
            font=("Segoe UI", 8, "bold"),
            fg=self.tema_actual["fg_dim"],
            bg=self.tema_actual["bg_panel"]
        )
        self.lbl_sec.pack(anchor="w", padx=10, pady=(6, 2))

        self.frame_etapas = tk.Frame(panel_recetas, bg=self.tema_actual["bg_panel"])
        self.frame_etapas.pack(fill="x", padx=8, pady=2)

        self.lbl_e1 = self._crear_fila_etapa(self.frame_etapas, 1, "Limpieza Electrolítica (T1)", "240s @ 85°C | 0.00A")
        self.lbl_e2 = self._crear_fila_etapa(self.frame_etapas, 2, "Decapado Ácido (T2)", "120s @ 85°C | 0.00A")
        self.lbl_e3 = self._crear_fila_etapa(self.frame_etapas, 3, "Zincado (T3)", "120s @ 25°C | 1.50A")
        self.lbl_e4 = self._crear_fila_etapa(self.frame_etapas, 4, "Niquelado Watts (T4)", "600s @ 30°C | 1.13A DC (pH 5.5)")

        self.frame_clock_box = tk.Frame(panel_recetas, bg=self.tema_actual["bg_card_inner"], bd=0, padx=6, pady=6)
        self.frame_clock_box.pack(fill="x", padx=8, pady=6)
        frame_clock_box = self.frame_clock_box

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
            font=("Consolas", 28, "bold"),
            fg=self.tema_actual["accent_primary"],
            bg="#1e293b"
        )
        self.lbl_timer_big.pack(pady=1)

        # Canvas con gradiente y marcadores de cuartos (B3)
        self.canvas_prog_etapa = tk.Canvas(frame_clock_box, height=18, bg=self.tema_actual["bg_panel"], bd=0, highlightthickness=1, highlightbackground="#334155")
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

        self.frame_stage_btns = tk.Frame(panel_recetas, bg=self.tema_actual["bg_panel"])
        self.frame_stage_btns.pack(fill="x", padx=8, pady=3)
        frame_stage_btns = self.frame_stage_btns

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
        self.frame_hw_box = tk.Frame(panel_recetas, bg=self.tema_actual["bg_card_inner"], bd=0, padx=6, pady=5)
        self.frame_hw_box.pack(fill="x", padx=8, pady=3)
        frame_hw_box = self.frame_hw_box

        self.var_auto_sync_hw = tk.BooleanVar(value=True)
        self.chk_auto_sp = tk.Checkbutton(
            frame_hw_box,
            text="Auto-enviar SPs al iniciar etapa",
            variable=self.var_auto_sync_hw,
            font=("Segoe UI", 7, "bold"),
            fg=self.tema_actual["info"],
            bg=self.tema_actual["bg_card_inner"],
            selectcolor=self.tema_actual["bg_entry"],
            activebackground=self.tema_actual["bg_card_inner"],
            activeforeground=self.tema_actual["info"]
        )
        self.chk_auto_sp.pack(anchor="w")

        self.frame_hw_actions = tk.Frame(frame_hw_box, bg=self.tema_actual["bg_card_inner"])
        self.frame_hw_actions.pack(fill="x", pady=2)
        frame_hw_actions = self.frame_hw_actions

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

        self.frame_stab = tk.Frame(panel_recetas, bg=self.tema_actual["bg_card_inner"], bd=0, padx=6, pady=4)
        self.frame_stab.pack(fill="x", padx=8, pady=(4, 8))
        frame_stab = self.frame_stab

        self.lbl_stab_title = tk.Label(
            frame_stab,
            text="Estabilidad de Corriente (ADS1115):",
            font=("Segoe UI", 7, "bold"),
            fg=self.tema_actual["fg_dim"],
            bg=self.tema_actual["bg_card_inner"]
        )
        self.lbl_stab_title.pack(anchor="w")

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
        self.panel_telemetria = tk.Frame(body, bg=self.tema_actual["bg_app"])
        self.panel_telemetria.pack(side="left", fill="both", expand=True, padx=4, pady=0)
        panel_telemetria = self.panel_telemetria

        self.ctrl_frame = tk.Frame(panel_telemetria, bg=self.tema_actual["bg_panel"], bd=0)
        self.ctrl_frame.pack(fill="x", padx=4, pady=2)
        ctrl_frame = self.ctrl_frame

        self.btn_frame = tk.Frame(ctrl_frame, bg=self.tema_actual["bg_panel"])
        self.btn_frame.pack(side="left", padx=8, pady=6)
        btn_frame = self.btn_frame

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

        self.kpi_frame = tk.Frame(ctrl_frame, bg=self.tema_actual["bg_panel"])
        self.kpi_frame.pack(side="right", padx=10, pady=6)
        kpi_frame = self.kpi_frame

        self.lbl_time = tk.Label(kpi_frame, text="Tiempo: 00:00", font=("Consolas", 9, "bold"), fg=self.tema_actual["accent_primary"], bg="#1e293b")
        self.lbl_time.pack(side="left", padx=8)

        self.lbl_samples = tk.Label(kpi_frame, text="Muestras: 0", font=("Segoe UI", 9, "bold"), fg="#a78bfa", bg="#1e293b")
        self.lbl_samples.pack(side="left", padx=8)

        self.lbl_incidentes = tk.Label(
            kpi_frame,
            text="INCIDENTES: 0",
            font=("Segoe UI", 9, "bold"),
            fg="#22c55e",
            bg="#1e293b",
            cursor="hand2"
        )
        self.lbl_incidentes.pack(side="left", padx=8)
        self.lbl_incidentes.bind("<Button-1>", lambda e: self.abrir_ventana_diagnostico())

        # 2. Tarjetas Rápidas de Sensores en Vivo con Indicadores de Gate TRIAC
        self.cards_bar = tk.Frame(panel_telemetria, bg=self.tema_actual["bg_app"])
        self.cards_bar.pack(fill="x", padx=2, pady=2)
        cards_bar = self.cards_bar

        self.card_t1 = self._crear_card_tina(cards_bar, "T1: Limpieza", 450.0, "#d95f02", canal_idx=0)
        self.card_t2 = self._crear_card_tina(cards_bar, "T2: Decapado", 450.0, "#e6ab02", canal_idx=1)
        self.card_t3 = self._crear_card_tina(cards_bar, "T3: Celda Hull", 18.0, self.tema_actual["accent_primary"], canal_idx=2)
        self.card_t4 = self._crear_card_tina(cards_bar, "T4: Níquel", 450.0, "#a78bfa", canal_idx=3)
        self.card_coulomb = self._crear_kpi_box(cards_bar, "Carga Q (Coulombs)", "0.0 C", "#f472b6", click_cmd=self.abrir_ventana_faraday)
        self.card_amp = self._crear_kpi_box(cards_bar, "Corriente (VCSS)", "0.00 A", "#22c55e", click_cmd=lambda: self.abrir_ventana_actuadores(4))
        self.card_ph = self._crear_kpi_box(cards_bar, "Sensor pH (A1)", "-- pH", "#c084fc", click_cmd=self.abrir_ventana_ph)
        self.card_env = self._crear_kpi_box(cards_bar, "Ambiente", "-- °C", "#94a3b8")

        # 3. Área de Gráficas en Acordeón Colapsable (Estilo Monitor de Recursos)
        self.plot_frame = tk.Frame(panel_telemetria, bg=self.tema_actual["bg_app"])
        self.plot_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Estados de visibilidad de acordeones
        self.plot_t_visible = True
        self.plot_u_visible = True
        self.plot_i_visible = True

        # --- Acordeón 1: Térmico (T1..T4) ---
        self.card_acc_t = tk.Frame(self.plot_frame, bg=self.tema_actual["border"], bd=1, relief="solid")
        self.card_acc_t.pack(fill="both", expand=True, pady=1)

        self.hdr_acc_t = tk.Frame(self.card_acc_t, bg=self.tema_actual["bg_acc_hdr"], height=26, cursor="hand2")
        self.hdr_acc_t.pack(fill="x")
        self.hdr_acc_t.pack_propagate(False)

        self.lbl_acc_t_title = tk.Label(self.hdr_acc_t, text="TEMPERATURA DE TINAS (T1..T4)", font=("Segoe UI", 8, "bold"), fg=self.tema_actual["fg_acc_title"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_t_title.pack(side="left", padx=8, pady=2)

        self.btn_acc_t = tk.Button(self.hdr_acc_t, text="▲", font=("Segoe UI", 7, "bold"), bg=self.tema_actual["btn_acc_bg"], fg=self.tema_actual["btn_acc_fg"], bd=0, padx=8, pady=1, cursor="hand2", command=self.toggle_acordeon_t)
        self.btn_acc_t.pack(side="right", padx=6, pady=2)

        self.lbl_acc_t_badge = tk.Label(self.hdr_acc_t, text="T1: -- °C | T2: -- °C | T3: -- °C | T4: -- °C", font=("Segoe UI", 7, "bold"), fg=self.tema_actual["fg_acc_badge"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_t_badge.pack(side="right", padx=(0, 10), pady=2)

        for w in (self.hdr_acc_t, self.lbl_acc_t_title, self.lbl_acc_t_badge):
            w.bind("<Button-1>", lambda e: self.toggle_acordeon_t())

        self.body_acc_t = tk.Frame(self.card_acc_t, bg=self.tema_actual["plot_bg"])
        self.body_acc_t.pack(fill="both", expand=True)

        self.fig_t = Figure(figsize=(8.5, 1.8), dpi=100, facecolor=self.tema_actual["plot_bg"])
        self.ax1 = self.fig_t.add_subplot(1, 1, 1)
        self.canvas_t = FigureCanvasTkAgg(self.fig_t, master=self.body_acc_t)
        self.canvas_t.get_tk_widget().pack(fill="both", expand=True)

        # --- Acordeón 2: TRIACs (%) ---
        self.card_acc_u = tk.Frame(self.plot_frame, bg=self.tema_actual["border"], bd=1, relief="solid")
        self.card_acc_u.pack(fill="both", expand=True, pady=1)

        self.hdr_acc_u = tk.Frame(self.card_acc_u, bg=self.tema_actual["bg_acc_hdr"], height=26, cursor="hand2")
        self.hdr_acc_u.pack(fill="x")
        self.hdr_acc_u.pack_propagate(False)

        self.lbl_acc_u_title = tk.Label(self.hdr_acc_u, text="CONDUCCIÓN DE TRIACS (%)", font=("Segoe UI", 8, "bold"), fg=self.tema_actual["fg_acc_title"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_u_title.pack(side="left", padx=8, pady=2)

        self.btn_acc_u = tk.Button(self.hdr_acc_u, text="▲", font=("Segoe UI", 7, "bold"), bg=self.tema_actual["btn_acc_bg"], fg=self.tema_actual["btn_acc_fg"], bd=0, padx=8, pady=1, cursor="hand2", command=self.toggle_acordeon_u)
        self.btn_acc_u.pack(side="right", padx=6, pady=2)

        self.lbl_acc_u_badge = tk.Label(self.hdr_acc_u, text="Gate: T1 0% | T2 0% | T3 0% | T4 0%", font=("Segoe UI", 7, "bold"), fg=self.tema_actual["fg_acc_badge"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_u_badge.pack(side="right", padx=(0, 10), pady=2)

        for w in (self.hdr_acc_u, self.lbl_acc_u_title, self.lbl_acc_u_badge):
            w.bind("<Button-1>", lambda e: self.toggle_acordeon_u())

        self.body_acc_u = tk.Frame(self.card_acc_u, bg=self.tema_actual["plot_bg"])
        self.body_acc_u.pack(fill="both", expand=True)

        self.fig_u = Figure(figsize=(8.5, 1.8), dpi=100, facecolor=self.tema_actual["plot_bg"])
        self.ax2 = self.fig_u.add_subplot(1, 1, 1)
        self.canvas_u = FigureCanvasTkAgg(self.fig_u, master=self.body_acc_u)
        self.canvas_u.get_tk_widget().pack(fill="both", expand=True)

        # --- Acordeón 3: Corriente VCSS ---
        self.card_acc_i = tk.Frame(self.plot_frame, bg=self.tema_actual["border"], bd=1, relief="solid")
        self.card_acc_i.pack(fill="both", expand=True, pady=1)

        self.hdr_acc_i = tk.Frame(self.card_acc_i, bg=self.tema_actual["bg_acc_hdr"], height=26, cursor="hand2")
        self.hdr_acc_i.pack(fill="x")
        self.hdr_acc_i.pack_propagate(False)

        self.lbl_acc_i_title = tk.Label(self.hdr_acc_i, text="CORRIENTE VCSS (A) & BANDA OBJETIVO", font=("Segoe UI", 8, "bold"), fg=self.tema_actual["fg_acc_title"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_i_title.pack(side="left", padx=8, pady=2)

        self.btn_acc_i = tk.Button(self.hdr_acc_i, text="▲", font=("Segoe UI", 7, "bold"), bg=self.tema_actual["btn_acc_bg"], fg=self.tema_actual["btn_acc_fg"], bd=0, padx=8, pady=1, cursor="hand2", command=self.toggle_acordeon_i)
        self.btn_acc_i.pack(side="right", padx=6, pady=2)

        self.lbl_acc_i_badge = tk.Label(self.hdr_acc_i, text="I: 0.00 A | Obj: -- A | Q: 0.0 C", font=("Segoe UI", 7, "bold"), fg=self.tema_actual["fg_acc_badge"], bg=self.tema_actual["bg_acc_hdr"], cursor="hand2")
        self.lbl_acc_i_badge.pack(side="right", padx=(0, 10), pady=2)

        for w in (self.hdr_acc_i, self.lbl_acc_i_title, self.lbl_acc_i_badge):
            w.bind("<Button-1>", lambda e: self.toggle_acordeon_i())

        self.body_acc_i = tk.Frame(self.card_acc_i, bg=self.tema_actual["plot_bg"])
        self.body_acc_i.pack(fill="both", expand=True)

        self.fig_i = Figure(figsize=(8.5, 1.8), dpi=100, facecolor=self.tema_actual["plot_bg"])
        self.ax3 = self.fig_i.add_subplot(1, 1, 1)
        self.canvas_i = FigureCanvasTkAgg(self.fig_i, master=self.body_acc_i)
        self.canvas_i.get_tk_widget().pack(fill="both", expand=True)

        self._estilizar_axes()

        # 4. Footer con información de archivo y anotaciones
        self.lbl_csv_info = tk.Label(
            self.root,
            text="Listo para iniciar. Los ensayos se guardarán en subcarpetas dentro de: telemetria/experimentos/",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg=self.tema_actual["bg_app"],
            anchor="w",
            padx=14,
            pady=3
        )
        self.lbl_csv_info.pack(fill="x", side="bottom")

        self._actualizar_lista_combo()
        self.aplicar_tema_global(self.tema_actual)


    def abrir_ventana_actuadores(self, canal_idx=0):
        if self.win_actuadores is not None:
            try:
                if hasattr(self.win_actuadores, 'win') and self.win_actuadores.win.winfo_exists():
                    if canal_idx is not None and canal_idx <= 5:
                        self.win_actuadores._seleccionar_canal(canal_idx)
                    self.win_actuadores.win.deiconify()
                    self.win_actuadores.win.lift()
                    self.win_actuadores.win.focus_force()
                    return
            except Exception:
                self.win_actuadores = None

        try:
            self.win_actuadores = VentanaActuadores(self, canal_inicial=canal_idx)
        except Exception:
            self.win_actuadores = None
            raise


    def abrir_ventana_errores(self):
        if self.win_errores is not None:
            try:
                if hasattr(self.win_errores, 'win') and self.win_errores.win.winfo_exists():
                    self.win_errores.win.deiconify()
                    self.win_errores.win.lift()
                    self.win_errores.win.focus_force()
                    return
            except Exception:
                self.win_errores = None

        try:
            self.win_errores = VentanaErrores(self)
        except Exception:
            self.win_errores = None
            raise


    def abrir_ventana_faraday(self):
        if self.win_faraday is not None:
            try:
                if hasattr(self.win_faraday, 'win') and self.win_faraday.win.winfo_exists():
                    self.win_faraday.win.deiconify()
                    self.win_faraday.win.lift()
                    self.win_faraday.win.focus_force()
                    return
            except Exception:
                self.win_faraday = None

        try:
            self.win_faraday = VentanaFaraday(self)
        except Exception:
            self.win_faraday = None
            raise


    def abrir_ventana_diagnostico(self):
        if self.win_diag is not None:
            try:
                if hasattr(self.win_diag, 'win') and self.win_diag.win.winfo_exists():
                    self.win_diag.win.deiconify()
                    self.win_diag.win.lift()
                    self.win_diag.win.focus_force()
                    return
            except Exception:
                self.win_diag = None

        try:
            self.win_diag = VentanaDiagnostico(self)
        except Exception:
            self.win_diag = None
            raise


    def abrir_ventana_ph(self):
        if self.win_ph is not None:
            try:
                if hasattr(self.win_ph, 'win') and self.win_ph.win.winfo_exists():
                    self.win_ph.win.deiconify()
                    self.win_ph.win.lift()
                    self.win_ph.win.focus_force()
                    return
            except Exception:
                self.win_ph = None

        try:
            self.win_ph = VentanaPH(self)
        except Exception:
            self.win_ph = None
            raise


    def abrir_ventana_nube(self):
        if self.win_nube is not None:
            try:
                if hasattr(self.win_nube, 'win') and self.win_nube.win.winfo_exists():
                    self.win_nube.win.deiconify()
                    self.win_nube.win.lift()
                    self.win_nube.win.focus_force()
                    return
            except Exception:
                self.win_nube = None

        try:
            self.win_nube = VentanaNube(self)
        except Exception:
            self.win_nube = None
            raise


    def abrir_ventana_visor_datos(self):
        if self.win_visor is not None:
            try:
                if hasattr(self.win_visor, 'win') and self.win_visor.win.winfo_exists():
                    self.win_visor.win.deiconify()
                    self.win_visor.win.lift()
                    self.win_visor.win.focus_force()
                    return
            except Exception:
                self.win_visor = None

        try:
            self.win_visor = VentanaVisorDatos(self)
        except Exception:
            self.win_visor = None
            raise


    def toggle_acordeon_t(self):
        self.plot_t_visible = not self.plot_t_visible
        if self.plot_t_visible:
            self.body_acc_t.pack(fill="both", expand=True)
            self.btn_acc_t.config(text="▲")
            self.card_acc_t.pack_configure(expand=True)
        else:
            self.body_acc_t.pack_forget()
            self.btn_acc_t.config(text="▼")
            self.card_acc_t.pack_configure(expand=False)
        self._redibujar_grafica_vivo()


    def toggle_acordeon_u(self):
        self.plot_u_visible = not self.plot_u_visible
        if self.plot_u_visible:
            self.body_acc_u.pack(fill="both", expand=True)
            self.btn_acc_u.config(text="▲")
            self.card_acc_u.pack_configure(expand=True)
        else:
            self.body_acc_u.pack_forget()
            self.btn_acc_u.config(text="▼")
            self.card_acc_u.pack_configure(expand=False)
        self._redibujar_grafica_vivo()


    def toggle_acordeon_i(self):
        self.plot_i_visible = not self.plot_i_visible
        if self.plot_i_visible:
            self.body_acc_i.pack(fill="both", expand=True)
            self.btn_acc_i.config(text="▲")
            self.card_acc_i.pack_configure(expand=True)
        else:
            self.body_acc_i.pack_forget()
            self.btn_acc_i.config(text="▼")
            self.card_acc_i.pack_configure(expand=False)
        self._redibujar_grafica_vivo()


    def toggle_colapso_graficas(self, colapsar=None):
        """Colapsa o expande todos los acordeones simultáneamente."""
        if colapsar is None:
            colapsar = (self.plot_t_visible or self.plot_u_visible or self.plot_i_visible)

        nuevo_estado = not colapsar
        self.plot_t_visible = nuevo_estado
        self.plot_u_visible = nuevo_estado
        self.plot_i_visible = nuevo_estado

        for (vis, body, btn, card) in [
            (nuevo_estado, getattr(self, 'body_acc_t', None), getattr(self, 'btn_acc_t', None), getattr(self, 'card_acc_t', None)),
            (nuevo_estado, getattr(self, 'body_acc_u', None), getattr(self, 'btn_acc_u', None), getattr(self, 'card_acc_u', None)),
            (nuevo_estado, getattr(self, 'body_acc_i', None), getattr(self, 'btn_acc_i', None), getattr(self, 'card_acc_i', None)),
        ]:
            if not body or not btn or not card:
                continue
            if vis:
                body.pack(fill="both", expand=True)
                btn.config(text="▲")
                card.pack_configure(expand=True)
            else:
                body.pack_forget()
                btn.config(text="▼")
                card.pack_configure(expand=False)
        self._redibujar_grafica_vivo()


    def toggle_tema_dia_noche(self):
        if self.tema_actual["nombre"] == "noche":
            self.tema_actual = TEMA_DIA
            guardar_tema_preferido("dia")
            self.btn_tema.config(text="MODO NOCHE")
        else:
            self.tema_actual = TEMA_NOCHE
            guardar_tema_preferido("noche")
            self.btn_tema.config(text="MODO DÍA")

        self.aplicar_tema_global(self.tema_actual)


    def aplicar_tema_global(self, tema):
        """Aplica la paleta temática en caliente a absolutamente todos los componentes de la interfaz."""
        is_day = (tema.get("nombre") == "dia")

        # 1. Ventana Raíz y Layout Principal
        self.root.configure(bg=tema["bg_app"])

        if hasattr(self, 'body_scroll') and self.body_scroll:
            self.body_scroll.aplicar_tema(tema)
        if hasattr(self, 'body_frame'):
            self.body_frame.configure(bg=tema["bg_app"])

        # 2. Barra Superior y Controles de Encabezado
        if hasattr(self, 'hdr_frame'):
            self.hdr_frame.configure(bg=tema["bg_header"])

        if hasattr(self, 'lbl_hdr_title') and self.lbl_hdr_title:
            self.lbl_hdr_title.configure(bg=tema["bg_header"], fg=tema["fg_text"] if is_day else tema["accent_primary"])

        # Unificación de botonera superior de navegación (sin arcoíris caótico)
        nav_bg = "#292524" if is_day else "#181a20"
        nav_fg = "#f5f5f4" if is_day else "#e2e8f0"
        nav_active_bg = "#44403c" if is_day else "#252833"
        nav_active_fg = "#ffffff"

        for b, _, _ in getattr(self, '_nav_btn_definitions', []):
            b.configure(
                bg=nav_bg,
                fg=nav_fg,
                activebackground=nav_active_bg,
                activeforeground=nav_active_fg
            )

        if hasattr(self, 'btn_tema'):
            self.btn_tema.configure(
                bg=nav_bg,
                fg=nav_fg,
                activebackground=nav_active_bg,
                activeforeground=nav_active_fg
            )

        if hasattr(self, 'frame_ip'):
            self.frame_ip.configure(bg=tema["bg_header"])
        if hasattr(self, 'chk_demo'):
            self.chk_demo.configure(bg=tema["bg_header"], fg=tema["warning"], selectcolor=tema["bg_entry"], activebackground=tema["bg_header"], activeforeground=tema["warning"])
        if hasattr(self, 'lbl_ip_tag'):
            self.lbl_ip_tag.configure(bg=tema["bg_header"], fg=tema["fg_dim"])
        if hasattr(self, 'entry_ip'):
            self.entry_ip.configure(bg=tema["bg_entry"], fg=tema["fg_text"], insertbackground=tema["accent_primary"])
        if hasattr(self, 'btn_ping'):
            self.btn_ping.configure(bg=tema["btn_acc_bg"], fg=tema["accent_primary"])
        if hasattr(self, 'frame_status_badge'):
            self.frame_status_badge.configure(bg=tema["bg_header"])
        if hasattr(self, 'canvas_heartbeat'):
            self.canvas_heartbeat.configure(bg=tema["bg_header"])
        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(bg=tema["bg_header"])
        if hasattr(self, 'frame_rxtx'):
            self.frame_rxtx.configure(bg=tema["bg_card_inner"], highlightbackground=tema["border"])
        if hasattr(self, 'lbl_rx'):
            self.lbl_rx.configure(bg=tema["bg_card_inner"], fg=tema["fg_dim"])
        if hasattr(self, 'canvas_rx'):
            self.canvas_rx.configure(bg=tema["bg_card_inner"])
        if hasattr(self, 'lbl_tx'):
            self.lbl_tx.configure(bg=tema["bg_card_inner"], fg=tema["fg_dim"])
        if hasattr(self, 'canvas_tx'):
            self.canvas_tx.configure(bg=tema["bg_card_inner"])

        # 3. Columna Izquierda: Panel de Recetas (ISA-88) y Secuenciador
        if hasattr(self, 'panel_recetas'):
            self.panel_recetas.configure(bg=tema["bg_panel"])

        if hasattr(self, 'lbl_sec_rec') and self.lbl_sec_rec:
            self.lbl_sec_rec.configure(bg=tema["bg_panel"], fg=tema["accent_primary"])
        if hasattr(self, 'frame_xl') and self.frame_xl:
            self.frame_xl.configure(bg=tema["bg_panel"])
        if hasattr(self, 'lbl_xl_info') and self.lbl_xl_info:
            self.lbl_xl_info.configure(bg=tema["bg_panel"], fg=tema["fg_muted"])
        if hasattr(self, 'btn_load_xl') and self.btn_load_xl:
            self.btn_load_xl.configure(bg=tema["btn_acc_bg"], fg=tema["btn_acc_fg"])

        if hasattr(self, 'lbl_filt') and self.lbl_filt:
            self.lbl_filt.configure(bg=tema["bg_panel"], fg=tema["fg_dim"])
        if hasattr(self, 'frame_filtros') and self.frame_filtros:
            self.frame_filtros.configure(bg=tema["bg_panel"])
        if hasattr(self, '_aplicar_filtro'):
            self._aplicar_filtro(getattr(self, 'filtro_actual', 'TODOS'))

        if hasattr(self, 'lbl_sel_placa') and self.lbl_sel_placa:
            self.lbl_sel_placa.configure(bg=tema["bg_panel"], fg=tema["fg_dim"])

        if hasattr(self, 'frame_badges') and self.frame_badges:
            self.frame_badges.configure(bg=tema["bg_card_inner"])
            for child in self.frame_badges.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=tema["bg_card_inner"])

        if hasattr(self, 'lbl_sec') and self.lbl_sec:
            self.lbl_sec.configure(bg=tema["bg_panel"], fg=tema["fg_dim"])
        if hasattr(self, 'frame_etapas') and self.frame_etapas:
            self.frame_etapas.configure(bg=tema["bg_panel"])
            for row in self.frame_etapas.winfo_children():
                if isinstance(row, tk.Frame):
                    row.configure(bg=tema["bg_panel"])
                    for lbl in row.winfo_children():
                        if isinstance(lbl, tk.Label):
                            lbl.configure(bg=tema["bg_panel"])

        if hasattr(self, 'frame_clock_box') and self.frame_clock_box:
            self.frame_clock_box.configure(bg=tema["bg_card_inner"])
        if hasattr(self, 'lbl_etapa_titulo') and self.lbl_etapa_titulo:
            self.lbl_etapa_titulo.configure(bg=tema["bg_card_inner"], fg=tema["fg_dim"])
        if hasattr(self, 'lbl_timer_big') and self.lbl_timer_big:
            self.lbl_timer_big.configure(bg=tema["bg_card_inner"], fg=tema["accent_primary"])
        if hasattr(self, 'canvas_prog_etapa') and self.canvas_prog_etapa:
            self.canvas_prog_etapa.configure(bg=tema["bg_entry"], highlightbackground=tema["border"])
            self._dibujar_progreso_canvas(getattr(self, '_ultimo_prog_pct', 0))
        if hasattr(self, 'lbl_aviso_etapa') and self.lbl_aviso_etapa:
            self.lbl_aviso_etapa.configure(bg=tema["bg_card_inner"], fg=tema["fg_muted"])

        if hasattr(self, 'frame_stage_btns') and self.frame_stage_btns:
            self.frame_stage_btns.configure(bg=tema["bg_panel"])
        if hasattr(self, 'btn_stage_prev') and self.btn_stage_prev:
            self.btn_stage_prev.configure(bg="#dedbd4" if is_day else "#1e2027", fg="#1c1917" if is_day else "#cbd5e1", relief="solid" if is_day else "flat", bd=1 if is_day else 0)
        if hasattr(self, 'btn_stage_toggle') and self.btn_stage_toggle:
            if getattr(self, 'etapa_corriendo', False):
                self.btn_stage_toggle.configure(bg=tema["warning"], fg="#ffffff")
            else:
                self.btn_stage_toggle.configure(bg=tema["success"], fg="#ffffff")
        if hasattr(self, 'btn_stage_next') and self.btn_stage_next:
            self.btn_stage_next.configure(bg=tema["accent_primary"], fg="#ffffff")
        if hasattr(self, 'btn_stage_reset') and self.btn_stage_reset:
            self.btn_stage_reset.configure(bg="#dedbd4" if is_day else "#1e2027", fg="#1c1917" if is_day else "#cbd5e1", relief="solid" if is_day else "flat", bd=1 if is_day else 0)

        if hasattr(self, 'frame_hw_box') and self.frame_hw_box:
            self.frame_hw_box.configure(bg=tema["bg_card_inner"])
        if hasattr(self, 'chk_auto_sp') and self.chk_auto_sp:
            self.chk_auto_sp.configure(bg=tema["bg_card_inner"], fg=tema["fg_text"] if is_day else tema["info"], selectcolor=tema["bg_entry"], activebackground=tema["bg_card_inner"])
        if hasattr(self, 'frame_hw_actions') and self.frame_hw_actions:
            self.frame_hw_actions.configure(bg=tema["bg_card_inner"])
        if hasattr(self, 'btn_send_sp') and self.btn_send_sp:
            self.btn_send_sp.configure(bg=tema["info"], fg="#ffffff")
        if hasattr(self, 'btn_test_alarm') and self.btn_test_alarm:
            self.btn_test_alarm.configure(bg="#fee2e2" if is_day else "#1e2027", fg=tema["danger"], relief="solid" if is_day else "flat", bd=1 if is_day else 0)
        if hasattr(self, 'lbl_hw_sync_status') and self.lbl_hw_sync_status:
            self.lbl_hw_sync_status.configure(bg=tema["bg_card_inner"], fg=tema["fg_muted"])

        if hasattr(self, 'frame_stab') and self.frame_stab:
            self.frame_stab.configure(bg=tema["bg_card_inner"])
        if hasattr(self, 'lbl_stab_title') and self.lbl_stab_title:
            self.lbl_stab_title.configure(bg=tema["bg_card_inner"], fg=tema["fg_dim"])
        if hasattr(self, 'lbl_stab_val') and self.lbl_stab_val:
            self.lbl_stab_val.configure(bg=tema["bg_card_inner"])

        # 4. Columna Derecha: Barra de Operación y Tarjetas Rápidas
        if hasattr(self, 'panel_telemetria'):
            self.panel_telemetria.configure(bg=tema["bg_app"])

        if hasattr(self, 'ctrl_frame'):
            self.ctrl_frame.configure(bg=tema["bg_panel"])
        if hasattr(self, 'btn_frame'):
            self.btn_frame.configure(bg=tema["bg_panel"])
        if hasattr(self, 'btn_folder'):
            self.btn_folder.configure(bg=tema["btn_acc_bg"], fg=tema["btn_acc_fg"])
        if hasattr(self, 'kpi_frame'):
            self.kpi_frame.configure(bg=tema["bg_panel"])
        if hasattr(self, 'lbl_time'):
            self.lbl_time.configure(bg=tema["bg_panel"], fg=tema["accent_primary"])
        if hasattr(self, 'lbl_samples'):
            self.lbl_samples.configure(bg=tema["bg_panel"], fg="#581c87" if is_day else "#a78bfa")
        if hasattr(self, 'lbl_incidentes'):
            self.lbl_incidentes.configure(bg=tema["bg_panel"])

        if hasattr(self, 'cards_bar'):
            self.cards_bar.configure(bg=tema["bg_app"])

        day_t_colors = ["#c2410c", "#b45309", "#0369a1", "#6d28d9"]
        night_t_colors = ["#fb923c", "#fbbf24", tema["accent_primary"], "#c084fc"]
        for i, card in enumerate(getattr(self, '_tina_cards', [])):
            card["frame"].configure(bg=tema["bg_card_inner"], highlightbackground=tema["border"])
            card["hdr_row"].configure(bg=tema["bg_card_inner"])
            card["hdr"].configure(bg=tema["bg_card_inner"], fg=tema["fg_text"])
            t_col = day_t_colors[i] if (is_day and i < len(day_t_colors)) else (night_t_colors[i] if i < len(night_t_colors) else tema["fg_text"])
            card["temp"].configure(bg=tema["bg_card_inner"], fg=t_col)
            card["default_color"] = t_col
            card["info_row"].configure(bg=tema["bg_card_inner"])
            card["gate"].configure(bg=tema["bg_card_inner"], fg=tema["fg_muted"])
            card["watts"].configure(bg=tema["bg_card_inner"], fg=tema["fg_muted"])
            if hasattr(card.get("trend"), "configure"):
                card["trend"].configure(bg=tema["success_bg"], fg=tema["success"])

        day_kpi_colors = ["#be185d", "#15803d", "#6b21a8", "#334155"]
        night_kpi_colors = ["#f472b6", "#34d399", "#c084fc", "#94a3b8"]
        for i, box in enumerate(getattr(self, '_kpi_boxes', [])):
            box.configure(bg=tema["bg_card_inner"], highlightbackground=tema["border"])
            if hasattr(box, '_lbl_t'):
                box._lbl_t.configure(bg=tema["bg_card_inner"], fg=tema["fg_dim"])
            if hasattr(box, '_lbl_v'):
                box._lbl_v.configure(bg=tema["bg_card_inner"])
                if i < len(day_kpi_colors):
                    box._lbl_v.configure(fg=day_kpi_colors[i] if is_day else night_kpi_colors[i])

        # 5. Barras de Acordeón de Gráficas (Estilo Perfmon)
        for card, hdr, lbl_t, lbl_b, btn in [
            (getattr(self, 'card_acc_t', None), getattr(self, 'hdr_acc_t', None), getattr(self, 'lbl_acc_t_title', None), getattr(self, 'lbl_acc_t_badge', None), getattr(self, 'btn_acc_t', None)),
            (getattr(self, 'card_acc_u', None), getattr(self, 'hdr_acc_u', None), getattr(self, 'lbl_acc_u_title', None), getattr(self, 'lbl_acc_u_badge', None), getattr(self, 'btn_acc_u', None)),
            (getattr(self, 'card_acc_i', None), getattr(self, 'hdr_acc_i', None), getattr(self, 'lbl_acc_i_title', None), getattr(self, 'lbl_acc_i_badge', None), getattr(self, 'btn_acc_i', None))
        ]:
            if card: card.configure(bg=tema["border"])
            if hdr: hdr.configure(bg=tema["bg_acc_hdr"])
            if lbl_t: lbl_t.configure(bg=tema["bg_acc_hdr"], fg=tema["fg_acc_title"])
            if lbl_b: lbl_b.configure(bg=tema["bg_acc_hdr"], fg=tema["fg_acc_badge"])
            if btn: btn.configure(bg=tema["btn_acc_bg"], fg=tema["btn_acc_fg"])

        for body in [getattr(self, 'body_acc_t', None), getattr(self, 'body_acc_u', None), getattr(self, 'body_acc_i', None)]:
            if body: body.configure(bg=tema["plot_bg"])

        if hasattr(self, 'plot_frame'):
            self.plot_frame.configure(bg=tema["bg_app"])

        # 6. Pie de Página
        if hasattr(self, 'lbl_csv_info'):
            self.lbl_csv_info.configure(bg=tema["bg_header"], fg=tema["fg_muted"])

        # 7. Sincronizar todas las ventanas modulares hijas si están abiertas
        for w_attr in ('win_visor', 'win_nube', 'win_ph', 'win_faraday', 'win_actuadores', 'win_errores', 'win_diag'):
            w = getattr(self, w_attr, None)
            if w and hasattr(w, 'win') and hasattr(w.win, 'winfo_exists') and w.win.winfo_exists():
                if hasattr(w, 'aplicar_tema'):
                    try:
                        w.aplicar_tema(tema)
                    except Exception:
                        pass

        # 8. Refrescar Estilos y Lienzos Matplotlib
        self._estilizar_axes()
        self._redibujar_grafica_vivo()
        if hasattr(self, '_cargar_etapa_actual') and getattr(self, 'placa_activa', None):
            self._cargar_etapa_actual()


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
        bg_card = self.tema_actual.get("bg_card_inner", "#131d31")
        border_col = self.tema_actual.get("border", "#27354f")
        fg_t = self.tema_actual.get("fg_dim", "#94a3b8")
        f = tk.Frame(parent, bg=bg_card, bd=1, relief="solid", highlightthickness=1, highlightbackground=border_col, padx=8, pady=4, cursor="hand2" if click_cmd else "arrow")
        f.pack(side="left", expand=True, fill="both", padx=2)
        lbl_t = tk.Label(f, text=title.upper(), font=("Segoe UI", 7, "bold"), fg=fg_t, bg=bg_card, cursor="hand2" if click_cmd else "arrow")
        lbl_t.pack(anchor="center")
        lbl_v = tk.Label(f, text=val_def, font=("Consolas", 13, "bold"), fg=color, bg=bg_card, cursor="hand2" if click_cmd else "arrow")
        lbl_v.pack(anchor="center", pady=(1, 0))
        if click_cmd:
            for w in (f, lbl_t, lbl_v):
                w.bind("<Button-1>", lambda e: click_cmd())
        f._lbl_t = lbl_t
        f._lbl_v = lbl_v
        if not hasattr(self, "_kpi_boxes"):
            self._kpi_boxes = []
        self._kpi_boxes.append(f)
        return lbl_v


    def _crear_card_tina(self, parent, title, max_w, color, canal_idx=0):
        bg_card = self.tema_actual.get("bg_card_inner", "#131d31")
        border_col = self.tema_actual.get("border", "#27354f")
        fg_hdr = self.tema_actual.get("fg_text", "#cbd5e1")
        fg_muted = self.tema_actual.get("fg_muted", "#64748b")

        f = tk.Frame(parent, bg=bg_card, bd=1, relief="solid", highlightthickness=1, highlightbackground=border_col, padx=6, pady=4, cursor="hand2")
        f.pack(side="left", expand=True, fill="both", padx=2)

        hdr_row = tk.Frame(f, bg=bg_card)
        hdr_row.pack(fill="x")
        lbl_h = tk.Label(hdr_row, text=f"{title}", font=("Segoe UI", 7, "bold"), fg=fg_hdr, bg=bg_card, cursor="hand2")
        lbl_h.pack(side="left")

        lbl_trend = tk.Label(
            hdr_row,
            text="ESTABLE",
            font=("Segoe UI", 6, "bold"),
            fg="#34d399",
            bg="#064e3b",
            padx=4,
            pady=0,
            cursor="hand2"
        )
        lbl_trend.pack(side="right")

        lbl_temp = tk.Label(f, text="-- °C / SP --°C", font=("Consolas", 12, "bold"), fg=color, bg=bg_card, cursor="hand2")
        lbl_temp.pack(anchor="w", pady=(1, 0))

        info_row = tk.Frame(f, bg=bg_card)
        info_row.pack(fill="x", pady=(1, 0))

        lbl_gate = tk.Label(info_row, text="Gate: 0%", font=("Segoe UI", 7), fg=fg_muted, bg=bg_card, cursor="hand2")
        lbl_gate.pack(side="left")

        lbl_w = tk.Label(info_row, text=f"0 W / {max_w:.0f}W", font=("Segoe UI", 7), fg=fg_muted, bg=bg_card, cursor="hand2")
        lbl_w.pack(side="right")

        for widget in (f, hdr_row, lbl_h, lbl_trend, lbl_temp, info_row, lbl_gate, lbl_w):
            widget.bind("<Button-1>", lambda e, c=canal_idx: self.abrir_ventana_actuadores(c))

        card_dict = {
            "frame": f,
            "hdr_row": hdr_row,
            "hdr": lbl_h,
            "trend": lbl_trend,
            "temp": lbl_temp,
            "info_row": info_row,
            "gate": lbl_gate,
            "watts": lbl_w,
            "last_t": None,
            "default_color": color
        }
        if not hasattr(self, '_tina_cards'):
            self._tina_cards = []
        self._tina_cards.append(card_dict)
        return card_dict


    def destellar_rx(self):
        """Micro-LED destella en verde esmeralda al recibir paquete de telemetría."""
        if hasattr(self, 'canvas_rx') and hasattr(self, '_led_rx'):
            self.canvas_rx.itemconfig(self._led_rx, fill="#10b981", outline="#34d399")
            self.root.after(120, lambda: self.canvas_rx.itemconfig(self._led_rx, fill=self.tema_actual["bg_panel"], outline="#475569"))


    def destellar_tx(self):
        """Micro-LED destella en azul cian al transmitir comandos HTTP hacia ESP32."""
        if hasattr(self, 'canvas_tx') and hasattr(self, '_led_tx'):
            self.canvas_tx.itemconfig(self._led_tx, fill="#06b6d4", outline=self.tema_actual["accent_primary"])
            self.root.after(140, lambda: self.canvas_tx.itemconfig(self._led_tx, fill=self.tema_actual["bg_panel"], outline="#475569"))


    def sonar_beep(self, freq=800, dur_ms=100):
        """Feedback acústico discreto y no bloqueante mediante winsound en Windows."""
        def _beep():
            try:
                import winsound
                winsound.Beep(int(freq), int(dur_ms))
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()


    def show_toast(self, mensaje, tipo="info", duracion_ms=3200):
        """Sistema de notificación flotante no bloqueante (Toast) en esquina superior derecha."""
        colores = {
            "info": (self.tema_actual["bg_panel"], self.tema_actual["accent_primary"], "#0284c7"),
            "success": ("#064e3b", "#34d399", "#059669"),
            "warning": ("#451a03", "#fbbf24", "#d97706"),
            "danger": ("#450a0a", "#f87171", "#dc2626"),
        }
        bg_col, fg_col, border_col = colores.get(tipo, colores["info"])

        if hasattr(self, '_active_toast') and self._active_toast is not None:
            try:
                self._active_toast.destroy()
            except Exception:
                pass

        toast_frame = tk.Frame(self.root, bg=bg_col, bd=1, relief="solid", highlightthickness=1, highlightbackground=border_col, padx=12, pady=6)
        toast_frame.place(relx=0.98, rely=0.08, anchor="ne")
        self._active_toast = toast_frame

        lbl = tk.Label(toast_frame, text=mensaje, font=("Segoe UI", 9, "bold"), fg=fg_col, bg=bg_col)
        lbl.pack(side="left")

        def _fade_out():
            try:
                if toast_frame.winfo_exists():
                    toast_frame.destroy()
                    if getattr(self, '_active_toast', None) == toast_frame:
                        self._active_toast = None
            except Exception:
                pass

        self.root.after(duracion_ms, _fade_out)


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
        self.canvas_prog_etapa.create_text(w//2 + 1, h//2 + 1, text=pct_txt, fill=self.tema_actual["bg_app"], font=("Segoe UI", 8, "bold"))
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

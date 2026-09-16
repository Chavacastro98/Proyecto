#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana Secundaria 4: Balanza Gravimétrica y Rendimiento Faradaico (ISA-88).
Optimizado para proceso Bicapa Zn + Ni (Pesaje Único al Final de Etapa 4).
"""

import os
from datetime import datetime
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VentanaFaraday:
    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("⚖️ Balanza Gravimétrica y Rendimiento Faradaico — Proceso Bicapa (Zn + Ni)")
        self.win.geometry("1100x780")
        self.win.minsize(960, 660)
        self.win.configure(bg="#0b1120")

        # Modo por defecto: BICAPA (Protocolo de Tesis: pesaje único final)
        self.var_metal = tk.StringVar(value="BICAPA")
        self.var_peso_ini = tk.StringVar(value=f"{getattr(self.app, 'peso_inicial_g', 0.0):.4f}")
        self.var_peso_fin = tk.StringVar(value=f"{getattr(self.app, 'peso_final_g', 0.0):.4f}")
        self.var_area = tk.StringVar(value=f"{getattr(self.app, 'area_placa_cm2', 65.0):.1f}")

        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _crear_ui(self):
        # 1. Header
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="BALANZA GRAVIMÉTRICA & RENDIMIENTO FARADAICO: m_teo = Σ (Q_i × M_i) / (z_i × F)",
            font=("Segoe UI", 10, "bold"),
            fg="#f472b6",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        lbl_info = tk.Label(
            hdr,
            text="Constante de Faraday: F = 96,485.33 C/mol  |  Zn: 0.33880 mg/C  |  Ni: 0.30414 mg/C",
            font=("Segoe UI", 8, "italic"),
            fg="#94a3b8",
            bg="#0f172a"
        )
        lbl_info.pack(side="right", padx=10)

        # 2. Cuerpo en 2 Columnas
        body = tk.Frame(self.win, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=6, pady=2)

        # Columna Izquierda: Controles, Balanza y Resultados
        col_ctrl = tk.Frame(body, bg="#111827", width=410, bd=1, relief="solid")
        col_ctrl.pack(side="left", fill="y", padx=4, pady=2)
        col_ctrl.pack_propagate(False)

        # 2.0 Banner Protocolar de Metalurgia / Tesis
        f_banner = tk.Frame(col_ctrl, bg="#1e1b4b", bd=1, relief="solid", highlightbackground="#6366f1", highlightthickness=1, padx=8, pady=6)
        f_banner.pack(fill="x", padx=8, pady=(8, 4))
        
        lbl_b_tit = tk.Label(
            f_banner, 
            text="🛡️ PROTOCOLO METALÚRGICO (TESIS):", 
            font=("Segoe UI", 7, "bold"), 
            fg="#a5b4fc", 
            bg="#1e1b4b"
        )
        lbl_b_tit.pack(anchor="w")

        lbl_b_desc = tk.Label(
            f_banner,
            text="La probeta NO se seca ni se pesa entre tinas para evitar la pasivación/oxidación del zinc. Se registra el Peso Inicial en seco (pre-Etapa 1) y el Peso Final al término de Etapa 4 (Bicapa terminada).",
            font=("Segoe UI", 7),
            fg="#c7d2fe",
            bg="#1e1b4b",
            wraplength=380,
            justify="left"
        )
        lbl_b_desc.pack(anchor="w", pady=(2, 0))

        # 2.1 Selector de Metal / Modo de Ensayo
        lbl_sec_m = tk.Label(col_ctrl, text="1. Modo de Electrodeposición y Constantes:", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_m.pack(anchor="w", padx=10, pady=(6, 2))

        f_metal = tk.Frame(col_ctrl, bg="#1e293b", padx=6, pady=6)
        f_metal.pack(fill="x", padx=8, pady=2)

        rb_bicapa = tk.Radiobutton(
            f_metal,
            text="Bicapa Zn + Ni (Receta Completa — Pesaje Final al terminar Etapa 4)",
            variable=self.var_metal,
            value="BICAPA",
            font=("Segoe UI", 7, "bold"),
            fg="#38bdf8",
            bg="#1e293b",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#38bdf8",
            command=self._recalcular
        )
        rb_bicapa.pack(anchor="w")

        rb_zn = tk.Radiobutton(
            f_metal,
            text="Monocapa Zinc (Zn²⁺): M=65.38 g/mol, z=2 (0.3388 mg/C, ρ=7.14 g/cm³)",
            variable=self.var_metal,
            value="ZN",
            font=("Segoe UI", 7),
            fg="#34d399",
            bg="#1e293b",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#34d399",
            command=self._recalcular
        )
        rb_zn.pack(anchor="w")

        rb_ni = tk.Radiobutton(
            f_metal,
            text="Monocapa Níquel (Ni²⁺): M=58.69 g/mol, z=2 (0.3041 mg/C, ρ=8.90 g/cm³)",
            variable=self.var_metal,
            value="NI",
            font=("Segoe UI", 7),
            fg="#a78bfa",
            bg="#1e293b",
            selectcolor="#0f172a",
            activebackground="#1e293b",
            activeforeground="#a78bfa",
            command=self._recalcular
        )
        rb_ni.pack(anchor="w")

        # 2.2 Entradas de Balanza Analítica
        lbl_sec_bal = tk.Label(col_ctrl, text="2. Datos Gravimétricos de Balanza Analítica:", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_bal.pack(anchor="w", padx=10, pady=(6, 2))

        f_bal = tk.Frame(col_ctrl, bg="#1e293b", padx=8, pady=6)
        f_bal.pack(fill="x", padx=8, pady=2)

        f_p1 = tk.Frame(f_bal, bg="#1e293b")
        f_p1.pack(fill="x", pady=2)
        tk.Label(f_p1, text="Peso Inicial en Seco (Pre-Etapa 1) [g]:", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_p1 = tk.Entry(f_p1, textvariable=self.var_peso_ini, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#38bdf8", insertbackground="#38bdf8")
        e_p1.pack(side="right")
        e_p1.bind("<KeyRelease>", lambda e: self._recalcular())

        f_p2 = tk.Frame(f_bal, bg="#1e293b")
        f_p2.pack(fill="x", pady=2)
        tk.Label(f_p2, text="Peso Final en Seco (Post-Etapa 4) [g]:", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_p2 = tk.Entry(f_p2, textvariable=self.var_peso_fin, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#34d399", insertbackground="#34d399")
        e_p2.pack(side="right")
        e_p2.bind("<KeyRelease>", lambda e: self._recalcular())

        f_area = tk.Frame(f_bal, bg="#1e293b")
        f_area.pack(fill="x", pady=2)
        tk.Label(f_area, text="Área Superficial Efectiva (cm²):", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_area = tk.Entry(f_area, textvariable=self.var_area, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#f8fafc", insertbackground="#38bdf8")
        e_area.pack(side="right")
        e_area.bind("<KeyRelease>", lambda e: self._recalcular())

        btn_calc = tk.Button(
            f_bal,
            text="⚖️ Calcular Rendimiento de Corriente Global",
            font=("Segoe UI", 8, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._recalcular
        )
        btn_calc.pack(fill="x", pady=(6, 2))

        # 2.3 Resultados Faraday
        lbl_sec_res = tk.Label(col_ctrl, text="3. Balance Faradaico y Rendimiento (η):", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_res.pack(anchor="w", padx=10, pady=(6, 2))

        f_res = tk.Frame(col_ctrl, bg="#1e293b", padx=8, pady=6)
        f_res.pack(fill="x", padx=8, pady=2)

        self.lbl_q_val = self._crear_fila_res(f_res, "Carga Eléctrica Q:", "0.0 C (0.000 mAh)", "#38bdf8")
        self.lbl_mteo_val = self._crear_fila_res(f_res, "Masa Teórica Faraday:", "0.00 mg (0.0000 g)", "#fbbf24")
        self.lbl_mreal_val = self._crear_fila_res(f_res, "Masa Real Depositada:", "0.00 mg (0.0000 g)", "#34d399")
        self.lbl_eta_val = self._crear_fila_res(f_res, "Eficiencia Faradaica η:", "0.0 %", "#f472b6", big=True)
        self.lbl_esp_val = self._crear_fila_res(f_res, "Espesor Medio Estimado:", "0.00 µm", "#a78bfa")

        # Botón Guardar en Ficha
        btn_guardar = tk.Button(
            col_ctrl,
            text="💾 Registrar en Ficha del Ensayo (resumen_receta.txt)",
            font=("Segoe UI", 8, "bold"),
            bg="#059669",
            fg="#ffffff",
            activebackground="#10b981",
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self._guardar_en_ficha
        )
        btn_guardar.pack(fill="x", padx=8, pady=(8, 4))

        f_btns = tk.Frame(col_ctrl, bg="#111827")
        f_btns.pack(fill="x", padx=8, pady=(2, 4))

        btn_cargar_csv = tk.Button(
            f_btns,
            text="📂 Cargar CSV Ensayo",
            font=("Segoe UI", 7, "bold"),
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            bd=0,
            pady=4,
            cursor="hand2",
            command=self._cargar_csv_ensayo
        )
        btn_cargar_csv.pack(side="left", fill="x", expand=True, padx=(0, 2))

        btn_graficas = tk.Button(
            f_btns,
            text="📊 Exportar 8 Figuras HD",
            font=("Segoe UI", 7, "bold"),
            bg="#7c3aed",
            fg="#ffffff",
            activebackground="#8b5cf6",
            bd=0,
            pady=4,
            cursor="hand2",
            command=lambda: self.app.exportar_grafica_hd()
        )
        btn_graficas.pack(side="right", fill="x", expand=True, padx=(2, 0))

        self.lbl_faraday_status = tk.Label(
            col_ctrl,
            text="Listo. Ingrese los pesos de la balanza o cargue un archivo CSV de ensayo.",
            font=("Segoe UI", 7, "italic"),
            fg="#94a3b8",
            bg="#111827",
            wraplength=380,
            justify="left"
        )
        self.lbl_faraday_status.pack(fill="x", padx=10, pady=2)

        # Columna Derecha: Gráficas Matplotlib
        col_plot = tk.Frame(body, bg="#0b1120")
        col_plot.pack(side="left", fill="both", expand=True, padx=4, pady=2)

        self.fig = Figure(figsize=(7.5, 5.5), dpi=100, facecolor="#0f172a")
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2, sharex=self.ax1)

        self._estilizar_axes()
        self.canvas = FigureCanvasTkAgg(self.fig, master=col_plot)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self._redibujar()

    def _crear_fila_res(self, parent, titulo, val_def, color, big=False):
        f = tk.Frame(parent, bg="#1e293b", pady=2)
        f.pack(fill="x")
        tk.Label(f, text=titulo, font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#1e293b").pack(side="left")
        lbl_v = tk.Label(f, text=val_def, font=("Segoe UI", 8 if not big else 10, "bold"), fg=color, bg="#1e293b")
        lbl_v.pack(side="right")
        return lbl_v

    def _estilizar_axes(self):
        for ax in [self.ax1, self.ax2]:
            ax.set_facecolor("#1e293b")
            ax.grid(True, linestyle=":", alpha=0.35, color="#475569")
            ax.tick_params(colors="#94a3b8", labelsize=7.5)
            for s in ax.spines.values():
                s.set_color("#334155")
        self.ax1.set_ylabel("Carga Q (Coulombs)", color="#e2e8f0", fontsize=8, fontweight="bold")
        self.ax2.set_ylabel("Masa Depositada (mg)", color="#e2e8f0", fontsize=8, fontweight="bold")
        self.ax2.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=8, fontweight="bold")
        self.fig.tight_layout(pad=1.2)

    def _recalcular(self):
        modo = self.var_metal.get()

        q_zn = max(0.0, getattr(self.app, 'coulombs_zn', 0.0))
        q_ni = max(0.0, getattr(self.app, 'coulombs_ni', 0.0))
        q_tot = max(0.0, getattr(self.app, 'coulombs_total', 0.0))

        # Si coulombs_total > 0 pero no se han dividido por etapa, asignar según modo
        if (q_zn == 0.0 and q_ni == 0.0) and q_tot > 0.0:
            if modo == "ZN":
                q_zn = q_tot
            elif modo == "NI":
                q_ni = q_tot

        try:
            p_ini = float(self.var_peso_ini.get().strip().replace(",", "."))
        except Exception:
            p_ini = 0.0

        try:
            p_fin = float(self.var_peso_fin.get().strip().replace(",", "."))
        except Exception:
            p_fin = 0.0

        try:
            area = max(0.1, float(self.var_area.get().strip().replace(",", ".")))
        except Exception:
            area = 65.0

        self.app.peso_inicial_g = p_ini
        self.app.peso_final_g = p_fin
        self.app.area_placa_cm2 = area

        m_real_g = max(0.0, p_fin - p_ini) if p_fin >= p_ini else (p_fin - p_ini)
        m_real_mg = m_real_g * 1000.0

        if modo == "BICAPA":
            # Modelo Aditivo Bicapa:
            # m_teo_total = m_teo_Zn + m_teo_Ni
            # Zn2+: M=65.38 g/mol, z=2 -> Eq = 0.33880 mg/C
            # Ni2+: M=58.69 g/mol, z=2 -> Eq = 0.30414 mg/C
            m_teo_zn_mg = q_zn * 0.33880
            m_teo_ni_mg = q_ni * 0.30414
            m_teo_total_mg = m_teo_zn_mg + m_teo_ni_mg
            m_teo_total_g = m_teo_total_mg / 1000.0

            q_usado = q_zn + q_ni if (q_zn + q_ni) > 0 else q_tot

            eta = (m_real_mg / m_teo_total_mg * 100.0) if m_teo_total_mg > 0.001 and m_real_mg > 0 else 0.0

            # Cálculo de espesores con densidades respectivas: rho_Zn=7.14, rho_Ni=8.90 g/cm3
            factor_rend = (eta / 100.0) if eta > 0 else 1.0
            esp_zn_um = (((m_teo_zn_mg * factor_rend) / 1000.0) / (7.14 * area)) * 10000.0 if area > 0 else 0.0
            esp_ni_um = (((m_teo_ni_mg * factor_rend) / 1000.0) / (8.90 * area)) * 10000.0 if area > 0 else 0.0
            esp_total_um = esp_zn_um + esp_ni_um

            mah_tot = (q_usado / 3600.0) * 1000.0
            self.lbl_q_val.config(text=f"{q_usado:.1f} C (Zn: {q_zn:.1f} C | Ni: {q_ni:.1f} C)")
            self.lbl_mteo_val.config(text=f"{m_teo_total_mg:.2f} mg (Zn: {m_teo_zn_mg:.1f} mg + Ni: {m_teo_ni_mg:.1f} mg)")
            self.lbl_mreal_val.config(text=f"{m_real_mg:.2f} mg ({m_real_g:.4f} g)")

            if eta > 0:
                color_eta = "#34d399" if (85.0 <= eta <= 105.0) else ("#fbbf24" if (70.0 <= eta <= 115.0) else "#ef4444")
                self.lbl_eta_val.config(text=f"{eta:.1f} % (Global)", fg=color_eta)
            else:
                self.lbl_eta_val.config(text="-- % (Global)", fg="#94a3b8")

            self.lbl_esp_val.config(text=f"{esp_total_um:.2f} µm (Zn: {esp_zn_um:.2f} µm + Ni: {esp_ni_um:.2f} µm)")

        elif modo == "ZN":
            q_usado = q_zn if q_zn > 0 else q_tot
            m_teo_mg = q_usado * 0.33880
            m_teo_g = m_teo_mg / 1000.0
            eta = (m_real_mg / m_teo_mg * 100.0) if m_teo_mg > 0.001 and m_real_mg > 0 else 0.0
            esp_um = (m_real_g / (7.14 * area)) * 10000.0 if m_real_g > 0 else ((m_teo_g / (7.14 * area)) * 10000.0 if m_teo_g > 0 else 0.0)
            mah = (q_usado / 3600.0) * 1000.0

            self.lbl_q_val.config(text=f"{q_usado:.1f} C ({mah:.1f} mAh)")
            self.lbl_mteo_val.config(text=f"{m_teo_mg:.2f} mg ({m_teo_g:.4f} g)")
            self.lbl_mreal_val.config(text=f"{m_real_mg:.2f} mg ({m_real_g:.4f} g)")
            if eta > 0:
                color_eta = "#34d399" if (85.0 <= eta <= 105.0) else ("#fbbf24" if (70.0 <= eta <= 115.0) else "#ef4444")
                self.lbl_eta_val.config(text=f"{eta:.1f} %", fg=color_eta)
            else:
                self.lbl_eta_val.config(text="-- %", fg="#94a3b8")
            self.lbl_esp_val.config(text=f"{esp_um:.2f} µm (Zinc)")

        else: # NI
            q_usado = q_ni if q_ni > 0 else q_tot
            m_teo_mg = q_usado * 0.30414
            m_teo_g = m_teo_mg / 1000.0
            eta = (m_real_mg / m_teo_mg * 100.0) if m_teo_mg > 0.001 and m_real_mg > 0 else 0.0
            esp_um = (m_real_g / (8.90 * area)) * 10000.0 if m_real_g > 0 else ((m_teo_g / (8.90 * area)) * 10000.0 if m_teo_g > 0 else 0.0)
            mah = (q_usado / 3600.0) * 1000.0

            self.lbl_q_val.config(text=f"{q_usado:.1f} C ({mah:.1f} mAh)")
            self.lbl_mteo_val.config(text=f"{m_teo_mg:.2f} mg ({m_teo_g:.4f} g)")
            self.lbl_mreal_val.config(text=f"{m_real_mg:.2f} mg ({m_real_g:.4f} g)")
            if eta > 0:
                color_eta = "#34d399" if (85.0 <= eta <= 105.0) else ("#fbbf24" if (70.0 <= eta <= 115.0) else "#ef4444")
                self.lbl_eta_val.config(text=f"{eta:.1f} %", fg=color_eta)
            else:
                self.lbl_eta_val.config(text="-- %", fg="#94a3b8")
            self.lbl_esp_val.config(text=f"{esp_um:.2f} µm (Níquel)")

        self._redibujar()

    def _guardar_en_ficha(self):
        modo = self.var_metal.get()
        p_ini = getattr(self.app, 'peso_inicial_g', 0.0)
        p_fin = getattr(self.app, 'peso_final_g', 0.0)
        m_real_g = max(0.0, p_fin - p_ini)
        m_real_mg = m_real_g * 1000.0
        area = getattr(self.app, 'area_placa_cm2', 65.0)

        q_zn = max(0.0, getattr(self.app, 'coulombs_zn', 0.0))
        q_ni = max(0.0, getattr(self.app, 'coulombs_ni', 0.0))
        q_tot = max(0.0, getattr(self.app, 'coulombs_total', 0.0))

        if modo == "BICAPA":
            m_teo_zn = q_zn * 0.33880
            m_teo_ni = q_ni * 0.30414
            m_teo_tot = m_teo_zn + m_teo_ni
            eta = (m_real_mg / m_teo_tot * 100.0) if m_teo_tot > 0 else 0.0
            factor = (eta / 100.0) if eta > 0 else 1.0
            esp_zn = (((m_teo_zn * factor) / 1000.0) / (7.14 * area)) * 10000.0 if area > 0 else 0.0
            esp_ni = (((m_teo_ni * factor) / 1000.0) / (8.90 * area)) * 10000.0 if area > 0 else 0.0
            esp_tot = esp_zn + esp_ni

            texto_guardar = (
                "\n========================================================================\n"
                f"ANÁLISIS DE RENDIMIENTO FARADAICO Y GRAVIMETRÍA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
                "========================================================================\n"
                "Modo de Proceso: BICAPA ZINC + NÍQUEL (Receta Completa)\n"
                "Nota de Protocolo: Probeta no se pesó entre tinas para prevenir pasivación/oxidación del zinc.\n"
                "                   Pesaje único al término de la Etapa 4.\n\n"
                "ETAPA 3 — ZINCADO ÁCIDO (Zn²⁺):\n"
                f"  • Carga Eléctrica Q_Zn: {q_zn:.2f} Coulombs ({(q_zn/3600.0)*1000.0:.2f} mAh)\n"
                f"  • Masa Teórica Faraday Zn: {m_teo_zn:.2f} mg ({m_teo_zn/1000.0:.5f} g) [Eq = 0.33880 mg/C]\n\n"
                "ETAPA 4 — NIQUELADO WATTS (Ni²⁺):\n"
                f"  • Carga Eléctrica Q_Ni: {q_ni:.2f} Coulombs ({(q_ni/3600.0)*1000.0:.2f} mAh)\n"
                f"  • Masa Teórica Faraday Ni: {m_teo_ni:.2f} mg ({m_teo_ni/1000.0:.5f} g) [Eq = 0.30414 mg/C]\n\n"
                "BALANCE GLOBAL DE LA BICAPA:\n"
                f"  • Carga Total Integrada: {q_zn + q_ni:.2f} Coulombs ({((q_zn + q_ni)/3600.0)*1000.0:.2f} mAh)\n"
                f"  • Masa Teórica Faraday Total: {m_teo_tot:.2f} mg ({m_teo_tot/1000.0:.5f} g)\n"
                f"  • Peso Inicial en Seco (Pre-Etapa 1): {p_ini:.4f} g\n"
                f"  • Peso Final en Seco (Post-Etapa 4):  {p_fin:.4f} g\n"
                f"  • Masa Real Neta Depositada:          {m_real_mg:.2f} mg ({m_real_g:.5f} g)\n"
                f"  • Rendimiento Faradaico Global (η):   {eta:.2f} %\n"
                f"  • Área Superficial Efectiva:         {area:.1f} cm²\n"
                f"  • Espesor Estimado Capa Zn (ρ=7.14): {esp_zn:.2f} µm\n"
                f"  • Espesor Estimado Capa Ni (ρ=8.90): {esp_ni:.2f} µm\n"
                f"  • Espesor Total de la Bicapa:        {esp_tot:.2f} µm\n"
                "========================================================================\n"
            )
        else:
            nom_m = "Zinc (Zn²⁺)" if modo == "ZN" else "Níquel (Ni²⁺)"
            eq_c = 0.33880 if modo == "ZN" else 0.30414
            rho = 7.14 if modo == "ZN" else 8.90
            q_m = q_zn if modo == "ZN" else q_ni
            if q_m == 0.0:
                q_m = q_tot
            m_teo = q_m * eq_c
            eta = (m_real_mg / m_teo * 100.0) if m_teo > 0 else 0.0
            esp = (m_real_g / (rho * area)) * 10000.0 if (m_real_g > 0 and area > 0) else 0.0

            texto_guardar = (
                "\n========================================================================\n"
                f"ANÁLISIS DE RENDIMIENTO FARADAICO Y GRAVIMETRÍA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
                "========================================================================\n"
                f"Metal Depositado: {nom_m} (Eq = {eq_c:.4f} mg/C, Densidad = {rho:.2f} g/cm³)\n"
                f"Carga Total Integrada Q: {q_m:.2f} Coulombs ({(q_m/3600.0)*1000.0:.2f} mAh)\n"
                f"Masa Teórica Faraday: {m_teo:.2f} mg ({m_teo/1000.0:.5f} g)\n"
                f"Peso Inicial Balanza: {p_ini:.4f} g\n"
                f"Peso Final Balanza:   {p_fin:.4f} g\n"
                f"Masa Real Depositada: {m_real_mg:.2f} mg ({m_real_g:.5f} g)\n"
                f"Rendimiento Faradaico (Eficiencia de Corriente η): {eta:.2f} %\n"
                f"Área Superficial Placa: {area:.1f} cm²\n"
                f"Espesor Medio Calculado: {esp:.2f} µm\n"
                "========================================================================\n"
            )

        if self.app.carpeta_ensayo_actual and os.path.exists(self.app.carpeta_ensayo_actual):
            f_path = os.path.join(self.app.carpeta_ensayo_actual, "resumen_receta.txt")
            try:
                with open(f_path, "a", encoding="utf-8") as f:
                    f.write(texto_guardar)
                self.lbl_faraday_status.config(
                    text=f"✅ Datos guardados con éxito en resumen_receta.txt ({datetime.now().strftime('%H:%M:%S')})",
                    fg="#34d399"
                )
                messagebox.showinfo("Registro Exitoso", f"✅ Análisis Gravimétrico guardado con éxito en:\n{f_path}")
            except Exception as e:
                self.lbl_faraday_status.config(text=f"🔴 Error al guardar: {e}", fg="#ef4444")
        else:
            messagebox.showinfo("Cálculo Realizado", "Cálculo completado correctamente. (Para guardar en disco inicie una grabación de ensayo).")

    def _cargar_csv_ensayo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Archivo CSV de Ensayo",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        if ruta and os.path.exists(ruta):
            try:
                df = pd.read_csv(ruta)
                
                # Identificar columnas
                t_col = None
                for c in ["Tiempo_Relativo_s", "tiempo_s", "t_s"]:
                    if c in df.columns:
                        t_col = c
                        break

                i_col = None
                for c in ["Fuente_Corriente_Real_A", "Fuente_Corriente_A", "corriente_a", "I_A"]:
                    if c in df.columns:
                        i_col = c
                        break

                etapa_col = None
                for c in ["Etapa_Num", "Etapa_Activa", "Etapa"]:
                    if c in df.columns:
                        etapa_col = c
                        break

                etapa_nom_col = None
                for c in ["Etapa_Nombre", "Nombre_Etapa", "etapa_nombre"]:
                    if c in df.columns:
                        etapa_nom_col = c
                        break

                q_zn = 0.0
                q_ni = 0.0
                q_tot = 0.0

                if t_col and i_col:
                    t_vals = pd.to_numeric(df[t_col], errors="coerce").fillna(0).values
                    i_vals = pd.to_numeric(df[i_col], errors="coerce").fillna(0).values
                    dt = np.diff(t_vals, prepend=t_vals[0] if len(t_vals) > 0 else 0.0)
                    dt = np.where(dt < 0, 0.0, dt)

                    # Determinar máscaras de Zinc (Etapa 3) y Níquel (Etapa 4)
                    mask_zn = np.zeros(len(df), dtype=bool)
                    mask_ni = np.zeros(len(df), dtype=bool)

                    if etapa_col:
                        e_vals = pd.to_numeric(df[etapa_col], errors="coerce").fillna(0).values
                        mask_zn |= (e_vals == 3)
                        mask_ni |= (e_vals == 4)

                    if etapa_nom_col:
                        n_vals = df[etapa_nom_col].astype(str).str.lower().values
                        mask_zn |= np.array(["zinc" in str(x) for x in n_vals])
                        mask_ni |= np.array(["niquel" in str(x) or "watts" in str(x) for x in n_vals])

                    # Si no hay etapas delimitadas, asignar según corriente
                    if not np.any(mask_zn) and not np.any(mask_ni):
                        q_tot = float(np.sum(i_vals * dt))
                    else:
                        q_zn = float(np.sum(i_vals[mask_zn] * dt[mask_zn]))
                        q_ni = float(np.sum(i_vals[mask_ni] * dt[mask_ni]))
                        q_tot = q_zn + q_ni

                    # Cargar buffers para graficar
                    self.app.buf_t = (t_vals / 60.0).tolist()
                    self.app.buf_q = np.cumsum(i_vals * dt).tolist()
                elif "Carga_Acumulada_Coulombs" in df.columns:
                    s_clean = pd.to_numeric(df["Carga_Acumulada_Coulombs"], errors="coerce").dropna()
                    if not s_clean.empty:
                        q_tot = float(s_clean.iloc[-1])

                self.app.coulombs_zn = max(0.0, q_zn)
                self.app.coulombs_ni = max(0.0, q_ni)
                self.app.coulombs_total = max(0.0, q_tot)
                self.app.carpeta_ensayo_actual = os.path.dirname(os.path.abspath(ruta))

                # Si detectamos ambas etapas, forzar modo BICAPA
                if q_zn > 0 and q_ni > 0:
                    self.var_metal.set("BICAPA")

                self._recalcular()
                self.lbl_faraday_status.config(
                    text=f"📂 CSV cargado: {os.path.basename(ruta)} (Q_Zn={q_zn:.1f} C, Q_Ni={q_ni:.1f} C, Total={q_tot:.1f} C)",
                    fg="#38bdf8"
                )
                messagebox.showinfo(
                    "CSV Cargado",
                    f"Se procesó el archivo de ensayo exitosamente:\n\n"
                    f"• Archivo: {os.path.basename(ruta)}\n"
                    f"• Carga Zinc (Etapa 3): {q_zn:.1f} C ({(q_zn/3600.0)*1000.0:.1f} mAh)\n"
                    f"• Carga Níquel (Etapa 4): {q_ni:.1f} C ({(q_ni/3600.0)*1000.0:.1f} mAh)\n"
                    f"• Carga Total Integrada: {q_tot:.1f} C\n\n"
                    "Ingrese el peso inicial y final de la balanza analítica para calcular la eficiencia faradaica."
                )
            except Exception as e:
                messagebox.showerror("Error al cargar CSV", f"No se pudo procesar el archivo CSV:\n{e}")

    def actualizar_datos(self):
        if not self.win.winfo_exists():
            return
        self._recalcular()

    def _redibujar(self):
        self.ax1.clear()
        self.ax2.clear()
        self._estilizar_axes()

        buf_t = getattr(self.app, 'buf_t', [])
        buf_q = getattr(self.app, 'buf_q', [])
        if not buf_t or not buf_q:
            self.canvas.draw_idle()
            return

        modo = self.var_metal.get()
        p_ini = getattr(self.app, 'peso_inicial_g', 0.0)
        p_fin = getattr(self.app, 'peso_final_g', 0.0)
        m_real_mg = max(0.0, (p_fin - p_ini) * 1000.0)
        area = max(0.1, getattr(self.app, 'area_placa_cm2', 65.0))

        # 1. Gráfica de Carga Eléctrica Q(t)
        self.ax1.fill_between(buf_t, buf_q, color="#38bdf8", alpha=0.25)
        self.ax1.plot(buf_t, buf_q, color="#38bdf8", lw=2.0, label=f"Carga Acumulada Q(t) [Total = {buf_q[-1]:.1f} C]")
        self.ax1.set_title("1. Integral de Corriente Faradaica: Q(t) = ∫ I(t)dt [Coulombs]", color="#e2e8f0", fontsize=8.5, fontweight="bold")
        self.ax1.legend(loc="upper left", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # 2. Gráfica de Masa Teórica Faradaica vs Masa Real de Balanza
        if modo == "BICAPA":
            # Calcular curva acumulativa teórica
            # Eq Zn = 0.33880 mg/C, Eq Ni = 0.30414 mg/C
            q_zn = getattr(self.app, 'coulombs_zn', 0.0)
            q_ni = getattr(self.app, 'coulombs_ni', 0.0)
            
            # Estimación de curva m_teo(t) proporcional
            if q_zn + q_ni > 0:
                eq_prom = ((q_zn * 0.33880) + (q_ni * 0.30414)) / (q_zn + q_ni)
            else:
                eq_prom = 0.33880

            buf_m_teo = [q * eq_prom for q in buf_q]
            m_teo_fin = (q_zn * 0.33880) + (q_ni * 0.30414)
            if m_teo_fin <= 0:
                m_teo_fin = buf_m_teo[-1]

            self.ax2.fill_between(buf_t, buf_m_teo, color="#fbbf24", alpha=0.25)
            self.ax2.plot(buf_t, buf_m_teo, color="#fbbf24", lw=2.0, label=f"Masa Teórica Bicapa m_teo(t) [Total = {m_teo_fin:.1f} mg]")

            if m_real_mg > 0:
                self.ax2.axhline(m_real_mg, color="#34d399", ls="--", lw=1.8, label=f"Masa Real Balanza (Bicapa Final) = {m_real_mg:.2f} mg")
                eta = (m_real_mg / m_teo_fin * 100.0) if m_teo_fin > 0 else 0.0
                mid_idx = len(buf_t) // 2
                self.ax2.text(
                    buf_t[mid_idx],
                    m_real_mg * 1.04,
                    f"Rendimiento Faradaico Global η = {eta:.1f} %",
                    color="#34d399",
                    fontsize=8,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f172a", edgecolor="#34d399", alpha=0.85)
                )

            self.ax2.set_title("2. Masa Teórica Faraday m_teo = (Q_Zn × 0.3388) + (Q_Ni × 0.3041) [mg]", color="#e2e8f0", fontsize=8.5, fontweight="bold")
        else:
            eq_mg_c = 0.33880 if modo == "ZN" else 0.30414
            nom_m = "Zinc" if modo == "ZN" else "Níquel"
            buf_m_teo = [q * eq_mg_c for q in buf_q]

            self.ax2.fill_between(buf_t, buf_m_teo, color="#fbbf24", alpha=0.25)
            self.ax2.plot(buf_t, buf_m_teo, color="#fbbf24", lw=2.0, label=f"Masa Teórica {nom_m} [Total = {buf_m_teo[-1]:.1f} mg]")

            if m_real_mg > 0:
                self.ax2.axhline(m_real_mg, color="#34d399", ls="--", lw=1.8, label=f"Masa Real Medida Balanza = {m_real_mg:.2f} mg")
                eta = (m_real_mg / buf_m_teo[-1] * 100.0) if buf_m_teo[-1] > 0 else 0.0
                mid_idx = len(buf_t) // 2
                self.ax2.text(
                    buf_t[mid_idx],
                    m_real_mg * 1.04,
                    f"Eficiencia Faradaica η = {eta:.1f} %",
                    color="#34d399",
                    fontsize=8,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f172a", edgecolor="#34d399", alpha=0.85)
                )

            self.ax2.set_title(f"2. Masa Teórica de {nom_m}: m_teo = Q × {eq_mg_c:.4f} mg/C", color="#e2e8f0", fontsize=8.5, fontweight="bold")

        self.ax2.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=8, fontweight="bold")
        self.ax2.legend(loc="upper left", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def _on_close(self):
        self.app.win_faraday = None
        self.win.destroy()

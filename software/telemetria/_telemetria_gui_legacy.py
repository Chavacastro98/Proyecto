#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
SISTEMA DE TELEMETRÍA EN VIVO, GESTOR DE ENSAYOS Y SUPERVISIÓN SCADA
===================================================================================
Tesis: Automatización y Control de Línea Piloto de Electrodeposición
Microcontrolador: ESP32 Master Node (Firmware v3.1 / v3.5)

Características:
1. Gestor de Ensayos ISA-88 con matriz de 32 placas y temporizadores automáticos.
2. Monitor de Telemetría en Vivo (2 Subplots amplios: Térmico y Corriente VCSS).
3. Ventana Modular de Actuadores: Osciloscopio virtual de TRIACs (Ángulo de Fase vs Burst Firing) y VCSS.
4. Ventana Modular de Errores de Control: e(t) = SP - PV con bandas de tolerancia e índices IAE / ISE.
5. Gestor de Carpetas Estructuradas por Ensayo: Subcarpetas con CSVs de sensores, errores y gráficas 300 DPI.
===================================================================================
"""

import sys
import os
import time
import csv
import math
import random
import threading
from datetime import datetime
import subprocess

# Compatibilidad UTF-8 en consola de Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import winsound
    def reproducir_alarma_sonora(patron="fin_etapa"):
        """
        Reproduce una alarma acústica industrial potente y bien audible sin bloquear la GUI.
        Patrones:
          - 'fin_etapa': Ráfaga de 3 pulsos dobles de alta frecuencia (1500Hz y 2200Hz)
          - 'fin_ensayo': Secuencia melódica de 4 tonos (C6, E6, G6, C7)
          - 'test': Tono de prueba nítido de 1800Hz
        """
        def _beep_thread():
            try:
                if sys.platform == "win32":
                    if patron == "fin_etapa":
                        for _ in range(3):
                            winsound.Beep(1500, 160)
                            time.sleep(0.06)
                            winsound.Beep(2200, 240)
                            time.sleep(0.18)
                    elif patron == "fin_ensayo":
                        for f in [1046, 1318, 1568, 2093]:
                            winsound.Beep(f, 220)
                            time.sleep(0.06)
                    elif patron == "test":
                        winsound.Beep(1800, 350)
                else:
                    for _ in range(3):
                        print("\a", flush=True)
                        time.sleep(0.2)
            except Exception:
                pass
        threading.Thread(target=_beep_thread, daemon=True).start()

    def play_chime():
        reproducir_alarma_sonora("fin_etapa")
except Exception:
    def reproducir_alarma_sonora(patron="fin_etapa"):
        pass
    def play_chime():
        pass

# Comprobación de librerías requeridas
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog
except ImportError:
    print("[ERROR] Tkinter no está instalado.")
    sys.exit(1)

try:
    import requests
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Librería faltante",
        "La librería 'requests' no está instalada.\n\nInstálala ejecutando: pip install requests"
    )
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Librería faltante",
        "La librería 'pandas' o 'openpyxl' no está instalada.\n\nInstálala ejecutando: pip install pandas openpyxl"
    )
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.patches as patches
    import numpy as np
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Librería faltante",
        "La librería 'matplotlib' o 'numpy' no está instalada.\n\nInstálala ejecutando: pip install matplotlib numpy"
    )
    sys.exit(1)


def calcular_disparo_triac(p_pct, max_watts):
    """Calcula el ángulo de disparo, retardo de fase en microsegundos y potencia activa RMS."""
    p_safe = max(0.0, min(100.0, float(p_pct)))
    if p_safe <= 0.0:
        return 0.0, 180.0, 8333, 0.0
    elif p_safe >= 100.0:
        return 100.0, 0.0, 0, float(max_watts)
    
    arg = 2.0 * (p_safe / 100.0) - 1.0
    alpha_rad = math.acos(max(-1.0, min(1.0, arg)))
    alpha_deg = round((alpha_rad / math.pi) * 180.0, 1)
    delay_us = int((alpha_rad / math.pi) * 8333.0)
    watts = round(float(max_watts) * (p_safe / 100.0), 1)
    return p_safe, alpha_deg, delay_us, watts


# =================================================================================
# VENTANA SECUNDARIA 1: MONITOR DE ACTUADORES & OSCILOSCOPIO DE TRIACS Y GATE
# =================================================================================
class VentanaActuadores:
    def __init__(self, parent_app, canal_inicial=0):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Osciloscopio de Potencia — Conmutación AC 60Hz y Señales de Compuerta")
        self.win.geometry("1000x740")
        self.win.minsize(850, 600)
        self.win.configure(bg="#0b1120")

        self.canal_sel = canal_inicial  # 0: T1, 1: T2, 2: T3, 3: T4, 4: Vista 4 Tinas
        self.modo_conmutacion = "FASE"  # "FASE" o "PROPORCIONAL"

        self.potencias_max = [450.0, 450.0, 18.0, 450.0]
        self.resistencias = [120.0**2 / 450.0, 120.0**2 / 450.0, 120.0**2 / 18.0, 120.0**2 / 450.0]  # R = V^2 / P (Ohms)
        self.nombres_tinas = ["T1: Limpieza (450W)", "T2: Decapado (450W)", "T3: Celda Hull (18W)", "T4: Níquel (450W)"]
        self.colores_tinas = ["#d95f02", "#e6ab02", "#38bdf8", "#a78bfa"]

        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _crear_ui(self):
        # 1. Header con Controles de Selección y Métodos de Disparo
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="OSCILOSCOPIO DIGITAL: ONDA AC SENOIDAL Y PULSOS DE GATE",
            font=("Segoe UI", 10, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        # Controles de Modo de Disparo
        frame_controles = tk.Frame(hdr, bg="#0f172a")
        frame_controles.pack(side="right", padx=10, pady=4)

        tk.Label(frame_controles, text="Método de Control:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#0f172a").pack(side="left", padx=(6, 4))
        self.var_modo = tk.StringVar(value=self.modo_conmutacion)
        rb_fase = tk.Radiobutton(
            frame_controles,
            text="Recorte de Fase (α)",
            variable=self.var_modo,
            value="FASE",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#38bdf8",
            command=self._on_modo_change
        )
        rb_fase.pack(side="left", padx=4)

        rb_prop = tk.Radiobutton(
            frame_controles,
            text="Burst Fire / Proporcional (ZCS)",
            variable=self.var_modo,
            value="PROPORCIONAL",
            font=("Segoe UI", 8, "bold"),
            fg="#34d399",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#34d399",
            command=self._on_modo_change
        )
        rb_prop.pack(side="left", padx=4)

        # 2. Barra de Botones de Tina
        bar_canales = tk.Frame(self.win, bg="#111827")
        bar_canales.pack(fill="x", padx=6, pady=2)

        self.btns_canales = []
        for i, nombre in enumerate(self.nombres_tinas):
            b = tk.Button(
                bar_canales,
                text=nombre,
                font=("Segoe UI", 8, "bold"),
                bg="#2563eb" if i == self.canal_sel else "#1e293b",
                fg="#ffffff",
                bd=0,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda idx=i: self._seleccionar_canal(idx)
            )
            b.pack(side="left", padx=3, pady=3, expand=True, fill="x")
            self.btns_canales.append(b)

        b_vcss = tk.Button(
            bar_canales,
            text="Fuente VCSS (Pulsos y Shunts)",
            font=("Segoe UI", 8, "bold"),
            bg="#2563eb" if self.canal_sel == 4 else "#1e293b",
            fg="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=lambda: self._seleccionar_canal(4)
        )
        b_vcss.pack(side="left", padx=3, pady=3, expand=True, fill="x")
        self.btns_canales.append(b_vcss)

        b_all = tk.Button(
            bar_canales,
            text="Vista 4 Tinas (2×2)",
            font=("Segoe UI", 8, "bold"),
            bg="#2563eb" if self.canal_sel == 5 else "#1e293b",
            fg="#ffffff",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=lambda: self._seleccionar_canal(5)
        )
        b_all.pack(side="left", padx=3, pady=3, expand=True, fill="x")
        self.btns_canales.append(b_all)

        # 3. Canvas de Matplotlib para la Onda AC y Señal de Gate
        plot_frame = tk.Frame(self.win, bg="#0b1120")
        plot_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self.fig = Figure(figsize=(8.5, 5.2), dpi=100, facecolor="#0f172a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # 4. KPI Bar en la parte inferior
        kpi_bar = tk.Frame(self.win, bg="#111827", bd=0)
        kpi_bar.pack(fill="x", side="bottom", padx=6, pady=4)

        self.lbl_kpi_u = self._crear_kpi_sub(kpi_bar, "Esfuerzo u(t)", "0.0 %", "#38bdf8")
        self.lbl_kpi_alpha = self._crear_kpi_sub(kpi_bar, "Ángulo Disparo α", "180.0°", "#fbbf24")
        self.lbl_kpi_delay = self._crear_kpi_sub(kpi_bar, "Retardo Gate", "8333 µs", "#f472b6")
        self.lbl_kpi_vrms = self._crear_kpi_sub(kpi_bar, "Voltaje RMS", "0.0 V", "#a78bfa")
        self.lbl_kpi_watts = self._crear_kpi_sub(kpi_bar, "Potencia Activa", "0.0 W", "#22c55e")
        self.lbl_kpi_gate_st = self._crear_kpi_sub(kpi_bar, "Estado Conducción", "BLOQUEO (0V)", "#ef4444")
        self.lbl_kpi_vcss = self._crear_kpi_sub(kpi_bar, "Sumidero VCSS", "0.00 A", "#34d399")

        self._redibujar()

    def _crear_kpi_sub(self, parent, title, val_def, color):
        f = tk.Frame(parent, bg="#1e293b", bd=0, padx=6, pady=3)
        f.pack(side="left", expand=True, fill="x", padx=2, pady=2)
        lbl_t = tk.Label(f, text=title, font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#1e293b")
        lbl_t.pack()
        lbl_v = tk.Label(f, text=val_def, font=("Segoe UI", 8, "bold"), fg=color, bg="#1e293b")
        lbl_v.pack()
        return lbl_v

    def _seleccionar_canal(self, idx):
        self.canal_sel = idx
        for i, b in enumerate(self.btns_canales):
            b.config(bg="#2563eb" if i == idx else "#1e293b")
        self._redibujar()

    def _on_modo_change(self):
        self.modo_conmutacion = self.var_modo.get()
        self._redibujar()

    def actualizar_datos(self):
        if not self.win.winfo_exists():
            return
        self._redibujar()

    def _redibujar(self):
        self.fig.clear()

        # Obtener valores actuales de potencia u(t) de los buffers del app
        u_vals = [
            getattr(self.app, 'ultimo_u1', 0.0),
            getattr(self.app, 'ultimo_u2', 0.0),
            getattr(self.app, 'ultimo_u3', 0.0),
            getattr(self.app, 'ultimo_u4', 0.0)
        ]

        if self.canal_sel < 4:
            # =========================================================================
            # VISTA DE CANAL INDIVIDUAL: 3 SUBPLOTS SINCRONIZADOS
            # 1. Tensión de Carga AC vs Red 120V (Recorte de Fase / Burst Firing)
            # 2. Señal Digital de Disparo de Compuerta (Gate Pulses 0V-5V)
            # 3. Potencia Instantánea en la Resistencia (Watts) y Sumidero VCSS
            # =========================================================================
            ax1 = self.fig.add_subplot(3, 1, 1)
            ax2 = self.fig.add_subplot(3, 1, 2, sharex=ax1)
            ax3 = self.fig.add_subplot(3, 1, 3, sharex=ax1)

            ch = self.canal_sel
            u = max(0.0, min(100.0, float(u_vals[ch])))
            p_max = self.potencias_max[ch]
            res_ohm = self.resistencias[ch]
            col = self.colores_tinas[ch]
            nom = self.nombres_tinas[ch]

            # Parámetros analíticos de fase
            p_pct, alpha_deg, delay_us, watts = calcular_disparo_triac(u, p_max)
            alpha_rad = (alpha_deg / 180.0) * math.pi
            v_rms_frac = math.sqrt(max(0.0, 1.0 - (alpha_rad / math.pi) + (math.sin(2.0 * alpha_rad) / (2.0 * math.pi))))
            v_rms = 120.0 * v_rms_frac

            # Actualizar KPIs inferiores
            self.lbl_kpi_u.config(text=f"{u:.1f} %")
            self.lbl_kpi_alpha.config(text=f"{alpha_deg:.1f}°")
            self.lbl_kpi_delay.config(text=f"{delay_us} µs")
            self.lbl_kpi_vrms.config(text=f"{v_rms:.1f} V")
            self.lbl_kpi_watts.config(text=f"{watts:.1f} W / {p_max:.0f}W")
            curr_val = getattr(self.app, 'ultimo_amps', 0.0)
            self.lbl_kpi_vcss.config(text=f"{curr_val:.2f} A")

            # --- ESTILIZAR AXES ---
            for ax in [ax1, ax2, ax3]:
                ax.set_facecolor("#1e293b")
                ax.grid(True, linestyle=":", alpha=0.35, color="#475569")
                ax.tick_params(colors="#94a3b8", labelsize=7.5)
                for s in ax.spines.values():
                    s.set_color("#334155")

            v_peak = 170.0  # 120 * sqrt(2)
            t_half_ms = 8.3333

            if self.modo_conmutacion == "FASE":
                # =====================================================================
                # MODO RECORTE DE FASE (60 Hz — Ventana de 2 ciclos = 33.33 ms)
                # =====================================================================
                if u <= 0.0:
                    self.lbl_kpi_gate_st.config(text="BLOQUEADO (0%)", fg="#ef4444")
                elif u >= 100.0:
                    self.lbl_kpi_gate_st.config(text="CONDUCCIÓN TOTAL (100%)", fg="#34d399")
                else:
                    self.lbl_kpi_gate_st.config(text=f"RECORTE α={alpha_deg:.0f}° ({delay_us}µs)", fg="#38bdf8")

                t_max = 33.333
                t_ms = np.linspace(0, t_max, 1000)
                v_ac = v_peak * np.sin(2 * np.pi * 60.0 * (t_ms / 1000.0))

                delay_ms = delay_us / 1000.0
                pulse_width_ms = 0.15  # Pulso de 150 us en el Gate

                v_conducido = np.zeros_like(v_ac)
                gate_signal = np.zeros_like(t_ms)

                for i, t in enumerate(t_ms):
                    t_mod = t % t_half_ms
                    if t_mod >= delay_ms and u > 0.0:
                        v_conducido[i] = v_ac[i]

                    if (delay_ms <= t_mod <= (delay_ms + pulse_width_ms)) and (0.0 < u < 100.0):
                        gate_signal[i] = 5.0
                    elif u >= 100.0:
                        if t_mod <= pulse_width_ms:
                            gate_signal[i] = 5.0

                # 1. Tensión de Carga
                ax1.plot(t_ms, v_ac, color="#64748b", ls="--", lw=1.1, alpha=0.6, label="Red 120V AC 60Hz")
                ax1.axhline(0, color="#475569", lw=0.8)

                for k in range(5):
                    t_zc = k * t_half_ms
                    ax1.axvline(t_zc, color="#fbbf24", ls=":", lw=0.9, alpha=0.5)
                    ax2.axvline(t_zc, color="#fbbf24", ls=":", lw=0.9, alpha=0.5)

                ax1.fill_between(t_ms, v_conducido, color=col, alpha=0.40)
                ax1.plot(t_ms, v_conducido, color=col, lw=2.0, label=f"V_load: {nom} ({v_rms:.1f} V_RMS)")
                ax1.set_title(
                    f"1. Tensión de Carga AC con Recorte de Fase — {nom}: u={u:.1f}% | α={alpha_deg:.0f}° ({delay_us} µs) | {watts:.1f} W",
                    color="#e2e8f0", fontsize=8.5, fontweight="bold"
                )
                ax1.set_ylabel("Voltaje (V)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax1.set_ylim(-190, 190)
                ax1.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

                # 2. Señal de Gate
                ax2.step(t_ms, gate_signal, color="#f472b6", lw=1.8, where="post", label="Pulso Gate (0V / 5V TTL)")
                ax2.fill_between(t_ms, gate_signal, color="#f472b6", alpha=0.30, step="post")

                for k in range(4):
                    t_gate_fire = k * t_half_ms + delay_ms
                    if t_gate_fire <= t_max and 0.0 < u < 100.0:
                        ax2.annotate(
                            f"Gate α={alpha_deg:.0f}°\n({delay_us}µs)",
                            xy=(t_gate_fire, 5.0),
                            xytext=(t_gate_fire + 0.6, 3.2),
                            fontsize=6.5,
                            color="#f472b6",
                            arrowprops=dict(arrowstyle="->", color="#f472b6", lw=0.8)
                        )

                ax2.set_title("2. Señal de Disparo de Compuerta (Gate Pulses al MOC3021 / Arduino Slave)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
                ax2.set_ylabel("Gate (V)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax2.set_ylim(-0.5, 6.0)
                ax2.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

                # 3. Potencia Instantánea
                p_inst = (v_conducido**2) / res_ohm
                ax3.fill_between(t_ms, p_inst, color="#22c55e", alpha=0.25)
                ax3.plot(t_ms, p_inst, color="#22c55e", lw=1.6, label=f"P(t) Instantánea (P_RMS = {watts:.1f} W)")
                ax3.axhline(watts, color="#34d399", ls="--", lw=1.2, label=f"P_media = {watts:.1f} W")
                ax3.set_title("3. Potencia Activa Instantánea Disipada en el Calentador: p(t) = v(t)² / R", color="#e2e8f0", fontsize=8.5, fontweight="bold")
                ax3.set_ylabel("Potencia (W)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax3.set_xlabel("Tiempo (milisegundos — 2 Ciclos AC de 16.66 ms c/u)", color="#e2e8f0", fontsize=7.5)
                ax3.set_ylim(0, max(p_max * 2.2, 50.0))
                ax3.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")
                ax1.set_xlim(0, t_max)

            else:
                # =====================================================================
                # MODO BURST FIRING (Control por Paquetes de Ciclos — Ventana de 12 Ciclos = 200 ms)
                # =====================================================================
                t_max = 200.0
                t_ms = np.linspace(0, t_max, 1500)
                v_ac = v_peak * np.sin(2 * np.pi * 60.0 * (t_ms / 1000.0))

                num_ciclos_base = 12
                t_ciclo_ms = 16.666
                n_on = int(round((u / 100.0) * num_ciclos_base))
                n_off = num_ciclos_base - n_on
                t_corte_ms = n_on * t_ciclo_ms

                self.lbl_kpi_gate_st.config(text=f"BURST {n_on} ON / {n_off} OFF", fg="#34d399" if n_on > 0 else "#ef4444")
                self.lbl_kpi_alpha.config(text="ZCS (0°)")
                self.lbl_kpi_delay.config(text="0 µs (ZCS)")

                v_conducido = np.zeros_like(v_ac)
                gate_burst = np.zeros_like(t_ms)

                for i, t in enumerate(t_ms):
                    if t <= t_corte_ms and u > 0.0:
                        v_conducido[i] = v_ac[i]
                        gate_burst[i] = 5.0
                    else:
                        v_conducido[i] = 0.0
                        gate_burst[i] = 0.0

                # 1. Tensión de Carga en Burst Fire
                ax1.plot(t_ms, v_ac, color="#64748b", ls=":", lw=1.0, label="Red AC 60Hz")
                if n_on > 0:
                    mask_on = t_ms <= t_corte_ms
                    ax1.axvspan(0, t_corte_ms, color="#10b981", alpha=0.12, label=f"ON: {n_on} Ciclos ({t_corte_ms:.1f} ms)")
                    ax1.fill_between(t_ms[mask_on], v_conducido[mask_on], color=col, alpha=0.40)
                    ax1.plot(t_ms[mask_on], v_conducido[mask_on], color=col, lw=2.0, label=f"Conducción ZCS ({n_on} Ciclos)")

                if n_off > 0:
                    ax1.axvspan(t_corte_ms, t_max, color="#ef4444", alpha=0.08, label=f"OFF: {n_off} Ciclos")
                    mask_off = t_ms >= t_corte_ms
                    ax1.plot(t_ms[mask_off], np.zeros(np.sum(mask_off)), color="#ef4444", lw=2.2, label="TRIAC Bloqueado (0V)")

                ax1.set_title(
                    f"1. Control por Paquetes de Ciclos (Burst Firing Cruce por Cero) — {nom}: {n_on} ON / {n_off} OFF ({u:.0f}% Potencia)",
                    color="#e2e8f0", fontsize=8.5, fontweight="bold"
                )
                ax1.set_ylabel("Voltaje (V)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax1.set_ylim(-190, 190)
                ax1.set_xlim(0, t_max)
                ax1.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

                # 2. Habilitación de Gate
                ax2.step(t_ms, gate_burst, color="#f472b6", lw=1.8, where="post", label="Habilitación Gate TRIAC (5V en Ciclos ON)")
                ax2.fill_between(t_ms, gate_burst, color="#f472b6", alpha=0.30, step="post")
                ax2.set_title("2. Señal de Disparo de Compuerta durante la Ventana de Control (200 ms = 12 Ciclos)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
                ax2.set_ylabel("Gate (V)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax2.set_ylim(-0.5, 6.0)
                ax2.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

                # 3. Potencia Media
                p_inst = np.where(t_ms <= t_corte_ms, (v_ac**2)/res_ohm, 0.0) if u > 0.0 else np.zeros_like(t_ms)
                ax3.fill_between(t_ms, p_inst, color="#22c55e", alpha=0.25)
                ax3.plot(t_ms, p_inst, color="#22c55e", lw=1.6, label="Potencia Instantánea")
                ax3.axhline(watts, color="#34d399", ls="--", lw=1.2, label=f"P_media = {watts:.1f} W")
                ax3.set_title("3. Potencia Activa Entregada en la Ventana de Control (200 ms)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
                ax3.set_ylabel("Potencia (W)", color="#e2e8f0", fontsize=8, fontweight="bold")
                ax3.set_xlabel("Tiempo (milisegundos — Ventana de 12 Ciclos / 200 ms)", color="#e2e8f0", fontsize=7.5)
                ax3.set_ylim(0, max(p_max * 2.2, 50.0))
                ax3.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        elif self.canal_sel == 4:
            # =========================================================================
            # VISTA FUENTE DE CORRIENTE VCSS (ONDA PULSADA Y SHUNTS DUALES)
            # 1. Tren de Onda de Corriente I(t) [Pico, Promedio, Ton, Toff]
            # 2. Señal de Control DAC y Gate del MOSFET (0V - 3.3V)
            # 3. Balance de Shunts (Rama 1 vs Rama 2: I1 e I2)
            # =========================================================================
            ax1 = self.fig.add_subplot(3, 1, 1)
            ax2 = self.fig.add_subplot(3, 1, 2, sharex=ax1)
            ax3 = self.fig.add_subplot(3, 1, 3)

            for ax in [ax1, ax2, ax3]:
                ax.set_facecolor("#1e293b")
                ax.grid(True, linestyle=":", alpha=0.35, color="#475569")
                ax.tick_params(colors="#94a3b8", labelsize=7.5)
                for s in ax.spines.values():
                    s.set_color("#334155")

            # Obtener datos de la fuente del app
            d_f = getattr(self.app, 'ultimo_df', {}) or {}
            es_activa = (d_f.get("act", 0) == 1)
            es_pul = (d_f.get("modo", 0) == 1)
            freq = max(1, int(d_f.get("freq", 10)))
            duty = max(1, min(99, int(d_f.get("duty", 20))))
            i_pico = float(d_f.get("i_real", d_f.get("amps", 0.0))) if es_activa else 0.0
            i_prom = (i_pico * (duty / 100.0)) if (es_activa and es_pul) else i_pico
            i1 = float(d_f.get("i1", i_pico * 0.5)) if es_activa else 0.0
            i2 = float(d_f.get("i2", i_pico * 0.5)) if es_activa else 0.0
            vs1 = float(d_f.get("vs1", i1 * 0.15))
            vs2 = float(d_f.get("vs2", i2 * 0.15))

            # Actualizar KPIs
            self.lbl_kpi_u.config(text=f"Duty: {duty}%" if es_pul else "DC 100%")
            self.lbl_kpi_alpha.config(text=f"Freq: {freq} Hz" if es_pul else "DC")
            periodo_ms = 1000.0 / freq if es_pul else 100.0
            t_on_ms = (periodo_ms * duty) / 100.0 if es_pul else periodo_ms
            t_off_ms = periodo_ms - t_on_ms if es_pul else 0.0
            self.lbl_kpi_delay.config(text=f"Ton: {t_on_ms:.1f} ms" if es_pul else "Continuo")
            self.lbl_kpi_vrms.config(text=f"I_prom: {i_prom:.2f} A")
            self.lbl_kpi_watts.config(text=f"I_pico: {i_pico:.2f} A")
            self.lbl_kpi_gate_st.config(text="PULSADO ACTIVO" if (es_activa and es_pul) else ("DC ACTIVO" if es_activa else "DESACTIVADA"), fg="#34d399" if es_activa else "#ef4444")
            self.lbl_kpi_vcss.config(text=f"{i_pico:.2f} A")

            # 1. Tren de Onda de Corriente I(t)
            t_max = 3.0 * periodo_ms if es_pul else 100.0
            t_ms = np.linspace(0, t_max, 1200)
            i_t = np.zeros_like(t_ms)

            if es_activa:
                if es_pul:
                    for i, t in enumerate(t_ms):
                        t_mod = t % periodo_ms
                        i_t[i] = i_pico if t_mod <= t_on_ms else 0.0
                else:
                    i_t[:] = i_pico

            ax1.fill_between(t_ms, i_t, color="#22c55e", alpha=0.30, step="post" if es_pul else None)
            ax1.plot(t_ms, i_t, color="#22c55e", lw=2.0, label=f"I(t) en la Celda (Pico = {i_pico:.2f} A)")
            if es_activa and es_pul:
                ax1.axhline(i_prom, color="#fbbf24", ls="--", lw=1.5, label=f"I_promedio = {i_prom:.2f} A")
                ax1.set_title(
                    f"1. Forma de Onda de Corriente Galvánica I(t) — Frecuencia: {freq} Hz | Duty: {duty}% | Ton: {t_on_ms:.1f}ms | Toff: {t_off_ms:.1f}ms",
                    color="#e2e8f0", fontsize=8.5, fontweight="bold"
                )
            else:
                ax1.set_title(
                    f"1. Corriente Galvánica Continua (DC) — I = {i_pico:.2f} A",
                    color="#e2e8f0", fontsize=8.5, fontweight="bold"
                )
            ax1.set_ylabel("Corriente (A)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax1.set_ylim(-0.2, max(2.5, i_pico * 1.35))
            ax1.set_xlim(0, t_max)
            ax1.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 2. Señal DAC MCP4725 y Control de Gate
            dac_signal = np.zeros_like(t_ms)
            if es_activa:
                if es_pul:
                    v_dac_max = (i_pico / 6.6) * 3.3
                    for i, t in enumerate(t_ms):
                        t_mod = t % periodo_ms
                        dac_signal[i] = v_dac_max if t_mod <= t_on_ms else 0.0
                else:
                    dac_signal[:] = (i_pico / 6.6) * 3.3

            ax2.step(t_ms, dac_signal, color="#38bdf8", lw=1.8, where="post", label="Voltaje Control DAC MCP4725 (0-3.3V)")
            ax2.fill_between(t_ms, dac_signal, color="#38bdf8", alpha=0.25, step="post")
            ax2.set_title("2. Señal de Control Analógica / Puerta MOSFET (DAC I2C @ 12-bit)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax2.set_ylabel("V_DAC (V)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax2.set_xlabel("Tiempo (milisegundos)", color="#e2e8f0", fontsize=7.5)
            ax2.set_ylim(-0.2, 3.8)
            ax2.legend(loc="upper right", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 3. Balance de Shunts (MOSFET 1 vs MOSFET 2)
            categorias = ["Shunt 1 (MOSFET 1)", "Shunt 2 (MOSFET 2)", "Total Medido"]
            valores_i = [i1, i2, i_pico]
            colores_bar = ["#38bdf8", "#818cf8", "#22c55e"]
            bars = ax3.barh(categorias, valores_i, color=colores_bar, height=0.55, edgecolor="#334155")
            for bar, val in zip(bars, valores_i):
                ax3.text(val + 0.04, bar.get_y() + bar.get_height()/2.0, f"{val:.2f} A", va="center", color="#f8fafc", fontsize=8, fontweight="bold")

            ax3.set_xlim(0, max(2.5, i_pico * 1.35))
            ax3.set_title(f"3. Balance Físico de Corriente en Shunts (A2: {vs1:.3f}V | A3: {vs2:.3f}V | Gm: {d_f.get('gm', 1.0):.4f})", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax3.set_xlabel("Corriente (Amperios)", color="#e2e8f0", fontsize=7.5)

        else:
            # =========================================================================
            # VISTA COMPARATIVA 2x2 DE LAS 4 TINAS
            # =========================================================================
            axes = [
                self.fig.add_subplot(2, 2, 1),
                self.fig.add_subplot(2, 2, 2),
                self.fig.add_subplot(2, 2, 3),
                self.fig.add_subplot(2, 2, 4),
            ]

            v_peak = 170.0

            if self.modo_conmutacion == "FASE":
                t_ms = np.linspace(0, 16.666, 500)  # 1 ciclo de 60Hz
                v_ac = v_peak * np.sin(2 * np.pi * 60.0 * (t_ms / 1000.0))
                t_half = 8.3333

                for ch, ax in enumerate(axes):
                    u = max(0.0, min(100.0, float(u_vals[ch])))
                    col = self.colores_tinas[ch]
                    nom = self.nombres_tinas[ch]
                    p_max = self.potencias_max[ch]

                    p_pct, alpha_deg, delay_us, watts = calcular_disparo_triac(u, p_max)
                    delay_ms = delay_us / 1000.0

                    ax.set_facecolor("#1e293b")
                    ax.grid(True, linestyle=":", alpha=0.3, color="#475569")
                    ax.tick_params(colors="#94a3b8", labelsize=6.5)
                    for s in ax.spines.values():
                        s.set_color("#334155")

                    v_cond = np.zeros_like(v_ac)
                    gate_sig = np.zeros_like(t_ms)

                    for i, t in enumerate(t_ms):
                        t_mod = t % t_half
                        if t_mod >= delay_ms and u > 0.0:
                            v_cond[i] = v_ac[i]
                        if (delay_ms <= t_mod <= (delay_ms + 0.2)) and (0.0 < u < 100.0):
                            gate_sig[i] = 40.0

                    ax.plot(t_ms, v_ac, color="#475569", ls="--", lw=0.9)
                    ax.fill_between(t_ms, v_cond, color=col, alpha=0.35)
                    ax.plot(t_ms, v_cond, color=col, lw=1.6)

                    # Señal de Gate superpuesta en la parte inferior
                    ax.step(t_ms, gate_sig - 160.0, color="#f472b6", lw=1.2, where="post")
                    ax.text(0.5, -150, "Gate Pulse", color="#f472b6", fontsize=5.5)

                    ax.set_title(f"{nom}: u={u:.0f}% ({watts:.1f}W | α={alpha_deg:.0f}° | {delay_us}µs)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
                    ax.set_ylim(-185, 185)
                    ax.set_xlim(0, 16.666)

            else:
                # 2x2 en Burst Firing (12 ciclos = 200 ms)
                t_ms = np.linspace(0, 200.0, 800)
                v_ac = v_peak * np.sin(2 * np.pi * 60.0 * (t_ms / 1000.0))

                for ch, ax in enumerate(axes):
                    u = max(0.0, min(100.0, float(u_vals[ch])))
                    col = self.colores_tinas[ch]
                    nom = self.nombres_tinas[ch]
                    p_max = self.potencias_max[ch]

                    n_on = int(round((u / 100.0) * 12))
                    n_off = 12 - n_on
                    t_corte = n_on * 16.666
                    watts = p_max * (u / 100.0)

                    ax.set_facecolor("#1e293b")
                    ax.grid(True, linestyle=":", alpha=0.3, color="#475569")
                    ax.tick_params(colors="#94a3b8", labelsize=6.5)
                    for s in ax.spines.values():
                        s.set_color("#334155")

                    ax.plot(t_ms, v_ac, color="#475569", ls=":", lw=0.9)
                    if n_on > 0:
                        mask_on = t_ms <= t_corte
                        ax.fill_between(t_ms[mask_on], v_ac[mask_on], color=col, alpha=0.40)
                        ax.plot(t_ms[mask_on], v_ac[mask_on], color=col, lw=1.6)
                    if n_off > 0:
                        mask_off = t_ms >= t_corte
                        ax.plot(t_ms[mask_off], np.zeros(np.sum(mask_off)), color="#ef4444", lw=1.8)

                    ax.set_title(f"{nom}: {n_on} ON / {n_off} OFF ({u:.0f}% | {watts:.1f}W)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
                    ax.set_ylim(-185, 185)
                    ax.set_xlim(0, 200.0)

        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def _on_close(self):
        self.app.win_actuadores = None
        self.win.destroy()


# =================================================================================
# VENTANA SECUNDARIA 2: MONITOR DE ERRORES DE CONTROL Y PLANO DE FASE (SP vs PV)
# =================================================================================
class VentanaErrores:
    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Monitor de Error de Control & Plano de Fase — Seguimiento Dinámico (e vs ė)")
        self.win.geometry("1020x780")
        self.win.minsize(850, 620)
        self.win.configure(bg="#0b1120")

        self.modo_vista = "COMPLETO"  # "COMPLETO", "TEMPORAL", "FASE"

        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _crear_ui(self):
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="ANÁLISIS DE ERROR Y PLANO DE FASE: e(t) vs ė(t) (Derivada del Error)",
            font=("Segoe UI", 10, "bold"),
            fg="#34d399",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        # Controles de Modo de Vista
        frame_modos = tk.Frame(hdr, bg="#0f172a")
        frame_modos.pack(side="right", padx=10, pady=4)

        self.var_vista = tk.StringVar(value=self.modo_vista)
        rb_comp = tk.Radiobutton(
            frame_modos,
            text="Vista 3 Paneles",
            variable=self.var_vista,
            value="COMPLETO",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#38bdf8",
            command=self._on_vista_change
        )
        rb_comp.pack(side="left", padx=3)

        rb_fase = tk.Radiobutton(
            frame_modos,
            text="Solo Retrato de Fase (ė vs e)",
            variable=self.var_vista,
            value="FASE",
            font=("Segoe UI", 8, "bold"),
            fg="#f472b6",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#f472b6",
            command=self._on_vista_change
        )
        rb_fase.pack(side="left", padx=3)

        rb_temp = tk.Radiobutton(
            frame_modos,
            text="Solo Error Temporal e(t)",
            variable=self.var_vista,
            value="TEMPORAL",
            font=("Segoe UI", 8, "bold"),
            fg="#34d399",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            activeforeground="#34d399",
            command=self._on_vista_change
        )
        rb_temp.pack(side="left", padx=3)

        # Matplotlib Canvas
        plot_frame = tk.Frame(self.win, bg="#0b1120")
        plot_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self.fig = Figure(figsize=(8.5, 5.5), dpi=100, facecolor="#0f172a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # KPIs de Índices de Desempeño
        kpi_bar = tk.Frame(self.win, bg="#111827", bd=0)
        kpi_bar.pack(fill="x", side="bottom", padx=6, pady=4)

        self.lbl_iae_t1 = self._crear_kpi_err(kpi_bar, "IAE T1 (Limp)", "0.0", "#d95f02")
        self.lbl_iae_t2 = self._crear_kpi_err(kpi_bar, "IAE T2 (Decap)", "0.0", "#e6ab02")
        self.lbl_iae_t3 = self._crear_kpi_err(kpi_bar, "IAE T3 (Zinc)", "0.0", "#38bdf8")
        self.lbl_iae_t4 = self._crear_kpi_err(kpi_bar, "IAE T4 (Níquel)", "0.0", "#a78bfa")
        self.lbl_dedt = self._crear_kpi_err(kpi_bar, "Derivada ė(t)", "0.00 °C/s", "#f472b6")
        self.lbl_err_curr = self._crear_kpi_err(kpi_bar, "Error Corriente", "0.00 A", "#34d399")
        self.lbl_regimen = self._crear_kpi_err(kpi_bar, "Estado Lazo / Fase", "EN ESPERA", "#fbbf24")

        self._redibujar()

    def _crear_kpi_err(self, parent, title, val_def, color):
        f = tk.Frame(parent, bg="#1e293b", bd=0, padx=6, pady=4)
        f.pack(side="left", expand=True, fill="x", padx=2, pady=2)
        lbl_t = tk.Label(f, text=title, font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#1e293b")
        lbl_t.pack()
        lbl_v = tk.Label(f, text=val_def, font=("Segoe UI", 9, "bold"), fg=color, bg="#1e293b")
        lbl_v.pack()
        return lbl_v

    def _on_vista_change(self):
        self.modo_vista = self.var_vista.get()
        self._redibujar()

    def actualizar_datos(self):
        if not self.win.winfo_exists():
            return
        self._redibujar()

    def _redibujar(self):
        self.fig.clear()

        buf_t = self.app.buf_t
        if not buf_t:
            self.canvas.draw_idle()
            return

        # Calcular series de error: e(t) = SP - T
        e_t1 = [sp - t for sp, t in zip(self.app.buf_t1_sp, self.app.buf_t1)]
        e_t2 = [sp - t for sp, t in zip(self.app.buf_t2_sp, self.app.buf_t2)]
        e_t3 = [sp - t for sp, t in zip(self.app.buf_t3_sp, self.app.buf_t3)]
        e_t4 = [sp - t for sp, t in zip(self.app.buf_t4_sp, self.app.buf_t4)]

        # Calcular derivadas discretas dedt: de/dt = (e[i] - e[i-1]) / dt (dt = 1s)
        def calc_dedt(e_series):
            if len(e_series) < 2:
                return [0.0] * len(e_series)
            d = [0.0]
            for i in range(1, len(e_series)):
                d.append(e_series[i] - e_series[i-1])
            return d

        de_t1 = calc_dedt(e_t1)
        de_t2 = calc_dedt(e_t2)
        de_t3 = calc_dedt(e_t3)
        de_t4 = calc_dedt(e_t4)

        # Error corriente: target - medido
        target_curr = 1.50 if (self.app.etapa_activa_idx == 2 and self.app.etapa_corriendo) else (1.13 if (self.app.etapa_activa_idx == 3 and self.app.etapa_corriendo) else 0.0)
        e_curr = [target_curr - i_val for i_val in self.app.buf_curr]

        def estilizar(ax):
            ax.set_facecolor("#1e293b")
            ax.grid(True, linestyle=":", alpha=0.35, color="#475569")
            ax.tick_params(colors="#94a3b8", labelsize=7.5)
            for s in ax.spines.values():
                s.set_color("#334155")

        if self.modo_vista == "COMPLETO":
            ax1 = self.fig.add_subplot(3, 1, 1)
            ax2 = self.fig.add_subplot(3, 1, 2)
            ax3 = self.fig.add_subplot(3, 1, 3)
            estilizar(ax1)
            estilizar(ax2)
            estilizar(ax3)

            # 1. Error Temporal
            ax1.axhspan(-1.0, 1.0, color="#fbbf24", alpha=0.12, label="Banda Tolerancia ±1.0°C")
            ax1.axhspan(-0.5, 0.5, color="#34d399", alpha=0.18, label="Alta Precisión ±0.5°C")
            ax1.axhline(0, color="#10b981", ls="--", lw=1.2)
            ax1.plot(buf_t, e_t1, color="#d95f02", ls="-", lw=1.6, zorder=2, label="e1: Limpieza")
            ax1.plot(buf_t, e_t2, color="#e6ab02", ls=(0, (6, 3)), lw=1.6, zorder=3, label="e2: Decapado")
            ax1.plot(buf_t, e_t3, color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=1.8, zorder=4, label="e3: Zincado")
            ax1.plot(buf_t, e_t4, color="#a78bfa", ls=(0, (1.5, 2.0)), lw=1.8, zorder=5, label="e4: Níquel")
            ax1.set_title("1. Desviación Térmica Temporal: e(t) = SP - PV (°C)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax1.set_ylabel("Error (°C)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax1.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 2. Retrato de Fase: ė vs e
            ax2.axvline(0, color="#64748b", ls="--", lw=1.0)
            ax2.axhline(0, color="#64748b", ls="--", lw=1.0)
            rect_atractor = matplotlib.patches.Rectangle((-0.5, -0.05), 1.0, 0.10, color="#10b981", alpha=0.18, zorder=1, label="Atractor de Estabilidad (±0.5°C)")
            ax2.add_patch(rect_atractor)

            ax2.plot(e_t1, de_t1, color="#d95f02", lw=1.4, alpha=0.8, label="Trayectoria T1")
            ax2.plot(e_t2, de_t2, color="#e6ab02", lw=1.4, alpha=0.8, label="Trayectoria T2")
            ax2.plot(e_t3, de_t3, color="#38bdf8", lw=1.8, alpha=0.9, label="Trayectoria T3")
            ax2.plot(e_t4, de_t4, color="#a78bfa", lw=1.8, alpha=0.9, label="Trayectoria T4")

            if e_t1: ax2.scatter([e_t1[-1]], [de_t1[-1]], color="#d95f02", s=28, zorder=6, edgecolors="#ffffff")
            if e_t2: ax2.scatter([e_t2[-1]], [de_t2[-1]], color="#e6ab02", s=28, zorder=6, edgecolors="#ffffff")
            if e_t3: ax2.scatter([e_t3[-1]], [de_t3[-1]], color="#38bdf8", s=36, zorder=6, edgecolors="#ffffff", marker="*")
            if e_t4: ax2.scatter([e_t4[-1]], [de_t4[-1]], color="#a78bfa", s=36, zorder=6, edgecolors="#ffffff", marker="*")

            ax2.set_title("2. Retrato de Fase del Control Térmico: ė(t) [Derivada] vs e(t) [Error] (Convergencia al Origen)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax2.set_xlabel("Error e(t) = SP - T (°C)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax2.set_ylabel("ė(t) (°C/s)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax2.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 3. Error Corriente
            ax3.axhspan(-0.05, 0.05, color="#38bdf8", alpha=0.15, label="Tolerancia ±50 mA")
            ax3.axhline(0, color="#38bdf8", ls="--", lw=1.2)
            ax3.plot(buf_t, e_curr, color="#34d399", lw=1.8, label="Error Corriente e_I(t)")
            ax3.set_title("3. Desviación de Corriente Galvánica respecto a la Consigna (A)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax3.set_ylabel("Error (A)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax3.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax3.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        elif self.modo_vista == "FASE":
            ax = self.fig.add_subplot(1, 1, 1)
            estilizar(ax)
            ax.axvline(0, color="#64748b", ls="--", lw=1.2)
            ax.axhline(0, color="#64748b", ls="--", lw=1.2)

            rect_atractor = matplotlib.patches.Rectangle((-0.5, -0.05), 1.0, 0.10, color="#10b981", alpha=0.22, zorder=1, label="Zona Atractora / Estabilidad (±0.5°C | ±0.05°C/s)")
            ax.add_patch(rect_atractor)
            rect_tol = matplotlib.patches.Rectangle((-1.0, -0.10), 2.0, 0.20, color="#fbbf24", alpha=0.10, zorder=0, label="Banda de Tolerancia (±1.0°C)")
            ax.add_patch(rect_tol)

            ax.plot(e_t1, de_t1, color="#d95f02", lw=2.0, alpha=0.85, label="T1: Limpieza (450W)")
            ax.plot(e_t2, de_t2, color="#e6ab02", lw=2.0, alpha=0.85, label="T2: Decapado (450W)")
            ax.plot(e_t3, de_t3, color="#38bdf8", lw=2.4, alpha=0.95, label="T3: Zincado Celda Hull (18W)")
            ax.plot(e_t4, de_t4, color="#a78bfa", lw=2.4, alpha=0.95, label="T4: Niquelado Watts (450W)")

            if e_t1: ax.scatter([e_t1[-1]], [de_t1[-1]], color="#d95f02", s=60, marker="*", edgecolors="#ffffff", zorder=6, label=f"T1 Actual: e={e_t1[-1]:.1f}°C")
            if e_t3: ax.scatter([e_t3[-1]], [de_t3[-1]], color="#38bdf8", s=80, marker="*", edgecolors="#ffffff", zorder=6, label=f"T3 Actual: e={e_t3[-1]:.1f}°C")
            if e_t4: ax.scatter([e_t4[-1]], [de_t4[-1]], color="#a78bfa", s=80, marker="*", edgecolors="#ffffff", zorder=6, label=f"T4 Actual: e={e_t4[-1]:.1f}°C")

            ax.set_title("RETRATO DE FASE: DERIVADA DEL ERROR ė(t) vs ERROR e(t) (Plano de Estado y Convergencia)", color="#e2e8f0", fontsize=10, fontweight="bold")
            ax.set_xlabel("Error Térmico e(t) = Setpoint - Temperatura (°C)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax.set_ylabel("Derivada del Error ė(t) = de/dt (°C/s)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax.legend(loc="upper right", fontsize=8, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        else:
            ax1 = self.fig.add_subplot(2, 1, 1)
            ax2 = self.fig.add_subplot(2, 1, 2)
            estilizar(ax1)
            estilizar(ax2)

            ax1.axhspan(-1.0, 1.0, color="#fbbf24", alpha=0.12, label="Banda Tolerancia ±1.0°C")
            ax1.axhspan(-0.5, 0.5, color="#34d399", alpha=0.18, label="Alta Precisión ±0.5°C")
            ax1.axhline(0, color="#10b981", ls="--", lw=1.2)
            ax1.plot(buf_t, e_t1, color="#d95f02", ls="-", lw=1.8, zorder=2, label="Error T1: Limpieza")
            ax1.plot(buf_t, e_t2, color="#e6ab02", ls=(0, (6, 3)), lw=1.8, zorder=3, label="Error T2: Decapado")
            ax1.plot(buf_t, e_t3, color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=2.0, zorder=4, label="Error T3: Zincado")
            ax1.plot(buf_t, e_t4, color="#a78bfa", ls=(0, (1.5, 2.0)), lw=2.0, zorder=5, label="Error T4: Níquel")
            ax1.set_title("Desviación Térmica Respecto al Setpoint: e(t) = SP - PV (°C)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax1.set_ylabel("Error (°C)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax1.legend(loc="upper right", fontsize=7.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            ax2.axhspan(-0.05, 0.05, color="#38bdf8", alpha=0.15, label="Tolerancia Corriente ±50 mA")
            ax2.axhline(0, color="#38bdf8", ls="--", lw=1.2)
            ax2.plot(buf_t, e_curr, color="#34d399", lw=2.0, label="Error Corriente e_I(t)")
            ax2.set_title("Desviación de Corriente del Sumidero VCSS (Target - Medida Real)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax2.set_ylabel("Error (A)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax2.set_xlabel("Tiempo de Proceso (minutos)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax2.legend(loc="upper right", fontsize=7.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # Actualizar KPIs
        self.lbl_iae_t1.config(text=f"{self.app.iae_t1:.1f}")
        self.lbl_iae_t2.config(text=f"{self.app.iae_t2:.1f}")
        self.lbl_iae_t3.config(text=f"{self.app.iae_t3:.1f}")
        self.lbl_iae_t4.config(text=f"{self.app.iae_t4:.1f}")

        curr_de = de_t3[-1] if de_t3 else 0.0
        self.lbl_dedt.config(text=f"{curr_de:+.3f} °C/s")

        curr_err_now = e_curr[-1] if e_curr else 0.0
        self.lbl_err_curr.config(text=f"{curr_err_now:+.2f} A")

        if e_t3 and de_t3:
            err_now = abs(e_t3[-1])
            dedt_now = abs(de_t3[-1])
            if err_now <= 0.5 and dedt_now <= 0.05:
                self.lbl_regimen.config(text="🟢 EN ATRACTOR (±0.5°C | Estacionario)", fg="#34d399")
            elif err_now <= 1.0:
                self.lbl_regimen.config(text="🟡 EN TOLERANCIA (±1°C | Amortiguando)", fg="#fbbf24")
            else:
                self.lbl_regimen.config(text="🔵 CONVERGIENDO AL ORIGEN", fg="#38bdf8")

        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def _on_close(self):
        self.app.win_errores = None
        self.win.destroy()


# =================================================================================
# VENTANA SECUNDARIA 4: BALANZA GRAVIMÉTRICA Y RENDIMIENTO FARADAICO (ISA-88)
# =================================================================================
class VentanaFaraday:
    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("⚖️ Balanza Gravimétrica y Rendimiento Faradaico — Ley de Faraday")
        self.win.geometry("1060x760")
        self.win.minsize(920, 620)
        self.win.configure(bg="#0b1120")

        self.var_metal = tk.StringVar(value="AUTO")
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
            text="BALANZA GRAVIMÉTRICA & RENDIMIENTO FARADAICO: m = (Q × M) / (z × F)",
            font=("Segoe UI", 10, "bold"),
            fg="#f472b6",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        lbl_info = tk.Label(
            hdr,
            text="Ley de Faraday: F = 96,485.33 C/mol",
            font=("Segoe UI", 8, "italic"),
            fg="#94a3b8",
            bg="#0f172a"
        )
        lbl_info.pack(side="right", padx=10)

        # 2. Cuerpo en 2 Columnas
        body = tk.Frame(self.win, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=6, pady=2)

        # Columna Izquierda: Controles, Balanza y Resultados
        col_ctrl = tk.Frame(body, bg="#111827", width=380, bd=1, relief="solid")
        col_ctrl.pack(side="left", fill="y", padx=4, pady=2)
        col_ctrl.pack_propagate(False)

        # 2.1 Selector de Metal
        lbl_sec_m = tk.Label(col_ctrl, text="1. Parámetros del Metal Depositado:", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_m.pack(anchor="w", padx=10, pady=(8, 2))

        f_metal = tk.Frame(col_ctrl, bg="#1e293b", padx=6, pady=6)
        f_metal.pack(fill="x", padx=8, pady=2)

        rb_auto = tk.Radiobutton(f_metal, text="Auto (Según Etapa Activa)", variable=self.var_metal, value="AUTO", font=("Segoe UI", 7, "bold"), fg="#38bdf8", bg="#1e293b", selectcolor="#0f172a", activebackground="#1e293b", activeforeground="#38bdf8", command=self._recalcular)
        rb_auto.pack(anchor="w")

        rb_zn = tk.Radiobutton(f_metal, text="Zinc (Zn²⁺): M=65.38 g/mol, z=2 (0.3388 mg/C)", variable=self.var_metal, value="ZN", font=("Segoe UI", 7, "bold"), fg="#34d399", bg="#1e293b", selectcolor="#0f172a", activebackground="#1e293b", activeforeground="#34d399", command=self._recalcular)
        rb_zn.pack(anchor="w")

        rb_ni = tk.Radiobutton(f_metal, text="Níquel (Ni²⁺): M=58.69 g/mol, z=2 (0.3041 mg/C)", variable=self.var_metal, value="NI", font=("Segoe UI", 7, "bold"), fg="#a78bfa", bg="#1e293b", selectcolor="#0f172a", activebackground="#1e293b", activeforeground="#a78bfa", command=self._recalcular)
        rb_ni.pack(anchor="w")

        # 2.2 Entradas de Balanza Analítica
        lbl_sec_bal = tk.Label(col_ctrl, text="2. Datos de Balanza Analítica (Gramos):", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_bal.pack(anchor="w", padx=10, pady=(8, 2))

        f_bal = tk.Frame(col_ctrl, bg="#1e293b", padx=8, pady=6)
        f_bal.pack(fill="x", padx=8, pady=2)

        f_p1 = tk.Frame(f_bal, bg="#1e293b")
        f_p1.pack(fill="x", pady=2)
        tk.Label(f_p1, text="Peso Inicial Placa (g):", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_p1 = tk.Entry(f_p1, textvariable=self.var_peso_ini, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#38bdf8", insertbackground="#38bdf8")
        e_p1.pack(side="right")
        e_p1.bind("<KeyRelease>", lambda e: self._recalcular())

        f_p2 = tk.Frame(f_bal, bg="#1e293b")
        f_p2.pack(fill="x", pady=2)
        tk.Label(f_p2, text="Peso Final Placa (g):", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_p2 = tk.Entry(f_p2, textvariable=self.var_peso_fin, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#34d399", insertbackground="#34d399")
        e_p2.pack(side="right")
        e_p2.bind("<KeyRelease>", lambda e: self._recalcular())

        f_area = tk.Frame(f_bal, bg="#1e293b")
        f_area.pack(fill="x", pady=2)
        tk.Label(f_area, text="Área Placa (cm²):", font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b").pack(side="left")
        e_area = tk.Entry(f_area, textvariable=self.var_area, font=("Segoe UI", 8), width=10, bg="#0f172a", fg="#f8fafc", insertbackground="#38bdf8")
        e_area.pack(side="right")
        e_area.bind("<KeyRelease>", lambda e: self._recalcular())

        btn_calc = tk.Button(
            f_bal,
            text="⚖️ Calcular Rendimiento de Corriente",
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
        lbl_sec_res = tk.Label(col_ctrl, text="3. Resultados y Eficiencia Faradaica:", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111827")
        lbl_sec_res.pack(anchor="w", padx=10, pady=(8, 2))

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
            text="💾 Registrar en Ficha del Ensayo",
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
        btn_guardar.pack(fill="x", padx=8, pady=(10, 4))

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
            text="📊 Exportar 5 Gráficas HD",
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
            text="Listo. Ingrese los pesos o cargue un archivo CSV de ensayo.",
            font=("Segoe UI", 7, "italic"),
            fg="#94a3b8",
            bg="#111827",
            wraplength=350,
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

    def _obtener_constantes_metal(self):
        sel = self.var_metal.get()
        if sel == "AUTO":
            if self.app.etapa_activa_idx == 2:
                sel = "ZN"
            elif self.app.etapa_activa_idx == 3:
                sel = "NI"
            else:
                sel = "ZN"

        if sel == "NI":
            return "Níquel (Ni²⁺)", 58.69, 2, 0.30414, 8.90
        else:
            return "Zinc (Zn²⁺)", 65.38, 2, 0.33880, 7.14

    def _recalcular(self):
        nom_m, M, z, eq_mg_c, rho = self._obtener_constantes_metal()
        q_total = getattr(self.app, 'coulombs_total', 0.0)

        m_teo_mg = q_total * eq_mg_c
        m_teo_g = m_teo_mg / 1000.0

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

        eta = (m_real_mg / m_teo_mg * 100.0) if m_teo_mg > 0.001 and m_real_mg > 0 else 0.0
        espesor_um = (m_real_g / (rho * area)) * 10000.0 if (m_real_g > 0 and area > 0) else ((m_teo_g / (rho * area)) * 10000.0 if (m_teo_g > 0) else 0.0)

        mah = (q_total / 3600.0) * 1000.0
        self.lbl_q_val.config(text=f"{q_total:.1f} C ({mah:.1f} mAh)")
        self.lbl_mteo_val.config(text=f"{m_teo_mg:.2f} mg ({m_teo_g:.4f} g)")
        self.lbl_mreal_val.config(text=f"{m_real_mg:.2f} mg ({m_real_g:.4f} g)")

        if eta > 0:
            color_eta = "#34d399" if (85.0 <= eta <= 105.0) else ("#fbbf24" if (70.0 <= eta <= 115.0) else "#ef4444")
            self.lbl_eta_val.config(text=f"{eta:.1f} %", fg=color_eta)
        else:
            self.lbl_eta_val.config(text="-- %", fg="#94a3b8")

        self.lbl_esp_val.config(text=f"{espesor_um:.2f} µm ({nom_m.split()[0]})")
        self._redibujar()

    def _guardar_en_ficha(self):
        nom_m, M, z, eq_mg_c, rho = self._obtener_constantes_metal()
        q_total = getattr(self.app, 'coulombs_total', 0.0)
        m_teo_mg = q_total * eq_mg_c
        m_teo_g = m_teo_mg / 1000.0
        p_ini = getattr(self.app, 'peso_inicial_g', 0.0)
        p_fin = getattr(self.app, 'peso_final_g', 0.0)
        m_real_g = max(0.0, p_fin - p_ini)
        m_real_mg = m_real_g * 1000.0
        eta = (m_real_mg / m_teo_mg * 100.0) if m_teo_mg > 0 else 0.0
        area = getattr(self.app, 'area_placa_cm2', 65.0)
        espesor_um = (m_real_g / (rho * area)) * 10000.0 if (m_real_g > 0 and area > 0) else 0.0

        if self.app.carpeta_ensayo_actual and os.path.exists(self.app.carpeta_ensayo_actual):
            f_path = os.path.join(self.app.carpeta_ensayo_actual, "resumen_receta.txt")
            try:
                with open(f_path, "a", encoding="utf-8") as f:
                    f.write("\n========================================================================\n")
                    f.write(f"ANÁLISIS DE RENDIMIENTO FARADAICO Y GRAVIMETRÍA ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
                    f.write("========================================================================\n")
                    f.write(f"Metal Depositado: {nom_m} (M={M} g/mol, z={z}, Eq={eq_mg_c:.4f} mg/C)\n")
                    f.write(f"Carga Total Integrada Q: {q_total:.2f} Coulombs ({(q_total/3600.0)*1000.0:.2f} mAh)\n")
                    f.write(f"Masa Teórica Faraday: {m_teo_mg:.2f} mg ({m_teo_g:.5f} g)\n")
                    f.write(f"Peso Inicial Balanza: {p_ini:.4f} g\n")
                    f.write(f"Peso Final Balanza:   {p_fin:.4f} g\n")
                    f.write(f"Masa Real Depositada: {m_real_mg:.2f} mg ({m_real_g:.5f} g)\n")
                    f.write(f"Rendimiento Faradaico (Eficiencia de Corriente η): {eta:.2f} %\n")
                    f.write(f"Área Superficial Placa: {area:.1f} cm²\n")
                    f.write(f"Espesor Medio Calculado: {espesor_um:.2f} µm (Densidad = {rho:.2f} g/cm³)\n")
                    f.write("========================================================================\n")
                self.lbl_faraday_status.config(text=f"✅ Datos guardados con éxito en resumen_receta.txt ({datetime.now().strftime('%H:%M:%S')})", fg="#34d399")
                messagebox.showinfo("Registro Exitoso", f"✅ Análisis de Rendimiento Faradaico guardado:\n\n• Carga Q: {q_total:.1f} C\n• Masa Teórica: {m_teo_mg:.2f} mg\n• Masa Real: {m_real_mg:.2f} mg\n• Eficiencia Faradaica η: {eta:.2f} %\n• Espesor: {espesor_um:.2f} µm")
            except Exception as e:
                self.lbl_faraday_status.config(text=f"🔴 Error al guardar: {e}", fg="#ef4444")
        else:
            messagebox.showinfo("Cálculo Realizado", f"Cálculo completado:\n\n• Carga Q: {q_total:.1f} C\n• Masa Teórica: {m_teo_mg:.2f} mg\n• Masa Real: {m_real_mg:.2f} mg\n• Eficiencia Faradaica: {eta:.2f} %")

    def _cargar_csv_ensayo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Archivo CSV de Ensayo",
            filetypes=[("Archivos CSV", "*.csv")]
        )
        if ruta and os.path.exists(ruta):
            try:
                df = pd.read_csv(ruta)
                q_cargado = 0.0
                if "Carga_Acumulada_Coulombs" in df.columns:
                    s_clean = pd.to_numeric(df["Carga_Acumulada_Coulombs"], errors="coerce").dropna()
                    if not s_clean.empty:
                        q_cargado = float(s_clean.iloc[-1])
                elif "Fuente_Corriente_Real_A" in df.columns and "Tiempo_Relativo_s" in df.columns:
                    t_vals = pd.to_numeric(df["Tiempo_Relativo_s"], errors="coerce").fillna(0).values
                    i_vals = pd.to_numeric(df["Fuente_Corriente_Real_A"], errors="coerce").fillna(0).values
                    dt = np.diff(t_vals, prepend=0.0)
                    q_cargado = float(np.sum(i_vals * dt))
                elif "Fuente_Corriente_A" in df.columns and "Tiempo_Relativo_s" in df.columns:
                    t_vals = pd.to_numeric(df["Tiempo_Relativo_s"], errors="coerce").fillna(0).values
                    i_vals = pd.to_numeric(df["Fuente_Corriente_A"], errors="coerce").fillna(0).values
                    dt = np.diff(t_vals, prepend=0.0)
                    q_cargado = float(np.sum(i_vals * dt))

                self.app.coulombs_total = max(0.0, q_cargado)
                self.app.carpeta_ensayo_actual = os.path.dirname(os.path.abspath(ruta))
                self._recalcular()
                self.lbl_faraday_status.config(
                    text=f"📂 CSV cargado: {os.path.basename(ruta)} (Q = {q_cargado:.1f} C)",
                    fg="#38bdf8"
                )
                messagebox.showinfo("CSV Cargado", f"Se cargó el ensayo correctamente:\n\n• Archivo: {os.path.basename(ruta)}\n• Carga Eléctrica Q: {q_cargado:.1f} Coulombs ({(q_cargado/3600.0)*1000.0:.1f} mAh)\n\nIngrese el peso inicial y final medidos para calcular la eficiencia.")
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

        buf_t = self.app.buf_t
        if not buf_t:
            self.canvas.draw_idle()
            return

        nom_m, M, z, eq_mg_c, rho = self._obtener_constantes_metal()
        buf_q = getattr(self.app, 'buf_q', [])

        p_ini = getattr(self.app, 'peso_inicial_g', 0.0)
        p_fin = getattr(self.app, 'peso_final_g', 0.0)
        m_real_mg = max(0.0, (p_fin - p_ini) * 1000.0)

        # 1. Gráfica de Carga Eléctrica Q(t)
        if buf_q:
            self.ax1.fill_between(buf_t, buf_q, color="#38bdf8", alpha=0.25)
            self.ax1.plot(buf_t, buf_q, color="#38bdf8", lw=2.0, label=f"Carga Acumulada Q(t) (Total = {buf_q[-1]:.1f} C)")
        self.ax1.set_title(f"1. Integral de Corriente: Q(t) = ∫ I(t)dt [Coulombs]", color="#e2e8f0", fontsize=8.5, fontweight="bold")
        self.ax1.legend(loc="upper left", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # 2. Gráfica de Masa Teórica vs Masa Real
        if buf_q:
            buf_m_teo = [q * eq_mg_c for q in buf_q]
            self.ax2.fill_between(buf_t, buf_m_teo, color="#fbbf24", alpha=0.25)
            self.ax2.plot(buf_t, buf_m_teo, color="#fbbf24", lw=2.0, label=f"Masa Teórica m_teo(t) ({nom_m.split()[0]} = {buf_m_teo[-1]:.2f} mg)")

            if m_real_mg > 0:
                self.ax2.axhline(m_real_mg, color="#34d399", ls="--", lw=1.8, label=f"Masa Real Medida Balanza = {m_real_mg:.2f} mg")
                eta = (m_real_mg / buf_m_teo[-1] * 100.0) if buf_m_teo[-1] > 0 else 0.0
                mid_idx = len(buf_t) // 2
                self.ax2.text(buf_t[mid_idx], m_real_mg * 1.05, f"Eficiencia Faradaica η = {eta:.1f} %", color="#34d399", fontsize=8, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f172a", edgecolor="#34d399", alpha=0.8))

        self.ax2.set_title(f"2. Masa de Metal Depositada: m_teo = (Q × {M:.2f}) / ({z} × 96485) [mg]", color="#e2e8f0", fontsize=8.5, fontweight="bold")
        self.ax2.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=8, fontweight="bold")
        self.ax2.legend(loc="upper left", fontsize=7, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def _on_close(self):
        self.app.win_faraday = None
        self.win.destroy()


# =================================================================================
# VENTANA SECUNDARIA 3: DIAGNÓSTICO DE SENSORES Y PERIFÉRICOS (v3.1 / v3.5)
# =================================================================================
class VentanaDiagnostico:
    def __init__(self, parent_app):
        self.app = parent_app
        self.win = tk.Toplevel(self.app.root)
        self.win.title("Diagnóstico de Hardware — Estado de Periféricos I2C y SPI")
        self.win.geometry("780x560")
        self.win.minsize(700, 480)
        self.win.configure(bg="#0b1120")

        self.running = True
        self._crear_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refrescar_datos()

    def _crear_ui(self):
        hdr = tk.Frame(self.win, bg="#0f172a", height=50, bd=0)
        hdr.pack(fill="x", side="top", padx=6, pady=4)

        lbl_t = tk.Label(
            hdr,
            text="DIAGNÓSTICO DE HARDWARE: ESTADO DE 8 PERIFÉRICOS (I2C / SPI)",
            font=("Segoe UI", 10, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_t.pack(side="left", padx=10, pady=8)

        btn_rescan = tk.Button(
            hdr,
            text="Re-escanear Bus",
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
        btn_rescan.pack(side="right", padx=10)

        # Contenedor de Tarjetas
        body = tk.Frame(self.win, bg="#0b1120")
        body.pack(fill="both", expand=True, padx=10, pady=6)

        # Sección 1: Bus I2C (0x38, 0x76/77, 0x48, 0x60)
        lbl_i2c = tk.Label(body, text="Periféricos en Bus I2C (GPIO 8 / 9 — 400 kHz):", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#0b1120")
        lbl_i2c.pack(anchor="w", pady=(4, 2))

        f_i2c = tk.Frame(body, bg="#111827", bd=1, relief="solid")
        f_i2c.pack(fill="x", pady=2)

        self.card_aht = self._crear_card_sensor(f_i2c, "AHT20 (0x38)", "Temp/Hum Ambiente", 0)
        self.card_bmp = self._crear_card_sensor(f_i2c, "BMP280 (0x76/77)", "Presión Barométrica", 1)
        self.card_ads = self._crear_card_sensor(f_i2c, "ADS1115 (0x48)", "pH + Shunts VCSS 16-bit", 2)
        self.card_dac = self._crear_card_sensor(f_i2c, "MCP4725 (0x60)", "DAC Corriente VCSS 12-bit", 3)

        # Sección 2: Bus SPI Termopares (MAX6675 T1..T4)
        lbl_spi = tk.Label(body, text="🔥 Sensores de Temperatura SPI MAX6675 (Termopares K):", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#0b1120")
        lbl_spi.pack(anchor="w", pady=(10, 2))

        f_spi = tk.Frame(body, bg="#111827", bd=1, relief="solid")
        f_spi.pack(fill="x", pady=2)

        self.card_t1 = self._crear_card_sensor(f_spi, "MAX6675 #1 (CS 5)", "Tina 1: Limpieza (450W)", 0)
        self.card_t2 = self._crear_card_sensor(f_spi, "MAX6675 #2 (CS 4)", "Tina 2: Decapado (450W)", 1)
        self.card_t3 = self._crear_card_sensor(f_spi, "MAX6675 #3 (CS 13)", "Tina 3: Celda Hull (18W)", 2)
        self.card_t4 = self._crear_card_sensor(f_spi, "MAX6675 #4 (CS 14)", "Tina 4: Níquel (450W)", 3)

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

    def _refrescar_datos(self):
        if not self.running or not self.win.winfo_exists():
            return

        def _fetch():
            if self.app.modo_demo:
                res = {"aht": 1, "bmp": 1, "ads": 1, "dac": 1, "tc": [1, 1, 1, 1]}
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


# =================================================================================
# APLICACIÓN PRINCIPAL DE TELEMETRÍA Y GESTOR DE ENSAYOS
# =================================================================================
class TelemetriaApp:
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
        self.archivo_csv = None
        self.archivo_csv_errores = None
        self.carpeta_ensayo_actual = ""
        self.carpeta_graficas_actual = ""
        self.ultimo_csv_generado = ""
        self.tiempo_inicio = None
        self.muestras_count = 0

        # Balanza Gravimétrica y Ley de Faraday (m = Q*M / z*F)
        self.coulombs_total = 0.0
        self.coulombs_etapa = 0.0
        self.peso_inicial_g = 0.0
        self.peso_final_g = 0.0
        self.area_placa_cm2 = 65.0

        # Últimos valores calculados de actuadores y corriente
        self.ultimo_u1 = 0.0
        self.ultimo_u2 = 0.0
        self.ultimo_u3 = 0.0
        self.ultimo_u4 = 0.0
        self.ultimo_amps = 0.0

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
        self.filtro_actual = "TODOS"

        self._cargar_datos_excel()
        self._crear_interfaz()
        self._probar_conexion_silenciosa()
        self._iniciar_timer_etapa_loop()

    def _buscar_excel_defecto(self):
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        candidatos = [
            os.path.join(directorio_actual, "Hoja de resultados matriz de experimentos.xlsx"),
            os.path.join(directorio_actual, "..", "telemetria", "Hoja de resultados matriz de experimentos.xlsx"),
            os.path.join(directorio_actual, "..", "Hoja de resultados matriz de experimentos.xlsx"),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return os.path.abspath(c)
        return ""

    def _cargar_datos_excel(self, ruta_custom=None):
        ruta = ruta_custom or self.excel_path
        self.lista_placas = []
        if not ruta or not os.path.exists(ruta):
            for i in range(1, 33):
                self.lista_placas.append({
                    "num": i,
                    "ronda": "Ronda 1" if i <= 16 else "Ronda 2",
                    "limpieza_s": 240,
                    "matizado_s": 120,
                    "ph": 2 if i % 2 == 1 else 4,
                    "temp_zin": 25 if i <= 8 or (17 <= i <= 24) else 40,
                    "tiem_zin_s": 120 if i % 4 in (1, 2) else 300,
                    "pulsado": 1 if i % 2 == 0 else 0,
                    "tiem_niq_s": 600,
                    "tag_filtro": f"pH {2 if i % 2 == 1 else 4} — {25 if i <= 8 or (17 <= i <= 24) else 40}°C"
                })
            return

        try:
            wb = pd.ExcelFile(ruta)
            for sheet in wb.sheet_names:
                df = pd.read_excel(ruta, sheet_name=sheet)
                for _, row in df.iterrows():
                    p_val = row.get("Placas")
                    if pd.notna(p_val):
                        placa_num = int(p_val)
                        limp = row.get("Limpieza")
                        limp_s = 240 if (pd.isna(limp) or limp == "") else int(float(limp))
                        mat = row.get("Tiempo de mat.")
                        mat_s = 120 if (pd.isna(mat) or mat == "") else int(float(mat))
                        ph = row.get("pH")
                        ph_val = 2 if (pd.isna(ph) or ph == "") else int(float(ph))
                        temp_z = row.get("Temperatura de zin.")
                        temp_z_val = 25 if (pd.isna(temp_z) or temp_z == "") else int(float(temp_z))
                        tiem_z = row.get("Tiempo de zin.")
                        tiem_z_val = 120 if (pd.isna(tiem_z) or tiem_z == "") else int(float(tiem_z))
                        puls = row.get("Corriente Pul.")
                        puls_val = 0 if (pd.isna(puls) or puls == "") else int(float(puls))
                        tiem_niq = row.get("Tiem. Niquelado")
                        tiem_niq_val = 600 if (pd.isna(tiem_niq) or tiem_niq == "") else int(float(tiem_niq))

                        tag = f"pH {ph_val} — {temp_z_val}°C"

                        self.lista_placas.append({
                            "num": placa_num,
                            "ronda": sheet,
                            "limpieza_s": limp_s,
                            "matizado_s": mat_s,
                            "ph": ph_val,
                            "temp_zin": temp_z_val,
                            "tiem_zin_s": tiem_z_val,
                            "pulsado": puls_val,
                            "tiem_niq_s": tiem_niq_val,
                            "tag_filtro": tag
                        })
            self.excel_path = ruta
        except Exception as e:
            print(f"[AVISO] Error al leer Excel ({e}). Se usarán valores predeterminados.")

    def _crear_interfaz(self):
        # 1. Header / Barra superior
        hdr = tk.Frame(self.root, bg="#0f172a", height=54, bd=0)
        hdr.pack(fill="x", side="top")

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

        self.lbl_status = tk.Label(
            frame_ip,
            text="DESCONECTADO",
            font=("Segoe UI", 8, "bold"),
            fg="#64748b",
            bg="#0f172a",
        )
        self.lbl_status.pack(side="left", padx=4)

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

        self.progress_etapa = ttk.Progressbar(frame_clock_box, orient="horizontal", mode="determinate")
        self.progress_etapa.pack(fill="x", padx=6, pady=4)

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

        kpi_frame = tk.Frame(ctrl_frame, bg="#1e293b")
        kpi_frame.pack(side="right", padx=10, pady=6)

        self.lbl_time = tk.Label(kpi_frame, text="Tiempo: 00:00", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#1e293b")
        self.lbl_time.pack(side="left", padx=8)

        self.lbl_samples = tk.Label(kpi_frame, text="Muestras: 0", font=("Segoe UI", 9, "bold"), fg="#a78bfa", bg="#1e293b")
        self.lbl_samples.pack(side="left", padx=8)

        # 2. Tarjetas Rápidas de Sensores en Vivo con Indicadores de Gate TRIAC
        cards_bar = tk.Frame(panel_telemetria, bg="#0b1120")
        cards_bar.pack(fill="x", padx=2, pady=2)

        self.card_t1 = self._crear_card_tina(cards_bar, "T1: Limpieza", 450.0, "#d95f02", canal_idx=0)
        self.card_t2 = self._crear_card_tina(cards_bar, "T2: Decapado", 450.0, "#e6ab02", canal_idx=1)
        self.card_t3 = self._crear_card_tina(cards_bar, "T3: Celda Hull", 18.0, "#38bdf8", canal_idx=2)
        self.card_t4 = self._crear_card_tina(cards_bar, "T4: Níquel", 450.0, "#a78bfa", canal_idx=3)
        self.card_coulomb = self._crear_kpi_box(cards_bar, "Carga Q (Coulombs)", "0.0 C", "#f472b6", click_cmd=self.abrir_ventana_faraday)
        self.card_amp = self._crear_kpi_box(cards_bar, "Corriente (VCSS)", "0.00 A", "#22c55e", click_cmd=lambda: self.abrir_ventana_actuadores(4))
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
        f = tk.Frame(parent, bg="#1e293b", bd=0, padx=5, pady=3, cursor="hand2")
        f.pack(side="left", expand=True, fill="both", padx=2)
        lbl_h = tk.Label(f, text=f"{title} ({max_w:.0f}W)", font=("Segoe UI", 7, "bold"), fg="#94a3b8", bg="#1e293b", cursor="hand2")
        lbl_h.pack(anchor="w")
        lbl_temp = tk.Label(f, text="-- °C / SP --°C", font=("Segoe UI", 8, "bold"), fg=color, bg="#1e293b", cursor="hand2")
        lbl_temp.pack(anchor="w")
        lbl_gate = tk.Label(f, text="Gate: 0% (α=180°)", font=("Segoe UI", 7, "bold"), fg="#64748b", bg="#1e293b", cursor="hand2")
        lbl_gate.pack(anchor="w")
        lbl_w = tk.Label(f, text="0.0 W", font=("Segoe UI", 7), fg="#34d399", bg="#1e293b", cursor="hand2")
        lbl_w.pack(anchor="w")

        # Al hacer clic en cualquier parte de la tarjeta, abrir el osciloscopio en ese canal
        for widget in (f, lbl_h, lbl_temp, lbl_gate, lbl_w):
            widget.bind("<Button-1>", lambda e, c=canal_idx: self.abrir_ventana_actuadores(c))

        return {
            "frame": f,
            "temp": lbl_temp,
            "gate": lbl_gate,
            "watts": lbl_w
        }

    def _estilizar_axes(self):
        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_facecolor("#1e293b")
            ax.grid(True, linestyle=":", alpha=0.3, color="#475569")
            ax.tick_params(colors="#94a3b8", labelsize=7.5)
            for spine in ax.spines.values():
                spine.set_color("#334155")

        self.ax1.set_ylabel("Temp (°C)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
        self.ax2.set_ylabel("TRIACs (%)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
        self.ax3.set_ylabel("Corriente (A)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
        self.ax3.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
        self.fig.tight_layout(pad=0.8)

    def _aplicar_filtro(self, tag):
        self.filtro_actual = tag
        todos_btns = [
            (self.btn_f_all, "TODOS"),
            (self.btn_f_p2_25, "pH 2 — 25°C"),
            (self.btn_f_p2_40, "pH 2 — 40°C"),
            (self.btn_f_p4_25, "pH 4 — 25°C"),
            (self.btn_f_p4_40, "pH 4 — 40°C"),
        ]
        for btn, b_tag in todos_btns:
            btn.config(bg="#2563eb" if b_tag == tag else "#1e293b")
        self._actualizar_lista_combo()

    def _actualizar_lista_combo(self):
        filtradas = []
        for p in self.lista_placas:
            if self.filtro_actual == "TODOS" or p["tag_filtro"] == self.filtro_actual:
                pul_txt = "Zin: Pul 1.5A" if p["pulsado"] == 1 else "Zin: DC 1.5A"
                label = f"Placa {p['num']:02d} — {p['ronda']} | {p['tag_filtro']} | Zin: {p['tiem_zin_s']}s | {pul_txt}"
                filtradas.append((label, p))

        self.mapa_combo = {item[0]: item[1] for item in filtradas}
        self.combo_placas["values"] = [item[0] for item in filtradas]
        if filtradas:
            self.combo_placas.current(0)
            self._on_placa_seleccionada(None)
        else:
            self.combo_placas.set("Sin placas en este filtro")

    def _on_placa_seleccionada(self, event):
        sel_text = self.combo_placas.get()
        if sel_text not in self.mapa_combo:
            return
        self.placa_activa = self.mapa_combo[sel_text]
        p = self.placa_activa

        self.lbl_badge_ronda.config(text=f"🏷️ {p['ronda']} — Placa #{p['num']:02d}")
        self.lbl_badge_cond.config(text=f"🧪 pH Ref: {p['ph']}  |  🌡️ Zincado: {p['temp_zin']} °C ({p['tiem_zin_s']}s)")

        if p["pulsado"] == 1:
            self.lbl_badge_zin.config(text="⚡ Zincado: PULSADO 1.50 A @ 10Hz (20% Duty)", fg="#f472b6")
        else:
            self.lbl_badge_zin.config(text="⚡ Zincado: DC CONTINUO 1.50 A", fg="#34d399")

        self.lbl_badge_niq.config(text="⚡ Níquel: DC CONTINUO 1.13 A (600s / 10 min)", fg="#a78bfa")

        self.lbl_e1.config(text=f"Limpieza (T1): {p['limpieza_s']}s @ 85°C | 0.00A")
        self.lbl_e2.config(text=f"Decapado (T2): {p['matizado_s']}s @ 85°C | 0.00A")
        zin_modo = "Pul 1.5A" if p["pulsado"] == 1 else "DC 1.5A"
        self.lbl_e3.config(text=f"Zincado (T3): {p['tiem_zin_s']}s @ {p['temp_zin']}°C | {zin_modo}")
        self.lbl_e4.config(text=f"Niquelado (T4): {p['tiem_niq_s']}s @ 30°C | 1.13A DC (pH 5.5)")

        self.etapa_activa_idx = 0
        self.etapa_corriendo = False
        self._cargar_etapa_actual()

    def _obtener_datos_etapa_actual(self):
        if not self.placa_activa:
            return "Limpieza", 240, 85.0, 0.0, "OFF"
        p = self.placa_activa
        if self.etapa_activa_idx == 0:
            return "Limpieza Electrolítica (T1)", p["limpieza_s"], 85.0, 0.0, "OFF"
        elif self.etapa_activa_idx == 1:
            return "Decapado Ácido (T2)", p["matizado_s"], 85.0, 0.0, "OFF"
        elif self.etapa_activa_idx == 2:
            modo = "PULSADO" if p["pulsado"] == 1 else "DC"
            return "Zincado Químico / Celda (T3)", p["tiem_zin_s"], float(p["temp_zin"]), 1.50, modo
        else:
            return "Niquelado Watts (T4)", p["tiem_niq_s"], 30.0, 1.13, "DC"

    def _cargar_etapa_actual(self):
        nombre, duracion, sp_t, curr, modo = self._obtener_datos_etapa_actual()
        self.etapa_duracion_total = duracion
        self.etapa_segundos_restantes = duracion
        self.etapa_segundos_transcurridos = 0

        self.lbl_etapa_titulo.config(text=f"ETAPA {self.etapa_activa_idx + 1}/4: {nombre.upper()}")
        self._actualizar_display_reloj()
        self.btn_stage_toggle.config(text="▶ Iniciar Etapa", bg="#059669", activebackground="#10b981")
        self.lbl_aviso_etapa.config(text=f"Objetivo: SP Temp {sp_t:.0f}°C | Corriente: {curr:.2f}A ({modo})", fg="#94a3b8")

        if hasattr(self, 'btn_stage_prev'):
            self.btn_stage_prev.config(state="normal" if self.etapa_activa_idx > 0 else "disabled")

        if hasattr(self, 'lbl_hw_sync_status'):
            self.lbl_hw_sync_status.config(text=f"📡 SPs listos: {curr:.2f}A ({modo}) | T{self.etapa_activa_idx+1}:{sp_t:.0f}°C", fg="#94a3b8")

        filas = [self.lbl_e1, self.lbl_e2, self.lbl_e3, self.lbl_e4]
        for idx, f in enumerate(filas):
            if idx == self.etapa_activa_idx:
                f.config(fg="#38bdf8", font=("Segoe UI", 7, "bold"))
            elif idx < self.etapa_activa_idx:
                f.config(fg="#34d399", font=("Segoe UI", 7))
            else:
                f.config(fg="#64748b", font=("Segoe UI", 7))

    def _actualizar_display_reloj(self):
        mins = int(self.etapa_segundos_restantes // 60)
        segs = int(self.etapa_segundos_restantes % 60)
        self.lbl_timer_big.config(text=f"{mins:02d}:{segs:02d}")
        if self.etapa_duracion_total > 0:
            prog = ((self.etapa_duracion_total - self.etapa_segundos_restantes) / self.etapa_duracion_total) * 100
            self.progress_etapa["value"] = prog

    def toggle_etapa(self):
        if not self.etapa_corriendo:
            self.etapa_corriendo = True
            self.btn_stage_toggle.config(text="⏸ Pausar", bg="#d97706", activebackground="#f59e0b")
            self.lbl_timer_big.config(fg="#34d399")
            self.lbl_aviso_etapa.config(text="⏳ Etapa en progreso...", fg="#34d399")
            if hasattr(self, 'var_auto_sync_hw') and self.var_auto_sync_hw.get():
                self.enviar_setpoints_esp32(feedback_usuario=False)
            if not self.grabando:
                self.iniciar_grabacion()
        else:
            self.etapa_corriendo = False
            self.btn_stage_toggle.config(text="▶ Reanudar", bg="#059669", activebackground="#10b981")
            self.lbl_timer_big.config(fg="#fbbf24")
            self.lbl_aviso_etapa.config(text="⏸ Etapa en pausa.", fg="#fbbf24")

    def avanzar_siguiente_etapa(self):
        if self.etapa_activa_idx < 3:
            self.etapa_activa_idx += 1
            self.etapa_corriendo = False
            self._cargar_etapa_actual()
            if hasattr(self, 'var_auto_sync_hw') and self.var_auto_sync_hw.get():
                self.enviar_setpoints_esp32(feedback_usuario=False)
        else:
            self.etapa_corriendo = False
            reproducir_alarma_sonora("fin_ensayo")
            p_num = self.placa_activa.get("num", 1) if self.placa_activa else 1
            self.lbl_aviso_etapa.config(
                text=f"🏆 ¡ENSAYO FINALIZADO! Enjuague/seque la probeta y registre en '⚖️ Faraday / Balanza'.",
                fg="#34d399"
            )
            messagebox.showinfo(
                "Ensayo Finalizado",
                f"✅ ¡Ensayo de la Placa #{p_num:02d} completado con éxito!\n\n"
                f"• La fuente VCSS está apagada y la celda aislada con relé ZCS.\n"
                f"• Retire la probeta, enjuáguela con agua destilada y séquela.\n"
                f"• Cuando esté seca y pesada, ingrese los valores en '⚖️ Faraday / Balanza'."
            )

    def retroceder_etapa_anterior(self):
        if self.etapa_activa_idx > 0:
            self.etapa_activa_idx -= 1
            self.etapa_corriendo = False
            self._cargar_etapa_actual()
            if hasattr(self, 'var_auto_sync_hw') and self.var_auto_sync_hw.get():
                self.enviar_setpoints_esp32(feedback_usuario=False)

    def reiniciar_etapa_actual(self):
        self.etapa_corriendo = False
        self._cargar_etapa_actual()

    def enviar_setpoints_esp32(self, feedback_usuario=False):
        """
        Envía los setpoints de temperatura y corriente de la etapa y placa activas al ESP32.
        - Etapa 1 (Limpieza - T1): SP T1=85°C, Fuente OFF (0.00A)
        - Etapa 2 (Decapado - T2): SP T2=85°C, Fuente OFF (0.00A)
        - Etapa 3 (Zincado - T3): SP T3=(25°C o 40°C), Fuente ON a 1.50A (DC o Pulsado 10Hz/20% según receta)
        - Etapa 4 (Niquelado - T4): SP T4=30°C, Fuente ON a 1.13A DC continuo (pH 5.5)
        """
        nombre, dur, sp_t, curr_sp, modo_corr = self._obtener_datos_etapa_actual()
        p = self.placa_activa or {"num": 1, "temp_zin": 25, "pulsado": 0}

        if self.modo_demo:
            txt_demo = f"🎮 Modo Demo: SPs aplicados ({curr_sp:.2f}A {modo_corr} | T{self.etapa_activa_idx+1}:{sp_t:.0f}°C)"
            if hasattr(self, 'lbl_hw_sync_status'):
                self.lbl_hw_sync_status.config(text=txt_demo, fg="#fbbf24")
            if feedback_usuario:
                messagebox.showinfo("Modo Demo", f"En Modo Demo los setpoints se aplican virtualmente:\n\n• Etapa {self.etapa_activa_idx+1}: {nombre}\n• Corriente: {curr_sp:.2f} A ({modo_corr})\n• Temperatura T{self.etapa_activa_idx+1}: {sp_t:.1f} °C")
            return

        ip = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"

        def _sync_thread():
            try:
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text="⏳ Enviando parámetros a ESP32...", fg="#38bdf8"))
                base_url = f"http://{ip}"
                session = requests.Session()

                # 1. Configuración de la Fuente de Corriente (VCSS)
                if self.etapa_activa_idx in (0, 1):
                    # Etapas 1 y 2: Fuente apagada con ZCS y amplitud a 0
                    session.get(f"{base_url}/act_f?run=0", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v=0", timeout=1.5)
                    session.get(f"{base_url}/modo_f?v=0", timeout=1.5)
                elif self.etapa_activa_idx == 2:
                    # Etapa 3 (Zincado): 1.50 A (DAC = 930)
                    dac_val = int((1.50 / 6.6) * 4095.0)
                    es_pulsado = 1 if p.get("pulsado", 0) == 1 else 0
                    session.get(f"{base_url}/modo_f?v={es_pulsado}", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v={dac_val}", timeout=1.5)
                    if es_pulsado:
                        session.get(f"{base_url}/set_f?p=f&v=10", timeout=1.5)  # 10 Hz
                        session.get(f"{base_url}/set_f?p=d&v=20", timeout=1.5)  # 20% duty
                    session.get(f"{base_url}/act_f?run=1", timeout=1.5)
                elif self.etapa_activa_idx == 3:
                    # Etapa 4 (Niquelado Watts): DC 1.13 A continuo (DAC = 701)
                    dac_val = int((1.13 / 6.6) * 4095.0)
                    session.get(f"{base_url}/modo_f?v=0", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v={dac_val}", timeout=1.5)
                    session.get(f"{base_url}/act_f?run=1", timeout=1.5)

                # 2. Configuración del Setpoint Térmico del canal de la etapa actual
                canal_id = self.etapa_activa_idx
                session.get(f"{base_url}/set_t?id={canal_id}&v={sp_t:.1f}", timeout=1.5)

                txt_ok = f"🟢 ESP32 OK: {curr_sp:.2f}A ({modo_corr}) | T{canal_id+1}:{sp_t:.0f}°C"
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text=txt_ok, fg="#34d399"))
                if feedback_usuario:
                    msg = (
                        f"✅ Setpoints cargados con éxito en el ESP32 ({ip}):\n\n"
                        f"• Etapa {self.etapa_activa_idx + 1}/4: {nombre}\n"
                        f"• Consigna Corriente: {curr_sp:.2f} A ({modo_corr})\n"
                        f"• Consigna Térmica T{canal_id + 1}: {sp_t:.1f} °C"
                    )
                    self.root.after(0, lambda: messagebox.showinfo("Sincronización Exitosa", msg))
            except Exception as e:
                txt_err = f"🔴 Error ESP32: {str(e)[:28]}"
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text=txt_err, fg="#ef4444"))
                if feedback_usuario:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Error de Comunicación",
                        f"No se pudieron enviar los parámetros al ESP32 en http://{ip}\n\nDetalle: {e}\n\nVerifique la red Wi-Fi o active el 'Modo Demo'."
                    ))

        threading.Thread(target=_sync_thread, daemon=True).start()

    def probar_alarma(self):
        reproducir_alarma_sonora("test")

    def _iniciar_timer_etapa_loop(self):
        def _loop():
            if self.etapa_corriendo:
                if self.etapa_segundos_restantes > 0:
                    self.etapa_segundos_restantes -= 1
                    self.etapa_segundos_transcurridos += 1
                    self._actualizar_display_reloj()
                else:
                    self.etapa_corriendo = False
                    self.btn_stage_toggle.config(text="▶ Iniciar", bg="#059669")
                    self.lbl_timer_big.config(fg="#fbbf24")
                    nom_etapa, _, _, _, _ = self._obtener_datos_etapa_actual()

                    if self.etapa_activa_idx == 3:
                        # Finalización de la Etapa 4: Niquelado Watts (Fin de la Receta)
                        reproducir_alarma_sonora("fin_ensayo")
                        self.lbl_aviso_etapa.config(
                            text=f"🏆 ¡ENSAYO FINALIZADO! Retire/seque la probeta y registre en '⚖️ Faraday / Balanza'.",
                            fg="#34d399"
                        )
                    elif self.etapa_activa_idx == 2:
                        reproducir_alarma_sonora("fin_etapa")
                        self.lbl_aviso_etapa.config(
                            text=f"🔔 ¡{nom_etapa} FINALIZADA! Cambie la placa a Tina 4 (Níquel) y presione 'Siguiente'.",
                            fg="#fbbf24"
                        )
                    else:
                        reproducir_alarma_sonora("fin_etapa")
                        self.lbl_aviso_etapa.config(
                            text=f"🔔 ¡{nom_etapa} FINALIZADA! Cambie de tina y presione 'Siguiente'.",
                            fg="#fbbf24"
                        )
            self.root.after(1000, self._iniciar_timer_etapa_loop)

        self.root.after(1000, _loop)

    def cargar_archivo_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Matriz Experimental en Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta and os.path.exists(ruta):
            self._cargar_datos_excel(ruta)
            self.lbl_xl_info.config(text=f"📁 {len(self.lista_placas)} placas ({os.path.basename(ruta)[:18]}...)")
            self._actualizar_lista_combo()
            messagebox.showinfo("Excel Cargado", f"Se cargaron correctamente {len(self.lista_placas)} placas desde:\n{ruta}")

    def _on_toggle_demo(self):
        self.modo_demo = self.var_demo.get()
        if self.modo_demo:
            self.lbl_status.config(text="🎮 MODO DEMO", fg="#fbbf24")
            self.lbl_csv_info.config(text="Modo Simulación activo: Generando datos sintéticos realistas en telemetria/experimentos/.", fg="#fbbf24")
        else:
            self.demo_forzar_corriente = False
            self.btn_demo_curr.config(bg="#1e293b", fg="#94a3b8")
            self._probar_conexion_silenciosa()

    def _toggle_forzar_corriente_demo(self):
        if not self.modo_demo:
            self.var_demo.set(True)
            self._on_toggle_demo()
        self.demo_forzar_corriente = not self.demo_forzar_corriente
        if self.demo_forzar_corriente:
            self.btn_demo_curr.config(bg="#22c55e", fg="#0f172a", text="⚡ Corriente ON (1.5A)")
        else:
            self.btn_demo_curr.config(bg="#1e293b", fg="#94a3b8", text="⚡ Forzar Corriente")

    def _probar_conexion_silenciosa(self):
        if self.modo_demo:
            return
        ip = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"
        def _ping():
            try:
                r = requests.get(f"http://{ip}/data_env", timeout=1.5)
                if r.status_code == 200:
                    self.conectado = True
                    try:
                        self.root.after(0, lambda: self.lbl_status.config(text="🟢 EN LÍNEA", fg="#34d399"))
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            self.conectado = False
            try:
                self.root.after(0, lambda: self.lbl_status.config(text="🔴 DESCONECTADO", fg="#ef4444"))
            except Exception:
                pass

        threading.Thread(target=_ping, daemon=True).start()

    def probar_conexion_manual(self):
        if self.modo_demo:
            messagebox.showinfo("Modo Demo", "El Modo Simulación está activo. Desmárcalo para conectar con hardware real.")
            return
        ip = self.entry_ip.get().strip()
        try:
            r = requests.get(f"http://{ip}/data_env", timeout=2.0)
            if r.status_code == 200:
                self.conectado = True
                self.lbl_status.config(text="🟢 EN LÍNEA", fg="#34d399")
                messagebox.showinfo("Conexión Exitosa", f"Conectado correctamente al ESP32 ({ip}).")
                return
        except Exception:
            self.conectado = False
            self.lbl_status.config(text="🔴 DESCONECTADO", fg="#ef4444")
            messagebox.showwarning(
                "Sin Conexión",
                f"No se pudo conectar a http://{ip}\n\n1. Verifica Wi-Fi 'Uli' (Pass: 12345678).\n2. Si deseas probar sin hardware, activa '🎮 Modo Demo'."
            )

    def toggle_grabacion(self):
        if not self.grabando:
            self.iniciar_grabacion()
        else:
            self.detener_grabacion()

    def iniciar_grabacion(self):
        self.ip_grabacion = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        p_num = self.placa_activa["num"] if self.placa_activa else 1
        r_name = str(self.placa_activa["ronda"]).replace(" ", "_") if self.placa_activa else "Manual"

        # Crear carpeta dedicada estructurada por ensayo
        self.carpeta_ensayo_actual = os.path.join(self.carpeta_experimentos, f"Ensayo_P{p_num:02d}_{r_name}_{timestamp_str}")
        self.carpeta_graficas_actual = os.path.join(self.carpeta_ensayo_actual, "graficas")
        os.makedirs(self.carpeta_graficas_actual, exist_ok=True)

        self.archivo_csv = os.path.join(self.carpeta_ensayo_actual, "telemetria_completa.csv")
        self.archivo_csv_errores = os.path.join(self.carpeta_ensayo_actual, "metricas_control_errores.csv")
        self.ultimo_csv_generado = self.archivo_csv

        # Crear archivo resumen técnico de la receta
        resumen_txt_path = os.path.join(self.carpeta_ensayo_actual, "resumen_receta.txt")
        try:
            with open(resumen_txt_path, "w", encoding="utf-8") as f_res:
                p = self.placa_activa or {"num": 1, "ronda": "Ronda 1", "ph": 2, "temp_zin": 25, "tiem_zin_s": 120, "pulsado": 0}
                f_res.write("========================================================================\n")
                f_res.write(f"FICHA TÉCNICA DE RECETA ISA-88 — ENSAYO PLACA #{p.get('num', 1):02d}\n")
                f_res.write("========================================================================\n")
                f_res.write(f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_res.write(f"Ronda / Bloque: {p.get('ronda')}\n")
                f_res.write(f"pH de Referencia Inicial: {p.get('ph')}\n")
                f_res.write(f"Etapa 1 - Limpieza: 240s @ 85°C (0.00 A)\n")
                f_res.write(f"Etapa 2 - Decapado: {p.get('matizado_s', 120)}s @ 85°C (0.00 A)\n")
                f_res.write(f"Etapa 3 - Zincado: {p.get('tiem_zin_s', 120)}s @ {p.get('temp_zin', 25)}°C | 1.50 A ({'Pulsado 10Hz 20%' if p.get('pulsado')==1 else 'DC'})\n")
                f_res.write(f"Etapa 4 - Niquelado Watts: {p.get('tiem_niq_s', 600)}s (10 min) @ 30°C | 1.13 A DC (pH ref ~5.5)\n")
                f_res.write("========================================================================\n")
        except Exception:
            pass

        try:
            # 1. CSV Principal de Telemetría (Compatible v3.1 / v3.5 con shunts y lazo cerrado)
            self.csv_file_handle = open(self.archivo_csv, mode="w", newline="", encoding="utf-8")
            self.csv_writer = csv.writer(self.csv_file_handle)

            headers_tel = [
                "Timestamp_ISO", "Tiempo_Relativo_s",
                "Placa_ID", "Ronda", "Etapa_Num", "Etapa_Nombre", "Etapa_Tiempo_s", "Etapa_Duracion_s",
                "Corriente_Target_A", "Modo_Corriente", "Temp_SP_Target_C",
                # Canal Térmico y TRIAC 1 (Limpieza - 450W)
                "T1_Limpieza_Temp_C", "T1_Limpieza_SP_C", "T1_Limpieza_Activo",
                "T1_TRIAC_Potencia_Pct", "T1_TRIAC_Alpha_Deg", "T1_TRIAC_Delay_us", "T1_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 2 (Decapado - 450W)
                "T2_Decapado_Temp_C", "T2_Decapado_SP_C", "T2_Decapado_Activo",
                "T2_TRIAC_Potencia_Pct", "T2_TRIAC_Alpha_Deg", "T2_TRIAC_Delay_us", "T2_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 3 (Celda Hull - 18W)
                "T3_CeldaHull_Temp_C", "T3_CeldaHull_SP_C", "T3_CeldaHull_Activo",
                "T3_TRIAC_Potencia_Pct", "T3_TRIAC_Alpha_Deg", "T3_TRIAC_Delay_us", "T3_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 4 (Niquelado - 450W)
                "T4_Niquelado_Temp_C", "T4_Niquelado_SP_C", "T4_Niquelado_Activo",
                "T4_TRIAC_Potencia_Pct", "T4_TRIAC_Alpha_Deg", "T4_TRIAC_Delay_us", "T4_TRIAC_Watts_W",
                # Módulo pH Dual
                "pH_Tina1", "pH_Tina2", "pH_Modulo_Activo",
                "pH_Modo_Cal_T1", "pH_Modo_Cal_T2",
                "pH_Slope_Pct_T1", "pH_Slope_Pct_T2", "pH_Interlock_Activo",
                # Fuente de Corriente Galvánica Lazo Cerrado v3.5
                "Fuente_Activa", "Fuente_Modo_Pulsado",
                "Fuente_Corriente_Consigna_A", "Fuente_Corriente_Real_A",
                "Fuente_Corriente_Shunt1_A", "Fuente_Corriente_Shunt2_A",
                "Fuente_Voltaje_Shunt1_V", "Fuente_Voltaje_Shunt2_V",
                "Fuente_Factor_Gm", "Fuente_Compensacion_Activa", "Fuente_Rele_VDD",
                "Fuente_Amplitud_DAC", "Fuente_Frecuencia_Hz", "Fuente_DutyCycle_Pct",
                # Ley de Faraday y Culombimetría
                "Carga_Acumulada_Coulombs", "Masa_Teorica_Faraday_mg",
                # Condiciones Ambientales
                "Ambiente_Temp_C", "Ambiente_Humedad_Pct", "Ambiente_Presion_hPa"
            ]
            self.csv_writer.writerow(headers_tel)
            self.csv_file_handle.flush()

            # 2. CSV Especializado de Métricas de Error y Control
            self.csv_err_handle = open(self.archivo_csv_errores, mode="w", newline="", encoding="utf-8")
            self.csv_err_writer = csv.writer(self.csv_err_handle)
            headers_err = [
                "Timestamp_ISO", "Tiempo_Relativo_s",
                "Etapa_Num", "Etapa_Nombre",
                "Error_T1_C", "Error_T2_C", "Error_T3_C", "Error_T4_C", "Error_Corriente_A",
                "IAE_T1", "IAE_T2", "IAE_T3", "IAE_T4", "IAE_Corriente",
                "Esfuerzo_u1_Pct", "Esfuerzo_u2_Pct", "Esfuerzo_u3_Pct", "Esfuerzo_u4_Pct"
            ]
            self.csv_err_writer.writerow(headers_err)
            self.csv_err_handle.flush()

        except Exception as e:
            messagebox.showerror("Error de Archivo", f"No se pudieron crear los archivos CSV del ensayo:\n{e}")
            return

        self.grabando = True
        self.tiempo_inicio = time.time()
        self.muestras_count = 0

        # Reiniciar acumuladores IAE y Culombimetría
        self.iae_t1 = 0.0
        self.iae_t2 = 0.0
        self.iae_t3 = 0.0
        self.iae_t4 = 0.0
        self.iae_curr = 0.0
        self.coulombs_total = 0.0
        self.coulombs_etapa = 0.0

        # Limpiar buffers
        self.buf_t.clear()
        self.buf_t1.clear()
        self.buf_t1_sp.clear()
        self.buf_t2.clear()
        self.buf_t2_sp.clear()
        self.buf_t3.clear()
        self.buf_t3_sp.clear()
        self.buf_t4.clear()
        self.buf_t4_sp.clear()
        self.buf_u1.clear()
        self.buf_u2.clear()
        self.buf_u3.clear()
        self.buf_u4.clear()
        self.buf_curr.clear()
        self.buf_curr_avg.clear()
        self.buf_ph1.clear()
        self.buf_ph2.clear()
        self.buf_ph_on.clear()

        self.btn_rec.config(text="⏹ DETENER GRABACIÓN", bg="#dc2626", activebackground="#ef4444")
        self.lbl_csv_info.config(text=f"💾 Guardando en: experimentos/{os.path.basename(self.carpeta_ensayo_actual)}/", fg="#34d399")

        self.hilo_muestreo = threading.Thread(target=self._bucle_adquisicion, daemon=True)
        self.hilo_muestreo.start()

    def detener_grabacion(self):
        self.grabando = False
        if self.csv_file_handle:
            try:
                self.csv_file_handle.close()
            except Exception:
                pass
            self.csv_file_handle = None

        if self.csv_err_handle:
            try:
                self.csv_err_handle.close()
            except Exception:
                pass
            self.csv_err_handle = None

        self.btn_rec.config(text="▶ INICIAR GRABACIÓN", bg="#059669", activebackground="#10b981")
        self.lbl_csv_info.config(text=f"✅ Ensayo cerrado en: {os.path.basename(self.carpeta_ensayo_actual)}/ ({self.muestras_count} muestras)", fg="#fbbf24")

    def _generar_datos_simulados(self, t_rel):
        sp1, sp2 = 85.0, 85.0
        p = self.placa_activa or {"temp_zin": 25, "ph": 2, "pulsado": 0}
        sp3 = float(p.get("temp_zin", 25))
        sp4 = 30.0

        tau = 80.0
        factor = 1.0 - math.exp(-t_rel / tau)
        t1 = 24.0 + (sp1 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t2 = 24.0 + (sp2 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t3 = 24.0 + (sp3 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t4 = 24.0 + (sp4 - 24.0) * factor + random.uniform(-0.15, 0.15)

        # Simular potencia TRIAC %
        u1_sim = int(max(0, min(100, (sp1 - t1) * 15.0 + 20.0)))
        u2_sim = int(max(0, min(100, (sp2 - t2) * 15.0 + 20.0)))
        u3_sim = int(max(0, min(100, (sp3 - t3) * 15.0 + 20.0)))
        u4_sim = int(max(0, min(100, (sp4 - t4) * 15.0 + 20.0)))

        d_t = [
            {"t": round(t1, 1), "sp": sp1, "p": u1_sim, "run": 1},
            {"t": round(t2, 1), "sp": sp2, "p": u2_sim, "run": 1},
            {"t": round(t3, 1), "sp": sp3, "p": u3_sim, "run": 1},
            {"t": round(t4, 1), "sp": sp4, "p": u4_sim, "run": 1}
        ]

        ph_target = float(p.get("ph", 2))
        d_ph = {
            "p1": round(ph_target + random.uniform(-0.04, 0.04), 2),
            "p2": round(4.20 + random.uniform(-0.03, 0.03), 2),
            "on": 1,
            "m1": 2,
            "m2": 2,
            "sl1": 98.4,
            "sl2": 97.8,
            "il": 0
        }

        if (self.etapa_corriendo and self.etapa_activa_idx in (2, 3)) or self.demo_forzar_corriente:
            curr_target = 1.50 if (self.etapa_activa_idx == 2 or self.demo_forzar_corriente) else 1.13
            modo_pul = p.get("pulsado", 0) if self.etapa_activa_idx == 2 else 0
            i_real_sim = round(curr_target + random.uniform(-0.02, 0.02), 3)
            i1_sim = round(i_real_sim * 0.502, 3)
            i2_sim = round(i_real_sim * 0.498, 3)
            d_f = {
                "act": 1,
                "modo": modo_pul,
                "amps": curr_target,
                "i_real": i_real_sim,
                "i1": i1_sim,
                "i2": i2_sim,
                "vs1": round(i1_sim * 0.15, 3),
                "vs2": round(i2_sim * 0.15, 3),
                "gm": 1.005,
                "comp": 1,
                "rele": 1,
                "amp": int(curr_target * 500),
                "sp": int(curr_target * 500),
                "freq": 10 if modo_pul == 1 else 0,
                "duty": 20 if modo_pul == 1 else 0
            }
        else:
            d_f = {
                "act": 0,
                "modo": 0,
                "amps": 0.0,
                "i_real": 0.0,
                "i1": 0.0,
                "i2": 0.0,
                "vs1": 0.0,
                "vs2": 0.0,
                "gm": 1.000,
                "comp": 0,
                "rele": 0,
                "amp": 0,
                "sp": 0,
                "freq": 0,
                "duty": 0
            }

        d_env = {
            "t": round(23.5 + random.uniform(-0.2, 0.2), 1),
            "h": round(58.0 + random.uniform(-0.5, 0.5), 1),
            "p": 1013.2
        }
        return d_t, d_ph, d_f, d_env

    def _bucle_adquisicion(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "TelemetriaGUI/3.5"})
        ip = getattr(self, 'ip_grabacion', '192.168.4.1')
        base_url = f"http://{ip}"

        # Caché para resiliencia ante jitter Wi-Fi
        ultimo_d_t = [
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0}
        ]
        ultimo_d_ph = {"p1": 7.0, "p2": 7.0, "on": 0, "m1": 0, "m2": 0, "sl1": 100.0, "sl2": 100.0, "il": 0}
        ultimo_d_f = {"act": 0, "modo": 0, "amps": 0.0, "i_real": 0.0, "i1": 0.0, "i2": 0.0, "vs1": 0.0, "vs2": 0.0, "gm": 1.0, "comp": 0, "rele": 0, "amp": 0, "freq": 0, "duty": 0}
        ultimo_d_env = {"t": "24.0", "h": "50", "p": "1013.2"}

        while self.grabando:
            t_ciclo_inicio = time.time()
            t_rel = round(t_ciclo_inicio - self.tiempo_inicio, 1)
            t_iso = datetime.now().isoformat(timespec="seconds")

            d_t, d_ph, d_f, d_env = None, None, None, None

            if self.modo_demo:
                d_t, d_ph, d_f, d_env = self._generar_datos_simulados(t_rel)
                self.conectado = True
                ultimo_d_t, ultimo_d_ph, ultimo_d_f, ultimo_d_env = d_t, d_ph, d_f, d_env
            else:
                any_success = False
                # 1. RUTA RÁPIDA OPTIMIZADA: Endpoint unificado /data_all (RTOS 1.0)
                try:
                    r_all = session.get(f"{base_url}/data_all", timeout=0.8)
                    if r_all.status_code == 200:
                        d_all = r_all.json()
                        d_t = d_all.get("t")
                        d_ph = d_all.get("ph")
                        d_f = d_all.get("f")
                        d_env = d_all.get("env")
                        ultimo_d_t, ultimo_d_ph, ultimo_d_f, ultimo_d_env = d_t, d_ph, d_f, d_env
                        any_success = True
                except Exception:
                    pass

                # 2. FALLBACK RETROCOMPATIBLE (Si el firmware no soporta /data_all)
                if not any_success:
                    try:
                        r_t = session.get(f"{base_url}/data_t", timeout=0.8)
                        if r_t.status_code == 200:
                            d_t = r_t.json()
                            ultimo_d_t = d_t
                            any_success = True
                    except Exception:
                        d_t = ultimo_d_t

                    try:
                        r_ph = session.get(f"{base_url}/get_ph_dual", timeout=0.8)
                        if r_ph.status_code == 200:
                            d_ph = r_ph.json()
                            ultimo_d_ph = d_ph
                            any_success = True
                    except Exception:
                        d_ph = ultimo_d_ph

                    try:
                        r_f = session.get(f"{base_url}/data_f", timeout=0.8)
                        if r_f.status_code == 200:
                            d_f = r_f.json()
                            ultimo_d_f = d_f
                            any_success = True
                    except Exception:
                        d_f = ultimo_d_f

                    try:
                        r_env = session.get(f"{base_url}/data_env", timeout=0.8)
                        if r_env.status_code == 200:
                            d_env = r_env.json()
                            ultimo_d_env = d_env
                            any_success = True
                    except Exception:
                        d_env = ultimo_d_env

                self.conectado = any_success
                d_t = d_t or ultimo_d_t
                d_ph = d_ph or ultimo_d_ph
                d_f = d_f or ultimo_d_f
                d_env = d_env or ultimo_d_env

            if d_t and d_ph and d_f and d_env:
                nom_etapa, dur_etapa, sp_target, curr_target, modo_corr = self._obtener_datos_etapa_actual()
                placa_id = self.placa_activa["num"] if self.placa_activa else ""
                ronda_id = self.placa_activa["ronda"] if self.placa_activa else ""

                # Extracción robusta de campos v3.1 / v3.5
                i_consigna = float(d_f.get("amps", 0.0))
                i_medida_real = float(d_f.get("i_real", i_consigna))
                i_shunt1 = float(d_f.get("i1", i_medida_real * 0.5))
                i_shunt2 = float(d_f.get("i2", i_medida_real * 0.5))
                v_shunt1 = float(d_f.get("vs1", 0.0))
                v_shunt2 = float(d_f.get("vs2", 0.0))
                factor_gm = float(d_f.get("gm", 1.0))
                comp_activa = int(d_f.get("comp", 0))
                rele_vdd = int(d_f.get("rele", 0))

                # Calcular Errores e IAE
                e1 = float(d_t[0]["sp"]) - float(d_t[0]["t"])
                e2 = float(d_t[1]["sp"]) - float(d_t[1]["t"])
                e3 = float(d_t[2]["sp"]) - float(d_t[2]["t"])
                e4 = float(d_t[3]["sp"]) - float(d_t[3]["t"])
                e_i = curr_target - i_medida_real

                self.iae_t1 += abs(e1) * 1.0
                self.iae_t2 += abs(e2) * 1.0
                self.iae_t3 += abs(e3) * 1.0
                self.iae_t4 += abs(e4) * 1.0
                self.iae_curr += abs(e_i) * 1.0

                # Obtener potencia de disparo del ESP32 (o estimarla)
                u1 = float(d_t[0].get("p", min(100.0, max(0.0, e1 * 15.0 + 25.0)) if d_t[0]["run"] == 1 else 0.0))
                u2 = float(d_t[1].get("p", min(100.0, max(0.0, e2 * 15.0 + 25.0)) if d_t[1]["run"] == 1 else 0.0))
                u3 = float(d_t[2].get("p", min(100.0, max(0.0, e3 * 15.0 + 25.0)) if d_t[2]["run"] == 1 else 0.0))
                u4 = float(d_t[3].get("p", min(100.0, max(0.0, e4 * 15.0 + 25.0)) if d_t[3]["run"] == 1 else 0.0))

                self.ultimo_u1 = u1
                self.ultimo_u2 = u2
                self.ultimo_u3 = u3
                self.ultimo_u4 = u4
                self.ultimo_amps = i_medida_real

                # Calcular variables de conmutación de fase y potencia de los TRIACs
                p1_pct, a1_deg, d1_us, w1 = calcular_disparo_triac(u1, 450.0)
                p2_pct, a2_deg, d2_us, w2 = calcular_disparo_triac(u2, 450.0)
                p3_pct, a3_deg, d3_us, w3 = calcular_disparo_triac(u3, 18.0)
                p4_pct, a4_deg, d4_us, w4 = calcular_disparo_triac(u4, 450.0)

                # Integración Culombimétrica Faradaica Q = ∫ I dt
                if i_medida_real > 0.005:
                    self.coulombs_total += i_medida_real * 1.0
                    self.coulombs_etapa += i_medida_real * 1.0

                metal_eq = 0.3388 if self.etapa_activa_idx == 2 else (0.3041 if self.etapa_activa_idx == 3 else 0.3388)
                m_teo_instantanea = self.coulombs_total * metal_eq

                # Fila de Telemetría Completa v3.5
                fila_tel = [
                    t_iso, t_rel,
                    placa_id, ronda_id, self.etapa_activa_idx + 1, nom_etapa,
                    self.etapa_segundos_transcurridos, dur_etapa,
                    curr_target, modo_corr, sp_target,
                    # T1 y TRIAC 1
                    d_t[0]["t"], d_t[0]["sp"], d_t[0]["run"],
                    p1_pct, a1_deg, d1_us, w1,
                    # T2 y TRIAC 2
                    d_t[1]["t"], d_t[1]["sp"], d_t[1]["run"],
                    p2_pct, a2_deg, d2_us, w2,
                    # T3 y TRIAC 3
                    d_t[2]["t"], d_t[2]["sp"], d_t[2]["run"],
                    p3_pct, a3_deg, d3_us, w3,
                    # T4 y TRIAC 4
                    d_t[3]["t"], d_t[3]["sp"], d_t[3]["run"],
                    p4_pct, a4_deg, d4_us, w4,
                    # pH
                    d_ph["p1"], d_ph["p2"], d_ph["on"],
                    d_ph["m1"], d_ph["m2"],
                    d_ph["sl1"], d_ph["sl2"], d_ph["il"],
                    # Fuente
                    d_f["act"], d_f["modo"],
                    i_consigna, i_medida_real,
                    i_shunt1, i_shunt2,
                    v_shunt1, v_shunt2,
                    factor_gm, comp_activa, rele_vdd,
                    d_f.get("amp", 0), d_f.get("freq", 0), d_f.get("duty", 0),
                    # Ley de Faraday y Culombimetría
                    round(self.coulombs_total, 2), round(m_teo_instantanea, 2),
                    # Ambiente
                    d_env.get("t", "--"), d_env.get("h", "--"), d_env.get("p", "--")
                ]

                # Fila de Métricas de Error
                fila_err = [
                    t_iso, t_rel,
                    self.etapa_activa_idx + 1, nom_etapa,
                    round(e1, 2), round(e2, 2), round(e3, 2), round(e4, 2), round(e_i, 3),
                    round(self.iae_t1, 1), round(self.iae_t2, 1), round(self.iae_t3, 1), round(self.iae_t4, 1), round(self.iae_curr, 2),
                    round(self.ultimo_u1, 1), round(self.ultimo_u2, 1), round(self.ultimo_u3, 1), round(self.ultimo_u4, 1)
                ]

                # Escribir a CSVs
                if self.csv_file_handle and not self.csv_file_handle.closed:
                    try:
                        self.csv_writer.writerow(fila_tel)
                        self.csv_file_handle.flush()
                        self.muestras_count += 1
                    except Exception:
                        pass

                if self.csv_err_handle and not self.csv_err_handle.closed:
                    try:
                        self.csv_err_writer.writerow(fila_err)
                        self.csv_err_handle.flush()
                    except Exception:
                        pass

                try:
                    self.root.after(0, self._actualizar_gui_datos, t_rel, d_t, d_ph, d_f, d_env)
                except Exception:
                    pass

            t_espera = 1.0 - (time.time() - t_ciclo_inicio)
            if t_espera > 0:
                time.sleep(t_espera)

    def _actualizar_gui_datos(self, t_rel, d_t, d_ph, d_f, d_env):
        if self.modo_demo:
            self.lbl_status.config(text="🎮 MODO DEMO", fg="#fbbf24")
        else:
            self.lbl_status.config(text="🟢 EN LÍNEA" if self.conectado else "🔴 RECONECTANDO", fg="#34d399" if self.conectado else "#ef4444")

        mins = int(t_rel // 60)
        segs = int(t_rel % 60)
        self.lbl_time.config(text=f"Tiempo: {mins:02d}:{segs:02d}")
        self.lbl_samples.config(text=f"Muestras: {self.muestras_count}")

        # Calcular parámetros de actuadores y TRIACs en tiempo real
        u1 = float(d_t[0].get("p", min(100.0, max(0.0, (float(d_t[0]["sp"]) - float(d_t[0]["t"])) * 15.0 + 25.0)) if d_t[0]["run"] == 1 else 0.0))
        u2 = float(d_t[1].get("p", min(100.0, max(0.0, (float(d_t[1]["sp"]) - float(d_t[1]["t"])) * 15.0 + 25.0)) if d_t[1]["run"] == 1 else 0.0))
        u3 = float(d_t[2].get("p", min(100.0, max(0.0, (float(d_t[2]["sp"]) - float(d_t[2]["t"])) * 15.0 + 25.0)) if d_t[2]["run"] == 1 else 0.0))
        u4 = float(d_t[3].get("p", min(100.0, max(0.0, (float(d_t[3]["sp"]) - float(d_t[3]["t"])) * 15.0 + 25.0)) if d_t[3]["run"] == 1 else 0.0))

        p1, a1, dl1, w1 = calcular_disparo_triac(u1, 450.0)
        p2, a2, dl2, w2 = calcular_disparo_triac(u2, 450.0)
        p3, a3, dl3, w3 = calcular_disparo_triac(u3, 18.0)
        p4, a4, dl4, w4 = calcular_disparo_triac(u4, 450.0)

        es_pulsado = (int(d_f.get("modo", 0)) == 1)
        duty_val = int(d_f.get("duty", 20))
        freq_val = int(d_f.get("freq", 10))
        amps_val = float(d_f.get("i_real", d_f.get("amps", 0.0)))
        rele_activo = (d_f.get("rele", 0) == 1)

        i_pico = amps_val
        i_prom = (i_pico * (duty_val / 100.0)) if es_pulsado else amps_val

        # Guardar últimos valores para osciloscopio y ventanas hijas
        self.ultimo_u1 = u1
        self.ultimo_u2 = u2
        self.ultimo_u3 = u3
        self.ultimo_u4 = u4
        self.ultimo_df = d_f
        self.ultimo_amps = amps_val

        # Actualizar Tarjetas de Tinas con Temperatura + Disparo de Gate TRIAC y Watts
        self.card_t1["temp"].config(text=f"{float(d_t[0]['t']):.1f}°C / SP {float(d_t[0]['sp']):.0f}°C")
        self.card_t1["gate"].config(text=f"Gate: {p1:.0f}% (α={a1:.0f}°, {dl1}µs)", fg="#38bdf8" if p1 > 0 else "#64748b")
        self.card_t1["watts"].config(text=f"{w1:.1f} W / 450W", fg="#34d399" if p1 > 0 else "#64748b")

        self.card_t2["temp"].config(text=f"{float(d_t[1]['t']):.1f}°C / SP {float(d_t[1]['sp']):.0f}°C")
        self.card_t2["gate"].config(text=f"Gate: {p2:.0f}% (α={a2:.0f}°, {dl2}µs)", fg="#38bdf8" if p2 > 0 else "#64748b")
        self.card_t2["watts"].config(text=f"{w2:.1f} W / 450W", fg="#34d399" if p2 > 0 else "#64748b")

        self.card_t3["temp"].config(text=f"{float(d_t[2]['t']):.1f}°C / SP {float(d_t[2]['sp']):.0f}°C")
        self.card_t3["gate"].config(text=f"Gate: {p3:.0f}% (α={a3:.0f}°, {dl3}µs)", fg="#38bdf8" if p3 > 0 else "#64748b")
        self.card_t3["watts"].config(text=f"{w3:.1f} W / 18W", fg="#34d399" if p3 > 0 else "#64748b")

        self.card_t4["temp"].config(text=f"{float(d_t[3]['t']):.1f}°C / SP {float(d_t[3]['sp']):.0f}°C")
        self.card_t4["gate"].config(text=f"Gate: {p4:.0f}% (α={a4:.0f}°, {dl4}µs)", fg="#38bdf8" if p4 > 0 else "#64748b")
        self.card_t4["watts"].config(text=f"{w4:.1f} W / 450W", fg="#34d399" if p4 > 0 else "#64748b")

        ph_activo = (d_ph.get("on") == 1)

        # Tarjeta Culombimétrica Q (Faraday)
        self.card_coulomb.config(text=f"{self.coulombs_total:.1f} C")

        if es_pulsado and amps_val > 0.05:
            self.card_amp.config(text=f"{i_pico:.2f}A Pk | {i_prom:.2f}A Pr")
        else:
            self.card_amp.config(text=f"{amps_val:.2f} A")
        self.card_env.config(text=f"{d_env.get('t', '--')}° / {d_env.get('h', '--')}%")

        if (self.etapa_corriendo and self.etapa_activa_idx in (2, 3)) or (self.modo_demo and self.demo_forzar_corriente):
            if self.etapa_activa_idx == 2 or (self.modo_demo and self.demo_forzar_corriente):
                target_i = 1.50
                nombre_op = "Zincado"
            else:
                target_i = 1.13
                nombre_op = "Niquelado"

            diff = abs(amps_val - target_i)
            i1 = float(d_f.get("i1", amps_val * 0.5))
            i2 = float(d_f.get("i2", amps_val * 0.5))
            if es_pulsado:
                if diff <= 0.08:
                    self.lbl_stab_val.config(
                        text=f"{nombre_op} Pulsado {freq_val}Hz: {i_pico:.2f}A Pico (Shunts: {i1:.2f}A / {i2:.2f}A) | {i_prom:.2f}A Prom — Estable (Q: {self.coulombs_total:.1f}C)",
                        fg="#34d399"
                    )
                else:
                    self.lbl_stab_val.config(
                        text=f"{nombre_op} Pulsado {freq_val}Hz: {i_pico:.2f}A Pico (Obj: {target_i:.2f}A) | {i_prom:.2f}A Prom",
                        fg="#fbbf24"
                    )
            else:
                if diff <= 0.08:
                    self.lbl_stab_val.config(
                        text=f"{nombre_op} DC: {amps_val:.2f}A (Shunts: {i1:.2f}A / {i2:.2f}A) — Estable (Q: {self.coulombs_total:.1f}C)",
                        fg="#34d399"
                    )
                else:
                    self.lbl_stab_val.config(
                        text=f"{nombre_op} DC: {amps_val:.2f}A (Obj: {target_i:.2f}A) — Ajustando Lazo",
                        fg="#fbbf24"
                    )
        else:
            self.lbl_stab_val.config(text=f"En reposo / Etapa {self.etapa_activa_idx + 1} ({amps_val:.2f} A | Q={self.coulombs_total:.1f}C)", fg="#94a3b8")

        # Buffers
        t_min = t_rel / 60.0
        self.buf_t.append(t_min)
        self.buf_t1.append(float(d_t[0]["t"]))
        self.buf_t1_sp.append(float(d_t[0]["sp"]))
        self.buf_t2.append(float(d_t[1]["t"]))
        self.buf_t2_sp.append(float(d_t[1]["sp"]))
        self.buf_t3.append(float(d_t[2]["t"]))
        self.buf_t3_sp.append(float(d_t[2]["sp"]))
        self.buf_t4.append(float(d_t[3]["t"]))
        self.buf_t4_sp.append(float(d_t[3]["sp"]))
        self.buf_u1.append(p1)
        self.buf_u2.append(p2)
        self.buf_u3.append(p3)
        self.buf_u4.append(p4)
        self.buf_curr.append(i_pico)
        self.buf_curr_avg.append(i_prom)
        self.buf_q.append(self.coulombs_total)
        self.buf_m_teo.append(self.coulombs_total * (0.3388 if self.etapa_activa_idx == 2 else (0.3041 if self.etapa_activa_idx == 3 else 0.3388)))
        self.buf_ph1.append(float(d_ph["p1"]) if ph_activo else None)
        self.buf_ph2.append(float(d_ph["p2"]) if ph_activo else None)
        self.buf_ph_on.append(ph_activo)

        if len(self.buf_t) > self.max_muestras_plot:
            self.buf_t.pop(0)
            self.buf_t1.pop(0)
            self.buf_t1_sp.pop(0)
            self.buf_t2.pop(0)
            self.buf_t2_sp.pop(0)
            self.buf_t3.pop(0)
            self.buf_t3_sp.pop(0)
            self.buf_t4.pop(0)
            self.buf_t4_sp.pop(0)
            self.buf_u1.pop(0)
            self.buf_u2.pop(0)
            self.buf_u3.pop(0)
            self.buf_u4.pop(0)
            self.buf_curr.pop(0)
            self.buf_curr_avg.pop(0)
            self.buf_q.pop(0)
            self.buf_m_teo.pop(0)
            self.buf_ph1.pop(0)
            self.buf_ph2.pop(0)
            self.buf_ph_on.pop(0)

        # Redibujar gráfica en vivo
        if self.muestras_count % 2 == 0:
            self._redibujar_grafica_vivo()

        # Actualizar ventanas secundarias si están abiertas
        if self.win_actuadores is not None and self.win_actuadores.win.winfo_exists():
            self.win_actuadores.actualizar_datos()

        if self.win_errores is not None and self.win_errores.win.winfo_exists():
            self.win_errores.actualizar_datos()

        if self.win_faraday is not None and self.win_faraday.win.winfo_exists():
            self.win_faraday.actualizar_datos()

    def _redibujar_grafica_vivo(self):
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self._estilizar_axes()

        if not self.buf_t:
            self.canvas.draw_idle()
            return

        # Subplot 1: Térmico
        self.ax1.plot(self.buf_t, self.buf_t1, color="#d95f02", ls="-", lw=1.8, zorder=2, label="T1: Limpieza [—]")
        self.ax1.plot(self.buf_t, self.buf_t1_sp, color="#d95f02", ls=(0, (4, 3)), lw=1.2, alpha=0.45, zorder=1)
        self.ax1.plot(self.buf_t, self.buf_t2, color="#e6ab02", ls=(0, (6, 3)), lw=1.8, zorder=3, label="T2: Decapado [_ _]")
        self.ax1.plot(self.buf_t, self.buf_t2_sp, color="#e6ab02", ls=(0, (3, 3, 1, 3)), lw=1.2, alpha=0.45, zorder=1)
        self.ax1.plot(self.buf_t, self.buf_t3, color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=2.0, zorder=4, label="T3: Zincado Celda Hull [_._]")
        self.ax1.plot(self.buf_t, self.buf_t3_sp, color="#38bdf8", ls=(0, (1, 3)), lw=1.3, alpha=0.5, zorder=1)
        self.ax1.plot(self.buf_t, self.buf_t4, color="#a78bfa", ls=(0, (1.5, 2.0)), lw=2.0, zorder=5, label="T4: Niquelado Watts [...]")
        self.ax1.plot(self.buf_t, self.buf_t4_sp, color="#a78bfa", ls=(0, (3, 4)), lw=1.2, alpha=0.45, zorder=1)
        self.ax1.legend(loc="upper left", fontsize=7.0, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # Subplot 2: Conducción de TRIACs (%)
        self.ax2.plot(self.buf_t, self.buf_u1, color="#d95f02", ls="-", lw=1.5, zorder=2, label="u1: Limp (450W) [—]")
        self.ax2.plot(self.buf_t, self.buf_u2, color="#e6ab02", ls=(0, (6, 3)), lw=1.5, zorder=3, label="u2: Decap (450W) [_ _]")
        self.ax2.plot(self.buf_t, self.buf_u3, color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=1.8, zorder=4, label="u3: Hull (18W) [_._]")
        self.ax2.plot(self.buf_t, self.buf_u4, color="#a78bfa", ls=(0, (1.5, 2.0)), lw=1.8, zorder=5, label="u4: Niq (450W) [...]")
        self.ax2.set_ylim(-5, 105)
        self.ax2.legend(loc="upper left", fontsize=7.0, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # Subplot 3: Corriente Galvánica
        hay_pulsado = any(self.buf_curr_avg) and any(abs(c - a) > 0.05 for c, a in zip(self.buf_curr, self.buf_curr_avg))
        if hay_pulsado:
            self.ax3.fill_between(self.buf_t, self.buf_curr_avg, color="#fbbf24", alpha=0.20)
            self.ax3.plot(self.buf_t, self.buf_curr, color="#22c55e", ls="-", lw=2.0, zorder=2, label="I_pico Medida (A)")
            self.ax3.plot(self.buf_t, self.buf_curr_avg, color="#fbbf24", ls="--", lw=1.8, zorder=3, label="I_promedio (A)")
        else:
            self.ax3.fill_between(self.buf_t, self.buf_curr, color="#22c55e", alpha=0.25)
            self.ax3.plot(self.buf_t, self.buf_curr, color="#22c55e", ls="-", lw=2.0, zorder=2, label="Corriente Real Medida (A)")

        self.ax3.set_ylim(0, max(max(self.buf_curr) * 1.25 if self.buf_curr else 1.0, 2.2))
        self.ax3.legend(loc="upper left", fontsize=7.0, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        self.canvas.draw_idle()

    def exportar_grafica_hd(self):
        target_csv = self.ultimo_csv_generado
        if not target_csv or not os.path.exists(target_csv):
            target_csv = filedialog.askopenfilename(
                title="Selecciona el archivo CSV para generar las gráficas",
                initialdir=self.carpeta_experimentos,
                filetypes=[("Archivos CSV", "*.csv")]
            )

        if not target_csv or not os.path.exists(target_csv):
            messagebox.showinfo("Información", "No hay ningún archivo CSV seleccionado.")
            return

        script_graf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficar_datos.py")
        try:
            subprocess.run([sys.executable, script_graf, target_csv], check=True)
            dir_graf = os.path.join(os.path.dirname(target_csv), "graficas")
            messagebox.showinfo(
                "Gráficas Científicas Generadas",
                f"✅ ¡4 Gráficas Científicas HD (300 DPI) generadas con éxito!\n\n"
                f"1. Perfil Electroquímico y Térmico\n"
                f"2. Seguimiento de Errores e(t) e IAE\n"
                f"3. Conmutación de TRIACs y Potencia Activa\n"
                f"4. Rendimiento Faradaico y Retrato de Fase (e vs ė)\n\n"
                f"Guardadas en:\n{dir_graf}"
            )
        except Exception as e:
            messagebox.showerror("Error al Graficar", f"Ocurrió un error al generar las imágenes:\n{e}")

    def abrir_carpeta_datos(self):
        destino = self.carpeta_ensayo_actual if (self.carpeta_ensayo_actual and os.path.exists(self.carpeta_ensayo_actual)) else self.carpeta_experimentos
        if sys.platform == "win32":
            os.startfile(destino)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", destino])
        else:
            subprocess.Popen(["xdg-open", destino])

    def _on_app_close(self):
        if self.grabando:
            self.detener_grabacion()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TelemetriaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

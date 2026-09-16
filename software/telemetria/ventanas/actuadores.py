#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana Secundaria 1: Monitor de Actuadores y Osciloscopio de TRIACs y VCSS.
"""

import math
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from telemetria.utilidades.calculos import calcular_disparo_triac

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

        # 3. KPI Bar en la parte inferior (empaquetado primero para asegurar visibilidad completa)
        kpi_bar = tk.Frame(self.win, bg="#111827", bd=0)
        kpi_bar.pack(fill="x", side="bottom", padx=6, pady=4)

        # 4. Canvas de Matplotlib para la Onda AC y Señal de Gate
        plot_frame = tk.Frame(self.win, bg="#0b1120")
        plot_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self.fig = Figure(figsize=(8.5, 5.2), dpi=100, facecolor="#0f172a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

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
                    v_dac_max = (i_pico / 7.06) * 3.53
                    for i, t in enumerate(t_ms):
                        t_mod = t % periodo_ms
                        dac_signal[i] = v_dac_max if t_mod <= t_on_ms else 0.0
                else:
                    dac_signal[:] = (i_pico / 7.06) * 3.53

            ax2.step(t_ms, dac_signal, color="#38bdf8", lw=1.8, where="post", label="Voltaje Control DAC MCP4725 (0-3.5V)")
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


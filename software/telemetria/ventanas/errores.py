#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana Secundaria 2: Monitor de Errores de Control e Índices IAE/ISE.
"""

import tkinter as tk
import matplotlib
import matplotlib.patches as patches
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        # KPIs de Índices de Desempeño (Empaquetado PRIMERO en bottom para evitar recorte visual)
        kpi_bar = tk.Frame(self.win, bg="#111827", bd=0)
        kpi_bar.pack(fill="x", side="bottom", padx=6, pady=4)

        self.lbl_iae_t1 = self._crear_kpi_err(kpi_bar, "IAE T1 (Limp)", "0.0", "#d95f02")
        self.lbl_iae_t2 = self._crear_kpi_err(kpi_bar, "IAE T2 (Decap)", "0.0", "#e6ab02")
        self.lbl_iae_t3 = self._crear_kpi_err(kpi_bar, "IAE T3 (Zinc)", "0.0", "#38bdf8")
        self.lbl_iae_t4 = self._crear_kpi_err(kpi_bar, "IAE T4 (Níquel)", "0.0", "#a78bfa")
        self.lbl_dedt = self._crear_kpi_err(kpi_bar, "Derivada ė(t)", "0.00 °C/s", "#f472b6")
        self.lbl_err_curr = self._crear_kpi_err(kpi_bar, "Error Corriente", "0.00 A", "#34d399")
        self.lbl_regimen = self._crear_kpi_err(kpi_bar, "Estado Lazo / Fase", "EN ESPERA", "#fbbf24")

        # Matplotlib Canvas (Llena todo el espacio central restante)
        plot_frame = tk.Frame(self.win, bg="#0b1120")
        plot_frame.pack(fill="both", expand=True, padx=6, pady=2)

        self.fig = Figure(figsize=(8.5, 5.5), dpi=100, facecolor="#0f172a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

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
        try:
            self._redibujar_interno()
        except Exception as e:
            print(f"[VentanaErrores] Error al redibujar gráficos: {e}")

    def _redibujar_interno(self):
        self.fig.clear()

        buf_t = getattr(self.app, "buf_t", [])
        if not buf_t:
            ax = self.fig.add_subplot(1, 1, 1)
            ax.set_facecolor("#1e293b")
            ax.grid(True, linestyle=":", alpha=0.35, color="#475569")
            ax.tick_params(colors="#94a3b8", labelsize=8)
            for s in ax.spines.values():
                s.set_color("#334155")
            ax.text(
                0.5, 0.5,
                "Esperando flujo de datos de telemetría...\nInicia la grabación o el bucle de adquisición para visualizar el seguimiento de error.",
                color="#94a3b8", fontsize=10, fontweight="bold",
                ha="center", va="center", transform=ax.transAxes
            )
            ax.set_title("MONITOR DE ERROR DE CONTROL (EN ESPERA)", color="#34d399", fontsize=9.5, fontweight="bold", pad=8)
            self.fig.tight_layout(pad=1.0)
            self.canvas.draw_idle()
            return

        # Calcular series de error: e(t) = SP - T
        buf_t1_sp = getattr(self.app, "buf_t1_sp", [])
        buf_t1 = getattr(self.app, "buf_t1", [])
        buf_t2_sp = getattr(self.app, "buf_t2_sp", [])
        buf_t2 = getattr(self.app, "buf_t2", [])
        buf_t3_sp = getattr(self.app, "buf_t3_sp", [])
        buf_t3 = getattr(self.app, "buf_t3", [])
        buf_t4_sp = getattr(self.app, "buf_t4_sp", [])
        buf_t4 = getattr(self.app, "buf_t4", [])
        buf_curr = getattr(self.app, "buf_curr", [])

        e_t1 = [sp - t for sp, t in zip(buf_t1_sp, buf_t1)]
        e_t2 = [sp - t for sp, t in zip(buf_t2_sp, buf_t2)]
        e_t3 = [sp - t for sp, t in zip(buf_t3_sp, buf_t3)]
        e_t4 = [sp - t for sp, t in zip(buf_t4_sp, buf_t4)]

        # Calcular derivadas discretas dedt: de/dt = (e[i] - e[i-1]) / dt (dt en segundos)
        def calc_dedt(e_series, t_series):
            if len(e_series) < 2:
                return [0.0] * len(e_series)
            d = [0.0]
            for i in range(1, len(e_series)):
                dt_s = (t_series[i] - t_series[i-1]) * 60.0 if len(t_series) > i else 1.0
                if dt_s <= 0.05:
                    dt_s = 1.0
                d.append((e_series[i] - e_series[i-1]) / dt_s)
            return d

        de_t1 = calc_dedt(e_t1, buf_t)
        de_t2 = calc_dedt(e_t2, buf_t)
        de_t3 = calc_dedt(e_t3, buf_t)
        de_t4 = calc_dedt(e_t4, buf_t)

        # Error corriente: target - medido
        etapa_idx = getattr(self.app, "etapa_activa_idx", 0)
        etapa_run = getattr(self.app, "etapa_corriendo", False)
        target_curr = 1.50 if (etapa_idx == 2 and etapa_run) else (1.13 if (etapa_idx == 3 and etapa_run) else 0.0)
        e_curr = [target_curr - i_val for i_val in buf_curr]

        # Dimensiones seguras
        n1 = min(len(buf_t), len(e_t1))
        n2 = min(len(buf_t), len(e_t2))
        n3 = min(len(buf_t), len(e_t3))
        n4 = min(len(buf_t), len(e_t4))
        n_curr = min(len(buf_t), len(e_curr))

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
            if n1 > 0: ax1.plot(buf_t[:n1], e_t1[:n1], color="#d95f02", ls="-", lw=1.6, zorder=2, label="e1: Limpieza")
            if n2 > 0: ax1.plot(buf_t[:n2], e_t2[:n2], color="#e6ab02", ls=(0, (6, 3)), lw=1.6, zorder=3, label="e2: Decapado")
            if n3 > 0: ax1.plot(buf_t[:n3], e_t3[:n3], color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=1.8, zorder=4, label="e3: Zincado")
            if n4 > 0: ax1.plot(buf_t[:n4], e_t4[:n4], color="#a78bfa", ls=(0, (1.5, 2.0)), lw=1.8, zorder=5, label="e4: Níquel")
            ax1.set_title("1. Desviación Térmica Temporal: e(t) = SP - PV (°C)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax1.set_ylabel("Error (°C)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax1.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 2. Retrato de Fase: ė vs e
            ax2.axvline(0, color="#64748b", ls="--", lw=1.0)
            ax2.axhline(0, color="#64748b", ls="--", lw=1.0)
            rect_atractor = patches.Rectangle((-0.5, -0.05), 1.0, 0.10, color="#10b981", alpha=0.18, zorder=1, label="Atractor de Estabilidad (±0.5°C)")
            ax2.add_patch(rect_atractor)

            if len(e_t1) > 0 and len(de_t1) > 0: ax2.plot(e_t1, de_t1, color="#d95f02", lw=1.4, alpha=0.8, label="Trayectoria T1")
            if len(e_t2) > 0 and len(de_t2) > 0: ax2.plot(e_t2, de_t2, color="#e6ab02", lw=1.4, alpha=0.8, label="Trayectoria T2")
            if len(e_t3) > 0 and len(de_t3) > 0: ax2.plot(e_t3, de_t3, color="#38bdf8", lw=1.8, alpha=0.9, label="Trayectoria T3")
            if len(e_t4) > 0 and len(de_t4) > 0: ax2.plot(e_t4, de_t4, color="#a78bfa", lw=1.8, alpha=0.9, label="Trayectoria T4")

            if e_t1 and de_t1: ax2.scatter([e_t1[-1]], [de_t1[-1]], color="#d95f02", s=28, zorder=6, edgecolors="#ffffff")
            if e_t2 and de_t2: ax2.scatter([e_t2[-1]], [de_t2[-1]], color="#e6ab02", s=28, zorder=6, edgecolors="#ffffff")
            if e_t3 and de_t3: ax2.scatter([e_t3[-1]], [de_t3[-1]], color="#38bdf8", s=36, zorder=6, edgecolors="#ffffff", marker="*")
            if e_t4 and de_t4: ax2.scatter([e_t4[-1]], [de_t4[-1]], color="#a78bfa", s=36, zorder=6, edgecolors="#ffffff", marker="*")

            ax2.set_title("2. Retrato de Fase del Control Térmico: ė(t) [Derivada] vs e(t) [Error] (Convergencia al Origen)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax2.set_xlabel("Error e(t) = SP - T (°C)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax2.set_ylabel("ė(t) (°C/s)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax2.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            # 3. Error Corriente
            ax3.axhspan(-0.05, 0.05, color="#38bdf8", alpha=0.15, label="Tolerancia ±50 mA")
            ax3.axhline(0, color="#38bdf8", ls="--", lw=1.2)
            if n_curr > 0: ax3.plot(buf_t[:n_curr], e_curr[:n_curr], color="#34d399", lw=1.8, label="Error Corriente e_I(t)")
            ax3.set_title("3. Desviación de Corriente Galvánica respecto a la Consigna (A)", color="#e2e8f0", fontsize=8.5, fontweight="bold")
            ax3.set_ylabel("Error (A)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax3.set_xlabel("Tiempo (minutos)", color="#e2e8f0", fontsize=7.5, fontweight="bold")
            ax3.legend(loc="upper right", fontsize=6.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        elif self.modo_vista == "FASE":
            ax = self.fig.add_subplot(1, 1, 1)
            estilizar(ax)
            ax.axvline(0, color="#64748b", ls="--", lw=1.2)
            ax.axhline(0, color="#64748b", ls="--", lw=1.2)

            rect_atractor = patches.Rectangle((-0.5, -0.05), 1.0, 0.10, color="#10b981", alpha=0.22, zorder=1, label="Zona Atractora / Estabilidad (±0.5°C | ±0.05°C/s)")
            ax.add_patch(rect_atractor)
            rect_tol = patches.Rectangle((-1.0, -0.10), 2.0, 0.20, color="#fbbf24", alpha=0.10, zorder=0, label="Banda de Tolerancia (±1.0°C)")
            ax.add_patch(rect_tol)

            if len(e_t1) > 0 and len(de_t1) > 0: ax.plot(e_t1, de_t1, color="#d95f02", lw=2.0, alpha=0.85, label="T1: Limpieza (450W)")
            if len(e_t2) > 0 and len(de_t2) > 0: ax.plot(e_t2, de_t2, color="#e6ab02", lw=2.0, alpha=0.85, label="T2: Decapado (450W)")
            if len(e_t3) > 0 and len(de_t3) > 0: ax.plot(e_t3, de_t3, color="#38bdf8", lw=2.4, alpha=0.95, label="T3: Zincado Celda Hull (18W)")
            if len(e_t4) > 0 and len(de_t4) > 0: ax.plot(e_t4, de_t4, color="#a78bfa", lw=2.4, alpha=0.95, label="T4: Niquelado Watts (450W)")

            if e_t1 and de_t1: ax.scatter([e_t1[-1]], [de_t1[-1]], color="#d95f02", s=60, marker="*", edgecolors="#ffffff", zorder=6, label=f"T1 Actual: e={e_t1[-1]:.1f}°C")
            if e_t3 and de_t3: ax.scatter([e_t3[-1]], [de_t3[-1]], color="#38bdf8", s=80, marker="*", edgecolors="#ffffff", zorder=6, label=f"T3 Actual: e={e_t3[-1]:.1f}°C")
            if e_t4 and de_t4: ax.scatter([e_t4[-1]], [de_t4[-1]], color="#a78bfa", s=80, marker="*", edgecolors="#ffffff", zorder=6, label=f"T4 Actual: e={e_t4[-1]:.1f}°C")

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
            if n1 > 0: ax1.plot(buf_t[:n1], e_t1[:n1], color="#d95f02", ls="-", lw=1.8, zorder=2, label="Error T1: Limpieza")
            if n2 > 0: ax1.plot(buf_t[:n2], e_t2[:n2], color="#e6ab02", ls=(0, (6, 3)), lw=1.8, zorder=3, label="Error T2: Decapado")
            if n3 > 0: ax1.plot(buf_t[:n3], e_t3[:n3], color="#38bdf8", ls=(0, (6, 2, 1.5, 2)), lw=2.0, zorder=4, label="Error T3: Zincado")
            if n4 > 0: ax1.plot(buf_t[:n4], e_t4[:n4], color="#a78bfa", ls=(0, (1.5, 2.0)), lw=2.0, zorder=5, label="Error T4: Níquel")
            ax1.set_title("Desviación Térmica Respecto al Setpoint: e(t) = SP - PV (°C)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax1.set_ylabel("Error (°C)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax1.legend(loc="upper right", fontsize=7.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

            ax2.axhspan(-0.05, 0.05, color="#38bdf8", alpha=0.15, label="Tolerancia Corriente ±50 mA")
            ax2.axhline(0, color="#38bdf8", ls="--", lw=1.2)
            if n_curr > 0: ax2.plot(buf_t[:n_curr], e_curr[:n_curr], color="#34d399", lw=2.0, label="Error Corriente e_I(t)")
            ax2.set_title("Desviación de Corriente del Sumidero VCSS (Target - Medida Real)", color="#e2e8f0", fontsize=9, fontweight="bold")
            ax2.set_ylabel("Error (A)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax2.set_xlabel("Tiempo de Proceso (minutos)", color="#e2e8f0", fontsize=8, fontweight="bold")
            ax2.legend(loc="upper right", fontsize=7.5, facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")

        # Actualizar KPIs
        iae_1 = getattr(self.app, "iae_t1", 0.0)
        iae_2 = getattr(self.app, "iae_t2", 0.0)
        iae_3 = getattr(self.app, "iae_t3", 0.0)
        iae_4 = getattr(self.app, "iae_t4", 0.0)
        self.lbl_iae_t1.config(text=f"{iae_1:.1f}")
        self.lbl_iae_t2.config(text=f"{iae_2:.1f}")
        self.lbl_iae_t3.config(text=f"{iae_3:.1f}")
        self.lbl_iae_t4.config(text=f"{iae_4:.1f}")

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


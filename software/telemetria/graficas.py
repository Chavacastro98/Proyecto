#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de visualización gráfica en vivo, subplots Matplotlib y exportación HD a 300 DPI.
"""

import os
import sys
import subprocess
import math
from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from telemetria.utilidades.calculos import calcular_disparo_triac


class GraficasMixin:

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


    def _actualizar_gui_datos(self, t_rel, d_t, d_ph, d_f, d_env):
        if self.modo_demo:
            self.lbl_status.config(text="🎮 MODO DEMO", fg="#fbbf24")
        else:
            self.lbl_status.config(text="🟢 EN LÍNEA" if self.conectado else "🔴 RECONECTANDO", fg="#34d399" if self.conectado else "#ef4444")

        mins = int(t_rel // 60)
        segs = int(t_rel % 60)
        self.lbl_time.config(text=f"Tiempo: {mins:02d}:{segs:02d}")
        self.lbl_samples.config(text=f"Muestras: {self.muestras_count}")
        if hasattr(self, 'lbl_incidentes'):
            n_anom = sum(1 for ev in getattr(self, 'historia_eventos_fallos', []) if ev.get("severidad") in ("CRITICO", "ADVERTENCIA"))
            if n_anom == 0:
                self.lbl_incidentes.config(text="⚠️ Incidentes: 0", fg="#22c55e")
            else:
                self.lbl_incidentes.config(text=f"⚠️ Incidentes: {n_anom}", fg="#ef4444")

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
        self.ultimo_d_f = d_f
        self.ultimo_d_ph = d_ph
        self.ultimo_d_t = d_t
        self.ultimo_d_env = d_env
        self.ultimo_amps = amps_val

        # Actualizar Tarjetas de Tinas con Temperatura + Disparo de Gate TRIAC, Watts y Tendencia (B2)
        def _upd_card(card, t_val, sp_val, gate_pct, a_deg, dl_us, w_val, max_w, canal_idx=0):
            prev_t = card.get("last_t")
            card["last_t"] = t_val

            falla_sonda = False
            salto_activo = False
            if hasattr(self, '_falla_sonda_activa') and canal_idx < len(self._falla_sonda_activa):
                falla_sonda = self._falla_sonda_activa[canal_idx]
            if hasattr(self, '_salto_termico_activo') and canal_idx < len(self._salto_termico_activo):
                salto_activo = self._salto_termico_activo[canal_idx]

            if "trend" in card and card["trend"] is not None:
                if falla_sonda:
                    card["trend"].config(text="⚠️ Falla Sonda", fg="#ef4444")
                elif salto_activo:
                    card["trend"].config(text="⚠️ Ruido EMI", fg="#f59e0b")
                elif prev_t is not None:
                    diff = t_val - prev_t
                    if diff > 0.08:
                        card["trend"].config(text="↑ Subiendo", fg="#f59e0b")
                    elif diff < -0.08:
                        card["trend"].config(text="↓ Bajando", fg="#38bdf8")
                    else:
                        card["trend"].config(text="→ Estable", fg="#34d399")
                else:
                    card["trend"].config(text="→ Estable", fg="#34d399")

            is_heating = (gate_pct > 5.0)
            if falla_sonda:
                card_bg = "#351518"
                border_col = "#ef4444"
            elif salto_activo:
                card_bg = "#382313"
                border_col = "#f59e0b"
            else:
                card_bg = "#271b1e" if is_heating else "#1e293b"
                border_col = "#f59e0b" if is_heating else "#334155"

            card["frame"].config(bg=card_bg, highlightbackground=border_col)
            for k in ("hdr_row", "hdr", "trend", "temp", "gate", "watts"):
                if k in card and card[k] is not None:
                    card[k].config(bg=card_bg)

            if falla_sonda:
                card["temp"].config(text="⚠️ DESCONECTADO", fg="#ef4444")
            elif salto_activo:
                card["temp"].config(text=f"{t_val:.1f}°C ⚠️ EMI", fg="#f59e0b")
            else:
                card["temp"].config(text=f"{t_val:.1f}°C / SP {sp_val:.0f}°C")

            card["gate"].config(text=f"Gate: {gate_pct:.0f}% (α={a_deg:.0f}°, {dl_us}µs)", fg="#38bdf8" if gate_pct > 0 else "#64748b")
            card["watts"].config(text=f"{w_val:.1f} W / {max_w:.0f}W", fg="#34d399" if gate_pct > 0 else "#64748b")

        _upd_card(self.card_t1, float(d_t[0]['t']), float(d_t[0]['sp']), p1, a1, dl1, w1, 450.0, canal_idx=0)
        _upd_card(self.card_t2, float(d_t[1]['t']), float(d_t[1]['sp']), p2, a2, dl2, w2, 450.0, canal_idx=1)
        _upd_card(self.card_t3, float(d_t[2]['t']), float(d_t[2]['sp']), p3, a3, dl3, w3, 18.0, canal_idx=2)
        _upd_card(self.card_t4, float(d_t[3]['t']), float(d_t[3]['sp']), p4, a4, dl4, w4, 450.0, canal_idx=3)

        ph_activo = (d_ph.get("on") == 1)

        # Tarjeta Culombimétrica Q (Faraday)
        self.card_coulomb.config(text=f"{self.coulombs_total:.1f} C")

        if es_pulsado and amps_val > 0.05:
            self.card_amp.config(text=f"{i_pico:.2f}A Pk | {i_prom:.2f}A Pr")
        else:
            self.card_amp.config(text=f"{amps_val:.2f} A")
        self.card_env.config(text=f"{d_env.get('t', '--')}° / {d_env.get('h', '--')}%")
        if hasattr(self, "card_ph"):
            p1_str = str(d_ph.get("p1", d_ph.get("ph1", "--")))
            p2_str = str(d_ph.get("p2", d_ph.get("ph2", "--")))
            self.card_ph.config(text=f"{p1_str} / {p2_str} pH")

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
        m_teo_zn = getattr(self, 'coulombs_zn', 0.0) * 0.33880
        m_teo_ni = getattr(self, 'coulombs_ni', 0.0) * 0.30414
        self.buf_m_teo.append(m_teo_zn + m_teo_ni)
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
        # Bandas sombreadas de tolerancia de setpoint (SP ± 1.5°C) (B4)
        if self.buf_t1_sp and self.buf_t1_sp[-1] > 20.0:
            self.ax1.fill_between(self.buf_t, [s - 1.5 for s in self.buf_t1_sp], [s + 1.5 for s in self.buf_t1_sp], color="#d95f02", alpha=0.08, zorder=0)
        if self.buf_t2_sp and self.buf_t2_sp[-1] > 20.0:
            self.ax1.fill_between(self.buf_t, [s - 1.5 for s in self.buf_t2_sp], [s + 1.5 for s in self.buf_t2_sp], color="#e6ab02", alpha=0.08, zorder=0)
        if self.buf_t3_sp and self.buf_t3_sp[-1] > 20.0:
            self.ax1.fill_between(self.buf_t, [s - 1.5 for s in self.buf_t3_sp], [s + 1.5 for s in self.buf_t3_sp], color="#38bdf8", alpha=0.08, zorder=0)
        if self.buf_t4_sp and self.buf_t4_sp[-1] > 20.0:
            self.ax1.fill_between(self.buf_t, [s - 1.5 for s in self.buf_t4_sp], [s + 1.5 for s in self.buf_t4_sp], color="#a78bfa", alpha=0.08, zorder=0)

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

        # Líneas verticales de cambio de etapa (B4)
        if hasattr(self, 'marcadores_etapas') and self.marcadores_etapas:
            t_min_cur = self.buf_t[0]
            t_max_cur = self.buf_t[-1]
            for m_t, m_label in self.marcadores_etapas:
                if t_min_cur <= m_t <= t_max_cur:
                    for ax in (self.ax1, self.ax2, self.ax3):
                        ax.axvline(x=m_t, color="#38bdf8", ls=":", lw=1.2, alpha=0.5, zorder=1)

        # Cursor / Anotación de valor actual en el último punto (B4)
        last_t_x = self.buf_t[-1]
        idx_act = getattr(self, 'etapa_activa_idx', 0)
        t_series = [self.buf_t1, self.buf_t2, self.buf_t3, self.buf_t4]
        t_colors = ["#d95f02", "#e6ab02", "#38bdf8", "#a78bfa"]
        t_names = ["T1", "T2", "T3", "T4"]
        cur_t = t_series[idx_act]
        cur_c = t_colors[idx_act]
        if cur_t:
            v_t = cur_t[-1]
            self.ax1.plot(last_t_x, v_t, marker="o", markersize=4.5, color=cur_c, zorder=6)
            self.ax1.annotate(f"{t_names[idx_act]}: {v_t:.1f}°C", (last_t_x, v_t), textcoords="offset points", xytext=(6, -2),
                              fontsize=6.8, fontweight="bold", color="#f8fafc",
                              bbox=dict(boxstyle="round,pad=0.25", fc="#0f172a", ec=cur_c, lw=0.9, alpha=0.9))

        if self.buf_curr:
            v_i = self.buf_curr[-1]
            self.ax3.plot(last_t_x, v_i, marker="o", markersize=4.5, color="#22c55e", zorder=6)
            self.ax3.annotate(f"{v_i:.2f} A", (last_t_x, v_i), textcoords="offset points", xytext=(6, -2),
                              fontsize=6.8, fontweight="bold", color="#f8fafc",
                              bbox=dict(boxstyle="round,pad=0.25", fc="#0f172a", ec="#22c55e", lw=0.9, alpha=0.9))

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
                f"✅ ¡Suite completa de 8 Figuras Científicas HD (300 DPI) generada con éxito!\n\n"
                f"1. Perfil Electroquímico y Térmico\n"
                f"2. Seguimiento de Errores e(t) e IAE\n"
                f"3. Conmutación de TRIACs y Potencia Activa\n"
                f"4. Rendimiento Faradaico y Retrato de Fase\n"
                f"5. Dashboard de Diagnóstico Integral\n"
                f"6. Diagrama Gantt y Tiempos Muertos\n"
                f"7. Histórico Ambiental de Cabina\n"
                f"8. Metrología VCSS y Reconstrucción ETS\n\n"
                f"Guardadas en:\n{dir_graf}"
            )
        except Exception as e:
            messagebox.showerror("Error al Graficar", f"Ocurrió un error al generar las imágenes:\n{e}")

    def abrir_gestor_graficas_offline(self):
        """Abre la herramienta visual independiente para gestionar y exportar gráficas por carpeta."""
        script_offline = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exportar_graficas_offline.py")
        if os.path.exists(script_offline):
            subprocess.Popen([sys.executable, script_offline])
        else:
            messagebox.showerror("Error", f"No se encontró el script de exportación en:\n{script_offline}")


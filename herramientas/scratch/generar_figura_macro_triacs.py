#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de la Figura 03b:
Macro-Conmutación de TRIACs en las 4 Tinas a lo largo de Todo el Proceso
Comparativa Lado a Lado:
- Columna 1: Modulación Continua por Ángulo de Fase (Recorte AC)
- Columna 2: Modulación por Tiempo Proporcional (Tren de Ondas / Burst Firing)
Con visualización del 'Rectángulo de Esfuerzo', la 'Zona Estriada de Transición'
y los 'Pulsos Espaciados de Asentamiento Térmico'.
"""

import os
import glob
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def generar_pulso_tiempo_proporcional(t_arr, u_arr):
    t_out = []
    u_out = []
    t_vals = np.array(t_arr)
    u_vals = np.array(u_arr)
    
    if len(t_vals) < 2:
        return t_vals, u_vals

    for i in range(len(t_vals) - 1):
        t0 = t_vals[i]
        t1 = t_vals[i+1]
        dt = t1 - t0
        u_val = float(np.clip(u_vals[i], 0.0, 100.0))
        
        if u_val >= 98.0:
            t_out.extend([t0, t1])
            u_out.extend([100.0, 100.0])
        elif u_val <= 2.0:
            t_out.extend([t0, t1])
            u_out.extend([0.0, 0.0])
        else:
            t_trans = t0 + dt * (u_val / 100.0)
            t_out.extend([t0, t_trans, t_trans, t1])
            u_out.extend([100.0, 100.0, 0.0, 0.0])
            
    return np.array(t_out), np.array(u_out)

def simular_envolvente_recorte_fase(alpha_series, v_rms=120.0):
    """
    Calcula la envolvente de tensión instantánea recortada en función de alpha(t).
    V_RMS(t) = V_grid * sqrt(1 - alpha/pi + sin(2*alpha)/(2*pi))
    V_peak_conducted = V_peak si alpha <= 90°, V_peak * sin(alpha) si alpha > 90°
    """
    v_peak = v_rms * np.sqrt(2)
    alpha_rad = np.radians(np.clip(alpha_series.fillna(180.0), 0.0, 180.0))
    
    # Voltaje eficaz RMS entregado a la carga
    v_rms_load = v_rms * np.sqrt(np.clip(1.0 - (alpha_rad / np.pi) + (np.sin(2.0 * alpha_rad) / (2.0 * np.pi)), 0.0, 1.0))
    
    # Envolvente superior e inferior de voltaje conducido instantáneo
    v_env_pos = []
    v_env_neg = []
    for a_deg in alpha_series:
        if a_deg >= 178.0:
            v_env_pos.append(0.0)
            v_env_neg.append(0.0)
        elif a_deg <= 2.0:
            v_env_pos.append(v_peak)
            v_env_neg.append(-v_peak)
        elif a_deg <= 90.0:
            v_env_pos.append(v_peak)
            v_env_neg.append(-v_peak)
        else:
            v_max = v_peak * math.sin(math.radians(a_deg))
            v_env_pos.append(v_max)
            v_env_neg.append(-v_max)
            
    return np.array(v_rms_load), np.array(v_env_pos), np.array(v_env_neg)

def main():
    csv_paths = glob.glob(r"c:\Proyecto\Proyecto\telemetria\experimentos\Ensayo_*\telemetria_completa.csv")
    if not csv_paths:
        print("No CSV found!")
        return
    csv_path = csv_paths[-1] # Most recent
    print(f"Leyendo CSV: {csv_path}")
    df = pd.read_csv(csv_path)

    t_min = df["Tiempo_Relativo_s"] / 60.0
    t_sec = df["Tiempo_Relativo_s"].values

    # Identificar etapas ISA-88
    colores_etapas = {1: "#f1f5f9", 2: "#e0f2fe", 3: "#fef3c7", 4: "#f3e8ff", 5: "#ecfdf5"}
    nombres_etapas = {1: "1. Limpieza", 2: "2. Decapado", 3: "3. Zn Hull", 4: "4. Ni", 5: "5. Fin"}
    
    def sombrear_etapas_ax(ax):
        if "Etapa_Num" in df.columns and "Etapa_Nombre" in df.columns:
            cambios = df["Etapa_Num"].ne(df["Etapa_Num"].shift()).cumsum()
            for _, grp in df.groupby(cambios):
                e_id = int(grp["Etapa_Num"].iloc[0])
                t_ini = grp["Tiempo_Relativo_s"].iloc[0] / 60.0
                t_fin = grp["Tiempo_Relativo_s"].iloc[-1] / 60.0
                c = colores_etapas.get(e_id, "#ffffff")
                ax.axvspan(t_ini, t_fin, color=c, alpha=0.35, zorder=0)

    # Configurar figura maestra de 4 filas x 2 columnas
    fig, axes = plt.subplots(4, 2, figsize=(16, 13), sharex=True)
    fig.patch.set_facecolor("#ffffff")
    fig.suptitle(
        "Física de Conmutación de TRIACs BTA24 en las 4 Tinas de Proceso — Todo el Ensayo (Escala Macro-Temporal)\n"
        "Columna Izquierda: Modulación por Recorte de Ángulo de Fase (α) | Columna Derecha: Tiempo Proporcional (Burst Firing / Tren de Ondas)",
        fontsize=12.5, fontweight="bold", y=0.985
    )

    tinas = [
        ("T1: Desengrase Alcalino (Resistencia 450W, SP = 85°C)", 
         df["T1_Limpieza_Temp_C"], df["T1_Limpieza_SP_C"], df["T1_TRIAC_Potencia_Pct"], df["T1_TRIAC_Alpha_Deg"], df["T1_TRIAC_Watts_W"], "#d95f02", 450.0),
        ("T2: Decapado Alcalino (Resistencia 450W, SP = 85°C)", 
         df["T2_Decapado_Temp_C"], df["T2_Decapado_SP_C"], df["T2_TRIAC_Potencia_Pct"], df["T2_TRIAC_Alpha_Deg"], df["T2_TRIAC_Watts_W"], "#d97706", 450.0),
        ("T3: Celda Hull Zincado Ácido (Peltier/Calentador 18W, SP = 25/40°C)", 
         df["T3_CeldaHull_Temp_C"], df["T3_CeldaHull_SP_C"], df["T3_TRIAC_Potencia_Pct"], df["T3_TRIAC_Alpha_Deg"], df["T3_TRIAC_Watts_W"], "#0284c7", 18.0),
        ("T4: Niquelado sobre Zinc (Resistencia 450W, SP = 35°C)", 
         df["T4_Niquelado_Temp_C"], df["T4_Niquelado_SP_C"], df["T4_TRIAC_Potencia_Pct"], df["T4_TRIAC_Alpha_Deg"], df["T4_TRIAC_Watts_W"], "#7c3aed", 450.0)
    ]

    for idx, (titulo_tina, s_temp, s_sp, s_u, s_alpha, s_watts, color_base, w_max) in enumerate(tinas):
        ax_fase = axes[idx, 0]
        ax_burst = axes[idx, 1]

        sombrear_etapas_ax(ax_fase)
        sombrear_etapas_ax(ax_burst)

        # -------------------------------------------------------------
        # COLUMNA 1: MODULACIÓN POR ÁNGULO DE FASE (RECORTE AC)
        # -------------------------------------------------------------
        v_rms_l, v_env_p, v_env_n = simular_envolvente_recorte_fase(s_alpha)
        
        # Envolvente sombreada de voltaje conducido (-V_env a +V_env)
        ax_fase.fill_between(t_min, v_env_n, v_env_p, color=color_base, alpha=0.20, label="Envolvente de Voltaje Instantáneo Conducido (±V_peak)")
        ax_fase.plot(t_min, v_env_p, color=color_base, lw=1.2, ls="--")
        ax_fase.plot(t_min, v_env_n, color=color_base, lw=1.2, ls="--")
        
        # Tensión eficaz RMS entregada a la resistencia
        ax_fase.plot(t_min, v_rms_l, color=color_base, lw=2.2, label=f"Tensión Eficaz V_RMS ({v_rms_l[-1]:.1f}V)")
        ax_fase.set_ylabel("Voltaje AC (V)", fontweight="bold")
        ax_fase.set_ylim(-195, 195)
        ax_fase.set_title(f"Tina {idx+1}: Recorte de Fase α — {titulo_tina}", fontsize=9.5, fontweight="bold")
        ax_fase.grid(True, linestyle=":", alpha=0.6)

        # Twin axis: Temperatura y Ángulo Alpha
        ax_fase_tw = ax_fase.twinx()
        ax_fase_tw.plot(t_min, s_temp, color="#0f172a", lw=1.8, label=f"Temp Real ({s_temp.iloc[-1]:.1f}°C)")
        ax_fase_tw.plot(t_min, s_sp, color="#64748b", ls=":", lw=1.5, label=f"SP ({s_sp.iloc[-1]:.1f}°C)")
        ax_fase_tw.plot(t_min, s_alpha, color="#e11d48", ls="-.", lw=1.4, alpha=0.85, label=f"Ángulo α ({s_alpha.iloc[-1]:.0f}°)")
        ax_fase_tw.set_ylabel("Temp (°C) / α (°)", fontweight="bold", color="#0f172a")
        ax_fase_tw.set_ylim(15, 185)
        ax_fase_tw.grid(False)

        # Leyenda combinada
        lines1, labels1 = ax_fase.get_legend_handles_labels()
        lines2, labels2 = ax_fase_tw.get_legend_handles_labels()
        ax_fase.legend(lines1[:2] + lines2[:3], labels1[:2] + labels2[:3], loc="lower left", fontsize=7, frameon=True, framealpha=0.85)

        # -------------------------------------------------------------
        # COLUMNA 2: MODULACIÓN POR TIEMPO PROPORCIONAL (BURST FIRING)
        # -------------------------------------------------------------
        t_r, u_r = generar_pulso_tiempo_proporcional(t_min, s_u.values)
        
        # Tren de pulsos rectangulares ON/OFF
        ax_burst.step(t_r, u_r, color=color_base, lw=1.3, where="post", label="Conducción Activa ON (100%) / OFF (0%)")
        ax_burst.fill_between(t_r, u_r, color=color_base, alpha=0.30, step="post")
        ax_burst.set_ylabel("Tiempo Proporcional (%)", fontweight="bold")
        ax_burst.set_ylim(-5, 115)
        ax_burst.set_title(f"Tina {idx+1}: Burst Firing — {titulo_tina}", fontsize=9.5, fontweight="bold")
        ax_burst.grid(True, linestyle=":", alpha=0.6)

        # Twin axis: Temperatura y Potencia Watts
        ax_burst_tw = ax_burst.twinx()
        ax_burst_tw.plot(t_min, s_temp, color="#0f172a", lw=1.8, label=f"Temp Real ({s_temp.iloc[-1]:.1f}°C)")
        ax_burst_tw.plot(t_min, s_sp, color="#64748b", ls=":", lw=1.5, label=f"SP ({s_sp.iloc[-1]:.1f}°C)")
        ax_burst_tw.plot(t_min, s_watts, color="#059669", ls="-.", lw=1.4, label=f"Potencia ({s_watts.iloc[-1]:.0f}W)")
        ax_burst_tw.set_ylabel(f"Temp (°C) / Potencia (W max {w_max:.0f})", fontweight="bold", color="#0f172a")
        ax_burst_tw.set_ylim(0, max(100, w_max * 1.1))
        ax_burst_tw.grid(False)

        lines3, labels3 = ax_burst.get_legend_handles_labels()
        lines4, labels4 = ax_burst_tw.get_legend_handles_labels()
        ax_burst.legend(lines3[:1] + lines4[:3], labels3[:1] + labels4[:3], loc="upper right", fontsize=7, frameon=True, framealpha=0.85)

        # Anotación física en la Tina 1 para ilustrar el fenómeno
        if idx == 0:
            # Anotación en burst firing
            ax_burst.annotate(
                "■ Rectángulo Sólido\n(Esfuerzo 95-100% Calentamiento)",
                xy=(0.5, 95), xytext=(0.8, 70),
                arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                fontsize=7.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="#fef08a", alpha=0.85)
            )
            ax_burst.annotate(
                "|||| Estriado / Código de Barras\n(Transición 50% Frenado PI)",
                xy=(1.8, 50), xytext=(2.2, 75),
                arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                fontsize=7.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="#bae6fd", alpha=0.85)
            )
            ax_burst.annotate(
                "| | | Pulsos Delgados Espaciados\n(Asentamiento Estable ~18% Reposición)",
                xy=(4.5, 20), xytext=(4.8, 45),
                arrowprops=dict(facecolor="black", shrink=0.08, width=1, headwidth=5),
                fontsize=7.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="#bbf7d0", alpha=0.85)
            )

    axes[3, 0].set_xlabel("Tiempo de Proceso (minutos)", fontweight="bold")
    axes[3, 1].set_xlabel("Tiempo de Proceso (minutos)", fontweight="bold")

    fig.tight_layout()
    
    out_dir = r"c:\Proyecto\Proyecto\documentos\imagenes"
    out_path = os.path.join(out_dir, "03b_macro_conmutacion_4tinas_proceso_completo.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Imagen guardada en: {out_path}")

    # Tambien guardarla en la carpeta de graficas del experimento mas reciente
    exp_graficas = os.path.join(os.path.dirname(csv_path), "graficas")
    if os.path.exists(exp_graficas):
        fig.savefig(os.path.join(exp_graficas, "03b_macro_conmutacion_4tinas_proceso_completo.png"), dpi=300, bbox_inches="tight")
        print(f"[OK] Imagen guardada en: {exp_graficas}")

if __name__ == "__main__":
    main()

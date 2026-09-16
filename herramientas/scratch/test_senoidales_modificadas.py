#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba de generacion de oscilogramas senoidales modificados por TRIAC
en los 3 periodos reales del experimento:
1. Periodo de Esfuerzo Maximo (Arranque / Calentamiento: u=100%, alpha~0°)
2. Periodo de Transicion (Aproximacion al Setpoint: u=50%, alpha=90°)
3. Periodo de Regimen Permanente (Mantenimiento Termico Estable: u=15-20%, alpha=135°)
Y comparativa con Tiempo Proporcional (Burst Firing).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def simular_onda_recortada_triac(alpha_deg, n_ciclos=3, v_rms=120.0, freq=60.0, pts_por_ciclo=1000):
    """Genera senoidal modificada por recorte de fase para un angulo alpha dado."""
    t_ciclo = 1.0 / freq
    t_semiciclo = t_ciclo / 2.0
    t_total = n_ciclos * t_ciclo
    t_ms = np.linspace(0, t_total * 1000.0, n_ciclos * pts_por_ciclo)
    
    v_peak = v_rms * np.sqrt(2)
    v_grid = v_peak * np.sin(2 * np.pi * freq * (t_ms / 1000.0))
    v_load = np.zeros_like(v_grid)
    
    delay_ms = (alpha_deg / 180.0) * (t_semiciclo * 1000.0)
    t_half_ms = t_semiciclo * 1000.0
    
    for i, t in enumerate(t_ms):
        t_en_semiciclo = t % t_half_ms
        if t_en_semiciclo >= delay_ms:
            v_load[i] = v_grid[i]
            
    return t_ms, v_grid, v_load

def simular_tiempo_proporcional_senoidales(duty_pct, n_ciclos_ventana=10, v_rms=120.0, freq=60.0):
    """Genera paquetes de ciclos senoidales completos (Burst Firing / Ciclo Integral)."""
    t_ciclo = 1.0 / freq
    pts_por_ciclo = 300
    t_ms = np.linspace(0, n_ciclos_ventana * t_ciclo * 1000.0, n_ciclos_ventana * pts_por_ciclo)
    
    v_peak = v_rms * np.sqrt(2)
    v_grid = v_peak * np.sin(2 * np.pi * freq * (t_ms / 1000.0))
    v_load = np.zeros_like(v_grid)
    
    ciclos_on = int(round(n_ciclos_ventana * (duty_pct / 100.0)))
    t_corte_ms = ciclos_on * t_ciclo * 1000.0
    
    for i, t in enumerate(t_ms):
        if t <= t_corte_ms:
            v_load[i] = v_grid[i]
            
    return t_ms, v_grid, v_load

# Crear figura de prueba
fig, axes = plt.subplots(3, 2, figsize=(14, 10))
fig.patch.set_facecolor("#ffffff")
fig.suptitle(
    "Física de Conmutación de TRIACs BTA24: Senoidales Modificadas en los 3 Periodos del Ensayo\n"
    "Columna Izquierda: Modulación por Ángulo de Fase (Recorte AC) | Columna Derecha: Tiempo Proporcional (Tren de Ondas / Burst Firing)",
    fontsize=12, fontweight="bold", y=0.98
)

# 1. Periodo de Esfuerzo Máximo (u = 95%, alpha = 25°)
t_ms, v_g, v_l1 = simular_onda_recortada_triac(alpha_deg=25.0)
axes[0, 0].plot(t_ms, v_g, color="#94a3b8", ls="--", lw=1.0, label="Tensión Red 120V RMS")
axes[0, 0].fill_between(t_ms, v_l1, color="#d95f02", alpha=0.35)
axes[0, 0].plot(t_ms, v_l1, color="#d95f02", lw=2.0, label="Tensión en Resistencia (u=95%, α=25°)")
axes[0, 0].set_title("1A. Periodo de Esfuerzo Máximo (Calentamiento Inicial: α=25° → 95% Potencia)", fontsize=10, fontweight="bold")
axes[0, 0].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[0, 0].set_ylim(-190, 190)
axes[0, 0].legend(loc="upper right", fontsize=8)
axes[0, 0].grid(True, linestyle=":", alpha=0.6)

t_burst, v_gb, v_lb1 = simular_tiempo_proporcional_senoidales(duty_pct=90.0)
axes[0, 1].plot(t_burst, v_gb, color="#94a3b8", ls="--", lw=1.0, label="Tensión Red")
axes[0, 1].fill_between(t_burst, v_lb1, color="#d95f02", alpha=0.35)
axes[0, 1].plot(t_burst, v_lb1, color="#d95f02", lw=2.0, label="Burst Firing: 9 de 10 Ciclos ON")
axes[0, 1].set_title("1B. Tiempo Proporcional en Esfuerzo (90% Ciclos Activos Continuos)", fontsize=10, fontweight="bold")
axes[0, 1].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[0, 1].set_ylim(-190, 190)
axes[0, 1].legend(loc="upper right", fontsize=8)
axes[0, 1].grid(True, linestyle=":", alpha=0.6)

# 2. Periodo de Transición (u = 50%, alpha = 90°)
t_ms, v_g, v_l2 = simular_onda_recortada_triac(alpha_deg=90.0)
axes[1, 0].plot(t_ms, v_g, color="#94a3b8", ls="--", lw=1.0)
axes[1, 0].fill_between(t_ms, v_l2, color="#d97706", alpha=0.35)
axes[1, 0].plot(t_ms, v_l2, color="#d97706", lw=2.0, label="Tensión en Resistencia (u=50%, α=90°)")
axes[1, 0].set_title("2A. Periodo de Transición (Aproximación a Consigna: α=90° → 50% Potencia)", fontsize=10, fontweight="bold")
axes[1, 0].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[1, 0].set_ylim(-190, 190)
axes[1, 0].legend(loc="upper right", fontsize=8)
axes[1, 0].grid(True, linestyle=":", alpha=0.6)

t_burst, v_gb, v_lb2 = simular_tiempo_proporcional_senoidales(duty_pct=50.0)
axes[1, 1].plot(t_burst, v_gb, color="#94a3b8", ls="--", lw=1.0)
axes[1, 1].fill_between(t_burst, v_lb2, color="#d97706", alpha=0.35)
axes[1, 1].plot(t_burst, v_lb2, color="#d97706", lw=2.0, label="Burst Firing: 5 de 10 Ciclos ON")
axes[1, 1].set_title("2B. Tiempo Proporcional en Transición (50% Ciclos Activos)", fontsize=10, fontweight="bold")
axes[1, 1].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[1, 1].set_ylim(-190, 190)
axes[1, 1].legend(loc="upper right", fontsize=8)
axes[1, 1].grid(True, linestyle=":", alpha=0.6)

# 3. Periodo de Régimen Permanente / Mantenimiento Estable (u = 18%, alpha = 135°)
t_ms, v_g, v_l3 = simular_onda_recortada_triac(alpha_deg=135.0)
axes[2, 0].plot(t_ms, v_g, color="#94a3b8", ls="--", lw=1.0)
axes[2, 0].fill_between(t_ms, v_l3, color="#16a34a", alpha=0.35)
axes[2, 0].plot(t_ms, v_l3, color="#16a34a", lw=2.0, label="Tensión en Resistencia (u=18%, α=135°)")
axes[2, 0].set_title("3A. Periodo Estable / Mantenimiento Térmico (α=135° → ~18% Potencia Reposición)", fontsize=10, fontweight="bold")
axes[2, 0].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[2, 0].set_xlabel("Tiempo (milisegundos — 3 Ciclos AC de 16.66 ms)", fontweight="bold")
axes[2, 0].set_ylim(-190, 190)
axes[2, 0].legend(loc="upper right", fontsize=8)
axes[2, 0].grid(True, linestyle=":", alpha=0.6)

t_burst, v_gb, v_lb3 = simular_tiempo_proporcional_senoidales(duty_pct=20.0)
axes[2, 1].plot(t_burst, v_gb, color="#94a3b8", ls="--", lw=1.0)
axes[2, 1].fill_between(t_burst, v_lb3, color="#16a34a", alpha=0.35)
axes[2, 1].plot(t_burst, v_lb3, color="#16a34a", lw=2.0, label="Burst Firing: 2 de 10 Ciclos ON")
axes[2, 1].set_title("3B. Tiempo Proporcional en Régimen Estable (20% Ciclos Activos Espaciados)", fontsize=10, fontweight="bold")
axes[2, 1].set_ylabel("Voltaje Instantáneo (V)", fontweight="bold")
axes[2, 1].set_xlabel("Tiempo (milisegundos — Paquete de 10 Ciclos AC = 166.6 ms)", fontweight="bold")
axes[2, 1].set_ylim(-190, 190)
axes[2, 1].legend(loc="upper right", fontsize=8)
axes[2, 1].grid(True, linestyle=":", alpha=0.6)

fig.tight_layout()
out_test = "C:/Users/salva/.gemini/antigravity-ide/brain/cfdd2e22-1e77-484e-af33-2aad92d4677e/graficas/03_senoidales_modificadas_triac_periodos.png"
fig.savefig(out_test, dpi=300, bbox_inches="tight")
plt.close(fig)
print("Senoidales modificadas generadas con exito en:", out_test)

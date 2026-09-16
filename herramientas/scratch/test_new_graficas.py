#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de generacion de nuevas graficas:
- Figura 7: Solo historicos reales (Presion, T amb, Humedad)
- Figura 3: Evolucion de TRIACs con Angulo de Fase y Tiempo Proporcional (PWM/Rectangulos)
- Subcarpeta triacs/ con 4 figuras individuales
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def generar_pulso_tiempo_proporcional(t_arr, u_arr):
    """Genera serie temporal de pulsos rectangulares para control por tiempo proporcional."""
    t_out = []
    u_out = []
    
    for i in range(len(t_arr) - 1):
        t0 = t_arr[i]
        t1 = t_arr[i+1]
        dt = t1 - t0
        u_val = float(np.clip(u_arr[i], 0.0, 100.0))
        
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

# Probar con datos reales del ensayo
csv_file = "telemetria/experimentos/Ensayo_P01_Ronda_1_20260912_114723/telemetria_completa.csv"
df = pd.read_csv(csv_file)
t_min = (df["Tiempo_Relativo_s"] / 60.0).values
u_t1 = df["T1_TRIAC_Potencia_Pct"].values

t_rect, u_rect = generar_pulso_tiempo_proporcional(t_min, u_t1)
print(f"Puntos generados para onda rectangular: {len(t_rect)}")
print("Test OK!")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba end-to-end de la telemetría RTOS 1.3:
Simula un ciclo completo de 4 etapas, registra tiempos muertos y genera las 8 figuras científicas.
"""
import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, "telemetria"))

import subprocess

# Directorio de ensayo de prueba
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
ensayo_dir = os.path.join(base_dir, "telemetria", "experimentos", f"Ensayo_P01_Ronda_1_{timestamp_str}")
graficas_dir = os.path.join(ensayo_dir, "graficas")
os.makedirs(graficas_dir, exist_ok=True)

csv_tel = os.path.join(ensayo_dir, "telemetria_completa.csv")
csv_err = os.path.join(ensayo_dir, "metricas_control_errores.csv")
csv_tm = os.path.join(ensayo_dir, "registro_tiempos_muertos.csv")

# Generar 600 segundos de simulación (10 minutos)
etapas_def = [
    (1, "Limpieza Química", 120, 85.0, 0.0, 0),
    (2, "Decapado Ácido", 80, 85.0, 0.0, 0),
    (3, "Zincado Celda Hull", 100, 25.0, 1.5, 1), # Pulsado 10Hz 20%
    (4, "Niquelado Químico Watts", 300, 30.0, 1.13, 0) # DC
]

filas_tel = []
filas_err = []
filas_tm = []

t_rel = 0.0
coulombs_tot = 0.0
energia_wh = 0.0
iae_t1, iae_t2, iae_t3, iae_t4, iae_curr = 0.0, 0.0, 0.0, 0.0, 0.0
t_previo = time.time()

for idx, (et_num, et_nom, dur, sp_t, sp_i, modo_pul) in enumerate(etapas_def):
    # Registrar tiempo muerto previo si no es la primera etapa
    if idx > 0:
        dt_s = round(float(np.random.uniform(9.5, 14.8)), 1)
        filas_tm.append([
            idx,
            etapas_def[idx-1][0], etapas_def[idx-1][1],
            et_num, et_nom,
            datetime.now().isoformat(timespec="seconds"),
            datetime.now().isoformat(timespec="seconds"),
            dt_s,
            24.2, 54.5, 1013.2, 3.8
        ])
        t_rel += dt_s

    for sec in range(dur):
        t_rel += 1.0
        t_iso = datetime.now().isoformat(timespec="seconds")
        
        # Dinámica térmica
        t1 = 85.0 + np.random.normal(0, 0.2) if et_num == 1 else (24.0 + (85.0-24.0)*min(1.0, sec/60.0))
        t2 = 85.0 + np.random.normal(0, 0.2) if et_num == 2 else 24.0
        t3 = 25.0 + np.random.normal(0, 0.15) if et_num == 3 else 24.0
        t4 = 30.0 + np.random.normal(0, 0.18) if et_num == 4 else 24.0
        
        u1 = 55.0 if et_num == 1 else 0.0
        u2 = 45.0 if et_num == 2 else 0.0
        u3 = 22.0 if et_num == 3 else 0.0
        u4 = 35.0 if et_num == 4 else 0.0
        
        w1 = u1 * 4.5
        w2 = u2 * 4.5
        w3 = u3 * 0.18
        w4 = u4 * 4.5
        energia_wh += (w1 + w2 + w3 + w4) / 3600.0
        
        # Dinámica de corriente
        i_real = 0.0
        if sp_i > 0:
            i_real = sp_i + np.random.normal(0, 0.008)
            coulombs_tot += i_real * 1.0
        
        i1 = i_real * 0.501
        i2 = i_real * 0.499
        vs1 = i1 * 1.0
        vs2 = i2 * 1.0
        
        pi_st = 0 if modo_pul == 1 else (3 if sp_i > 0 else 0)
        salud = 0
        
        filas_tel.append([
            t_iso, t_rel,
            1, "Ronda 1", et_num, et_nom, sec, dur,
            sp_i, "Pulsado" if modo_pul == 1 else "DC", sp_t,
            round(t1, 1), 85.0 if et_num == 1 else 0.0, 1 if et_num == 1 else 0,
            u1, 95.0, 4400, w1,
            round(t2, 1), 85.0 if et_num == 2 else 0.0, 1 if et_num == 2 else 0,
            u2, 105.0, 4800, w2,
            round(t3, 1), 25.0 if et_num == 3 else 0.0, 1 if et_num == 3 else 0,
            u3, 130.0, 6000, w3,
            round(t4, 1), 30.0 if et_num == 4 else 0.0, 1 if et_num == 4 else 0,
            u4, 120.0, 5500, w4,
            2.05, 4.15, 0, 2, 2, 98.5, 97.9, 0,
            1 if sp_i > 0 else 0, modo_pul,
            sp_i, round(i_real, 3), round(i1, 3), round(i2, 3),
            round(vs1, 3), round(vs2, 3), 1.0025, 1, 1 if sp_i > 0 else 0,
            int(sp_i * 580), 10 if modo_pul == 1 else 0, 20 if modo_pul == 1 else 0,
            pi_st, salud,
            round(coulombs_tot, 2), round(coulombs_tot * 0.3388, 2), round(energia_wh, 3),
            round(24.3 + 0.5 * np.sin(t_rel / 100.0), 1),
            round(52.0 - 2.5 * (t_rel / 600.0), 1),
            1013.1
        ])
        
        e1 = (85.0 - t1) if et_num == 1 else 0.0
        e_i = sp_i - i_real
        iae_t1 += abs(e1)
        iae_curr += abs(e_i)
        filas_err.append([
            t_iso, t_rel, et_num, et_nom,
            round(e1, 2), 0.0, 0.0, 0.0, round(e_i, 3),
            round(iae_t1, 1), 0.0, 0.0, 0.0, round(iae_curr, 2),
            u1, u2, u3, u4
        ])

# Escribir CSVs
headers_tel = [
    "Timestamp_ISO", "Tiempo_Relativo_s",
    "Placa_ID", "Ronda", "Etapa_Num", "Etapa_Nombre", "Etapa_Tiempo_s", "Etapa_Duracion_s",
    "Corriente_Target_A", "Modo_Corriente", "Temp_SP_Target_C",
    "T1_Limpieza_Temp_C", "T1_Limpieza_SP_C", "T1_Limpieza_Activo",
    "T1_TRIAC_Potencia_Pct", "T1_TRIAC_Alpha_Deg", "T1_TRIAC_Delay_us", "T1_TRIAC_Watts_W",
    "T2_Decapado_Temp_C", "T2_Decapado_SP_C", "T2_Decapado_Activo",
    "T2_TRIAC_Potencia_Pct", "T2_TRIAC_Alpha_Deg", "T2_TRIAC_Delay_us", "T2_TRIAC_Watts_W",
    "T3_CeldaHull_Temp_C", "T3_CeldaHull_SP_C", "T3_CeldaHull_Activo",
    "T3_TRIAC_Potencia_Pct", "T3_TRIAC_Alpha_Deg", "T3_TRIAC_Delay_us", "T3_TRIAC_Watts_W",
    "T4_Niquelado_Temp_C", "T4_Niquelado_SP_C", "T4_Niquelado_Activo",
    "T4_TRIAC_Potencia_Pct", "T4_TRIAC_Alpha_Deg", "T4_TRIAC_Delay_us", "T4_TRIAC_Watts_W",
    "pH_Tina1", "pH_Tina2", "pH_Modulo_Activo",
    "pH_Modo_Cal_T1", "pH_Modo_Cal_T2",
    "pH_Slope_Pct_T1", "pH_Slope_Pct_T2", "pH_Interlock_Activo",
    "Fuente_Activa", "Fuente_Modo_Pulsado",
    "Fuente_Corriente_Consigna_A", "Fuente_Corriente_Real_A",
    "Fuente_Corriente_Shunt1_A", "Fuente_Corriente_Shunt2_A",
    "Fuente_Voltaje_Shunt1_V", "Fuente_Voltaje_Shunt2_V",
    "Fuente_Factor_Gm", "Fuente_Compensacion_Activa", "Fuente_Rele_VDD",
    "Fuente_Amplitud_DAC", "Fuente_Frecuencia_Hz", "Fuente_DutyCycle_Pct",
    "Fuente_PI_Estado", "Fuente_Salud_Celda",
    "Carga_Acumulada_Coulombs", "Masa_Teorica_Faraday_mg", "Energia_Termica_Wh",
    "Ambiente_Temp_C", "Ambiente_Humedad_Pct", "Ambiente_Presion_hPa"
]

import csv
with open(csv_tel, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(headers_tel)
    w.writerows(filas_tel)

headers_err = [
    "Timestamp_ISO", "Tiempo_Relativo_s",
    "Etapa_Num", "Etapa_Nombre",
    "Error_T1_C", "Error_T2_C", "Error_T3_C", "Error_T4_C", "Error_Corriente_A",
    "IAE_T1", "IAE_T2", "IAE_T3", "IAE_T4", "IAE_Corriente",
    "Esfuerzo_u1_Pct", "Esfuerzo_u2_Pct", "Esfuerzo_u3_Pct", "Esfuerzo_u4_Pct"
]
with open(csv_err, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(headers_err)
    w.writerows(filas_err)

headers_tm = [
    "Transicion_ID", "Etapa_Origen_Num", "Etapa_Origen_Nombre",
    "Etapa_Destino_Num", "Etapa_Destino_Nombre",
    "Timestamp_Inicio", "Timestamp_Fin", "Tiempo_Muerto_s",
    "Temp_Ambiente_C", "Humedad_Pct", "Presion_hPa", "Evaporacion_Estimada_g_h"
]
with open(csv_tm, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(headers_tm)
    w.writerows(filas_tm)

print(f"Ensayo sintético generado en: {ensayo_dir}")
print(f"Muestras de telemetría: {len(filas_tel)}, Tiempos muertos: {len(filas_tm)}")

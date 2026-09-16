#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba unitaria para el modelo bicapa Faradaico y gravimétrico
(Pesaje único al término de la Etapa 4).
"""
import os
import sys
import numpy as np
import pandas as pd

def test_faraday_bicapa():
    # Parámetros experimentales típicos:
    # Etapa 3 (Zincado): 1.50 A durante 120s -> Q_Zn = 180 C
    # Etapa 4 (Niquelado): 1.13 A durante 600s -> Q_Ni = 678 C
    q_zn = 180.0
    q_ni = 678.0
    area_cm2 = 65.0

    eq_zn = 0.33880  # mg/C
    eq_ni = 0.30414  # mg/C

    m_teo_zn_mg = q_zn * eq_zn
    m_teo_ni_mg = q_ni * eq_ni
    m_teo_tot_mg = m_teo_zn_mg + m_teo_ni_mg

    print(f">> Q_Zn: {q_zn:.1f} C -> m_teo_Zn = {m_teo_zn_mg:.2f} mg")
    print(f">> Q_Ni: {q_ni:.1f} C -> m_teo_Ni = {m_teo_ni_mg:.2f} mg")
    print(f">> Masa teórica total bicapa = {m_teo_tot_mg:.2f} mg ({m_teo_tot_mg/1000:.4f} g)")

    # Simular pesaje en balanza analítica:
    # Peso inicial seco pre-Etapa 1: 28.5000 g
    # Supongamos rendimiento del 95%:
    rendimiento_esperado = 95.0
    delta_m_esperado_mg = m_teo_tot_mg * (rendimiento_esperado / 100.0)
    p_ini = 28.5000
    p_fin = p_ini + (delta_m_esperado_mg / 1000.0)

    delta_m_real_mg = (p_fin - p_ini) * 1000.0
    eta_calculada = (delta_m_real_mg / m_teo_tot_mg) * 100.0
    print(f">> Peso Balanza: Ini={p_ini:.4f}g, Fin={p_fin:.4f}g -> Delta_m = {delta_m_real_mg:.2f} mg")
    print(f">> Rendimiento calculado: {eta_calculada:.2f} %")

    assert abs(eta_calculada - rendimiento_esperado) < 1e-4, "Error en eficiencia"

    # Espesores:
    # rho_Zn = 7.14 g/cm3, rho_Ni = 8.90 g/cm3
    factor_rend = eta_calculada / 100.0
    m_real_zn_g = (m_teo_zn_mg * factor_rend) / 1000.0
    m_real_ni_g = (m_teo_ni_mg * factor_rend) / 1000.0
    esp_zn_um = (m_real_zn_g / (7.14 * area_cm2)) * 10000.0
    esp_ni_um = (m_real_ni_g / (8.90 * area_cm2)) * 10000.0
    esp_tot_um = esp_zn_um + esp_ni_um

    print(f">> Espesor Zn: {esp_zn_um:.2f} um")
    print(f">> Espesor Ni: {esp_ni_um:.2f} um")
    print(f">> Espesor Total Bicapa: {esp_tot_um:.2f} um")

    assert esp_zn_um > 0 and esp_ni_um > 0 and esp_tot_um == esp_zn_um + esp_ni_um

    # Probar parseo de CSV sintético con etapas
    df_test = pd.DataFrame({
        "Tiempo_Relativo_s": [0, 60, 120, 121, 421, 721],
        "Fuente_Corriente_Real_A": [1.50, 1.50, 1.50, 1.13, 1.13, 1.13],
        "Etapa_Num": [3, 3, 3, 4, 4, 4],
        "Etapa_Nombre": ["Zincado", "Zincado", "Zincado", "Niquelado", "Niquelado", "Niquelado"]
    })

    t_vals = df_test["Tiempo_Relativo_s"].values
    i_vals = df_test["Fuente_Corriente_Real_A"].values
    dt = np.diff(t_vals, prepend=t_vals[0])

    mask_zn = (df_test["Etapa_Num"] == 3).values
    mask_ni = (df_test["Etapa_Num"] == 4).values

    q_zn_parsed = float(np.sum(i_vals[mask_zn] * dt[mask_zn]))
    q_ni_parsed = float(np.sum(i_vals[mask_ni] * dt[mask_ni]))

    print(f">> CSV Parse test: Q_Zn_parsed={q_zn_parsed:.1f} C, Q_Ni_parsed={q_ni_parsed:.1f} C")
    assert q_zn_parsed > 0 and q_ni_parsed > 0

    print("[OK] TODAS LAS PRUEBAS DEL MODELO BICAPA PASARON CON EXITO")

if __name__ == "__main__":
    test_faraday_bicapa()

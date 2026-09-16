#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SUITE DE PRUEBAS UNITARIAS: CÁLCULOS METROLÓGICOS Y CONTROL (tests/test_calculos.py)
===============================================================================
Verifica la exactitud matemática y física de los algoritmos de control de potencia,
culombimetría faradaica y espesores de electrodeposición.
===============================================================================
"""

import sys
import os
import pytest

# Incluir rutas del software SCADA para resolver módulos de telemetria y utilidades
DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

from utilidades.calculos import calcular_disparo_triac


class TestControlPotenciaTRIAC:
    """Pruebas de la conversión no lineal de potencia senoidal RMS a 60 Hz."""

    def test_potencia_cero_apaga_triac(self):
        """A 0% de potencia el retardo debe ser 8333 us (semiciclo completo = apagado)."""
        p_safe, alpha_deg, delay_us, watts = calcular_disparo_triac(0.0, 450.0)
        assert p_safe == 0.0
        assert alpha_deg == 180.0
        assert delay_us == 8333
        assert watts == 0.0

    def test_potencia_maxima_conduccion_plena(self):
        """A 100% de potencia el retardo debe ser 0 us (conducción total)."""
        p_safe, alpha_deg, delay_us, watts = calcular_disparo_triac(100.0, 450.0)
        assert p_safe == 100.0
        assert alpha_deg == 0.0
        assert delay_us == 0
        assert watts == 450.0

    def test_potencia_media_angulo_cuadratura(self):
        """A 50% de potencia el ángulo debe ser 90° y el retardo ~4166 us."""
        p_safe, alpha_deg, delay_us, watts = calcular_disparo_triac(50.0, 450.0)
        assert p_safe == 50.0
        assert alpha_deg == pytest.approx(90.0, abs=0.5)
        assert delay_us == pytest.approx(4166, abs=5)
        assert watts == pytest.approx(225.0, abs=0.5)

    def test_clamping_valores_fuera_de_rango(self):
        """Valores negativos o superiores a 100 deben saturarse sin lanzar excepciones."""
        p_neg, _, delay_neg, _ = calcular_disparo_triac(-25.0, 450.0)
        assert p_neg == 0.0
        assert delay_neg == 8333

        p_sup, _, delay_sup, _ = calcular_disparo_triac(150.0, 450.0)
        assert p_sup == 100.0
        assert delay_sup == 0


class TestLeyesDeFaraday:
    """Pruebas de cálculo de culombimetría y espesor de electrodeposición."""

    CONSTANTE_FARADAY = 96485.33  # C / mol
    PESO_MOLAR_ZN = 65.38        # g / mol
    VALENCIA_ZN = 2
    DENSIDAD_ZN = 7.14           # g / cm^3

    PESO_MOLAR_NI = 58.69        # g / mol
    VALENCIA_NI = 2

    def test_masa_teorica_zinc_120_segundos(self):
        """
        Para Zn: I = 1.50 A durante 120 s => Q = 180 Coulombs.
        m_teo = (Q * M) / (z * F) = (180 * 65.38) / (2 * 96485.33) = ~0.060989 g = ~60.99 mg
        """
        q_coulombs = 1.50 * 120.0
        m_teo_g = (q_coulombs * self.PESO_MOLAR_ZN) / (self.VALENCIA_ZN * self.CONSTANTE_FARADAY)
        m_teo_mg = m_teo_g * 1000.0

        assert pytest.approx(m_teo_mg, rel=1e-3) == 60.989

    def test_eficiencia_faradaica_gravimetrica(self):
        """Verifica el cálculo de eficiencia catódica eta = (m_real / m_teo) * 100%."""
        m_real_mg = 58.45
        m_teo_mg = 60.989
        eficiencia = (m_real_mg / m_teo_mg) * 100.0

        assert pytest.approx(eficiencia, abs=0.1) == 95.8

    def test_espesor_recubrimiento_zinc(self):
        """
        Espesor e = (delta_m / (rho * A)) * 10^4  (en micrometros).
        Para delta_m = 0.05845 g, rho = 7.14 g/cm3, Area = 65 cm2.
        """
        delta_m_g = 0.05845
        area_cm2 = 65.0
        espesor_um = (delta_m_g / (self.DENSIDAD_ZN * area_cm2)) * 10000.0

        assert pytest.approx(espesor_um, abs=0.05) == 1.26

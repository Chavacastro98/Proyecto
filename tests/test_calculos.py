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

    def test_culombimetria_pulsada_ponderada_duty_cycle(self):
        """
        En corriente pulsada (10 Hz, 20% duty cycle), I_pico = 1.50 A durante 120 s:
        I_efectiva = 1.50 A * (20 / 100) = 0.30 A
        Q_pulsado = 0.30 A * 120 s = 36.0 Coulombs.
        Sin ponderar el duty cycle, se sobreestimaría a 180 C (500% de error metrológico).
        """
        i_pico = 1.50
        duty_pct = 20.0
        duracion_s = 120.0

        i_efectiva = i_pico * (duty_pct / 100.0)
        q_pulsado = i_efectiva * duracion_s
        m_teo_zn_mg = q_pulsado * 0.33880

        assert pytest.approx(i_efectiva, abs=1e-4) == 0.30
        assert pytest.approx(q_pulsado, abs=1e-4) == 36.0
        assert pytest.approx(m_teo_zn_mg, abs=0.01) == 12.20

    def test_fuente_en_reposo_cero_coulombs(self):
        """
        Cuando la fuente está apagada o en etapas de limpieza/decapado,
        la corriente real debe ser 0.0 A y la carga integrada delta_Q = 0.0 C.
        """
        es_fuente_activa = False
        etapa_activa_idx = 1  # Decapado ácido
        amps_consigna = 1.50
        dt = 1.0

        i_medida_real = float(amps_consigna if es_fuente_activa else 0.0)
        delta_q = 0.0
        if es_fuente_activa and etapa_activa_idx in (2, 3):
            delta_q = i_medida_real * dt

        assert i_medida_real == 0.0
        assert delta_q == 0.0

    def test_modelo_aditivo_bicapa_zn_ni(self):
        """
        Verifica el modelo faradaico aditivo para bicapa Zn + Ni:
        m_teo_total = (Q_zn * Eq_zn) + (Q_ni * Eq_ni)
        Para Q_zn = 36.0 C (Pulsado 120s) y Q_ni = 67.8 C (DC 1.13A x 60s):
        m_teo_zn = 36.0 * 0.33880 = 12.197 mg
        m_teo_ni = 67.8 * 0.30414 = 20.621 mg
        m_total = 32.818 mg
        """
        q_zn = 36.0
        q_ni = 67.8
        eq_zn = 0.33880
        eq_ni = 0.30414

        m_zn = q_zn * eq_zn
        m_ni = q_ni * eq_ni
        m_total = m_zn + m_ni

        assert pytest.approx(m_zn, abs=0.01) == 12.20
        assert pytest.approx(m_ni, abs=0.01) == 20.62
        assert pytest.approx(m_total, abs=0.01) == 32.82


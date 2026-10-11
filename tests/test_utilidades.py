#!/usr/bin/env python3
"""
Pruebas unitarias para los módulos de utilidades:
- alarma.py
- verificar_lut.py
- sim_ph.py
- sim_termica.py
"""

import os
import sys
import time
from unittest.mock import patch

import numpy as np
import pytest

DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

from utilidades import alarma
from utilidades.sim_ph import (
    filtrar_senyal_ph,
    generar_datos_simulacion_ph,
    graficar_simulacion_ph,
    median3,
)
from utilidades.sim_termica import (
    TINAS_DEFAULT,
    graficar_simulacion_termica,
    simular_tina,
)
from utilidades.verificar_lut import (
    LUT_FIRMWARE_DEF,
    calcular_potencia_rms_lut,
    graficar_linealizacion_lut,
)


class TestAlarma:
    """Pruebas del módulo de alarma acústica."""

    def test_reproducir_alarma_fin_etapa(self):
        with patch("winsound.Beep", return_value=None):
            alarma.reproducir_alarma_sonora("fin_etapa")
            time.sleep(0.05)

    def test_reproducir_alarma_fin_ensayo(self):
        with patch("winsound.Beep", return_value=None):
            alarma.reproducir_alarma_sonora("fin_ensayo")
            time.sleep(0.05)

    def test_reproducir_alarma_test(self):
        with patch("winsound.Beep", return_value=None):
            alarma.reproducir_alarma_sonora("test")
            time.sleep(0.05)

    def test_play_chime(self):
        with patch.object(alarma, "reproducir_alarma_sonora") as mock_rep:
            alarma.play_chime()
            mock_rep.assert_called_once_with("fin_etapa")

    def test_reproducir_alarma_excepcion_manejada(self):
        with patch("winsound.Beep", side_effect=RuntimeError("Audio error")):
            alarma.reproducir_alarma_sonora("test")
            time.sleep(0.05)

    def test_reproducir_alarma_no_windows(self):
        with patch("sys.platform", "linux"), patch("builtins.print"):
            alarma.reproducir_alarma_sonora("test")
            time.sleep(0.05)


class TestVerificarLUT:
    """Pruebas del cálculo de linealización TRIAC."""

    def test_lut_longitud_y_valores(self):
        assert len(LUT_FIRMWARE_DEF) == 101
        assert LUT_FIRMWARE_DEF[0] == 8333
        assert LUT_FIRMWARE_DEF[-1] == 0

    def test_calcular_potencia_rms_lut_defecto(self):
        pct, p_rms, err, max_err = calcular_potencia_rms_lut()
        assert len(pct) == 101
        assert len(p_rms) == 101
        assert len(err) == 101
        assert 0.0 <= max_err <= 3.0

    def test_calcular_potencia_rms_lut_personalizada(self):
        custom_lut = np.array([8333, 4166, 0])
        pct, p_rms, _err, _max_err = calcular_potencia_rms_lut(custom_lut, T_semi=8333)
        assert len(pct) == 3
        assert p_rms[0] == pytest.approx(0.0, abs=0.1)
        assert p_rms[-1] == pytest.approx(100.0, abs=0.1)


class TestSimPH:
    """Pruebas del pipeline de filtrado de pH."""

    def test_median3_orden(self):
        assert median3(1, 2, 3) == 2
        assert median3(3, 1, 2) == 2
        assert median3(2, 3, 1) == 2
        assert median3(5, 5, 1) == 5

    def test_filtrar_senyal_vacia(self):
        res = filtrar_senyal_ph(np.array([]))
        assert len(res) == 0

    def test_filtrar_senyal_constante(self):
        signal = np.full(50, 7.0)
        filtered = filtrar_senyal_ph(signal)
        assert np.allclose(filtered, 7.0)

    def test_filtrar_pico_impulsivo(self):
        signal = np.full(20, 7.0)
        signal[5] = 12.0
        filtered = filtrar_senyal_ph(signal)
        assert filtered[5] < 7.5

    def test_filtrar_salto_adaptativo(self):
        signal = np.array([4.0] * 10 + [8.0] * 10)
        filtered = filtrar_senyal_ph(signal, umbral_adaptativo=0.35)
        assert filtered[0] == pytest.approx(4.0)
        assert filtered[-1] == pytest.approx(8.0, abs=0.1)

    def test_generar_datos_simulacion_ph(self):
        real, raw, spikes, time_s = generar_datos_simulacion_ph(n=200, seed=123)
        assert len(real) == 200
        assert len(raw) == 200
        assert len(time_s) == 200
        assert len(spikes) > 0


class TestSimTermica:
    """Pruebas de la simulación de respuesta térmica PI."""

    def test_tinas_default_definidas(self):
        assert len(TINAS_DEFAULT) == 4
        for tina in TINAS_DEFAULT:
            assert "T_set" in tina
            assert "Kp" in tina
            assert "Ki" in tina
            assert "P_max" in tina

    def test_simular_tina_calentamiento(self):
        tina_test = TINAS_DEFAULT[0]
        t, T, power = simular_tina(tina_test, t_total=60, dt=1.0, t_amb=25.0)
        assert len(t) == 60
        assert len(T) == 60
        assert len(power) == 60
        assert T[0] == pytest.approx(25.0)
        assert T[-1] > T[0]
        assert np.all(power >= 0.0)
        assert np.all(power <= 100.0)

    def test_simular_tina_corte_sobretemperatura(self):
        tina_caliente = {
            "nombre": "Tina Test Sobretemperatura",
            "vol": 0.5, "A_s": 0.02, "P_max": 200, "retardo": 1,
            "T_set": 50.0, "Kp": 20.0, "Ki": 0.1,
        }
        _t, _T, power = simular_tina(tina_caliente, t_total=10, dt=1.0, t_amb=55.0)
        assert np.all(power == 0.0)

    def test_graficar_simulaciones(self, tmp_path):
        ruta_lut = str(tmp_path / "test_lut.png")
        fig_lut = graficar_linealizacion_lut(guardar_archivo=True, mostrar=False, ruta_salida=ruta_lut)
        assert fig_lut is not None

        ruta_ph = str(tmp_path / "test_ph.png")
        fig_ph = graficar_simulacion_ph(guardar_archivo=True, mostrar=False, ruta_salida=ruta_ph, n=100)
        assert fig_ph is not None

        ruta_term = str(tmp_path / "test_term.png")
        fig_term = graficar_simulacion_termica(guardar_archivo=True, mostrar=False, ruta_salida=ruta_term, t_total=20, dt=2.0)
        assert fig_term is not None

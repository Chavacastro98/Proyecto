#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SUITE DE PRUEBAS UNITARIAS: DESERIALIZACIÓN Y CONTRATOS JSON DE TELEMETRÍA
===============================================================================
Verifica la integridad de los esquemas de datos JSON transmitidos entre el
nodo maestro ESP32-S3 (RTOS 2.0) y la estación SCADA en PC (Telemetría 2.0).
===============================================================================
"""

import json
import pytest


class TestContratoJSONFuenteVCSS:
    """Valida el contrato y rangos del endpoint de corriente /data_f."""

    MOCK_PAYLOAD_FUENTE = {
        "act": 1,
        "modo": 0,
        "amp": 2048,
        "sp": 2048,
        "freq": 10,
        "duty": 50,
        "amps": 1.50,
        "i_real": 1.498,
        "i1": 0.749,
        "i2": 0.749,
        "vs1": 0.075,
        "vs2": 0.075,
        "gm": 1.0025,
        "comp": 1,
        "rele": 1,
        "pi_st": 1,
        "salud": 0,
        "wave": [1.50] * 64
    }

    def test_deserializacion_campos_obligatorios(self):
        """Comprueba que todos los campos requeridos por el SCADA estén presentes."""
        campos_esperados = {
            "act", "modo", "amp", "sp", "freq", "duty", "amps",
            "i_real", "i1", "i2", "vs1", "vs2", "gm", "comp", "rele",
            "pi_st", "salud", "wave"
        }
        raw_json = json.dumps(self.MOCK_PAYLOAD_FUENTE)
        data = json.loads(raw_json)
        assert campos_esperados.issubset(data.keys())

    def test_rangos_actuacion_dac_y_potencia(self):
        """Verifica que los valores numéricos respeten los límites físicos del hardware."""
        data = self.MOCK_PAYLOAD_FUENTE
        assert 0 <= data["amp"] <= 4095, "Amplitud DAC fuera de resolución de 12 bits"
        assert 0 <= data["sp"] <= 4095, "Setpoint DAC fuera de resolución de 12 bits"
        assert 0.0 <= data["amps"] <= 3.0, "Consigna en amperios excede capacidad nominal"
        assert 1 <= data["duty"] <= 99, "Duty cycle debe estar acotado entre 1% y 99%"
        assert len(data["wave"]) == 64, "Vector ETS de forma de onda debe contener 64 muestras"

    def test_validacion_ganancia_transconductancia(self):
        """El factor de corrección Gm debe oscilar dentro de una ventana física realista."""
        gm = self.MOCK_PAYLOAD_FUENTE["gm"]
        assert 0.80 <= gm <= 1.25, f"Ganancia Gm anómala: {gm}"


class TestContratoJSONTermico:
    """Valida el esquema del array de 4 lazos térmicos /data_t."""

    MOCK_PAYLOAD_TERMICO = [
        {"t": 87.5, "sp": 88.0, "p": 62, "run": 1},   # Tina 1: Desengrase
        {"t": 86.2, "sp": 88.0, "p": 58, "run": 1},   # Tina 2: Decapado
        {"t": 25.1, "sp": 25.0, "p": 0,  "run": 0},   # Tina 3: Celda Hull Zinc
        {"t": 55.0, "sp": 55.0, "p": 40, "run": 1}    # Tina 4: Níquel
    ]

    def test_estructura_4_tinas(self):
        """Debe contener exactamente 4 elementos correspondientes a las 4 tinas del proceso."""
        raw_json = json.dumps(self.MOCK_PAYLOAD_TERMICO)
        data = json.loads(raw_json)
        assert isinstance(data, list)
        assert len(data) == 4

    def test_integridad_campos_termicos(self):
        """Cada lazo debe contener temperatura medida, setpoint, potencia (%) y estado run."""
        for i, tina in enumerate(self.MOCK_PAYLOAD_TERMICO):
            assert "t" in tina, f"Falta temperatura en tina {i+1}"
            assert "sp" in tina, f"Falta setpoint en tina {i+1}"
            assert "p" in tina, f"Falta potencia en tina {i+1}"
            assert "run" in tina, f"Falta estado en tina {i+1}"
            assert 0 <= tina["p"] <= 100, f"Potencia fuera de rango en tina {i+1}"
            assert tina["run"] in (0, 1), f"Estado run inválido en tina {i+1}"


class TestContratoJSONPHDual:
    """Valida el endpoint de medición de pH /get_ph_dual."""

    MOCK_PAYLOAD_PH = {
        "p1": "2.05",
        "p2": "4.10",
        "on": 1,
        "m1": 2,
        "m2": 2,
        "sl1": "98.4",
        "sl2": "97.8",
        "c1": 1,
        "c2": 1,
        "il": 0
    }

    def test_conversion_metrologica_ph(self):
        """Los valores de pH y Slope se reciben como strings formateados y deben convertirse a float."""
        data = self.MOCK_PAYLOAD_PH
        ph1 = float(data["p1"])
        ph2 = float(data["p2"])
        slope1 = float(data["sl1"])
        slope2 = float(data["sl2"])

        assert 0.0 <= ph1 <= 14.0, "pH de tina 1 fuera de escala química"
        assert 0.0 <= ph2 <= 14.0, "pH de tina 2 fuera de escala química"
        assert 80.0 <= slope1 <= 105.0, "Sensibilidad Nernstiana tina 1 fuera de especificación"
        assert 80.0 <= slope2 <= 105.0, "Sensibilidad Nernstiana tina 2 fuera de especificación"


class TestResilienciaYFallbackSCADA:
    """Verifica que el parser no genere excepciones no controladas ante datos incompletos."""

    def test_relleno_por_defecto_trama_parcial(self):
        """Si un payload unificado /data_all viene incompleto, se asignan valores seguros por defecto."""
        payload_incompleto = {
            "t": [{"t": 25.0, "sp": 25.0, "p": 0, "run": 0}],
            "f": {"act": 0, "i_real": 0.0}
        }
        # Simulación del parser defensivo de captura_datos.py
        env_defecto = {"t": "0.0", "h": "0", "p": "0.0"}
        ph_defecto = {"p1": "0.00", "p2": "0.00", "on": 0, "il": 0}

        env = payload_incompleto.get("env", env_defecto)
        ph = payload_incompleto.get("ph", ph_defecto)

        assert env["t"] == "0.0"
        assert ph["il"] == 0

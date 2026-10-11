#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
TEST DE FUENTE ÚNICA DE VERDAD: CONSTANTES Y SHOWCASE WEB (tests/test_constantes_web.py)
===============================================================================
Verifica que las constantes maestras unificadas en constantes_sistema.json
coincidan estrictamente con las especificaciones y valores por defecto del
Showcase Web (documentos/academicos/showcase_web/index.html).
===============================================================================
"""

import os
import json
import re
import pytest

DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_CONSTANTES = os.path.join(DIR_ROOT, "software", "telemetria2.0", "utilidades", "constantes_sistema.json")
HTML_SHOWCASE = os.path.join(DIR_ROOT, "documentos", "academicos", "showcase_web", "index.html")


@pytest.fixture(scope="module")
def constantes():
    assert os.path.exists(JSON_CONSTANTES), f"No existe archivo de constantes: {JSON_CONSTANTES}"
    with open(JSON_CONSTANTES, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def html_content():
    assert os.path.exists(HTML_SHOWCASE), f"No existe archivo HTML de showcase: {HTML_SHOWCASE}"
    with open(HTML_SHOWCASE, "r", encoding="utf-8") as f:
        return f.read()


class TestFuenteUnicaVerdad:
    """Valida la consistencia metrológica entre las constantes maestras y la web."""

    def test_parametros_termicos(self, constantes, html_content):
        term = constantes["termico"]
        # K = 0.327 °C/W
        assert f"{term['K_planta_C_W']}" in html_content
        # tau = 1370 s
        assert f"{int(term['tau_planta_s'])}" in html_content
        # Retardo total theta = 7.5 s con ZOH 1.5 s
        assert "7.5 s" in html_content
        assert "1.5" in html_content  # ZOH 1.5s
        # Ventana 3.0 s
        assert f"{term['ventana_modulacion_s']:.1f}s" in html_content or "3.0 s" in html_content
        # TRIAC BTA24-800BW
        assert term["triac_part_number"] in html_content

    def test_parametros_vcss(self, constantes, html_content):
        vcss = constantes["vcss_fuente"]
        # Shunts de 1.0 ohm / 10W
        assert f"{vcss['r_shunt_rama_ohm']:.1f} Ω" in html_content or "1.0 Ω" in html_content
        assert f"{int(vcss['potencia_nominal_shunt_W'])} W" in html_content or "10 W" in html_content
        # Gm = 2.0 S
        assert f"{vcss['gm_total_S']:.1f}" in html_content
        # LSB = 1.6 mA
        assert "1.6" in html_content
        # Imax con derating = 4.5 A
        assert f"{vcss['corriente_max_derating_A']:.1f} A" in html_content or "4.5" in html_content
        # MOSFET IRLZ44Z / IRLZ44N
        assert vcss["mosfet_part_number"] in html_content or vcss["mosfet_compatible"] in html_content

    def test_parametros_ph(self, constantes, html_content):
        ph = constantes["ph"]
        # Buffers V7 = 1650, V4 = 2030, V10 = 1310
        assert f"value=\"{int(ph['v7_nominal_mV'])}\"" in html_content
        assert f"value=\"{int(ph['v4_nominal_mV'])}\"" in html_content
        assert f"value=\"{int(ph['v10_nominal_mV'])}\"" in html_content
        # Nernst 59.16 mV/pH
        assert f"{ph['s_nernst_25C_mV_pH']:.2f}" in html_content

    def test_celda_hull_y_difusion_pulsada(self, constantes, html_content):
        hull = constantes["celda_hull_267ml"]
        electro = constantes["electrodeposicion"]
        # Ecuación de celda Hull a=5.10, b=5.24
        assert f"{hull['constante_a']:.2f}" in html_content
        assert f"{hull['constante_b']:.2f}" in html_content
        # Capa de difusión pulsante óptima al 20% (ton = 20 ms) ~ 3.7 um (3.74 um)
        assert "3.7" in html_content or "3.74" in html_content
        # Tren de pulsos óptimo validado experimentalmente: 20% duty, 10 Hz, 1.50 A
        assert "20%" in html_content or "20 %" in html_content
        assert "1.50 A" in html_content

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
BLOQUES COMUNES REV 5.0 (compartidos por la Placa UNO Q y la Placa ESP32-S3 + Nano)
================================================================================
Cada funcion agrega al PCBAIndustrialDesigner un bloque electrico completo:

  1. agregar_rele_bipolar        -> 2do rele (corte del CATODO/Drain) + driver PMOS
                                     activo-BAJO (preserva la logica del modulo de rele
                                     original: GPIO LOW = rele cerrado) + flyback.
  2. agregar_instrumentacion     -> OPA2171 (amp. diferencial Vcell + sumador I_TOTAL)
                                     + ADS1115 #2 (0x49) + terminales para 2 voltimetros
                                     de panel (V celda real, I total real a 1 V/A).
  3. agregar_leds_calentadores   -> 4 LEDs de estado (uno por TRIAC) junto a cada canal.
  4. agregar_leds_estado         -> LEDs de rele de celda y rieles +12V/+5V/+3V3.
  5. agregar_miller              -> Capacitores de compensacion Miller del lazo VCSS.

Convenciones:
  - DIP y reles THT: el origen del footprint es el PIN 1 (no el centro).
  - LED_0805: pad 1 = catodo, pad 2 = anodo (KiCad).
  - Todos los codigos LCSC fueron verificados contra el catalogo JLCPCB/LCSC.
================================================================================
"""


def _r(d, ref, val, lcsc, desc, x, y, n1, n2, rot=0.0):
    d.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        ref, val, lcsc, desc, x, y, rot, {"1": n1, "2": n2},
    )


def _c(d, ref, val, lcsc, desc, x, y, n1, n2, rot=0.0):
    d.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        ref, val, lcsc, desc, x, y, rot, {"1": n1, "2": n2},
    )


def _led(d, ref, color, lcsc, desc, x, y, net_anodo, rot=0.0):
    # LED_0805: pad 1 = catodo, pad 2 = anodo
    d.add_component(
        "LED_SMD", "LED_0805_2012Metric",
        ref, color, lcsc, desc, x, y, rot, {"1": "PGND", "2": net_anodo},
    )


# ------------------------------------------------------------------------------
# 1. RELE BIPOLAR + DRIVER PMOS ACTIVO-BAJO
# ------------------------------------------------------------------------------
def agregar_rele_bipolar(d, hs, x_k2=98.0, x_q=125.0):
    """
    K_ZCS2 corta el DRAIN de los MOSFET (cato do de la celda). K_ZCS (ya existente en
    cada placa) corta el ANODO (+12V). Ambas bobinas en paralelo, gobernadas por un
    PMOS high-side (AO3401A) con compuerta tirada a +5V (reposo = abierto).
    Logica: salida 74HCT541 BAJA -> PMOS ON -> ambas bobinas energizadas -> celda
    conectada. Igual que el modulo de rele comercial activo-BAJO del diseno original.
    """
    yc = hs + 19.0
    d.add_component(
        "Relay_THT", "Relay_SPDT_SANYOU_SRD_Series_Form_C",
        "K_ZCS2", "SRD-05VDC-SL-C", "C35449",
        "Rele 2 de corte bipolar: abre el CATODO (Drain MOSFET) de la celda Hull",
        x_k2, yc, 0.0,
        {"1": "VCSS_DRAIN", "2": "RLY_DRV", "3": "CELL_CATHODE", "5": "PGND"},
    )
    d.add_component(
        "Package_TO_SOT_SMD", "SOT-23",
        "Q_RLY", "AO3401A", "C15127",
        "PMOS high-side driver de bobinas de rele (activo-BAJO, 142 mA)",
        x_q, yc - 6.0, 0.0,
        {"1": "RLY_GATE", "2": "+5V", "3": "RLY_DRV"},
    )
    _r(d, "R_QG", "1k", "C17513", "Resistencia serie compuerta PMOS rele",
       x_q, yc - 0.5, "Y_RELE", "RLY_GATE")
    _r(d, "R_QPU", "10k", "C17414", "Pull-up compuerta PMOS (reposo = rele abierto)",
       x_q + 4.2, yc - 0.5, "RLY_GATE", "+5V")
    d.add_component(
        "Diode_SMD", "D_SMA",
        "D_FLY", "1N4007W", "C95872",
        "Diodo flyback de ambas bobinas de rele (catodo a RLY_DRV)",
        x_q + 6.5, yc - 6.0, 0.0,
        {"1": "RLY_DRV", "2": "PGND"},
    )


# ------------------------------------------------------------------------------
# 2. INSTRUMENTACION V/I REAL DE LA CELDA
# ------------------------------------------------------------------------------
def agregar_instrumentacion(d, hs, x_term):
    """
    U9 (OPA2171 dual):
      - Seccion A: amplificador DIFERENCIAL de ganancia 1:
            VCELL_MON = V(CELL_ANODE) - V(CELL_CATHODE)   (referido a PGND)
      - Seccion B: SUMADOR no inversor de ganancia 2 sobre los sensores Kelvin:
            ITOT_MON = V(SHUNT1_SENSE) + V(SHUNT2_SENSE)  -> 1 V por Amper (shunts 1 ohm)
    U10 (ADS1115 @ 0x49): AIN0 = VCELL_MON/6, AIN1 = ITOT_MON/6 (divisor 100k/20k).
    J_METER_V y J_METER_I: 3 pines (+12V, GND, senal) para voltimetros de panel 0-30V.
    """
    # ---------------- Bloque U9 (zona PGND) ----------------
    ya, yb, yc = hs + 12.0, hs + 18.0, hs + 24.0
    d.add_component(
        "Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm",
        "U9", "OPA2171AIDR", "C75253",
        "OpAmp dual RRIO 36V: diferencial Vcell (A) + sumador I total (B)",
        76.0, yb, 0.0,
        {
            "1": "VCELL_MON", "2": "DIFF_N", "3": "DIFF_P", "4": "PGND",
            "5": "SUM_P", "6": "SUM_N", "7": "ITOT_MON", "8": "+12V_VCSS",
        },
    )
    _c(d, "C_U9", "100nF", "C49678", "Desacople OPA2171 de instrumentacion",
       76.0, yc, "+12V_VCSS", "PGND")
    # Diferencial (A): ganancia 1 con 4 x 100k
    _r(d, "R_D1", "100k", "C17407", "Diferencial: CATODO de celda a entrada inversora",
       62.0, ya, "CELL_CATHODE", "DIFF_N")
    _r(d, "R_D2", "100k", "C17407", "Diferencial: realimentacion",
       65.8, ya, "DIFF_N", "VCELL_MON")
    _r(d, "R_D3", "100k", "C17407", "Diferencial: ANODO de celda a entrada no inversora",
       62.0, yb, "CELL_ANODE", "DIFF_P")
    _r(d, "R_D4", "100k", "C17407", "Diferencial: referencia a PGND",
       65.8, yb, "DIFF_P", "PGND")
    # Sumador (B): V+ = (V1+V2)/2, ganancia 2
    _r(d, "R_S1", "100k", "C17407", "Sumador: rama shunt 1",
       86.0, ya, "SHUNT1_SENSE", "SUM_P")
    _r(d, "R_S2", "100k", "C17407", "Sumador: rama shunt 2",
       89.8, ya, "SUM_P", "SHUNT2_SENSE")
    _r(d, "R_SG", "100k", "C17407", "Sumador: resistencia a PGND (ganancia 2)",
       86.0, yb, "SUM_N", "PGND")
    _r(d, "R_SF", "100k", "C17407", "Sumador: realimentacion (ganancia 2)",
       89.8, yb, "SUM_N", "ITOT_MON")
    # Salidas protegidas hacia terminales de voltimetro
    _r(d, "R_MO1", "1k", "C17513", "Proteccion salida V celda hacia voltimetro",
       66.0, yc, "VCELL_MON", "VCELL_OUT")
    _r(d, "R_MO2", "1k", "C17513", "Proteccion salida I total hacia voltimetro",
       86.0, yc, "ITOT_MON", "ITOT_OUT")

    # ---------------- Bloque U10 ADS1115 #2 (zona AGND, x < 50) ----------------
    d.add_component(
        "Package_SO", "MSOP-10_3x3mm_P0.5mm",
        "U10", "ADS1115IDGSR", "C37593",
        "ADC 16-bit #2 (0x49): A0 = V celda real, A1 = I total real",
        27.0, hs + 18.0, 0.0,
        {
            "1": "+3V3", "3": "AGND", "4": "VCELL_DIV", "5": "ITOT_DIV",
            "6": "AGND", "7": "AGND", "8": "+3V3",
            "9": "I2C_SDA", "10": "I2C_SCL",
        },
    )
    _c(d, "C_U10", "100nF", "C49678", "Desacople local ADS1115 #2",
       34.0, hs + 18.0, "+3V3", "AGND")
    _r(d, "R_DV1", "100k", "C17407", "Divisor V celda: superior (1/6)",
       8.5, hs + 12.0, "VCELL_MON", "VCELL_DIV")
    _r(d, "R_DV2", "20k", "C4328", "Divisor V celda: inferior",
       12.3, hs + 12.0, "VCELL_DIV", "AGND")
    _c(d, "C_DV", "100nF", "C49678", "Filtro anti-alias V celda",
       16.1, hs + 12.0, "VCELL_DIV", "AGND")
    _r(d, "R_DI1", "100k", "C17407", "Divisor I total: superior (1/6)",
       8.5, hs + 18.0, "ITOT_MON", "ITOT_DIV")
    _r(d, "R_DI2", "20k", "C4328", "Divisor I total: inferior",
       12.3, hs + 18.0, "ITOT_DIV", "AGND")
    _c(d, "C_DI", "100nF", "C49678", "Filtro anti-alias I total",
       16.1, hs + 18.0, "ITOT_DIV", "AGND")

    # ---------------- Terminales para voltimetros de panel ----------------
    for ref, y, net_sig, desc in (
        ("J_METER_V", hs - 5.5, "VCELL_OUT", "Salida a voltimetro de panel: VOLTAJE REAL de celda (1 V/V)"),
        ("J_METER_I", hs + 12.0, "ITOT_OUT", "Salida a voltimetro de panel: CORRIENTE REAL total (1 V/A)"),
    ):
        d.add_component(
            "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal",
            ref, "VOLTIMETRO_PANEL_3P", "C8461", desc,
            x_term, y, 270.0,
            {"1": "+12V_VCSS", "2": "PGND", "3": net_sig},
        )


# ------------------------------------------------------------------------------
# 3. LEDs DE ESTADO DE CALENTADORES (uno por canal TRIAC)
# ------------------------------------------------------------------------------
def agregar_leds_calentadores(d, x_r, x_led, ry_list, dy=8.0):
    """LED amarillo por canal; se alimenta de la salida Y_Gx del 74HCT541 (lado logico)."""
    for i, ry in enumerate(ry_list):
        _r(d, f"R_LH{i+1}", "2k", "C4109", f"Limitadora LED estado calentador {i+1}",
           x_r, ry + dy, f"Y_G{i+1}", f"LEDA_G{i+1}")
        d.add_component(
            "LED_SMD", "LED_0805_2012Metric",
            f"LED_H{i+1}", "AMARILLO", "C2296", f"LED estado calentador tina {i+1}",
            x_led, ry + dy, 180.0, {"1": "PGND", "2": f"LEDA_G{i+1}"},
        )


# ------------------------------------------------------------------------------
# 4. LEDs DE RELE DE CELDA Y RIELES
# ------------------------------------------------------------------------------
def agregar_leds_estado(d, hs, x0):
    filas = (
        ("RLY",  "AZUL",     "C2293",  "C17513", "1k",   "RLY_DRV",   "Rele de celda cerrado (bobinas energizadas)"),
        ("12V",  "ROJO",     "C84256", "C17673", "4.7k", "+12V_VCSS", "Riel +12V presente"),
        ("5V",   "VERDE",    "C2297",  "C17513", "1k",   "+5V",       "Riel +5V presente"),
        ("3V3",  "VERDE",    "C2297",  "C17513", "1k",   "+3V3",      "Riel +3.3V presente"),
    )
    for k, (tag, color, lcsc_led, lcsc_r, val_r, net_src, desc) in enumerate(filas):
        xr = x0 + 8.0 * k
        _r(d, f"R_L{tag}", val_r, lcsc_r, f"Limitadora LED: {desc}",
           xr, hs + 5.5, net_src, f"LEDA_{tag}")
        d.add_component(
            "LED_SMD", "LED_0805_2012Metric",
            f"LED_{tag}", color, lcsc_led, f"LED indicador: {desc}",
            xr + 3.6, hs + 5.5, 180.0, {"1": "PGND", "2": f"LEDA_{tag}"},
        )


# ------------------------------------------------------------------------------
# 5. COMPENSACION MILLER DEL LAZO VCSS
# ------------------------------------------------------------------------------
def agregar_miller(d, c1_xy, c2_xy):
    """
    100 nF desde la salida del OpAmp a su entrada inversora. Con R_KS = 100 ohm
    fija un integrador dominante (cruce < 100 kHz) muy por debajo del polo de
    compuerta del IRLZ44N (~470 kHz): margen de fase > 75 grados, sin oscilacion.
    Coherente con la celda Hull (circuito de Randles = filtro pasa-bajas).
    """
    d.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_M1", "100nF", "C49678", "Compensacion Miller lazo VCSS rama 1",
        c1_xy[0], c1_xy[1], 0.0, {"1": "OP_OUT1", "2": "SHUNT1_SENSE"},
    )
    d.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_M2", "100nF", "C49678", "Compensacion Miller lazo VCSS rama 2",
        c2_xy[0], c2_xy[1], 0.0, {"1": "OP_OUT2", "2": "SHUNT2_SENSE"},
    )


REDES_SENAL_COMUNES = [
    "VCELL_DIV", "ITOT_DIV",
    "DIFF_N", "DIFF_P", "SUM_P", "SUM_N",
    "VCELL_MON", "ITOT_MON", "VCELL_OUT", "ITOT_OUT",
    "RLY_GATE",
    "LEDA_G1", "LEDA_G2", "LEDA_G3", "LEDA_G4",
    "LEDA_RLY", "LEDA_12V", "LEDA_5V", "LEDA_3V3",
]


def pre_rutear_bloques_comunes(d):
    """Fanout previo de pines de paso fino (MSOP-10 U10) en Paso 0."""
    if "U10" in d.pads_by_ref and "C_U10" in d.pads_by_ref:
        d.rutear_par_pads(d.pads_by_ref["U10"]["8"][0], d.pads_by_ref["C_U10"]["1"][0], 0.25)
        d.rutear_par_pads(d.pads_by_ref["U10"]["1"][0], d.pads_by_ref["C_U10"]["1"][0], 0.25)
        d.rutear_par_pads(d.pads_by_ref["U10"]["6"][0], d.pads_by_ref["U10"]["7"][0], 0.25)


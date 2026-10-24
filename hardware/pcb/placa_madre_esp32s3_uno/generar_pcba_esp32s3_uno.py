#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
PLANTA PILOTO — GENERADOR PCBA INDUSTRIAL REV 4.0 (ESP32-S3 RTOS 2.0 + UNO/NANO)
================================================================================
Implementa el circuito físico real de la Planta Piloto (config.h + nano2.ino +
BOM.md + esquematico_proteus_planta.png) con ruteo 45° Octilinear en 2 capas:
  1. Pines Exactos de Producción ESP32-S3 RTOS 2.0 (config.h):
     - Bus I2C 400kHz: SDA = GPIO 8, SCL = GPIO 9 (ADS1115 0x48, MCP4725 0x60,
       AHT20 0x38, BMP280 0x76).
     - Bus SPI Compartido Termopares: SCK = GPIO 18, SO/MISO = GPIO 19,
       CS_TC0 = GPIO 5, CS_TC1 = GPIO 4, CS_TC2 = GPIO 13, CS_TC3 = GPIO 14.
     - Relé ZCS Corte en Frío (+12V Celda): GPIO 20.
     - Enlace Serie Asíncrono UART2 (9600 bps, CRC-8): TX2 = GPIO 17 -> RX0 (D0).
  2. Pines Exactos Esclavo de Potencia Térmica (nano2.ino):
     - ZC_PIN = D3 (4N35 detector de cruce por cero AC).
     - GATE_PINS = {D7, D8, D9, D10} -> 4x MOC3021M + 4x BTA24-800BW + 4x Snubber RC.
  3. Módulo Acondicionador PH-4502C (Zócalo 6P: To, Do, Po, GND2, AGND, +5V) +
     Divisores de Precisión Kelvin 100k/200k + 100nF (Modo Diferencial A1-A0).
  4. Sumidero de Corriente VCSS Simétrico de 2 Ramas (Gm = 2.00 S):
     - Op-Amp Dual LM358 (U8:A y U8:B) + 2x Resistencias Gate 100 Ohm
     - 2x MOSFETs IRLZ44NPBF (TO-220) con Disipadores Extruidos Aletados 3D
       (AAVID 34.9x12.7x25.4 mm)
     - 2x Resistencias de Bloque Cerámico Blanco 10W 1.0 Ohm (SQP 10W 1RJ,
       50x9x9 mm, paso 55.88 mm) con lazos Kelvin hacia AIN2 y AIN3 del ADS1115.
  5. Cascada de Potencia Triple desde 12V/10A SMPS:
     - Etapa 1: Buck LM2596S-ADJ + Inductor 33uH + Diodo SS34 (12V -> 6.80V)
     - Etapa 2: Regulador Lineal LM7805CT TO-220 (6.80V -> +5.0V Analógico Limpio)
     - Etapa 3: LDO LM1117IMPX-3.3 SOT-223 (+5.0V -> +3.3V Digital/AFE)
================================================================================
"""

import os
import shutil
import sys

RUTA_MOTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "carrier_shield"))
sys.path.insert(0, RUTA_MOTOR)
from motor_pcba_industrial import PCBAIndustrialDesigner
from bloques_comunes import (
    REDES_SENAL_COMUNES,
    agregar_instrumentacion,
    agregar_leds_calentadores,
    agregar_leds_estado,
    agregar_miller,
    agregar_rele_bipolar,
    pre_rutear_bloques_comunes,
)

BOARD_W = 195.00
HS = 125.00
BOARD_H = 159.00


def construir_pcba_esp32s3_uno_rev4(directorio_base: str):
    designer = PCBAIndustrialDesigner(board_w=BOARD_W, board_h=BOARD_H, step=0.50)

    # ==========================================================================
    # 1. NODO MAESTRO: ESP32-S3-DEVKITC-1 (CON VACIADO DE COBRE ANTENA RF)
    # ==========================================================================
    # Mapa real ESP32-S3 (config.h):
    # SDA=GPIO8, SCL=GPIO9, SCK=GPIO18, MISO=GPIO19, CS0..3=GPIO5,4,13,14, TX2=GPIO17, RELE=GPIO20
    designer.add_component(
        "Connector_PinSocket_2.54mm", "PinSocket_1x20_P2.54mm_Vertical",
        "J_S3_L", "ESP32_S3_LEFT", "C124382", "Zócalo Hembra 1x20 Izquierdo ESP32-S3-DevKitC-1",
        14.0, 14.0, 0.0,
        {
            "1": "+3V3",
            "4": "CS1_GPIO4",
            "5": "CS0_GPIO5",
            "7": "RST_NANO",
            "8": "UART2_RX16",
            "9": "UART2_TX17",
            "10": "SPI_SCK18",
            "12": "I2C_SDA",
            "13": "SPI_MISO19",
            "14": "RELE_GPIO20",
            "15": "I2C_SCL",
            "17": "CS3_GPIO14",
            "18": "CS2_GPIO13",
            "19": "DGND",
            "20": "+5V",
        },
    )
    designer.add_component(
        "Connector_PinSocket_2.54mm", "PinSocket_1x20_P2.54mm_Vertical",
        "J_S3_R", "ESP32_S3_RIGHT", "C124382", "Zócalo Hembra 1x20 Derecho ESP32-S3-DevKitC-1",
        39.4, 14.0, 0.0,
        {"1": "DGND", "16": "PIN_LED_RGB", "19": "DGND", "20": "DGND"},
    )

    # Indicador Baliza LED RGB Direccionable Inteligente (WS2812B-5050 en GPIO 48)
    # Ubicado en zona central despejada (x=50, y=52) inmediatamente junto al pin 16 de J_S3_R
    designer.add_component(
        "LED_SMD", "LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm",
        "LED_RGB", "WS2812B-B", "C114586", "LED RGB Inteligente Direccionable Baliza RTOS (GPIO 48)",
        50.0, 52.0, 0.0,
        {"1": "+5V", "2": "RGB_DOUT", "3": "DGND", "4": "RGB_DIN"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_RGB", "330R_1%", "C17630", "Resistencia Serie Datos Din WS2812B (GPIO 48)",
        43.5, 52.0, 0.0,
        {"1": "PIN_LED_RGB", "2": "RGB_DIN"},
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_RGB", "100nF_X7R", "C49678", "Desacople Local LED RGB WS2812B",
        50.0, 46.0, 0.0,
        {"1": "+5V", "2": "DGND"},
    )

    # Pull-ups I2C y Amortiguación SPI SCK junto al ESP32-S3
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_SCL", "4.7k_1%", "C17673", "Pull-Up Bus I2C SCL (GPIO 9)",
        26.5, 44.0, 0.0,
        {"1": "I2C_SCL", "2": "+3V3"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_SDA", "4.7k_1%", "C17673", "Pull-Up Bus I2C SDA (GPIO 8)",
        26.5, 48.0, 0.0,
        {"1": "I2C_SDA", "2": "+3V3"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_SCK", "33R_1%", "C17638", "Amortiguador Serie Reloj SPI SCK (GPIO 18)",
        26.5, 36.0, 0.0,
        {"1": "SPI_SCK18", "2": "SPI_SCK_FILT"},
    )

    # ==========================================================================
    # 2. AFE TERMOPARES (4x MAX6675 SMD + BORNERA 8P) Y MÓDULO PH-4502C (E201C-BNC)
    # ==========================================================================
    designer.add_component(
        "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-8-5.08_1x08_P5.08mm_Horizontal",
        "J_TC", "4x_TERMOPAR_K", "C8465", "Bornera Industrial 8P 4x Termopar Tipo K",
        9.5, 108.0, 90.0,
        {
            "8": "TC0_POS", "7": "AGND",
            "6": "TC1_POS", "5": "AGND",
            "4": "TC2_POS", "3": "AGND",
            "2": "TC3_POS", "1": "AGND",
        },
    )

    cs_nets = ["CS0_GPIO5", "CS1_GPIO4", "CS2_GPIO13", "CS3_GPIO14"]
    tc_pos_nets = ["TC0_POS", "TC1_POS", "TC2_POS", "TC3_POS"]
    for idx in range(4):
        uy = 75.0 + idx * 11.5
        designer.add_component(
            "Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm",
            f"U{idx+3}", "MAX6675ISA+", "C16030", f"Digitalizador Termopar Tipo K Tina {idx+1} SPI",
            23.0, uy, 0.0,
            {
                "1": "AGND", "2": "AGND", "3": tc_pos_nets[idx], "4": "+3V3",
                "5": "SPI_SCK_FILT", "6": cs_nets[idx], "7": "SPI_MISO19",
            },
        )
        designer.add_component(
            "Capacitor_SMD", "C_0805_2012Metric",
            f"C{idx+3}", "100nF", "C49678", f"Desacople Local MAX6675 Tina {idx+1}",
            23.0, uy - 4.5, 0.0,
            {"1": "+3V3", "2": "AGND"},
        )

    # Zócalo I2C Sensor Ambiental AHT20 + BMP280 y Zócalo 6P Acondicionador PH-4502C
    designer.add_component(
        "Connector_PinSocket_2.54mm", "PinSocket_1x04_P2.54mm_Vertical",
        "J_ENV", "AHT20_BMP280_I2C", "C124375", "Zócalo 4P Sensor Ambiental I2C AHT20+BMP280 (0x38/0x76)",
        32.0, 60.0, 0.0,
        {"1": "+3V3", "2": "DGND", "3": "I2C_SCL", "4": "I2C_SDA"},
    )
    designer.add_component(
        "Connector_PinSocket_2.54mm", "PinSocket_1x06_P2.54mm_Vertical",
        "J_PH4502C", "MODULO_PH_4502C", "C124376", "Zócalo 6P Módulo Acondicionador PH-4502C (To,Do,Po,GND2,AGND,V+5V)",
        32.0, 102.0, 0.0,
        {"3": "PH_PO", "4": "PH_GND2", "5": "AGND", "6": "+5V"},
    )

    # Divisores Kelvin 100k/200k + 100nF para Modo Pseudo-Diferencial A1-A0 (Modulo_PH.cpp)
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_PH1A", "100k_0.1%", "C17407", "Divisor Kelvin Superior Po PH-4502C (100k 0.1%)",
        33.0, 82.0, 0.0,
        {"1": "PH_PO", "2": "PH_AIN1"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_PH1B", "200k_0.1%", "C25809", "Divisor Kelvin Inferior Po PH-4502C (200k 0.1%)",
        33.0, 86.5, 0.0,
        {"1": "PH_AIN1", "2": "AGND"},
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_PH1", "100nF_X7R", "C49678", "Filtro Antialiasing RC Canal A1 pH",
        33.0, 91.0, 0.0,
        {"1": "PH_AIN1", "2": "AGND"},
    )

    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_PH0A", "100k_0.1%", "C17407", "Divisor Kelvin Superior Referencia GND2 PH-4502C (100k 0.1%)",
        38.0, 82.0, 0.0,
        {"1": "PH_GND2", "2": "PH_AIN0"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_PH0B", "200k_0.1%", "C25809", "Divisor Kelvin Inferior Referencia GND2 PH-4502C (200k 0.1%)",
        38.0, 86.5, 0.0,
        {"1": "PH_AIN0", "2": "AGND"},
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_PH0", "100nF_X7R", "C49678", "Filtro Antialiasing RC Canal A0 Kelvin Ref",
        38.0, 91.0, 0.0,
        {"1": "PH_AIN0", "2": "AGND"},
    )

    # ADS1115 (16-Bit 860 SPS) + MCP4725 (12-Bit)
    designer.add_component(
        "Package_SO", "MSOP-10_3x3mm_P0.5mm",
        "U2", "ADS1115IDGSR", "C37593", "ADC 16-Bit 860SPS (A1-A0: pH Kelvin, A2: Shunt1, A3: Shunt2)",
        44.0, 82.0, 0.0,
        {
            "1": "AGND", "3": "AGND", "4": "PH_AIN0", "5": "PH_AIN1",
            "6": "SHUNT1_SENSE", "7": "SHUNT2_SENSE", "8": "+3V3",
            "9": "I2C_SDA", "10": "I2C_SCL",
        },
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C2", "100nF", "C49678", "Desacople Local ADS1115",
        49.5, 82.0, 0.0,
        {"1": "+3V3", "2": "AGND"},
    )
    designer.add_component(
        "Package_TO_SOT_SMD", "SOT-23-6",
        "U7", "MCP4725A0T-E/CH", "C144198", "DAC 12-Bit I2C Consigna VCSS (0..3.53V)",
        44.0, 94.0, 0.0,
        {"1": "VREF_DAC", "2": "AGND", "3": "+3V3", "4": "I2C_SDA", "5": "I2C_SCL", "6": "AGND"},
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C7", "100nF", "C49678", "Desacople Local MCP4725",
        44.0, 99.0, 0.0,
        {"1": "+3V3", "2": "AGND"},
    )

    # Puentes en Estrella de Tierras
    designer.add_component(
        "Inductor_SMD", "L_0805_2012Metric",
        "FB1", "BLM21PG221SN1", "C85832", "Ferrita Unión Estrella AGND a DGND",
        42.0, 68.0, 0.0,
        {"1": "AGND", "2": "DGND"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_STAR", "0R_STAR_TIE", "C17477", "Puente Estrella Punto Único DGND a PGND",
        52.0, 68.0, 0.0,
        {"1": "DGND", "2": "PGND"},
    )

    # ==========================================================================
    # 3. NODO ESCLAVO ARDUINO NANO (DIP-30) + ENLACE SERIE ASÍNCRONO + WATCHDOG HW
    # ==========================================================================
    # Pines nano2.ino:
    #   - Pin 1 (D1/TX0) -> Divisor 1.0k/2.0k -> ESP32-S3 RX2 (GPIO 16, 3.3V safe)
    #   - Pin 2 (D0/RX0) <- ESP32-S3 TX2 (GPIO 17, 3.3V directo)
    #   - Pin 3 (RESET)  <- ESP32-S3 RST_NANO (GPIO 21 para auto-recovery)
    #   - Pin 6 (D3/INT1)<- Sincronismo ZC_D3 desde Optoacoplador 4N35
    #   - Pines 10..13 (D7..D10) -> Compuertas TRIACs Tina 1..4 vía Buffer 74HCT541
    #   - Pin 27 (+5V) y Pin 29 (DGND)
    designer.add_component(
        "Module", "Arduino_Nano",
        "U_NANO", "ARDUINO_NANO_V3", "C124380", "Zócalo DIP-30 Esclavo Potencia Térmica Arduino Nano (nano2.ino)",
        65.0, 14.0, 0.0,
        {
            "1": "NANO_TX",
            "2": "UART2_TX17",
            "3": "RST_NANO",
            "4": "DGND",
            "6": "ZC_D3",
            "10": "GATE1_D7",
            "11": "GATE2_D8",
            "12": "GATE3_D9",
            "13": "GATE4_D10",
            "27": "+5V",
            "29": "DGND",
        },
    )

    # Divisor de Nivel Adaptador 5V -> 3.3V para Nano TX0 (D1) -> ESP32-S3 RX2 (GPIO 16)
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_NANO_RX1", "1.0k_1%", "C17513", "Resistencia Serie Divisor 5V a 3.3V Nano TX a ESP32 RX2",
        52.0, 22.0, 0.0,
        {"1": "NANO_TX", "2": "UART2_RX16"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_NANO_RX2", "2.0k_1%", "C25805", "Resistencia Shunt Divisor a DGND (Vout = 3.33V)",
        52.0, 27.0, 0.0,
        {"1": "UART2_RX16", "2": "DGND"},
    )

    # ==========================================================================
    # ARQUITECTURA DE ALIMENTACIÓN OPTIMIZADA: 12V -> +5.0V (LM2596S-5.0 3A) -> +3.3V (LM1117-3.3)
    # ==========================================================================
    designer.add_component(
        "Package_TO_SOT_SMD", "TO-263-5_TabPin3",
        "U_BUCK", "LM2596S-5.0", "C116713", "Regulador Buck Step-Down 12V a +5.0V Directo 3A (TI LM2596S-5.0)",
        65.0, 68.0, 0.0,
        {"1": "+12V_VCSS", "2": "BUCK_SW", "3": "PGND", "4": "+5V", "5": "PGND"},
    )
    designer.add_component(
        "Diode_SMD", "D_SMB",
        "D_BUCK", "SS34", "C8678", "Diodo Schottky rueda libre 3A 40V Buck LM2596",
        65.0, 78.5, 0.0,
        {"1": "BUCK_SW", "2": "PGND"},
    )
    designer.add_component(
        "Inductor_SMD", "L_Bourns_SRR1260",
        "L_BUCK", "33uH_3A", "C408335", "Inductor Potencia Blindado 33uH 3A Salida +5.0V",
        80.0, 67.5, 0.0,
        {"1": "BUCK_SW", "2": "+5V"},
    )
    designer.add_component(
        "Capacitor_SMD", "CP_Elec_6.3x7.7",
        "C_BUCK", "100uF_25V", "C134731", "Capacitor Electrolítico Salida Buck +5.0V",
        80.0, 78.5, 0.0,
        {"1": "+5V", "2": "PGND"},
    )
    designer.add_component(
        "Package_TO_SOT_SMD", "SOT-223-3_TabPin2",
        "U_REG3V3", "LM1117IMPX-3.3", "C6186", "Regulador Lineal LDO +3.3V Precisión",
        92.0, 68.5, 0.0,
        {"1": "DGND", "2": "+3V3", "3": "+5V"},
    )
    designer.add_component(
        "Capacitor_SMD", "C_0805_2012Metric",
        "C_3V3", "10uF_X5R", "C15850", "Filtro Salida LDO +3.3V",
        99.5, 68.5, 0.0,
        {"1": "+3V3", "2": "DGND"},
    )

    # Buffer Octal 74HCT541D
    designer.add_component(
        "Package_SO", "SOIC-20W_7.5x12.8mm_P1.27mm",
        "U1", "74HCT541D", "C5584", "Buffer Octal Aislamiento Digital de Compuertas y Relé",
        98.0, 32.0, 0.0,
        {
            "1": "PGND", "2": "RELE_GPIO20", "3": "GATE1_D7", "4": "GATE2_D8",
            "5": "GATE3_D9", "6": "GATE4_D10", "10": "PGND",
            "14": "Y_G4", "15": "Y_G3", "16": "Y_G2", "17": "Y_G1",
            "18": "Y_RELE", "19": "PGND", "20": "+5V",
        },
    )

    # ==========================================================================
    # 4. SUMIDERO VCSS SIMÉTRICO DE 2 RAMAS (OPA2171 RRIO + MILLER + 2x IRLZ44N + 2x 10W 1R0)
    # ==========================================================================
    designer.add_component(
        "Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm",
        "U8", "OPA2171AIDR", "C75253", "Amplificador Operacional Dual RRIO Precisión 36V Lazo Corriente VCSS",
        58.0, 84.0, 0.0,
        {
            "1": "OP_OUT1", "2": "SHUNT1_SENSE", "3": "VREF_DAC", "4": "PGND",
            "5": "VREF_DAC", "6": "SHUNT2_SENSE", "7": "OP_OUT2", "8": "+12V_VCSS",
        },
    )
    agregar_miller(designer, c1_xy=(58.0, 77.5), c2_xy=(58.0, 90.5))

    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_G1", "100R_1%", "C17408", "Resistencia Compuerta Rama 1 MOSFET Q_VCSS1",
        67.0, 83.0, 0.0,
        {"1": "OP_OUT1", "2": "GATE_M1"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_G2", "100R_1%", "C17408", "Resistencia Compuerta Rama 2 MOSFET Q_VCSS2",
        67.0, 89.0, 0.0,
        {"1": "OP_OUT2", "2": "GATE_M2"},
    )

    designer.add_component(
        "Package_TO_SOT_THT", "TO-220-3_Vertical",
        "Q_VCSS1", "IRLZ44NPBF", "C209995", "MOSFET N Lógico 55V 47A 22mR Rama 1 VCSS + Disipador TO-220",
        76.0, 89.0, 0.0,
        {"1": "GATE_M1", "2": "VCSS_DRAIN", "3": "SHUNT1_PWR"},
        attach_to220_heatsink=True,
    )
    designer.add_component(
        "Package_TO_SOT_THT", "TO-220-3_Vertical",
        "Q_VCSS2", "IRLZ44NPBF", "C209995", "MOSFET N Lógico 55V 47A 22mR Rama 2 VCSS + Disipador TO-220",
        106.0, 89.0, 0.0,
        {"1": "GATE_M2", "2": "VCSS_DRAIN", "3": "SHUNT2_PWR"},
        attach_to220_heatsink=True,
    )

    # 2x Resistencias de Bloque Cerámico Blanco 10W 1.0 Ohm (SQP 10W 1RJ, 50x9x9 mm)
    designer.add_component(
        "Resistor_THT", "R_Axial_Power_L50.0mm_W9.0mm_P55.88mm",
        "R_SH1", "SQP_10W_1R0_J", "C165812", "Resistencia Bloque Cerámico Blanco Cemento 10W 1.0 Ohm Rama 1",
        66.0, 98.0, 0.0,
        {"1": "SHUNT1_PWR", "2": "PGND"},
    )
    designer.add_component(
        "Resistor_THT", "R_Axial_Power_L50.0mm_W9.0mm_P55.88mm",
        "R_SH2", "SQP_10W_1R0_J", "C165812", "Resistencia Bloque Cerámico Blanco Cemento 10W 1.0 Ohm Rama 2",
        66.0, 110.0, 0.0,
        {"1": "SHUNT2_PWR", "2": "PGND"},
    )

    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_KS1", "100R_0.1%", "C23186", "Toma Kelvin Sensado Corriente Shunt 1 (Hacia OPA2171:2 y ADS1115:AIN2)",
        58.0, 98.0, 0.0,
        {"1": "SHUNT1_PWR", "2": "SHUNT1_SENSE"},
    )
    designer.add_component(
        "Resistor_SMD", "R_0805_2012Metric",
        "R_KS2", "100R_0.1%", "C23186", "Toma Kelvin Sensado Corriente Shunt 2 (Hacia OPA2171:6 y ADS1115:AIN3)",
        58.0, 110.0, 0.0,
        {"1": "SHUNT2_PWR", "2": "SHUNT2_SENSE"},
    )

    # Relé 1 de Corte Bipolar ZCS (Ánodo +12V) + Relé 2 (Cátodo Drain) + TVS + Borneras Potencia
    designer.add_component(
        "Relay_THT", "Relay_SPDT_SANYOU_SRD_Series_Form_C",
        "K_ZCS", "SRD-05VDC-SL-C", "C35449", "Relé 1 de Corte Bipolar: Abre el ÁNODO (+12V) de la Celda Hull (GPIO 20)",
        138.0, 85.0, 0.0,
        {"1": "+12V_VCSS", "2": "RLY_DRV", "3": "CELL_ANODE", "5": "PGND"},
    )
    designer.add_component(
        "Diode_SMD", "D_SMB",
        "D_TVS_CELL", "SMBJ18CA", "C123805", "Diodo TVS Bidireccional 600W Protección Celda Hull",
        146.0, 100.0, 90.0,
        {"1": "CELL_ANODE", "2": "CELL_CATHODE"},
    )
    designer.add_component(
        "Diode_SMD", "D_SMB",
        "D_TVS1", "SMBJ15A", "C123828", "Diodo TVS Unidireccional 600W Supresor Riel +12V",
        131.0, 102.0, 90.0,
        {"1": "+12V_VCSS", "2": "PGND"},
    )
    designer.add_component(
        "Capacitor_SMD", "CP_Elec_6.3x7.7",
        "C_BULK1", "100uF_25V", "C134731", "Capacitor Electrolítico Entrada Principal +12V",
        138.5, 102.0, 90.0,
        {"1": "+12V_VCSS", "2": "PGND"},
    )
    designer.add_component(
        "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
        "J_CELL", "CELDA_HULL_OUT", "C8459", "Bornera Alta Corriente Salida Celda Hull (OUT+ Ánodo / OUT- Cátodo)",
        186.0, 78.0, 270.0,
        {"1": "CELL_ANODE", "2": "CELL_CATHODE"},
    )
    designer.add_component(
        "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
        "J_PWR_12V", "ENTRADA_12V_10A", "C8459", "Bornera Entrada Principal Fuente SMPS 12V / 10A",
        186.0, 98.0, 270.0,
        {"1": "+12V_VCSS", "2": "PGND"},
    )

    # Bloques Comunes Rev 5.0: Relé 2 Bipolar + Driver PMOS, Instrumentación V/I y LEDs de Estado
    agregar_rele_bipolar(designer, hs=HS, x_k2=138.0, x_q=165.0)
    agregar_instrumentacion(designer, hs=HS, x_term=186.0)
    agregar_leds_calentadores(designer, x_r=113.0, x_led=118.0, ry_list=[14.0, 34.0, 54.0, 74.0], dy=8.0)
    agregar_leds_estado(designer, hs=HS, x0=98.0)

    # ==========================================================================
    # 5. ETAPA DE POTENCIA AC 4 CANALES (DISIPADORES COMPACTOS + 2 CLEMAS SEGREGADAS)
    # ==========================================================================
    y_gates = ["Y_G1", "Y_G2", "Y_G3", "Y_G4"]
    opt_anodes = ["OPT_A1", "OPT_A2", "OPT_A3", "OPT_A4"]
    tr_gates = ["TR_G1", "TR_G2", "TR_G3", "TR_G4"]
    ac_outs = ["AC_T1", "AC_T2", "AC_T3", "AC_T4"]

    for idx in range(4):
        ry = 14.0 + idx * 20.0
        designer.add_component(
            "Resistor_SMD", "R_0805_2012Metric",
            f"R_OPT{idx+1}", "330R", "C17630", f"Resistencia Limitadora LED Optotriac Tina {idx+1}",
            110.0, ry, 0.0,
            {"1": y_gates[idx], "2": opt_anodes[idx]},
        )
        designer.add_component(
            "Package_DIP", "DIP-6_W7.62mm",
            f"U_OPT{idx+1}", "MOC3021M", "C123202", f"Optotriac Aislamiento Galvánico 5000Vrms Tina {idx+1}",
            118.0, ry - 1.27, 0.0,
            {"1": opt_anodes[idx], "2": "PGND", "4": tr_gates[idx], "6": ac_outs[idx]},
        )
        designer.add_component(
            "Resistor_SMD", "R_1206_3216Metric",
            f"R_TR{idx+1}", "360R_1206", "C17930", f"Resistencia Disparo Compuerta TRIAC BTA24 Tina {idx+1}",
            132.0, ry, 0.0,
            {"1": tr_gates[idx], "2": f"BG_{idx+1}"},
        )
        designer.add_component(
            "Package_TO_SOT_THT", "TO-220-3_Vertical",
            f"TR{idx+1}", "BTA24-800BW", "C76203", f"TRIAC Potencia 25A 800V Calentador Tina {idx+1} + Disipador Aletado",
            148.0, ry - 2.0, 0.0,
            {"1": "AC_LINE", "2": ac_outs[idx], "3": f"BG_{idx+1}"},
            attach_to220_heatsink=True,
        )
        designer.add_component(
            "Resistor_SMD", "R_2512_6332Metric",
            f"R_SN{idx+1}", "39R_1W", "C25410", f"Resistencia Snubber dV/dt 39 Ohm 1W Tina {idx+1}",
            162.0, ry + 3.0, 0.0,
            {"1": ac_outs[idx], "2": "AC_LINE"},
        )

    designer.add_component(
        "Package_DIP", "DIP-6_W7.62mm",
        "U_ZC", "4N35", "C575341", "Optoacoplador Sincronismo Cruce por Cero AC (Pin D3)",
        90.0, 14.0, 0.0,
        {"4": "DGND", "5": "ZC_D3"},
    )

    # 1) Bornera de Entrada AC de Red (Fase L, Neutro N, Tierra PE)
    designer.add_component(
        "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal",
        "J_AC_IN", "ALIMENTACION_RED_AC", "C8461", "Bornera 3P Entrada Red 120/220V AC (Fase L, Neutro N, Tierra PE)",
        186.0, 12.0, 270.0,
        {"1": "AC_LINE", "2": "AC_NEUTRAL", "3": "AC_EARTH"},
    )
    # 2) Bornera de Salida a 4 Calentadores (4 Pares: Fase Conmutada + Neutro Retorno Directo)
    designer.add_component(
        "TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-8-5.08_1x08_P5.08mm_Horizontal",
        "J_HEATERS", "SALIDA_4_CALENTADORES", "C8465", "Bornera 8P Calentadores 4 Tinas (Pares Fase/Neutro)",
        186.0, 32.0, 270.0,
        {
            "1": "AC_T1", "2": "AC_NEUTRAL",
            "3": "AC_T2", "4": "AC_NEUTRAL",
            "5": "AC_T3", "6": "AC_NEUTRAL",
            "7": "AC_T4", "8": "AC_NEUTRAL",
        },
    )

    for idx_m, (mx, my) in enumerate([(4.5, 4.5), (BOARD_W - 4.5, 4.5), (4.5, BOARD_H - 4.5), (BOARD_W - 4.5, BOARD_H - 4.5)]):
        designer.add_component(
            "MountingHole", "MountingHole_3.2mm_M3_Pad",
            f"MH{idx_m+1}", "M3_DIN", "N/A", "Montaje Mecánico M3",
            mx, my, 0.0, {}, in_bom=False,
        )

    # ==========================================================================
    # 6. ZONAS KEEPOUT RF Y 3 PLANOS DE TIERRA PARTICIONADOS EN 4 CAPAS (In1.Cu + B.Cu)
    # ==========================================================================
    designer.add_keepout_rf(10.0, 2.0, 43.0, 11.5)

    for gnd_layer in ("In1.Cu", "B.Cu"):
        designer.add_copper_zone("AGND", gnd_layer, 3.0, 66.5, 51.0, BOARD_H - 3.0, clearance=0.35, priority=1)
        designer.add_copper_zone("DGND", gnd_layer, 3.0, 2.5, 114.0, 66.0, clearance=0.35, priority=1)
        designer.add_copper_zone("PGND", gnd_layer, 51.5, 66.5, 191.0, BOARD_H - 3.0, clearance=0.35, priority=1)

    # ==========================================================================
    # 7. AUTORUTEO OCTILINEAR 45° EN 4 CAPAS (F.Cu, In1.Cu, In2.Cu, B.Cu)
    # ==========================================================================
    # Paso 0: Fanout inmediato de rieles locales, LED RGB y bus de Neutro AC
    designer.rutear_par_pads(
        designer.pads_by_ref["R_RGB"]["2"][0],
        designer.pads_by_ref["LED_RGB"]["4"][0],
        0.35,
    )
    designer.rutear_par_pads(
        designer.pads_by_ref["C_RGB"]["1"][0],
        designer.pads_by_ref["LED_RGB"]["1"][0],
        0.35,
    )
    designer.rutear_par_pads(
        designer.pads_by_ref["C_RGB"]["2"][0],
        designer.pads_by_ref["LED_RGB"]["3"][0],
        0.35,
    )
    designer.rutear_par_pads(
        designer.pads_by_ref["LED_RGB"]["3"][0],
        designer.pads_by_ref["J_S3_R"]["19"][0],
        0.35,
    )
    # Backbone de retornos Neutro AC directo
    p_ac_n = designer.pads_by_ref["J_AC_IN"]["2"][0]
    for hp in ("2", "4", "6", "8"):
        designer.rutear_par_pads(p_ac_n, designer.pads_by_ref["J_HEATERS"][hp][0], 1.50)

    designer.rutear_par_pads(
        designer.pads_by_ref["U2"]["8"][0],
        designer.pads_by_ref["C2"]["1"][0],
        0.30,
    )
    designer.rutear_par_pads(
        designer.pads_by_ref["C2"]["1"][0],
        designer.pads_by_ref["C7"]["1"][0],
        0.30,
    )
    designer.rutear_par_pads(
        designer.pads_by_ref["U7"]["2"][0],
        designer.pads_by_ref["U7"]["6"][0],
        0.25,
    )
    pre_rutear_bloques_comunes(designer)
    designer.rutear_red_completa("BUCK_SW", width=1.20)
    if len(designer.pads_by_ref["U_BUCK"].get("3", [])) >= 2:
        designer.rutear_par_pads(
            designer.pads_by_ref["U_BUCK"]["3"][0],
            designer.pads_by_ref["U_BUCK"]["3"][1],
            0.80,
        )
    if "U1" in designer.pads_by_ref and "19" in designer.pads_by_ref["U1"] and "1" in designer.pads_by_ref["U1"]:
        designer.rutear_par_pads(
            designer.pads_by_ref["U1"]["19"][0],
            designer.pads_by_ref["U1"]["1"][0],
            0.35,
        )
    if "U_OPT4" in designer.pads_by_ref and "4" in designer.pads_by_ref["U_OPT4"]:
        designer.rutear_par_pads(
            designer.pads_by_ref["U_OPT4"]["4"][0],
            designer.pads_by_ref["R_TR4"]["1"][0],
            0.35,
        )

    # 1°: Ruteamos las redes de señal y buses digitales (MSOP-10 ADS1115 de arriba hacia abajo, CSx antes de MISO/SCK)
    redes_senal = [
        "I2C_SCL", "I2C_SDA",
        "PH_AIN0", "PH_AIN1", "SHUNT2_SENSE", "SHUNT1_SENSE",
        "VREF_DAC", "PH_PO", "PH_GND2",
        "OP_OUT1", "OP_OUT2", "GATE_M1", "GATE_M2",
        "TC0_POS", "TC1_POS", "TC2_POS", "TC3_POS",
        "SPI_MISO19", "CS0_GPIO5", "CS2_GPIO13", "CS1_GPIO4", "CS3_GPIO14",
        "SPI_SCK18", "SPI_SCK_FILT",
        "UART2_TX17", "UART2_RX16", "NANO_TX", "RST_NANO", "RELE_GPIO20",
        "GATE1_D7", "GATE2_D8", "GATE3_D9", "GATE4_D10", "ZC_D3",
        "Y_RELE", "Y_G1", "Y_G2", "Y_G3", "Y_G4",
        "OPT_A1", "OPT_A2", "OPT_A3", "OPT_A4",
        "TR_G1", "TR_G2", "TR_G3", "TR_G4",
        "BG_1", "BG_2", "BG_3", "BG_4",
        "PIN_LED_RGB", "RGB_DIN",
    ] + REDES_SENAL_COMUNES
    for net_name in redes_senal:
        w_sig = 0.25 if net_name in ("PH_AIN0", "PH_AIN1", "SHUNT1_SENSE", "SHUNT2_SENSE", "I2C_SDA", "I2C_SCL", "VCELL_DIV", "ITOT_DIV") else 0.35
        ok = designer.rutear_red_completa(net_name, width=w_sig)
        print(f"  [Ruteo 45° Señal]    {net_name:15s} (w={w_sig:.2f}mm) -> {'OK' if ok else 'PARCIAL'}")

    # Excluir U2.8, C2.1, U10.1 y U10.8 de la lista pendiente de +3V3 porque ya fueron unidos en el Paso 0
    nid_3v3 = designer.get_net_id("+3V3")
    designer.pads_by_net[nid_3v3] = [
        p for p in designer.pads_by_net[nid_3v3]
        if not (
            (p.ref == "U2" and p.pad_num == "8")
            or (p.ref == "C2" and p.pad_num == "1")
            or (p.ref == "U10" and p.pad_num in ("1", "8"))
        )
    ]
    nid_agnd = designer.get_net_id("AGND")
    designer.pads_by_net[nid_agnd] = [
        p for p in designer.pads_by_net[nid_agnd]
        if not (p.ref == "U10" and p.pad_num == "6")
    ]

    redes_alta_corriente = [
        ("CELL_CATHODE", 2.20),
        ("CELL_ANODE", 2.20),
        ("VCSS_DRAIN", 2.00),
        ("SHUNT1_PWR", 2.00),
        ("SHUNT2_PWR", 2.00),
        ("+12V_VCSS", 1.80),
        ("AC_NEUTRAL", 2.00),
        ("AC_LINE", 1.80),
        ("AC_T1", 1.80),
        ("AC_T2", 1.80),
        ("AC_T3", 1.80),
        ("AC_T4", 1.80),
        ("AC_EARTH", 1.20),
        ("RLY_DRV", 0.60),
        ("+5V", 0.60),
        ("+3V3", 0.35),
    ]
    for net_name, w in redes_alta_corriente:
        ok = designer.rutear_red_completa(net_name, width=w)
        print(f"  [Ruteo 45° Potencia] {net_name:15s} (w={w:.2f}mm) -> {'OK' if ok else 'PARCIAL'}")

    for gnd_net in ("AGND", "DGND", "PGND"):
        ok = designer.rutear_red_completa(gnd_net, width=0.45)
        print(f"  [Ruteo 45° Tierra]   {gnd_net:15s} (w=0.45mm) -> {'OK' if ok else 'PARCIAL'}")

    textos_fab = [
        (90.0, 4.0, "PLACA MADRE INDUSTRIAL PCBA REV 5.0 — ESP32-S3 RTOS 2.0 + ARDUINO NANO (CORTE BIPOLAR + BUCK 5V + INSTRUMENTACION V/I + MILLER)", 1.25),
        (26.0, 62.0, "NODO MAESTRO: ESP32-S3-DEVKITC-1", 1.00),
        (72.0, 62.0, "NODO ESCLAVO: ARDUINO NANO (UART DUAL + WDT)", 1.00),
        (30.0, 116.5, "ZONA AFE: 4x MAX6675 + ZOCALO PH-4502C + DIVISOR KELVIN + ADS1115 #1 & #2", 1.00),
        (88.0, 63.5, "BUCK LM2596S-5.0 (3A) + LDO LM1117-3.3", 1.00),
        (110.0, 155.0, "VCSS SIMETRICO (OPA2171 + MILLER + 2x IRLZ44N + 2x RELE BIPOLAR + INSTRUMENTACION V/I)", 0.95),
        (148.0, 6.5, "ETAPA AC AISLADA + 4x LED ESTADO", 1.00),
    ]

    ruta_pcb = os.path.join(directorio_base, "placa_madre_esp32s3_uno.kicad_pcb")
    resumen = designer.guardar_y_exportar_manufactura(
        ruta_pcb=ruta_pcb,
        titulo_placa="Placa Madre Industrial PCBA Rev 5.0 — ESP32-S3 RTOS 2.0 + UNO/Nano (VCSS Bipolar + Buck 5V + Instrumentacion V/I + Miller)",
        rev_placa="5.0-TURNKEY",
        textos_fab=textos_fab,
    )
    print(f"[DRC ESP32-S3 + UNO REV 5.0] Violaciones: {resumen['violations']} | Sin conectar: {resumen['unconnected']}")

    # Sincronizar con C:\Proyecto\Proyecto\hardware_pcb
    dir_proyecto_orig = r"C:\Proyecto\Proyecto\hardware_pcb"
    os.makedirs(dir_proyecto_orig, exist_ok=True)
    for item in os.listdir(directorio_base):
        s_path = os.path.join(directorio_base, item)
        d_path = os.path.join(dir_proyecto_orig, item)
        if os.path.isdir(s_path):
            if os.path.exists(d_path):
                shutil.rmtree(d_path)
            shutil.copytree(s_path, d_path)
        else:
            shutil.copy2(s_path, d_path)


if __name__ == "__main__":
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    construir_pcba_esp32s3_uno_rev4(dir_actual)

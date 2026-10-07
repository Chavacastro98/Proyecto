#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador Maestro del Diagrama de Bloques Funcional de Hardware Moderno (sistema.png)
Planta Piloto Modular de Electrodeposición y Galvanoplastia (ESP32-S3 / Arduino Nano / SCADA)

Versión Perfeccionada:
- Cero solapamiento de textos o tarjetas
- Espaciado milimétrico y tipografía nítida de alta visibilidad
- Inclusión formal del MÓDULO ZCS DUAL (Detector Cruce por Cero AC 60Hz 4N35 + Relé de Corte DC GPIO 20)
- Inclusión formal de la MEDICIÓN PSEUDO-DIFERENCIAL de pH (A1 = Po, A0 = AGND limpia, DeltaV = A1 - A0)
- Preservación y enriquecimiento de todos los módulos del sistema.png original
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

# Resolución de salida Ultra-HD
W = 2700
H = 1800

# Tipografías TrueType de Windows
FONT_TITLE_MAIN = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
FONT_SUB_MAIN   = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 21)
FONT_CARD_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 21)
FONT_CARD_SUB   = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_CARD_BODY  = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
FONT_CARD_BOLD  = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
FONT_BADGE      = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_WIRE_LABEL = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_LEGEND     = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_FORMULA    = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 16)
FONT_FORMULA_SM = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 12)

# Paleta Dark Industrial de Alta Fidelidad
C_BG            = (10, 15, 29)       # Azul noche técnico (#0a0f1d)
C_GRID          = (20, 30, 52)       # Puntos de retícula
C_CARD_FILL     = (15, 23, 42)       # Slate 900 sólido (#0f172a)
C_TEXT_WHITE    = (255, 255, 255)    # Blanco puro
C_TEXT_MUTED    = (148, 163, 184)    # Slate 400
C_TEXT_BODY     = (226, 232, 240)    # Slate 200 de alto contraste

# Colores de buses y funciones
C_ESP32         = (14, 165, 233)     # Sky Blue (#0ea5e9)
C_NANO          = (168, 85, 247)     # Violeta (#a855f7)
C_I2C           = (6, 182, 212)      # Cyan (#06b6d4)
C_SPI           = (245, 158, 11)     # Amber (#f59e0b)
C_UART          = (236, 72, 153)     # Pink / Magenta (#ec4899)
C_PH_DIFF       = (16, 185, 129)     # Emerald Green (#10b981)
C_ZCS           = (234, 179, 8)      # Yellow Gold (#eab308)
C_VCSS          = (139, 92, 246)     # Purple (#8b5cf6)
C_TRIAC         = (239, 68, 68)      # Coral Red (#ef4444)
C_POWER         = (20, 184, 166)     # Teal (#14b8a6)
C_HULL          = (59, 130, 246)     # Royal Blue (#3b82f6)

def draw_hud_brackets(draw, bbox, color, length=14, width=2):
    x1, y1, x2, y2 = bbox
    # TL
    draw.line([(x1, y1), (x1 + length, y1)], fill=color, width=width)
    draw.line([(x1, y1), (x1, y1 + length)], fill=color, width=width)
    # TR
    draw.line([(x2, y1), (x2 - length, y1)], fill=color, width=width)
    draw.line([(x2, y1), (x2 - length, y1 + length)], fill=color, width=width)
    # BL
    draw.line([(x1, y2), (x1 + length, y2)], fill=color, width=width)
    draw.line([(x1, y2), (x1, y2 - length)], fill=color, width=width)
    # BR
    draw.line([(x2, y2), (x2 - length, y2)], fill=color, width=width)
    draw.line([(x2, y2), (x2, y2 - length)], fill=color, width=width)

def draw_module_card(draw, bbox, title, subtitle, badge_text, theme_color, lines=[], badge_bg=None):
    x1, y1, x2, y2 = bbox
    # 1. Fondo sólido Slate 900
    draw.rounded_rectangle(bbox, radius=12, fill=C_CARD_FILL, outline=theme_color, width=2)
    
    # 2. Cabecera con tinte del color temático
    header_h = 54
    hdr_box = [(x1 + 2, y1 + 2), (x2 - 2, y1 + header_h)]
    hdr_tint = (int(theme_color[0]*0.22 + 15*0.78), int(theme_color[1]*0.22 + 23*0.78), int(theme_color[2]*0.22 + 42*0.78))
    draw.rounded_rectangle(hdr_box, radius=10, fill=hdr_tint)
    draw.line([(x1, y1 + header_h), (x2, y1 + header_h)], fill=theme_color, width=2)
    
    # 3. HUD Corner Brackets
    draw_hud_brackets(draw, (x1 - 3, y1 - 3, x2 + 3, y2 + 3), theme_color, length=14, width=2)
    
    # 4. Textos de Cabecera
    draw.text((x1 + 16, y1 + 7), title, fill=C_TEXT_WHITE, font=FONT_CARD_TITLE)
    draw.text((x1 + 16, y1 + 31), subtitle, fill=theme_color, font=FONT_CARD_SUB)
    
    # 5. Badge a la derecha
    if badge_text:
        bg_col = badge_bg if badge_bg else theme_color
        tb = FONT_BADGE.getbbox(badge_text)
        bw = tb[2] - tb[0] + 18
        bx1 = x2 - bw - 14
        by1 = y1 + 14
        draw.rounded_rectangle([(bx1, by1), (bx1 + bw, by1 + 26)], radius=6, fill=bg_col)
        draw.text((bx1 + 9, by1 + 4), badge_text, fill=(255, 255, 255), font=FONT_BADGE)
        
    # 6. Lista de especificaciones técnicas
    curr_y = y1 + header_h + 12
    for item in lines:
        if isinstance(item, tuple):
            prefix, text, col = item
            draw.text((x1 + 16, curr_y), prefix, fill=col, font=FONT_CARD_BOLD)
            tb = FONT_CARD_BOLD.getbbox(prefix)
            draw.text((x1 + 16 + (tb[2] - tb[0]) + 5, curr_y), text, fill=C_TEXT_BODY, font=FONT_CARD_BODY)
        else:
            draw.text((x1 + 16, curr_y), item, fill=C_TEXT_BODY, font=FONT_CARD_BODY)
        curr_y += 22

def draw_wire(draw, points, color, width=3, is_dashed=False, arrow_end=True, arrow_start=False):
    if is_dashed:
        dash_len = 10
        gap_len = 6
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                continue
            ux, uy = dx / dist, dy / dist
            cov = 0
            while cov < dist:
                step = min(dash_len, dist - cov)
                s_pt = (p1[0] + ux * cov, p1[1] + uy * cov)
                e_pt = (p1[0] + ux * (cov + step), p1[1] + uy * (cov + step))
                draw.line([s_pt, e_pt], fill=color, width=width)
                cov += dash_len + gap_len
    else:
        draw.line(points, fill=color, width=width)
        
    # Flecha al final
    if arrow_end and len(points) >= 2:
        p_last, p_prev = points[-1], points[-2]
        ang = math.atan2(p_last[1] - p_prev[1], p_last[0] - p_prev[0])
        asz = 11
        a1 = (p_last[0] - asz * math.cos(ang - math.pi/6), p_last[1] - asz * math.sin(ang - math.pi/6))
        a2 = (p_last[0] - asz * math.cos(ang + math.pi/6), p_last[1] - asz * math.sin(ang + math.pi/6))
        draw.polygon([p_last, a1, a2], fill=color)

    # Flecha al inicio
    if arrow_start and len(points) >= 2:
        p_first, p_next = points[0], points[1]
        ang = math.atan2(p_first[1] - p_next[1], p_first[0] - p_next[0])
        asz = 11
        a1 = (p_first[0] - asz * math.cos(ang - math.pi/6), p_first[1] - asz * math.sin(ang - math.pi/6))
        a2 = (p_first[0] - asz * math.cos(ang + math.pi/6), p_first[1] - asz * math.sin(ang + math.pi/6))
        draw.polygon([p_first, a1, a2], fill=color)

def draw_pill(draw, cx, cy, text, color, bg=(15, 23, 42)):
    tb = FONT_WIRE_LABEL.getbbox(text)
    pw = tb[2] - tb[0] + 16
    ph = 22
    x1, y1 = cx - pw // 2, cy - ph // 2
    draw.rounded_rectangle([(x1, y1), (x1 + pw, y1 + ph)], radius=5, fill=bg, outline=color, width=1)
    draw.text((x1 + 8, y1 + 2), text, fill=color, font=FONT_WIRE_LABEL)

def render_diagram():
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)
    
    # 1. Retícula de ingeniería técnica
    grid_spacing = 38
    for x in range(0, W, grid_spacing):
        for y in range(0, H, grid_spacing):
            draw.point((x, y), fill=C_GRID)

    # =========================================================================
    # BANNER SUPERIOR (HUD HEADER)
    # =========================================================================
    banner_h = 135
    draw.rectangle([(0, 0), (W, banner_h)], fill=(7, 12, 22))
    draw.line([(0, banner_h), (W, banner_h)], fill=C_ESP32, width=4)
    draw.line([(0, banner_h - 4), (W, banner_h - 4)], fill=(30, 58, 138), width=1)

    draw.text((45, 18), "DIAGRAMA DE BLOQUES FUNCIONAL DE HARDWARE — ARQUITECTURA INTEGRAL", fill=C_TEXT_WHITE, font=FONT_TITLE_MAIN)
    draw.text((45, 68), "ESP32-S3 Dual-Core Master + Arduino Nano Slave • Sensado Pseudo-Diferencial pH • Sincronización ZCS y VCSS", fill=C_ESP32, font=FONT_SUB_MAIN)
    draw.text((45, 98), "Protocolo Experimental Zinc-Níquel sobre Al 6061-T6 (VUGR) • Buses I2C Fast-Mode (400kHz), SPI (4MHz) y UART2 (9600 Baud)", fill=C_TEXT_MUTED, font=FONT_CARD_BODY)

    # Badges en Header
    badges = [
        ("ESP32-S3 SMP @ 240 MHz", C_ESP32),
        ("ZCS AC Cruce Cero (4N35) + Relé DC", C_ZCS),
        ("pH Pseudo-Diferencial (A1-A0)", C_PH_DIFF),
        ("VCSS Shunts 10W (0-7.06A)", C_VCSS),
    ]
    bx = W - 45
    by = 40
    for b_txt, b_col in reversed(badges):
        tb = FONT_BADGE.getbbox(b_txt)
        bw = tb[2] - tb[0] + 24
        bx -= bw
        draw.rounded_rectangle([(bx, by), (bx + bw, by + 34)], radius=8, fill=(15, 23, 42), outline=b_col, width=2)
        draw.text((bx + 12, by + 7), b_txt, fill=b_col, font=FONT_BADGE)
        bx -= 15

    # =========================================================================
    # COORDENADAS LIMPIAS DE TARJETAS (PERFECTAMENTE AJUSTADAS)
    # =========================================================================

    # FILA 1: SUPERIOR (y: 165 .. 495)
    CARD_PSU     = (45, 165, 360, 485)       # Alimentación Híbrida (w: 315)
    CARD_DAC     = (380, 165, 735, 485)      # DAC MCP4725 (w: 355)
    CARD_ENV     = (755, 165, 1055, 485)     # Ambiental AHT20+BMP280 (w: 300)
    CARD_ADS     = (1075, 165, 1785, 485)    # ADC ADS1115 16-bit (w: 710)
    CARD_PH      = (1985, 165, 2655, 485)    # Sensor pH PH-4502C (w: 670)

    # FILA 2: CENTRO (y: 545 .. 1165)
    CARD_VCSS    = (45, 545, 685, 915)       # Sumidero VCSS Lazo Cerrado (w: 640)
    CARD_HULL    = (45, 955, 685, 1275)      # Celda Hull 267 mL (w: 640)
    CARD_ESP     = (715, 565, 1865, 1175)    # ESP32-S3 Maestro Dual-Core (w: 1150)
    CARD_SPI     = (1895, 545, 2655, 1175)   # 4x MAX6675 Termopares SPI (w: 760)

    # FILA 3: INFERIOR (y: 1245 .. 1705)
    CARD_RELE_ZCS= (45, 1315, 685, 1705)     # Relé ZCS DC Corte Galvánico (+12V VDD) (w: 640)
    CARD_NANO    = (715, 1245, 1635, 1705)   # Arduino Nano Esclavo AC (w: 920)
    CARD_ZCS_AC  = (1665, 1245, 2165, 1705)  # Detector ZCS AC 60Hz (Opto 4N35) (w: 500)
    CARD_TRIAC   = (2195, 1245, 2655, 1705)  # 4x Módulos Opto-TRIACs BTA24 (w: 460)

    # =========================================================================
    # DIBUJAR TARJETAS MODULARES CON LÍNEAS COMPLETAS
    # =========================================================================

    # 1. FUENTE HÍBRIDA
    draw_module_card(draw, CARD_PSU,
        "ALIMENTACIÓN", "Topología Híbrida", "12V / 10A", C_POWER,
        lines=[
            ("• SMPS 12V 10A:", "Fuente primaria", C_POWER),
            ("• Buck LM2596:", "12V -> 6.80V DC (Alivio)", C_POWER),
            ("• LDO LM7805:", "6.80V -> +5V (Nano/Relé/Op)", C_POWER),
            ("• LM1117-3.3:", "+5V -> +3.3V (ESP32/ADC)", C_POWER),
            ("• Filtros LC:", "Supresión rizo 150 kHz", C_TEXT_MUTED),
            ("• Derating >60%:", "Operación térmica segura", C_TEXT_MUTED),
        ])

    # 2. DAC MCP4725
    draw_module_card(draw, CARD_DAC,
        "DAC MCP4725", "Generador Consigna", "I2C 0x60", C_I2C,
        lines=[
            ("• Resolución:", "12 bits (4096 pasos, ~0.86 mV)", C_I2C),
            ("• Consigna Vref:", "0.00 V a 3.53 V continuo", C_I2C),
            ("• EEPROM NVS:", "Retención offset calibrado", C_TEXT_MUTED),
            ("• Transconductancia:", "Gm = 2.0 S hacia etapa VCSS", C_VCSS),
            ("• Salida VOUT:", "Hacia entrada no-inversora", C_TEXT_WHITE),
            ("• RefGND Dedicada:", "Masa sin bucles de tierra", C_TEXT_MUTED),
        ])

    # 3. AMBIENTAL AHT20 + BMP280
    draw_module_card(draw, CARD_ENV,
        "AHT20 + BMP280", "Ambiente Cabina", "I2C 0x38/76", C_I2C,
        lines=[
            ("• AHT20 (0x38):", "Temperatura y HR (±2%)", C_I2C),
            ("• BMP280 (0x76):", "Presión Barométrica (hPa)", C_I2C),
            ("• Muestreo:", "Cadencia periódica 1 Hz", C_TEXT_MUTED),
            ("• Monitoreo:", "Detección de vapores", C_TEXT_MUTED),
        ])

    # 4. ADC ADS1115 (16-bit) CON MEDIDA PSEUDO-DIFERENCIAL
    draw_module_card(draw, CARD_ADS,
        "ADC ADS1115", "Convertidor 16-bit Alta Precisión (860 SPS)", "I2C 0x48", C_I2C,
        lines=[
            ("• Bus I2C Fast-Mode:", "Velocidad 400 kHz @ 860 SPS continuo sin demoras de conmutación", C_I2C),
            ("• Filtros RC Dedicados:", "Redes pasa-bajas analógicas (100 Ω + 100 nF) en canales A0 a A3", C_TEXT_MUTED),
            ("• CANAL A0 (Inversor Ref-):", "Masa Analógica Limpia AGND (PH-4502C) [PSEUDO-DIFERENCIAL]", C_PH_DIFF),
            ("• CANAL A1 (No-Inversor In+):", "Voltaje Po Sonda de Vidrio pH [PSEUDO-DIFERENCIAL]", C_PH_DIFF),
            ("• CANALES A2 y A3:", "Sensado Caída Shunts Cerámicos SH1 y SH2 VCSS (1.0 V/A)", C_VCSS),
            ("• Rechazo Modo Común:", "Alto CMRR inmune a ruidos EMI de TRIACs y transitorios de celda", C_TEXT_WHITE),
            ("• Fórmula Diferencial:", "V_ph = V(A1) - V(A0)  [Cancelación total de corrientes de masa]", C_PH_DIFF),
        ])

    # 5. SENSOR pH PH-4502C (PSEUDO-DIFERENCIAL)
    draw_module_card(draw, CARD_PH,
        "SENSOR pH (PH-4502C)", "Front-End Pseudo-Diferencial", "Sonda BNC", C_PH_DIFF,
        lines=[
            ("• Electrodo Combinado:", "Vidrio de ultra-alta impedancia (>10¹² Ω) con BNC", C_PH_DIFF),
            ("• Buffer Analógico LM358:", "Seguidor de tensión de baja corriente de polarización", C_PH_DIFF),
            ("• Potenciómetro Offset:", "Ajuste multivuelta de cero en corto (1.765 V @ pH 7.00)", C_TEXT_WHITE),
            ("• TOPOLOGÍA PSEUDO-DIFERENCIAL:", "Separación galvánica de señal y masa de referencia", C_PH_DIFF),
            ("  1. Señal Po (Salida):", "-> Entrada No-Inversora ADS1115 Canal A1 vía Filtro RC", C_PH_DIFF),
            ("  2. AGND Limpia (Ref):", "-> Entrada Inversora ADS1115 Canal A0 (Sin bucles)", C_PH_DIFF),
            ("• Alimentación +5V DC:", "Línea regulada y filtrada independiente desde LM7805", C_POWER),
            ("• Calibración Tri-Modo NVS:", "Nernst / 2-Puntos / 3-Puntos Asimétrico en Flash ESP32", C_TEXT_MUTED),
        ])

    # 6. SUMIDERO DE CORRIENTE VCSS
    draw_module_card(draw, CARD_VCSS,
        "SUMIDERO VCSS", "Lazo Analógico Cerrado (0 - 7.06 A)", "0 - 7.06 A", C_VCSS,
        lines=[
            ("• Op-Amp LM358N:", "Retroalimentación negativa analógica de respuesta rápida", C_VCSS),
            ("• 2x MOSFET IRLZ44N:", "Transistores N-Channel Nivel Lógico 5V (TO-220 en paralelo)", C_VCSS),
            ("• 2x Shunts Cerámicos:", "Resistencias 1.0 Ω / 10W Cemento Blanco (Wirewound SQP)", C_ZCS),
            ("• Reparto Balanceado:", "Rama 1 (0-3.53 A) + Rama 2 (0-3.53 A) en paralelo", C_TEXT_WHITE),
            ("• Headers Sensado SH1/SH2:", "Caída de tensión 1.0 V/A hacia Canales A2 y A3 de ADS1115", C_I2C),
            ("• Entrada VREF:", "Consigna 0-3.53V desde DAC MCP4725 (Clema 2)", C_TEXT_MUTED),
            ("• Conexión Cátodo Celda:", "Terminal OUT- hacia probeta de trabajo (Aluminio 6061)", C_HULL),
        ])

    # 7. CELDA HULL
    draw_module_card(draw, CARD_HULL,
        "CELDA HULL (267 mL)", "Reactor Químico Electroquímico", "Zn-Ni / Hull", C_HULL,
        lines=[
            ("• Tina Química 3:", "Zincado ácido (ZnSO4) a 25 - 40 °C (Protocolo VUGR)", C_HULL),
            ("• Cátodo Oblicuo Al 6061:", "Conectado a OUT- del Sumidero VCSS (Drains MOSFET)", C_VCSS),
            ("• Ánodo Zn Puro (+):", "Conectado a línea +12V VDD protegida por Relé ZCS", C_ZCS),
            ("• Culombimetría Faradaica:", "Integración en Core 1: Q = ∫ I dt (Rendimiento Catódico)", C_TEXT_WHITE),
            ("• Gradiente de Corriente:", "Densidad no uniforme continua 0.1 a 5.0 A/dm²", C_TEXT_MUTED),
            ("• Diagnóstico de Celda:", "SaludCelda_t (V_celda, circuito abierto y cortocircuito)", C_TEXT_MUTED),
        ])

    # 8. MÓDULO RELÉ ZCS DC (+12V VDD)
    draw_module_card(draw, CARD_RELE_ZCS,
        "MÓDULO RELÉ ZCS (DC)", "Aislamiento Galvánico +12V VDD (Corte Cero)", "GPIO 20", C_ZCS,
        lines=[
            ("• Disparo Optoacoplado:", "Módulo Relevador 5V (Active-LOW, Optoacoplador PC817)", C_ZCS),
            ("• Contactos de Potencia:", "2x Relés Songle 10A / 30VDC en paralelo redundante", C_ZCS),
            ("• Protocolo ZCS DC:", "Conmutación mecánica estrictamente a corriente I = 0.00 A", C_TEXT_WHITE),
            ("• Secuencia Encendido:", "1. DAC=0V -> 2. Relé ON -> 3. Espera 80ms -> 4. Soft-Start", C_TEXT_MUTED),
            ("• Secuencia Apagado:", "1. DAC=0V -> 2. Espera 30ms -> 3. Relé OFF (Sin Chispa/Arco)", C_TEXT_MUTED),
            ("• Aislamiento Total:", "Línea +12V físicamente abierta ante alarmas o reposo", C_TRIAC),
            ("• Vida Mecánica:", ">100,000 ciclos garantizados al eliminar arco voltaico", C_TEXT_MUTED),
        ])

    # 9. ESP32-S3 MAESTRO (NODO CENTRAL)
    draw_module_card(draw, CARD_ESP,
        "ESP32-S3 N16R8 (NODO MAESTRO)", "Procesador Central Dual-Core Xtensa LX7 @ 240 MHz", "MASTER CORE", C_ESP32,
        lines=[
            ("• Arquitectura SMP Dual-Core:", "240 MHz con FPU 32-bit (FreeRTOS SMP / Super-Loop v4.0)", C_ESP32),
            ("• Memoria del Sistema:", "16 MB Quad/Octal SPI Flash + 8 MB Octal PSRAM OPI", C_TEXT_MUTED),
            ("• Core 0 (Comunicaciones):", "Servidor Web HTTP, Wi-Fi SoftAP 'Uli', WebSockets, Telemetría /data_all", C_ESP32),
            ("• Core 1 (Control Tiempo Real):", "Lazo PI Térmico (1 Hz), PI VCSS Discreto (2 Hz), Filtro Adaptativo pH EWMA", C_ESP32),
            ("• Asignación de Pines:", "I2C(8,9), SPI(18,19), UART2(17), ZCS Relé(20), Baliza Neopixel WS2812(48)", C_TEXT_WHITE),
            ("• Interlocks de Seguridad:", "Exclusión Mutua Química, Alarma Fail-Safe Latch (Norma ISA-18.2)", C_TRIAC),
            ("• Persistencia Flash NVS:", "Calibración pH por Modo, Balances Culombimétricos Faradaicos", C_PH_DIFF),
            ("• Algoritmo Soft-Start VCSS:", "Rampa lineal 500 ms + Blanking Time 300 ms (Inmunidad Anti-Inrush)", C_ZCS),
        ])

    # 10. BUS SPI (4x MAX6675)
    draw_module_card(draw, CARD_SPI,
        "TERMOCOPLAS SPI", "4x Módulos MAX6675 + Sondas Tipo K", "SPI 4 MHz", C_SPI,
        lines=[
            ("• Bus SPI Half-Duplex:", "Reloj Compartido SCK=GPIO18, Retorno MISO=GPIO19 (Sin MOSI)", C_SPI),
            ("• Resolución y Precisión:", "Conversores 12-bit (0.25 °C) con compensación de junta fría", C_TEXT_MUTED),
            ("• Tina 1 (Desengrase Alcalino):", "CS: GPIO 5  | Control PI: 80 - 95 °C (Na3PO4 + Na2SiO4)", C_SPI),
            ("• Tina 2 (Decapado Alcalino):", "CS: GPIO 4  | Control PI: 80 - 95 °C (Remoción Al2O3)", C_SPI),
            ("• Tina 3 (Celda Hull Zincado):", "CS: GPIO 13 | Control PI: 25 - 40 °C (ZnSO4 Ácido)", C_SPI),
            ("• Tina 4 (Niquelado sobre Zinc):", "CS: GPIO 14 | Control PI: 20 - 40 °C (NiSO4 + Na2SO4)", C_SPI),
            ("• Detección Termopar Roto:", "Bit D2 en trama SPI genera paro de seguridad instantáneo", C_TRIAC),
            ("• Inmunidad Industrial:", "Sondas tipo bayoneta con malla trenzada de acero inox", C_TEXT_MUTED),
        ])

    # 11. ARDUINO NANO (ESCLAVO AC)
    draw_module_card(draw, CARD_NANO,
        "ARDUINO NANO (ESCLAVO AC)", "Controlador de Disparo TRIACs 60 Hz", "ATmega328P", C_NANO,
        lines=[
            ("• Microcontrolador Dedicado:", "ATmega328P @ 16 MHz (Lógica 5V TTL desacoplada)", C_NANO),
            ("• Enlace Serie UART2:", "Pin RX 0 <- ESP32 TX GPIO17 (Trama CSV 'pot0,pot1,pot2,pot3\\n')", C_UART),
            ("• Watchdog de Seguridad:", "3.0 s sin recibir trama UART -> Apaga los 4 TRIACs al 0% (Fail-Safe)", C_TRIAC),
            ("• Interrupción Externa INT1:", "Pin D3 sincronizado con pulso de Cruce por Cero (ZCS AC 60Hz)", C_ZCS),
            ("• Rutina ISR alCruzarPorCero:", "Tiempo de ejecución ultrarrápido ~8 µs (Captura tCruceCero micros())", C_ZCS),
            ("• Modulación Ángulo de Fase:", "Tabla LUT retardos_us calibrada para 60 Hz (Pulsos Gate 80 µs)", C_TEXT_WHITE),
            ("• 4x Salidas de Disparo:", "Pines D4, D5, D6, D7 -> Entradas Opto-TRIACs Canales 1, 2, 3 y 4", C_TRIAC),
        ])

    # 12. DETECTOR CRUCE POR CERO ZCS AC (OPTO 4N35)
    draw_module_card(draw, CARD_ZCS_AC,
        "DETECTOR ZCS AC", "Detector Cruce por Cero 60 Hz", "Opto 4N35", C_ZCS,
        lines=[
            ("• Entrada de Línea AC:", "Red Eléctrica 110V / 220V AC @ 60 Hz (Periodo 16.66 ms)", C_TRIAC),
            ("• Aislamiento Galvánico:", "Optoacoplador 4N35 / PC817 (Barrera 5000 Vrms)", C_ZCS),
            ("• Sincronismo Semiciclo:", "Detecta transición de 0V cada 8.33 ms (120 cruces/s)", C_ZCS),
            ("• Salida de Disparo:", "Flanco de subida RISING -> Pin D3 (INT1) Arduino Nano", C_TEXT_WHITE),
            ("• Referencia Temporal:", "Base de tiempo estricta para modulación de ángulo", C_TEXT_MUTED),
            ("• Red de Protección:", "Resistencias de potencia y diodos zener de protección", C_TEXT_MUTED),
        ])

    # 13. MÓDULOS TRIACS AC
    draw_module_card(draw, CARD_TRIAC,
        "ETAPA TRIACS AC", "4 Canales de Potencia", "BTA24 / MOC", C_TRIAC,
        lines=[
            ("• 4x Opto-TRIACs MOC3021:", "Disparo no-cero (Fase)", C_TRIAC),
            ("• 4x TRIACs BTA24-600B:", "Capacidad 25 A / 600 V", C_TRIAC),
            ("• Tina 1, 2 y 4 (Inmersión):", "3x Calentadores 450W AC", C_TEXT_WHITE),
            ("• Tina 3 (Celda Hull):", "1x Calentador cartucho 18W", C_TEXT_WHITE),
            ("• Redes Snubber RC:", "Protección transitorios dV/dt", C_TEXT_MUTED),
            ("• Conexión Red AC:", "Línea Potencia AC 120V 60Hz", C_TRIAC),
        ])

    # =========================================================================
    # CABLEADO Y CONEXIONES CON ENRUTAMIENTO ORTOGONAL LIMPIO
    # =========================================================================

    # 1. TRONCAL BUS I2C (ESP32-S3 -> ADS1115, MCP4725, AHT20/BMP280)
    draw_wire(draw, [(1285, 565), (1285, 525), (555, 525), (555, 485)], C_I2C, width=4) # Hacia DAC MCP4725
    draw_wire(draw, [(1285, 525), (1285, 485)], C_I2C, width=4)                             # Hacia ADS1115
    draw_wire(draw, [(905, 525), (905, 485)], C_I2C, width=3)                              # Hacia AHT20+BMP280
    draw_pill(draw, 1060, 525, "BUS I2C FAST-MODE (400 kHz) [SDA=GPIO8, SCL=GPIO9]", C_I2C)

    # 2. DAC MCP4725 -> VCSS (Consigna Vref)
    draw_wire(draw, [(555, 485), (555, 515), (365, 515), (365, 545)], C_VCSS, width=4)
    draw_pill(draw, 365, 515, "Consigna VREF (0.00 V - 3.53 V)", C_VCSS)

    # 3. VCSS SHUNTS -> ADS1115 (Canales A2 y A3)
    draw_wire(draw, [(685, 730), (700, 730), (700, 505), (1150, 505), (1150, 485)], C_VCSS, width=3, is_dashed=True)
    draw_pill(draw, 925, 505, "Shunts SH1 & SH2 -> ADS1115 Canales A2 y A3 (1.0 V/A)", C_VCSS)

    # 4. CONEXIÓN PSEUDO-DIFERENCIAL DE pH (PH-4502C -> ADS1115)
    # En el espacio libre entre ADS1115 (x=1785) y PH-4502C (x=1985), ancho = 200px
    draw_wire(draw, [(1985, 260), (1785, 260)], C_PH_DIFF, width=4)
    draw_pill(draw, 1885, 240, "Po (Señal pH) -> A1 (In+)", C_PH_DIFF)

    draw_wire(draw, [(1985, 330), (1785, 330)], (52, 211, 153), width=4, is_dashed=True)
    draw_pill(draw, 1885, 350, "AGND Limpia -> A0 (Ref-)", (52, 211, 153))

    # Badge central de la fórmula Pseudo-Diferencial
    f_box = (1805, 380, 1965, 455)
    draw.rounded_rectangle(f_box, radius=8, fill=(6, 78, 59), outline=C_PH_DIFF, width=2)
    draw.text((1814, 388), "PSEUDO-DIFERENCIAL", fill=C_TEXT_WHITE, font=FONT_FORMULA_SM)
    draw.text((1810, 408), "V=V(A1)-V(A0)", fill=(110, 231, 183), font=FONT_FORMULA)
    draw.text((1818, 432), "Alto CMRR (EMI)", fill=(167, 243, 208), font=FONT_FORMULA_SM)

    # 5. VCSS -> CELDA HULL (Cátodo -)
    draw_wire(draw, [(365, 915), (365, 955)], C_HULL, width=5)
    draw_pill(draw, 365, 935, "OUT- Cátodo (-) 0 - 7.06 A", C_HULL)

    # 6. RELÉ ZCS DC -> CELDA HULL (Ánodo +)
    draw_wire(draw, [(365, 1315), (365, 1275)], C_ZCS, width=5)
    draw_pill(draw, 365, 1295, "OUT+ Ánodo (+) +12V VDD (Protegida ZCS)", C_ZCS)

    # 7. ESP32-S3 -> RELÉ ZCS DC (Control GPIO 20)
    draw_wire(draw, [(715, 875), (695, 875), (695, 1510), (685, 1510)], C_ZCS, width=4)
    draw_pill(draw, 695, 1190, "ZCS GPIO 20 (Active-LOW)", C_ZCS)

    # 8. SMPS 12V -> VCSS & RELÉ ZCS & PRE-REGULADOR
    draw_wire(draw, [(200, 485), (200, 545)], C_POWER, width=4)
    draw_wire(draw, [(45, 325), (25, 325), (25, 1510), (45, 1510)], C_POWER, width=3, is_dashed=True)
    draw_pill(draw, 200, 515, "+12V VDD Potencia", C_POWER)

    # 9. BUS SPI (ESP32-S3 -> 4x MAX6675)
    draw_wire(draw, [(1865, 860), (1895, 860)], C_SPI, width=4)
    draw_pill(draw, 1880, 835, "BUS SPI READ-ONLY [SCK=18, MISO=19, CS=5,4,13,14]", C_SPI)

    # 10. BUS UART2 (ESP32-S3 TX -> Arduino Nano RX)
    draw_wire(draw, [(1175, 1175), (1175, 1245)], C_UART, width=4)
    draw_pill(draw, 1175, 1210, "ENLACE SERIE UART2 (9600 Baud) [ESP32 TX GPIO17 -> Nano RX Pin D0]", C_UART)

    # 11. DETECTOR CRUCE POR CERO ZCS AC (4N35) -> ARDUINO NANO INT1
    draw_wire(draw, [(1665, 1475), (1635, 1475)], C_ZCS, width=4)
    draw_pill(draw, 1650, 1445, "INT1 (Pin D3) Cruce Cero 60Hz", C_ZCS)

    # 12. ARDUINO NANO -> MÓDULOS TRIACS (Pines D4-D7)
    draw_wire(draw, [(1635, 1585), (2195, 1585)], C_TRIAC, width=4)
    draw_pill(draw, 1915, 1585, "4x Pulsos Disparo de Gate (D4, D5, D6, D7) [80 µs]", C_TRIAC)

    # 13. RED AC 120V -> DETECTOR ZCS Y TRIACS
    draw_wire(draw, [(1915, 1705), (1915, 1730), (2425, 1730), (2425, 1705)], C_TRIAC, width=3, is_dashed=True)
    draw_pill(draw, 2170, 1730, "LÍNEA DE POTENCIA RED AC 120V @ 60 Hz", C_TRIAC)

    # =========================================================================
    # PANEL INFERIOR DE LEYENDA TÉCNICA (FOOTER)
    # =========================================================================
    footer_y1 = H - 65
    draw.rectangle([(0, footer_y1), (W, H)], fill=(7, 12, 22))
    draw.line([(0, footer_y1), (W, footer_y1)], fill=(30, 41, 59), width=2)

    legends = [
        ("BUS I2C (400 kHz)", C_I2C),
        ("BUS SPI (4 MHz)", C_SPI),
        ("BUS UART2 (9600)", C_UART),
        ("SENSADO PSEUDO-DIFERENCIAL (A1-A0)", C_PH_DIFF),
        ("ZCS AC CRUCE CERO (4N35)", C_ZCS),
        ("ZCS DC CORTE GALVÁNICO (+12V)", (202, 138, 4)),
        ("SUMIDERO VCSS ANALÓGICO", C_VCSS),
        ("POTENCIA AC 120V / TRIACS", C_TRIAC),
        ("ALIMENTACIÓN HÍBRIDA DC", C_POWER),
    ]

    lx = 45
    ly = footer_y1 + 20
    for l_text, l_color in legends:
        draw.ellipse([(lx, ly + 3), (lx + 13, ly + 16)], fill=l_color)
        draw.text((lx + 19, ly), l_text, fill=C_TEXT_WHITE, font=FONT_LEGEND)
        tb = FONT_LEGEND.getbbox(l_text)
        lx += (tb[2] - tb[0]) + 45

    # =========================================================================
    # GUARDADO MULTI-DESTINO Y ACTUALIZACIÓN DEL PROYECTO
    # =========================================================================
    destinations = [
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema.png",
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema_moderno.png",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema.png",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema_moderno.png",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema.png",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema_moderno.png",
    ]

    for d in destinations:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        img.save(d, quality=95)
        print(f"[GUARDADO EXITOSO] -> {d}")

if __name__ == "__main__":
    render_diagram()

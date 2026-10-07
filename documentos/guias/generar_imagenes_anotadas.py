#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Infografías Técnicas de Planta Física — Reactor Químico y Celda Hull
Renderizado en 2 Fases (Alpha Composite + Draw Nítido) con fidelidad 100% de pines y hardware.

Imágenes producidas:
1. 01_Placa_Principal_Rotulada.jpg              — Mapa maestro de sockets, pines y arquitectura híbrida
2. 02_Placa_Conectada_Rotulada.jpg              — Gabinete en operación viva (SMPS 12V, Buck 6.80V, buses) [Rotada 180°]
3. 03_Etapa_VCSS_Rotulada.jpg                   — Sumidero de corriente analógico (IRLZ44N, LM358N, shunts) [Rotada 180°]
4. 04_Modulo_TRIACS_Rotulado.jpg                — 4 Canales AC 120V + Detector ZCS (Header VCC GND ZC CH1-CH4)
5. 05_Detalle_Bus_ADC_I2C.jpg                   — Macro de ADS1115 (A0-A3 + RC), MCP4725 y AHT20/BMP280
6. 06_Detalle_Buses_Termopares.jpg              — Macro de 4x sockets MAX6675 (SO, CS, CLK, VCC, GND)
7. 08_Alineacion_Pines_Sensores_Actuadores.jpg — Infografía Maestra de correspondencia 1:1 de pines y cabezales
8. 09_Gabinete_Operacion_Completo.jpg           — Vista panorámica del gabinete industrial en operación viva
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"documentos/imagenes/Planta Fisica"
OUTPUT_DIR = r"documentos/imagenes/Planta Fisica/anotadas"
MANUAL_OUTPUT_DIR = r"documentos/manuales/imagenes/Planta Fisica/anotadas"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MANUAL_OUTPUT_DIR, exist_ok=True)

# Tipografías TrueType de alta legibilidad
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
FONT_SUB = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
FONT_BADGE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
FONT_TAG = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
FONT_MONO = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 23)
FONT_BANNER_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 46)
FONT_BANNER_SUB = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 27)


def resolve_src_path(filename):
    """Busca el archivo de imagen en BASE_DIR o en directorios raíz de imágenes."""
    candidates = [
        os.path.join(BASE_DIR, filename),
        os.path.join("documentos/imagenes", filename),
        os.path.join("documentos/imagenes/Planta Fisica", filename)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"No se encontró el archivo de imagen: {filename}")


def draw_header_banner(draw, w, title, subtitle, badge_text, badge_color):
    """Renderiza banner superior HUD/Industrial con alto contraste."""
    banner_height = 140
    draw.rectangle([(0, 0), (w, banner_height)], fill=(10, 15, 29))
    draw.line([(0, banner_height), (w, banner_height)], fill=(2, 132, 199), width=5)
    
    # Badge
    bbox_b = FONT_BADGE.getbbox(badge_text)
    bw = bbox_b[2] - bbox_b[0] + 32
    bh = 40
    bx = 35
    by = 20
    draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=8, fill=badge_color)
    draw.text((bx + 16, by + 6), badge_text, fill=(255, 255, 255), font=FONT_BADGE)
    
    # Título principal
    draw.text((bx + bw + 25, 18), title, fill=(248, 250, 252), font=FONT_BANNER_TITLE)
    
    # Subtítulo explicativo
    draw.text((35, 80), subtitle, fill=(148, 163, 184), font=FONT_BANNER_SUB)


class Callout:
    def __init__(self, bbox, title, lines, theme_color, card_xy, pointer=None, extra_bboxes=None, bbox_labels=None):
        self.bbox = bbox           # (x1, y1, x2, y2)
        self.title = title         # Título del componente
        self.lines = lines         # Lista de líneas de texto
        self.theme_color = theme_color  # (R, G, B)
        self.card_xy = card_xy     # (cx1, cy1)
        self.pointer = pointer     # (px, py)
        self.extra_bboxes = extra_bboxes or []
        self.bbox_labels = bbox_labels or []  # List of string labels for each bbox


def render_annotated_image(src_filename, out_filename, banner_data, callouts, rotate_deg=0):
    """
    Renderiza la imagen en 2 fases rigurosas:
    1. Alpha Composite: Bounding boxes translúcidos y fondos de tarjetas oscuras.
    2. Draw Nítido: Retículas HUD en esquinas, micro-etiquetas de pines, líneas de guía y tarjetas de especificación.
    """
    src_path = resolve_src_path(src_filename)
    orig = Image.open(src_path)
    if rotate_deg != 0:
        orig = orig.rotate(rotate_deg, expand=True)
        
    w, h = orig.size
    img = orig.convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # FASE 1: Bounding boxes y fondos de tarjetas oscuras
    card_boxes = []
    for c in callouts:
        cx1, cy1 = c.card_xy
        r, g, b = c.theme_color
        all_boxes = [c.bbox] + c.extra_bboxes
        
        # 1. Bounding boxes translúcidos con radio ajustado
        for b_box in all_boxes:
            bx1, by1, bx2, by2 = b_box
            draw_overlay.rounded_rectangle(
                [(bx1, by1), (bx2, by2)],
                radius=10,
                fill=(r, g, b, 45),
                outline=(r, g, b, 230),
                width=3
            )
        
        # Medir ancho y alto de tarjeta
        tb = FONT_TITLE.getbbox(c.title)
        max_w = tb[2] - tb[0]
        line_heights = []
        for line in c.lines:
            lb = FONT_SUB.getbbox(line)
            lw = lb[2] - lb[0]
            if lw > max_w:
                max_w = lw
            line_heights.append(lb[3] - lb[1])
            
        card_w = max_w + 44
        total_text_h = (tb[3] - tb[1]) + sum(line_heights) + (len(c.lines) * 8) + 36
        card_h = total_text_h
        
        # Clamping dentro del canvas
        if cx1 + card_w > w - 20:
            cx1 = max(20, w - card_w - 20)
        if cy1 + card_h > h - 20:
            cy1 = max(150, h - card_h - 20)
            
        cx2 = cx1 + card_w
        cy2 = cy1 + card_h
        
        # Fondo de tarjeta oscuro (95% opaco)
        draw_overlay.rounded_rectangle(
            [(cx1, cy1), (cx2, cy2)],
            radius=10,
            fill=(11, 17, 32, 242)
        )
        card_boxes.append((cx1, cy1, cx2, cy2, card_w, card_h))
        
    # FASE 2: Composición final nítida
    img = Image.alpha_composite(img, overlay)
    draw_final = ImageDraw.Draw(img)
    
    # Banner
    draw_header_banner(
        draw_final, w,
        banner_data["title"],
        banner_data["subtitle"],
        banner_data["badge_text"],
        banner_data["badge_color"]
    )
    
    # Dibujar elementos nítidos
    for i, c in enumerate(callouts):
        cx1, cy1, cx2, cy2, cw, ch = card_boxes[i]
        r, g, b = c.theme_color
        all_boxes = [c.bbox] + c.extra_bboxes
        
        # Retículas HUD en esquinas y micro-etiquetas para cada caja
        labels = c.bbox_labels if isinstance(c.bbox_labels, list) else [c.bbox_labels]
        for b_idx, b_box in enumerate(all_boxes):
            bx1, by1, bx2, by2 = b_box
            arm = min(18, (bx2 - bx1) // 4, (by2 - by1) // 4)
            # HUD L-brackets en las 4 esquinas
            # Top-Left
            draw_final.line([(bx1 - 3, by1 - 3), (bx1 + arm, by1 - 3)], fill=(255, 255, 255), width=3)
            draw_final.line([(bx1 - 3, by1 - 3), (bx1 - 3, by1 + arm)], fill=(255, 255, 255), width=3)
            # Top-Right
            draw_final.line([(bx2 + 3, by1 - 3), (bx2 - arm, by1 - 3)], fill=(255, 255, 255), width=3)
            draw_final.line([(bx2 + 3, by1 - 3), (bx2 + 3, by1 + arm)], fill=(255, 255, 255), width=3)
            # Bottom-Left
            draw_final.line([(bx1 - 3, by2 + 3), (bx1 + arm, by2 + 3)], fill=(255, 255, 255), width=3)
            draw_final.line([(bx1 - 3, by2 + 3), (bx1 - 3, by2 - arm)], fill=(255, 255, 255), width=3)
            # Bottom-Right
            draw_final.line([(bx2 + 3, by2 + 3), (bx2 - arm, by2 + 3)], fill=(255, 255, 255), width=3)
            draw_final.line([(bx2 + 3, by2 + 3), (bx2 + 3, by2 - arm)], fill=(255, 255, 255), width=3)
            
            # Micro-etiqueta tipo pill si está definida
            if b_idx < len(labels) and labels[b_idx]:
                lbl = labels[b_idx]
                t_bbox = FONT_TAG.getbbox(lbl)
                tw, th = t_bbox[2] - t_bbox[0], t_bbox[3] - t_bbox[1]
                tag_x = bx1 + 10
                tag_y = by1 - th - 10
                if tag_y < 145:
                    tag_y = by1 + 8
                draw_final.rounded_rectangle(
                    [(tag_x, tag_y), (tag_x + tw + 16, tag_y + th + 6)],
                    radius=5,
                    fill=(11, 17, 32),
                    outline=(r, g, b),
                    width=2
                )
                draw_final.text((tag_x + 8, tag_y + 1), lbl, fill=(255, 255, 255), font=FONT_TAG)
        
        # Punto de guía principal
        primary_x1, primary_y1, primary_x2, primary_y2 = c.bbox
        target_pt = c.pointer if c.pointer else ((primary_x1 + primary_x2) // 2, (primary_y1 + primary_y2) // 2)
        
        # Punto de anclaje más natural hacia la tarjeta
        card_anchor_x = cx1 if target_pt[0] < cx1 else (cx2 if target_pt[0] > cx2 else (cx1 + cx2) // 2)
        card_anchor_y = cy1 if target_pt[1] < cy1 else (cy2 if target_pt[1] > cy2 else (cy1 + cy2) // 2)
        
        # Línea de guía con punto diana
        draw_final.line([target_pt, (card_anchor_x, card_anchor_y)], fill=(r, g, b), width=3)
        draw_final.ellipse([(target_pt[0]-8, target_pt[1]-8), (target_pt[0]+8, target_pt[1]+8)], fill=(255, 255, 255), outline=(r, g, b), width=3)
        draw_final.ellipse([(target_pt[0]-3, target_pt[1]-3), (target_pt[0]+3, target_pt[1]+3)], fill=(r, g, b))
        
        # Borde y barra de acento superior de la tarjeta
        draw_final.rounded_rectangle([(cx1, cy1), (cx2, cy2)], radius=10, outline=(r, g, b), width=3)
        draw_final.rounded_rectangle([(cx1, cy1), (cx2, cy1 + 7)], radius=4, fill=(r, g, b))
        
        # Título en blanco brillante
        draw_final.text((cx1 + 20, cy1 + 16), c.title, fill=(255, 255, 255), font=FONT_TITLE)
        
        # Líneas descriptivas
        curr_y = cy1 + 60
        for line in c.lines:
            draw_final.text((cx1 + 20, curr_y), line, fill=(226, 232, 240), font=FONT_SUB)
            lb = FONT_SUB.getbbox(line)
            curr_y += (lb[3] - lb[1]) + 8

    # Guardar en ambas carpetas
    out_rgb = img.convert("RGB")
    p1 = os.path.join(OUTPUT_DIR, out_filename)
    p2 = os.path.join(MANUAL_OUTPUT_DIR, out_filename)
    out_rgb.save(p1, quality=95)
    out_rgb.save(p2, quality=95)
    print(f"Generada exitosamente: {out_filename}")


# ==============================================================================
# 1. IMAGEN 1: PLACA PRINCIPAL ROTULADA (ARQUITECTURA COMPLETA)
# ==============================================================================
def generar_01_placa_principal():
    callouts = [
        Callout(
            bbox=(450, 420, 1500, 1200),
            title="Etapa de Alimentación y Pre-Regulación",
            lines=[
                "• Zócalo LM2596 Buck: 12V -> 6.80V frío hacia reguladores lineales",
                "• L7805 (TO-220): Barra lógica +5V (Nano, Relés, ZCS, Pantallas)",
                "• LM317T / LM1117: Barra +3.3V (ESP32-S3, MAX6675, I2C pull-ups)",
                "• Bornera Power In: VCC 12V / GND desde fuente SMPS 10A"
            ],
            theme_color=(245, 158, 11),  # Ámbar
            card_xy=(80, 160),
            pointer=(980, 800),
            bbox_labels=["Buck 6.8V & Regs 5V/3.3V"]
        ),
        Callout(
            bbox=(1650, 520, 1960, 1200),
            title="Arduino Nano (Esclavo de Fase AC)",
            lines=[
                "• Pin D3 (INT1): Entrada señal detector Cruce por Cero (ZCS)",
                "• Pines D7 a D10: Disparo pulsos TTL a optotriacs Canales 0-3",
                "• Pin D0 (RX): Recepción comandos seriales desde ESP32 (9600 bps)",
                "• Base de tiempo Timer1: Resolución de 1 µs para ángulo α"
            ],
            theme_color=(16, 185, 129),  # Verde
            card_xy=(1380, 160),
            pointer=(1800, 680),
            bbox_labels=["Arduino Nano Esclavo"]
        ),
        Callout(
            bbox=(2180, 480, 2640, 1440),
            title="ESP32-S3 N16R8 (Controlador Maestro)",
            lines=[
                "• Core 0: Web Server Async SoftAP 'Uli' (192.168.4.1) + WebSockets",
                "• Core 1: Lazo de control térmico PI, telemetría y safety checks",
                "• GPIO 17 (TX): Transmisión UART hacia Arduino Nano D0 (RX)",
                "• GPIO 18 (SCK) / 19 (SO): Bus SPI compartido MAX6675",
                "• GPIO 5, 4, 13, 14: Pines Chip Select (CS0-CS3) para termopares"
            ],
            theme_color=(14, 165, 233),  # Cyan
            card_xy=(2440, 160),
            pointer=(2410, 680),
            bbox_labels=["ESP32-S3 Maestro"]
        ),
        Callout(
            bbox=(480, 1480, 750, 1620),
            title="Header Bus TRIAC (7 Pines)",
            lines=[
                "• Orden físico 1:1: [VCC | GND | ZC | CH1 | CH2 | CH3 | CH4]",
                "• ZC -> Pin D3 (INT1) | CH1 -> D7 | CH2 -> D8 | CH3 -> D9 | CH4 -> D10"
            ],
            theme_color=(239, 68, 68),  # Rojo
            card_xy=(80, 1620),
            pointer=(600, 1550),
            bbox_labels=["Bus TRIAC 7P"]
        ),
        Callout(
            bbox=(1960, 520, 2180, 680),
            title="Socket Power Relé & ZCS",
            lines=[
                "• Pines: [5V Lógica | 5V Relé (JD-VCC) | 5GND]",
                "• Alimentación aislada para bobinas de relé de inversión de celda"
            ],
            theme_color=(249, 115, 22),  # Naranja
            card_xy=(1750, 450),
            pointer=(2070, 600),
            bbox_labels=["Power Relé & ZCS"]
        ),
        Callout(
            bbox=(1100, 1680, 1420, 1840),
            title="Sockets SPI para 4x Módulos MAX6675",
            lines=[
                "• Orden físico 1:1 con módulo: [SO | CS | CLK | VCC | GND]",
                "• Desacoplo: Capacitor cerámico 100 nF en cada socket entre VCC y GND",
                "• Sensores: Tina Desengrase, Decapado, Celda Hull y Niquelado"
            ],
            theme_color=(20, 184, 166),  # Turquesa
            card_xy=(950, 1480),
            pointer=(1850, 1730),
            extra_bboxes=[(1470, 1680, 1790, 1840), (1840, 1680, 2160, 1840), (2210, 1680, 2530, 1840)],
            bbox_labels=["TC0 Desengrase", "TC1 Decapado", "TC2 Celda Hull", "TC3 Niquelado"]
        ),
        Callout(
            bbox=(2920, 1180, 3200, 1420),
            title="MCP4725 DAC 12-bit (I2C @ 0x60)",
            lines=[
                "• Pinout: [OUT | GND | SCL | SDA | VCC | GND]",
                "• OUT: Consigna analógica VREF (0.00 a 3.53 V) hacia etapa VCSS",
                "• Resolución: 0.86 mV/LSB -> Lazo analógico de corriente"
            ],
            theme_color=(239, 68, 68),  # Rojo
            card_xy=(3380, 500),
            pointer=(3060, 1280),
            bbox_labels=["MCP4725 DAC"]
        ),
        Callout(
            bbox=(2620, 1430, 3120, 1780),
            title="ADS1115 ADC 16-bit (I2C @ 0x48)",
            lines=[
                "• Pinout: [VDD | GND | SCL | SDA | ADDR | ALRT | A0 | A1 | A2 | A3]",
                "• Canal A1: Sonda de pH (PH-4502C, 0.00 - 14.00 pH)",
                "• Canales A2 y A3: Sensado Shunts 1 y 2 VCSS (ETS 16 pts)",
                "• Filtros pasabajos RC individuales soldados bajo el zócalo"
            ],
            theme_color=(59, 130, 246),  # Azul
            card_xy=(3380, 950),
            pointer=(2870, 1550),
            bbox_labels=["ADS1115 ADC"]
        ),
        Callout(
            bbox=(3190, 1440, 3450, 1720),
            title="AHT20 + BMP280 (I2C)",
            lines=[
                "• Pinout: [VDD | SDA | GND | SCL]",
                "• AHT20 (0x38): Temp y Humedad en cabina",
                "• BMP280 (0x76): Presión barométrica"
            ],
            theme_color=(168, 85, 247),  # Morado
            card_xy=(3480, 1440),
            pointer=(3320, 1550),
            bbox_labels=["AHT20/BMP280"]
        )
    ]
    render_annotated_image(
        src_filename="Placa Principal ESP32 + NANO + I2C.jpg",
        out_filename="01_Placa_Principal_Rotulada.jpg",
        banner_data={
            "title": "MAPA DE COMPONENTES E INTERFACES EN ZÓCALOS — PLACA MADRE",
            "subtitle": "Arquitectura Híbrida: ESP32-S3 Maestro (RTOS 2.0) + Arduino Nano Esclavo AC (120 Hz) + Instrumentación I2C/SPI",
            "badge_text": "PLACA MAESTRA",
            "badge_color": (2, 132, 199)
        },
        callouts=callouts
    )


# ==============================================================================
# 2. IMAGEN 2: PLACA PRINCIPAL CONECTADA (INTEGRACIÓN EN GABINETE - ROTADA 180°)
# ==============================================================================
def generar_02_placa_conectada():
    # Coordenadas calibradas con precisión sobre la imagen rotada 180°
    callouts = [
        Callout(
            bbox=(20, 200, 780, 1800),
            title="Fuente Conmutada Industrial (SMPS 12V / 10A)",
            lines=[
                "• Alimentación primaria 120W DC para todo el sistema",
                "• Entrada 120 VAC con fusible de seguridad 2A",
                "• Salida +12V distribuida a Celda, Buck, Ventiladores y VCSS"
            ],
            theme_color=(220, 38, 38),  # Rojo
            card_xy=(80, 200),
            pointer=(400, 800),
            bbox_labels=["SMPS 12V 10A"]
        ),
        Callout(
            bbox=(1240, 280, 2180, 880),
            title="Pre-Regulador DC-DC Buck LM2596 (Display 6.80V)",
            lines=[
                "• Reduce 12V de SMPS a 6.80V fríos y estables",
                "• Alimenta reguladores lineales LM7805 y LM1117 de la placa",
                "• Previene sobrecalentamiento térmico en gabinete cerrado"
            ],
            theme_color=(245, 158, 11),  # Ámbar
            card_xy=(1050, 180),
            pointer=(1700, 480),
            bbox_labels=["Buck LM2596 (6.80V)"]
        ),
        Callout(
            bbox=(2320, 240, 2800, 1180),
            title="ESP32-S3 Maestro Operativo en Chasis",
            lines=[
                "• Servidor Web SoftAP 'Uli' activo (192.168.4.1)",
                "• Concentrador de telemetría y lazos PI en tiempo real",
                "• Comunicación UART continua a 9600 bps con esclavo Nano"
            ],
            theme_color=(14, 165, 233),  # Cyan
            card_xy=(2100, 180),
            pointer=(2560, 650),
            bbox_labels=["ESP32-S3 Maestro"]
        ),
        Callout(
            bbox=(2750, 780, 3550, 1480),
            title="Submódulos de Instrumentación I2C Conectados",
            lines=[
                "• Bus I2C apantallado: SDA (GPIO 21), SCL (GPIO 22)",
                "• ADS1115 (ADC con filtros RC), MCP4725 (DAC) y AHT20"
            ],
            theme_color=(59, 130, 246),  # Azul
            card_xy=(2850, 180),
            pointer=(3150, 1100),
            bbox_labels=["ADS1115 + MCP4725"]
        ),
        Callout(
            bbox=(750, 1400, 1450, 1840),
            title="Header Bus TRIAC y Arnés Ribbon",
            lines=[
                "• Orden físico 1:1: [VCC | GND | ZC | CH1 | CH2 | CH3 | CH4]",
                "• Cable plano de 7 hilos hacia módulo de potencia AC"
            ],
            theme_color=(168, 85, 247),  # Morado
            card_xy=(450, 1450),
            pointer=(1100, 1600),
            bbox_labels=["Arnés Ribbon 7P"]
        ),
        Callout(
            bbox=(1850, 1150, 2750, 1550),
            title="Sockets SPI para 4x Termopares MAX6675",
            lines=[
                "• Orden físico 1:1: [SO | CS | CLK | VCC | GND]",
                "• Desacoplo: Capacitor cerámico 100 nF en cada zócalo",
                "• Buses compartidos de reloj y datos hacia ESP32-S3"
            ],
            theme_color=(20, 184, 166),  # Turquesa
            card_xy=(1450, 1450),
            pointer=(2300, 1350),
            bbox_labels=["4x MAX6675 SPI"]
        ),
        Callout(
            bbox=(3450, 50, 4080, 1450),
            title="Ventilación Forzada de Gabinete (12V)",
            lines=[
                "• Flujo de aire directo a disipadores de potencia",
                "• Mantiene MOSFETs y semiconductores bajo 45 °C"
            ],
            theme_color=(100, 116, 139),  # Pizarra
            card_xy=(3300, 1450),
            pointer=(3750, 600),
            bbox_labels=["Ventilación 12V"]
        )
    ]
    render_annotated_image(
        src_filename="Placa principal conectada.jpg",
        out_filename="02_Placa_Conectada_Rotulada.jpg",
        banner_data={
            "title": "GABINETE DE CONTROL Y POTENCIA EN OPERACIÓN VIVA",
            "subtitle": "Integración Eléctrica Completa: Fuente SMPS 12V 10A, Buck 6.80V, Buses y Refrigeración",
            "badge_text": "PANEL INTEGRADO",
            "badge_color": (16, 185, 129)
        },
        callouts=callouts,
        rotate_deg=180
    )


# ==============================================================================
# 3. IMAGEN 3: ETAPA VCSS ROTULADA (ORIENTACIÓN NATURAL)
# ==============================================================================
def generar_03_etapa_vcss():
    callouts = [
        Callout(
            bbox=(1080, 980, 1580, 1340),
            title="Clema 1: [GND | AGND]",
            lines=[
                "• Borne GND: Retorno de potencia de alta corriente (hasta 3.5A) a SMPS",
                "• Borne AGND: Masa analógica limpia hacia cabezal púrpura de placa madre",
                "• Desacoplo galvánico para suprimir caídas parásitas en consigna VREF"
            ],
            theme_color=(59, 130, 246),
            card_xy=(80, 1380),
            pointer=(1330, 1160),
            bbox_labels=["Clema 1: [GND | AGND]"]
        ),
        Callout(
            bbox=(1860, 980, 2380, 1340),
            title="Clema 2: [VREF | VCC]",
            lines=[
                "• Borne VREF: Consigna analógica continua 0-3.3V desde MCP4725 (0x60)",
                "• Borne VCC: +12.0V DC desde SMPS para polarización VDD de LM358N (Pin 8)",
                "• Garantiza plena excursión de compuerta (Vgs ≈ 6–10V) en MOSFETs"
            ],
            theme_color=(249, 115, 22),
            card_xy=(1350, 1380),
            pointer=(2120, 1160),
            bbox_labels=["Clema 2: [VREF | VCC]"]
        ),
        Callout(
            bbox=(2660, 980, 3180, 1340),
            title="Clema 3: [VCC | Out Drain]",
            lines=[
                "• Borne VCC: +12V hacia contacto COM 1 de Relé de Celda (Ánodo)",
                "• Borne Out Drain: Retorno catódico hacia Drains en paralelo de IRLZ44N",
                "• Conmutación Low-Side comandada por relé bipolar de seguridad"
            ],
            theme_color=(16, 185, 129),
            card_xy=(2650, 1380),
            pointer=(2920, 1160),
            bbox_labels=["Clema 3: [VCC | Out Drain]"]
        ),
        Callout(
            bbox=(1300, 260, 1680, 820),
            title="2x MOSFETs IRLZ44N (Sumidero Low-Side)",
            lines=[
                "• Transistores de potencia montados sobre disipador con aislamiento",
                "• Operan en región activa lineal gobernados por OpAmp LM358N",
                "• Reparto equitativo de disipación térmica y corriente de celda"
            ],
            theme_color=(14, 165, 233),
            card_xy=(80, 180),
            pointer=(1700, 550),
            extra_bboxes=[(1720, 260, 2100, 820)],
            bbox_labels=["Q1 (IRLZ44N)", "Q2 (IRLZ44N)"]
        ),
        Callout(
            bbox=(2300, 260, 2680, 820),
            title="2x Shunts de Precisión 1.0 Ω / 10W (Cerámica)",
            lines=[
                "• Conversión analógica I -> V: Sensibilidad exacta de 1.0 V/A",
                "• Headers SH1 y SH2: Conectan por Dupont amarillo hacia placa madre [A2 | A3]",
                "• Permite al ADC ADS1115 medir balance térmico y corriente total"
            ],
            theme_color=(168, 85, 247),
            card_xy=(2650, 180),
            pointer=(2700, 550),
            extra_bboxes=[(2720, 260, 3100, 820)],
            bbox_labels=["R_SH1 (1.0Ω 10W)", "R_SH2 (1.0Ω 10W)"]
        )
    ]
    render_annotated_image(
        src_filename="VCCS.jpg",
        out_filename="03_Etapa_VCSS_Rotulada.jpg",
        banner_data={
            "title": "SUMIDERO DE CORRIENTE CONSTANTE (ETAPA ANALÓGICA VCSS)",
            "subtitle": "Mapeo de Clemas Referenciadas: [GND | AGND], [VREF | VCC], [VCC | Out Drain] + Shunts 10W y MOSFETs IRLZ44N",
            "badge_text": "CIRCUITO VCSS",
            "badge_color": (249, 115, 22)
        },
        callouts=callouts,
        rotate_deg=0
    )


# ==============================================================================
# 4. IMAGEN 4: MODULO DE TRIACS ROTULADO
# ==============================================================================
def generar_04_modulo_triacs():
    callouts = [
        Callout(
            bbox=(530, 1100, 930, 1520),
            title="🟢 Clema de Entrada: [AC] 120V",
            lines=[
                "• Bornera 2P reforzada para línea viva (120 VAC) y neutro general",
                "• Alimenta los 4 canales resistivos de calentamiento de las tinas",
                "• Alimenta el detector optoacoplado de Cruce por Cero (ZCS)"
            ],
            theme_color=(16, 185, 129),
            card_xy=(80, 1150),
            pointer=(730, 1310),
            bbox_labels=["Entrada AC 120V"]
        ),
        Callout(
            bbox=(1300, 1100, 1750, 1520),
            title="🟠 Salidas de Potencia: [T1 | T2 | T3 | T4]",
            lines=[
                "• T1: Calentador Tina 1 (Desengrase Alcalino 450W) — TRIAC BTA24-600B",
                "• T2: Calentador Tina 2 (Decapado Alcalino 450W) — TRIAC BTA24-600B",
                "• T3: Calentador Tina 3 (Celda Hull Zincado 18W) — TRIAC BTA24-600B",
                "• T4: Calentador Tina 4 (Niquelado Watts 450W) — TRIAC BTA24-600B",
                "• Conmutación por control de ángulo de fase α gobernado por interrupción ZC"
            ],
            theme_color=(249, 115, 22),
            card_xy=(1300, 1150),
            pointer=(2425, 1310),
            extra_bboxes=[(1900, 1100, 2350, 1520), (2500, 1100, 2950, 1520), (3100, 1100, 3550, 1520)],
            bbox_labels=["T1 (Desengrase)", "T2 (Decapado)", "T3 (Celda Hull)", "T4 (Niquelado)"]
        ),
        Callout(
            bbox=(850, 250, 1250, 520),
            title="🔵 Cabezal de Control: [VCC | GND | ZC]",
            lines=[
                "• Pin 1 (VCC): +5.0V Lógica para ánodos de optoacopladores MOC3021",
                "• Pin 2 (GND): Masa lógica común hacia Arduino Nano y placa madre",
                "• Pin 3 (ZC): Pulso Cruce por Cero (120 Hz) -> Arduino Nano Pin D3 (INT1)",
                "• Optoacoplador 4N35 entrega interrupción en flanco cada 8.33 ms"
            ],
            theme_color=(14, 165, 233),
            card_xy=(80, 180),
            pointer=(1050, 385),
            bbox_labels=["Control: [VCC | GND | ZC]"]
        ),
        Callout(
            bbox=(1450, 250, 1850, 520),
            title="🔴 Disparos Optoacoplados: [1 | 2 | 3 | 4]",
            lines=[
                "• Pin 1 (CH1): Compuerta Optotriac 1 <- Arduino Nano Pin D7 (Timer 1)",
                "• Pin 2 (CH2): Compuerta Optotriac 2 <- Arduino Nano Pin D8 (Timer 1)",
                "• Pin 3 (CH3): Compuerta Optotriac 3 <- Arduino Nano Pin D9 (Timer 1)",
                "• Pin 4 (CH4): Compuerta Optotriac 4 <- Arduino Nano Pin D10 (Timer 1)",
                "• Aislamiento galvánico de 5000 Vrms con red amortiguadora Snubber RC"
            ],
            theme_color=(239, 68, 68),
            card_xy=(1500, 180),
            pointer=(2475, 385),
            extra_bboxes=[(2000, 250, 2400, 520), (2550, 250, 2950, 520), (3100, 250, 3500, 520)],
            bbox_labels=["1 (CH1 -> D7)", "2 (CH2 -> D8)", "3 (CH3 -> D9)", "4 (CH4 -> D10)"]
        )
    ]
    render_annotated_image(
        src_filename="Modulo TRIACS.jpg",
        out_filename="04_Modulo_TRIACS_Rotulado.jpg",
        banner_data={
            "title": "MÓDULO DE POTENCIA AC (4 CANALES TRIAC + DETECTOR CRUCE POR CERO)",
            "subtitle": "Mapeo Referenciado: 🟢 Entrada [AC] | 🟠 Salidas [T1..T4] | 🔵 Control [VCC GND ZC] | 🔴 Disparos [1..4]",
            "badge_text": "POTENCIA 120 VAC",
            "badge_color": (239, 68, 68)
        },
        callouts=callouts
    )


# ==============================================================================
# 5. IMAGEN 5: MACRO DETALLE BUS ADC E I2C (SIN COLISIÓN AHT20)
# ==============================================================================
def generar_05_detalle_bus_adc():
    callouts = [
        Callout(
            bbox=(1420, 580, 2300, 1120),
            title="ADS1115 ADC 16-bit (I2C @ 0x48)",
            lines=[
                "• Silkscreen 1:1: [VDD | GND | SCL | SDA | ADDR | ALRT | A0 | A1 | A2 | A3]",
                "• VDD: Alimentado a +5V lógico para rango dinámico óptimo",
                "• Bus I2C: Conectado a SDA (GPIO 21) y SCL (GPIO 22) de ESP32-S3"
            ],
            theme_color=(59, 130, 246),  # Azul
            card_xy=(80, 200),
            pointer=(1450, 850),
            bbox_labels=["ADS1115 ADC (0x48)"]
        ),
        Callout(
            bbox=(1500, 1180, 2400, 1520),
            title="Redes de Filtro Pasabajos RC (Canales A0 - A3)",
            lines=[
                "• 4x Filtros RC dedicados: Resistencia serie + Capacitor cerámico 100 nF",
                "• Canal A1: Entrada filtrada desde Sonda de pH (PH-4502C)",
                "• Canales A2 y A3: Entradas filtradas de corriente Shunts 1 y 2 VCSS",
                "• Supresión de rizado de alta frecuencia y ruido de conmutación SMPS"
            ],
            theme_color=(245, 158, 11),  # Ámbar
            card_xy=(80, 750),
            pointer=(1950, 1350),
            bbox_labels=["Filtros RC Canales A0-A3"]
        ),
        Callout(
            bbox=(2120, 50, 2580, 440),
            title="MCP4725 DAC 12-bit (I2C @ 0x60)",
            lines=[
                "• Silkscreen 1:1: [OUT | GND | SCL | SDA | VCC | GND]",
                "• Salida OUT: Consigna analógica VREF hacia etapa VCSS (0 - 3.53 V)",
                "• Control de corriente de electrodeposición en lazo cerrado"
            ],
            theme_color=(239, 68, 68),  # Rojo
            card_xy=(2650, 180),
            pointer=(2350, 250),
            bbox_labels=["MCP4725 DAC (0x60)"]
        ),
        Callout(
            bbox=(2580, 560, 3080, 1040),
            title="Sensor Ambiental AHT20 + BMP280",
            lines=[
                "• Silkscreen 1:1: [VDD | SDA | GND | SCL]",
                "• AHT20 (0x38): Temperatura y Humedad relativa en cabina",
                "• BMP280 (0x76): Presión barométrica ambiental"
            ],
            theme_color=(168, 85, 247),  # Morado
            card_xy=(2650, 1150),
            pointer=(2800, 800),
            bbox_labels=["AHT20 / BMP280 (I2C)"]
        )
    ]
    render_annotated_image(
        src_filename="BUS ADC.jpg",
        out_filename="05_Detalle_Bus_ADC_I2C.jpg",
        banner_data={
            "title": "MACRO DETALLE: BUS DE INSTRUMENTACIÓN I2C Y CONVERTIDORES",
            "subtitle": "ADS1115 (ADC 16-bit con filtros RC A0-A3) + MCP4725 (DAC 12-bit VREF) + AHT20/BMP280",
            "badge_text": "DETALLE I2C/ADC",
            "badge_color": (59, 130, 246)
        },
        callouts=callouts
    )


# ==============================================================================
# 6. IMAGEN 6: MACRO DETALLE BUSES TERMOPARES (PUNTEROS PARALELOS)
# ==============================================================================
def generar_06_detalle_termopares():
    callouts = [
        Callout(
            bbox=(1080, 1060, 1500, 1340),
            title="Socket Termopar Canal 0 (Desengrase)",
            lines=[
                "• Pines 1:1: [SO | CS | CLK | VCC | GND]",
                "• CS0 asignado a ESP32-S3 GPIO 5 | Bus SPI: SCK=18, SO=19",
                "• Desacoplo cerámico 100 nF dedicado entre VCC y GND"
            ],
            theme_color=(239, 68, 68),  # Rojo
            card_xy=(80, 180),
            pointer=(1290, 1200),
            bbox_labels=["Socket TC0: Desengrase (CS0=D5)"]
        ),
        Callout(
            bbox=(1580, 1060, 2000, 1340),
            title="Socket Termopar Canal 1 (Decapado)",
            lines=[
                "• Pines 1:1: [SO | CS | CLK | VCC | GND]",
                "• CS1 asignado a ESP32-S3 GPIO 4 | Bus SPI compartido",
                "• Desacoplo cerámico 100 nF dedicado entre VCC y GND"
            ],
            theme_color=(249, 115, 22),  # Naranja
            card_xy=(850, 180),
            pointer=(1790, 1200),
            bbox_labels=["Socket TC1: Decapado (CS1=D4)"]
        ),
        Callout(
            bbox=(2080, 1060, 2500, 1340),
            title="Socket Termopar Canal 2 (Celda Hull)",
            lines=[
                "• Pines 1:1: [SO | CS | CLK | VCC | GND]",
                "• CS2 asignado a ESP32-S3 GPIO 13 | Bus SPI compartido",
                "• Desacoplo cerámico 100 nF dedicado entre VCC y GND"
            ],
            theme_color=(16, 185, 129),  # Verde
            card_xy=(1850, 180),
            pointer=(2290, 1200),
            bbox_labels=["Socket TC2: Celda Hull (CS2=D13)"]
        ),
        Callout(
            bbox=(2580, 1060, 3000, 1340),
            title="Socket Termopar Canal 3 (Niquelado)",
            lines=[
                "• Pines 1:1: [SO | CS | CLK | VCC | GND]",
                "• CS3 asignado a ESP32-S3 GPIO 14 | Bus SPI compartido",
                "• Desacoplo cerámico 100 nF dedicado entre VCC y GND"
            ],
            theme_color=(14, 165, 233),  # Cyan
            card_xy=(2750, 180),
            pointer=(2790, 1200),
            bbox_labels=["Socket TC3: Niquelado (CS3=D14)"]
        ),
        Callout(
            bbox=(1100, 420, 3000, 680),
            title="Buses de Pistas SPI Ruteadas",
            lines=[
                "• Pista Superior: Línea de Reloj SCK (ESP32-S3 GPIO 18) común a los 4 sockets",
                "• Pista Inferior: Línea de Datos MISO/SO (ESP32-S3 GPIO 19) común a los 4 sockets",
                "• Conexión directa 1:1 al pinout estándar del módulo MAX6675"
            ],
            theme_color=(245, 158, 11),  # Ámbar
            card_xy=(80, 680),
            pointer=(2050, 550),
            bbox_labels=["Pistas SPI [SCK: D18 | SO: D19]"]
        )
    ]
    render_annotated_image(
        src_filename="Buses Termopares .jpg",
        out_filename="06_Detalle_Buses_Termopares.jpg",
        banner_data={
            "title": "MACRO DETALLE: 4x SOCKETS SPI PARA TERMOPARES MAX6675",
            "subtitle": "Alineación Física 1:1 de Pines [SO | CS | CLK | VCC | GND] + Desacoplo Cerámico 100 nF por Canal",
            "badge_text": "BUS SPI TERMOPARES",
            "badge_color": (20, 184, 166)
        },
        callouts=callouts
    )


# ==============================================================================
# 7. IMAGEN 7: MACRO DETALLE CABEZALES PLACA MADRE VCSS & POTENCIA
# ==============================================================================
def generar_07_detalle_cabezales_madre_vcss():
    socket_callouts = [
        Callout(
            bbox=(1920, 440, 2380, 710),
            title="🟣 Cabezal Consigna DAC: [Vref | NC | GND]",
            lines=[
                "• Pin 1 (Vref): Consigna analógica continua 0-3.3V desde MCP4725 (0x60)",
                "• Pin 2 (NC): Guarda intermedia no conectada (aislamiento contra EMI)",
                "• Pin 3 (GND): Retorno de masa analógica limpia (AGND hacia VCSS)",
                "• Conecta directamente a Clema 2 [VREF] y Clema 1 [AGND] de VCSS"
            ],
            theme_color=(168, 85, 247),
            card_xy=(2450, 180),
            pointer=(2150, 575),
            bbox_labels=["🟣 [Vref | NC | GND]"]
        ),
        Callout(
            bbox=(1680, 970, 2220, 1370),
            title="🟡 Cabezal Sensado Shunts: [A2 | A3]",
            lines=[
                "• Pin 1 (A2): Entrada ADC ADS1115 Canal A2 <- Header SH1 (1.0 V/A)",
                "• Pin 2 (A3): Entrada ADC ADS1115 Canal A3 <- Header SH2 (1.0 V/A)",
                "• Conexión por cable Dupont dual amarillo hacia shunts 10W de VCSS",
                "• Muestreo analógico a 16 bits @ 860 SPS para control y balance"
            ],
            theme_color=(234, 179, 8),
            card_xy=(2350, 1100),
            pointer=(1950, 1175),
            bbox_labels=["🟡 [A2 | A3]"]
        ),
        Callout(
            bbox=(1020, 430, 1480, 830),
            title="🔵 Cabezal Potencia Celda: [VCC | OUT+ | GND]",
            lines=[
                "• Pin 1 (VCC): Riel de potencia +12.0V DC desde fuente SMPS",
                "• Pin 2 (OUT+): Línea de celda protegida y conmutada por relé",
                "• Pin 3 (GND): Retorno común de masa de potencia",
                "• Distribución hacia etapa de relés y retorno catódico"
            ],
            theme_color=(14, 165, 233),
            card_xy=(80, 180),
            pointer=(1240, 635),
            bbox_labels=["🔵 [VCC | OUT+ | GND]"]
        ),
        Callout(
            bbox=(1100, 1120, 1520, 1620),
            title="🟠 Cabezal de Bobina: [Socket Power ZCS]",
            lines=[
                "• Pin 1 (5V): +5V Lógica de control para optoacopladores PC817",
                "• Pin 2 (5V Rele): +5V Aislado para bobinas de relé (terminal JD-VCC)",
                "• Pin 3 (5GND): Masa aislada de retorno inductivo",
                "• Obligatorio retirar jumper azul JD-VCC/VCC en módulo de relés"
            ],
            theme_color=(249, 115, 22),
            card_xy=(80, 1100),
            pointer=(1300, 1375),
            bbox_labels=["🟠 [Socket Power ZCS]"]
        )
    ]
    render_annotated_image(
        src_filename="Sockets ZCS, A3,A2  VREF AGND .jpg",
        out_filename="07_Detalle_Cabezales_Madre_VCSS.jpg",
        banner_data={
            "title": "MACRO DETALLE: CABEZALES DE INTERCONEXIÓN VCSS & POTENCIA",
            "subtitle": "Placa Madre (Sector ESP32-S3): 🟣 [Vref | NC | GND] | 🟡 [A2 | A3] | 🔵 [VCC | OUT+ | GND] | 🟠 [Socket Power ZCS]",
            "badge_text": "CABEZALES PLACA MADRE",
            "badge_color": (168, 85, 247)
        },
        callouts=socket_callouts
    )


# ==============================================================================
# 8. IMAGEN 8: INFOGRAFÍA MAESTRA DE ALINEACIÓN DE PINES (COMPOSITE)
# ==============================================================================
def generar_08_alineacion_sensores():
    """
    Genera un póster técnico ultra-HD (4096 x 2304) que presenta la correspondencia 1:1
    entre los sensores/actuadores sueltos y los cabezales/zócalos de la placa madre:
    - Termopares MAX6675 (SO CS CLK VCC GND) frente a frente con el zócalo + cap 100 nF
    - Cabezal TRIAC (VCC GND ZC CH1 CH2 CH3 CH4)
    - Módulo Relé dividido (Lógica GND IN1 IN2 VCC y Alimentación aislada 5V 5V Rele 5GND)
    - Módulo pH (PH-4502C) y convertidores I2C (ADS1115 con filtros RC y MCP4725 DAC)
    """
    W, H = 4096, 2304
    canvas = Image.new("RGB", (W, H), (11, 17, 32))
    draw = ImageDraw.Draw(canvas)

    # 1. Banner superior
    draw_header_banner(
        draw, W,
        "GUÍA MAESTRA DE ALINEACIÓN DE PINES: SENSORES, ACTUADORES Y CABEZALES",
        "Correspondencia Física 1:1 entre Módulos Externos y Zócalos de la Placa Madre — Reglas Críticas de Ensamblaje",
        "MAPA DE PINES 1:1",
        (16, 185, 129)
    )

    # Coordenadas de las 4 tarjetas principales (2x2 grid)
    # Fila 1: y = 160 a 1180 | Fila 2: y = 1220 a 2240
    # Col 1: x = 50 a 2010   | Col 2: x = 2086 a 4046

    # ==========================================================================
    # TARJETA A (TOP-LEFT): MÓDULO TERMOPAR K (MAX6675) & SOCKET SPI
    # ==========================================================================
    ax1, ay1, ax2, ay2 = 50, 160, 2010, 1180
    draw.rounded_rectangle([(ax1, ay1), (ax2, ay2)], radius=14, fill=(15, 23, 42), outline=(20, 184, 166), width=3)
    draw.rounded_rectangle([(ax1, ay1), (ax2, ay1 + 8)], radius=4, fill=(20, 184, 166))
    
    # Header de tarjeta
    draw.text((ax1 + 25, ay1 + 20), "1. MÓDULO TERMOPAR K (MAX6675) <---> ZÓCALO SPI DE PLACA MADRE", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((ax1 + 25, ay1 + 65), "Regla Física: Al colocar el módulo frente al zócalo hembra, el orden de pines coincide exactamente 1:1", fill=(148, 163, 184), font=FONT_SUB)

    # Pegar imagen de MAX6675
    path_max = resolve_src_path("AR0780-Termopar-K-Con-Modulo-Max6675-PINOUT-768x768.jpg")
    im_max = Image.open(path_max).resize((420, 420), Image.Resampling.LANCZOS)
    canvas.paste(im_max, (ax1 + 25, ay1 + 130))
    draw.rectangle([(ax1 + 25, ay1 + 130), (ax1 + 445, ay1 + 550)], outline=(20, 184, 166), width=2)
    draw.text((ax1 + 100, ay1 + 560), "Pinout Módulo MAX6675", fill=(20, 184, 166), font=FONT_BADGE)

    # Pegar recorte de zócalo real con capacitor cerámico
    path_pcb = resolve_src_path("Placa todos los sockets.jpg")
    im_pcb = Image.open(path_pcb)
    crop_tc = im_pcb.crop((1600, 1150, 3050, 1800)).resize((580, 290), Image.Resampling.LANCZOS)
    canvas.paste(crop_tc, (ax1 + 475, ay1 + 150))
    draw.rectangle([(ax1 + 475, ay1 + 150), (ax1 + 1055, ay1 + 440)], outline=(20, 184, 166), width=2)
    draw.text((ax1 + 510, ay1 + 450), "4x Zócalos Hembra en Placa + Capacitores 100 nF", fill=(20, 184, 166), font=FONT_BADGE)

    # Tabla de correspondencia de pines
    tx = ax1 + 1090
    ty = ay1 + 130
    draw.text((tx, ty), "CORRESPONDENCIA DIRECTA 1:1:", fill=(248, 250, 252), font=FONT_BADGE)
    
    pin_tc = [
        ("SO",  "ESP32-S3 GPIO 19 (MISO Compartido)", (168, 85, 247)),
        ("CS",  "Chip Select Dedicado (CS0=G5, CS1=G4, CS2=G13, CS3=G14)", (249, 115, 22)),
        ("CLK", "ESP32-S3 GPIO 18 (SCK Compartido)", (16, 185, 129)),
        ("VCC", "+3.3V Lógica (Alimentación regulada LM1117)", (239, 68, 68)),
        ("GND", "GND Digital Común", (59, 130, 246))
    ]
    cur_ty = ty + 40
    for p_name, p_desc, p_color in pin_tc:
        # Badge pin
        draw.rounded_rectangle([(tx, cur_ty), (tx + 75, cur_ty + 34)], radius=6, fill=p_color)
        draw.text((tx + 12, cur_ty + 4), p_name, fill=(255, 255, 255), font=FONT_MONO)
        draw.text((tx + 90, cur_ty + 4), f"<--->  {p_desc}", fill=(226, 232, 240), font=FONT_SUB)
        cur_ty += 46

    # Notas técnicas inferiores de tarjeta
    ny = ay1 + 640
    notes_tc = [
        "• Regla de oro de orientación: Poniendo el conector del sensor de frente al zócalo hembra coinciden exactamente.",
        "• Desacoplo por hardware: Cada zócalo posee un capacitor cerámico de 100 nF soldado entre VCC y GND.",
        "• Asignación: Canal 0 (Desengrase - CS0), Canal 1 (Decapado - CS1), Canal 2 (Celda Hull - CS2), Canal 3 (Niquelado - CS3)."
    ]
    for n in notes_tc:
        draw.text((ax1 + 30, ny), n, fill=(203, 213, 225), font=FONT_SUB)
        ny += 36


    # ==========================================================================
    # TARJETA B (TOP-RIGHT): CABEZAL BUS TRIAC (7 PINES)
    # ==========================================================================
    bx1, by1, bx2, by2 = 2086, 160, 4046, 1180
    draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=14, fill=(15, 23, 42), outline=(239, 68, 68), width=3)
    draw.rounded_rectangle([(bx1, by1), (bx2, by1 + 8)], radius=4, fill=(239, 68, 68))
    
    draw.text((bx1 + 25, by1 + 20), "2. CABEZAL BUS TRIAC (7 PINES) — PLACA MADRE <---> MÓDULO POTENCIA", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((bx1 + 25, by1 + 65), "Orden de Pines: VCC | GND | ZC | CH1 | CH2 | CH3 | CH4 (Arnés plano ribbon 7 hilos)", fill=(148, 163, 184), font=FONT_SUB)

    # Pegar foto macro de arnés conectado
    path_triac_live = resolve_src_path("COnexion TRIACS .jpg")
    im_tr_live = Image.open(path_triac_live)
    crop_tr = im_tr_live.crop((250, 0, 3100, 1100)).resize((720, 420), Image.Resampling.LANCZOS)
    canvas.paste(crop_tr, (bx1 + 30, by1 + 130))
    draw.rectangle([(bx1 + 30, by1 + 130), (bx1 + 750, by1 + 550)], outline=(239, 68, 68), width=2)
    draw.text((bx1 + 150, by1 + 560), "Conexión Real Ribbon 7 Pines + Cargas", fill=(239, 68, 68), font=FONT_BADGE)

    # Tabla de bus TRIAC
    ttx = bx1 + 790
    tty = by1 + 130
    draw.text((ttx, tty), "ORDEN DE PINES Y CÓDIGO DE COLORES RIBBON:", fill=(248, 250, 252), font=FONT_BADGE)

    pin_triac = [
        ("VCC", "Blanco", "+5V Lógica de control para optoacopladores", (255, 255, 255), (30, 41, 59)),
        ("GND", "Negro", "Tierra de control común", (51, 65, 85), (255, 255, 255)),
        ("ZC",  "Gris",  "Cruce por Cero (ZCS 120 Hz) -> Arduino Nano Pin D3 (INT1)", (100, 116, 139), (255, 255, 255)),
        ("CH1", "Morado","Disparo TTL Canal 0 (Desengrase 450W) -> Nano D7", (168, 85, 247), (255, 255, 255)),
        ("CH2", "Azul",  "Disparo TTL Canal 1 (Decapado 450W) -> Nano D8", (59, 130, 246), (255, 255, 255)),
        ("CH3", "Verde", "Disparo TTL Canal 2 (Celda Hull 18W) -> Nano D9", (16, 185, 129), (255, 255, 255)),
        ("CH4", "Amarillo","Disparo TTL Canal 3 (Niquelado 450W) -> Nano D10", (234, 179, 8), (0, 0, 0))
    ]
    cur_tty = tty + 40
    for p_name, p_col_name, p_desc, p_bg, p_fg in pin_triac:
        draw.rounded_rectangle([(ttx, cur_tty), (ttx + 65, cur_tty + 32)], radius=5, fill=p_bg, outline=(203, 213, 225), width=1)
        draw.text((ttx + 10, cur_tty + 4), p_name, fill=p_fg, font=FONT_MONO)
        draw.text((ttx + 78, cur_tty + 4), f"[{p_col_name}]: {p_desc}", fill=(226, 232, 240), font=FONT_SUB)
        cur_tty += 42

    # Notas técnicas
    bny = by1 + 640
    notes_tr = [
        "• Conexión Directa: El arnés plano ribbon conecta pin a pin el cabezal macho de la placa madre al módulo TRIAC.",
        "• Sincronización AC: El detector ZCS (4N35) genera pulsos a 120 Hz; el Nano calcula el retardo α con Timer1.",
        "• Etapa de Salida: 4x TRIACs BTA24-600B (25A) aislados galvánicamente por 4x MOC3021 con redes Snubber RC."
    ]
    for n in notes_tr:
        draw.text((bx1 + 30, bny), n, fill=(203, 213, 225), font=FONT_SUB)
        bny += 36


    # ==========================================================================
    # TARJETA C (BOTTOM-LEFT): MÓDULO RELÉ Y CABEZAL "SOCKET POWER ZCS"
    # ==========================================================================
    cx1, cy1, cx2, cy2 = 50, 1220, 2010, 2240
    draw.rounded_rectangle([(cx1, cy1), (cx2, cy2)], radius=14, fill=(15, 23, 42), outline=(249, 115, 22), width=3)
    draw.rounded_rectangle([(cx1, cy1), (cx2, cy1 + 8)], radius=4, fill=(249, 115, 22))

    draw.text((cx1 + 25, cy1 + 20), "3. MÓDULO DE RELÉS 2 CANALES & CABEZAL 'SOCKET POWER ZCS' (AISLADO)", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((cx1 + 25, cy1 + 65), "Arquitectura Dividida: Lado Lógico (GND IN1 IN2 VCC) y Lado Bobina Aislada (5V 5V Rele 5GND)", fill=(148, 163, 184), font=FONT_SUB)

    # Pegar imagen del relé
    path_rele = resolve_src_path("mod2rele-2.png")
    im_rele = Image.open(path_rele).resize((440, 440), Image.Resampling.LANCZOS)
    canvas.paste(im_rele, (cx1 + 30, cy1 + 130))
    draw.rectangle([(cx1 + 30, cy1 + 130), (cx1 + 470, cy1 + 570)], outline=(249, 115, 22), width=2)
    draw.text((cx1 + 110, cy1 + 580), "Módulo Relé 2 Canales", fill=(249, 115, 22), font=FONT_BADGE)

    # Pegar recorte de Socket Power ZCS de la placa madre
    path_zcs_sock = resolve_src_path("Socket Power ZCS.jpg")
    im_zcs_raw = Image.open(path_zcs_sock)
    crop_zcs = im_zcs_raw.crop((1200, 400, 2400, 1200)).resize((660, 330), Image.Resampling.LANCZOS)
    canvas.paste(crop_zcs, (cx1 + 510, cy1 + 150))
    draw.rectangle([(cx1 + 510, cy1 + 150), (cx1 + 1170, cy1 + 480)], outline=(249, 115, 22), width=2)
    draw.text((cx1 + 580, cy1 + 490), "Cabezal 'Socket Power ZCS' (Filas 32-34)", fill=(249, 115, 22), font=FONT_BADGE)

    # Explicación de conexión aislada
    ctx = cx1 + 1210
    cty = cy1 + 130
    draw.text((ctx, cty), "DISTRIBUCIÓN DEL CABEZAL POWER ZCS:", fill=(248, 250, 252), font=FONT_BADGE)

    pin_rele = [
        ("5V",      "Pin 1: +5V Lógica de control", (239, 68, 68)),
        ("5V Rele", "Pin 2: +5V Alimentación Bobina (JD-VCC)", (249, 115, 22)),
        ("5GND",    "Pin 3: Tierra Aislada de Bobina de Relé", (59, 130, 246))
    ]
    cur_cty = cty + 40
    for p_name, p_desc, p_color in pin_rele:
        draw.rounded_rectangle([(ctx, cur_cty), (ctx + 110, cur_cty + 34)], radius=6, fill=p_color)
        draw.text((ctx + 12, cur_cty + 4), p_name, fill=(255, 255, 255), font=FONT_MONO)
        draw.text((ctx + 125, cur_cty + 4), f"<--->  {p_desc}", fill=(226, 232, 240), font=FONT_SUB)
        cur_cty += 46

    draw.text((ctx, cur_cty + 10), "LADO CONTROL LÓGICO: [GND | IN1 | IN2 | VCC]", fill=(16, 185, 129), font=FONT_BADGE)
    draw.text((ctx, cur_cty + 48), "• IN1 / IN2: Inversión de polaridad Ánodo/Cátodo", fill=(226, 232, 240), font=FONT_SUB)

    # Notas técnicas
    cny = cy1 + 640
    notes_rele = [
        "• Desconexión obligatoria de jumper: Se retira el jumper azul JD-VCC / VCC en el módulo de relés.",
        "• Supresión de rebote inductivo: Al alimentar la bobina desde el cabezal 'Socket Power ZCS', los transitorios",
        "  de apertura/cierre quedan galvánicamente aislados y no provocan reseteos en el ESP32-S3 ni en el Nano.",
        "• Contactos de Potencia: Conmutan la corriente de la celda (+12V hacia ánodo o inversión despasivación)."
    ]
    for n in notes_rele:
        draw.text((cx1 + 30, cny), n, fill=(203, 213, 225), font=FONT_SUB)
        cny += 34


    # ==========================================================================
    # TARJETA D (BOTTOM-RIGHT): SENSOR DE pH & CONVERTIDORES I2C
    # ==========================================================================
    dx1, dy1, dx2, dy2 = 2086, 1220, 4046, 2240
    draw.rounded_rectangle([(dx1, dy1), (dx2, dy2)], radius=14, fill=(15, 23, 42), outline=(59, 130, 246), width=3)
    draw.rounded_rectangle([(dx1, dy1), (dx2, dy1 + 8)], radius=4, fill=(59, 130, 246))

    draw.text((dx1 + 25, dy1 + 20), "4. SENSOR DE pH (PH-4502C) Y CONVERTIDORES I2C (ADS1115 & MCP4725)", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((dx1 + 25, dy1 + 65), "Alineación y Filtrado RC: Entrada pH en ADS1115 Canal A1 + Consigna VREF de DAC MCP4725 a VCSS", fill=(148, 163, 184), font=FONT_SUB)

    # Pegar foto del sensor de pH
    path_ph = resolve_src_path("sensor PH.jpg")
    im_ph = Image.open(path_ph).resize((310, 310), Image.Resampling.LANCZOS)
    canvas.paste(im_ph, (dx1 + 25, dy1 + 130))
    draw.rectangle([(dx1 + 25, dy1 + 130), (dx1 + 335, dy1 + 440)], outline=(59, 130, 246), width=2)
    draw.text((dx1 + 70, dy1 + 450), "Sensor pH-4502C", fill=(59, 130, 246), font=FONT_BADGE)

    # Pegar foto de ADS1115
    path_adc = resolve_src_path("AR0318-ADS1115-ADC-Amplificador-de-Ganancia-Programable-PINOUT-768x768.jpg")
    im_adc = Image.open(path_adc).resize((310, 310), Image.Resampling.LANCZOS)
    canvas.paste(im_adc, (dx1 + 355, dy1 + 130))
    draw.rectangle([(dx1 + 355, dy1 + 130), (dx1 + 665, dy1 + 440)], outline=(59, 130, 246), width=2)
    draw.text((dx1 + 395, dy1 + 450), "ADS1115 (ADC 16-bit)", fill=(59, 130, 246), font=FONT_BADGE)

    # Pegar foto de MCP4725
    path_dac = resolve_src_path("AR0578-DAC-MCP4725-I2C-PINOUT.jpg")
    im_dac = Image.open(path_dac).resize((310, 310), Image.Resampling.LANCZOS)
    canvas.paste(im_dac, (dx1 + 685, dy1 + 130))
    draw.rectangle([(dx1 + 685, dy1 + 130), (dx1 + 995, dy1 + 440)], outline=(239, 68, 68), width=2)
    draw.text((dx1 + 725, dy1 + 450), "MCP4725 (DAC 12-bit)", fill=(239, 68, 68), font=FONT_BADGE)

    # Mapeo y correspondencia
    dtx = dx1 + 1030
    dty = dy1 + 130
    draw.text((dtx, dty), "CONEXIÓN SENSOR pH -> ADS1115 (ADC):", fill=(248, 250, 252), font=FONT_BADGE)

    pin_ph = [
        ("PO",   "Salida Analógica pH", "-> ADS1115 Pin A1 vía Filtro Pasabajos RC", (249, 115, 22)),
        ("GNDA", "GND Analógica",       "-> AGND (Tierra analógica de instrumentación)", (59, 130, 246)),
        ("GND",  "Tierra Común",        "-> GND Digital de placa", (100, 116, 139)),
        ("VCC",  "+5V Alimentación",    "-> Barra +5V regulada limpia", (239, 68, 68))
    ]
    cur_dty = dty + 40
    for p_pin, p_fun, p_dest, p_col in pin_ph:
        draw.rounded_rectangle([(dtx, cur_dty), (dtx + 80, cur_dty + 32)], radius=5, fill=p_col)
        draw.text((dtx + 10, cur_dty + 4), p_pin, fill=(255, 255, 255), font=FONT_MONO)
        draw.text((dtx + 92, cur_dty + 4), f"{p_fun} {p_dest}", fill=(226, 232, 240), font=FONT_SUB)
        cur_dty += 42

    draw.text((dtx, cur_dty + 10), "CONEXIÓN MCP4725 (DAC) -> ETAPA VCSS:", fill=(248, 250, 252), font=FONT_BADGE)
    cur_dty += 46
    draw.text((dtx, cur_dty), "• OUT (0 - 3.53 V): Consigna VREF analógica hacia Clema 2 Pin 1 de VCSS", fill=(226, 232, 240), font=FONT_SUB)
    draw.text((dtx, cur_dty + 34), "• Canales A2 y A3 de ADS1115: Sensado de corriente Shunts 1 y 2 (1.0 V/A)", fill=(16, 185, 129), font=FONT_SUB)

    # Notas técnicas
    dny = dy1 + 640
    notes_ph = [
        "• Filtros Pasabajos RC Dedicados: Los 4 canales (A0-A3) del ADS1115 cuentan con resistencias serie y capacitores",
        "  cerámicos de 100 nF soldados bajo el zócalo para atenuar completamente el ruido de conmutación de la SMPS.",
        "• Calibración pH: Potenciómetro 1 (Offset) ajusta el punto neutro a 2.50V (pH 7.00).",
        "• Seguridad Galvánica: Los shunts cerámicos de 10W garantizan medición diferencial inmune a ruidos de tierra."
    ]
    for n in notes_ph:
        draw.text((dx1 + 30, dny), n, fill=(203, 213, 225), font=FONT_SUB)
        dny += 34

    # Guardar en ambas rutas
    out_rgb = canvas.convert("RGB")
    p1 = os.path.join(OUTPUT_DIR, "08_Alineacion_Pines_Sensores_Actuadores.jpg")
    p2 = os.path.join(MANUAL_OUTPUT_DIR, "08_Alineacion_Pines_Sensores_Actuadores.jpg")
    out_rgb.save(p1, quality=95)
    out_rgb.save(p2, quality=95)
    print("Generada exitosamente: 08_Alineacion_Pines_Sensores_Actuadores.jpg")


# ==============================================================================
# EJECUCIÓN MAESTRA
# ==============================================================================
def generar_todas():
    print("1/8 Generando Placa Principal Rotulada...")
    generar_01_placa_principal()
    print("2/8 Generando Placa Conectada Rotulada (180°)...")
    generar_02_placa_conectada()
    print("3/8 Generando Etapa VCSS Rotulada (Orientación Natural)...")
    generar_03_etapa_vcss()
    print("4/8 Generando Módulo TRIACS Rotulado...")
    generar_04_modulo_triacs()
    print("5/8 Generando Detalle Bus ADC e I2C...")
    generar_05_detalle_bus_adc()
    print("6/8 Generando Detalle Buses Termopares...")
    generar_06_detalle_termopares()
    print("7/8 Generando Detalle Cabezales Placa Madre VCSS & Potencia...")
    generar_07_detalle_cabezales_madre_vcss()
    print("8/8 Generando Infografía Maestra de Alineación de Pines...")
    generar_08_alineacion_sensores()


if __name__ == "__main__":
    print("=" * 70)
    print("Iniciando generación de 8 infografías técnicas en ultra-alta resolución...")
    print("=" * 70)
    generar_todas()
    print("=" * 70)
    print("¡Todas las 8 infografías generadas y replicadas exitosamente!")
    print("=" * 70)

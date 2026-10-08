#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del Diagrama de Bloques Funcional Limpio y Minimalista (Nombre + Función)
Planta Piloto de Electrodeposición y Galvanoplastia (SMEQ 2026)

Concepto de Diseño:
- Bloques limpios y espaciosos con estilo: [NOMBRE DEL BLOQUE] + [FUNCIÓN CLARA EN 1-2 LÍNEAS]
- Tipografía grande y de alta legibilidad a cualquier distancia o pantalla
- Flujo lógico evidente: Sensores (Izq) -> Control Central (Centro) -> Potencia y Celda (Der)
- HMI / SCADA en parte superior
- Colores semánticos bien diferenciados
"""

import os
from PIL import Image, ImageDraw, ImageFont

W = 2700
H = 1700

# Fuentes TrueType
FONT_TITLE_MAIN = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 38)
FONT_SUB_MAIN   = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
FONT_SECTION    = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)

FONT_BLOCK_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
FONT_BLOCK_TAG   = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
FONT_BLOCK_DESC  = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
FONT_BUS_LABEL   = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)

# Paleta Dark Tech Elegante
C_BG            = (10, 15, 29)        # Fondo azul noche #0a0f1d
C_GRID          = (20, 30, 52)        # Puntos de retícula
C_CARD_BG       = (15, 23, 42)        # Slate 900
C_CARD_BORDER   = (51, 65, 85)        # Slate 700

# Colores de acento por categoría
C_CTRL_MASTER   = (14, 165, 233)      # Sky Blue (ESP32-S3)
C_CTRL_SLAVE    = (168, 85, 247)      # Purple (Arduino Nano)
C_POWER_AC      = (245, 158, 11)      # Amber (ZCS Térmico)
C_POWER_DC      = (139, 92, 246)      # Indigo/Violet (VCSS Fuente)
C_SENSOR_PH     = (16, 185, 129)      # Emerald (pH Pseudo-Diferencial)
C_SENSOR_TEMP   = (249, 115, 22)      # Orange (MAX6675 Termopares)
C_SENSOR_ENV    = (6, 182, 212)       # Cyan (AHT20/BMP280 Ambiental)
C_CONV_ADC      = (20, 184, 166)      # Teal (ADS1115 / MCP4725)
C_I2C           = (6, 182, 212)       # Cyan (Bus I2C)
C_HMI_SCADA     = (99, 102, 241)      # Indigo (SCADA / Web)
C_PLANT         = (59, 130, 246)      # Blue (Celda y Tinas)

def crear_diagrama():
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)

    # 1. Retícula de fondo
    for x in range(0, W, 40):
        for y in range(0, H, 40):
            draw.point((x, y), fill=C_GRID)

    # 2. Encabezado Maestro
    draw.rectangle([0, 0, W, 130], fill=(7, 12, 24))
    draw.line([(0, 130), (W, 130)], fill=(14, 165, 233), width=4)
    draw.line([(0, 126), (W, 126)], fill=(30, 58, 138), width=1)

    draw.text((60, 32), "DIAGRAMA DE BLOQUES FUNCIONAL — ARQUITECTURA DEL SISTEMA", fill=(255, 255, 255), font=FONT_TITLE_MAIN)
    draw.text((60, 82), "Sistema Automatizado de Electrodeposición y Galvanoplastia • Control In-Operando (SMEQ 2026)", fill=(14, 165, 233), font=FONT_SUB_MAIN)

    # Badges en el banner superior
    badges = [
        ("ESP32-S3 DUAL-CORE", C_CTRL_MASTER),
        ("DUAL ZCS (AC / DC)", C_POWER_AC),
        ("pH PSEUDO-DIFERENCIAL", C_SENSOR_PH),
        ("VCSS 0-7A PULSADO", C_POWER_DC),
        ("SUPERVISIÓN ISA-88", C_HMI_SCADA)
    ]
    bx = 1450
    for text, color in badges:
        tw = int(draw.textlength(text, font=FONT_BLOCK_TAG)) + 24
        draw.rounded_rectangle([bx, 48, bx + tw, 86], radius=6, fill=(15, 23, 42), outline=color, width=2)
        draw.text((bx + 12, 57), text, fill=color, font=FONT_BLOCK_TAG)
        bx += tw + 14

    # Función auxiliar para dibujar un bloque "Nombre + Función"
    def draw_block(x, y, w, h, title, tag, desc_lines, accent_color, icon=""):
        # Fondo y borde
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=C_CARD_BG, outline=C_CARD_BORDER, width=2)
        
        # Barra de acento superior
        draw.rounded_rectangle([x + 2, y + 2, x + w - 2, y + 10], radius=4, fill=accent_color)
        
        # Etiqueta / Tag categoría (Esquina superior derecha)
        tag_text = tag.upper()
        tw = int(draw.textlength(tag_text, font=FONT_BLOCK_TAG)) + 16
        draw.rounded_rectangle([x + w - tw - 16, y + 18, x + w - 16, y + 42], radius=4, fill=(10, 15, 29), outline=accent_color, width=1)
        draw.text((x + w - tw - 8, y + 23), tag_text, fill=accent_color, font=FONT_BLOCK_TAG)

        # Título principal
        full_title = f"{icon} {title}".strip()
        draw.text((x + 20, y + 22), full_title, fill=(255, 255, 255), font=FONT_BLOCK_TITLE)

        # Línea separadora sutil
        draw.line([(x + 20, y + 56), (x + w - 20, y + 56)], fill=(30, 41, 59), width=1)

        # Líneas de descripción (Función del bloque)
        dy = y + 68
        for line in desc_lines:
            draw.text((x + 20, dy), line, fill=(226, 232, 240), font=FONT_BLOCK_DESC)
            dy += 26

    # =========================================================================
    # COLUMNA 1: SENSORES E INSTRUMENTACIÓN (Izquierda, X: 60 - 640)
    # =========================================================================
    # Rótulo de Columna
    draw.text((60, 160), "1. INSTRUMENTACIÓN & SENSADO", fill=C_SENSOR_PH, font=FONT_SECTION)

    # 1.1 Sensor de pH Pseudo-Diferencial
    draw_block(
        60, 200, 580, 175,
        "Sensor de pH Pseudo-Diferencial", "Sensado Analógico",
        [
            "Función: Medición de pH inmune al ruido galvánico.",
            "Estrategia: Resta diferencial de potenciales (Po -> A1, AGND -> A0)",
            "para rechazar corrientes parásitas de la electrólisis."
        ],
        C_SENSOR_PH, "🧪"
    )

    # 1.2 Termopares K + MAX6675
    draw_block(
        60, 405, 580, 165,
        "Termopares Tipo K (MAX6675)", "Sensado Térmico",
        [
            "Función: Monitoreo digital de temperatura en las 4 tinas.",
            "Estrategia: Conversor SPI con compensación de unión fría,",
            "rango 0 a 1024 °C con resolución de 0.25 °C."
        ],
        C_SENSOR_TEMP, "🌡️"
    )

    # 1.3 Sensor Ambiental AHT20 + BMP280
    draw_block(
        60, 600, 580, 165,
        "Sensor Ambiental (AHT20 / BMP280)", "Variables de Entorno",
        [
            "Función: Monitoreo de condiciones ambientales de sala.",
            "Estrategia: Adquisición por bus I2C de temperatura ambiente,",
            "humedad relativa y presión barométrica en tiempo real."
        ],
        C_SENSOR_ENV, "🌤️"
    )

    # 1.4 ADC ADS1115 (16 bits)
    draw_block(
        60, 795, 580, 165,
        "ADC de Precisión (ADS1115)", "Conversión Analógica",
        [
            "Función: Digitalización de alta resolución (16 bits) con PGA.",
            "Estrategia: Muestreo diferencial de la sonda de pH y",
            "telemetría de tensión analógica por bus I2C a 400 kHz."
        ],
        C_CONV_ADC, "📊"
    )

    # 1.5 DAC MCP4725 (12 bits)
    draw_block(
        60, 990, 580, 165,
        "DAC de Setpoint (MCP4725)", "Comando Analógico",
        [
            "Función: Generación del voltaje de referencia para la corriente.",
            "Estrategia: Fija el setpoint del sumidero VCSS (0 - 1.0V) con",
            "resolución de 12 bits controlado por el microcontrolador."
        ],
        C_CONV_ADC, "🎯"
    )

    # =========================================================================
    # COLUMNA 2: NÚCLEO DE CONTROL Y PROCESAMIENTO (Centro, X: 760 - 1560)
    # =========================================================================
    draw.text((760, 160), "2. NÚCLEO DE CONTROL Y PROCESAMIENTO", fill=C_CTRL_MASTER, font=FONT_SECTION)

    # 2.1 ESP32-S3 Maestro
    draw_block(
        760, 200, 800, 290,
        "ESP32-S3 Dual-Core (Control Maestro)", "Master Controller",
        [
            "Función: Coordinación global, lazos de control y conectividad.",
            "• Core 0 (Comunicaciones): Servidor Web asíncrono, WebSockets telemetría,",
            "  gestión de eventos y tareas FreeRTOS de red a 240 MHz.",
            "• Core 1 (Tiempo Real): Ejecución de algoritmos PI térmicos, modulación",
            "  de pulsos VCSS (10 Hz) y máquina de estados ANSI/ISA-88.",
            "• Memoria: 512 KB SRAM + 8 MB PSRAM octal + 16 MB Flash."
        ],
        C_CTRL_MASTER, "⚡"
    )

    # 2.2 Arduino Nano Esclavo
    draw_block(
        760, 520, 800, 210,
        "Arduino Nano ATmega328P (Esclavo)", "Coprocesador E/S",
        [
            "Función: Coprocesador periférico para aislamiento de interrupciones.",
            "Estrategia: Enlace bidireccional por bus UART2 @ 9600 Baud con el ESP32,",
            "descargando al procesador principal del escaneo continuo de sensores",
            "y garantizando aislamiento galvánico de la lógica digital."
        ],
        C_CTRL_SLAVE, "🔄"
    )

    # 2.3 Máquina de Estados ISA-88 & Gestión de Recetas
    draw_block(
        760, 760, 800, 200,
        "Supervisión ISA-88 & Gestor de Ensayos", "Lógica de Control",
        [
            "Función: Ejecución segura de recetas y fases del ensayo experimental.",
            "Estrategia: Control por lotes (ANSI/ISA-88.01) con estados formales:",
            "IDLE -> RUNNING -> HOLDING -> COMPLETED y enclavamientos de seguridad",
            "ante sobretemperatura (>95 °C) o pérdida de nivel de solución."
        ],
        C_HMI_SCADA, "📋"
    )

    # 2.4 Aislamiento Galvánico & Protección
    draw_block(
        760, 990, 800, 165,
        "Barrera de Aislamiento Galvánico", "Seguridad Eléctrica",
        [
            "Función: Desacoplar las tierras de potencia, de red y de control.",
            "Estrategia: Optoacopladores rápidos (4N35, MOC3041) que evitan que",
            "transitorios de conmutación o ruidos de red afecten a los microprocesadores."
        ],
        (239, 68, 68), "🛡️"
    )

    # =========================================================================
    # COLUMNA 3: POTENCIA, ACTUACIÓN Y PLANTA FÍSICA (Derecha, X: 1680 - 2640)
    # =========================================================================
    # =========================================================================
    # COLUMNA 3: ETAPA DE POTENCIA Y PLANTA FÍSICA (Derecha, X: 1680 - 2640)
    # Subcolumna 3A (X: 1680 - 2130): Rama Térmica AC
    # Subcolumna 3B (X: 2190 - 2640): Rama Electroquímica DC (Celda Hull)
    # =========================================================================
    draw.text((1680, 160), "3A. CONTROL TÉRMICO AC (TINAS)", fill=C_POWER_AC, font=FONT_SECTION)
    draw.text((2190, 160), "3B. POTENCIA DC & CELDA HULL", fill=C_POWER_DC, font=FONT_SECTION)

    # 3.1 Módulo ZCS por Tiempo Proporcional (AC)
    draw_block(
        1680, 200, 470, 360,
        "Módulo Dual ZCS", "Actuación Térmica",
        [
            "Función: Calentamiento de tinas",
            "con cero ruido electromagnético.",
            "",
            "Estrategia: Conmutación por",
            "Tiempo Proporcional sincronizada",
            "con cruce por cero AC (60 Hz).",
            "Conmuta en V=0 eliminando EMI",
            "y protegiendo la sonda de pH."
        ],
        C_POWER_AC, "🔥"
    )

    # 3.2 Resistencias Calefactoras en Tinas (AC)
    draw_block(
        1680, 680, 470, 475,
        "Resistencias en Tinas", "Planta Térmica",
        [
            "Función: Calentamiento de baños",
            "químicos a temperatura consigna.",
            "",
            "• Tina 1: Desengrase (90 °C, 450W)",
            "• Tina 2: Decapado (90 °C, 450W)",
            "• Tina 3: Niquelado (30 °C, 450W)",
            "• Tina 4: Zincado (30 °C, 18W)",
            "",
            "Resistencias blindadas con sensor",
            "de termopar K sumergido."
        ],
        C_POWER_AC, "♨️"
    )

    # 3.3 Sumidero VCSS (DC Lineal y Pulsado 10 Hz)
    draw_block(
        2190, 200, 450, 360,
        "Sumidero VCSS (0-7A)", "Potencia DC",
        [
            "Función: Regulación de corriente",
            "catódica para electrodeposición.",
            "",
            "Estrategia: Fuente de corriente",
            "analógica con Op-Amp + MOSFET",
            "operando en modo lineal activo.",
            "Permite DC Puro y Pulsada a",
            "10 Hz (50% ciclo de trabajo)."
        ],
        C_POWER_DC, "⚡"
    )

    # 3.4 Relé de Seguridad DC
    draw_block(
        2190, 620, 450, 200,
        "Relé de Corte DC", "Seguridad Celda",
        [
            "Función: Desconexión física",
            "inmediata del circuito catódico.",
            "",
            "Estrategia: Corte en GPIO 20",
            "ante parada de emergencia, fin",
            "de tiempo o sobrecorriente."
        ],
        (244, 63, 94), "🛑"
    )

    # 3.5 Celda Hull & Electrodeposición
    draw_block(
        2190, 880, 450, 275,
        "Celda Hull (Zinc)", "Electrodeposición",
        [
            "Función: Baño galvánico de zinc",
            "sobre probeta de Al 6061-T6.",
            "",
            "• Ánodo: Placa de Zinc puro (99.9%)",
            "• Cátodo: Sustrato Al 6061-T6",
            "• Volumen: 267 mL (trapezoidal)",
            "Con pre-tratamiento en zincato."
        ],
        C_PLANT, "⚗️"
    )

    # =========================================================================
    # LÍNEAS DE CONEXIÓN Y BUSES PRINCIPALES (SIN CRUCES EXTRAÑOS)
    # =========================================================================
    # Bus I2C (Cyan): Desde Sensores a ESP32
    draw.line([(640, 875), (700, 875), (700, 360), (760, 360)], fill=C_I2C, width=4)
    draw.text((655, 850), "Bus I2C", fill=C_I2C, font=FONT_BUS_LABEL)

    # Bus SPI (Orange): Desde MAX6675 a ESP32
    draw.line([(640, 485), (730, 485), (730, 400), (760, 400)], fill=C_SENSOR_TEMP, width=4)
    draw.text((655, 460), "Bus SPI", fill=C_SENSOR_TEMP, font=FONT_BUS_LABEL)

    # Enlace UART2 (Magenta): Entre ESP32 y Arduino Nano
    draw.line([(1160, 490), (1160, 520)], fill=(236, 72, 153), width=5)
    draw.text((1175, 495), "UART2 (9600 Baud)", fill=(236, 72, 153), font=FONT_BUS_LABEL)

    # Señal de Disparo ZCS (Amber): Desde ESP32 hacia Módulo ZCS
    draw.line([(1560, 300), (1680, 300)], fill=C_POWER_AC, width=4)
    draw.text((1570, 275), "Pulsos ZCS", fill=C_POWER_AC, font=FONT_BUS_LABEL)

    # Señal de Potencia AC (Amber): Desde Módulo ZCS hacia Resistencias Calefactoras (Baja directo)
    draw.line([(1915, 560), (1915, 680)], fill=C_POWER_AC, width=5)
    # Flecha hacia abajo
    draw.polygon([(1915, 680), (1907, 665), (1923, 665)], fill=C_POWER_AC)
    draw.text((1930, 610), "Potencia AC 60 Hz", fill=C_POWER_AC, font=FONT_BUS_LABEL)

    # Señal de Comando VCSS (Purple): Desde ESP32 hacia Sumidero VCSS
    draw.line([(1560, 420), (2190, 420)], fill=C_POWER_DC, width=4)
    draw.text((1600, 395), "Setpoint VCSS (DAC)", fill=C_POWER_DC, font=FONT_BUS_LABEL)

    # Señal de Corriente DC (Purple): Desde VCSS baja hacia el Relé DC
    draw.line([(2415, 560), (2415, 620)], fill=C_POWER_DC, width=5)
    draw.polygon([(2415, 620), (2407, 605), (2423, 605)], fill=C_POWER_DC)
    draw.text((2430, 580), "Línea DC", fill=C_POWER_DC, font=FONT_BUS_LABEL)

    # Señal de Corriente DC (Purple): Desde Relé DC baja hacia Celda Hull
    draw.line([(2415, 820), (2415, 880)], fill=C_POWER_DC, width=5)
    draw.polygon([(2415, 880), (2407, 865), (2423, 865)], fill=C_POWER_DC)
    draw.text((2430, 840), "Corriente 0-7A", fill=C_POWER_DC, font=FONT_BUS_LABEL)

    # Conexión SCADA a ESP32 (Vertical)
    draw.line([(1160, 1200), (1160, 1245)], fill=C_HMI_SCADA, width=4)

    # 4. Pie de página institucional con Responsables del Proyecto
    draw.line([(60, 1610), (W - 60, 1610)], fill=C_CARD_BORDER, width=1)
    draw.text((60, 1622), "Tesista: V. U. Gutiérrez Ramírez   |   Directores de Tesis: Dr. O. A. González-Meza & Dr. N. Casillas Santana", fill=(241, 245, 249), font=FONT_BLOCK_DESC)
    draw.text((60, 1652), "Desarrollo Hardware, Firmware & Software: S. Castro Pérez & F. S. Samayoa Martínez   |   UdeG (CUCEI) & Volta Plating Solutions", fill=(148, 163, 184), font=FONT_BLOCK_TAG)
    draw.text((W - 440, 1632), "SMEQ 2026 • CARTEL CTS-C51", fill=C_CTRL_MASTER, font=FONT_SECTION)

    # Rutas oficiales a actualizar
    rutas_salida = [
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema.png",
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema_moderno.png",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema.png",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema_moderno.png",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema.png",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema_moderno.png",
        r"C:\Proyecto\Proyecto\documentos\academicos\showcase_web\assets\sistema.png"
    ]

    for ruta in rutas_salida:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        img.save(ruta, "PNG", dpi=(300, 300))
        print(f"[OK] Diagrama guardado en: {ruta}")

    return rutas_salida[0]

if __name__ == "__main__":
    crear_diagrama()

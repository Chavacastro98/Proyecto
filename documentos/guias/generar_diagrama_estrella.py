#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del Diagrama de Bloques Funcional en Topología Radial / Estrella Literal
Planta Piloto de Electrodeposición y Galvanoplastia (SMEQ 2026 - CTS-C51)

Arquitectura Física Literal:
- CENTRO: ESP32-S3 Maestro (Dual-Core @ 240 MHz, RTOS 2.0)
- ARRIBA: HMI & Supervisión (SCADA PyQt6 / WebSockets Wi-Fi)
- DERECHA (Bus I2C común en paralelo):
    -> ADS1115 (ADC 16-bit) -> pH Pseudo-Diferencial (A1-A0) & Sensado Voltaje Celda (A2-A3)
    -> MCP4725 (DAC 12-bit) -> Sumidero VCSS (0-7A) -> Relé Corte DC (GPIO 20) -> Celda Hull
    -> Display OLED 0.96" & Sensores Ambientales (AHT20/BMP280)
- IZQUIERDA (Bus SPI @ 4 MHz):
    -> Módulos MAX6675 -> 4 Termopares Tipo K sumergidos en Tinas 1, 2, 3 y 4
- ABAJO (Bus UART2 @ 9600 Baud):
    -> Arduino Nano Esclavo -> Disparo a Módulo TRIACs BTA24 (4 Canales AC) con ZCS 60Hz 4N35
       -> Resistencias Calefactoras en Tinas (T1, T2, T3, T4)
"""

import os
from PIL import Image, ImageDraw, ImageFont

W = 2700
H = 1750

# Fuentes TrueType
FONT_TITLE_MAIN = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
FONT_SUB_MAIN   = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
FONT_SECTION    = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 19)

FONT_BLOCK_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
FONT_BLOCK_TAG   = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
FONT_BLOCK_DESC  = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 15)
FONT_BUS_LABEL   = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 16)
FONT_CREDITS     = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 15)

# Paleta Dark Industrial de Alto Contraste
C_BG            = (10, 15, 29)        # Azul noche #0a0f1d
C_GRID          = (20, 30, 52)        # Retícula
C_CARD_BG       = (15, 23, 42)        # Slate 900
C_CARD_BORDER   = (51, 65, 85)        # Slate 700

# Colores de buses y señales
C_ESP32         = (14, 165, 233)      # Sky Blue (ESP32-S3 Maestro)
C_NANO          = (168, 85, 247)      # Purple (Arduino Nano Esclavo)
C_I2C           = (6, 182, 212)       # Cyan (Bus I2C)
C_SPI           = (249, 115, 22)      # Orange (Bus SPI)
C_UART          = (236, 72, 153)      # Pink/Magenta (Bus UART2)
C_POWER_AC      = (245, 158, 11)      # Amber (ZCS Térmico AC)
C_POWER_DC      = (139, 92, 246)      # Violet (VCSS Fuente DC)
C_PH_DIFF       = (16, 185, 129)      # Emerald (pH Pseudo-Diferencial)
C_ENV           = (45, 212, 191)      # Teal (Ambiental / OLED)
C_HMI           = (99, 102, 241)      # Indigo (SCADA)
C_PLANT         = (59, 130, 246)      # Blue (Celda y Tinas)

def crear_diagrama():
    img = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)

    # 1. Retícula de fondo
    for x in range(0, W, 40):
        for y in range(0, H, 40):
            draw.point((x, y), fill=C_GRID)

    # 2. Encabezado Maestro
    draw.rectangle([0, 0, W, 125], fill=(7, 12, 24))
    draw.line([(0, 125), (W, 125)], fill=C_ESP32, width=4)

    draw.text((60, 28), "ARQUITECTURA DE HARDWARE LITERAL — TOPOLOGÍA CENTRALIZADA (EN ESTRELLA)", fill=(255, 255, 255), font=FONT_TITLE_MAIN)
    draw.text((60, 78), "ESP32-S3 Maestro Central con Buses Dedicados I2C, SPI y UART hacia Periferia y Potencia (SMEQ 2026)", fill=C_ESP32, font=FONT_SUB_MAIN)

    # Badges en el banner superior
    badges = [
        ("NÚCLEO CENTRAL ESP32-S3", C_ESP32),
        ("BUS I2C PARALELO", C_I2C),
        ("BUS SPI TÉRMICO", C_SPI),
        ("ENLACE UART ESCLAVO", C_UART),
        ("DUAL ZCS AC/DC", C_POWER_AC)
    ]
    bx = 1420
    for text, color in badges:
        tw = int(draw.textlength(text, font=FONT_BLOCK_TAG)) + 22
        draw.rounded_rectangle([bx, 44, bx + tw, 82], radius=6, fill=(15, 23, 42), outline=color, width=2)
        draw.text((bx + 11, 53), text, fill=color, font=FONT_BLOCK_TAG)
        bx += tw + 12

    # Función auxiliar para dibujar bloques
    def draw_block(x, y, w, h, title, tag, desc_lines, accent_color, icon=""):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=C_CARD_BG, outline=C_CARD_BORDER, width=2)
        draw.rounded_rectangle([x + 2, y + 2, x + w - 2, y + 8], radius=3, fill=accent_color)
        
        tag_text = tag.upper()
        tw = int(draw.textlength(tag_text, font=FONT_BLOCK_TAG)) + 14
        draw.rounded_rectangle([x + w - tw - 12, y + 14, x + w - 12, y + 36], radius=4, fill=(10, 15, 29), outline=accent_color, width=1)
        draw.text((x + w - tw - 5, y + 18), tag_text, fill=accent_color, font=FONT_BLOCK_TAG)

        full_title = f"{icon} {title}".strip()
        draw.text((x + 16, y + 16), full_title, fill=(255, 255, 255), font=FONT_BLOCK_TITLE)
        draw.line([(x + 16, y + 46), (x + w - 16, y + 46)], fill=(30, 41, 59), width=1)

        dy = y + 54
        for line in desc_lines:
            draw.text((x + 16, dy), line, fill=(226, 232, 240), font=FONT_BLOCK_DESC)
            dy += 22

    # =========================================================================
    # CENTRO: MICROCONTROLADOR MAESTRO (ESP32-S3 DUAL-CORE)
    # Coordenadas: X: 1040 a 1660 (w=620), Y: 560 a 980 (h=420)
    # =========================================================================
    draw_block(
        1040, 560, 620, 420,
        "ESP32-S3 (Control Maestro)", "Master Controller",
        [
            "Función: Cerebro central, lazos de control y telemetría.",
            "",
            "• Core 0 (Comunicaciones): Servidor Web asíncrono,",
            "  WebSockets telemetría a 60 FPS y stack Wi-Fi.",
            "• Core 1 (Tiempo Real): Lazos PI térmicos, cálculo",
            "  de pulsos a 10 Hz y máquina de estados ANSI/ISA-88.",
            "• Puertos de Conexión Física:",
            "  - Bus I2C (SDA/SCL a 400 kHz) hacia ADC, DAC y Sensores.",
            "  - Bus SPI (SCK/MISO/CS0-3) hacia 4 x MAX6675.",
            "  - Bus UART2 (TX/RX @ 9600 Baud) hacia Arduino Nano.",
            "  - GPIO 20: Control directo de Relé de Seguridad DC."
        ],
        C_ESP32, "🧠"
    )

    # =========================================================================
    # ARRIBA: HMI & SUPERVISIÓN (SCADA PyQt6 & Servidor Web Wi-Fi)
    # =========================================================================
    draw_block(
        1040, 160, 620, 260,
        "Supervisión & Telemetría Externa", "HMI & SCADA",
        [
            "Función: Interfaz con el operador y registro científico.",
            "",
            "• Estación SCADA (PC / PyQt6): Enlace USB/Serial y Wi-Fi,",
            "  cálculo culombimétrico de Faraday y guardado CSV.",
            "• Servidor Web Móvil: Panel de control autónomo accesible",
            "  desde celulares sin instalar software.",
            "• Display OLED 0.96\" (I2C): Despliegue de variables in-situ."
        ],
        C_HMI, "💻"
    )
    # Conexión vertical entre SCADA y ESP32
    draw.line([(1350, 420), (1350, 560)], fill=C_HMI, width=5)
    draw.polygon([(1350, 560), (1342, 545), (1358, 545)], fill=C_HMI)
    draw.polygon([(1350, 420), (1342, 435), (1358, 435)], fill=C_HMI)
    draw.text((1365, 480), "Wi-Fi / USB Serial", fill=C_HMI, font=FONT_BUS_LABEL)

    # =========================================================================
    # IZQUIERDA: BUS SPI -> TERMOPARES MAX6675 -> 4 TINAS
    # =========================================================================
    draw.text((80, 160), "RAMA IZQUIERDA: BUS SPI (MONITOREO TÉRMICO)", fill=C_SPI, font=FONT_SECTION)

    # Bloque MAX6675
    draw_block(
        80, 220, 720, 260,
        "4 x Conversores MAX6675", "Bus SPI @ 4 MHz",
        [
            "Función: Digitalización de temperatura por termopares K.",
            "",
            "Estrategia: Comunicación SPI compartida (SCK, MISO) con",
            "4 líneas Chip Select (CS_T1, CS_T2, CS_T3, CS_T4).",
            "Resolución de 0.25 °C con compensación de unión fría",
            "integrada en cada canal para monitoreo continuo de baños."
        ],
        C_SPI, "🌡️"
    )

    # Bloque Tinas Térmicas
    draw_block(
        80, 580, 720, 360,
        "Planta Térmica: 4 Tinas de Baño", "Proceso de Tratamiento",
        [
            "Función: Baños químicos calefaccionados con termopar sumergido.",
            "",
            "• Tina 1 (Desengrase Alcalino): 90.0 °C  |  Vol: 1.0 L, 450 W",
            "• Tina 2 (Decapado Ácido):     90.0 °C  |  Vol: 1.0 L, 450 W",
            "• Tina 3 (Niquelado Químico):  30.0 °C  |  Vol: 1.0 L, 450 W",
            "• Tina 4 (Zincado Celda Hull): 30.0 °C  |  Vol: 0.267 L, 18 W",
            "",
            "Cada tina cuenta con termopar K blindado y resistencia blindada."
        ],
        C_PLANT, "♨️"
    )

    # Conexión SPI: Desde ESP32 hacia MAX6675
    draw.line([(1040, 680), (880, 680), (880, 350), (800, 350)], fill=C_SPI, width=5)
    draw.polygon([(800, 350), (815, 342), (815, 358)], fill=C_SPI)
    draw.text((895, 480), "Bus SPI (4 MHz)", fill=C_SPI, font=FONT_BUS_LABEL)

    # Conexión Termopares: Desde Tinas hacia MAX6675
    draw.line([(440, 580), (440, 480)], fill=C_SPI, width=4)
    draw.polygon([(440, 480), (432, 495), (448, 495)], fill=C_SPI)
    draw.text((455, 525), "Cables Termopar K", fill=C_SPI, font=FONT_BUS_LABEL)

    # =========================================================================
    # ABAJO: BUS UART2 -> ARDUINO NANO -> MÓDULO TRIACs -> RESISTENCIAS
    # =========================================================================
    draw.text((80, 1030), "RAMA INFERIOR: BUS UART (DISPARO DE TRIACs Y POTENCIA AC)", fill=C_UART, font=FONT_SECTION)

    # Arduino Nano
    draw_block(
        1040, 1070, 620, 230,
        "Arduino Nano (Coprocesador Esclavo)", "Enlace UART2",
        [
            "Función: Control dedicado de disparo de TRIACs y ZCS.",
            "",
            "Estrategia: Recibe porcentajes de potencia (0-100%) por UART",
            "desde el ESP32. Sincronizado a interrupción externa INT1 (Pin 3)",
            "desde el 4N35 para disparo en cruce por cero AC a 60 Hz.",
            "Watchdog de 2 segundos apaga todo si pierde comunicación."
        ],
        C_NANO, "🔄"
    )

    # Módulo TRIACs (MDAC4C)
    draw_block(
        80, 1100, 720, 260,
        "Módulo TRIACs (MDAC4C - 4 Canales AC)", "Potencia AC 60 Hz",
        [
            "Función: Conmutación de potencia AC de calentamiento.",
            "",
            "Estrategia: 4 canales con optoacopladores MOC3021 y TRIACs BTA24.",
            "Modula en cruce por cero (V=0) por Tiempo Proporcional (Burst Firing)",
            "eliminando por completo armónicos EMI sobre la sonda de pH.",
            "Detector de cruce por cero AC 4N35 integrado en placa."
        ],
        C_POWER_AC, "🔥"
    )

    # Conexión UART: Desde ESP32 hacia Nano
    draw.line([(1350, 980), (1350, 1070)], fill=C_UART, width=5)
    draw.polygon([(1350, 1070), (1342, 1055), (1358, 1055)], fill=C_UART)
    draw.text((1365, 1018), "UART2 (9600 Baud)", fill=C_UART, font=FONT_BUS_LABEL)

    # Conexión Disparos: Desde Nano hacia Módulo TRIACs
    draw.line([(1040, 1200), (800, 1200)], fill=C_POWER_AC, width=4)
    draw.polygon([(800, 1200), (815, 1192), (815, 1208)], fill=C_POWER_AC)
    draw.text((825, 1175), "Pines Gate 7,8,9,10 + ZC Pin 3", fill=C_POWER_AC, font=FONT_BUS_LABEL)

    # Conexión Potencia AC: Desde TRIACs hacia las Resistencias de las Tinas
    draw.line([(440, 1100), (440, 940)], fill=C_POWER_AC, width=5)
    draw.polygon([(440, 940), (432, 955), (448, 955)], fill=C_POWER_AC)
    draw.text((455, 1010), "Potencia AC (Calentamiento)", fill=C_POWER_AC, font=FONT_BUS_LABEL)

    # =========================================================================
    # DERECHA: BUS I2C EN PARALELO -> ADS1115 & MCP4725 -> VCSS & CELDA
    # =========================================================================
    draw.text((1760, 160), "RAMA DERECHA: BUS I2C (SENSADO & CONTROL DE CORRIENTE)", fill=C_I2C, font=FONT_SECTION)

    # Troncal I2C desde ESP32
    draw.line([(1660, 680), (1780, 680)], fill=C_I2C, width=5)
    draw.text((1675, 655), "Bus I2C (400 kHz)", fill=C_I2C, font=FONT_BUS_LABEL)

    # Distribución I2C vertical hacia sub-nodos
    draw.line([(1780, 240), (1780, 1150)], fill=C_I2C, width=5)

    # Nodo 1 (Arriba): Pantalla OLED & AHT20/BMP280
    draw.line([(1780, 240), (1850, 240)], fill=C_I2C, width=4)
    draw.polygon([(1850, 240), (1835, 232), (1835, 248)], fill=C_I2C)

    draw_block(
        1850, 170, 780, 150,
        "OLED 0.96\" & Ambiental AHT20/BMP280", "I2C Periféricos",
        [
            "Función: Despliegue local y monitoreo ambiental (Temp, Humedad, Presión).",
            "Conectados en paralelo al bus I2C común (SDA: GPIO 8, SCL: GPIO 9)."
        ],
        C_ENV, "🌤️"
    )

    # Nodo 2 (Centro-Arriba): ADS1115 (ADC 16-bit) -> pH y Sensado Voltaje
    draw.line([(1780, 430), (1850, 430)], fill=C_I2C, width=4)
    draw.polygon([(1850, 430), (1835, 422), (1835, 438)], fill=C_I2C)

    draw_block(
        1850, 345, 780, 310,
        "ADC ADS1115 (16 bits con PGA)", "I2C Dirección 0x48",
        [
            "Función: Conversión analógica diferencial de alta precisión a 860 SPS.",
            "",
            "• Canal A1 - A0 (Pseudo-Diferencial):",
            "  - A1: Tensión acondicionada de la sonda de vidrio de pH (Po).",
            "  - A0: Tierra local analógica aislada (AGND / Kelvin Ground).",
            "  - Resta DeltaV = A1 - A0 rechaza ruidos galvánicos de la celda (CMRR > 75dB).",
            "• Canales A2 / A3:",
            "  - Monitoreo de tensión analógica en bornes de la celda galvánica."
        ],
        C_PH_DIFF, "🧪"
    )

    # Nodo 3 (Centro-Abajo): MCP4725 (DAC 12-bit) -> Sumidero VCSS
    draw.line([(1780, 770), (1850, 770)], fill=C_I2C, width=4)
    draw.polygon([(1850, 770), (1835, 762), (1835, 778)], fill=C_I2C)

    draw_block(
        1850, 680, 780, 230,
        "DAC MCP4725 (12 bits) & Sumidero VCSS", "I2C Dirección 0x60",
        [
            "Función: Generación y regulación precisa de la corriente catódica.",
            "",
            "• MCP4725: Fija tensión de consigna analógica V_ref (0 a 3.53 V).",
            "• Sumidero VCSS: Op-Amp como amplificador de error (V_ref = Id · Rs)",
            "  pilotando 2 ramas MOSFET con shunts cerámicos de 1 Ω / 10W (Rs,eq = 0.5 Ω).",
            "  Ganancia de transconductancia Gm = 2 A/V (salida regulada 0 a 7.0 A DC / 10 Hz)."
        ],
        C_POWER_DC, "⚡"
    )

    # Nodo 4 (Abajo): Relé de Corte DC -> Celda Hull (Electrodeposición)
    draw_block(
        1850, 940, 780, 260,
        "Relé DC & Celda Hull (Proceso Galvánico)", "Potencia DC & Celda",
        [
            "Función: Desconexión de seguridad y electrodeposición de zinc.",
            "",
            "• Relé de Corte DC: Gobernado directamente por GPIO 20 del ESP32",
            "  para corte físico instantáneo sin arco al finalizar ensayo o alarma.",
            "• Celda Hull (Zincado Ácido): Prisma trapezoidal (267 mL),",
            "  ánodo de Zinc puro y cátodo de probeta Al 6061-T6 con zincato previo."
        ],
        (244, 63, 94), "🛑"
    )

    # Conexión VCSS hacia Relé y Celda
    draw.line([(2240, 910), (2240, 940)], fill=C_POWER_DC, width=5)
    draw.polygon([(2240, 940), (2232, 925), (2248, 925)], fill=C_POWER_DC)
    draw.text((2255, 922), "Corriente Catódica Regulada", fill=C_POWER_DC, font=FONT_BUS_LABEL)

    # Conexión Sonda de pH hacia Celda Hull
    draw.line([(2550, 655), (2550, 940)], fill=C_PH_DIFF, width=4)
    draw.polygon([(2550, 655), (2542, 670), (2558, 670)], fill=C_PH_DIFF)
    draw.text((2565, 800), "Sonda pH en Baño", fill=C_PH_DIFF, font=FONT_BUS_LABEL)

    # =========================================================================
    # PIE DE PÁGINA: AUTORES, DIRECTORES Y CRÉDITOS INSTITUCIONALES
    # =========================================================================
    draw.line([(60, 1640), (W - 60, 1640)], fill=C_CARD_BORDER, width=1)
    draw.text(
        (60, 1655),
        "Investigación Electroquímica: V. U. Gutiérrez Ramírez (Problemática Volta Plating)   |   Asesores: Dr. O. A. González-Meza & Dr. N. Casillas",
        fill=(241, 245, 249),
        font=FONT_BLOCK_DESC
    )
    draw.text(
        (60, 1685),
        "Plataforma de Ensayos, Firmware & SCADA: Salvador² C Dev Team (S. Castro Pérez & F. S. Samayoa Martínez)   |   CUCEI - UdeG",
        fill=(148, 163, 184),
        font=FONT_BLOCK_TAG
    )
    draw.text(
        (W - 440, 1665),
        "SMEQ 2026 • CARTEL CTS-C51",
        fill=C_ESP32,
        font=FONT_SECTION
    )

    # Guardar en todas las rutas oficiales
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
        print(f"[OK] Diagrama Estrella guardado en: {ruta}")

    return rutas_salida[0]

if __name__ == "__main__":
    crear_diagrama()

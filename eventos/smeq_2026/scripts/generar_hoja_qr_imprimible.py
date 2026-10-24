#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Hoja Imprimible de Código QR Suelto en Hoja Blanca (SMEQ 2026).
Produce un documento PDF tamaño Carta (8.5 x 11 in) con diseño académico formal,
código QR de 300 DPI centrado y guía técnica para evaluadores y asistentes.
"""

import os
import qrcode
from PIL import Image
import pymupdf

BASE_DIR = r"C:\Proyecto\Proyecto\documentos\academicos"
URL_DESTINO = "https://chavacastro98.github.io/Proyecto/"
PDF_SALIDA = os.path.join(BASE_DIR, "HOJA_QR_MESA_SMEQ2026.pdf")
QR_TEMP_PNG = os.path.join(BASE_DIR, "qr_temp_hoja.png")

def generar_qr_png():
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% redundancia
        box_size=20,
        border=2,
    )
    qr.add_data(URL_DESTINO)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0b1120", back_color="#ffffff").convert("RGB")
    img.save(QR_TEMP_PNG, "PNG", dpi=(300, 300))
    return QR_TEMP_PNG

def generar_pdf_hoja_imprimible():
    qr_img = generar_qr_png()

    # Tamaño Carta estándar: 612 x 792 pt
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)

    # Colores
    c_primary = (14/255, 165/255, 233/255)     # #0ea5e9
    c_dark = (11/255, 17/255, 32/255)          # #0b1120
    c_text = (30/255, 41/255, 59/255)          # #1e293b
    c_muted = (100/255, 116/255, 139/255)      # #64748b
    c_card_bg = (248/255, 250/255, 252/255)    # #f8fafc
    c_border = (226/255, 232/255, 240/255)     # #e2e8f0

    # 1. Marco decorativo de página
    page.draw_rect(pymupdf.Rect(24, 24, 588, 768), color=c_border, width=1.5)
    page.draw_rect(pymupdf.Rect(28, 28, 584, 764), color=c_border, width=0.5)

    # 2. Barra de encabezado
    page.draw_rect(pymupdf.Rect(28, 28, 584, 85), fill=c_dark)
    page.insert_textbox(pymupdf.Rect(35, 40, 577, 56), "XLI CONGRESO NACIONAL DE LA SOCIEDAD MEXICANA DE ELECTROQUÍMICA", 
                         fontsize=10.5, fontname="helv", color=(1, 1, 1), align=pymupdf.TEXT_ALIGN_CENTER)
    page.insert_textbox(pymupdf.Rect(35, 58, 577, 74), "SMEQ 2026  •  SESIÓN DE CARTELES  •  CÓDIGO: CTS-C51", 
                         fontsize=9, fontname="helv", color=c_primary, align=pymupdf.TEXT_ALIGN_CENTER)

    # 3. Título del Proyecto
    y = 105
    page.insert_textbox(
        pymupdf.Rect(45, y, 567, y + 48),
        "Optimización Electroquímica de Recubrimientos de Zinc sobre Aluminio 6061 T-6\nmediante Diseño de Experimentos y Control In-Operando",
        fontsize=13,
        fontname="helv",
        color=c_dark,
        align=pymupdf.TEXT_ALIGN_CENTER
    )

    y += 50
    page.insert_textbox(pymupdf.Rect(45, y, 567, y + 20), "Universidad de Guadalajara — CUCEI  |  Volta Plating Solutions",
                         fontsize=9.5, fontname="helv", color=c_muted, align=pymupdf.TEXT_ALIGN_CENTER)

    # 4. Cuadro del Código QR
    y += 20
    qr_box = pymupdf.Rect(186, y, 426, y + 240)
    page.draw_rect(qr_box, color=c_primary, fill=(1, 1, 1), width=1.5)
    
    # Insertar QR dentro del cuadro (216 x 216 pt)
    qr_inner = pymupdf.Rect(198, y + 12, 414, y + 228)
    page.insert_image(qr_inner, filename=qr_img)

    y += 248
    page.insert_textbox(pymupdf.Rect(45, y, 567, y + 16), "ESCANEE PARA ABRIR LA DEMOSTRACIÓN TÉCNICA EN VIVO",
                         fontsize=10, fontname="helv", color=c_primary, align=pymupdf.TEXT_ALIGN_CENTER)
    y += 18
    page.insert_textbox(pymupdf.Rect(45, y, 567, y + 16), URL_DESTINO,
                         fontsize=9.5, fontname="courier", color=c_dark, align=pymupdf.TEXT_ALIGN_CENTER)

    # 5. Caja explicativa de contenidos técnicos disponibles
    y += 24
    content_box = pymupdf.Rect(45, y, 567, y + 205)
    page.draw_rect(content_box, fill=c_card_bg, color=c_border, width=1)

    y_t = y + 14
    page.insert_text(pymupdf.Point(58, y_t), "CONTENIDOS Y SIMULADORES INTERACTIVOS DISPONIBLES EN EL PORTAL:",
                     fontsize=9, fontname="helv", color=c_dark)

    bullets = [
        ("• Diagrama de Bloques en Ultra HD:", "Arquitectura Dual-Core ESP32-S3 (240 MHz), bus I2C (400 kHz), SPI y aislamiento óptico."),
        ("• Control Térmico ZCS (Burst Firing):", "Fundamentación de conmutación en cruce por cero vs. ángulo de fase y modelo MATLAB."),
        ("• Calculadora Analítica VCSS (MOSFET):", "Punto de operación en modo activo lineal, disipación de potencia y límites de SOA térmica."),
        ("• Sensado Pseudo-Diferencial de pH:", "Ecuación de Nernst con compensación de temperatura y eliminación de bucles galvánicos (Po-AGND)."),
        ("• Suite SCADA PyQt6 & Supervisión ISA-88:", "Telemetría in-operando en tiempo real, metrología de pulsos a 10 Hz y culombimetría de Faraday."),
        ("• Matriz Experimental DOE 2^5 · 4:", "Explorador interactivo de los 128 ensayos factoriales y galería fotográfica de la planta física.")
    ]

    for title, desc in bullets:
        y_t += 18
        page.insert_text(pymupdf.Point(60, y_t), title, fontsize=8, fontname="helv", color=c_dark)
        page.insert_text(pymupdf.Point(236, y_t), desc, fontsize=7.5, fontname="helv", color=c_muted)

    # 6. Pie de página institucional y Créditos del Equipo de Trabajo
    y_foot = 730
    page.draw_line(pymupdf.Point(45, y_foot), pymupdf.Point(567, y_foot), color=c_border, width=0.8)
    page.insert_textbox(pymupdf.Rect(45, y_foot + 4, 567, y_foot + 18), 
                         "Tesista: V. U. Gutiérrez Ramírez (Tesis y Resultados)   |   Asesores: Dr. O. A. González-Meza & Dr. N. Casillas Santana (Línea Electroquímica UdeG)",
                         fontsize=7.4, fontname="helv", color=c_dark, align=pymupdf.TEXT_ALIGN_CENTER)
    page.insert_textbox(pymupdf.Rect(45, y_foot + 18, 567, y_foot + 32), 
                         "Instrumentación y Control (Hardware, Firmware, Térmico, SCADA): S. Castro Pérez & F. S. Samayoa Martínez",
                         fontsize=7.1, fontname="helv", color=c_muted, align=pymupdf.TEXT_ALIGN_CENTER)
    page.insert_textbox(pymupdf.Rect(45, y_foot + 32, 567, y_foot + 46), 
                         "UdeG (CUCEI) & Volta Plating • Contacto Técnico: salvadorcastroperez@hotmail.com | fernando.samayoa@alumnos.udg.mx",
                         fontsize=6.8, fontname="helv", color=c_primary, align=pymupdf.TEXT_ALIGN_CENTER)

    doc.save(PDF_SALIDA)
    doc.close()

    if os.path.exists(QR_TEMP_PNG):
        os.remove(QR_TEMP_PNG)

    print(f"[OK] Hoja imprimible generada en: {PDF_SALIDA}")

if __name__ == "__main__":
    generar_pdf_hoja_imprimible()

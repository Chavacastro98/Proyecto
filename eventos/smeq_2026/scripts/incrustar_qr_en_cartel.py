#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar el código QR de alta resolución e incrustarlo automáticamente
en el cartel académico DOC-20261004-WA0001.pdf (XLI Congreso Nacional SMEQ 2026).
"""

import os
import sys
import argparse
import qrcode
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

DEFAULT_URL = "https://chavacastro98.github.io/Proyecto/"
BASE_DIR = r"C:\Proyecto\Proyecto\documentos\academicos"
PDF_INPUT = os.path.join(BASE_DIR, "DOC-20261004-WA0001.pdf")
PDF_OUTPUT = os.path.join(BASE_DIR, "DOC-20261004-WA0001_con_QR.pdf")
QR_PNG_OUTPUT = os.path.join(BASE_DIR, "codigo_qr_cartel.png")
PREVIEW_OUTPUT = os.path.join(BASE_DIR, "cartel_con_qr_preview.png")

def generar_codigo_qr(url_destino, output_path):
    """Genera código QR de alta resolución con margen y diseño nítido."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta corrección (30% redundancia)
        box_size=20,
        border=3,
    )
    qr.add_data(url_destino)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="#0b1120", back_color="#ffffff").convert("RGBA")
    
    # Agregar marco estilizado y leyenda
    w, h = img_qr.size
    canvas_h = h + 120
    canvas = Image.new("RGBA", (w, canvas_h), (255, 255, 255, 255))
    canvas.paste(img_qr, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    try:
        font_txt = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 26)
    except:
        font_txt = ImageFont.load_default()
        font_sub = font_txt
        
    draw.text((w // 2, h + 15), "ESCANEAR DEMO EN VIVO", fill="#0284c7", font=font_txt, anchor="mm")
    draw.text((w // 2, h + 65), "Control In-Operando & SCADA", fill="#64748b", font=font_sub, anchor="mm")

    canvas.save(output_path, "PNG", dpi=(300, 300))
    print(f"[OK] Código QR generado en: {output_path}")
    return canvas

def incrustar_qr_en_pdf(pdf_in, pdf_out, qr_img_path):
    """Incrusta el código QR en la esquina inferior derecha bajo 'Referencias y Diseño de control'."""
    doc = fitz.open(pdf_in)
    page = doc[0]
    
    # Coordenadas exactas en el espacio en blanco bajo "Referencias y Diseño de control"
    # Espacio libre: X ~ 2188 a 2474 (centrado en 2330), Y ~ 3208 a 3392
    qr_x1 = 2235.0
    qr_y1 = 3208.0
    qr_x2 = 2425.0
    qr_y2 = 3392.0
    rect_qr = fitz.Rect(qr_x1, qr_y1, qr_x2, qr_y2)
    
    page.insert_image(rect_qr, filename=qr_img_path)
    doc.save(pdf_out)
    doc.close()
    print(f"[OK] PDF final con QR guardado en: {pdf_out}")

    # Generar miniatura de verificación
    doc_verif = fitz.open(pdf_out)
    p = doc_verif[0]
    pix = p.get_pixmap(dpi=100)
    pix.save(PREVIEW_OUTPUT)
    doc_verif.close()
    print(f"[OK] Previsualización del cartel guardada en: {PREVIEW_OUTPUT}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incrustador de QR en Cartel SMEQ 2026")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"URL del destino (default: {DEFAULT_URL})")
    args = parser.parse_args()

    generar_codigo_qr(args.url, QR_PNG_OUTPUT)
    incrustar_qr_en_pdf(PDF_INPUT, PDF_OUTPUT, QR_PNG_OUTPUT)

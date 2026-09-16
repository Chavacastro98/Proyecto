#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un PDF imprimible del Manual de Operación SCADA.
  - Embebe todas las imágenes como base64 data URIs
  - Reescribe CSS para formato impreso (fondo blanco, márgenes cuidados)
  - Evita cortes de página en tablas, figuras, cards y alertas
  - Tablas compactas y legibles
  - Sin propiedades web (hover, transitions, modal, JS, sidebar)
  - Usa Playwright (Chrome headless) para renderizar el PDF
"""

import base64
import os
import re
import sys
from pathlib import Path

# Directorio del manual
MANUAL_DIR = Path(__file__).resolve().parent.parent / "manuales"
HTML_FILE = MANUAL_DIR / "MANUAL_DE_OPERACION_QUIMICA.html"
IMG_DIR = MANUAL_DIR / "imagenes"
OUTPUT_PDF = MANUAL_DIR / "MANUAL_DE_OPERACION_QUIMICA_IMPRIMIBLE.pdf"
INTERMEDIATE_HTML = MANUAL_DIR / "MANUAL_IMPRIMIBLE_TEMP.html"


def log(msg):
    """Print sin emojis para evitar errores de encoding en Windows."""
    safe = msg.encode('ascii', errors='replace').decode('ascii')
    print(safe)


def embed_images(html: str) -> str:
    """Reemplaza todas las rutas de imagenes relativas con data URIs base64."""
    def replace_src(match):
        full_match = match.group(0)
        src = match.group(1)
        img_path = MANUAL_DIR / src
        if not img_path.exists():
            log(f"  [WARN] Imagen no encontrada: {img_path}")
            return full_match

        ext = img_path.suffix.lower()
        mime = {
            '.png': 'image/png', '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', '.gif': 'image/gif',
            '.svg': 'image/svg+xml', '.webp': 'image/webp',
        }.get(ext, 'image/png')

        data = img_path.read_bytes()
        b64 = base64.b64encode(data).decode('ascii')
        data_uri = f"data:{mime};base64,{b64}"
        log(f"  [OK] Embebida: {src} ({len(data)//1024} KB)")
        return f'src="{data_uri}"'

    return re.sub(r'src="(imagenes/[^"]+)"', replace_src, html)


def remove_web_elements(html: str) -> str:
    """Elimina sidebar, modal, JavaScript y botones interactivos."""
    # Sidebar
    html = re.sub(r'<aside class="sidebar">.*?</aside>', '', html, flags=re.DOTALL)
    # Modal de zoom
    html = re.sub(r'<div id="imgModal".*?</div>\s*</div>', '', html, flags=re.DOTALL)
    # Scripts
    html = re.sub(r'<script>.*?</script>', '', html, flags=re.DOTALL)
    # KaTeX CDN
    html = re.sub(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/katex[^"]*"[^>]*>', '', html)
    html = re.sub(r'<script[^>]*src="https://cdn\.jsdelivr\.net/npm/katex[^"]*"[^>]*>[^<]*</script>', '', html)
    # onclick
    html = re.sub(r'\s*onclick="openModal\(this\.src\)"', '', html)
    # hero-actions
    html = re.sub(r'<div class="hero-actions">.*?</div>', '', html, flags=re.DOTALL)
    # enlace preview local
    html = re.sub(r'<a href="\.\./preview/[^"]*"[^>]*>.*?</a>', '', html, flags=re.DOTALL)
    return html


def build_print_css() -> str:
    """CSS completo optimizado para impresion en PDF via Chrome."""
    return """
    /* ========== RESET ========== */
    * { box-sizing: border-box; margin: 0; padding: 0; }

    @page {
      size: letter;
      margin: 1.8cm 1.6cm 1.8cm 1.6cm;
    }

    body {
      background-color: #ffffff !important;
      color: #1a1a1a !important;
      font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
      font-size: 9pt;
      line-height: 1.5;
      display: block;
    }

    /* ========== LAYOUT ========== */
    main.main-content {
      max-width: 100% !important;
      padding: 0 !important;
      overflow: visible;
    }

    /* ========== HERO BANNER (portada) ========== */
    .hero-banner {
      background: #f0f4f8 !important;
      border: 2px solid #333 !important;
      border-radius: 6px;
      padding: 18px 22px !important;
      margin-bottom: 22px;
      box-shadow: none !important;
      break-inside: avoid;
      page-break-inside: avoid;
    }

    .hero-banner h1 {
      color: #111 !important;
      font-size: 17pt !important;
      line-height: 1.25;
      margin-bottom: 6px;
    }

    .hero-banner p.lead {
      color: #333 !important;
      font-size: 9pt !important;
    }

    .badge-bar { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
    .badge {
      font-size: 6.5pt; font-weight: 700; padding: 2px 6px;
      border-radius: 10px; letter-spacing: 0.3px; text-transform: uppercase;
      color: #444 !important; border: 1px solid #888 !important; background: #e8e8e8 !important;
    }
    .badge-primary, .badge-success, .badge-warning, .badge-purple, .badge-pink, .badge-danger {
      color: #444 !important; border: 1px solid #888 !important; background: #eee !important;
    }

    /* ========== SECTIONS ========== */
    section { margin-bottom: 16px; }

    h2.section-title {
      font-size: 13pt; color: #003d82 !important;
      border-bottom: 2px solid #003d82; padding-bottom: 4px;
      margin-bottom: 10px; margin-top: 14px;
      display: flex; align-items: center; gap: 7px;
      break-after: avoid; page-break-after: avoid;
    }

    h3.subsection-title {
      font-size: 11pt; color: #1a1a1a !important;
      margin-top: 12px; margin-bottom: 7px;
      display: flex; align-items: center; gap: 5px;
      break-after: avoid; page-break-after: avoid;
      font-weight: 700;
    }

    h4 {
      font-size: 10pt; color: #1a1a1a !important;
      break-after: avoid; page-break-after: avoid;
    }

    p {
      color: #222 !important; margin-bottom: 7px; font-size: 9pt;
      orphans: 3; widows: 3;
    }
    strong { color: #111 !important; }
    em { color: #333 !important; }

    /* ========== ALERTS ========== */
    .alert {
      padding: 8px 12px; border-radius: 3px; margin: 8px 0;
      border-left: 4px solid; background-color: #f9f9f9 !important;
      font-size: 8pt; color: #222 !important;
      break-inside: avoid; page-break-inside: avoid;
    }
    .alert-warning { border-color: #b8860b !important; background: #fffbf0 !important; }
    .alert-danger  { border-color: #cc0000 !important; background: #fff5f5 !important; }
    .alert-info    { border-color: #0066cc !important; background: #f0f7ff !important; }
    .alert-success { border-color: #228b22 !important; background: #f0fff0 !important; }
    .alert strong { display: block; margin-bottom: 2px; font-size: 8.5pt; color: #111 !important; }

    /* ========== CARDS ========== */
    .card-grid {
      display: grid; grid-template-columns: repeat(2, 1fr);
      gap: 8px; margin: 8px 0;
    }
    .card {
      background-color: #fafafa !important; border: 1px solid #bbb !important;
      border-radius: 3px; padding: 8px 10px;
      break-inside: avoid; page-break-inside: avoid;
      overflow-wrap: break-word; word-break: break-word;
      min-width: 0; overflow: hidden;
    }
    .card:hover { border-color: #bbb !important; transform: none !important; }
    .card-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 5px; border-bottom: 1px solid #ddd; padding-bottom: 3px;
    }
    .card-header h4 { font-size: 8.5pt; color: #111 !important; }
    .card-param {
      display: flex; justify-content: space-between;
      font-size: 7.5pt; padding: 2px 0; border-bottom: 1px dashed #ddd;
    }
    .card-param .label { color: #555 !important; }
    .card-param .value { font-weight: 600; color: #111 !important; }

    /* ========== TABLES (COMPACTAS) ========== */
    .table-container {
      overflow: visible; margin: 8px 0;
      border: 1px solid #999; border-radius: 2px;
      break-inside: avoid; page-break-inside: avoid;
    }
    table {
      width: 100%; border-collapse: collapse;
      font-size: 7.5pt; text-align: left;
    }
    th {
      background-color: #e0e6ed !important; color: #111 !important;
      padding: 4px 5px; font-weight: 700; font-size: 7.5pt;
      border-bottom: 1.5px solid #999; white-space: normal;
    }
    td {
      padding: 3px 5px; border-bottom: 1px solid #ddd;
      color: #222 !important; vertical-align: top;
      font-size: 7.5pt; line-height: 1.35;
    }
    tr { break-inside: avoid; page-break-inside: avoid; }
    tr:hover td { background-color: transparent !important; }

    .badge-btn {
      display: inline-block; padding: 1px 4px;
      background-color: #f0f0f0 !important; border: 1px solid #777 !important;
      border-radius: 2px; color: #111 !important;
      font-weight: 700; font-size: 7pt; white-space: nowrap;
    }

    /* ========== FIGURES ========== */
    .figure-box {
      background-color: #fafafa !important; border: 1px solid #bbb !important;
      border-radius: 3px; padding: 8px; margin: 10px 0; text-align: center;
      break-inside: avoid; page-break-inside: avoid;
    }
    .figure-box img {
      max-width: 90% !important; height: auto;
      border-radius: 2px; border: 1px solid #999 !important; cursor: default !important;
    }
    .figure-box img:hover { box-shadow: none !important; }
    .figure-caption {
      margin-top: 5px; font-size: 7.5pt;
      color: #555 !important; font-style: italic;
    }

    /* ========== CODE ========== */
    pre, code {
      font-family: 'Consolas', 'Courier New', monospace;
      word-break: break-word; overflow-wrap: anywhere;
    }
    code {
      background: #f0f0f0 !important; padding: 1px 3px;
      border-radius: 2px; color: #003d82 !important; font-size: 7.5pt;
    }
    .code-box {
      background-color: #f5f5f5 !important; border: 1px solid #999 !important;
      border-radius: 3px; padding: 8px 10px;
      font-size: 6.5pt; font-family: 'Consolas', monospace;
      color: #222 !important; overflow: visible; margin: 8px 0;
      white-space: pre-wrap; line-height: 1.3;
      break-inside: avoid; page-break-inside: avoid;
    }
    .code-box pre {
      color: #222 !important; font-weight: 600 !important;
      font-size: 6pt !important; line-height: 1.25 !important;
    }

    /* ========== LINKS ========== */
    a { color: #003d82 !important; text-decoration: underline; }
    .link-pdf { color: #003d82 !important; text-decoration: underline; font-weight: 600; }

    /* ========== PAGE BREAKS ========== */
    h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
    .card, .alert, .figure-box, .table-container, .code-box {
      break-inside: avoid; page-break-inside: avoid;
    }

    /* ========== HIDDEN WEB ELEMENTS ========== */
    .hero-actions, .btn, aside.sidebar, .modal { display: none !important; }
"""


def inject_print_styles(html: str) -> str:
    """Reemplaza el bloque <style> original con CSS de impresion."""
    new_style = f"<style>{build_print_css()}</style>"
    html = re.sub(r'<style>.*?</style>', new_style, html, count=1, flags=re.DOTALL)
    return html


def fix_inline_styles(html: str) -> str:
    """Corrige estilos inline pensados para fondo oscuro."""
    replacements = {
        'color:#e2e8f0;': 'color:#222;',
        'color:#38bdf8;': 'color:#003d82;',
        'color:#10b981;': 'color:#228b22;',
        'color:#f59e0b;': 'color:#b8860b;',
        'color:#c084fc;': 'color:#6a3d9a;',
        'color:#ef4444;': 'color:#cc0000;',
        'color:#34d399;': 'color:#228b22;',
        'color:#f472b6;': 'color:#993366;',
    }
    for old, new in replacements.items():
        html = html.replace(old, new)

    # Fondos oscuros inline en code-box
    html = re.sub(
        r'style="background:#090d16;[^"]*"',
        'style="background:#f5f5f5; border:1px solid #999; padding:10px; border-radius:4px;"',
        html
    )
    html = re.sub(
        r'style="background:#060913;[^"]*"',
        'style="background:#f5f5f5; border:1px solid #999; padding:10px; border-radius:4px;"',
        html
    )

    # Colores de pre dentro de code-box
    html = html.replace(
        'color:#38bdf8; font-weight:700;',
        'color:#222; font-weight:600;'
    )
    html = html.replace(
        'color:#34d399; font-weight:700;',
        'color:#222; font-weight:600;'
    )

    # Fondos de creditos
    html = re.sub(
        r'style="background:rgba\(15,23,42,0\.6\);[^"]*"',
        'style="background:#f5f5f5; padding:7px 10px; border-radius:3px; border:1px solid #ccc; font-size:7.5pt; line-height:1.35; margin-bottom:5px;"',
        html
    )

    # Border-left en cards
    html = re.sub(
        r'style="border-left:4px solid #[a-fA-F0-9]+;"',
        'style="border-left:4px solid #666;"',
        html
    )

    # padding-left de nav links (ya eliminados pero por si acaso)
    html = re.sub(
        r'style="padding-left:24px;font-size:0\.78rem;color:#38bdf8;"',
        '',
        html
    )

    # Inline font-size en p tags de cards (reducir para impresion)
    html = html.replace('font-size:0.85rem;', 'font-size:8pt;')
    html = html.replace('font-size:0.82rem;', 'font-size:7.5pt;')
    html = html.replace('font-size:0.87rem;', 'font-size:8pt;')
    html = html.replace('font-size:0.88rem;', 'font-size:8pt;')
    html = html.replace('font-size:0.92rem;', 'font-size:8.5pt;')

    # Alert inline overrides
    html = re.sub(
        r'style="margin-top:16px; border-left:4px solid #ef4444; background: rgba\(239,68,68,0\.08\);"',
        'style="margin-top:10px; border-left:4px solid #cc0000; background:#fff5f5;"',
        html
    )
    html = re.sub(
        r'style="margin-top:16px; border-left:4px solid #38bdf8;"',
        'style="margin-top:10px; border-left:4px solid #003d82;"',
        html
    )

    return html


def add_page_breaks_before_sections(html: str) -> str:
    """Saltos de pagina antes de secciones principales."""
    first = True
    def add_break(match):
        nonlocal first
        if first:
            first = False
            return match.group(0)
        return f'\n<div style="break-before: page; page-break-before: always;"></div>\n{match.group(0)}'
    html = re.sub(r'<section\s+id="[^"]*">', add_break, html)
    return html


def add_footer_info(html: str) -> str:
    """Agrega info de version al banner."""
    footer = """
    <div style="margin-top:10px; padding-top:6px; border-top:1px solid #999; font-size:7.5pt; color:#555;">
      <strong>Documento generado para impresion</strong> -- Septiembre 2026<br>
      Software SCADA Python (v3.5 / RTOS 1.3) -- ESP32 Master + Arduino Nano
    </div>
    """
    html = html.replace(
        '</div>\n\n    <!-- SECCIÓN 1:',
        f'{footer}</div>\n\n    <!-- SECCIÓN 1:'
    )
    return html


def generate_pdf():
    """Pipeline principal."""
    log("=" * 60)
    log("  GENERADOR DE PDF IMPRIMIBLE -- Manual SCADA")
    log("=" * 60)

    # 1. Leer HTML
    log("\n[1/7] Leyendo HTML original...")
    html = HTML_FILE.read_text(encoding='utf-8')
    log(f"       {len(html):,} bytes")

    # 2. Embeber imagenes
    log("\n[2/7] Embebiendo imagenes como base64...")
    html = embed_images(html)

    # 3. Eliminar elementos web
    log("\n[3/7] Eliminando elementos web...")
    html = remove_web_elements(html)

    # 4. CSS de impresion
    log("\n[4/7] Inyectando CSS para impresion...")
    html = inject_print_styles(html)

    # 5. Fix inline styles
    log("\n[5/7] Corrigiendo estilos inline...")
    html = fix_inline_styles(html)

    # 6. Page breaks
    log("\n[6/7] Saltos de pagina entre secciones...")
    html = add_page_breaks_before_sections(html)
    html = add_footer_info(html)

    # Guardar HTML intermedio
    INTERMEDIATE_HTML.write_text(html, encoding='utf-8')
    log(f"       HTML temporal: {INTERMEDIATE_HTML}")

    # 7. Generar PDF con Playwright (Chrome headless)
    log("\n[7/7] Generando PDF con Chrome headless (Playwright)...")
    try:
        from playwright.sync_api import sync_playwright

        file_url = INTERMEDIATE_HTML.as_uri()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # Cargar HTML
            page.goto(file_url, wait_until='networkidle')

            # Esperar a que las imagenes carguen
            page.wait_for_timeout(2000)

            # Generar PDF
            page.pdf(
                path=str(OUTPUT_PDF),
                format='Letter',
                margin={
                    'top': '1.8cm',
                    'bottom': '1.8cm',
                    'left': '1.6cm',
                    'right': '1.6cm',
                },
                print_background=True,
                prefer_css_page_size=False,
            )

            browser.close()

        size_mb = OUTPUT_PDF.stat().st_size / (1024 * 1024)
        log(f"\n{'=' * 60}")
        log(f"  [OK] PDF GENERADO EXITOSAMENTE")
        log(f"     Archivo: {OUTPUT_PDF}")
        log(f"     Tamano:  {size_mb:.1f} MB")
        log(f"{'=' * 60}")

        # Limpiar HTML temporal
        if INTERMEDIATE_HTML.exists():
            INTERMEDIATE_HTML.unlink()
            log("       HTML temporal eliminado.")

    except Exception as e:
        log(f"\n  [ERROR] Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    generate_pdf()

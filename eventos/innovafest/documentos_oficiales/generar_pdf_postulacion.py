import markdown
from playwright.sync_api import sync_playwright
import os
import fitz

md_path = r"C:\Proyecto\Proyecto\Innovafest\01_DOCUMENTO_OFICIAL_POSTULACION.md"
pdf_path = r"C:\Proyecto\Proyecto\Innovafest\01_DOCUMENTO_OFICIAL_POSTULACION.pdf"

with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

import base64
with open(r"C:\Proyecto\Proyecto\Innovafest\logo_udg.png", "rb") as f:
    udg_b64 = base64.b64encode(f.read()).decode("utf-8")
with open(r"C:\Proyecto\Proyecto\Innovafest\logo_cucei.png", "rb") as f:
    cucei_b64 = base64.b64encode(f.read()).decode("utf-8")

html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: letter;
        margin: 20mm 18mm 20mm 18mm;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 9.8pt;
        line-height: 1.48;
        color: #1e293b;
        margin: 0;
        padding: 0;
    }}
    .institutional-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2.5px solid #0284c7;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }}
    .header-logo {{
        height: 56px;
        width: auto;
        object-fit: contain;
    }}
    .header-titles {{
        text-align: center;
        flex: 1;
        padding: 0 12px;
    }}
    .univ-title {{
        font-size: 12pt;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 0.5px;
    }}
    .center-title {{
        font-size: 9.5pt;
        font-weight: 600;
        color: #0284c7;
        margin-top: 1px;
    }}
    .event-title {{
        font-size: 8pt;
        font-weight: 600;
        color: #64748b;
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    h1 {{
        font-size: 13pt;
        color: #0f172a;
        margin: 0 0 4px 0;
        font-weight: 800;
        text-align: center;
    }}
    h2 {{
        font-size: 10pt;
        color: #0284c7;
        margin: 0 0 10px 0;
        font-weight: 600;
        text-align: center;
        text-transform: uppercase;
    }}
    h3 {{
        font-size: 10.5pt;
        color: #0f172a;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 2px;
        margin-top: 12px;
        margin-bottom: 6px;
        font-weight: 700;
    }}
    h4 {{
        font-size: 9.8pt;
        color: #0369a1;
        margin-top: 8px;
        margin-bottom: 3px;
        font-weight: 600;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 6px;
        text-align: justify;
    }}
    ul, ol {{
        margin-top: 0;
        margin-bottom: 6px;
        padding-left: 18px;
    }}
    li {{
        margin-bottom: 2px;
        text-align: justify;
    }}
    strong {{
        color: #0f172a;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        margin-bottom: 10px;
        font-size: 8.5pt;
    }}
    th, td {{
        border: 1px solid #cbd5e1;
        padding: 5px 7px;
        text-align: left;
    }}
    th {{
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: 700;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    hr {{
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 10px 0;
    }}
    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>
<div class="institutional-header">
    <img src="data:image/png;base64,{udg_b64}" class="header-logo" alt="Universidad de Guadalajara">
    <div class="header-titles">
        <div class="univ-title">UNIVERSIDAD DE GUADALAJARA</div>
        <div class="center-title">Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI)</div>
        <div class="event-title">Premio a la Innovación Mexicana 2026 · InnovaFest Guadalajara</div>
    </div>
    <img src="data:image/png;base64,{cucei_b64}" class="header-logo" alt="CUCEI">
</div>
{html_body}
</body>
</html>
"""

temp_html = r"C:\Proyecto\Proyecto\Innovafest\temp_doc.html"
with open(temp_html, "w", encoding="utf-8") as f:
    f.write(html_content)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file:///{temp_html.replace(os.sep, '/')}")
    page.pdf(
        path=pdf_path,
        format="Letter",
        print_background=True,
        display_header_footer=True,
        header_template='<div style="font-size: 7.5pt; color: #94a3b8; width: 100%; text-align: right; padding-right: 18mm;">InnovaFest Guadalajara 2026 — Premio a la Innovación Mexicana</div>',
        footer_template='<div style="font-size: 7.5pt; color: #94a3b8; width: 100%; text-align: center;">Página <span class="pageNumber"></span> de <span class="totalPages"></span></div>',
        margin={
            "top": "22mm",
            "bottom": "22mm",
            "left": "18mm",
            "right": "18mm"
        }
    )
    browser.close()

if os.path.exists(temp_html):
    os.remove(temp_html)

doc = fitz.open(pdf_path)
page_count = len(doc)
file_size_kb = os.path.getsize(pdf_path) / 1024
print(f"Generated {pdf_path}")
print(f"Total Pages: {page_count} (Limit is max 6 pages: 1 portada + 5 desarrollo)")
print(f"File Size: {file_size_kb:.1f} KB (Limit is max 5000 KB)")

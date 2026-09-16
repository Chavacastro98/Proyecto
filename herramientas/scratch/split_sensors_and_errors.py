# -*- coding: utf-8 -*-
import subprocess
import os

preview_file = r"C:\Proyecto\Proyecto\preview\RTOS1.3\sensores.html"
with open(preview_file, "r", encoding="utf-8") as f:
    full_html = f.read()

# 1. PARTE A: DIAGNÓSTICO DE SENSORES I2C & SPI
# Desactivamos animaciones que empiezan con opacity: 0 para evitar capturas en blanco o a medio desvanecer
no_anim_style = """
<style>
  .s-card {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
  .hb-dot {
    animation: none !important;
    opacity: 1 !important;
  }
</style>
"""

html_sensores = full_html.replace(
    "</head>",
    f"{no_anim_style}</head>"
).replace(
    "<div class='led-box'>",
    "<div class='led-box' style='display:none;'>"
)

with open(r"C:\Proyecto\Proyecto\scratch\view_sensores_grid.html", "w", encoding="utf-8") as f:
    f.write(html_sensores)

# 2. PARTE B: BALIZA LED RGB Y ERRORES DEL SUPERVISOR
no_anim_baliza = """
<style>
  * {
    animation-duration: 0.001s !important;
  }
</style>
"""

html_errores = full_html.replace(
    "</head>",
    f"{no_anim_baliza}</head>"
).replace(
    "<div class='hdr-title'>Diagn&oacute;stico de Sensores</div>",
    "<div class='hdr-title'>Baliza LED RGB & Diagn&oacute;stico de Errores</div>"
).replace(
    "<span class='hdr-sub'>I2C &middot; SPI &middot; 8 PERIF&Eacute;RICOS EN PLANTA</span>",
    "<span class='hdr-sub'>SUPERVISOR FREERTOS EN TIEMPO REAL (CORE 1) &middot; 13 C&Oacute;DIGOS</span>"
).replace(
    "<div class='summary'>",
    "<div class='summary' style='display:none;'>"
).replace(
    "<div class='filter-bar'>",
    "<div class='filter-bar' style='display:none;'>"
).replace(
    "<div class='grid' id='grid'></div>",
    ""
).replace(
    "<div class='ts' id='ts'>",
    "<div class='ts' id='ts' style='display:none;'>"
)

with open(r"C:\Proyecto\Proyecto\scratch\view_baliza_errores.html", "w", encoding="utf-8") as f:
    f.write(html_errores)

# 3. RENDERIZAR CON CHROME HEADLESS
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dir = r"C:\Proyecto\Proyecto\documentos\imagenes"

# Usamos 960x780 para la cuadrícula de sensores para que la fila inferior (MAX6675) y el timestamp no se corten
captures = [
    (
        "web_05a_sensores.png",
        r"C:\Proyecto\Proyecto\scratch\view_sensores_grid.html",
        "960,780"
    ),
    (
        "web_05b_baliza_errores.png",
        r"C:\Proyecto\Proyecto\scratch\view_baliza_errores.html",
        "960,880"
    )
]

for name, html_path, size in captures:
    out_file = os.path.join(out_dir, name)
    url = f"file:///{html_path.replace(os.sep, '/')}"
    args = [
        chrome_path,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--virtual-time-budget=2000",
        f"--window-size={size}",
        f"--screenshot={out_file}",
        url
    ]
    print(f"Rendering {name} with size {size} and virtual-time-budget...")
    res = subprocess.run(args, capture_output=True, text=True)
    if os.path.exists(out_file):
        print(f"  OK: {name} ({os.path.getsize(out_file)} bytes)")
    else:
        print(f"  FAIL: {name}")

print("Done rendering split views!")

# -*- coding: utf-8 -*-
"""
Script para eliminar todas las rutas absolutas y referencias a C:\ o c:/
reemplazándolas por rutas relativas portátiles que funcionan en cualquier
ubicación donde se extraiga el ZIP del proyecto.
"""

import re

# 1. MANUAL_DE_OPERACION_QUIMICA.html
html_path = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    "en la raíz del repositorio (<code>c:\\Proyecto\\Proyecto\\</code>):",
    "en la raíz del repositorio:"
)
html = html.replace(
    "c:\\Proyecto\\Proyecto\\\n",
    "Proyecto/\n"
)
html = html.replace(
    'href="file:///c:/Proyecto/Proyecto/preview/index.html"',
    'href="../preview/index.html"'
)
html = html.replace(
    'href="file:///c:/Proyecto/Proyecto/documentos/instaladores/instalar_librerias_arduino.bat"',
    'href="instaladores/instalar_librerias_arduino.bat"'
)
html = html.replace(
    "Simplemente abre la carpeta raíz del proyecto (<code>c:\\Proyecto</code>) dentro de <strong>Antigravity IDE</strong>.",
    "Simplemente abre la carpeta raíz del proyecto descomprimido dentro de <strong>Antigravity IDE</strong>."
)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("MANUAL_DE_OPERACION_QUIMICA.html cleaned.")

# 2. MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md
md_path = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md"
with open(md_path, "r", encoding="utf-8") as f:
    md = f.read()

# Replace all file:/// links to images
md = md.replace("file:///c:/Proyecto/Proyecto/documentos/imagenes/", "imagenes/")

# Replace other file:/// links
md = md.replace("file:///c:/Proyecto/Proyecto/Iniciar_Telemetria.bat", "../Iniciar_Telemetria.bat")
md = md.replace("file:///c:/Proyecto/Proyecto/telemetria/app.py", "../telemetria/app.py")
md = md.replace("file:///c:/Proyecto/telemetria/graficar_datos.py", "../telemetria/graficar_datos.py")
md = md.replace("file:///c:/Proyecto/Proyecto/telemetria/graficar_datos.py", "../telemetria/graficar_datos.py")
md = md.replace("file:///c:/Proyecto/Proyecto/documentos/instaladores/instalar_librerias_arduino.bat", "instaladores/instalar_librerias_arduino.bat")

# Replace c:\Proyecto references in text
md = md.replace("c:\\Proyecto\\Proyecto\\\n", "Proyecto/\n")
md = md.replace("carpeta raíz `c:\\Proyecto`", "carpeta raíz del proyecto descomprimido")

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md)
print("MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md cleaned.")

# 3. diagramas/README.md
diag_path = r"c:\Proyecto\Proyecto\diagramas\README.md"
with open(diag_path, "r", encoding="utf-8") as f:
    diag = f.read()

diag = diag.replace("file:///c:/Proyecto/Proyecto/diagramas/iniciar_visor_diagramas.bat", "iniciar_visor_diagramas.bat")
diag = diag.replace("file:///c:/Proyecto/Proyecto/Ver_Diagramas.bat", "../Ver_Diagramas.bat")
diag = diag.replace("file:///c:/Proyecto/Proyecto/diagramas/index.html", "index.html")
diag = diag.replace("file:///c:/Proyecto/Proyecto/diagramas", "./")

with open(diag_path, "w", encoding="utf-8") as f:
    f.write(diag)
print("diagramas/README.md cleaned.")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizador Automático de GitHub Pages y Paquete Móvil Galaxy
Copia automáticamente cualquier cambio realizado en documentos/academicos/showcase_web/
hacia la carpeta pública docs/ y actualiza el archivo ZIP de Fernando.
"""

import os
import shutil
import zipfile

def sincronizar():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir = os.path.join(repo_root, "documentos", "academicos", "showcase_web")
    docs_dir = os.path.join(repo_root, "docs")
    zip_path = os.path.join(repo_root, "documentos", "academicos", "showcase_web_galaxy_s26_ultra.zip")

    if not os.path.exists(src_dir):
        print(f"[AVISO] No se encontró la carpeta fuente: {src_dir}")
        return

    os.makedirs(docs_dir, exist_ok=True)

    # 1. Regenerar showcase_galaxy_standalone.html en src_dir
    try:
        index_file = os.path.join(src_dir, "index.html")
        with open(index_file, "r", encoding="utf-8") as f:
            html = f.read()

        css_var = open(os.path.join(src_dir, "css", "variables.css"), "r", encoding="utf-8").read()
        css_lay = open(os.path.join(src_dir, "css", "layout.css"), "r", encoding="utf-8").read()
        css_comp = open(os.path.join(src_dir, "css", "components.css"), "r", encoding="utf-8").read()
        js_sim = open(os.path.join(src_dir, "js", "simuladores.js"), "r", encoding="utf-8").read()
        js_ph = open(os.path.join(src_dir, "js", "calibracion_ph.js"), "r", encoding="utf-8").read()
        js_app = open(os.path.join(src_dir, "js", "app.js"), "r", encoding="utf-8").read()

        css_bundle = f"<style>\n{css_var}\n\n{css_lay}\n\n{css_comp}\n</style>"
        html_standalone = html.replace(
            '  <link rel="stylesheet" href="css/variables.css">\n  <link rel="stylesheet" href="css/layout.css">\n  <link rel="stylesheet" href="css/components.css">',
            css_bundle
        )
        js_bundle = f"<script>\n{js_sim}\n\n{js_ph}\n\n{js_app}\n</script>"
        html_standalone = html_standalone.replace(
            '  <script src="js/simuladores.js"></script>\n  <script src="js/calibracion_ph.js"></script>\n  <script src="js/app.js"></script>',
            js_bundle
        )
        with open(os.path.join(src_dir, "showcase_galaxy_standalone.html"), "w", encoding="utf-8") as f:
            f.write(html_standalone)
    except Exception as e:
        print(f"[AVISO] Error regenerando standalone: {e}")

    # 2. Copiar archivos de src_dir a docs_dir
    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(docs_dir, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # 3. Asegurar .nojekyll en docs
    nojekyll_file = os.path.join(docs_dir, ".nojekyll")
    if not os.path.exists(nojekyll_file):
        with open(nojekyll_file, "w") as f:
            f.write("")

    # 4. Actualizar ZIP para Fernando
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(src_dir):
                for file in files:
                    if file.endswith(('.zip', '.tmp')):
                        continue
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, src_dir)
                    zipf.write(full_p, arcname=rel_p)
    except Exception as e:
        print(f"[AVISO] Error actualizando zip: {e}")

    print("[OK] Sincronizacion exitosa: showcase_web -> docs/ y ZIP actualizado.")

if __name__ == '__main__':
    sincronizar()

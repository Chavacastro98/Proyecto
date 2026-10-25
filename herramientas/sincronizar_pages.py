#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizador Oficial de GitHub Pages (docs/)
Copia automáticamente cualquier cambio realizado en documentos/academicos/showcase_web/
hacia la carpeta pública docs/ para despliegue directo en GitHub Pages.
"""

import os
import shutil

def sincronizar():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_dir = os.path.join(repo_root, "documentos", "academicos", "showcase_web")
    docs_dir = os.path.join(repo_root, "docs")

    if not os.path.exists(src_dir):
        print("[INFO] La carpeta docs/ es la fuente principal para GitHub Pages.")
        return

    os.makedirs(docs_dir, exist_ok=True)

    # 1. Copiar archivos de src_dir a docs_dir
    EXCLUIR_DOCS = {
        "showcase_galaxy_standalone.html",
        "showcase_web_galaxy_s26_ultra.zip",
        "servidor_showcase.py",
        "iniciar_servidor.bat",
        "servidor_local_showcase.py",
        "iniciar_servidor_showcase.bat",
    }
    for item in os.listdir(src_dir):
        if item in EXCLUIR_DOCS or item.endswith(('.tmp', '.zip')):
            continue
        s = os.path.join(src_dir, item)
        d = os.path.join(docs_dir, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    # Limpiar archivos obsoletos en docs si existían previamente
    for exc in EXCLUIR_DOCS:
        p_exc = os.path.join(docs_dir, exc)
        if os.path.exists(p_exc):
            try:
                if os.path.isdir(p_exc):
                    shutil.rmtree(p_exc)
                else:
                    os.remove(p_exc)
            except Exception:
                pass

    # 2. Asegurar .nojekyll en docs para GitHub Pages
    nojekyll_file = os.path.join(docs_dir, ".nojekyll")
    if not os.path.exists(nojekyll_file):
        with open(nojekyll_file, "w") as f:
            f.write("")

    print("[OK] Sincronización exitosa: showcase_web -> docs/ (GitHub Pages).")

if __name__ == '__main__':
    sincronizar()

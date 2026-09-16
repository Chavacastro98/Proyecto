#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
VISOR Y GENERADOR MODULAR DE DIAGRAMAS TÉCNICOS
Planta Piloto de Electrodeposición — ESP32-S3 / Arduino Nano / SCADA
===================================================================================
Arquitecturas Soportadas:
  1. Super-Loop (v4.0): Super-loop asíncrono, MVC modular, spinlocks portMUX_TYPE.
  2. FreeRTOS SMP (RTOS 1.0): Multitarea simétrica dual-core, N16R8, Fail-Safe Latch.

Diseño Modular:
  - Fuentes Mermaid en archivos independientes: diagramas/<suite>/fuentes/*.mmd
  - Metadatos estructurados en: diagramas/<suite>/catalogo.json
  - Sincronización automática con el visor web (diagramas/catalogos_data.js).
===================================================================================
"""

import os
import sys
import json
import time
import base64
import urllib.parse
import argparse
import webbrowser
import subprocess
import requests

# Forzar codificación UTF-8 para stdout/stderr en consolas Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import argparse
import webbrowser
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

# Directorio base del módulo de diagramas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUITES_DISPONIBLES = ["rtos", "superloop"]
SUITE_NOMBRES = {
    "rtos": "⚡ FreeRTOS SMP (RTOS 1.3 - ESP32-S3 N16R8)",
    "superloop": "🔬 Super-Loop (v4.0 - Arquitectura Clásica)"
}

# =================================================================================
# GESTOR DE DATOS Y CARGA DINÁMICA DE SUITES
# =================================================================================

def cargar_suite(suite_id):
    """
    Carga los metadatos y el código Mermaid (.mmd) de una suite específica.
    Retorna un diccionario estructurado o None si falla.
    """
    suite_dir = os.path.join(BASE_DIR, suite_id)
    catalogo_path = os.path.join(suite_dir, "catalogo.json")
    fuentes_dir = os.path.join(suite_dir, "fuentes")

    if not os.path.exists(catalogo_path):
        print(f"[ERROR] No se encontró el catálogo en: {catalogo_path}")
        return None

    try:
        with open(catalogo_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Error al leer {catalogo_path}: {e}")
        return None

    diagramas = data.get("diagramas", {})
    for key, item in diagramas.items():
        archivo_mmd = item.get("archivo", f"{key}.mmd")
        ruta_mmd = os.path.join(fuentes_dir, archivo_mmd)
        if os.path.exists(ruta_mmd):
            try:
                with open(ruta_mmd, "r", encoding="utf-8") as f:
                    item["codigo"] = f.read().strip()
            except Exception as e:
                print(f"[WARN] Error al leer archivo {ruta_mmd}: {e}")
                item["codigo"] = "graph TD\n    ERROR[Error al leer archivo fuente]"
        else:
            print(f"[WARN] Archivo .mmd no encontrado: {ruta_mmd}")
            item["codigo"] = "graph TD\n    MISSING[Archivo .mmd no encontrado]"

        # Rutas locales de imágenes
        item["ruta_png"] = os.path.join(suite_dir, "imagenes", f"{key}.png")
        item["ruta_svg"] = os.path.join(suite_dir, "imagenes", f"{key}.svg")

    return data


def generar_catalogos_js():
    """
    Genera automáticamente el archivo 'catalogos_data.js' para el visor web (index.html).
    Permite que el navegador web funcione 100% offline y sin problemas de CORS local (file://).
    """
    datos_completos = {}
    for suite_id in SUITES_DISPONIBLES:
        suite_data = cargar_suite(suite_id)
        if suite_data:
            # Limpiar rutas de disco locales antes de guardar en JS
            datos_limpios = {
                "suite": suite_data.get("suite"),
                "version": suite_data.get("version"),
                "nombre": suite_data.get("nombre"),
                "descripcion": suite_data.get("descripcion"),
                "diagramas": {}
            }
            for k, d in suite_data.get("diagramas", {}).items():
                datos_limpios["diagramas"][k] = {
                    "num": d.get("num"),
                    "cat": d.get("cat"),
                    "title": d.get("title"),
                    "badge": d.get("badge"),
                    "archivo": d.get("archivo"),
                    "desc": d.get("desc"),
                    "code": d.get("codigo", "")
                }
            datos_completos[suite_id] = datos_limpios

    js_path = os.path.join(BASE_DIR, "catalogos_data.js")
    js_content = (
        "// ============================================================================\n"
        "// CATÁLOGOS UNIFICADOS DE DIAGRAMAS TÉCNICOS (GENERADO AUTOMÁTICAMENTE)\n"
        "// Permite ejecución local (file://) sin restricciones de CORS ni latencia de red.\n"
        "// ============================================================================\n\n"
        f"const SUITES_DIAGRAMAS = {json.dumps(datos_completos, indent=2, ensure_ascii=False)};\n"
    )

    try:
        with open(js_path, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"  [OK] Visor Web sincronizado: {js_path}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo generar {js_path}: {e}")
        return False


import zlib

def generar_mermaid_url(code, form_ext="img"):
    """Genera URL segura y compacta con compresión pako (zlib + urlsafe_base64) en tema claro / fondo blanco."""
    payload = json.dumps({'code': code, 'mermaid': {'theme': 'default'}})
    compressed = zlib.compress(payload.encode('utf-8'), 9)
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii')
    return f"https://mermaid.ink/{form_ext}/pako:{b64}"


def descargar_diagrama(suite_id, key, item_data, callback_status=None):
    """Descarga un diagrama desde mermaid.ink en formatos PNG y SVG con compresión pako."""
    suite_dir = os.path.join(BASE_DIR, suite_id)
    img_dir = os.path.join(suite_dir, "imagenes")
    os.makedirs(img_dir, exist_ok=True)

    code = item_data.get("codigo", "")
    if not code or "MISSING" in code:
        return False

    url_png = generar_mermaid_url(code, "img")
    url_svg = generar_mermaid_url(code, "svg")
    png_path = os.path.join(img_dir, f"{key}.png")
    svg_path = os.path.join(img_dir, f"{key}.svg")

    try:
        if callback_status:
            callback_status(f"Descargando [{suite_id.upper()}] {item_data.get('num')}: {item_data.get('title')}...")

        r_png = requests.get(url_png, timeout=15)
        r_svg = requests.get(url_svg, timeout=15)

        ok_png = False
        ok_svg = False

        if r_png.status_code == 200:
            with open(png_path, "wb") as f:
                f.write(r_png.content)
            ok_png = True
        else:
            print(f"  [WARN] Fallo PNG {key} ({suite_id}): HTTP {r_png.status_code}")

        if r_svg.status_code == 200:
            with open(svg_path, "wb") as f:
                f.write(r_svg.content)
            ok_svg = True
        else:
            print(f"  [WARN] Fallo SVG {key} ({suite_id}): HTTP {r_svg.status_code}")

        return ok_png and ok_svg
    except Exception as e:
        print(f"[ERROR] Fallo al descargar {key} ({suite_id}): {e}")
        return False


def exportar_todas_las_imagenes(suite_filtro=None, callback_progreso=None):
    """Descarga y exporta las imágenes para la suite seleccionada o para todas."""
    suites = [suite_filtro] if suite_filtro in SUITES_DISPONIBLES else SUITES_DISPONIBLES
    total_diagramas = 0
    exitosos = 0

    for s_id in suites:
        s_data = cargar_suite(s_id)
        if not s_data:
            continue
        items = s_data.get("diagramas", {})
        total_diagramas += len(items)

    actual = 0
    for s_id in suites:
        s_data = cargar_suite(s_id)
        if not s_data:
            continue
        items = s_data.get("diagramas", {})
        for key, item in items.items():
            actual += 1
            if callback_progreso:
                callback_progreso(actual, total_diagramas, s_id, item.get("title", key))
            ok = descargar_diagrama(s_id, key, item)
            if ok:
                exitosos += 1
            time.sleep(0.12)

    # Actualizar también el archivo catalogos_data.js
    generar_catalogos_js()
    return exitosos, total_diagramas


# =================================================================================
# VENTANA FLOTANTE INDEPENDIENTE DE DIAGRAMA
# =================================================================================

class VentanaDiagrama(tk.Toplevel):
    """Ventana independiente para visualizar e interactuar con un diagrama."""

    def __init__(self, master, suite_id, key, item_data, pos_x=None, pos_y=None):
        super().__init__(master)
        self.suite_id = suite_id
        self.key = key
        self.item = item_data
        self.title(f"[{self.item.get('num', '??')}] {self.item.get('title', '')} ({self.suite_id.upper()})")
        self.geometry("960x740")
        self.minsize(640, 480)
        self.configure(bg="#0b1120")

        if pos_x is not None and pos_y is not None:
            self.geometry(f"+{pos_x}+{pos_y}")

        self.img_original = None
        self.img_tk = None
        self.zoom_factor = 1.0

        self._crear_interfaz()
        self._cargar_imagen()

    def _crear_interfaz(self):
        # Cabecera
        header = tk.Frame(self, bg="#1e293b", padx=16, pady=10)
        header.pack(side=tk.TOP, fill=tk.X)

        badge_lbl = tk.Label(
            header,
            text=f"  {self.item.get('badge', '')}  ",
            bg="#0369a1",
            fg="#e0f2fe",
            font=("Segoe UI", 9, "bold"),
            padx=4,
            pady=2
        )
        badge_lbl.pack(side=tk.LEFT, padx=(0, 10))

        title_lbl = tk.Label(
            header,
            text=f"[{self.item.get('num')}] {self.item.get('title')}",
            bg="#1e293b",
            fg="#f8fafc",
            font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(side=tk.LEFT)

        # Botones cabecera
        btn_box = tk.Frame(header, bg="#1e293b")
        btn_box.pack(side=tk.RIGHT)

        btn_save = tk.Button(
            btn_box,
            text="💾 Guardar Como...",
            bg="#0284c7",
            fg="#ffffff",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._guardar_como
        )
        btn_save.pack(side=tk.LEFT, padx=4)

        btn_code = tk.Button(
            btn_box,
            text="📄 Código Mermaid",
            bg="#334155",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._ver_codigo
        )
        btn_code.pack(side=tk.LEFT, padx=4)

        # Canvas con scrollbars
        canvas_frame = tk.Frame(self, bg="#0b1120")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#0b1120", highlightthickness=0)
        self.hbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bindings de mouse
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_motion)

        # Pie con descripción
        footer = tk.Frame(self, bg="#0f172a", padx=16, pady=8)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        desc_lbl = tk.Label(
            footer,
            text=self.item.get("desc", ""),
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 8),
            wraplength=900,
            justify=tk.LEFT
        )
        desc_lbl.pack(anchor=tk.W)

    def _cargar_imagen(self):
        png_path = self.item.get("ruta_png", "")
        if not os.path.exists(png_path):
            self.canvas.delete("all")
            self.canvas.create_text(
                450, 300,
                text=f"Imagen no disponible localmente.\n\nDescargando desde mermaid.ink...",
                fill="#38bdf8",
                font=("Segoe UI", 12),
                justify=tk.CENTER
            )
            self.update_idletasks()
            ok = descargar_diagrama(self.suite_id, self.key, self.item)
            if not ok or not os.path.exists(png_path):
                self.canvas.delete("all")
                self.canvas.create_text(
                    450, 300,
                    text="No se pudo descargar la imagen.\nVerifica tu conexión a Internet o usa el visor web (HTML).",
                    fill="#ef4444",
                    font=("Segoe UI", 11),
                    justify=tk.CENTER
                )
                return

        try:
            self.img_original = Image.open(png_path)
            self.zoom_factor = 1.0
            self._actualizar_canvas()
        except Exception as e:
            print(f"[ERROR] Error al abrir imagen: {e}")

    def _actualizar_canvas(self):
        if not self.img_original:
            return
        iw, ih = self.img_original.size
        nw = max(int(iw * self.zoom_factor), 20)
        nh = max(int(ih * self.zoom_factor), 20)

        resized = self.img_original.resize((nw, nh), Image.Resampling.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(resized)

        cw = max(self.canvas.winfo_width(), 400)
        ch = max(self.canvas.winfo_height(), 300)
        pos_x = max(cw // 2, nw // 2 + 20)
        pos_y = max(ch // 2, nh // 2 + 20)

        self.canvas.delete("all")
        self.canvas.create_image(pos_x, pos_y, image=self.img_tk, anchor=tk.CENTER)
        self.canvas.config(scrollregion=(0, 0, max(cw, nw + 40), max(ch, nh + 40)))

    def _on_mousewheel(self, event):
        if not self.img_original:
            return
        if event.delta > 0:
            self.zoom_factor = min(self.zoom_factor * 1.15, 3.5)
        else:
            self.zoom_factor = max(self.zoom_factor / 1.15, 0.2)
        self._actualizar_canvas()

    def _on_pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_pan_motion(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _guardar_como(self):
        png_path = self.item.get("ruta_png", "")
        if not os.path.exists(png_path):
            messagebox.showerror("Error", "La imagen no existe aún en disco.")
            return

        dest = filedialog.asksaveasfilename(
            title="Guardar Diagrama como Imagen",
            initialfile=f"{self.suite_id}_{self.key}.png",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png"), ("Todos los archivos", "*.*")]
        )
        if dest:
            try:
                import shutil
                shutil.copyfile(png_path, dest)
                messagebox.showinfo("Éxito", f"Diagrama guardado en:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {e}")

    def _ver_codigo(self):
        w = tk.Toplevel(self)
        w.title(f"Código Mermaid — {self.item.get('title')}")
        w.geometry("720x520")
        w.configure(bg="#0f172a")

        txt = tk.Text(w, bg="#0b1120", fg="#38bdf8", font=("Consolas", 10), wrap=tk.NONE)
        scroll_y = ttk.Scrollbar(w, orient=tk.VERTICAL, command=txt.yview)
        scroll_x = ttk.Scrollbar(w, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.insert(tk.END, self.item.get("codigo", ""))
        txt.config(state=tk.DISABLED)


# =================================================================================
# VENTANA PRINCIPAL DE LA APLICACIÓN MODULAR
# =================================================================================

class AplicacionVisorDiagramas(tk.Tk):
    """Ventana principal del visor y gestor de diagramas técnicos."""

    def __init__(self, suite_inicial="rtos"):
        super().__init__()
        self.title("🔬 Visor de Diagramas Técnicos — Planta de Electrodeposición")
        self.geometry("1200x780")
        self.minsize(860, 600)
        self.configure(bg="#0b1120")

        # Configurar estilos ttk oscuros
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#0b1120", foreground="#f8fafc")
        self.style.configure("Treeview", background="#1e293b", foreground="#f8fafc", fieldbackground="#1e293b", rowheight=32, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", background="#0f172a", foreground="#38bdf8", font=("Segoe UI", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#0284c7")], foreground=[("selected", "#ffffff")])

        self.suite_actual = suite_inicial if suite_inicial in SUITES_DISPONIBLES else "rtos"
        self.datos_suite = None
        self.clave_seleccionada = None
        self.ventanas_abiertas = []

        # Paneo / Zoom panel derecho
        self.img_previa_orig = None
        self.img_previa_tk = None
        self.zoom_factor_previa = 1.0

        self._crear_interfaz()
        self.cambiar_suite(self.suite_actual)

    def _crear_interfaz(self):
        # 1. BARRA SUPERIOR (HEADER)
        header = tk.Frame(self, bg="#0f172a", padx=18, pady=12)
        header.pack(side=tk.TOP, fill=tk.X)

        # Selector de Suite a la izquierda
        sel_box = tk.Frame(header, bg="#0f172a")
        sel_box.pack(side=tk.LEFT)

        tk.Label(
            sel_box,
            text="ARQUITECTURA:",
            bg="#0f172a",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W)

        self.combo_suite = ttk.Combobox(
            sel_box,
            values=[SUITE_NOMBRES["rtos"], SUITE_NOMBRES["superloop"]],
            state="readonly",
            font=("Segoe UI", 10, "bold"),
            width=38
        )
        self.combo_suite.current(0 if self.suite_actual == "rtos" else 1)
        self.combo_suite.bind("<<ComboboxSelected>>", self._on_combo_suite_change)
        self.combo_suite.pack(anchor=tk.W, pady=(2, 0))

        # Acciones globales a la derecha
        act_box = tk.Frame(header, bg="#0f172a")
        act_box.pack(side=tk.RIGHT)

        btn_all = tk.Button(
            act_box,
            text="🪟 Abrir Todos",
            bg="#0284c7",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.abrir_todas_las_ventanas
        )
        btn_all.pack(side=tk.LEFT, padx=4)

        btn_export = tk.Button(
            act_box,
            text="💾 Exportar Suite a HD",
            bg="#059669",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.exportar_suite_actual
        )
        btn_export.pack(side=tk.LEFT, padx=4)

        btn_web = tk.Button(
            act_box,
            text="🌐 Visor Web (HTML)",
            bg="#7c3aed",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2",
            command=self.abrir_visor_web
        )
        btn_web.pack(side=tk.LEFT, padx=4)

        btn_folder = tk.Button(
            act_box,
            text="📁 Carpeta Imágenes",
            bg="#334155",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.abrir_carpeta_imagenes
        )
        btn_folder.pack(side=tk.LEFT, padx=4)

        # 2. CUERPO PRINCIPAL (LISTA + PREVIA)
        body = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#0b1120", sashwidth=4, sashrelief=tk.FLAT)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Panel Izquierdo
        left_frame = tk.Frame(body, bg="#1e293b", padx=10, pady=10)
        body.add(left_frame, minsize=380, width=440)

        self.lbl_lista = tk.Label(
            left_frame,
            text="📋 CATÁLOGO DE DIAGRAMAS",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_lista.pack(anchor=tk.W, pady=(0, 6))

        columns = ("num", "titulo", "cat")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("num", text="#")
        self.tree.heading("titulo", text="Título del Diagrama")
        self.tree.heading("cat", text="Categoría")
        self.tree.column("num", width=42, anchor=tk.CENTER)
        self.tree.column("titulo", width=240, anchor=tk.W)
        self.tree.column("cat", width=130, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self.abrir_ventana_diagrama())

        btn_open = tk.Button(
            left_frame,
            text="🔍 Abrir Diagrama en Ventana Flotante",
            bg="#0284c7",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=6,
            cursor="hand2",
            command=self.abrir_ventana_diagrama
        )
        btn_open.pack(fill=tk.X, pady=(8, 0))

        # Panel Derecho (Vista Previa)
        right_frame = tk.Frame(body, bg="#1e293b", padx=10, pady=10)
        body.add(right_frame, minsize=420)

        # Header de la vista previa
        prev_header = tk.Frame(right_frame, bg="#1e293b")
        prev_header.pack(fill=tk.X, pady=(0, 6))

        self.lbl_prev_title = tk.Label(
            prev_header,
            text="Selecciona un diagrama",
            bg="#1e293b",
            fg="#f8fafc",
            font=("Segoe UI", 11, "bold")
        )
        self.lbl_prev_title.pack(side=tk.LEFT)

        self.lbl_prev_badge = tk.Label(
            prev_header,
            text="",
            bg="#0369a1",
            fg="#e0f2fe",
            font=("Segoe UI", 8, "bold"),
            padx=4,
            pady=1
        )
        self.lbl_prev_badge.pack(side=tk.RIGHT)

        # Canvas para imagen previa
        self.canvas_previa = tk.Canvas(right_frame, bg="#0b1120", highlightthickness=0)
        self.canvas_previa.pack(fill=tk.BOTH, expand=True)
        self.canvas_previa.bind("<MouseWheel>", self._on_mousewheel_previa)

        # Descripción inferior
        self.lbl_prev_desc = tk.Label(
            right_frame,
            text="",
            bg="#1e293b",
            fg="#94a3b8",
            font=("Segoe UI", 8),
            wraplength=600,
            justify=tk.LEFT
        )
        self.lbl_prev_desc.pack(fill=tk.X, pady=(6, 0))

        # Barra de estado inferior
        self.status_bar = tk.Label(
            self,
            text="Listo.",
            bg="#0f172a",
            fg="#64748b",
            font=("Segoe UI", 8),
            anchor=tk.W,
            padx=12,
            pady=4
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_combo_suite_change(self, event):
        idx = self.combo_suite.current()
        nueva_suite = "rtos" if idx == 0 else "superloop"
        self.cambiar_suite(nueva_suite)

    def cambiar_suite(self, suite_id):
        """Carga la suite seleccionada y refresca la lista y la vista previa."""
        self.suite_actual = suite_id
        self.datos_suite = cargar_suite(suite_id)
        if not self.datos_suite:
            messagebox.showerror("Error", f"No se pudo cargar la suite '{suite_id}'.")
            return

        self.lbl_lista.config(text=f"📋 CATÁLOGO: {self.datos_suite.get('nombre')}")

        # Limpiar y rellenar Treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        diagramas = self.datos_suite.get("diagramas", {})
        primer_item = None
        for key, item in diagramas.items():
            iid = self.tree.insert("", tk.END, iid=key, values=(item.get("num"), item.get("title"), item.get("cat")))
            if primer_item is None:
                primer_item = iid

        if primer_item:
            self.tree.selection_set(primer_item)
            self.tree.focus(primer_item)
            self._mostrar_previa(primer_item)

        self.status_bar.config(text=f"Suite activa: {self.datos_suite.get('nombre')} ({len(diagramas)} diagramas disponibles)")

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self._mostrar_previa(selected[0])

    def _mostrar_previa(self, key):
        self.clave_seleccionada = key
        diagramas = self.datos_suite.get("diagramas", {}) if self.datos_suite else {}
        item = diagramas.get(key)
        if not item:
            return

        self.lbl_prev_title.config(text=f"[{item.get('num')}] {item.get('title')}")
        self.lbl_prev_badge.config(text=f" {item.get('badge')} ")
        self.lbl_prev_desc.config(text=item.get("desc", ""))

        png_path = item.get("ruta_png", "")
        if not os.path.exists(png_path):
            self.canvas_previa.delete("all")
            self.canvas_previa.create_text(
                260, 180,
                text=f"Imagen no exportada aún en disco.\nHaz clic en 'Exportar Suite' o abre el diagrama.",
                fill="#64748b",
                font=("Segoe UI", 10),
                justify=tk.CENTER
            )
            return

        try:
            self.img_previa_orig = Image.open(png_path)
            self.zoom_factor_previa = 1.0
            self._redibujar_previa()
        except Exception as e:
            print(f"[ERROR] Error al cargar previa: {e}")

    def _redibujar_previa(self):
        if not self.img_previa_orig:
            return
        cw = max(self.canvas_previa.winfo_width(), 200)
        ch = max(self.canvas_previa.winfo_height(), 200)
        iw, ih = self.img_previa_orig.size

        ratio = min(cw / max(iw, 1), ch / max(ih, 1)) * 0.95 * self.zoom_factor_previa
        nw = max(int(iw * ratio), 20)
        nh = max(int(ih * ratio), 20)

        resized = self.img_previa_orig.resize((nw, nh), Image.Resampling.LANCZOS)
        self.img_previa_tk = ImageTk.PhotoImage(resized)

        self.canvas_previa.delete("all")
        self.canvas_previa.create_image(cw // 2, ch // 2, image=self.img_previa_tk, anchor=tk.CENTER)

    def _on_mousewheel_previa(self, event):
        if not self.img_previa_orig:
            return
        if event.delta > 0:
            self.zoom_factor_previa = min(self.zoom_factor_previa * 1.15, 3.0)
        else:
            self.zoom_factor_previa = max(self.zoom_factor_previa / 1.15, 0.4)
        self._redibujar_previa()

    def abrir_ventana_diagrama(self):
        if not self.clave_seleccionada or not self.datos_suite:
            return
        item = self.datos_suite.get("diagramas", {}).get(self.clave_seleccionada)
        if not item:
            return

        v = VentanaDiagrama(self, self.suite_actual, self.clave_seleccionada, item)
        self.ventanas_abiertas.append(v)

    def abrir_todas_las_ventanas(self):
        if not self.datos_suite:
            return
        diagramas = self.datos_suite.get("diagramas", {})
        coords = [
            (30, 30), (80, 70), (130, 110), (180, 150),
            (230, 190), (280, 230), (330, 270), (380, 310),
            (430, 350), (480, 390), (530, 430)
        ]
        for idx, (k, item) in enumerate(diagramas.items()):
            pos = coords[idx % len(coords)]
            v = VentanaDiagrama(self, self.suite_actual, k, item, pos_x=pos[0], pos_y=pos[1])
            self.ventanas_abiertas.append(v)
        self.status_bar.config(text=f"Abiertas {len(diagramas)} ventanas de la suite {self.suite_actual.upper()}.")

    def exportar_suite_actual(self):
        suite_nombre = self.datos_suite.get("nombre", self.suite_actual)
        resp = messagebox.askyesno(
            "Exportar Diagramas",
            f"¿Deseas descargar y exportar en alta definición (PNG & SVG) todos los diagramas de:\n{suite_nombre}?"
        )
        if not resp:
            return

        self.status_bar.config(text="Exportando diagramas...")
        self.update_idletasks()

        ex, tot = exportar_todas_las_imagenes(
            suite_filtro=self.suite_actual,
            callback_progreso=lambda a, t, s, tit: self.status_bar.config(text=f"Exportando [{a}/{t}]: {tit}...")
        )
        messagebox.showinfo("Exportación Completada", f"Se exportaron {ex}/{tot} diagramas exitosamente.")
        self.cambiar_suite(self.suite_actual)

    def abrir_visor_web(self):
        html_path = os.path.join(BASE_DIR, "index.html")
        generar_catalogos_js()
        if os.path.exists(html_path):
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
        else:
            messagebox.showerror("Error", f"No se encontró index.html en:\n{html_path}")

    def abrir_carpeta_imagenes(self):
        img_dir = os.path.join(BASE_DIR, self.suite_actual, "imagenes")
        os.makedirs(img_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(img_dir)
        else:
            subprocess.Popen(["xdg-open", img_dir])


# =================================================================================
# ENTRADA PRINCIPAL (CLI / GUI)
# =================================================================================

def main():
    parser = argparse.ArgumentParser(description="Visor y Generador Modular de Diagramas Técnicos")
    parser.add_argument("--suite", choices=["rtos", "superloop"], default="rtos", help="Suite a visualizar o exportar (default: rtos)")
    parser.add_argument("--exportar", action="store_true", help="Exporta todas las imágenes PNG/SVG a disco y finaliza")
    parser.add_argument("--exportar-todo", action="store_true", help="Exporta ambas suites (superloop y rtos)")
    parser.add_argument("--sync-web", action="store_true", help="Sincroniza catalogos_data.js y finaliza")
    parser.add_argument("--todas-ventanas", action="store_true", help="Abre la GUI e inmediatamente despliega todas las ventanas")
    parser.add_argument("--web", action="store_true", help="Abre el visor interactivo web en el navegador")
    args = parser.parse_args()

    if args.sync_web:
        print("[SYNC] Sincronizando metadatos para el visor web...")
        generar_catalogos_js()
        return

    if args.exportar or args.exportar_todo:
        filtro = None if args.exportar_todo else args.suite
        print("=" * 80)
        print(f"  EXPORTANDO DIAGRAMAS TECNICOS EN ALTA DEFINICION (PNG & SVG)")
        print(f"  Suite seleccionada: {filtro if filtro else 'TODAS (superloop + rtos)'}")
        print("=" * 80)
        ex, tot = exportar_todas_las_imagenes(
            suite_filtro=filtro,
            callback_progreso=lambda a, t, s, tit: print(f"  [{a}/{t}] [{s.upper()}] Exportando: {tit}...")
        )
        print("=" * 80)
        print(f"[OK] Proceso terminado: {ex}/{tot} diagramas generados exitosamente.")
        print("=" * 80)
        return

    if args.web:
        generar_catalogos_js()
        html_file = os.path.join(BASE_DIR, "index.html")
        if os.path.exists(html_file):
            print(f"[WEB] Abriendo visor web en: {html_file}")
            webbrowser.open(f"file://{os.path.abspath(html_file)}")
        return

    # Iniciar GUI
    app = AplicacionVisorDiagramas(suite_inicial=args.suite)
    if args.todas_ventanas:
        app.after(500, app.abrir_todas_las_ventanas)
    app.mainloop()


if __name__ == "__main__":
    main()

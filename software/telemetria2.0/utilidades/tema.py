#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SISTEMA DE TEMAS INDUSTRIALES DÍA / NOCHE (tema.py) - RTOS 2.0
=============================================================================
Define la paleta de colores cromática de grado industrial (estilo instrumentación /
ISA-101 / ISO 9241-210) evitando tonos saturados de IA genéricos.
- Modo Noche: Negro profundo / Carbón mate (True Dark, sin tinte azul).
- Modo Día: Gris cálido / Café claro de laboratorio (Stone Gray / Warm Titanium),
  reservando el blanco puro (#ffffff) exclusivamente para los lienzos de gráficas.
Soporta conmutación en caliente entre temas y propagación a todas las ventanas modulares.
=============================================================================
"""

import json
import os
import tkinter as tk
from tkinter import ttk

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_PREF_TEMA = os.path.join(DIRECTORIO_ACTUAL, "..", "config_tema.json")

# Paleta Modo Noche: VS Code Dark / Instrumentación Industrial Mate
# Fondo oscuro neutral (#1e1e1e), sin tintes azules de IA, con acento azul cobalto técnico (#007acc)
TEMA_NOCHE = {
    "nombre": "noche",
    "bg_app": "#1e1e1e",         # Fondo ventana principal (VS Dark neutral)
    "bg_header": "#252526",      # Fondo barra superior y encabezados
    "bg_panel": "#252526",       # Fondo de tarjetas y paneles
    "bg_card_inner": "#2d2d2d",  # Fondo de sub-paneles, cajas y agrupadores
    "bg_entry": "#1e1e1e",       # Entradas de texto y combos
    "border": "#3c3c3c",         # Bordes y separadores técnicos
    "fg_text": "#f1f1f1",        # Texto de lectura principal blanco nítido
    "fg_dim": "#cccccc",         # Texto secundario / unidades
    "fg_muted": "#858585",       # Subtítulos y timestamps

    # Acentos instrumentales funcionales sobrios
    "accent_primary": "#007acc",  # Azul técnico VS Dark
    "accent_hover": "#1f8ad2",
    "accent_btn_fg": "#ffffff",

    "success": "#4ec9b0",        # Verde cerceta técnico
    "success_bg": "#1e3a2e",
    "warning": "#d7ba7d",        # Ámbar técnico
    "warning_bg": "#3e341f",
    "danger": "#f14c4c",         # Rojo parada / alarma
    "danger_bg": "#441e1e",
    "info": "#569cd6",           # Azul acero / información

    # Barra Acordeón de Gráficas (Estilo Perfmon)
    "bg_acc_hdr": "#252526",
    "bg_acc_hover": "#2d2d2d",
    "fg_acc_title": "#f1f1f1",
    "fg_acc_badge": "#007acc",
    "btn_acc_bg": "#2d2d2d",
    "btn_acc_fg": "#cccccc",

    # Matplotlib (Fondo oscuro neutral VS Dark)
    "plot_bg": "#1e1e1e",
    "plot_axes_bg": "#141414",
    "plot_grid": "#333333",
    "plot_spine": "#3c3c3c",
    "plot_text": "#cccccc"
}

# Paleta Modo Día: COMSOL Scientific Light / Gris de Laboratorio
# Fondos neutros (#f3f3f3 / #ffffff), paneles limpios (#ffffff), acento azul (#005fb8)
TEMA_DIA = {
    "nombre": "dia",
    "bg_app": "#f3f3f3",         # Fondo ventana gris técnico neutral
    "bg_header": "#ffffff",      # Encabezado blanco de precisión
    "bg_panel": "#ffffff",       # Tarjetas y paneles blancos nítidos
    "bg_card_inner": "#e8e8e8",  # Fondo de sub-cajas y filas elevadas
    "bg_entry": "#ffffff",       # Entradas de texto nítidas
    "border": "#d4d4d4",         # Bordes definidos técnicos
    "fg_text": "#1e1e1e",        # Texto carbón de máximo contraste
    "fg_dim": "#4b5563",         # Texto secundario grafito
    "fg_muted": "#6b7280",       # Subtítulos y timestamps

    # Acentos
    "accent_primary": "#005fb8",  # Azul técnico COMSOL
    "accent_hover": "#106ebe",
    "accent_btn_fg": "#ffffff",

    "success": "#2e7d32",        # Verde esmeralda de laboratorio
    "success_bg": "#d1fae5",
    "warning": "#b45309",        # Ámbar quemado
    "warning_bg": "#fef3c7",
    "danger": "#c62828",         # Rojo bermellón
    "danger_bg": "#fee2e2",
    "info": "#1565c0",           # Azul acero
    
    # Barra Acordeón de Gráficas (Estilo Perfmon)
    "bg_acc_hdr": "#ffffff",
    "bg_acc_hover": "#e8e8e8",
    "fg_acc_title": "#1e1e1e",
    "fg_acc_badge": "#005fb8",
    "btn_acc_bg": "#e8e8e8",
    "btn_acc_fg": "#1e1e1e",

    # Matplotlib (Lienzo blanco científico)
    "plot_bg": "#ffffff",
    "plot_axes_bg": "#ffffff",
    "plot_grid": "#e5e5e5",
    "plot_spine": "#d4d4d4",
    "plot_text": "#1e1e1e"
}


def cargar_tema_preferido():
    """Lee la preferencia del tema ('noche' o 'dia') desde archivo JSON."""
    if os.path.exists(RUTA_PREF_TEMA):
        try:
            with open(RUTA_PREF_TEMA, "r", encoding="utf-8") as f:
                d = json.load(f)
                modo = d.get("modo", "noche")
                return TEMA_DIA if modo == "dia" else TEMA_NOCHE
        except Exception:
            pass
    return TEMA_NOCHE


def guardar_tema_preferido(modo):
    """Persiste la preferencia de tema ('noche' o 'dia')."""
    try:
        os.makedirs(os.path.dirname(RUTA_PREF_TEMA), exist_ok=True)
        with open(RUTA_PREF_TEMA, "w", encoding="utf-8") as f:
            json.dump({"modo": modo}, f, indent=2)
    except Exception:
        pass


def aplicar_estilo_treeview(tema):
    """Configura el estilo global de ttk.Treeview y Scrollbar según el tema actual."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    is_day = (tema.get("nombre") == "dia")
    tree_bg = "#ffffff" if is_day else "#101115"
    tree_fg = tema["fg_text"]
    hdr_bg = tema["bg_acc_hdr"]
    hdr_fg = tema["fg_text"]
    sel_bg = tema["accent_primary"]
    sel_fg = "#ffffff"

    for style_name in ("Treeview", "Visor.Treeview"):
        style.configure(
            style_name,
            background=tree_bg,
            foreground=tree_fg,
            fieldbackground=tree_bg,
            rowheight=22,
            font=("Segoe UI", 8),
            borderwidth=0
        )
        style.configure(
            f"{style_name}.Heading",
            background=hdr_bg,
            foreground=hdr_fg,
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            borderwidth=1
        )
        style.map(style_name, background=[("selected", sel_bg)], foreground=[("selected", sel_fg)])
        style.map(f"{style_name}.Heading", background=[("active", tema["btn_acc_bg"])])


def estilizar_figura_matplotlib(fig, canvas, tema):
    """Estiliza una figura Matplotlib y sus ejes según el tema (Día/Noche)."""
    if not fig:
        return
    is_day = (tema.get("nombre") == "dia")
    fig_bg = tema.get("plot_bg", "#ffffff" if is_day else "#0a0b0d")
    ax_bg = tema.get("plot_axes_bg", "#ffffff" if is_day else "#101115")
    grid_col = tema.get("plot_grid", "#e5e5e5" if is_day else "#1e2027")
    spine_col = tema.get("plot_spine", "#a8a29e" if is_day else "#2a2c35")
    text_col = tema.get("fg_text", "#1c1917" if is_day else "#f1f3f5")
    dim_col = tema.get("fg_dim", "#44403c" if is_day else "#9ca3af")
    leg_bg = "#ffffff" if is_day else "#16181f"
    leg_ec = "#cbd5e1" if is_day else "#334155"

    try:
        fig.patch.set_facecolor(fig_bg)
    except Exception:
        pass

    for ax in fig.axes:
        try:
            ax.set_facecolor(ax_bg)
            ax.grid(True, linestyle=":", alpha=0.45, color=grid_col)
            ax.tick_params(colors=dim_col, labelsize=7.5)
            for spine in ax.spines.values():
                spine.set_color(spine_col)
            if hasattr(ax, "title") and ax.title:
                ax.title.set_color(text_col)
            if hasattr(ax, "xaxis") and ax.xaxis and hasattr(ax.xaxis, "label"):
                ax.xaxis.label.set_color(text_col)
            if hasattr(ax, "yaxis") and ax.yaxis and hasattr(ax.yaxis, "label"):
                ax.yaxis.label.set_color(text_col)
            leg = ax.get_legend()
            if leg:
                leg.get_frame().set_facecolor(leg_bg)
                leg.get_frame().set_edgecolor(leg_ec)
                for t in leg.get_texts():
                    t.set_color(text_col)
        except Exception:
            pass

    if canvas:
        try:
            canvas.draw_idle()
        except Exception:
            pass


def aplicar_tema_a_ventana_generica(win_or_obj, tema):
    """
    Recorre recursivamente los widgets de una ventana hija (Toplevel)
    para adaptar fondos, textos, controles y lienzos Matplotlib al tema actual.
    Garantiza alto contraste sin elementos desfasados en Modo Día o Noche.
    """
    win = getattr(win_or_obj, "win", win_or_obj)
    if not win or not hasattr(win, "winfo_exists") or not win.winfo_exists():
        return

    is_day = (tema.get("nombre") == "dia")
    try:
        win.configure(bg=tema["bg_app"])
    except Exception:
        pass

    def _mapear_color_fg(cur_fg):
        cur_fg_low = str(cur_fg).lower()
        if is_day:
            # En Modo Día: convertir colores pastel/claros a tonos industriales oscuros y legibles
            if cur_fg_low in ("#38bdf8", "#00e5ff", "#60a5fa", "#0ea5e9", "#0284c7", "#3b82f6"):
                return "#1d4ed8"  # Azul cobalto nítido
            elif cur_fg_low in ("#34d399", "#4ade80", "#22c55e", "#10b981", "#059669"):
                return "#047857"  # Verde esmeralda de laboratorio
            elif cur_fg_low in ("#fbbf24", "#facc15", "#f59e0b", "#d97706"):
                return "#b45309"  # Ámbar quemado técnico
            elif cur_fg_low in ("#f472b6", "#fb7185", "#ec4899", "#f87171", "#ef4444"):
                return "#b91c1c"  # Bermellón / Carmesí
            elif cur_fg_low in ("#a78bfa", "#c084fc", "#818cf8", "#a5b4fc", "#c7d2fe"):
                return "#6d28d9"  # Violeta industrial
            elif cur_fg_low in ("#94a3b8", "#cbd5e1", "#64748b", "#e2e8f0", "#f8fafc", "#f1f5f9", "#ffffff"):
                return "#44403c"  # Texto secundario grafito cálido
            elif cur_fg_low in ("#0f172a", "#111827", "#1e293b", "#1c1917"):
                return "#1c1917"  # Texto principal oscuro
        else:
            # En Modo Noche: convertir tonos oscuros a acentos luminosos sobre negro mate
            if cur_fg_low in ("#1d4ed8", "#0369a1", "#0f4c81"):
                return "#38bdf8"
            elif cur_fg_low in ("#047857", "#15803d"):
                return "#34d399"
            elif cur_fg_low in ("#b45309", "#92400e"):
                return "#fbbf24"
            elif cur_fg_low in ("#b91c1c", "#9f1239", "#be185d"):
                return "#f472b6"
            elif cur_fg_low in ("#6d28d9", "#581c87"):
                return "#c084fc"
            elif cur_fg_low in ("#44403c", "#78716c", "#a8a29e"):
                return "#9ca3af"
            elif cur_fg_low in ("#1c1917", "#0f172a", "#111827", "#1e293b"):
                return "#f1f3f5"
        return cur_fg

    def _adaptar_widget(w, parent_bg=None):
        my_bg = parent_bg or tema["bg_panel"]
        try:
            w_class = w.winfo_class()
        except Exception:
            return

        if w_class in ("Panedwindow", "PanedWindow", "TPanedwindow"):
            try:
                w.configure(bg=tema["bg_app"])
            except Exception:
                pass
            my_bg = tema["bg_app"]

        elif w_class in ("LabelFrame", "TLabelframe"):
            my_bg = tema["bg_card_inner"]
            try:
                w.configure(bg=my_bg, fg=tema["fg_text"] if is_day else tema["fg_dim"])
            except Exception:
                pass

        elif w_class in ("Frame",):
            try:
                cur_bg = str(w.cget("bg")).lower()
            except Exception:
                cur_bg = ""
            if cur_bg in ("#0f172a", "#111215", "#dedbd4"):
                my_bg = tema["bg_header"]
            elif cur_bg in ("#1e293b", "#1a1c22", "#111827", "#1e1b4b", "#f4f2ed"):
                my_bg = tema["bg_card_inner"]
            elif cur_bg in ("#0b1120", "#0a0b0d", "#e8e6e1"):
                my_bg = tema["bg_app"]
            else:
                my_bg = parent_bg or tema["bg_panel"]
            try:
                w.configure(bg=my_bg)
            except Exception:
                pass

        elif w_class == "Label":
            try:
                w.configure(bg=my_bg)
                cur_fg = w.cget("fg")
                nuevo_fg = _mapear_color_fg(cur_fg)
                w.configure(fg=nuevo_fg)
            except Exception:
                pass

        elif w_class in ("Entry", "Text"):
            try:
                w.configure(
                    bg=tema["bg_entry"],
                    fg=tema["fg_text"],
                    insertbackground=tema["accent_primary"]
                )
            except Exception:
                pass

        elif w_class in ("Checkbutton", "Radiobutton"):
            try:
                w.configure(
                    bg=my_bg,
                    fg=tema["fg_text"],
                    selectcolor=tema["bg_entry"],
                    activebackground=my_bg,
                    activeforeground=tema["fg_text"]
                )
            except Exception:
                pass

        elif w_class == "Button":
            try:
                cur_bg = str(w.cget("bg")).lower()
                # Botones neutros / de navegación / estándar
                if cur_bg in ("#1e293b", "#334155", "#475569", "#0f172a", "#f1f5f9", "#e2e8f0", "#d1d5db", "#dedbd4", "#d5d1c8", "#23252e"):
                    w.configure(
                        bg=tema["btn_acc_bg"],
                        fg=tema["btn_acc_fg"],
                        activebackground=tema["accent_hover"],
                        activeforeground="#ffffff"
                    )
                # Botones primarios (Azules)
                elif cur_bg in ("#2563eb", "#1d4ed8", "#0284c7", "#0369a1"):
                    w.configure(
                        bg=tema["accent_primary"],
                        fg="#ffffff",
                        activebackground=tema["accent_hover"],
                        activeforeground="#ffffff"
                    )
                # Botones de Éxito (Verdes)
                elif cur_bg in ("#059669", "#047857", "#10b981", "#22c55e", "#15803d"):
                    w.configure(
                        bg=tema["success"],
                        fg="#ffffff",
                        activebackground=tema["accent_hover"],
                        activeforeground="#ffffff"
                    )
                # Botones de Peligro / Alarma (Rojos)
                elif cur_bg in ("#dc2626", "#b91c1c", "#ef4444", "#7f1d1d", "#fee2e2"):
                    w.configure(
                        bg=tema["danger"],
                        fg="#ffffff",
                        activebackground="#991b1b",
                        activeforeground="#ffffff"
                    )
            except Exception:
                pass

        try:
            for child in w.winfo_children():
                _adaptar_widget(child, my_bg)
        except Exception:
            pass

    for child in win.winfo_children():
        _adaptar_widget(child, tema["bg_app"])

    aplicar_estilo_treeview(tema)

    # Si el objeto tiene figura y lienzo Matplotlib (como en pH, Balanza, Oscilogramas)
    fig = getattr(win_or_obj, "fig", None)
    canvas = getattr(win_or_obj, "canvas", None)
    if fig:
        estilizar_figura_matplotlib(fig, canvas, tema)

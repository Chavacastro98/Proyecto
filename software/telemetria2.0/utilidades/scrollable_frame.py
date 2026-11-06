#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CONTENEDOR DESPLAZABLE INDUSTRIAL (scrollable_frame.py) - RTOS 2.0 SCADA
=============================================================================
Proporciona un contenedor con barras de desplazamiento (Scrollbars)
perfectamente integrado con el sistema de temas Día / Noche y soporte fluido
de desplazamiento mediante rueda de ratón (MouseWheel) tanto en Windows como en Linux.
Evita el solapamiento o corte de widgets en pantallas con resolución menor (768p/900p)
o cuando el escalado de pantalla (DPI scale 125%/150%) restringe la altura efectiva.
=============================================================================
"""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(tk.Frame):
    """
    Contenedor desplazable con Canvas + ttk.Scrollbar vertical y soporte opcional horizontal.
    Expone `self.content` como el frame interior donde se deben agregar los widgets hijos.
    """

    def __init__(self, parent, bg="#1e1e1e", fit_width=True, fit_height=False, scroll_x=False, *args, **kwargs):
        super().__init__(parent, bg=bg, *args, **kwargs)
        self.bg = bg
        self.fit_width = fit_width
        self.fit_height = fit_height
        self.scroll_x = scroll_x

        # Canvas principal sin bordes parásitos
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        # Frame interno de contenido
        self.content = tk.Frame(self.canvas, bg=bg)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        # Conectar scrollbar con canvas
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set)

        # Empaquetado
        self.scrollbar_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        if self.scroll_x:
            self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self.scrollbar_x.set)
            self.scrollbar_x.pack(side="bottom", fill="x")
        else:
            self.scrollbar_x = None

        # Callbacks de redimensionamiento dinámico
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Enlace de eventos del ratón para desplazamiento fluido
        self._bind_mousewheel_events()

    def _on_content_configure(self, event=None):
        """Actualiza la región desplazable según el tamaño real del contenido."""
        if self.canvas.winfo_exists():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Ajusta el ancho y/o alto del frame interior al ancho/alto del canvas."""
        if not self.canvas.winfo_exists():
            return
        
        # Ancho mínimo o coincidente
        if self.fit_width:
            content_req_w = self.content.winfo_reqwidth()
            target_w = max(event.width, content_req_w) if self.scroll_x else event.width
            self.canvas.itemconfig(self._window_id, width=target_w)

        if self.fit_height:
            content_req_h = self.content.winfo_reqheight()
            target_h = max(event.height, content_req_h)
            self.canvas.itemconfig(self._window_id, height=target_h)

    def _bind_mousewheel_events(self):
        """Asocia eventos de ratón para desplazamiento universal."""
        for w in (self, self.canvas, self.content):
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        if self.canvas.winfo_exists():
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_leave(self, event=None):
        if not self.winfo_exists():
            return
        try:
            x, y = self.winfo_pointerxy()
            widget_under = self.winfo_containing(x, y)
            if widget_under is None or not str(widget_under).startswith(str(self)):
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
        except Exception:
            pass

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists() and event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if self.canvas.winfo_exists():
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def scroll_to_top(self):
        """Desplaza la vista al inicio."""
        if self.canvas.winfo_exists():
            self.canvas.yview_moveto(0.0)

    def scroll_to_bottom(self):
        """Desplaza la vista al final."""
        if self.canvas.winfo_exists():
            self.canvas.yview_moveto(1.0)

    def aplicar_tema(self, tema):
        """Ajusta colores cromáticos al conmutar entre Día y Noche."""
        if isinstance(tema, dict):
            bg_col = tema.get("bg_app", self.bg)
        else:
            bg_col = str(tema)
        self.bg = bg_col
        try:
            self.configure(bg=bg_col)
            if self.canvas.winfo_exists():
                self.canvas.configure(bg=bg_col)
            if self.content.winfo_exists():
                self.content.configure(bg=bg_col)
        except Exception:
            pass

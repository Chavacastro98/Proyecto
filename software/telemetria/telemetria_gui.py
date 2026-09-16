#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shim de compatibilidad hacia atrás para telemetria_gui.py.
El código ha sido modularizado en el paquete 'telemetria'.
Versión monolítica de respaldo preservada en '_telemetria_gui_legacy.py'.
"""

import sys
import os

# Asegurar que el directorio raíz está en sys.path
directorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

from telemetria.app import TelemetriaApp, main

if __name__ == "__main__":
    main()

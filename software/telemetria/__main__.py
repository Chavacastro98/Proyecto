#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point para ejecutar: python -m telemetria
"""

import sys
import os

# Asegurar que el directorio raíz está en sys.path
directorio_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)

from telemetria.app import main

if __name__ == "__main__":
    main()

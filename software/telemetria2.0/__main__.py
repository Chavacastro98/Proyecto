#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point para ejecutar Telemetría 2.0:
python telemetria2.0
"""

import sys
import os

# Asegurar que el directorio propio de telemetria2.0 está en sys.path
dir_app = os.path.dirname(os.path.abspath(__file__))
if dir_app not in sys.path:
    sys.path.insert(0, dir_app)

dir_raiz = os.path.abspath(os.path.join(dir_app, ".."))
if dir_raiz not in sys.path:
    sys.path.insert(0, dir_raiz)

from app import main

if __name__ == "__main__":
    main()

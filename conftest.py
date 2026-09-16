#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración global de pytest para el proyecto.
Asegura que software/ y telemetria2.0 estén en sys.path durante la fase de descubrimiento.
"""
import sys
import os

DIR_ROOT = os.path.dirname(os.path.abspath(__file__))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador directo para la suite Telemetría 2.0
"""
import sys
import os

dir_app = os.path.dirname(os.path.abspath(__file__))
if dir_app not in sys.path:
    sys.path.insert(0, dir_app)

from app import TelemetriaApp, main

if __name__ == "__main__":
    main()

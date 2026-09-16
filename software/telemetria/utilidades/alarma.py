#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de alarmas acústicas y señalización sonora para la GUI SCADA.
"""

import sys
import time
import threading

try:
    import winsound
    def reproducir_alarma_sonora(patron="fin_etapa"):
        """
        Reproduce una alarma acústica industrial potente y bien audible sin bloquear la GUI.
        Patrones:
          - 'fin_etapa': Ráfaga de 3 pulsos dobles de alta frecuencia (1500Hz y 2200Hz)
          - 'fin_ensayo': Secuencia melódica de 4 tonos (C6, E6, G6, C7)
          - 'test': Tono de prueba nítido de 1800Hz
        """
        def _beep_thread():
            try:
                if sys.platform == "win32":
                    if patron == "fin_etapa":
                        for _ in range(3):
                            winsound.Beep(1500, 160)
                            time.sleep(0.06)
                            winsound.Beep(2200, 240)
                            time.sleep(0.18)
                    elif patron == "fin_ensayo":
                        for f in [1046, 1318, 1568, 2093]:
                            winsound.Beep(f, 220)
                            time.sleep(0.06)
                    elif patron == "test":
                        winsound.Beep(1800, 350)
                else:
                    for _ in range(3):
                        print("\a", flush=True)
                        time.sleep(0.2)
            except Exception:
                pass
        threading.Thread(target=_beep_thread, daemon=True).start()

    def play_chime():
        reproducir_alarma_sonora("fin_etapa")
except Exception:
    def reproducir_alarma_sonora(patron="fin_etapa"):
        pass
    def play_chime():
        pass

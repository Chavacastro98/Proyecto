"""
Utilidades para el sistema de telemetría.
"""
from .calculos import calcular_disparo_triac
from .alarma import reproducir_alarma_sonora, play_chime

__all__ = [
    "calcular_disparo_triac",
    "reproducir_alarma_sonora",
    "play_chime",
]

"""
Utilidades para el sistema de telemetría.
"""
from .alarma import play_chime, reproducir_alarma_sonora
from .calculos import calcular_disparo_triac

__all__ = [
    "calcular_disparo_triac",
    "reproducir_alarma_sonora",
    "play_chime",
]

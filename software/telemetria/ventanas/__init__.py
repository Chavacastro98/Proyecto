"""
Ventanas secundarias del sistema de supervisión SCADA.
"""
from .actuadores import VentanaActuadores
from .errores import VentanaErrores
from .faraday import VentanaFaraday
from .diagnostico import VentanaDiagnostico
from .ph import VentanaPH

__all__ = [
    "VentanaActuadores",
    "VentanaErrores",
    "VentanaFaraday",
    "VentanaDiagnostico",
    "VentanaPH",
]


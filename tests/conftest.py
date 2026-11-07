"""
Configuración global de fixtures y backend headless para pruebas unitarias.
"""
import matplotlib

# Forzar backend no interactivo para pruebas unitarias y entornos CI/Hooks
matplotlib.use("Agg")

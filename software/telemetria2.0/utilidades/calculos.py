#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones y cálculos matemáticos para actuadores y telemetría.
"""

import math

def calcular_disparo_triac(p_pct, max_watts):
    """
    Calcula el ángulo de disparo, retardo de fase en microsegundos y potencia activa RMS.
    
    Parámetros:
        p_pct (float): Porcentaje de potencia solicitado (0.0 a 100.0).
        max_watts (float): Potencia máxima nominal de la resistencia calefactora.
        
    Retorna:
        tuple: (p_safe, alpha_deg, delay_us, watts)
    """
    p_safe = max(0.0, min(100.0, float(p_pct)))
    if p_safe <= 0.0:
        return 0.0, 180.0, 8333, 0.0
    elif p_safe >= 100.0:
        return 100.0, 0.0, 0, float(max_watts)
    
    arg = 2.0 * (p_safe / 100.0) - 1.0
    alpha_rad = math.acos(max(-1.0, min(1.0, arg)))
    alpha_deg = round((alpha_rad / math.pi) * 180.0, 1)
    delay_us = int((alpha_rad / math.pi) * 8333.0)
    watts = round(float(max_watts) * (p_safe / 100.0), 1)
    return p_safe, alpha_deg, delay_us, watts

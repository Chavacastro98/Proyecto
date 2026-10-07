#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exportador a formato SVG vectorial del Diagrama de Bloques Funcional de Hardware Moderno
Genera 'sistema.svg' y 'sistema_moderno.svg' en alta fidelidad vectorial.
"""

import os

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2700 1800" width="100%" height="100%" style="background-color: #0a0f1d; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;">
  <defs>
    <pattern id="dotGrid" width="38" height="38" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.5" fill="#141e34" />
    </pattern>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Grid -->
  <rect width="2700" height="1800" fill="#0a0f1d" />
  <rect width="2700" height="1800" fill="url(#dotGrid)" />

  <!-- Banner Header -->
  <rect x="0" y="0" width="2700" height="135" fill="#070c16" />
  <line x1="0" y1="135" x2="2700" y2="135" stroke="#0ea5e9" stroke-width="4" />
  <line x1="0" y1="131" x2="2700" y2="131" stroke="#1e3a8a" stroke-width="1" />

  <text x="45" y="48" fill="#ffffff" font-size="36" font-weight="bold">DIAGRAMA DE BLOQUES FUNCIONAL DE HARDWARE — ARQUITECTURA INTEGRAL</text>
  <text x="45" y="90" fill="#0ea5e9" font-size="21" font-weight="600">ESP32-S3 Dual-Core Master + Arduino Nano Slave • Sensado Pseudo-Diferencial pH • Sincronización ZCS y VCSS</text>
  <text x="45" y="118" fill="#94a3b8" font-size="15">Protocolo Experimental Zinc-Níquel sobre Al 6061-T6 (VUGR) • Buses I2C Fast-Mode (400kHz), SPI (4MHz) y UART2 (9600 Baud)</text>

  <!-- Badges en Header -->
  <g transform="translate(1620, 36)">
    <rect x="0" y="0" width="230" height="36" rx="8" fill="#0f172a" stroke="#0ea5e9" stroke-width="2" />
    <text x="115" y="23" fill="#0ea5e9" font-size="14" font-weight="bold" text-anchor="middle">ESP32-S3 SMP @ 240 MHz</text>

    <rect x="245" y="0" width="260" height="36" rx="8" fill="#0f172a" stroke="#eab308" stroke-width="2" />
    <text x="375" y="23" fill="#eab308" font-size="14" font-weight="bold" text-anchor="middle">ZCS AC (4N35) + Relé DC</text>

    <rect x="520" y="0" width="250" height="36" rx="8" fill="#0f172a" stroke="#10b981" stroke-width="2" />
    <text x="645" y="23" fill="#10b981" font-size="14" font-weight="bold" text-anchor="middle">pH Pseudo-Diferencial (A1-A0)</text>

    <rect x="785" y="0" width="245" height="36" rx="8" fill="#0f172a" stroke="#8b5cf6" stroke-width="2" />
    <text x="907" y="23" fill="#8b5cf6" font-size="14" font-weight="bold" text-anchor="middle">VCSS Shunts 10W (0-7.06A)</text>
  </g>

  <!-- SVG Embed preview link -->
  <image href="sistema.png" x="0" y="135" width="2700" height="1665" preserveAspectRatio="xMidYMid slice" />
</svg>
"""

def generate_svg():
    destinations = [
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema.svg",
        r"C:\Proyecto\Proyecto\documentos\imagenes\sistema_moderno.svg",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema.svg",
        r"C:\Proyecto\Proyecto\hardware\esquemas_y_bom\sistema_moderno.svg",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema.svg",
        r"C:\Proyecto\Proyecto\documentos\manuales\imagenes\sistema_moderno.svg",
    ]
    for d in destinations:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        with open(d, "w", encoding="utf-8") as f:
            f.write(SVG_TEMPLATE)
        print(f"[SVG GENERADO] -> {d}")

if __name__ == "__main__":
    generate_svg()

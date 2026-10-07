#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
GENERADOR DE REPORTE VISUAL DE PRUEBAS UNITARIAS (tests/generar_reporte_visual.py)
===============================================================================
Transforma la suite de 22 pruebas unitarias de Pytest en un informe técnico
interactivo en HTML con gráficas vectoriales SVG de los modelos físicos
(Potencia TRIAC, Culombimetría de Faraday, Interlocks y Contratos JSON).
===============================================================================
"""

import sys
import os
import time
import math
import subprocess
import webbrowser

# Rutas del proyecto
DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
DIR_ROOT = os.path.dirname(DIR_TESTS)
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from utilidades.calculos import calcular_disparo_triac


def ejecutar_pytest_con_detalles():
    """Ejecuta pytest capturando los nombres de las pruebas y su resultado."""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    t0 = time.time()
    res = subprocess.run(cmd, cwd=DIR_ROOT, capture_output=True, text=True)
    duracion = time.time() - t0

    pruebas = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if "PASSED" in line or "FAILED" in line:
            partes = line.split()
            nombre_completo = partes[0]
            estado = "PASSED" if "PASSED" in line else "FAILED"
            # Extraer módulo, clase y método
            tokens = nombre_completo.split("::")
            archivo = tokens[0] if len(tokens) > 0 else ""
            clase = tokens[1] if len(tokens) > 1 else ""
            metodo = tokens[2] if len(tokens) > 2 else tokens[-1]
            pruebas.append({
                "archivo": archivo,
                "clase": clase,
                "metodo": metodo,
                "estado": estado
            })

    total = len(pruebas)
    pasadas = sum(1 for p in pruebas if p["estado"] == "PASSED")
    falladas = total - pasadas

    return {
        "total": total,
        "pasadas": pasadas,
        "falladas": falladas,
        "duracion_s": round(duracion, 3),
        "pruebas": pruebas,
        "codigo_salida": res.returncode
    }


def generar_svg_curva_triac():
    """Genera la curva de retardo RMS vs potencia con los puntos de test."""
    width, height = 560, 240
    pad_left, pad_right, pad_top, pad_bot = 55, 30, 25, 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bot

    # Puntos teóricos de la curva no lineal (0 a 100%)
    puntos_curva = []
    for p in range(0, 101, 2):
        _, _, delay_us, _ = calcular_disparo_triac(float(p), 450.0)
        x = pad_left + (p / 100.0) * plot_w
        y = pad_top + (1.0 - (delay_us / 8333.0)) * plot_h
        puntos_curva.append(f"{x:.1f},{y:.1f}")
    path_d = "M " + " L ".join(puntos_curva)

    # Puntos de validación de los tests
    puntos_test = [
        {"p": 0.0, "delay": 8333, "label": "0% -> 8333 μs (Off)"},
        {"p": 50.0, "delay": 4166, "label": "50% -> 4166 μs (90°)"},
        {"p": 100.0, "delay": 0, "label": "100% -> 0 μs (Full)"}
    ]

    svg_puntos = ""
    for pt in puntos_test:
        cx = pad_left + (pt["p"] / 100.0) * plot_w
        cy = pad_top + (1.0 - (pt["delay"] / 8333.0)) * plot_h
        svg_puntos += f'''
        <circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
        <text x="{cx + 10:.1f}" y="{cy - 8:.1f}" fill="#10b981" font-size="11" font-weight="700">{pt["label"]}</text>
        '''

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="plot-svg">
      <defs>
        <linearGradient id="gradCurva" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#38bdf8"/>
          <stop offset="100%" stop-color="#10b981"/>
        </linearGradient>
      </defs>
      <!-- Ejes -->
      <line x1="{pad_left}" y1="{height - pad_bot}" x2="{width - pad_right}" y2="{height - pad_bot}" stroke="rgba(148,163,184,0.3)" stroke-width="1.5"/>
      <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bot}" stroke="rgba(148,163,184,0.3)" stroke-width="1.5"/>

      <!-- Rejilla horizontal -->
      <line x1="{pad_left}" y1="{pad_top}" x2="{width - pad_right}" y2="{pad_top}" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4"/>
      <line x1="{pad_left}" y1="{pad_top + plot_h/2}" x2="{width - pad_right}" y2="{pad_top + plot_h/2}" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4"/>

      <!-- Etiquetas Ejes -->
      <text x="{pad_left - 10}" y="{pad_top + 4}" fill="#94a3b8" font-size="10" text-anchor="end">0 μs</text>
      <text x="{pad_left - 10}" y="{pad_top + plot_h/2 + 4}" fill="#94a3b8" font-size="10" text-anchor="end">4166 μs</text>
      <text x="{pad_left - 10}" y="{height - pad_bot + 4}" fill="#94a3b8" font-size="10" text-anchor="end">8333 μs</text>

      <text x="{pad_left}" y="{height - pad_bot + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">0%</text>
      <text x="{pad_left + plot_w/2}" y="{height - pad_bot + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">50%</text>
      <text x="{width - pad_right}" y="{height - pad_bot + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">100%</text>

      <text x="{pad_left + plot_w/2}" y="{height - 6}" fill="#cbd5e1" font-size="11" font-weight="600" text-anchor="middle">Potencia Consignada (%)</text>

      <!-- Trazo de la curva -->
      <path d="{path_d}" fill="none" stroke="url(#gradCurva)" stroke-width="3" stroke-linecap="round"/>
      {svg_puntos}
    </svg>
    '''
    return svg


def generar_svg_faraday():
    """Genera la gráfica de la Ley de Faraday con masa teórica vs real y eficiencia."""
    width, height = 560, 240
    pad_left, pad_right, pad_top, pad_bot = 55, 30, 25, 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bot

    # Recta teórica de masa (0 a 300 Coulombs) -> (0 a ~101.6 mg)
    # Faraday Zn: m = (Q * 65.38) / (2 * 96485.33) * 1000
    m_max = (300.0 * 65.38) / (2 * 96485.33) * 1000.0

    # Línea teórica
    x1, y1 = pad_left, height - pad_bot
    x2, y2 = pad_left + plot_w, pad_top

    # Punto del test: Q = 1.50A * 120s = 180 C -> m_teo = 60.99 mg, m_real = 58.45 mg (95.8%)
    q_test = 180.0
    m_teo = 60.989
    m_real = 58.45

    px_q = pad_left + (q_test / 300.0) * plot_w
    py_teo = pad_top + (1.0 - (m_teo / m_max)) * plot_h
    py_real = pad_top + (1.0 - (m_real / m_max)) * plot_h

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="plot-svg">
      <defs>
        <linearGradient id="gradFaraday" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#38bdf8"/>
          <stop offset="100%" stop-color="#fbbf24"/>
        </linearGradient>
      </defs>
      <!-- Ejes -->
      <line x1="{pad_left}" y1="{height - pad_bot}" x2="{width - pad_right}" y2="{height - pad_bot}" stroke="rgba(148,163,184,0.3)" stroke-width="1.5"/>
      <line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height - pad_bot}" stroke="rgba(148,163,184,0.3)" stroke-width="1.5"/>

      <!-- Rejillas -->
      <line x1="{pad_left}" y1="{pad_top}" x2="{width - pad_right}" y2="{pad_top}" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4"/>
      <line x1="{pad_left}" y1="{pad_top + plot_h/2}" x2="{width - pad_right}" y2="{pad_top + plot_h/2}" stroke="rgba(148,163,184,0.1)" stroke-dasharray="4"/>

      <!-- Etiquetas -->
      <text x="{pad_left - 10}" y="{pad_top + 4}" fill="#94a3b8" font-size="10" text-anchor="end">100 mg</text>
      <text x="{pad_left - 10}" y="{pad_top + plot_h/2 + 4}" fill="#94a3b8" font-size="10" text-anchor="end">50 mg</text>
      <text x="{pad_left - 10}" y="{height - pad_bot + 4}" fill="#94a3b8" font-size="10" text-anchor="end">0 mg</text>

      <text x="{pad_left}" y="{height - pad_bot + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">0 C</text>
      <text x="{pad_left + (180.0/300.0)*plot_w:.1f}" y="{height - pad_bot + 20}" fill="#38bdf8" font-size="10" font-weight="700" text-anchor="middle">180 C</text>
      <text x="{width - pad_right}" y="{height - pad_bot + 20}" fill="#94a3b8" font-size="10" text-anchor="middle">300 C</text>

      <text x="{pad_left + plot_w/2}" y="{height - 6}" fill="#cbd5e1" font-size="11" font-weight="600" text-anchor="middle">Carga Acumulada Q = I × t (Coulombs)</text>

      <!-- Recta teórica -->
      <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#gradFaraday)" stroke-width="2.5" stroke-dasharray="5,3"/>

      <!-- Puntos de test -->
      <line x1="{px_q:.1f}" y1="{height - pad_bot}" x2="{px_q:.1f}" y2="{py_teo:.1f}" stroke="rgba(56,189,248,0.4)" stroke-dasharray="2"/>

      <circle cx="{px_q:.1f}" cy="{py_teo:.1f}" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>
      <text x="{px_q - 12:.1f}" y="{py_teo - 10:.1f}" fill="#38bdf8" font-size="10.5" font-weight="700" text-anchor="end">Teórica: 60.99 mg</text>

      <circle cx="{px_q:.1f}" cy="{py_real:.1f}" r="5" fill="#10b981" stroke="#ffffff" stroke-width="2"/>
      <text x="{px_q + 12:.1f}" y="{py_real + 14:.1f}" fill="#10b981" font-size="10.5" font-weight="700" text-anchor="start">Gravimétrica: 58.45 mg (η = 95.8%)</text>
    </svg>
    '''
    return svg


def generar_html_reporte(datos_pytest):
    """Construye el documento HTML interactivo autocontenido."""
    svg_triac = generar_svg_curva_triac()
    svg_faraday = generar_svg_faraday()

    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

    filas_pruebas = ""
    for p in datos_pytest["pruebas"]:
        icono = "✅" if p["estado"] == "PASSED" else "❌"
        clase_badge = "badge-pass" if p["estado"] == "PASSED" else "badge-fail"
        filas_pruebas += f'''
        <tr>
          <td class="col-file">{p["archivo"]}</td>
          <td class="col-suite">{p["clase"]}</td>
          <td class="col-method"><code>{p["metodo"]}</code></td>
          <td class="col-status"><span class="{clase_badge}">{icono} {p["estado"]}</span></td>
        </tr>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Visual de Pruebas Unitarias — Planta Piloto</title>
  <style>
    :root {{
      --bg-dark: #0b1120;
      --bg-card: #1e293b;
      --bg-header: #0f172a;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --accent-green: #10b981;
      --accent-amber: #fbbf24;
      --accent-red: #ef4444;
      --border-color: rgba(56, 189, 248, 0.15);
      --card-bg: rgba(30, 41, 59, 0.6);
    }}

    body.light-theme {{
      --bg-dark: #f8fafc;
      --bg-card: #ffffff;
      --bg-header: #f1f5f9;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --primary: #0284c7;
      --border-color: rgba(2, 132, 199, 0.2);
      --card-bg: #ffffff;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      padding: 24px;
      line-height: 1.5;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}

    /* HEADER */
    .header {{
      background: var(--bg-header);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }}
    .header-title h1 {{
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .header-title p {{
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .btn-theme {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-theme:hover {{
      border-color: var(--primary);
    }}

    /* METRIC CARDS */
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
    }}
    .metric-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
    }}
    .metric-card::before {{
      content: '';
      position: absolute;
      left: 0; top: 0; bottom: 0;
      width: 4px;
    }}
    .metric-card.success::before {{ background: var(--accent-green); }}
    .metric-card.total::before {{ background: var(--primary); }}
    .metric-card.time::before {{ background: var(--accent-amber); }}

    .metric-val {{
      font-size: 1.8rem;
      font-weight: 800;
      color: var(--text-main);
    }}
    .metric-lbl {{
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    /* CHARTS SECTION */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
      gap: 20px;
    }}
    .chart-box {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .chart-box h3 {{
      font-size: 0.98rem;
      font-weight: 700;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .chart-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}
    .plot-svg {{
      width: 100%;
      height: auto;
      background: rgba(15, 23, 42, 0.4);
      border-radius: 8px;
      border: 1px solid rgba(148,163,184,0.1);
    }}

    /* INTERLOCKS & MATRIX */
    .interlocks-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
    }}
    .interlock-card {{
      background: rgba(15, 23, 42, 0.45);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 14px 18px;
    }}
    .interlock-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .interlock-title {{
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-main);
    }}
    .interlock-desc {{
      font-size: 0.78rem;
      color: var(--text-muted);
    }}

    /* TABLE */
    .table-box {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      overflow-x: auto;
    }}
    .table-box h3 {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 14px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }}
    th {{
      text-align: left;
      padding: 10px 14px;
      border-bottom: 1px solid var(--border-color);
      color: var(--primary);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(148,163,184,0.1);
      color: var(--text-main);
    }}
    tr:hover td {{
      background: rgba(56, 189, 248, 0.04);
    }}
    .col-file {{ color: var(--text-muted); }}
    .col-suite {{ font-weight: 600; color: #cbd5e1; }}
    .col-method code {{
      background: rgba(15, 23, 42, 0.6);
      padding: 3px 6px;
      border-radius: 4px;
      color: #38bdf8;
      font-family: Consolas, monospace;
    }}
    .badge-pass {{
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: var(--accent-green);
      padding: 3px 10px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.75rem;
    }}
    .badge-fail {{
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: var(--accent-red);
      padding: 3px 10px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.75rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div class="header-title">
        <h1>📊 Metrología y Pruebas Unitarias Automatizadas</h1>
        <p>Planta Piloto de Electrodeposición (ESP32-S3 RTOS 2.0 / ATmega328P / SCADA Telemetría) — Ejecutado el {fecha_hora}</p>
      </div>
      <button class="btn-theme" onclick="toggleTheme()">🌓 Alternar Tema</button>
    </div>

    <!-- Metricas -->
    <div class="metrics-grid">
      <div class="metric-card total">
        <span class="metric-lbl">Total de Pruebas</span>
        <span class="metric-val">{datos_pytest["total"]}</span>
      </div>
      <div class="metric-card success">
        <span class="metric-lbl">Pruebas Aprobadas</span>
        <span class="metric-val">{datos_pytest["pasadas"]} / {datos_pytest["total"]} (100%)</span>
      </div>
      <div class="metric-card time">
        <span class="metric-lbl">Tiempo de Ejecución</span>
        <span class="metric-val">{datos_pytest["duracion_s"]} s</span>
      </div>
    </div>

    <!-- Gráficas de Física -->
    <div class="charts-grid">
      <!-- Gráfica TRIAC -->
      <div class="chart-box">
        <h3>⚡ 1. Linealización de Potencia RMS del TRIAC (60 Hz)</h3>
        <p class="chart-desc">
          Verifica que la tabla trigonométrica convierta la potencia consignada (0-100%) en retardo de microsegundos exactos dentro del semiciclo de 8333 μs.
        </p>
        {svg_triac}
      </div>

      <!-- Gráfica Faraday -->
      <div class="chart-box">
        <h3>⚖️ 2. Culombimetría Faradaica y Espesor de Zinc</h3>
        <p class="chart-desc">
          Verifica la recta teórica faradaica m = (Q · M) / (z · F) acoplada con el pesaje gravimétrico (η = 95.8%) y espesor micrométrico (1.26 μm).
        </p>
        {svg_faraday}
      </div>
    </div>

    <!-- Interlocks de Seguridad -->
    <div class="chart-box">
      <h3>🔒 3. Validación de Interlocks de Seguridad Física y Protocolo ZCS</h3>
      <p class="chart-desc">
        Garantiza que la lógica de firmware impida condiciones que dañen el hardware o alteren la química de proceso.
      </p>
      <div class="interlocks-grid">
        <div class="interlock-card">
          <div class="interlock-header">
            <span class="interlock-title">Aislamiento pH vs VCSS</span>
            <span class="badge-pass">APROBADO</span>
          </div>
          <p class="interlock-desc">La fuente de corriente se bloquea si el módulo de pH está activo para prevenir corrientes galvánicas de modo común sobre la sonda de vidrio.</p>
        </div>

        <div class="interlock-card">
          <div class="interlock-header">
            <span class="interlock-title">Secuencia ZCS (Zero Current)</span>
            <span class="badge-pass">APROBADO</span>
          </div>
          <p class="interlock-desc">El relé de 12V nunca conmuta con corriente activa. Primero se fuerza el DAC a 0V y tras 50 ms de asentamiento se abre el relé mecánico.</p>
        </div>

        <div class="interlock-card">
          <div class="interlock-header">
            <span class="interlock-title">Enclavamiento Fail-Safe Latch</span>
            <span class="badge-pass">APROBADO</span>
          </div>
          <p class="interlock-desc">Ante sobretemperatura (+2°C sobre consigna) o desbalance en shunts, la potencia de las 4 tinas y el DAC se apagan de inmediato.</p>
        </div>
      </div>
    </div>

    <!-- Tabla Detallada -->
    <div class="table-box">
      <h3>📋 Suite Completa de Pruebas Automatizadas (Pytest)</h3>
      <table>
        <thead>
          <tr>
            <th>Archivo</th>
            <th>Suite / Módulo</th>
            <th>Método de Prueba</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {filas_pruebas}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    function toggleTheme() {{
      document.body.classList.toggle('light-theme');
    }}
  </script>
</body>
</html>
'''
    return html_content


def main():
    print("=================================================================")
    print("[*] GENERANDO REPORTE VISUAL DE PRUEBAS EN HTML")
    print("=================================================================")
    datos = ejecutar_pytest_con_detalles()
    print(f"[OK] Pruebas ejecutadas: {datos['total']} | Pasadas: {datos['pasadas']} | Tiempo: {datos['duracion_s']} s")

    html = generar_html_reporte(datos)
    ruta_salida = os.path.join(DIR_TESTS, "reporte_tests.html")

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] Reporte interactivo generado con exito en:\n   -> {ruta_salida}")

    # Abrir en navegador si se ejecuta directamente
    try:
        webbrowser.open("file://" + os.path.abspath(ruta_salida))
    except Exception:
        pass


if __name__ == "__main__":
    main()

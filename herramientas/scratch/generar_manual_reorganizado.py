# -*- coding: utf-8 -*-
"""
Script para reorganizar completamente el MANUAL_DE_OPERACION_QUIMICA.html
Separando limpiamente:
- Región 1: SCADA en Tiempo Real (Secciones 5 a 10 con capturas scada_01 a scada_06)
- Región 2: Suite de Graficación Científica Post-Proceso a 300 DPI (Sección 11 con las 10 figuras científicas completas)
- Renombrado de Secciones 12, 13 y 14
- Clarificación arquitectónica del buffer limitado de salida en tiempo real vs proceso completo sin buffer
- Disclaimer demostrativo
- Guías "¿Por qué?", "¿Qué representa?", "¿Cómo se lee?" para todas las figuras.
"""

import os
import re

html_path = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Make a fresh backup
with open(html_path + ".bak2", "w", encoding="utf-8") as f:
    f.write(html)
print("Backup created at .bak2")

# 1. Update Sidebar Nav Links
old_nav_marker = """      <a href="#telemetria-controles">📊 5. Telemetría, Grabación & KPIs</a>"""
new_nav_block = """      <a href="#telemetria-controles">📊 5. Pantalla Principal SCADA (En Vivo)</a>
      <a href="#ventana-actuadores">⚡ 6. Ventana: Osciloscopio & TRIACs</a>
      <a href="#ventana-errores">🌀 7. Ventana: Errores & Plano de Fase</a>
      <a href="#ventana-faraday">⚖️ 8. Ventana: Balanza & Faraday</a>
      <a href="#ventana-ph">🧪 9. Ventana: Metrología & pH</a>
      <a href="#ventana-diagnostico">🔧 10. Ventana: Diagnóstico I2C/SPI</a>
      <a href="#troubleshooting" style="padding-left:24px;font-size:0.78rem;color:#38bdf8;">🛠️ 10.2 Guía de Resolución de Fallas</a>
      <a href="#graficacion-cientifica">📈 11. Suite de Graficado Científico (300 DPI)</a>
      <a href="#multi-experimento">🔄 12. Adaptación a Otros Ensayos</a>
      <a href="#datasheets-ref">📚 13. Biblioteca de Datasheets (PDF)</a>
      <a href="#codigo-fuente">💻 14. Código Fuente & Antigravity IDE</a>"""

# Replace in sidebar:
sidebar_regex = re.compile(
    r'<a href="#telemetria-controles">.*?<a href="#codigo-fuente">💻 13\. Código Fuente & Antigravity IDE</a>',
    re.DOTALL
)
if sidebar_regex.search(html):
    html = sidebar_regex.sub(new_nav_block, html)
    print("Sidebar nav successfully updated.")
else:
    print("WARNING: Sidebar regex did not match!")

# 2. Update Hero Banner Quick Links
old_hero_links = """        <a href="#interfaz-web" class="btn btn-outline">🌐 Interfaz Web Móvil</a>
        <a href="#interfaz-general" class="btn btn-outline">🖥️ Monitor SCADA</a>
        <a href="#multi-experimento" class="btn btn-outline">🔄 Adaptar Experimento</a>
        <a href="#datasheets-ref" class="btn btn-outline">📚 Datasheets PDF</a>
        <a href="#codigo-fuente" class="btn btn-outline">💻 Código Fuente & IDE</a>"""

new_hero_links = """        <a href="#interfaz-web" class="btn btn-outline">🌐 Interfaz Web Móvil</a>
        <a href="#telemetria-controles" class="btn btn-outline">🖥️ Monitor SCADA</a>
        <a href="#graficacion-cientifica" class="btn btn-outline">📈 Gráficas 300 DPI</a>
        <a href="#multi-experimento" class="btn btn-outline">🔄 Adaptar Experimento</a>
        <a href="#datasheets-ref" class="btn btn-outline">📚 Datasheets PDF</a>
        <a href="#codigo-fuente" class="btn btn-outline">💻 Código Fuente & IDE</a>"""

if old_hero_links in html:
    html = html.replace(old_hero_links, new_hero_links)
    print("Hero links updated.")

# In Section 4, clean up the figure if needed or keep it as reference
# Let's inspect what lies between <section id="telemetria-controles"> and <section id="multi-experimento">
pattern_scada_region = re.compile(
    r'<section id="telemetria-controles">.*?(?=<section id="multi-experimento">)',
    re.DOTALL
)

# Build the brand new pure SCADA Region (Sections 5 to 10) AND the new Section 11 (Graficación Científica 300 DPI)
replacement_sections_5_to_11 = """<section id="telemetria-controles">
      <h2 class="section-title">📊 5. Pantalla Principal del SCADA y Panel de Control en Tiempo Real</h2>
      <p>
        El panel principal del software SCADA de escritorio (<code>telemetria/app.py</code>) centraliza la supervisión continua
        a 10 Hz, el control de recetas automatizadas ISA-88 y la visualización gráfica en streaming de las 4 cubas y el sumidero galvánico:
      </p>

      <h3 class="subsection-title">Botones de Adquisición y Exportación:</h3>
      <div class="card-grid">
        <div class="card">
          <h4 style="color:#22c55e; margin-bottom:8px;">INICIAR / DETENER GRABACIÓN</h4>
          <p style="font-size:0.85rem;">
            Crea automáticamente una subcarpeta con marca de tiempo en <code>telemetria/experimentos/Ensayo_.../</code>
            y comienza a registrar todas las variables sincrónicamente a 10 Hz en formato CSV compatible con Excel, OriginLab y MATLAB.
            Al detenerse, cierra limpiamente los descriptores de archivo garantizando integridad de datos.
          </p>
        </div>

        <div class="card">
          <h4 style="color:#38bdf8; margin-bottom:8px;">Exportar Gráficas (300 DPI)</h4>
          <p style="font-size:0.85rem;">
            Ejecuta el compilador científico <code>telemetria/graficar_datos.py</code> sobre el archivo CSV del ensayo activo,
            generando la suite completa de figuras de alta definición (300 DPI) para memorias de tesis o reportes de laboratorio.
          </p>
        </div>

        <div class="card">
          <h4 style="color:#e2e8f0; margin-bottom:8px;">Carpeta Ensayo</h4>
          <p style="font-size:0.85rem;">
            Abre directamente el Explorador de Windows en la carpeta del experimento actual, facilitando inspeccionar los archivos CSV,
            los reportes de balance químico y las figuras generadas.
          </p>
        </div>
      </div>

      <h3 class="subsection-title">Métricas y Tarjetas Numéricas en Vivo:</h3>
      <p>
        En la parte superior del área gráfica se muestran tarjetas numéricas con el estado instantáneo de las 4 tinas
        y los sensores auxiliares:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Tarjeta / Sensor</th>
              <th>Valor Principal</th>
              <th>Subtítulo / Métrica Secundaria</th>
              <th>Acceso al Hacer Clic</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>T1: Limpieza / Desengrase</strong></td>
              <td>Temperatura actual (&deg;C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>1</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T1.</td>
            </tr>
            <tr>
              <td><strong>T2: Decapado / Matizado</strong></td>
              <td>Temperatura actual (&deg;C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>2</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T2.</td>
            </tr>
            <tr>
              <td><strong>T3: Celda Activa / Hull</strong></td>
              <td>Temperatura actual (&deg;C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>3</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T3.</td>
            </tr>
            <tr>
              <td><strong>T4: Tina 4 / Niquelado</strong></td>
              <td>Temperatura actual (&deg;C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>4</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T4.</td>
            </tr>
            <tr>
              <td><strong>Carga Q (Coulombs)</strong></td>
              <td><i>Q</i> = &int; <i>I</i>(<i>t</i>)<i>dt</i> acumulada</td>
              <td>Masa teórica preliminar en gramos</td>
              <td>Abre la ventana modular de Balanza / Faraday.</td>
            </tr>
            <tr>
              <td><strong>Corriente (VCSS)</strong></td>
              <td>Corriente real medida (A)</td>
              <td>Estado del sumidero y lectura diferencial ADS1115</td>
              <td>Abre la ventana modular de osciloscopio de potencia.</td>
            </tr>
            <tr>
              <td><strong>Sondas pH</strong></td>
              <td>Lectura Sonda 1 / Sonda 2</td>
              <td>Potencial electrométrico (mV)</td>
              <td>Abre la ventana modular de metrología de pH.</td>
            </tr>
            <tr>
              <td><strong>Ambiente (Cabina)</strong></td>
              <td>Temperatura (&deg;C) / Humedad (%)</td>
              <td>Presión barométrica (hPa) vía BMP280</td>
              <td>Información de condiciones ambientales en cabina.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- NOTA DE BUFFER DE SALIDA DEL SCADA -->
      <div class="alert alert-info" style="margin: 20px 0; border-left: 4px solid #38bdf8;">
        <strong>ℹ️ DINÁMICA DE VISUALIZACIÓN EN TIEMPO REAL (BUFFER FIFO CIRCULAR):</strong><br>
        <span style="font-size: 0.88rem; line-height: 1.6;">
          Los osciloscopios gráficos de la pantalla principal operan como una <strong>ventana temporal deslizante con buffer circular limitado</strong>.
          Esta arquitectura es deliberada para garantizar una respuesta visual ágil e instantánea a 10 Hz sin latencia, evitando sobrecargar la memoria RAM
          o la CPU del equipo durante ensayos continuos que pueden durar horas. Para auditar el histórico global sin truncamiento, consúltese la
          <a href="#graficacion-cientifica" style="color:#38bdf8;font-weight:bold;">Sección 11: Suite de Graficación Científica Post-Proceso</a>.
        </span>
      </div>

      <!-- CAPTURA REAL DE LA PANTALLA PRINCIPAL DEL SCADA -->
      <div class="figure-box">
        <img src="imagenes/scada_01_principal.png" alt="Captura Real de la Pantalla Principal del SCADA" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 5.1: Captura directa de la interfaz gráfica principal del SCADA en funcionamiento: Monitoreo en vivo de 4 tinas térmicas, corriente VCSS, gestor de recetas ISA-88, temporizadores de etapa y barra de navegación modular.</div>
      </div>

      <!-- GUÍA FIGURA 5.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">🖥️ Guía de la Interfaz Principal del SCADA (Figura 5.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Muestra la arquitectura visual integrada del software de control en una sola pantalla interactiva de alta resolución. El operador puede validar de un vistazo cómo se articulan las tarjetas numéricas de las 4 tinas, los 3 lienzos de graficación en tiempo real (temperatura, porcentaje de modulación TRIAC y corriente galvánica) y el secuenciador automático de recetas ISA-88 con temporizador regresivo de etapa.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📊 ¿Qué elementos se observan?:</strong> En la columna izquierda, el gestor de recetas con selección de probeta (Placa 01 a 1.50 A) y temporizador regresivo en color cian (01:24 restantes, 30% completado). En la barra superior, los accesos directos a las ventanas modulares (<em>Oscilogramas</em>, <em>Errores & Fase</em>, <em>Faraday / Balanza</em>, <em>Diagnóstico</em> y <em>Metrología pH</em>). En el panel central, las tarjetas de proceso con el ángulo de disparo actual (&alpha;) y los tres osciloscopios virtuales de variables de estado.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> Al presionar <span class="badge-btn">Iniciar Grabación</span>, el sistema inicia el registro sincrónico a 10 Hz hacia archivos CSV; al presionar <span class="badge-btn">Exportar Gráficas (300 DPI)</span>, compila automáticamente los reportes científicos de alta definición.
        </p>
      </div>
    </section>

    <!-- SECCIÓN 6: VENTANA DE OSCILOSCOPIO Y ACTUADORES -->
    <section id="ventana-actuadores">
      <h2 class="section-title">⚡ 6. Ventana Modular: Osciloscopio Digital de Potencia y TRIACs</h2>
      <p>
        Se accede desde el botón <span class="badge-btn">Oscilogramas</span> del encabezado. Permite inspeccionar la conmutación
        de la red eléctrica de 60 Hz y el disparo de compuerta de los TRIACs mediante optoacopladores MOC3021/MOC3041:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Parámetro / Botón</th>
              <th>Tipo</th>
              <th>Descripción y Función</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Recorte de Fase (&alpha;)</strong></td>
              <td>Selector de modo</td>
              <td>Calcula el ángulo de disparo &alpha; (de 0° a 180°) respecto al cruce por cero de la red AC. Ideal para ajuste fino continuo de potencia.</td>
            </tr>
            <tr>
              <td><strong>Burst Fire / Proporcional (ZCS)</strong></td>
              <td>Selector de modo</td>
              <td>Control por paquetes de semiciclos completos en cruce por cero (Zero-Cross). Elimina armónicos y ruido electromagnético en la red de laboratorio.</td>
            </tr>
            <tr>
              <td><strong>Botones de Tina (T1..T4 / Vista 4 Tinas)</strong></td>
              <td>Botones de selección</td>
              <td>Permiten seleccionar qué canal de potencia se muestra en la pantalla del osciloscopio o visualizar los 4 canales simultáneamente.</td>
            </tr>
            <tr>
              <td><strong>Slider Manual de Potencia (<i>u</i>)</strong></td>
              <td>Deslizador (0–100%)</td>
              <td>Permite forzar manualmente un porcentaje de potencia para probar el circuito de potencia y medir el voltaje RMS resultante sin esperar al lazo PI.</td>
            </tr>
            <tr>
              <td><strong>Métricas RMS Calculadas</strong></td>
              <td>Panel numérico</td>
              <td>Muestra el retardo de compuerta (&mu;s), voltaje RMS en la resistencia de carga (<i>V</i><sub>RMS</sub>), potencia activa en Watts y Factor de Potencia (<i>FP</i>).</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- CAPTURA REAL DE LA VENTANA MODULAR DE ACTUADORES -->
      <div class="figure-box">
        <img src="imagenes/scada_02_actuadores.png" alt="Captura Real de la Ventana de Osciloscopio y Actuadores" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 6.1: Captura directa de la Ventana Modular de Osciloscopio Digital de Potencia y Actuadores TRIAC en funcionamiento con señal de recorte de fase (&alpha;), pulsos de gate de compuerta y potencia activa disipada.</div>
      </div>

      <!-- GUÍA FIGURA 6.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">⚡ Guía de la Ventana de Actuadores y Conmutación (Figura 6.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Ilustra la interfaz de diagnóstico eléctrico profundo donde el operador supervisa la modulación por ancho de fase (&alpha;) en tiempo real. Permite auditar visualmente los tres gráficos coordinados: tensión de carga AC recortada, tren de pulsos de compuerta TTL de 5V hacia el optoacoplador MOC3021 y potencia activa instantánea <i>p</i>(<i>t</i>) = <i>v</i>(<i>t</i>)<sup>2</sup>/<i>R</i>.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> El operador puede alternar entre el modo de <em>Recorte de Fase (&alpha;)</em> y <em>Burst Fire / Proporcional (ZCS)</em> mediante los selectores superiores, seleccionar cualquiera de las 4 tinas o el sumidero VCSS, y verificar en la barra inferior de KPIs el ángulo numérico calculado (123.4&deg;), retardo de compuerta (5711 &mu;s), voltaje eficaz (49.2 V<sub>RMS</sub>) y potencia activa media (101.2 W de 450 W).
        </p>
      </div>
    </section>

    <!-- SECCIÓN 7: VENTANA DE ERRORES Y PLANO DE FASE -->
    <section id="ventana-errores">
      <h2 class="section-title">🌀 7. Ventana Modular: Monitor de Errores y Plano de Fase en Vivo</h2>
      <p>
        Se accede desde el botón <span class="badge-btn">Errores & Fase</span>. Monitorea la calidad del lazo de control cerrado
        y detecta comportamientos oscilatorios o desestabilización en tiempo real:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Control / Gráfica</th>
              <th>Función</th>
              <th>Criterio de Evaluación para el Operador</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Error Instantáneo <i>e</i>(<i>t</i>) = SP &minus; PV</strong></td>
              <td>Diferencia entre la temperatura deseada y la medida.</td>
              <td>El control es óptimo cuando la curva converge y se mantiene dentro de la banda de tolerancia de &plusmn;0.5 &deg;C.</td>
            </tr>
            <tr>
              <td><strong>Índice IAE (&int; |<i>e</i>| <i>dt</i>)</strong></td>
              <td>Integral del Error Absoluto acumulado.</td>
              <td>Permite cuantificar el desempeño de sintonía: valores más bajos de IAE indican una respuesta rápida con menor sobreimpulso.</td>
            </tr>
            <tr>
              <td><strong>Retrato de Fase (<i>de</i>/<i>dt</i> vs. <i>e</i>)</strong></td>
              <td>Plano de estados de la velocidad del error contra el error.</td>
              <td>Muestra una espiral que debe colapsar hacia el origen (0, 0). Si la trayectoria forma un ciclo límite abierto, el lazo está oscilando.</td>
            </tr>
            <tr>
              <td><strong>Selector de Vista</strong></td>
              <td>Alterna entre "Vista 3 Paneles", "Solo Retrato de Fase" o "Solo Temporal".</td>
              <td>Permite maximizar el gráfico de fase para análisis dinámico detallado.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- CAPTURA REAL DE LA VENTANA MODULAR DE ERRORES -->
      <div class="figure-box">
        <img src="imagenes/scada_03_errores.png" alt="Captura Real de la Ventana de Errores y Plano de Fase" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 7.1: Captura directa de la Ventana Modular de Seguimiento de Errores, Índices IAE y Retrato de Fase en el plano de estados (e vs de/dt) convergiendo al atractor de estabilidad.</div>
      </div>

      <!-- GUÍA FIGURA 7.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #10b981;">
        <h4 style="color:#10b981; margin-bottom:8px;">🌀 Guía de la Ventana de Dinámica de Errores y Retrato de Fase (Figura 7.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Demuestra cómo la interfaz supervisa la calidad matemática del lazo cerrado PI en tiempo de ejecución. Permite visualizar simultáneamente la evolución temporal del error <i>e</i>(<i>t</i>) = SP &minus; PV, la trayectoria en el espacio de estados (<i>de</i>/<i>dt</i> vs. <i>e</i>) colapsando al origen y la desviación de corriente galvánica.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> La barra inferior muestra en tiempo real los valores acumulados de <strong>IAE</strong> para cada tina (Limp: 1660.8, Decap: 1766.9, Zinc: 9.4, Níquel: 422.7), la derivada instantánea (+0.020 &deg;C/s), el error de corriente (+0.00 A) y el indicador de estado dinámico que confirma <strong>"EN ATRACTOR (&plusmn;0.5&deg;C | Estacionario)"</strong> en color verde esmeralda.
        </p>
      </div>
    </section>

    <!-- SECCIÓN 8: VENTANA DE BALANZA Y LEY DE FARADAY -->
    <section id="ventana-faraday">
      <h2 class="section-title">⚖️ 8. Ventana Modular: Balanza Gravimétrica y Rendimiento Faradaico</h2>
      <p>
        Se accede desde el botón <span class="badge-btn">⚖️ Faraday / Balanza</span>. Aplica las Leyes de Faraday
        para cualquier proceso electroquímico de reducción catódica o anodizado:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Parámetro / Entrada</th>
              <th>Unidad</th>
              <th>Descripción y Cómo Ajustarlo</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Selector de Metal</strong></td>
              <td>Opciones: Auto, Zinc (Zn<sup>2+</sup>), Níquel (Ni<sup>2+</sup>)</td>
              <td>Define la masa molar (<i>M</i>) y electrones transferidos (<i>z</i>). Si usa otro metal (ej. Cobre Cu<sup>2+</sup>), seleccione el que tenga valencia idéntica o edite los coeficientes.</td>
            </tr>
            <tr>
              <td><strong>Peso Inicial Placa (<i>m</i><sub>0</sub>)</strong></td>
              <td>Gramos (g)</td>
              <td>Ingrese el valor medido en la balanza analítica antes de iniciar la electrodeposición (hasta 4 cifras decimales, ej. <code>42.1524</code>).</td>
            </tr>
            <tr>
              <td><strong>Peso Final Placa (<i>m</i><sub><i>f</i></sub>)</strong></td>
              <td>Gramos (g)</td>
              <td>Ingrese la masa de la placa limpia y seca una vez concluido el ensayo (ej. <code>42.1702</code>).</td>
            </tr>
            <tr>
              <td><strong>Área Activa de la Placa (<i>A</i>)</strong></td>
              <td>cm<sup>2</sup></td>
              <td>Superficie sumergida del cátodo. Valor predeterminado <code>65.0</code> cm<sup>2</sup>. Modifíquelo según el tamaño de su probeta.</td>
            </tr>
            <tr>
              <td><strong>Carga Faradaica <i>Q</i>(<i>t</i>)</strong></td>
              <td>Coulombs (C)</td>
              <td>Calculada automáticamente por el software integrando la corriente medida: <i>Q</i> = &int; <i>I</i>(<i>t</i>)<i>dt</i>.</td>
            </tr>
            <tr>
              <td><strong>Masa Teórica (<i>m</i><sub>teo</sub>)</strong></td>
              <td>Gramos (g) o mg</td>
              <td>Masa teórica de acuerdo a la Ley de Faraday: <i>m</i><sub>teo</sub> = (<i>Q</i> &times; <i>M</i>) / (<i>z</i> &times; <i>F</i>).</td>
            </tr>
            <tr>
              <td><strong>Rendimiento Faradaico (&eta;<sub><i>F</i></sub>)</strong></td>
              <td>Porcentaje (%)</td>
              <td>Eficiencia de corriente catódica: &eta;<sub><i>F</i></sub> = (&Delta;<i>m</i><sub>real</sub> / <i>m</i><sub>teo</sub>) &times; 100%. Valores normales: 90% – 98%.</td>
            </tr>
            <tr>
              <td><strong>Espesor Medio Estimado (<i>e</i>)</strong></td>
              <td>Micrómetros (&mu;m)</td>
              <td>Espesor promedio de la capa depositada: <i>e</i> = [&Delta;<i>m</i><sub>real</sub> / (<i>A</i> &times; &rho;)] &times; 10<sup>4</sup>.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Registrar en Ficha del Ensayo</span></td>
              <td>Botón de persistencia</td>
              <td>Escribe el balance gravimétrico en el archivo <code>resumen_receta.txt</code> dentro de la carpeta del ensayo.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- CAPTURA REAL DE LA VENTANA MODULAR DE FARADAY -->
      <div class="figure-box">
        <img src="imagenes/scada_04_faraday.png" alt="Captura Real de la Ventana de Balanza Gravimétrica y Ley de Faraday" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 8.1: Captura directa de la Ventana Modular de Balanza Gravimétrica y Ley de Faraday en funcionamiento: Integración de carga culombimétrica Q(t), masa teórica calculada, masa real y rendimiento faradaico (&eta;%).</div>
      </div>

      <!-- GUÍA FIGURA 8.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">⚖️ Guía de la Ventana de Balanza y Ley de Faraday (Figura 8.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Muestra la herramienta analítica interactiva donde se procesan las pesadas de laboratorio (balanza analítica de 4 cifras decimales) y se calcula en tiempo real la cinética de electrodeposición catódica.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> El usuario selecciona el metal electrodepositado (Zinc Zn<sup>2+</sup> o Níquel Ni<sup>2+</sup>), ingresa peso inicial (<code>42.1524</code> g), peso final (<code>42.1702</code> g) y área de probeta (<code>65.0</code> cm<sup>2</sup>). El software calcula automáticamente la carga eléctrica total (232.6 C), masa teórica (78.79 mg), masa real depositada (17.80 mg), eficiencia Faradaica (&eta;%) y espesor medio en micrómetros (0.38 &mu;m). Con el botón <span class="badge-btn">Registrar en Ficha del Ensayo</span>, los resultados se guardan permanentemente en la memoria del lote.
        </p>
      </div>
    </section>

    <!-- SECCIÓN 9: VENTANA DE METROLOGÍA Y CALIBRACIÓN DE pH -->
    <section id="ventana-ph">
      <h2 class="section-title">🧪 9. Ventana Modular: Metrología y Calibración de pH</h2>
      <p>
        Se accede desde el botón <span class="badge-btn">🧪 Metrología pH</span>. Gestiona la calibración y monitoreo
        de las sondas de pH conectadas al conversor ADS1115 de 16 bits:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Botón / Control</th>
              <th>Función en el Software</th>
              <th>Procedimiento en el Laboratorio</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Selección de Sonda (1 o 2)</strong></td>
              <td>Elige qué canal analógico se va a calibrar.</td>
              <td>Seleccione Sonda 1 o Sonda 2 antes de sumergir el electrodo en los tampones patrón.</td>
            </tr>
            <tr>
              <td><strong>Modo 2 Puntos vs 3 Puntos</strong></td>
              <td>Configura el tipo de regresión de Nernst.</td>
              <td><strong>2 Puntos</strong> (Buffers 7 y 4) para ensayos puramente ácidos; <strong>3 Puntos</strong> (4, 7 y 10) para el rango completo.</td>
            </tr>
            <tr>
              <td><strong>Detector de Estabilidad</strong></td>
              <td>Verifica que la lectura analógica esté quieta.</td>
              <td>Monitorea |<i>dV</i>/<i>dt</i>| &lt; 10 mV durante 3 segundos continuos. Muestra una barra verde cuando es seguro presionar Capturar.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Capturar Buffer 7.00</span></td>
              <td>Registra el punto isopotencial / cero.</td>
              <td>Sumerja en tampón pH 7.00, espere a que el detector indique "ESTABLE" y presione el botón.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Capturar Buffer 4.01</span></td>
              <td>Registra la pendiente en el rango ácido.</td>
              <td>Enjuague con agua desionizada, sumerja en buffer 4.01, espere estabilidad y capture el valor.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Capturar Buffer 10.01</span></td>
              <td>Registra la pendiente en el rango alcalino.</td>
              <td>Enjuague, sumerja en buffer 10.01 y capture el valor (solo en modo de 3 puntos).</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Enviar Calibración a Flash NVS</span></td>
              <td>Guarda la calibración en el hardware.</td>
              <td>Calcula la pendiente de Nernst (mV/pH), verifica que <i>R</i><sup>2</sup> &ge; 0.995 y escribe los coeficientes en la Flash NVS del ESP32.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Iniciar Historial Exclusivo pH</span></td>
              <td>Crea un registro CSV independiente.</td>
              <td>Graba únicamente las variables de pH y potencial (mV) a alta frecuencia en <code>experimentos/calibraciones_ph/</code>.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- CAPTURA REAL DE LA VENTANA MODULAR DE PH -->
      <div class="figure-box">
        <img src="imagenes/scada_05_ph.png" alt="Captura Real de la Ventana de Metrología y Calibración de pH" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 9.1: Captura directa de la Ventana Modular de Metrología y Calibración Nernstiana de pH Dual (ADS1115 de 16 bits): Dinámica de estabilización y oscilaciones, curva de regresión Nernst experimental vs teórica y panel de calibración multi-buffer.</div>
      </div>

      <!-- GUÍA FIGURA 9.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #a855f7;">
        <h4 style="color:#a855f7; margin-bottom:8px;">🧪 Guía de la Ventana de Metrología y Calibración de pH (Figura 9.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Documenta el módulo metrológico que garantiza la trazabilidad analítica de las sondas de pH. Muestra cómo el software grafica las oscilaciones y la estabilidad de potencial antes de aceptar una calibración, comparando la curva experimental con la pendiente teórica de Nernst (59.16 mV/pH).
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> El display numérico de alto contraste indica el valor actual de pH (6.99 pH, 1.767 V), la sensibilidad medida (235.67 mV/pH) y el diagnóstico de salud de la sonda (<em>Slope %</em> al 110.0%, estado ÓPTIMA). Una vez calibrados los patrones con los botones de Buffer 7.00, 4.01 y 10.01, el botón <span class="badge-btn">Enviar Calibración a Flash NVS</span> graba los coeficientes directamente en la memoria no volátil del microcontrolador ESP32.
        </p>
      </div>
    </section>

    <!-- SECCIÓN 10: VENTANA DE DIAGNÓSTICO -->
    <section id="ventana-diagnostico">
      <h2 class="section-title">🔧 10. Ventana Modular: Diagnóstico de Hardware y Sensores</h2>
      <p>
        Se accede desde el botón <span class="badge-btn">Diagnóstico</span> o haciendo clic en el contador de incidentes:
      </p>

      <div class="card-grid">
        <div class="card">
          <h4 style="color:#38bdf8; margin-bottom:8px;">Monitoreo de Periféricos I2C (400 kHz)</h4>
          <p style="font-size:0.85rem;">
            Verifica el estado de comunicación con:<br>
            • <strong>AHT20 (0x38):</strong> Sensor de humedad relativa y temperatura ambiental.<br>
            • <strong>BMP280 (0x76/77):</strong> Sensor de presión barométrica de cabina.<br>
            • <strong>ADS1115 (0x48):</strong> Convertidor ADC de 16 bits para pH y shunts de corriente.<br>
            • <strong>MCP4725 (0x60):</strong> Convertidor DAC de 12 bits para control del sumidero VCSS.
          </p>
        </div>

        <div class="card">
          <h4 style="color:#f59e0b; margin-bottom:8px;">Monitoreo de Termopares SPI (MAX6675)</h4>
          <p style="font-size:0.85rem;">
            Verifica la lectura de los 4 conversores de termopar Tipo K:<br>
            • Detecta circuito abierto / sonda desconectada.<br>
            • Muestra advertencia inmediata si la sonda pierde contacto térmico con el fluido.
          </p>
        </div>

        <div class="card">
          <h4 style="color:#22c55e; margin-bottom:8px;">Auditoría de Incidentes y Fallos</h4>
          <p style="font-size:0.85rem;">
            Registra en una tabla en vivo cada anomalía ocurrida durante el ensayo (desconexión de bus,
            saturación del sumidero, fallos de lectura) con marca de tiempo exacta.<br>
            • Botón <strong>"📄 Abrir CSV de Eventos"</strong> para exportar el registro.
          </p>
        </div>
      </div>

      <!-- CAPTURA REAL DE LA VENTANA MODULAR DE DIAGNÓSTICO -->
      <div class="figure-box">
        <img src="imagenes/scada_06_diagnostico.png" alt="Captura Real de la Ventana de Diagnóstico de Hardware y Sensores" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 10.1: Captura directa de la Ventana Modular de Diagnóstico de Hardware y Auditoría de Incidentes en Tiempo Real: Monitoreo de periféricos I2C, termopares SPI MAX6675, registro de auditoría de eventos clasificados por severidad y barra de inyección de fallos controlados.</div>
      </div>

      <!-- GUÍA FIGURA 10.1 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #10b981;">
        <h4 style="color:#10b981; margin-bottom:8px;">🔧 Guía de la Ventana de Diagnóstico de Hardware y Auditoría (Figura 10.1)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta imagen?:</strong> Muestra la pantalla de mantenimiento predictivo y monitoreo de bajo nivel del hardware embebido. El operador o investigador puede verificar en segundos el estado de salud de los 8 dispositivos del bus (AHT20, BMP280, ADS1115, MCP4725 y los 4 termopares MAX6675).
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Operación práctica:</strong> La tabla de auditoría registra cronológicamente cada evento del sistema (inicializaciones de ADC, estabilización isotérmica, balance de transistores y carga acumulada) con severidad codificada en colores (verde para <em>INFO</em>, amarillo para <em>ADVERTENCIA</em> y rojo para <em>CRÍTICO</em>). En la parte inferior, la barra de pruebas permite inyectar perturbaciones controladas (salto térmico, desconexión de sonda, sobretemperatura, desbalance de shunts) para validar la robustez de las alarmas antes de operar con reactivos químicos costosos.
        </p>
      </div>

      <!-- 10.2 GUÍA DE RESOLUCIÓN DE ANOMALÍAS Y FALLAS (TROUBLESHOOTING) -->
      <h3 class="subsection-title" id="troubleshooting">10.2 Guía de Resolución de Anomalías y Fallas Operativas (Troubleshooting)</h3>
      <p>
        Durante el trabajo experimental en planta y laboratorio químico, es común enfrentarse a ruidos electromagnéticos por conmutación AC,
        desacoples galvánicos, descalibraciones térmicas o lecturas anómalas. A continuación se detalla cómo diagnosticar y resolver cada caso:
      </p>

      <!-- 10.2.1 MEDICIONES SALTANDO DE FORMA IMPOSIBLE -->
      <h4 style="color:#f87171; margin-top:20px; margin-bottom:10px;">10.2.1 Sensores Saltando de Mediciones de Forma Imposible (Spikes y Ruido)</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Síntoma en Pantalla</th>
              <th>Causa Física / Raíz</th>
              <th>Medida Correctiva Inmediata</th>
              <th>Prevención Permanente</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Spikes en Termopar (&plusmn;25 &deg;C súbitos)</strong></td>
              <td>Ruido inducido por conmutación de TRIACs en el cable no blindado del termopar o acoplamiento capacitivo al chasis metálico.</td>
              <td>Separar el cable del termopar al menos 10 cm de las líneas de potencia AC de 120V de las resistencias.</td>
              <td>Asegurar malla a tierra física (GND) en el extremo del gabinete; activar el filtro por media móvil en el firmware.</td>
            </tr>
            <tr>
              <td><strong>Lectura NaN o 1024 &deg;C en Tina</strong></td>
              <td>Circuito abierto en el termopar Tipo K (cable roto o bornera floja en el conversor MAX6675).</td>
              <td>Apretar la bornera azul con destornillador perillero. Comprobar continuidad con multímetro.</td>
              <td>El lazo PI apaga inmediatamente el TRIAC de esa tina por seguridad ante circuito abierto (Failsafe).</td>
            </tr>
            <tr>
              <td><strong>pH saltando al encender corriente VCSS</strong></td>
              <td>Bucle de tierra (Ground Loop) o corriente parásita viajando a través del electrolito hacia la sonda de vidrio de pH.</td>
              <td>Comprobar que el electrodo de referencia del pH esté sumergido en zona con baja densidad de líneas de corriente.</td>
              <td>Utilizar aislador galvánico digital I2C (ADuM1250) o medir pH con el sumidero en pausa momentánea.</td>
            </tr>
            <tr>
              <td><strong>Corriente oscilando violentamente (&plusmn;0.5 A)</strong></td>
              <td>Sobretemperatura en los MOSFETs IRLZ44N provocando deriva térmica, o reactancia inductiva en cables largos de celda.</td>
              <td>Verificar que el ventilador de 12V del disipador esté girando a plena velocidad; reducir longitud de cables de ánodo/cátodo.</td>
              <td>Ajustar la compensación de fase en el lazo analógico del LM358 (red RC snubber en paralelo con shunt).</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 10.2.2 DESCONEXIÓN O PÉRDIDA DE PAQUETES -->
      <h4 style="color:#fbbf24; margin-top:24px; margin-bottom:10px;">10.2.2 Desconexión o Pérdida de Paquetes Wi-Fi / Serial</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Comportamiento</th>
              <th>Diagnóstico</th>
              <th>Solución Paso a Paso</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Heartbeat parpadea en Rojo (TIMEOUT)</strong></td>
              <td>El monitor SCADA en Python no recibe respuesta HTTP 200 en 1000 ms.</td>
              <td>1. Comprobar que la PC esté conectada a la red Wi-Fi <strong><code>Uli</code></strong>.<br>2. Probar ping en consola: <code>ping 192.168.4.1</code>.<br>3. Si no responde, verificar el LED azul del ESP32.</td>
            </tr>
            <tr>
              <td><strong>Caídas intermitentes cada 2 o 3 minutos</strong></td>
              <td>Interferencia en el canal 2.4 GHz de Wi-Fi provocada por el arco eléctrico o conmutación severa en el laboratorio.</td>
              <td>Conectar el cable USB tipo C directamente a la PC y conmutar el selector del SCADA al modo <strong>SERIAL (COM)</strong> a 115200 baudios.</td>
            </tr>
            <tr>
              <td><strong>Consola Web Serial vacía (<code>/consola</code>)</strong></td>
              <td>El buffer circular de logs del ESP32 está lleno o la tarea FreeRTOS de telemetría está pausada.</td>
              <td>Refrescar la página web con <code>F5</code> o presionar el botón "Limpiar Consola" en la interfaz.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 10.2.3 DIAGNÓSTICO POR CÓDIGO DE COLORES LED -->
      <h4 style="color:#a78bfa; margin-top:24px; margin-bottom:10px;">10.2.3 Diagnóstico Mediante el LED Baliza de la Cabina</h4>
      <div class="card-grid">
        <div class="card" style="border-left:4px solid #ef4444;">
          <h4 style="color:#f87171;">🔴 Rojo Intermitente (2 Hz)</h4>
          <p style="font-size:0.82rem;">
            <strong>Causa:</strong> Parada de emergencia activa (E-STOP) o sobretemperatura crítica (>95 °C) en cualquiera de las tinas.<br>
            <strong>Solución:</strong> Liberar la seta de paro girándola un cuarto de vuelta; verificar nivel de líquido en las tinas antes de rearmar.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #f59e0b;">
          <h4 style="color:#fbbf24;">🟡 Ámbar Fijo</h4>
          <p style="font-size:0.82rem;">
            <strong>Causa:</strong> Sensores ambientales AHT20 o BMP280 ausentes o no detectados en el bus I2C.<br>
            <strong>Solución:</strong> El sistema térmico y de corriente continúa operable; revisar conexiones de pines 8 (SDA) y 9 (SCL).
          </p>
        </div>

        <div class="card" style="border-left:4px solid #10b981;">
          <h4 style="color:#34d399;">🟢 Verde Baliza (Destello Lento)</h4>
          <p style="font-size:0.82rem;">
            <strong>Causa:</strong> Planta en espera (Standby) sin ningún cliente Wi-Fi conectado.<br>
            <strong>Solución:</strong> Conectar la PC o celular a la red Wi-Fi <strong><code>Uli</code></strong> (clave: <code>12345678</code>). Al conectar, cambiará a verde fijo.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #38bdf8;">
          <h4 style="color:#38bdf8;">🔵 Azul Pulso Rápido</h4>
          <p style="font-size:0.82rem;">
            <strong>Causa:</strong> Cliente web conectado transmitiendo peticiones HTTP / telemetría continua.<br>
            <strong>Solución:</strong> Operación normal; indica tráfico activo entre el navegador y el Core 0 del ESP32.
          </p>
        </div>
      </div>

      <!-- 10.2.4 DICCIONARIO DE LOGS FREERTOS -->
      <h4 style="color:#38bdf8; margin-top:24px; margin-bottom:10px;">10.2.4 Diccionario de Alarmas y Eventos en la Consola Web Serial (<code>/consola</code>)</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Tag y Mensaje de Log en Consola</th>
              <th>Nivel</th>
              <th>Significado Técnico en FreeRTOS</th>
              <th>Acción Recomendada</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>[THRM] WARN: Tina X circuito abierto (D2=1)</code></td>
              <td><span class="badge badge-warning">WARN</span></td>
              <td>El conversor MAX6675 detectó resistencia infinita en la termocupla K.</td>
              <td>El lazo PI apaga el TRIAC de esa tina por seguridad. Conectar la sonda firmemente.</td>
            </tr>
            <tr>
              <td><code>[VCSS] ERR: FALLA_RESISTENCIA_ALTA (R > 10 Ohm)</code></td>
              <td><span class="badge badge-danger">ERROR</span></td>
              <td>La celda presenta circuito abierto, electrodos desconectados o baño sin electrolito.</td>
              <td>Verificar cables de ánodo y cátodo; sumergir las placas en la solución.</td>
            </tr>
            <tr>
              <td><code>[VCSS] ERR: FALLA_SATURACION (DAC=4095, I < 0.2A)</code></td>
              <td><span class="badge badge-danger">ERROR</span></td>
              <td>El sumidero abrió compuertas al 100% pero no circula corriente (ánodo pasivado o relé abierto).</td>
              <td>Lijar ánodo y comprobar que el relé de +12V esté energizado en GPIO 20.</td>
            </tr>
            <tr>
              <td><code>[VCSS] WARN: Desbalance de shunts |I1 - I2| > 0.35A</code></td>
              <td><span class="badge badge-warning">WARN</span></td>
              <td>Una de las ramas MOSFET está conduciendo más corriente que la otra (posible sobrecalentamiento).</td>
              <td>Comprobar que ambas resistencias de 10W estén refrigeradas y no haya un MOSFET dañado.</td>
            </tr>
            <tr>
              <td><code>[SYS] WARN: Nano Watchdog timeout (>2.0s)</code></td>
              <td><span class="badge badge-warning">WARN</span></td>
              <td>El Arduino Nano no ha recibido tramas de control de potencia térmica en 2 segundos.</td>
              <td>El Nano apaga los 4 TRIACs preventivamente. Comprobar cable GPIO 17 &rarr; Nano RX.</td>
            </tr>
            <tr>
              <td><code>[SYS] INFO: Heap libre: XX KB, PSRAM: X.X MB</code></td>
              <td><span class="badge badge-primary">INFO</span></td>
              <td>Diagnóstico de memoria dinámica del ESP32-S3.</td>
              <td>Normal cuando Heap &gt; 50 KB y PSRAM &gt; 6.0 MB. Si Heap baja de 20 KB, reiniciar chip.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- SECCIÓN 11: SUITE DE GRAFICACIÓN CIENTÍFICA POST-PROCESO Y REPORTES A 300 DPI -->
    <section id="graficacion-cientifica">
      <h2 class="section-title">📈 11. Suite de Graficación Científica Post-Proceso y Reportes de Proceso Completo (300 DPI)</h2>

      <!-- GRAN BANNER DE DIFERENCIACIÓN ARQUITECTÓNICA -->
      <div class="alert alert-info" style="margin: 24px 0; border-left: 5px solid #38bdf8; background: rgba(56, 189, 248, 0.08); padding: 18px 22px;">
        <h3 style="color:#38bdf8; margin-top:0; font-size:1.15rem; display:flex; align-items:center; gap:8px;">
          <span>💡</span> CLARIFICACIÓN ARQUITECTÓNICA: SUPERVISIÓN SCADA EN VIVO vs. SUITE DE GRAFICACIÓN CIENTÍFICA
        </h3>
        <div style="font-size: 0.90rem; line-height: 1.7; color: #e2e8f0;">
          <p style="margin-bottom: 12px;">
            Para comprender con precisión el ecosistema de telemetría de la planta, es fundamental distinguir claramente entre los dos motores de visualización del sistema:
          </p>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 14px 0;">
            <div style="background: rgba(15, 23, 42, 0.6); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.2);">
              <strong style="color: #38bdf8; font-size: 0.98rem; display: block; margin-bottom: 6px;">
                🖥️ 1. Entorno SCADA en Tiempo Real (Secciones 5 a 10)
              </strong>
              <ul style="margin: 0; padding-left: 18px; font-size: 0.86rem; line-height: 1.6;">
                <li><strong>Objetivo:</strong> Supervisión en vivo, control reactivo a <strong>10 Hz</strong> y disparo de alarmas.</li>
                <li><strong>Buffer de Salida Limitado:</strong> Emplea una <strong>memoria intermedia FIFO circular (ventana deslizante)</strong>.</li>
                <li><strong>Justificación Técnica:</strong> Durante un ensayo continuo de varias horas, almacenar y renderizar millones de muestras en vivo colapsaría la memoria RAM y congelaría el hilo principal de la interfaz gráfica. El buffer deslizante acota el consumo de recursos garantizando latencia cero.</li>
              </ul>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(34, 197, 94, 0.2);">
              <strong style="color: #22c55e; font-size: 0.98rem; display: block; margin-bottom: 6px;">
                📈 2. Suite Científica Post-Proceso a 300 DPI (Esta Sección 11)
              </strong>
              <ul style="margin: 0; padding-left: 18px; font-size: 0.86rem; line-height: 1.6;">
                <li><strong>Objetivo:</strong> Post-procesamiento analítico riguroso para memorias de tesis, artículos y dossieres de calidad.</li>
                <li><strong>Sin Límite de Buffer (Proceso Completo):</strong> Lee directamente el archivo CSV íntegro almacenado en disco, procesando <strong>la totalidad del experimento (todos los 1200+ segundos)</strong> de 0 a <i>t</i><sub>final</sub> sin truncamiento.</li>
                <li><strong>Capacidades Avanzadas:</strong> Integra curvas de energía activa en Wh, masa acumulada de Faraday, envolventes continuas de 72,000 ciclos senoidales a 60 Hz y genera figuras compuestas de resolución editorial (300 DPI).</li>
              </ul>
            </div>
          </div>
          <p style="margin-bottom: 0; font-style: italic; color: #94a3b8; font-size: 0.85rem;">
            * Regla práctica: el SCADA permite al operador pilotar la planta en tiempo presente; la Suite de Graficación permite al investigador auditar y certificar el histórico global de todo el proceso.
          </p>
        </div>
      </div>

      <!-- DISCLAIMER DEMOSTRATIVO -->
      <div class="alert alert-warning" style="margin: 18px 0; border-left: 4px solid #f59e0b;">
        <strong>⚠️ DESCARGO DE RESPONSABILIDAD METROLÓGICA (GRÁFICAS DEMOSTRATIVAS):</strong><br>
        <span style="font-size: 0.87rem; line-height: 1.6;">
          Todas las curvas, oscilogramas y gráficas científicas expuestas en este manual son de carácter <strong>estrictamente demostrativo y didáctico</strong>.
          Fueron generadas mediante modelos numéricos y datos simulados para exhibir la capacidad analítica de la suite de software y no corresponden
          a un lote químico de producción industrial real.
        </span>
      </div>

      <!-- 11.1 SCRIPT GRAFICADOR -->
      <h3 class="subsection-title" id="script-graficador">11.1 Compilador Automatizado de Reportes Científicos (<code>telemetria/graficar_datos.py</code>)</h3>
      <p>
        Al concluir cualquier ensayo, el sistema permite compilar la suite gráfica completa de 10 figuras de alta definición (300 DPI)
        listas para impresión, artículos o tesis mediante el comando:
      </p>

      <div class="code-block" style="background:#0f172a; padding:12px 16px; border-radius:6px; font-family:monospace; color:#38bdf8; font-size:0.85rem; margin:12px 0;">
        python telemetria/graficar_datos.py --experimento "telemetria/experimentos/Ensayo_2026-09-12_14-30-00" --dpi 300
      </div>

      <p style="font-size:0.88rem; line-height:1.6;">
        El motor analiza el CSV completo desde el segundo 0 hasta el final, realiza integraciones trapeciales de corriente y potencia,
        aplica filtrado digital Savitzky-Golay, calcula planos de fase y compila el catálogo gráfico exhaustivo que se detalla a continuación.
      </p>

      <!-- 11.2 CATÁLOGO DE FIGURAS CIENTÍFICAS -->
      <h3 class="subsection-title">11.2 Catálogo Completo de Figuras Científicas a 300 DPI y Guías de Interpretación Metrológica</h3>

      <!-- FIGURA 11.1: PERFIL ELECTROQUÍMICO Y TÉRMICO -->
      <div class="figure-box">
        <img src="imagenes/01_perfil_electroquimico_termico.png" alt="Perfil Electroquímico y Térmico Multizona" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.1: Perfil electroquímico y térmico multizona a 300 DPI: Evolución sincrónica de temperatura en las 4 tinas, consignas de proceso y escalón galvánico VCSS de 0 a 1200 s (Proceso Completo).</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.1 (Perfil Electroquímico y Térmico Multizona)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Proporciona la visión global del experimento completo, verificando de forma irrefutable que cada tina alcanzó su temperatura de consigna antes de autorizar la inmersión de la probeta, y que la corriente galvánica se mantuvo estable sin caídas durante toda la fase de electrodeposición.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📊 ¿Qué representa?:</strong> Dos paneles sincronizados a lo largo de 1200 segundos (20 minutos): el panel superior traza las curvas de temperatura de las 4 tinas (&deg;C) contrastadas contra sus consignas punteadas; el panel inferior muestra la corriente galvánica real (A) frente a la consigna del sumidero VCSS.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• <em>Tinas 1 y 2 (Desengrase y Decapado):</em> Muestran una rampa de calentamiento de 25 &deg;C a 85 &deg;C (~500 s), seguida de una meseta isotérmica rigurosa (&plusmn;0.5 &deg;C).
          <br>• <em>Tina 3 (Celda Hull):</em> Opera a temperatura ambiente regulada (25–30 &deg;C) con mínima intervención térmica.
          <br>• <em>Corriente VCSS:</em> Permanece en 0 A durante el acondicionamiento superficial y conmuta a escalón continuo (ej. 1.50 A) exactamente durante la ventana de zincado.
        </p>
      </div>

      <!-- FIGURA 11.2: SEGUIMIENTO DE ERRORES Y IAE -->
      <div class="figure-box">
        <img src="imagenes/02_seguimiento_errores_control.png" alt="Seguimiento de Errores e Índices IAE" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.2: Auditoría metrológica de errores de control térmico e índice acumulativo IAE para las 4 tinas a lo largo de todo el proceso (Proceso Completo).</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #10b981;">
        <h4 style="color:#10b981; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.2 (Seguimiento de Errores e Índices IAE)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Para auditar la robustez analítica de los controladores PI. Permite demostrar que el sistema no presentó oscilaciones sostenidas ni sobreimpulsos que degraden las soluciones químicas.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📊 ¿Qué representa?:</strong> Panel superior con el error dinámico instantáneo <i>e</i>(<i>t</i>) = SP &minus; PV (&deg;C) para las cuatro tinas con una banda sombreada de tolerancia de &plusmn;0.5 &deg;C; panel inferior con la curva monótona creciente de la Integral del Error Absoluto IAE(<i>t</i>) = &int; |<i>e</i>| <i>dt</i> (&deg;C&middot;s).
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• <em>Banda de Tolerancia:</em> Tras el periodo transitorio, todas las curvas de error deben confinarse estrictamente dentro de la franja gris (&plusmn;0.5 &deg;C).
          <br>• <em>Curva IAE:</em> Crece rápidamente durante el arranque y debe aplanarse por completo al alcanzarse el régimen permanente. Si la pendiente del IAE sigue empinada en régimen permanente, el lazo presenta error en estado estacionario o subamortiguamiento.
        </p>
      </div>

      <!-- FIGURA 11.3: ACTUADORES TRIACS Y POTENCIA RMS -->
      <div class="figure-box">
        <img src="imagenes/03_actuadores_triacs_potencia.png" alt="Oscilogramas y Potencia RMS de Actuadores" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.3: Esfuerzo de control de TRIACs, evolución del ángulo de disparo &alpha; y potencia activa RMS disipada en Watts para cada cuba (Proceso Completo).</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #f59e0b;">
        <h4 style="color:#f59e0b; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.3 (Esfuerzo de Control de TRIACs y Potencia RMS)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Para auditar el estrés eléctrico y térmico en los semiconductores de potencia (TRIACs BTA24-600B) y validar la potencia consumida en Watts por las resistencias calefactoras sin picos dañinos en la red eléctrica.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📊 ¿Qué representa?:</strong> Tres paneles sincronizados: panel superior con el ángulo de disparo &alpha;(<i>t</i>) en grados (0&deg; a 180&deg;); panel medio con la tensión eficaz <i>V</i><sub>RMS</sub>(<i>t</i>); panel inferior con la potencia activa real disipada <i>P</i>(<i>t</i>) = <i>V</i><sub>RMS</sub><sup>2</sup> / <i>R</i> en Watts.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• <em>Arranque:</em> &alpha; se ubica entre 0&deg; y 25&deg;, produciendo <i>V</i><sub>RMS</sub> &approx; 115–120 V y <i>P</i> &approx; 450 W (plena potencia).
          <br>• <em>Régimen Permanente:</em> &alpha; se abre progresivamente a 120&deg;–140&deg;, la tensión eficaz cae a 45–55 V y la potencia se estabiliza en 70–90 W (compensación de pérdidas por convección).
        </p>
      </div>

      <!-- FIGURA 11.4: MACRO-CONMUTACIÓN 4 TINAS (TODO EL PROCESO) -->
      <div class="figure-box">
        <img src="imagenes/03b_macro_conmutacion_4tinas_proceso_completo.png" alt="Macro-Conmutación de TRIACs en las 4 Tinas a lo largo de todo el proceso" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.4: Física de macro-conmutación de TRIACs en las 4 tinas (0 a 1200 s) — Matriz comparativa entre Recorte de Fase (&alpha;) y Tiempo Proporcional (Burst Firing ZCS), ilustrando los 72,000 ciclos senoidales a 60 Hz y la transición hacia pulsos delgados de asentamiento térmico (Proceso Completo).</div>
      </div>

      <!-- GUÍA FIGURA 11.4 -->
      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">🔬 Guía de Interpretación Metrológica de la Figura 11.4 (Macro-Conmutación de 72,000 Ciclos Senoidales)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> En la industria, el control térmico se audita comúnmente con una simple curva de temperatura contra tiempo (<i>T</i> vs. <i>t</i>). Sin embargo, esa curva oculta por completo el comportamiento del actuador: no permite saber si el TRIAC estuvo saturado, si el lazo osciló o si hubo conmutaciones erráticas. Esta figura se incluye para brindar una <strong>auditoría ciberfísica exhaustiva de los 1200 segundos del proceso</strong>.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📊 ¿Qué representa?:</strong> Una matriz de 4 Filas (las 4 cubas) &times; 2 Columnas: la columna izquierda muestra el <em>Recorte de Ángulo de Fase (&alpha;)</em> y la columna derecha muestra el <em>Tiempo Proporcional (Burst Firing ZCS)</em>. El eje gemelo derecho traza la curva de temperatura real en rojo y la consigna punteada en azul marino.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 Física de la portadora de 60 Hz y origen óptico del «bloque sólido»:</strong> En la red eléctrica de 60 Hz, cada ciclo senoidal dura apenas 16.66 ms. En 1200 segundos se suceden exactamente <strong>72,000 ciclos senoidales completos (144,000 excursiones entre +170V y -170V pico)</strong>. En el arranque (100% potencia), la sucesión ininterrumpida de ondas densamente comprimidas en pantalla crea la apariencia óptica de un <em>rectángulo sólido de color</em>. Conforme la temperatura llega a la consigna, la modulación adelgaza progresivamente los paquetes hasta verse como líneas finas aisladas (pulsos de mantenimiento).
        </p>
      </div>

      <!-- FIGURA 11.5: SENOIDALES MODIFICADAS EN ESCALA MICROSCÓPICA -->
      <div class="figure-box">
        <img src="imagenes/03_senoidales_modificadas_periodos.png" alt="Senoidales modificadas por TRIAC en escala microscópica" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.5: Oscilogramas microscópicos a 60 Hz en milisegundos (0 a 50 ms) para los tres regímenes operativos: Calentamiento Máximo, Transición Proporcional y Régimen Permanente Estabilizado.</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #a855f7;">
        <h4 style="color:#a855f7; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.5 (Oscilogramas Microscópicos a 60 Hz en Milisegundos)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Proporciona la resolución temporal de un osciloscopio de laboratorio (0 a 50 ms) para inspeccionar la morfología íntima de la onda senoidal y contrastar el mecanismo físico del recorte de fase frente a los paquetes de ciclos enteros (Burst Firing).
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• <em>Fila 1 (Recorte de Fase):</em> La onda permanece en 0V al cruce por cero y salta bruscamente a la senoidal al alcanzarse el ángulo &alpha;. A mayor &alpha;, menor es el área encerrada y menor el calor aportado.
          <br>• <em>Fila 2 (Burst Firing):</em> Conduce ondas senoidales completas sin cortes intermedios, eliminando por completo armónicos y radiación electromagnética (EMI).
        </p>
      </div>

      <!-- FIGURA 11.6: BALANZA Y FARADAY -->
      <div class="figure-box">
        <img src="imagenes/04_analisis_faraday_plano_fase.png" alt="Análisis Faradaico y Cinética Electroquímica" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.6: Cinética electroquímica y balance culombimétrico: Carga integrada Q(t), comparación masa teórica vs real, y rendimiento Faradaico catódico (&eta;%).</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.6 (Cinética Faradaica y Balanza Gravimétrica)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Para contrastar las leyes fundamentales de la electroquímica teórica con los resultados experimentales obtenidos en la balanza analítica, determinando la eficiencia catódica del baño galvánico.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• La curva superior traza la integral de carga acumulada <i>Q</i>(<i>t</i>) = &int; <i>I</i>(<i>t</i>)<i>dt</i> en Coulombs.
          <br>• El panel inferior compara la masa teórica predicha por la Ley de Faraday <i>m</i><sub>teo</sub> = (<i>Q</i> &times; <i>M</i>) / (<i>z</i> &times; <i>F</i>) con la masa real pesada (&Delta;<i>m</i><sub>real</sub>), indicando el rendimiento Faradaico resultante (&eta;<sub><i>F</i></sub> &approx; 93.4%).
        </p>
      </div>

      <!-- FIGURA 11.7: DASHBOARD EJECUTIVO Y BALANCE WH -->
      <div class="figure-box">
        <img src="imagenes/05_diagnostico_integral_resumen.png" alt="Dashboard Ejecutivo de Diagnóstico y Balance Energético" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.7: Dashboard ejecutivo post-ensayo: Balance global de energía en Wh por tina, radar multivariable de control y resumen estadístico del lote.</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #10b981;">
        <h4 style="color:#10b981; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.7 (Dashboard Ejecutivo y Balance de Energía en Wh)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Condensa en un reporte gerencial los indicadores clave de desempeño (KPIs) para auditoría técnica, control de costes eléctricos de planta y aseguramiento de calidad.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• <em>Distribución Energética:</em> Gráfico de barras que confirma que las tinas de alta temperatura (T1 y T2 a 85 &deg;C) concentran el 85% de la energía consumida en Watt-hora (Wh), mientras que la celda galvánica consume una fracción menor.
          <br>• <em>Radar de Control:</em> Evalúa simétricamente el IAE, rizado térmico, estabilidad galvánica y tiempos de establecimiento.
        </p>
      </div>

      <!-- FIGURA 11.8: CRONOGRAMA GANTT ISA-88 -->
      <div class="figure-box">
        <img src="imagenes/06_tiempos_muertos_gantt_fases.png" alt="Cronograma Gantt de Fases y Tiempos de Transferencia" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.8: Cronograma Gantt de etapas del proceso ISA-88: Auditoría de tiempos de inmersión activa, tiempos de reposo y verificación de tiempos de transferencia entre cubas.</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #38bdf8;">
        <h4 style="color:#38bdf8; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.8 (Cronograma Gantt ISA-88 y Tiempos Muertos)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> En electrodeposición sobre aluminio, los tiempos de transferencia aérea entre tinas no deben exceder 15 segundos para evitar la pasivación por óxido superficial. Esta figura audita el cumplimiento temporal estricto de la receta.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• Las barras horizontales cronológicas representan las 8 etapas del tratamiento de la probeta.
          <br>• Permite detectar inmediatamente demoras excesivas del operador en los enjuagues o transiciones fuera de tolerancia.
        </p>
      </div>

      <!-- FIGURA 11.9: METROLOGÍA VCSS Y PULSOS ETS -->
      <div class="figure-box">
        <img src="imagenes/08_metrologia_vcss_ets_pulsado.png" alt="Metrología de Corriente VCSS y Muestreo ETS" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.9: Metrología de corriente galvánica VCSS y muestreo estroboscópico ETS a 10 Hz: Reconstrucción de onda en corriente pulsada e histéresis de regulación analógica.</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #f59e0b;">
        <h4 style="color:#f59e0b; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.9 (Metrología VCSS y Muestreo ETS)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Verifica la fidelidad de corriente del sumidero analógico regulado por el MCP4725 y el LM358, auditando la estabilidad en modo continuo DC y la reconstrucción estroboscópica en corriente pulsada.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• Evalúa la planicidad del escalón de corriente (rizado &lt; 5 mA) y el reparto equilibrado de corriente entre los transistores MOSFET mediante los resistores shunt de precisión.
        </p>
      </div>

      <!-- FIGURA 11.10: METROLOGÍA DE PH Y FILTRADO DIGITAL -->
      <div class="figure-box">
        <img src="imagenes/08_filtro_ph_tri_modo.png" alt="Metrología de pH y Filtrado Digital Tri-Modo" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 11.10: Metrología de pH, curva de calibración de Nernst (buffers 4.01, 7.00 y 10.01) y respuesta del filtro digital tri-modo ante perturbaciones químicas.</div>
      </div>

      <div class="card" style="margin: 14px 0 20px 0; border-left: 4px solid #a855f7;">
        <h4 style="color:#a855f7; margin-bottom:8px;">🔍 Guía de Interpretación de la Figura 11.10 (Metrología de pH y Filtrado Digital)</h4>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:8px;">
          <strong>📌 ¿Por qué se añade esta gráfica?:</strong> Garantiza la trazabilidad metrológica de la acidez en la Celda Hull de zincado ácido (pH nominal 2.0 a 4.0) y demuestra la efectividad del filtro digital eliminando spikes sin retardar la respuesta.
        </p>
        <p style="font-size:0.87rem; line-height:1.6; margin-bottom:0;">
          <strong>📖 ¿Cómo se lee e interpreta?:</strong>
          <br>• El panel izquierdo muestra la recta de regresión de Nernst validando que la pendiente experimental sea &ge; 95% del valor teórico (59.16 mV/pH a 25 &deg;C).
          <br>• El panel derecho compara la señal ruidosa del electrodo de vidrio frente a la curva limpia del filtro de mediana y ventana móvil.
        </p>
      </div>
    </section>

    <!-- SECCIÓN 12: CÓMO ADAPTAR EL SISTEMA A OTRO TIPO DE EXPERIMENTO -->
    <section id="multi-experimento">
      <h2 class="section-title">🔄 12. Guía Práctica: Adaptación a Otro Tipo de Experimento</h2>"""

# Check replacement in HTML
if pattern_scada_region.search(html):
    # Notice pattern_scada_region stops before <section id="multi-experimento">
    # So we replace up to <section id="multi-experimento"> and also rename Section 11 -> 12, Section 12 -> 13, Section 13 -> 14
    html = pattern_scada_region.sub(replacement_sections_5_to_11, html)
    print("SCADA region and Section 11 successfully replaced!")
else:
    print("ERROR: pattern_scada_region not found!")

# Now rename former sections:
# Section 12: Guía Práctica was replaced with 12. in replacement_sections_5_to_11 above.
# Let's fix former Section 12 (Datasheets) -> 13, and Section 13 (Código fuente) -> 14
html = html.replace(
    '<h2 class="section-title">📚 12. Biblioteca de Datasheets de Componentes (Descargas PDF)</h2>',
    '<h2 class="section-title">📚 13. Biblioteca de Datasheets de Componentes (Descargas PDF)</h2>'
)

html = html.replace(
    '<h2 class="section-title">💻 13. Arquitectura del Código Fuente, Librerías & Entornos de Desarrollo</h2>',
    '<h2 class="section-title">💻 14. Arquitectura del Código Fuente, Librerías & Entornos de Desarrollo</h2>'
)

# Renumber subsections of section 14: 13.1 -> 14.1, etc.
for i in range(1, 10):
    html = html.replace(f'<h3 class="subsection-title">13.{i} ', f'<h3 class="subsection-title">14.{i} ')

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("MANUAL_DE_OPERACION_QUIMICA.html successfully updated and saved!")

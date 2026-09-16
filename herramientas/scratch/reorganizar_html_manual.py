import os
import re

path_html = r"c:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"

with open(path_html, "r", encoding="utf-8") as f:
    html = f.read()

# Make backup
with open(path_html + ".bak", "w", encoding="utf-8") as f:
    f.write(html)
print("Backup created successfully.")

# 1. Update Sidebar
old_nav = """      <a href="#telemetria-controles">📊 5. Telemetría, Grabación & KPIs</a>
      <a href="#script-graficador" style="padding-left:24px;font-size:0.78rem;color:#38bdf8;">📈 5.3 Script Graficador 300 DPI</a>
      <a href="#ventana-actuadores">⚡ 6. Ventana: Osciloscopio & TRIACs</a>
      <a href="#ventana-errores">🌀 7. Ventana: Errores & Plano de Fase</a>
      <a href="#ventana-faraday">⚖️ 8. Ventana: Balanza & Faraday</a>
      <a href="#ventana-ph">🧪 9. Ventana: Metrología & pH</a>
      <a href="#ventana-diagnostico">🔧 10. Ventana: Diagnóstico I2C/SPI</a>
      <a href="#troubleshooting">🛠️ 10.2 Guía de Resolución de Fallas</a>
      <a href="#multi-experimento">🔄 11. Adaptación a Otros Ensayos</a>
      <a href="#datasheets-ref">📚 12. Biblioteca de Datasheets (PDF)</a>
      <a href="#codigo-fuente">💻 13. Código Fuente & Antigravity IDE</a>"""

new_nav = """      <a href="#telemetria-controles">📊 5. Pantalla Principal SCADA (En Vivo)</a>
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

if old_nav in html:
    html = html.replace(old_nav, new_nav)
    print("Sidebar nav updated.")
else:
    print("WARNING: old_nav not matched exactly.")

# 2. Section 5: Telemetría en Vivo y Pantalla Principal
sec5_replacement = """    <!-- SECCIÓN 5: TELEMETRÍA EN VIVO Y PANTALLA PRINCIPAL SCADA -->
    <section id="telemetria-controles">
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
              <td>Temperatura actual (°C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>1</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T1.</td>
            </tr>
            <tr>
              <td><strong>T2: Decapado / Matizado</strong></td>
              <td>Temperatura actual (°C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>2</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T2.</td>
            </tr>
            <tr>
              <td><strong>T3: Celda Activa / Hull</strong></td>
              <td>Temperatura actual (°C)</td>
              <td>Setpoint fijado y esfuerzo de control <i>u</i><sub>3</sub> (%)</td>
              <td>Abre la ventana modular de osciloscopio en Canal T3.</td>
            </tr>
            <tr>
              <td><strong>T4: Tina 4 / Niquelado</strong></td>
              <td>Temperatura actual (°C)</td>
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
              <td>Temperatura (°C) / Humedad (%)</td>
              <td>Presión barométrica (hPa) vía BMP280</td>
              <td>Información de condiciones ambientales en cabina.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- NOTA DE BUFFER DE SALIDA DEL SCADA -->
      <div class="alert alert-info" style="margin: 20px 0;">
        <strong>ℹ️ DINÁMICA DE VISUALIZACIÓN EN TIEMPO REAL (BUFFER FIFO CIRCULAR):</strong><br>
        <span style="font-size: 0.88rem; line-height: 1.6;">
          Los 3 osciloscopios gráficos de la pantalla principal operan como una <strong>ventana temporal deslizante con buffer circular limitado</strong>.
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
    </section>"""

# Match old Section 5
patt_sec5 = re.compile(r'<!-- SECCIÓN 4: TELEMETRÍA, GRABACIÓN Y KPIS.*?<!-- SECCIÓN 5: VENTANA DE OSCILOSCOPIO Y ACTUADORES -->', re.DOTALL)
if patt_sec5.search(html):
    html = patt_sec5.sub(sec5_replacement + "\n\n    <!-- SECCIÓN 6: VENTANA DE OSCILOSCOPIO Y ACTUADORES -->", html)
    print("Section 5 replaced successfully.")
else:
    print("WARNING: Section 5 pattern not found.")

# 3. Section 6: Ventana Modular Actuadores
sec6_replacement = """    <!-- SECCIÓN 6: VENTANA DE OSCILOSCOPIO Y ACTUADORES -->
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
    </section>"""

patt_sec6 = re.compile(r'<!-- SECCIÓN 5: VENTANA DE OSCILOSCOPIO Y ACTUADORES -->.*?<!-- SECCIÓN 6: VENTANA DE ERRORES Y PLANO DE FASE -->', re.DOTALL)
if patt_sec6.search(html):
    html = patt_sec6.sub(sec6_replacement + "\n\n    <!-- SECCIÓN 7: VENTANA DE ERRORES Y PLANO DE FASE -->", html)
    print("Section 6 replaced successfully.")
else:
    print("WARNING: Section 6 pattern not found.")

# 4. Section 7: Ventana Modular Errores
sec7_replacement = """    <!-- SECCIÓN 7: VENTANA DE ERRORES Y PLANO DE FASE -->
    <section id="ventana-errores">
      <h2 class="section-title">🌀 7. Ventana Modular: Monitor de Errores y Plano de Fase</h2>
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
    </section>"""

patt_sec7 = re.compile(r'<!-- SECCIÓN 6: VENTANA DE ERRORES Y PLANO DE FASE -->.*?<!-- SECCIÓN 7: VENTANA DE BALANZA Y LEY DE FARADAY -->', re.DOTALL)
if patt_sec7.search(html):
    html = patt_sec7.sub(sec7_replacement + "\n\n    <!-- SECCIÓN 8: VENTANA DE BALANZA Y LEY DE FARADAY -->", html)
    print("Section 7 replaced successfully.")
else:
    print("WARNING: Section 7 pattern not found.")

# 5. Section 8: Ventana Modular Faraday
sec8_replacement = """    <!-- SECCIÓN 8: VENTANA DE BALANZA Y LEY DE FARADAY -->
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
    </section>"""

patt_sec8 = re.compile(r'<!-- SECCIÓN 7: VENTANA DE BALANZA Y LEY DE FARADAY -->.*?<!-- SECCIÓN 8: VENTANA DE METROLOGÍA Y CALIBRACIÓN DE pH -->', re.DOTALL)
if patt_sec8.search(html):
    html = patt_sec8.sub(sec8_replacement + "\n\n    <!-- SECCIÓN 9: VENTANA DE METROLOGÍA Y CALIBRACIÓN DE pH -->", html)
    print("Section 8 replaced successfully.")
else:
    print("WARNING: Section 8 pattern not found.")

# 6. Section 9: Ventana Modular pH
sec9_replacement = """    <!-- SECCIÓN 9: VENTANA DE METROLOGÍA Y CALIBRACIÓN DE pH -->
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
    </section>"""

patt_sec9 = re.compile(r'<!-- SECCIÓN 8: VENTANA DE METROLOGÍA Y CALIBRACIÓN DE pH -->.*?<!-- SECCIÓN 9: VENTANA DE DIAGNÓSTICO -->', re.DOTALL)
if patt_sec9.search(html):
    html = patt_sec9.sub(sec9_replacement + "\n\n    <!-- SECCIÓN 10: VENTANA DE DIAGNÓSTICO -->", html)
    print("Section 9 replaced successfully.")
else:
    print("WARNING: Section 9 pattern not found.")

# 7. Section 10: Ventana Modular Diagnóstico + Troubleshooting
# In section 10, remove Figure 10.2 (dashboard ejecutivo) and keep Figure 10.1 (scada_06) + troubleshooting
patt_sec10_fig = re.compile(r'<!-- GUÍA FIGURA 10\.1 -->\s*<div class="card".*?<!-- GUÍA FIGURA 10\.2 -->\s*<div class="card".*?</div>\s*</div>\s*(?=<h3 class="subsection-title" id="troubleshooting">)', re.DOTALL)

# Let's inspect section 10 closely to avoid regex mismatch
print("Section 10 inspection...")

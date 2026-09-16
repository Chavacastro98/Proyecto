# -*- coding: utf-8 -*-
import os

manual_path = r"C:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"

with open(manual_path, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = '    <!-- SECCIÓN 2: INTERFAZ WEB EMBEBIDA DEL ESP32 -->'
end_marker = '    <!-- SECCIÓN 3: PANEL PRINCIPAL SCADA EN PYTHON (BOTÓN POR BOTÓN) -->'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"Error: Markers not found! start_idx={start_idx}, end_idx={end_idx}")
    exit(1)

new_section_2 = """    <!-- SECCIÓN 2: INTERFAZ WEB EMBEBIDA DEL ESP32 -->
    <section id="interfaz-web">
      <h2 class="section-title">🌐 2. Interfaz Web Embebida del ESP32 (http://192.168.4.1 o http://interfaz.local)</h2>
      <p>
        Además del software SCADA de escritorio para PC, el microcontrolador maestro ESP32-S3 ejecuta un <strong>servidor web HTTP autónomo en el puerto 80 (Core 0 - Task_Web)</strong>.
        Esta interfaz está construida con arquitectura moderna (HTML5, Vanilla CSS responsivo y JavaScript asíncrono) almacenada de forma permanente en la memoria Flash (PROGMEM) del ESP32.
        Permite el control total de la planta, ajuste de temperaturas, gobierno de corriente VCSS, calibración metrológica de pH e inspección de logs desde cualquier <strong>teléfono inteligente, tablet o laptop</strong> sin instalar ningún software ni driver.
      </p>

      <div class="alert alert-info">
        <strong>📱 GUÍA RÁPIDA DE CONEXIÓN INALÁMBRICA:</strong>
        1. <strong>Conectar Wi-Fi:</strong> En su celular, tablet o PC, busque la red inalámbrica del equipo: <strong>SSID: <code>Uli</code></strong> | Contraseña: <strong><code>12345678</code></strong>.<br>
        2. <strong>Abrir Navegador:</strong> Abra cualquier navegador (Chrome, Safari, Firefox, Edge) e ingrese la IP: <strong><code>http://192.168.4.1</code></strong> o la dirección mDNS: <strong><code>http://interfaz.local</code></strong>.<br>
        3. <strong>Exploración sin Hardware (Simulador Local):</strong> Para explorar e interactuar con las 7 vistas web sin encender el equipo físico, abra la réplica interactiva: <a href="../preview/RTOS1.3/index.html" class="link-pdf" target="_blank">🌐 Abrir Vista Previa Web Local (RTOS 1.3)</a>.
      </div>

      <!-- 2.1 HUB PRINCIPAL -->
      <h3 class="subsection-title" id="web-hub">2.1 Pantalla Principal / Hub de Control (<code>/</code> o <code>/index.html</code>)</h3>
      <p>
        Es el centro neurálgico móvil. Proporciona una visión instantánea de la meteorología ambiental de cabina,
        el latido FreeRTOS en tiempo real, avisos de seguridad FailSafe y accesos directos a todos los módulos instrumentales con telemetría viva.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_01_hub.png" alt="Pantalla Principal Hub Web ESP32" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.1: Menú Principal / Hub Web del ESP32 (Supervisión meteorológica ambiental AHT20/BMP280, latido FreeRTOS SMP y accesos con telemetría viva).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Elemento / Control</th>
              <th>Tipo de Control</th>
              <th>Función en la Interfaz</th>
              <th>Efecto Físico en el ESP32 / Sensores</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Badge de Estado</strong> (<code>sys-badge</code>)</td>
              <td>Indicador dinámico</td>
              <td>Muestra <code>FreeRTOS SMP</code> con pulso verde animado si hay enlace continuo con el microcontrolador. Cambia a rojo si el ESP32 no responde en 3 segundos.</td>
              <td>Supervisa la tarea <code>Task_Web</code> en Core 0. Si el watchdog de FreeRTOS detecta bloqueo, el indicador conmuta a Offline.</td>
            </tr>
            <tr>
              <td><strong>Chip Tag</strong> (<code>chip-tag</code>)</td>
              <td>Etiqueta estática</td>
              <td>Identifica el hardware montado: <code>ESP32-S3 Dual-Core N16R8</code> (16 MB Flash Quad-SPI, 8 MB Octal-PSRAM).</td>
              <td>Garantiza al operador que se está comunicando con el procesador maestro del equipo.</td>
            </tr>
            <tr>
              <td><strong>Banner Fail-Safe</strong> (<code>failsafe-banner</code>)</td>
              <td>Banner de Alarma Crítica</td>
              <td>Permanece oculto en operación normal. Si ocurre un fallo térmico o de corriente, aparece con animación de vibración roja indicando la causa exacta.</td>
              <td>Contiene el botón <span class="badge-btn">DESBLOQUEAR SISTEMA</span>, que envía un <code>POST /api/failsafe_reset</code> para rehabilitar el bus I2C y compuertas de potencia tras resolver la causa.</td>
            </tr>
            <tr>
              <td><strong>Estación Ambiental</strong> (<code>env-box</code>)</td>
              <td>3 Displays numéricos</td>
              <td>Muestra <strong>Temp. Amb.</strong> (°C), <strong>Humedad</strong> (% HR) y <strong>Presión</strong> (hPa). Se iluminan en color azul cian con efecto de flash cada vez que se actualiza una muestra.</td>
              <td>Lee directamente los sensores I2C de cabina: termo-higrómetro AHT20 (dirección <code>0x38</code>) y barómetro digital BMP280 (dirección <code>0x76</code>).</td>
            </tr>
            <tr>
              <td><strong>Tarjeta Salida de Corriente</strong></td>
              <td>Botón de navegación</td>
              <td>Muestra la corriente entregada viva (ej. <code>2.40 A DC</code> o cadencia pulsada) y da acceso a la vista de la fuente.</td>
              <td>Navega a <code>/fuente</code> para manipulación de consigna del MCP4725 y sumidero VCSS.</td>
            </tr>
            <tr>
              <td><strong>Tarjeta Control Térmico</strong></td>
              <td>Botón de navegación</td>
              <td>Muestra cuántas tinas tienen calentamiento activo (ej. <code>2/4 tinas activas</code>).</td>
              <td>Navega a <code>/termico</code> para ajustar setpoints individuales de los 4 canales PI.</td>
            </tr>
            <tr>
              <td><strong>Tarjeta Módulo de pH</strong></td>
              <td>Botón de navegación</td>
              <td>Muestra el valor de pH actual de Tina 1 y Tina 2 (ej. <code>Zinc: 7.05 · Ni: 4.12</code>).</td>
              <td>Navega a <code>/ph</code> para visualización de diales cromáticos y calibración con soluciones buffer.</td>
            </tr>
            <tr>
              <td><strong>Accesos a Herramientas</strong></td>
              <td>Botonera secundaria</td>
              <td>Enlaces rápidos hacia <code>Estado de Sensores</code>, <code>Consola de Diagnóstico</code> y <code>Actualizar Firmware (OTA)</code>.</td>
              <td>Permite mantenimiento avanzado del hardware sin necesidad de abrir el monitor SCADA en la PC.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.2 CONTROL TÉRMICO WEB -->
      <h3 class="subsection-title" id="web-termico">2.2 Control Térmico Web de 4 Canales (<code>/termico</code>)</h3>
      <p>
        Permite regular la temperatura de los 4 baños químicos de manera independiente o conjunta.
        El operador puede modificar las temperaturas deseadas acercando su celular a las cubas y observando la respuesta en tiempo real.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_02_termico.png" alt="Control Térmico Web 4 Canales" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.2: Panel de Control Térmico Web (Dígitos gigantes, indicador de tendencia, barras de potencia TRIAC y ajuste paso a paso).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Control Interactivo</th>
              <th>Tipo</th>
              <th>Función al Pulsar</th>
              <th>Efecto en el Hardware / Algoritmo PI</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="badge-btn">ACTIVAR CALENTAMIENTO</span></td>
              <td>Botón maestro verde</td>
              <td>Inicia el lazo de control PI en todos los canales térmicos configurados.</td>
              <td>Habilita el disparo de los 4 opto-TRIACs MOC3021 en sincronía con el cruce por cero (ZCS) de la red AC 60 Hz.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">PARAR SISTEMA</span></td>
              <td>Botón maestro rojo</td>
              <td>Suspende inmediatamente la entrega de potencia en todas las tinas.</td>
              <td>Fuerza el ángulo de disparo $\\alpha = 180^\\circ$ (apagado total) y reinicia el acumulador integral del PID para prevenir sobrepicos de temperatura al reanudar.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">+</span> / <span class="badge-btn">-</span> (Paso a Paso)</td>
              <td>Botones de setpoint</td>
              <td>Aumenta o disminuye la temperatura deseada de la tina seleccionada en incrementos de <strong>1 °C</strong> por pulsación.</td>
              <td>Actualiza la variable de consigna $SP_i$ en la memoria del ESP32 y envía la nueva referencia al cálculo de error $e(t) = SP_i - PV_i$.</td>
            </tr>
            <tr>
              <td><strong>Dígitos Gigantes (54px)</strong></td>
              <td>Display numérico</td>
              <td>Muestra la temperatura actual leída en la tina con resolución de 0.1 °C.</td>
              <td>Proviene de la lectura digital del termopar tipo K a través del convertidor SPI MAX6675 (actualizado cada 250 ms).</td>
            </tr>
            <tr>
              <td><strong>Flecha de Tendencia</strong> (<code>trend</code>)</td>
              <td>Badge con flecha</td>
              <td>Indica si la temperatura está <code>SUBIENDO</code> (naranja), <code>BAJANDO</code> (azul) o <code>ESTABLE</code> (verde, variación menor a 0.2 °C/min).</td>
              <td>Cálculo de derivada temporal discreta $dT/dt$ ejecutado por el ESP32 para dar retroalimentación intuitiva al operario.</td>
            </tr>
            <tr>
              <td><strong>Barra de Potencia TRIAC</strong></td>
              <td>Barra de gradiente</td>
              <td>Muestra el porcentaje instantáneo de potencia aplicada al calefactor (0% a 100%).</td>
              <td>Refleja el tiempo de conducción del TRIAC dentro de cada semiciclo de 8.33 ms (60 Hz AC).</td>
            </tr>
            <tr>
              <td><strong>Píldora de Estado</strong></td>
              <td>Badge de tina</td>
              <td>Indica si la tina está <code>ACTIVA</code>, <code>EN ESPERA</code> o <code>ERROR SENSOR</code> si el termopar se rompe o desconecta.</td>
              <td>Si detecta circuito abierto en el MAX6675 (bit D2 en alto), desactiva de inmediato el TRIAC de esa tina por seguridad intrínseca.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.3 SALIDA DE CORRIENTE VCSS -->
      <h3 class="subsection-title" id="web-fuente">2.3 Salida de Corriente VCSS & Metrología ETS (<code>/fuente</code>)</h3>
      <p>
        Controla el generador y sumidero de corriente constante para electrodeposición, pasivado o ensayos galvánicos.
        Ofrece modo de corriente continua (DC) y modo pulsado de alta velocidad con visualización estroboscópica ETS.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_03_fuente.png" alt="Salida de Corriente Web VCSS" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.3: Interfaz de la Fuente de Corriente VCSS (Amperímetro VU-meter, modos DC/Pulsado, sliders táctiles, calibración y oscilograma ETS).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Control Interactivo</th>
              <th>Rango / Opciones</th>
              <th>Función Operativa</th>
              <th>Efecto en el Circuito Electrónico VCSS</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="badge-btn">ENCENDER FUENTE</span> / <span class="badge-btn">APAGAR FUENTE</span></td>
              <td>Biestable (Verde / Rojo)</td>
              <td>Activa o desactiva la entrega de corriente hacia la celda electroquímica.</td>
              <td>Dispara el optoacoplador PC817 del relé de aislamiento físico de +12V y conmuta el DAC MCP4725 de 0V a la tensión de consigna.</td>
            </tr>
            <tr>
              <td><strong>Amperímetro Display Gigante</strong></td>
              <td>0.00 a 6.60 A</td>
              <td>Muestra la corriente real que fluye por la celda con dos decimales de precisión.</td>
              <td>Adquirida por el ADC ADS1115 de 16 bits en los canales A2 y A3 midiendo la caída en las resistencias de shunt cerámicas de 10W.</td>
            </tr>
            <tr>
              <td><strong>Selector de Modo</strong></td>
              <td><code>Modo DC Continuo</code> / <code>Modo Pulsado</code></td>
              <td>Conmuta la topología de conducción eléctrica del sumidero.</td>
              <td>En modo DC, el DAC entrega una tensión analógica estable; en modo pulsado, el ESP32 modula la polarización de compuerta a frecuencia y ciclo de trabajo programables.</td>
            </tr>
            <tr>
              <td><strong>Slider Consigna de Corriente</strong></td>
              <td>0 a 4095 bits (0.00 a 6.60 A)</td>
              <td>Ajusta gradualmente la corriente deseada arrastrando el control con el dedo.</td>
              <td>Escribe en el registro del DAC MCP4725 vía I2C (dirección <code>0x60</code>), ajustando la tensión de referencia aplicada a los operacionales LM358.</td>
            </tr>
            <tr>
              <td><strong>Presets Rápidos</strong></td>
              <td><span class="badge-btn">0.5 A</span>, <span class="badge-btn">1.5 A</span>, <span class="badge-btn">3.0 A</span>, <span class="badge-btn">5.0 A</span></td>
              <td>Salta directamente a valores estándar de ensayo con un solo toque.</td>
              <td>Calcula la palabra binaria del DAC y la transmite de inmediato sin demoras de arrastre.</td>
            </tr>
            <tr>
              <td><strong>Slider Frecuencia Pulsada</strong></td>
              <td>1 a 100 Hz</td>
              <td>Define la frecuencia de conmutación de la onda cuadrada en modo pulsado.</td>
              <td>Ajusta el temporizador de hardware del ESP32 que gobierna la conmutación de los transistores MOSFET.</td>
            </tr>
            <tr>
              <td><strong>Slider Ciclo de Trabajo (Duty)</strong></td>
              <td>10% a 90%</td>
              <td>Regula el porcentaje de tiempo activo ($T_{\\\\text{on}} / T$) del pulso catódico.</td>
              <td>Permite controlar el crecimiento cristalográfico y refinamiento de grano en recubrimientos metálicos.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Auto-Calibrar Shunts</span></td>
              <td>Botón de acción</td>
              <td>Ejecuta la calibración en vacío del circuito de corriente.</td>
              <td>Pone el DAC a 0V, mide las tensiones de desbalance en los shunts cerámicos y almacena el factor de corrección $G_m$ en la Flash NVS del ESP32.</td>
            </tr>
            <tr>
              <td><strong>Osciloscopio ETS (Canvas)</strong></td>
              <td>16 muestras estroboscópicas</td>
              <td>Reconstruye la forma de onda del pulso de corriente sin saturar el bus I2C.</td>
              <td>Implementa muestreo de tiempo equivalente (ETS), tomando una muestra por cada ciclo con desfase progresivo para graficar pulsos de hasta 100 Hz con un ADC de 860 SPS.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.4 MÓDULO DE PH DUAL -->
      <h3 class="subsection-title" id="web-ph">2.4 Módulo de pH Dual & Calibración / Offset Hardware (<code>/ph</code>)</h3>
      <p>
        Supervisa los sensores de pH de los baños químicos críticos (ej. Tina 1 y Tina 2).
        Incluye un asistente de calibración guiada con soluciones buffer estándar y un voltímetro de ajuste fino para el circuito preamplificador analógico.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_04_ph.png" alt="Módulo de pH Web ESP32" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.4: Módulo de pH Web (Diales cromáticos circulares, calibración guiada por buffers y panel de ajuste fino de offset LM358).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Elemento Web</th>
              <th>Opciones / Valores</th>
              <th>Propósito Operativo</th>
              <th>Impacto Técnico en el Sistema</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Interruptor Maestro</strong> (<code>tog</code>)</td>
              <td><code>LECTURA ACTIVA</code> / <code>SUSPENDIDO</code></td>
              <td>Habilita o pausa la adquisición continua del sensor de pH.</td>
              <td>Activa o apaga la tarea de conversión del ADC ADS1115 (canal A0/A1), ahorrando ancho de banda en el bus I2C cuando no se use pH.</td>
            </tr>
            <tr>
              <td><strong>Dial Cromático Circular</strong></td>
              <td>Escala 0.00 a 14.00 pH</td>
              <td>Muestra el pH con color dinámico: rojo (&lt;3 ácido fuerte), naranja (3-6), verde (6-8 neutro), azul (8-11) y púrpura (&gt;11 alcalino).</td>
              <td>Calculado mediante la ecuación de Nernst con compensación por temperatura de la tina: $\\\\text{pH} = 7.0 - \\\\frac{V - V_0}{S(T)}$.</td>
            </tr>
            <tr>
              <td><strong>Selector de Calibración</strong></td>
              <td><code>Teórico (Nernst)</code> / <code>2 Puntos (7 & 4)</code> / <code>3 Puntos (7, 4 & 10)</code></td>
              <td>Elige el modelo matemático de calibración electroquímica.</td>
              <td>El modo 2 puntos ajusta el offset en pH 7 y la pendiente ácida con pH 4; el modo 3 puntos ajusta pendientes asimétricas para rango ácido y básico.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Calibrar con Buffer 7.00</span></td>
              <td>Solución neutra verde</td>
              <td>Punto cero del electrodo de vidrio.</td>
              <td>Abre una ventana modal con cuenta regresiva de 10 segundos donde el ESP32 verifica estabilidad ($|dV/dt| < 10\\\\text{ mV}$) antes de fijar $V_{\\\\text{offset}}$.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Calibrar con Buffer 4.01</span></td>
              <td>Solución ácida roja</td>
              <td>Calibra la pendiente ácida del electrodo.</td>
              <td>Calcula la pendiente real $S = (V_7 - V_4) / (7.00 - 4.01)$ en mV/pH y verifica que esté entre el 90% y 105% del valor teórico de Nernst.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Calibrar con Buffer 10.01</span></td>
              <td>Solución básica azul</td>
              <td>Calibra la pendiente alcalina del electrodo.</td>
              <td>Permite compensar el error de ion alcalino (error de sodio) en soluciones altamente básicas.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Restaurar Fábrica</span></td>
              <td>Botón de reset</td>
              <td>Borra la calibración de la memoria Flash NVS y vuelve a $59.16\\\\text{ mV/pH}$ a 25 °C.</td>
              <td>Útil cuando se conecta un electrodo nuevo y se desconoce la calibración anterior.</td>
            </tr>
            <tr>
              <td><strong>Ajuste Fino de Offset Hardware</strong></td>
              <td>Panel desplegable</td>
              <td>Voltímetro con aguja indicadora respecto a la tierra virtual de $1.765\\\\text{ V}$ ($V_{\\\\text{ref}}/2$).</td>
              <td>Permite al operador girar el trimpot multivuelta del módulo LM358 con un desarmador plano hasta que la aguja quede en el centro de la zona verde ($\\\\pm 15\\\\text{ mV}$).</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.5 ESTADO DE SENSORES Y LEDS -->
      <h3 class="subsection-title" id="web-sensores">2.5 Diagnóstico de Sensores & Leyenda Neopixel de 13 Códigos (<code>/sensores</code>)</h3>
      <p>
        Audita los 8 dispositivos periféricos conectados a los buses digitales I2C y SPI.
        Además, contiene la referencia visual completa de los 13 códigos de colores y cadencias del LED Neopixel RGB del panel de control.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_05_sensores.png" alt="Diagnóstico de Sensores Web" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.5: Pantalla de Diagnóstico de Sensores (Estado de los 8 periféricos, botón de escaneo y decodificador de 13 estados LED).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Periférico Sensado</th>
              <th>Bus / Pines</th>
              <th>Dirección / CS</th>
              <th>Estado Esperado</th>
              <th>Función en el Sistema</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>BMP280</strong></td>
              <td>I2C (SDA 21, SCL 22)</td>
              <td><code>0x76</code></td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Presión barométrica atmosférica y temperatura de referencia del gabinete.</td>
            </tr>
            <tr>
              <td><strong>AHT20</strong></td>
              <td>I2C (SDA 21, SCL 22)</td>
              <td><code>0x38</code></td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Humedad relativa del aire (%) para monitoreo ambiental y punto de rocío en cabina.</td>
            </tr>
            <tr>
              <td><strong>ADS1115</strong></td>
              <td>I2C (SDA 21, SCL 22)</td>
              <td><code>0x48</code></td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Conversor ADC de 16 bits: canales de pH (A0/A1) y corriente en shunts VCSS (A2/A3).</td>
            </tr>
            <tr>
              <td><strong>MCP4725</strong></td>
              <td>I2C (SDA 21, SCL 22)</td>
              <td><code>0x60</code></td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Conversor DAC de 12 bits: fija la tensión de referencia del sumidero de corriente.</td>
            </tr>
            <tr>
              <td><strong>MAX6675 Tina 1</strong></td>
              <td>SPI (SCK 18, MISO 19)</td>
              <td>CS GPIO 15</td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Digitalizador de termopar tipo K para Tina 1 (0 a 1024 °C, resolución 0.25 °C).</td>
            </tr>
            <tr>
              <td><strong>MAX6675 Tina 2</strong></td>
              <td>SPI (SCK 18, MISO 19)</td>
              <td>CS GPIO 2</td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Digitalizador de termopar tipo K para Tina 2.</td>
            </tr>
            <tr>
              <td><strong>MAX6675 Tina 3</strong></td>
              <td>SPI (SCK 18, MISO 19)</td>
              <td>CS GPIO 0</td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Digitalizador de termopar tipo K para Tina 3.</td>
            </tr>
            <tr>
              <td><strong>MAX6675 Tina 4</strong></td>
              <td>SPI (SCK 18, MISO 19)</td>
              <td>CS GPIO 4</td>
              <td><span class="badge badge-success">OK</span></td>
              <td>Digitalizador de termopar tipo K para Tina 4.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h4 style="color:#e2e8f0; margin-top:20px; margin-bottom:10px;">Guía de los 13 Códigos Lumínicos del LED Neopixel (RGB WS2812):</h4>
      <div class="card-grid">
        <div class="card"><p style="font-size:0.82rem;"><strong>1. Rojo Estroboscópico Rápido (0.25s):</strong> Parada de emergencia Fail-Safe activada o watchdog disparado.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>2. Rojo Intermitente Lento (1s):</strong> Fallo crítico en sensor I2C/SPI o termopar roto.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>3. Blanco Estroboscópico (0.2s):</strong> Flasheo de firmware inalámbrico OTA en progreso.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>4. Púrpura Respiración Lenta:</strong> Auto-calibración de shunts VCSS en proceso.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>5. Fucsia Respiración (2s):</strong> Calibración de electrodo de pH con solución buffer activa.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>6. Cian Pulso Rítmico:</strong> Modo de corriente pulsada activo entregando energía a la celda.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>7. Cian Sólido:</strong> Modo de corriente continua (DC) activo en la celda.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>8. Azul Oscuro Sólido:</strong> Inicializando subsistema Wi-Fi.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>9. Azul Pulso Rápido:</strong> Cliente web conectado transmitiendo peticiones HTTP.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>10. Azul Claro Sólido:</strong> Punto de acceso SoftAP <code>Uli</code> listo para recibir conexiones.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>11. Ámbar Sólido:</strong> Calentamiento térmico activo (TRIACs conmutando).</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>12. Verde Sólido:</strong> Sistema en operación normal sin anomalías.</p></div>
        <div class="card"><p style="font-size:0.82rem;"><strong>13. Verde Baliza / Respiración:</strong> Sistema en espera (Standby) listo para iniciar ciclo.</p></div>
      </div>

      <!-- 2.6 CONSOLA WEB SERIAL -->
      <h3 class="subsection-title" id="web-consola">2.6 Consola Web Serial & Logs FreeRTOS (<code>/consola</code>)</h3>
      <p>
        Permite a los operadores e ingenieros inspeccionar los mensajes internos del sistema operativo FreeRTOS en tiempo real
        desde el navegador, sin necesidad de conectar el microcontrolador a la computadora con un cable USB.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_06_consola.png" alt="Consola Web Serial FreeRTOS" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.6: Terminal Serial Web del ESP32 (Inspección de eventos FreeRTOS, etiquetas por subsistema y latencia en vivo).</div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Elemento / Botón</th>
              <th>Función</th>
              <th>Comportamiento en el Navegador</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><span class="badge-btn">Auto-Scroll: ON/OFF</span></td>
              <td>Control de desplazamiento</td>
              <td>Mantiene la ventana al final del registro al llegar nuevas líneas. Al desactivarse, permite leer líneas antiguas sin que la pantalla salte.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Pausar / Reanudar</span></td>
              <td>Control de flujo</td>
              <td>Detiene temporalmente la adición de nuevas líneas en la vista sin perder los registros en el buffer del microcontrolador.</td>
            </tr>
            <tr>
              <td><span class="badge-btn">Limpiar</span></td>
              <td>Borrado de terminal</td>
              <td>Vacía la ventana del terminal para iniciar una inspección limpia de un evento específico.</td>
            </tr>
            <tr>
              <td><strong>Indicador de Latencia</strong></td>
              <td>Telemetría de enlace</td>
              <td>Muestra el tiempo de ida y vuelta HTTP en milisegundos (típicamente entre 12 y 25 ms sobre la red SoftAP <code>Uli</code>).</td>
            </tr>
            <tr>
              <td><strong>Etiquetas de Subsistema</strong></td>
              <td>Filtro contextual</td>
              <td>Clasifica los eventos por origen: <code>[BOOT]</code>, <code>[FREERTOS]</code>, <code>[I2C]</code>, <code>[THRM]</code>, <code>[VCSS]</code>, <code>[PH]</code>, <code>[AMB]</code>, <code>[OTA]</code>.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.7 PORTAL OTA -->
      <h3 class="subsection-title" id="web-update">2.7 Portal OTA de Actualización Inalámbrica de Firmware (<code>/update</code>)</h3>
      <p>
        Permite actualizar el firmware del microcontrolador sin abrir el gabinete ni desconectar sensores.
        Utiliza el esquema de particiones duales de FreeRTOS para garantizar que si la carga falla o se interrumpe, el equipo regresa intacto al firmware anterior.
      </p>

      <div class="figure-box">
        <img src="imagenes/web_07_update.png" alt="Portal OTA Firmware ESP32" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 2.7: Portal de Actualización Inalámbrica OTA (Zona de arrastre drag-and-drop y flasheo seguro en Flash SPI).</div>
      </div>

      <div class="alert alert-warning">
        <strong>⚠️ INSTRUCCIONES PARA ACTUALIZAR FIRMWARE VÍA OTA:</strong>
        1. Compile el nuevo código en el IDE de Arduino seleccionando <em>Programa &rarr; Exportar Binarios Compilados</em> para generar el archivo <code>.bin</code>.<br>
        2. Ingrese a <strong><code>http://192.168.4.1/update</code></strong> desde cualquier dispositivo conectado a la red <code>Uli</code>.<br>
        3. Arrastre el archivo <code>.bin</code> a la zona punteada o haga clic en ella para seleccionarlo.<br>
        4. Presione el botón <span class="badge-btn">INICIAR ACTUALIZACIÓN OTA</span>. Espere a que la barra complete el 100%. El ESP32 verificará el checksum y se reiniciará automáticamente en 5 segundos.
      </div>

      <!-- 2.8 REST API JSON -->
      <h3 class="subsection-title" id="web-api">2.8 Endpoints REST API JSON del ESP32 (Para Integración Externa)</h3>
      <p>
        Si se desea controlar la estación desde scripts externos (Python, MATLAB, LabVIEW, Node-RED o cURL),
        el servidor HTTP del ESP32 expone una API REST ligera basada en JSON:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Método HTTP</th>
              <th>Endpoint URL</th>
              <th>Parámetros Requeridos</th>
              <th>Respuesta JSON</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>GET</code></td>
              <td><code>/api/status</code></td>
              <td>Ninguno</td>
              <td><code>{"temp":[64.8,25.1,44.9,24.3],"amps":2.40,"ph":[7.05,4.12],"env":{"t":24.6,"h":48,"p":1013}}</code></td>
              <td>Devuelve el paquete completo de telemetría instantánea de todos los sensores y actuadores.</td>
            </tr>
            <tr>
              <td><code>POST</code></td>
              <td><code>/api/termico</code></td>
              <td><code>tina=0..3&sp=XX.X&run=0|1</code></td>
              <td><code>{"status":"ok","tina":0,"sp":65.0,"run":1}</code></td>
              <td>Modifica la consigna de temperatura o activa/apaga el lazo PI de la tina especificada.</td>
            </tr>
            <tr>
              <td><code>POST</code></td>
              <td><code>/api/fuente</code></td>
              <td><code>pwr=0|1&modo=0|1&amps=X.XX&freq=XX&duty=XX</code></td>
              <td><code>{"status":"ok","pwr":1,"modo":0,"amps":2.50}</code></td>
              <td>Controla el encendido, modo de corriente continua/pulsada, frecuencia y ciclo de trabajo del sumidero VCSS.</td>
            </tr>
            <tr>
              <td><code>POST</code></td>
              <td><code>/api/ph_cal</code></td>
              <td><code>ch=1|2&point=4|7|10</code></td>
              <td><code>{"status":"calibrating","ch":1,"point":7,"mv":1762}</code></td>
              <td>Inicia la rutina de captura y cálculo de offset/pendiente para el canal de pH indicado.</td>
            </tr>
            <tr>
              <td><code>POST</code></td>
              <td><code>/api/calibrar_vcss</code></td>
              <td>Ninguno</td>
              <td><code>{"status":"ok","gm":1.0042,"r1_zero":0.001,"r2_zero":0.002}</code></td>
              <td>Ejecuta la rutina de auto-balance de shunts en vacío y guarda el factor de transconductancia en NVS.</td>
            </tr>
            <tr>
              <td><code>POST</code></td>
              <td><code>/api/failsafe_reset</code></td>
              <td>Ninguno</td>
              <td><code>{"status":"reset_ok"}</code></td>
              <td>Rearma el sistema tras una condición de sobretemperatura o fallo crítico.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 2.9 MATRIZ COMPARATIVA -->
      <h3 class="subsection-title">2.9 Matriz Comparativa: ¿Cuándo usar la Interfaz Web y cuándo el SCADA en Python?</h3>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Criterio de Elección</th>
              <th>🌐 Interfaz Web Embebida (ESP32)</th>
              <th>🖥️ Monitor SCADA de Escritorio (Python)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Dispositivo de Acceso</strong></td>
              <td>Cualquier celular, tablet, laptop o PC con navegador web.</td>
              <td>Computadora con Python 3.9+ y pantalla amplia.</td>
            </tr>
            <tr>
              <td><strong>Instalación de Software</strong></td>
              <td><strong>Cero instalación.</strong> Corre directamente desde el chip.</td>
              <td>Requiere dependencias de <code>requirements.txt</code> (Tkinter, Matplotlib).</td>
            </tr>
            <tr>
              <td><strong>Control Manual Rápido</strong></td>
              <td><strong>Ideal:</strong> Ajuste de setpoints sobre la marcha, encendido/apagado de tinas, prueba de corriente VCSS desde el celular junto a la cuba.</td>
              <td>Posible, pero más orientado a la ejecución de secuencias automáticas.</td>
            </tr>
            <tr>
              <td><strong>Gestión de Recetas ISA-88</strong></td>
              <td>Control por parámetros manuales individuales.</td>
              <td><strong>Completa:</strong> Carga de matrices experimentales Excel, cronómetros automáticos por fase y alertas sonoras.</td>
            </tr>
            <tr>
              <td><strong>Almacenamiento de Datos</strong></td>
              <td>Visualización instantánea en vivo (sin disco duro en el ESP32).</td>
              <td><strong>Grabación Masiva CSV a 1 Hz</strong> en el disco duro de la PC dentro de <code>telemetria/experimentos/</code>.</td>
            </tr>
            <tr>
              <td><strong>Metrología de Faraday</strong></td>
              <td>Lectura de corriente y carga instantánea.</td>
              <td><strong>Completa:</strong> Entrada de 4 decimales de balanza analítica, masa real vs. teórica, espesor ($\\\\mu\\\\text{m}$) y rendimiento $\\\\eta\\\\%$.</td>
            </tr>
            <tr>
              <td><strong>Exportación de Gráficas HD</strong></td>
              <td>No disponible en el chip (recursos de memoria limitados).</td>
              <td><strong>Paquete de 5 Figuras Científicas a 300 DPI</strong> listas para tesis o publicaciones científicas.</td>
            </tr>
            <tr>
              <td><strong>Mantenimiento y Firmware</strong></td>
              <td><strong>Portal OTA en <code>/update</code></strong> para subir nuevos firmwares sin cables.</td>
              <td>Supervisión de fallos de hardware en ventana de diagnóstico.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

"""

new_content = content[:start_idx] + new_section_2 + content[end_idx:]

with open(manual_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Manual successfully updated! Total length: {len(new_content)} characters.")

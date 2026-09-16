import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. UPDATE MANUAL_DE_OPERACION_QUIMICA.html
html_path = 'documentos/MANUAL_DE_OPERACION_QUIMICA.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# A. Insert warning in Section 2.7 after alert-warning
ota_warning_target = """      <div class="alert alert-warning">
        <strong>⚠️ INSTRUCCIONES PARA ACTUALIZAR FIRMWARE VÍA OTA:</strong>
        1. Compile el nuevo código en el IDE de Arduino seleccionando <em>Programa &rarr; Exportar Binarios Compilados</em> para generar el archivo <code>.bin</code>.<br>
        2. Ingrese a <strong><code>http://192.168.4.1/update</code></strong> desde cualquier dispositivo conectado a la red <code>Uli</code>.<br>
        3. Arrastre el archivo <code>.bin</code> a la zona punteada o haga clic en ella para seleccionarlo.<br>
        4. Presione el botón <span class="badge-btn">INICIAR ACTUALIZACIÓN OTA</span>. Espere a que la barra complete el 100%. El ESP32 verificará el checksum y se reiniciará automáticamente en 5 segundos.
      </div>"""

ota_nano_block = """      <div class="alert alert-warning">
        <strong>⚠️ INSTRUCCIONES PARA ACTUALIZAR FIRMWARE VÍA OTA:</strong>
        1. Compile el nuevo código en el IDE de Arduino seleccionando <em>Programa &rarr; Exportar Binarios Compilados</em> para generar el archivo <code>.bin</code>.<br>
        2. Ingrese a <strong><code>http://192.168.4.1/update</code></strong> desde cualquier dispositivo conectado a la red <code>Uli</code>.<br>
        3. Arrastre el archivo <code>.bin</code> a la zona punteada o haga clic en ella para seleccionarlo.<br>
        4. Presione el botón <span class="badge-btn">INICIAR ACTUALIZACIÓN OTA</span>. Espere a que la barra complete el 100%. El ESP32 verificará el checksum y se reiniciará automáticamente en 5 segundos.
      </div>

      <div class="alert alert-danger" style="margin-top:16px; border-left:4px solid #ef4444; background: rgba(239,68,68,0.08);">
        <h4 style="color:#f87171; margin-bottom:8px;">🛑 IMPORTANTE: El Arduino Nano (Nodo Dimmer AC) NO se actualiza vía OTA</h4>
        <p style="font-size:0.86rem; line-height:1.5; color:#cbd5e1; margin-bottom:10px;">
          El portal web <code>/update</code> flashea de forma inalámbrica <strong>únicamente la memoria Flash SPI del microcontrolador maestro ESP32-S3</strong>.
          El microcontrolador esclavo <strong>Arduino Nano (ATmega328P)</strong> no posee tarjeta de red Wi-Fi ni líneas de control de reset/DTR enlazadas al ESP32 (se encuentra aislado galvánicamente y comunicado exclusivamente por el enlace serie UART2 en modo esclavo).
        </p>
        <p style="font-size:0.86rem; line-height:1.5; color:#fca5a5; margin-bottom:8px;">
          <strong>⚡ Procedimiento de Actualización del Arduino Nano (Vía Cable USB Físico):</strong>
        </p>
        <ol style="font-size:0.84rem; line-height:1.6; padding-left:22px; color:#e2e8f0; margin-bottom:8px;">
          <li><strong>⚠️ SEGURIDAD CRÍTICA:</strong> Desconecte la clavija principal de corriente alterna (110V/220V AC) del gabinete antes de conectar cualquier cable a la computadora para garantizar el aislamiento físico del operador y de la PC.</li>
          <li>Conecte el Arduino Nano a su computadora mediante un cable USB (Mini-B o Type-C según la versión de su placa Nano).</li>
          <li>Abra el código fuente <code>arduino_nano/nano/nano.ino</code> en <strong>Arduino IDE</strong> (versión 2.x o clásica).</li>
          <li>En el menú <em>Herramientas (Tools)</em>, configure con exactitud:
            <ul style="margin-top:4px; margin-bottom:4px;">
              <li><strong>Placa (Board):</strong> <code>Arduino Nano</code></li>
              <li><strong>Procesador (Processor):</strong> <code>ATmega328P</code>. <em>(Nota: Si la placa es un clon común con chip de comunicación CH340 y falla la subida, cámbielo a <code>ATmega328P (Old Bootloader)</code> que opera a 57600 baudios).</em></li>
              <li><strong>Puerto (Port):</strong> Seleccione el puerto <code>COM</code> asignado al Arduino Nano (verifique en el Administrador de Dispositivos que sea el del Nano y no el del ESP32).</li>
            </ul>
          </li>
          <li>Haga clic en el botón <strong>Subir (Upload)</strong>. Espere a que la barra inferior indique <em>"Subido" / "Done uploading"</em>.</li>
          <li>Desconecte el cable USB del Arduino Nano antes de volver a energizar la etapa de potencia de 110V/220V AC.</li>
        </ol>
      </div>"""

if ota_warning_target in html:
    html = html.replace(ota_warning_target, ota_nano_block)
    print("Section 2.7 Arduino Nano update alert inserted successfully!")
else:
    print("WARNING: ota_warning_target not found!")

# B. Insert Section 14.8, Section 15 (FAQ), and Section 16 (Creditos) before </main>
section_14_end_target = """      <div class="alert alert-info" style="margin-top:22px;">
        <strong>💡 ¿Cómo explorar el código fuente con Antigravity IDE?</strong>
        Simplemente abre la carpeta raíz del proyecto descomprimido dentro de <strong>Antigravity IDE</strong>.
        Podrás examinar simultáneamente el árbol de carpetas, abrir los archivos <code>.ino</code>, <code>.cpp</code>, <code>.py</code> y <code>.html</code> con resaltado de sintaxis optimizado, consultar la relación entre módulos mediante la búsqueda semántica y ejecutar scripts de prueba con asistencia inteligente integrada.
      </div>
    </section>

  </main>"""

new_sections_block = """      <div class="alert alert-info" style="margin-top:22px;">
        <strong>💡 ¿Cómo explorar el código fuente con Antigravity IDE?</strong>
        Simplemente abre la carpeta raíz del proyecto descomprimido dentro de <strong>Antigravity IDE</strong>.
        Podrás examinar simultáneamente el árbol de carpetas, abrir los archivos <code>.ino</code>, <code>.cpp</code>, <code>.py</code> y <code>.html</code> con resaltado de sintaxis optimizado, consultar la relación entre módulos mediante la búsqueda semántica y ejecutar scripts de prueba con asistencia inteligente integrada.
      </div>

      <!-- 14.8 COMPARATIVA DE MÉTODOS DE CONTROL -->
      <h3 class="subsection-title" id="comparativa-metodos">14.8 Comparativa de Métodos de Control: ¿Por qué existen 2 Alternativas? Ventajas y Desventajas</h3>
      <p>
        Tanto en el control de potencia térmica como en la supervisión de la planta, el proyecto implementa dos metodologías complementarias. Esta dualidad no es redundancia accidental, sino una respuesta de ingeniería a compromisos físicos entre determinismo en tiempo real, resolución analógica, aislamiento de ruido e inmunidad a caídas:
      </p>

      <h4 style="color:#38bdf8; margin-top:20px; margin-bottom:10px;">A. Métodos de Control de Potencia Térmica AC (Calefacción de Tinas)</h4>
      <p style="font-size:0.88rem; color:#cbd5e1; margin-bottom:12px;">
        Para gobernar las resistencias calefactoras de 110V/220V AC se estudiaron e implementaron dos topologías de conmutación:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Criterio Técnico</th>
              <th>Método 1: Recorte de Ángulo de Fase (&alpha;-Firing)<br><span style="color:#38bdf8;font-size:0.75rem;">(Implementado en Producción: <code>arduino_nano/nano/nano.ino</code>)</span></th>
              <th>Método 2: Paquetes de Ciclos / Ventana Proporcional (Burst)<br><span style="color:#c084fc;font-size:0.75rem;">(Alternativa OOP: <code>arduino_nano/historico/nano2/</code>)</span></th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Principio Físico</strong></td>
              <td>Recorta cada semiciclo de la onda senoidal (120 semiciclos/segundo) modulando el retardo de disparo &alpha; de 0 a 8333 &mu;s tras el cruce por cero.</td>
              <td>Enciende la onda senoidal completa durante un número entero de ciclos y la apaga el resto dentro de una ventana de tiempo (ej. 3.0 segundos).</td>
            </tr>
            <tr>
              <td><strong>Resolución & Dinámica</strong></td>
              <td><strong>Ultra alta (sub-milisegundo):</strong> Ajusta la entrega de energía 120 veces por segundo de forma continua y suave.</td>
              <td><strong>Discreta:</strong> Modulación por paquetes de 3 segundos; resolución limitada al periodo de la ventana.</td>
            </tr>
            <tr>
              <td><strong>Estabilidad Térmica en Celda Hull (267 mL)</strong></td>
              <td><strong>Excelente (&plusmn;0.2 &deg;C):</strong> No produce oscilaciones perceptibles. Ideal para reactores de muy baja inercia térmica donde una pausa de 1 segundo enfría la disolución.</td>
              <td><strong>Deficiente (&plusmn;1.5 &deg;C a &plusmn;2.0 &deg;C):</strong> Provoca ciclos visibles de "calentamiento y enfriamiento" (oleadas térmicas) en volúmenes menores a 500 mL.</td>
            </tr>
            <tr>
              <td><strong>Ruido Electromagnético (EMI / dv/dt)</strong></td>
              <td><strong>Genera armónicos de conmutación:</strong> El encendido abrupto a mitad de senoidal crea transitorios dv/dt que requieren filtros RC snubber y optoacopladores MOC3021.</td>
              <td><strong>Cero ruido de alta frecuencia:</strong> Conmuta exclusivamente en el cruce por cero natural (tensión cero), erradicando el ruido electromagnético.</td>
            </tr>
            <tr>
              <td><strong>Hardware & Requerimiento de CPU</strong></td>
              <td><strong>Exige Co-procesador Esclavo (Arduino Nano):</strong> Requiere atender interrupciones críticas a 120 Hz en microsegundos sin jitter provocado por Wi-Fi o tareas web del ESP32.</td>
              <td><strong>Simplificado:</strong> Podría implementarse dentro del mismo ESP32 mediante temporizadores lentos de FreeRTOS sin microcontrolador esclavo.</td>
            </tr>
            <tr>
              <td><strong>Actualización Remota por OTA</strong></td>
              <td><strong>No disponible en el Nano:</strong> Requiere cable USB directo para flashear el ATmega328P. El ESP32 solo actualiza su propio firmware por OTA.</td>
              <td><strong>100% Viable por OTA:</strong> Al no requerir co-procesador dedicado, todo el código residiría en el ESP32 y se actualizaría inalámbricamente.</td>
            </tr>
            <tr>
              <td><strong>Veredicto de Selección</strong></td>
              <td><strong>ELEGIDO PARA PRODUCCIÓN:</strong> La precisión fisicoquímica del ensayo de electrodeposición en la Celda Hull exige estabilidad estricta de &plusmn;0.2 &deg;C.</td>
              <td><strong>VÁLIDO PARA GRANDES VOLÚMENES:</strong> Excelente alternativa si se amplía la planta a tinas industriales de 20 a 100 litros con alta inercia térmica.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h4 style="color:#10b981; margin-top:24px; margin-bottom:10px;">B. Métodos de Supervisión y Operación del Sistema (Web Móvil vs SCADA de Escritorio)</h4>
      <p style="font-size:0.88rem; color:#cbd5e1; margin-bottom:12px;">
        El operador dispone de dos entornos complementarios para interactuar con la planta:
      </p>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Parámetro Operativo</th>
              <th>Vía 1: Interfaz Web Embebida (ESP32 / Navegador Móvil)</th>
              <th>Vía 2: Monitor SCADA de Escritorio (Python / Tkinter)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Dispositivo de Acceso</strong></td>
              <td>Cualquier smartphone, tablet o laptop conectada a la red Wi-Fi <code>Uli</code> abriendo <code>http://192.168.4.1</code>.</td>
              <td>Computadora de laboratorio con Python 3 ejecutando <code>Iniciar_Telemetria.bat</code>.</td>
            </tr>
            <tr>
              <td><strong>Instalación de Software</strong></td>
              <td><strong>Cero instalación:</strong> Opera sobre el navegador web estándar del dispositivo (Chrome, Safari, Firefox).</td>
              <td>Requiere Python y librerías científicas (instalables en 1 clic con <code>instalar_python_y_librerias.bat</code>).</td>
            </tr>
            <tr>
              <td><strong>Almacenamiento de Datos</strong></td>
              <td><strong>Buffer circular volátil:</strong> Conserva las lecturas recientes en memoria RAM. Si el ESP32 se reinicia, los datos web se pierden.</td>
              <td><strong>Persistencia masiva a disco:</strong> Guarda cada segundo en archivos <code>.csv</code> ilimitados con redundancia en disco duro.</td>
            </tr>
            <tr>
              <td><strong>Automatización ISA-88</strong></td>
              <td><strong>Control Manual / Puntual:</strong> Ajuste directo de consignas, encendido individual de tinas y calibración asistida de pH.</td>
              <td><strong>Control Automatizado de Recetas:</strong> Ejecuta secuencias multietapa (Precalentamiento, Electrodeposición, Pasivado, Enjuague) con temporizadores.</td>
            </tr>
            <tr>
              <td><strong>Metrología Avanzada</strong></td>
              <td>Visualización instantánea de variables de proceso, alarmas y estado de sensores.</td>
              <td>Balanza virtual de Faraday (&Delta;m culombimétrico en vivo), osciloscopio virtual, plano de fase e historial de errores.</td>
            </tr>
            <tr>
              <td><strong>Generación de Reportes</strong></td>
              <td>No genera gráficos exportables para publicaciones.</td>
              <td>Suite de Gráficas Científicas automatizada con exportación a 300 DPI en PNG y PDF vectorial.</td>
            </tr>
            <tr>
              <td><strong>Actualización de Firmware</strong></td>
              <td><strong>Portal OTA en <code>/update</code>:</strong> Permite flashear el ESP32 sin cables mediante arrastrar y soltar el archivo <code>.bin</code>.</td>
              <td>No gestiona actualización de firmware.</td>
            </tr>
            <tr>
              <td><strong>Caso de Uso Recomendado</strong></td>
              <td><strong>Operación a pie de tina:</strong> Inspección rápida, calibración de electrodos de pH con buffers, encendido preliminar y mantenimiento.</td>
              <td><strong>Ensayos científicos formales:</strong> Ejecución de recetas completas, recopilación de datos para tesis y análisis cuantitativo.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- SECCIÓN 15: PREGUNTAS FRECUENTES (FAQ) -->
    <section id="faq">
      <h2 class="section-title">❓ 15. Preguntas Frecuentes (FAQ)</h2>
      <p>
        Respuestas directas y fundamentadas a las dudas técnicas y operativas más comunes en el uso, mantenimiento y puesta en marcha de la estación:
      </p>

      <div class="faq-container" style="display:flex; flex-direction:column; gap:14px; margin-top:16px;">
        <div class="card" style="border-left:4px solid #38bdf8;">
          <h4 style="color:#38bdf8; margin-bottom:6px;">1. ¿Por qué el Arduino Nano no se actualiza a través del portal web inalámbrico OTA (<code>/update</code>)?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            El servidor web y el gestor OTA residen físicamente en el chip ESP32-S3 y escriben sobre su memoria Flash externa de 16 MB.
            El <strong>Arduino Nano (ATmega328P)</strong> es un microcontrolador esclavo independiente que no tiene antena Wi-Fi ni comparte el bus de memoria del ESP32.
            Su único canal de enlace con el ESP32 es un par de líneas serie UART2 (GPIO 17 TX a D0 RX). Como el ESP32 no cuenta con líneas de control de reset físico (DTR) conectadas al Nano para activar el bootloader STK500, cualquier actualización del código del Nano (<code>arduino_nano/nano/nano.ino</code>) <strong>debe realizarse conectando un cable USB directo a la computadora</strong> mediante Arduino IDE.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #10b981;">
          <h4 style="color:#10b981; margin-bottom:6px;">2. ¿Por qué se utilizó un Arduino Nano dedicado y no se controlaron los TRIACs directamente desde el ESP32?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            Por <strong>determinismo temporal estricto y seguridad eléctrica</strong>.
            La modulación por ángulo de fase a 60 Hz requiere calcular y disparar compuertas cada 8.33 ms con una precisión de microsegundos (&plusmn;10 &mu;s).
            En el ESP32, la pila Wi-Fi SoftAP, el servidor HTTP asíncrono y los cambios de contexto del planificador FreeRTOS introducen jitter temporal que causaría parpadeos y disparos asimétricos en la corriente alterna.
            Al delegar el control de potencia al ATmega328P (un procesador RISC sin sistema operativo que atiende la interrupción externa INT1 en 8 &mu;s), se garantiza un lazo de disparo 100% determinista.
            Además, separa físicamente la etapa de 110V/220V AC del procesador de instrumentación de precisión (pH y ADC de 16 bits).
          </p>
        </div>

        <div class="card" style="border-left:4px solid #f59e0b;">
          <h4 style="color:#f59e0b; margin-bottom:6px;">3. ¿Qué sucede si el ESP32 se congela, se reinicia o se corta la comunicación con el Arduino Nano?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            El firmware del Arduino Nano implementa un <strong>Perro Guardián por Software (UART Watchdog)</strong> de 3000 ms.
            Cada segundo, el ESP32 envía una trama serie <code>&lt;T1,T2,T3,T4&gt;</code> con los porcentajes de potencia calculados por el lazo PI térmico.
            Si el Arduino Nano deja de recibir tramas válidas durante más de 3 segundos consecutivos, su temporizador expira y <strong>fuerza inmediatamente el apagado total de los 4 canales TRIAC (retardo 8333 &mu;s, potencia 0%)</strong>.
            Este comportamiento <em>Fail-Safe</em> impide que las resistencias queden encendidas de forma descontrolada ante un fallo de software o desconexión del cable de datos.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #ef4444;">
          <h4 style="color:#ef4444; margin-bottom:6px;">4. Al intentar subir el código al Arduino Nano, el IDE muestra <code>avrdude: stk500_recv(): programmer is not responding</code>. ¿Cómo se soluciona?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            Este es el error más frecuente en placas Arduino Nano con convertidor USB-Serie CH340. Se debe a que el fabricante grabó el bootloader clásico de 57600 baudios en lugar del nuevo optiboot a 115200 baudios.
            <strong>Solución:</strong> En Arduino IDE, diríjase al menú <code>Herramientas &rarr; Procesador</code> y seleccione <strong><code>ATmega328P (Old Bootloader)</code></strong>.
            Asimismo, asegúrese de haber seleccionado el puerto COM correcto y de haber desconectado previamente la alimentación de potencia de 110V/220V AC.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #c084fc;">
          <h4 style="color:#c084fc; margin-bottom:6px;">5. ¿Por qué la lectura de pH fluctúa o es inestable cuando la fuente de corriente VCSS o los calentadores están activos?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            El electrodo de pH de vidrio es un sensor electroquímico de ultra alta impedancia interna (~100 M&Omega;) que genera una señal diminuta (~59.16 mV por unidad de pH).
            Cuando la fuente de corriente inyecta amperios a través del baño galvánico o los TRIACs conmutan resistencias calefactoras, se crean gradientes de potencial y lazos de tierra en la disolución que interfieren directamente con la señal del bulbo de vidrio.
            <strong>Procedimiento de diseño:</strong> La estación incluye un módulo de 2 relevadores con aislamiento bipolar que desconecta físicamente los electrodos de potencia durante la medición de pH.
            Para obtener mediciones exactas y estables, la toma de pH debe realizarse como <strong>muestreo intermitente con la celda en reposo</strong> o mediante alícuotas extraídas con pipeta.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #38bdf8;">
          <h4 style="color:#38bdf8; margin-bottom:6px;">6. ¿Cuándo debo operar desde la interfaz web móvil y cuándo desde el SCADA en Python?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            • <strong>Interfaz Web Móvil (<code>http://192.168.4.1</code>):</strong> Diseñada para la interacción rápida y directa en el laboratorio desde su teléfono celular o tablet. Es ideal para inspección visual a pie de tina, calibración guiada de sensores de pH con soluciones buffer estándar pH 4.01 / 7.00, encendido de prueba de actuadores y actualización inalámbrica de firmware por OTA.<br>
            • <strong>Monitor SCADA de Escritorio (<code>Iniciar_Telemetria.bat</code>):</strong> Diseñado para la ejecución de ensayos formales de investigación. Es indispensable cuando se requiere automatizar recetas por fases ISA-88 con temporizadores programados, registrar telemetría masiva continua en archivos CSV en disco, supervisar la balanza de Faraday y generar las 5 figuras científicas a 300 DPI para informes o tesis.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #10b981;">
          <h4 style="color:#10b981; margin-bottom:6px;">7. ¿Por qué las gráficas en vivo del SCADA tienen un buffer de 60 segundos mientras que la Suite Científica muestra horas completas?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            Se trata de una estrategia fundamental de diseño para sistemas en tiempo real:
            El monitor SCADA en vivo renderiza a 10 Hz mediante Matplotlib embebido en Tkinter. Si acumulara cientos de miles de puntos en memoria para redibujarlos en cada ciclo, la interfaz gráfica colapsaría por sobrecarga de renderizado.
            Por ello, la pantalla en vivo mantiene un buffer deslizante ágil de 60 segundos optimizado para supervisión de control en tiempo presente.
            Paralelamente, el hilo de grabación a disco (<code>grabacion.py</code>) almacena cada muestra en un archivo CSV continuo sin límite de tiempo.
            Al concluir el experimento, la Suite de Graficación Científica (<code>graficar_datos.py</code>) toma ese archivo CSV completo y procesa todas las horas del ensayo para producir figuras científicas de calidad editorial a 300 DPI.
          </p>
        </div>

        <div class="card" style="border-left:4px solid #f59e0b;">
          <h4 style="color:#f59e0b; margin-bottom:6px;">8. ¿Dónde se guardan los datos experimentales y cómo abrirlos en Excel, OriginLab o MATLAB?</h4>
          <p style="font-size:0.85rem; line-height:1.55; color:#cbd5e1;">
            Todos los registros se guardan automáticamente en la subcarpeta <code>telemetria/experimentos/</code> bajo la nomenclatura <code>ensayo_AAAAMMDD_HHMMSS.csv</code>.
            Son archivos de texto plano estructurados en columnas separadas por comas (formato CSV estándar en codificación UTF-8).
            Pueden abrirse directamente en <strong>Microsoft Excel</strong> haciendo doble clic sobre el archivo, o importarse en <strong>OriginLab</strong>, <strong>MATLAB</strong> o <strong>Python (Pandas)</strong> mediante la función estándar <code>read_csv()</code> para análisis estadístico, ajuste cinético y cálculo de densidades de corriente.
          </p>
        </div>
      </div>
    </section>

    <!-- SECCIÓN 16: CRÉDITOS Y RECONOCIMIENTOS -->
    <section id="creditos">
      <h2 class="section-title">📜 16. Créditos, Autoría & Reconocimientos del Proyecto</h2>
      <p>
        Metadatos técnicos, autoría del desarrollo ciberfísico, marco de aplicación y reconocimiento a las herramientas y librerías de código abierto utilizadas en esta estación:
      </p>

      <div class="card-grid" style="grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));">
        <div class="card" style="border-top:4px solid #38bdf8;">
          <h4 style="color:#38bdf8; margin-bottom:8px;">🎓 Tesis de Grado & Propósito Académico</h4>
          <p style="font-size:0.84rem; line-height:1.5; color:#cbd5e1;">
            <strong>Proyecto:</strong> Sistema Automatizado de Electrodeposición y Galvanoplastia Química.<br>
            <strong>Aplicación:</strong> Estación Piloto de Control Multizona, Fuente Galvánica de Corriente VCSS y Metrología de pH en Celda Hull.<br>
            <strong>Área:</strong> Ingeniería en Automatización, Control de Procesos Electroquímicos y Sistemas Ciberfísicos Embebidos.<br>
            <strong>Desarrollo y Autoría:</strong> Salvador (Arquitectura de Firmware FreeRTOS, Diseño de Circuitos Electrónicos VCSS, Software SCADA en Python y Suite Científica).
          </p>
        </div>

        <div class="card" style="border-top:4px solid #10b981;">
          <h4 style="color:#10b981; margin-bottom:8px;">⚙️ Pila Tecnológica del Sistema</h4>
          <p style="font-size:0.84rem; line-height:1.5; color:#cbd5e1;">
            • <strong>Microcontrolador Maestro:</strong> Espressif ESP32-S3 (Dual Xtensa LX7 @ 240 MHz, 16 MB Flash, 8 MB PSRAM) bajo FreeRTOS SMP v1.3.<br>
            • <strong>Co-procesador de Potencia AC:</strong> Microchip ATmega328P @ 16 MHz (Arduino Nano) con interrupción ZCS INT1 a 120 Hz.<br>
            • <strong>Software SCADA:</strong> Python 3.9+ con GUI modular en Tkinter y comunicación REST JSON asíncrona a 10 Hz.<br>
            • <strong>Servidor Web Embebido:</strong> Arquitectura MVC en C++ con interfaces táctiles responsivas Glassmorphism Dark Mode.<br>
            • <strong>Visualización Científica:</strong> Matplotlib, NumPy y Pandas para exportación editorial a 300 DPI.
          </p>
        </div>
      </div>

      <div class="card" style="margin-top:16px;">
        <h4 style="color:#c084fc; margin-bottom:10px;">🌐 Reconocimiento a Librerías y Proyectos de Código Abierto</h4>
        <p style="font-size:0.84rem; line-height:1.5; color:#cbd5e1; margin-bottom:10px;">
          Esta plataforma de investigación se construyó sobre la sólida base del ecosistema de software y hardware de código abierto. Se reconoce y agradece el trabajo de las siguientes comunidades y proyectos:
        </p>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px;">
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#38bdf8;">Espressif Systems</strong><br>
            Por el framework ESP-IDF, la integración de FreeRTOS SMP Dual-Core y el soporte del microcontrolador ESP32-S3 en el ecosistema Arduino.
          </div>
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#10b981;">Adafruit Industries</strong><br>
            Por el desarrollo y mantenimiento de los controladores de instrumentación I2C y SPI: <code>Adafruit ADS1X15</code>, <code>Adafruit MCP4725</code>, <code>Adafruit AHTX0</code>, <code>Adafruit BMP280</code> y <code>MAX6675</code>.
          </div>
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#f59e0b;">Python Software Foundation</strong><br>
            Por el lenguaje Python 3 y su rica biblioteca estándar de hilos, conectividad HTTP y estructuras de datos para computación científica.
          </div>
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#c084fc;">Matplotlib Development Team</strong><br>
            Por la biblioteca de graficado científico utilizada para renderizar los oscilogramas embebidos y generar las figuras a 300 DPI.
          </div>
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#38bdf8;">Mermaid-js & KaTeX</strong><br>
            Por los motores de renderizado en cliente para diagramas arquitecturales ISA-88 / FreeRTOS y tipografía de ecuaciones matemáticas.
          </div>
          <div style="background:rgba(15,23,42,0.6); padding:10px 14px; border-radius:10px; border:1px solid rgba(51,65,85,0.4); font-size:0.82rem; line-height:1.45;">
            <strong style="color:#10b981;">Antigravity IDE (Google DeepMind)</strong><br>
            Por el entorno de pair-programming y navegación contextual inteligente que facilitó la integración, trazabilidad y refinamiento del proyecto.
          </div>
        </div>
      </div>

      <div class="alert alert-info" style="margin-top:16px;">
        <strong>📄 Licencia y Disponibilidad Académica:</strong>
        El código fuente, esquemáticos y manuales de este proyecto se ponen a disposición bajo principios de libre consulta y replicabilidad científica para fines de docencia, investigación académica y desarrollo industrial en ingeniería electroquímica.
      </div>
    </section>

  </main>"""

if section_14_end_target in html:
    html = html.replace(section_14_end_target, new_sections_block)
    print("Sections 14.8, 15 (FAQ), and 16 (Credits) inserted successfully!")
else:
    print("WARNING: section_14_end_target not found!")

# C. Update Sidebar navigation
old_sidebar_end = """      <a href="#datasheets-ref">📚 13. Biblioteca de Datasheets (PDF)</a>
      <a href="#codigo-fuente">💻 14. Código Fuente & Antigravity IDE</a>
    </nav>"""

new_sidebar_end = """      <a href="#datasheets-ref">📚 13. Biblioteca de Datasheets (PDF)</a>
      <a href="#codigo-fuente">💻 14. Código Fuente & Antigravity IDE</a>
      <a href="#comparativa-metodos" style="padding-left:24px;font-size:0.78rem;color:#38bdf8;">⚖️ 14.8 Comparativa de Métodos</a>
      <a href="#faq">❓ 15. Preguntas Frecuentes (FAQ)</a>
      <a href="#creditos">📜 16. Créditos & Autoría</a>
    </nav>"""

if old_sidebar_end in html:
    html = html.replace(old_sidebar_end, new_sidebar_end)
    print("Sidebar navigation links updated successfully!")
else:
    print("WARNING: old_sidebar_end not found!")

# D. Update Hero Banner Buttons
old_hero_buttons = """        <a href="#datasheets-ref" class="btn btn-outline">📚 Datasheets PDF</a>
        <a href="#codigo-fuente" class="btn btn-outline">💻 Código Fuente & IDE</a>
      </div>"""

new_hero_buttons = """        <a href="#datasheets-ref" class="btn btn-outline">📚 Datasheets PDF</a>
        <a href="#codigo-fuente" class="btn btn-outline">💻 Código Fuente & IDE</a>
        <a href="#faq" class="btn btn-outline">❓ FAQ</a>
        <a href="#creditos" class="btn btn-outline">📜 Créditos</a>
      </div>"""

if old_hero_buttons in html:
    html = html.replace(old_hero_buttons, new_hero_buttons)
    print("Hero buttons updated successfully!")
else:
    print("WARNING: old_hero_buttons not found!")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated HTML manual saved successfully!")

# 2. UPDATE MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md
md_path = 'documentos/MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md'
with open(md_path, 'r', encoding='utf-8') as f:
    md = f.read()

# Add to markdown at the end of section 9
md_append = """

---

### 9.10 Comparativa de Métodos de Control: ¿Por qué existen 2 Alternativas?

El proyecto implementa una dualidad fundamentada de métodos tanto en el control físico de potencia como en la supervisión operativa:

#### A. Control de Potencia Térmica AC (Calefacción de Tinas)
* **Método 1: Recorte de Ángulo de Fase (&alpha;-Firing a 120 Hz) con Co-procesador Arduino Nano (`nano.ino`):**
  * *Ventajas:* Regulación analógica ultra-fina y continua en cada semiciclo de 8.33 ms. Garantiza una estabilidad de $\\pm 0.2\\,^\\circ\\text{C}$ sin oscilaciones en reactores pequeños como la Celda Hull (267 mL).
  * *Desventajas:* Requiere un microcontrolador esclavo dedicado (Arduino Nano) con interrupción crítica `INT1` para no verse afectado por el jitter de red del ESP32; no puede actualizarse por la interfaz web OTA (exige cable USB físico); genera armónicos de conmutación (ruido EMI/dv/dt) que demandan filtrado RC snubber y optoacoplamiento estricto.
* **Método 2: Paquetes de Ciclos / Ventana Proporcional de Tiempo (`nano2/` con JELDimmer2 o directo en ESP32):**
  * *Ventajas:* Conmuta exclusivamente en el cruce por cero de la senoidal (cero ruido electromagnético de alta frecuencia); algoritmo simplificado que podría ejecutarse directamente en el ESP32 sin microcontrolador esclavo, lo que permitiría actualización 100% inalámbrica por OTA.
  * *Desventajas:* En ventanas de 3 segundos produce variaciones cíclicas de temperatura (oleadas térmicas de $\\pm 1.5\\,^\\circ\\text{C}$) inadmisibles en la Celda Hull de 267 mL (aunque es viable para tinas industriales de 20 a 100 litros con alta inercia térmica).

#### B. Métodos de Supervisión y Operación (Web Móvil vs SCADA de Escritorio)
* **Vía Web Móvil (`http://192.168.4.1`):** Cero instalación de software, accesible desde cualquier celular o tablet a pie de reactor, actualización remota del ESP32 por OTA, calibración asistida de pH. Limitada a un buffer circular en memoria RAM y control puntual.
* **Vía Monitor SCADA de Escritorio (`telemetria/app.py`):** Registro continuo a disco en CSV sin límite de tiempo, ejecución automatizada de recetas multietapa ISA-88 con temporizadores programados, balanza virtual de Faraday ($Q=\\int I dt$), osciloscopio virtual y suite de generación de figuras científicas a 300 DPI.

---

## 10. Preguntas Frecuentes (FAQ)

1. **¿Por qué el Arduino Nano no se actualiza por la interfaz web OTA (`/update`)?**  
   Porque el servidor web y el gestor OTA residen físicamente en la memoria Flash del ESP32-S3. El Arduino Nano (ATmega328P) es un microcontrolador esclavo independiente aislado galvánicamente que solo se comunica por UART2 y no cuenta con líneas de reset (DTR) conectadas al ESP32 para activar el bootloader remoto. Debe actualizarse mediante cable USB directo desde Arduino IDE.
2. **¿Por qué se utilizó un Arduino Nano y no se ejecutó el control de TRIACs en el ESP32?**  
   Por determinismo temporal estricto en microsegundos y aislamiento eléctrico. Las tareas de red Wi-Fi y FreeRTOS en el ESP32 introducen jitter que desestabilizaría el disparo de fase a 60 Hz. El ATmega328P atiende la interrupción externa INT1 en 8 &mu;s sin perturbaciones de red.
3. **¿Qué sucede si el ESP32 se congela o se pierde la comunicación serie con el Arduino Nano?**  
   El Arduino Nano cuenta con un Perro Guardián UART de 3000 ms. Si no recibe tramas válidas del ESP32 durante 3 segundos, fuerza de inmediato el apagado total de los 4 TRIACs (corte Fail-Safe) para evitar sobrecalentamiento.
4. **Al subir el código al Nano aparece `avrdude: stk500_recv(): programmer is not responding`. ¿Qué hacer?**  
   En Arduino IDE, vaya a `Herramientas -> Procesador` y cambie a **`ATmega328P (Old Bootloader)`** (57600 baudios). Asegúrese de desconectar los 110V/220V AC antes de conectar el cable USB.
5. **¿Por qué la lectura de pH fluctúa cuando la celda de corriente o calentadores están activos?**  
   Por corrientes parásitas y lazos de tierra en la disolución que afectan al electrodo de vidrio (~100 M&Omega;). La estación cuenta con un módulo de relevadores de aislamiento bipolar para medir con la celda desconectada o mediante alícuotas.
6. **¿Cuándo usar la interfaz web móvil y cuándo el SCADA de escritorio?**  
   Use la web móvil para inspección rápida a pie de tina, calibración de electrodos de pH y actualización OTA. Use el SCADA para ensayos formales de investigación, recetas automatizadas ISA-88, culombimetría y gráficas a 300 DPI.
7. **¿Por qué las gráficas en vivo del SCADA muestran 60 segundos mientras que la Suite Científica procesa todo el ensayo?**  
   Para evitar sobrecarga de CPU y congelamiento de la GUI en tiempo real a 10 Hz. La Suite Científica lee el archivo CSV continuo guardado en disco al finalizar el ensayo y procesa la totalidad del experimento en alta resolución.
8. **¿Dónde se guardan los datos experimentales?**  
   En `telemetria/experimentos/ensayo_AAAAMMDD_HHMMSS.csv`, compatibles directamente con Excel, OriginLab y MATLAB.

---

## 11. Créditos, Autoría & Reconocimientos del Proyecto

* **Proyecto / Tesis:** Sistema Automatizado de Electrodeposición y Galvanoplastia Química.
* **Autoría y Desarrollo:** Salvador (Ingeniería de Automatización, Firmware FreeRTOS SMP, Diseño Electrónico VCSS, SCADA Python y Suite Científica).
* **Plataforma:** ESP32-S3 Dual-Core (RTOS 1.3) + Arduino Nano (ATmega328P) + Python 3.9+ SCADA.
* **Reconocimiento de Librerías y Proyectos Open Source:**
  * **Espressif Systems:** ESP-IDF y Arduino ESP32 Core.
  * **Adafruit Industries:** Controladores de instrumentación (`Adafruit ADS1X15`, `Adafruit MCP4725`, `Adafruit AHTX0`, `Adafruit BMP280`, `MAX6675`).
  * **Python Software Foundation & Matplotlib Team:** Ecosistema científico de análisis de datos.
  * **Mermaid-js & KaTeX:** Renderizado de arquitectura y fórmulas matemáticas.
  * **Antigravity IDE (Google DeepMind):** Entorno unificado de navegación y pair-programming inteligente.
* **Licencia:** Libre consulta y replicabilidad académica para docencia e investigación electroquímica.
"""

# Update Table of Contents in MD if present
md_toc_target = "* 9. [Arquitectura del Software, Librerías y Entornos de Desarrollo](#9-arquitectura-del-software-librerias-y-entornos-de-desarrollo)"
md_toc_replacement = """* 9. [Arquitectura del Software, Librerías y Entornos de Desarrollo](#9-arquitectura-del-software-librerias-y-entornos-de-desarrollo)
  * [9.10 Comparativa de Métodos de Control](#910-comparativa-de-metodos-de-control-por-que-existen-2-alternativas)
* 10. [Preguntas Frecuentes (FAQ)](#10-preguntas-frecuentes-faq)
* 11. [Créditos, Autoría & Reconocimientos del Proyecto](#11-creditos-autoria--reconocimientos-del-proyecto)"""

if md_toc_target in md:
    md = md.replace(md_toc_target, md_toc_replacement)
    print("MD Table of Contents updated successfully!")

md += md_append

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md)
print("Updated Markdown manual saved successfully!")

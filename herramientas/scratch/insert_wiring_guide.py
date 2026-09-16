# -*- coding: utf-8 -*-
import os

manual_path = r"C:\Proyecto\Proyecto\documentos\MANUAL_DE_OPERACION_QUIMICA.html"

with open(manual_path, "r", encoding="utf-8") as f:
    content = f.read()

target_marker = """      <div class="figure-box">
        <img src="imagenes/sistema.png" alt="Esquema de Hardware del Sistema" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 1.1: Diagrama de interconexión eléctrica del sistema (Alimentación única 12V 10A, Pre-regulador Buck 6.80V, LDOs, ESP32 y sensores).</div>
      </div>
    </section>"""

if target_marker not in content:
    print("Error: Target marker not found in manual!")
    exit(1)

wiring_guide_html = """      <div class="figure-box">
        <img src="imagenes/sistema.png" alt="Esquema de Hardware del Sistema" onclick="openModal(this.src)">
        <div class="figure-caption">Figura 1.1: Diagrama de interconexión eléctrica del sistema (Alimentación única 12V 10A, Pre-regulador Buck 6.80V, LDOs, ESP32 y sensores).</div>
      </div>

      <!-- SUBSECCIÓN 1.2: GUÍA DE CABLEADO Y PINOUT FÍSICO -->
      <h3 class="subsection-title" id="guia-cableado">1.2 Guía Completa de Conexiones y Pinout Físico ("¿Qué va conectado a qué?")</h3>
      <p>
        Para facilitar el ensamble, mantenimiento, diagnóstico y reproducción del equipo sin ambigüedades,
        a continuación se detalla la distribución exacta de pines, bornes, clemas de tornillos y señales entre todos los módulos del sistema.
      </p>

      <div class="alert alert-warning">
        <strong>⚡ REGLA DE ORO DE ALIMENTACIÓN Y TIERRA COMÚN:</strong>
        Todos los niveles de tensión (<strong>+12V DC</strong> de potencia, <strong>+6.80V</strong> del Buck, <strong>+5.0V</strong> del LM7805 y <strong>+3.3V</strong> del LM1117)
        <strong>deben compartir una única masa común (GND en estrella)</strong> conectada al negativo de la fuente de 12V.
        Nunca conecte los 5V ni los 12V directamente a los pines del ESP32-S3 (su nivel lógico es estrictamente 3.3V).
      </div>

      <!-- 1.2.1 DISTRIBUCIÓN DE ALIMENTACIÓN -->
      <h4 style="color:#e2e8f0; margin-top:20px; margin-bottom:10px;">1.2.1 Cascada de Regulación y Rieles de Tensión</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Riel / Etapa</th>
              <th>Módulo Generador</th>
              <th>Tensión Nominal</th>
              <th>Pines de Origen</th>
              <th>Destino Físico (Carga / Consumidores)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Potencia Primaria</strong></td>
              <td>Fuente Conmutada (SMPS)</td>
              <td><code>+12.0 V DC (10A)</code></td>
              <td>Bornes <code>V+</code> y <code>V-</code></td>
              <td>
                • Entrada <code>Vin+ / Vin-</code> del Módulo Buck LM2596<br>
                • Clema <code>VDD</code> de la placa casera VCSS (alimentación de celda y LM358N)
              </td>
            </tr>
            <tr>
              <td><strong>Pre-Regulador Buck</strong></td>
              <td>Módulo LM2596 (150 kHz)</td>
              <td><code>+6.80 V DC (Display)</code></td>
              <td>Bornes <code>OUT+</code> y <code>OUT-</code></td>
              <td>
                • Pin 1 (Input) del regulador lineal LM7805 (TO-220)<br>
                • Pin 2 (GND) a masa común
              </td>
            </tr>
            <tr>
              <td><strong>Lógica / Analógico 5V</strong></td>
              <td>Regulador Lineal LM7805</td>
              <td><code>+5.0 V DC (Limpio)</code></td>
              <td>Pin 3 (Output)</td>
              <td>
                • Pin <code>5V</code> de placa Arduino Nano<br>
                • Terminal <code>VCC</code> del Módulo de 2 Relevadores 5V<br>
                • Pines <code>VCC</code> de los 2 módulos de pH PH-4502C<br>
                • Pin 3 (Input) del regulador LDO LM1117-3.3 (TO-220)
              </td>
            </tr>
            <tr>
              <td><strong>Lógica / Sensores 3.3V</strong></td>
              <td>Regulador Lineal LM1117-3.3</td>
              <td><code>+3.3 V DC</code></td>
              <td>Pin 2 (Output / Tab)</td>
              <td>
                • Pin <code>3V3</code> del ESP32-S3 DevKit<br>
                • Terminales <code>VDD</code> de ADS1115 (0x48), MCP4725 (0x60), AHT20/BMP280<br>
                • Terminales <code>VCC</code> de los 4 módulos termopar MAX6675 SPI
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 1.2.2 DETALLE DE LA PLACA CASERA VCSS -->
      <h4 style="color:#e2e8f0; margin-top:24px; margin-bottom:10px;">1.2.2 Placa Casera del Sumidero de Corriente (VCSS PCB DIY)</h4>
      <p>
        La placa casera del sumidero de corriente constante alberga el amplificador operacional dual LM358N, los 2 transistores MOSFET IRLZ44N y las 2 resistencias cerámicas de cemento de 10W (1.0 &Omega;).
        Cuenta con <strong>3 pares de clemas de tornillo</strong> y <strong>2 pines header macho</strong> organizados de la siguiente forma:
      </p>

      <div class="code-box" style="background:#090d16; border:1px solid #0284c7; padding:18px; border-radius:10px;">
<pre style="color:#38bdf8; font-weight:700; font-size:0.85rem; line-height:1.45;">
+---------------------------------------------------------------------------------------------------+
|                        PLACA CASERA DEL SUMIDERO VCSS (DISTRIBUCIÓN FÍSICA)                       |
|                                                                                                   |
|    [CLEMA 1: REFERENCIA GND]       [CLEMA 2: CONTROL & POTENCIA]        [CLEMA 3: SALIDAS CELDA]  |
|       [ GND ]    [ RefGND ]            [ VREF ]      [ VDD ]              [ OUT+ ]    [ OUT- ]    |
|          |           |                    |             |                    |           |        |
|      GND Común   GND de Señal        VOUT analógica   +12V SMPS           Hacia COM   Hacia COM   |
|      del Sistema  del MCP4725         del MCP4725    (Alim. LM358)         Relé 1      Relé 2     |
|                                                                                                   |
|                        CIRCUITO ACTIVO: OpAmp LM358N (VCC = +12V VDD)                             |
|                                                                                                   |
|             MOSFET Rama 1 (IRLZ44N)                           MOSFET Rama 2 (IRLZ44N)             |
|          R_Shunt 1 (10W / 1.0 Ohm Blanca)                  R_Shunt 2 (10W / 1.0 Ohm Blanca)       |
|                         |                                                 |                       |
|                  [ HEADER SH1 ]                                    [ HEADER SH2 ]                 |
|                   (Pin Macho)                                       (Pin Macho)                   |
|                         |                                                 |                       |
|                         +-------------> Hacia ADS1115 Canal A2 <----------+                       |
|                         +-------------> Hacia ADS1115 Canal A3 <----------+                       |
|                         (Indiferente: Ambos miden caídas 0-3.53V de ramas balanceadas)            |
+---------------------------------------------------------------------------------------------------+
</pre>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Clema / Conector</th>
              <th>Nombre del Borne</th>
              <th>Tipo de Señal</th>
              <th>Conectado Físicamente a</th>
              <th>Función en el Circuito</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td rowspan="2"><strong>Clema 1 (Par Izquierdo)</strong></td>
              <td><code>GND</code></td>
              <td>Masa Potencia</td>
              <td>Barra de GND común (Negativo de 12V)</td>
              <td>Retorno de potencia de los shunts hacia la fuente.</td>
            </tr>
            <tr>
              <td><code>RefGND</code></td>
              <td>Masa Señal</td>
              <td>Pin <code>GND</code> del módulo DAC MCP4725</td>
              <td>Tierra analógica de referencia limpia para evitar caídas de tensión parásitas en la lectura de consigna.</td>
            </tr>
            <tr>
              <td rowspan="2"><strong>Clema 2 (Par Central)</strong></td>
              <td><code>VREF</code></td>
              <td>Consigna Analógica</td>
              <td>Pin <code>VOUT</code> del módulo DAC MCP4725</td>
              <td>Tensión de referencia analógica (0.00 V a 3.53 V) que fija la corriente deseada ($I = V_{\text{REF}} \times G_m$).</td>
            </tr>
            <tr>
              <td><code>VDD</code></td>
              <td>Alimentación +12V</td>
              <td>Línea positiva +12V de la fuente SMPS</td>
              <td>Alimenta el riel de potencia de la celda y el pin V+ (Pin 8) del operacional LM358N para asegurar plena excursión de compuerta ($V_{gs} \approx 6\text{--}10\text{ V}$).</td>
            </tr>
            <tr>
              <td rowspan="2"><strong>Clema 3 (Par Derecho)</strong></td>
              <td><code>OUT+</code></td>
              <td>Positivo Celda (+12V)</td>
              <td>Terminal <code>COM</code> del Relé 1 (Módulo de 2 Relés)</td>
              <td>Puenteado internamente al lado VDD (+12V). Conduce la corriente hacia el ánodo a través del contacto del relé.</td>
            </tr>
            <tr>
              <td><code>OUT-</code></td>
              <td>Retorno Celda (Sumidero)</td>
              <td>Terminal <code>COM</code> del Relé 2 (Módulo de 2 Relés)</td>
              <td>Conectado a los Drains de los dos MOSFETs IRLZ44N en paralelo. Es el sumidero que regula la corriente de retorno catódica.</td>
            </tr>
            <tr>
              <td rowspan="2"><strong>Headers Macho (Sensado)</strong></td>
              <td><code>HEADER SH1</code></td>
              <td>Caída de Tensión Shunt 1</td>
              <td>Canal <code>A2</code> del ADC ADS1115 (Pin Macho/Cable Dupont)</td>
              <td>Tensión analógica $V_{s1} = I_1 \times 1.0\,\Omega$. Rango 0 a 3.50 V para lectura culombimétrica en 16 bits.</td>
            </tr>
            <tr>
              <td><code>HEADER SH2</code></td>
              <td>Caída de Tensión Shunt 2</td>
              <td>Canal <code>A3</code> del ADC ADS1115 (Pin Macho/Cable Dupont)</td>
              <td>Tensión analógica $V_{s2} = I_2 \times 1.0\,\Omega$. Permite auditar el balance térmico entre ambas ramas.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 1.2.3 MÓDULO DE 2 RELEVADORES 5V (AISLAMIENTO BIPOLAR ZCS) -->
      <h4 style="color:#e2e8f0; margin-top:24px; margin-bottom:10px;">1.2.3 Módulo de 2 Relevadores 5V (Aislamiento Galvánico Bipolar ZCS)</h4>
      <p>
        Para garantizar que la celda electroquímica no tenga bucles de corriente parásita ni degrade la lectura de pH,
        el módulo de 2 relevadores conmuta <strong>simultáneamente tanto el polo positivo como el polo negativo de la celda</strong>:
      </p>

      <div class="code-box" style="background:#090d16; border:1px solid #10b981; padding:18px; border-radius:10px;">
<pre style="color:#34d399; font-weight:700; font-size:0.85rem; line-height:1.45;">
+---------------------------------------------------------------------------------------------------+
|                        MÓDULO DE 2 RELEVADORES 5V (AISLAMIENTO TOTAL BIPOLAR)                     |
|                                                                                                   |
|  Control Lógico (Pines de Entrada):                                                               |
|    • [ VCC ]   ---> Conectado a +5.0V (Salida LM7805)                                             |
|    • [ GND ]   ---> Conectado a Masa Común (GND)                                                  |
|    • [ IN1 ] --+                                                                                  |
|                +--> Puenteados juntos hacia el GPIO 20 del ESP32-S3 (Disparo ZCS Active-LOW)      |
|    • [ IN2 ] --+                                                                                  |
|                                                                                                   |
|  Contactos de Potencia:                                                                           |
|    RELÉ 1 (Aislamiento Ánodo +12V):                                                               |
|      • [ COM 1 ] <--- Recibe cable OUT+ de la placa VCSS (+12V VDD)                               |
|      • [ NO 1 ]  ---> Conecta al ÁNODO de la Celda Hull (o ánodo de electrodeposición)            |
|                                                                                                   |
|    RELÉ 2 (Aislamiento Cátodo / Sumidero):                                                        |
|      • [ COM 2 ] <--- Recibe cable OUT- de la placa VCSS (Drains MOSFETs)                         |
|      • [ NO 2 ]  ---> Conecta al CÁTODO / Probeta de ensayo en la Celda                           |
|                                                                                                   |
|  COMPORTAMIENTO METROLÓGICO:                                                                      |
|    • Cuando GPIO 20 = LOW (Fuente Activa): Ambos relés cierran contactos NO; la celda energiza.   |
|    • Cuando GPIO 20 = HIGH (Fuente Apagada o Muestreo pH): Ambos relés se abren; la cuba química   |
|      queda 100% flotante, permitiendo lecturas estables del electrodo de vidrio sin corrientes.   |
+---------------------------------------------------------------------------------------------------+
</pre>
      </div>

      <!-- 1.2.4 PINOUT ESP32-S3 -->
      <h4 style="color:#e2e8f0; margin-top:24px; margin-bottom:10px;">1.2.4 Pinout Completo del Nodo Maestro ESP32-S3 (N16R8)</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Pin ESP32-S3</th>
              <th>Nombre Señal</th>
              <th>Nivel Lógico</th>
              <th>Módulo / Dispositivo de Destino</th>
              <th>Descripción y Función</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>3V3</code></td>
              <td>VCC Lógica</td>
              <td>+3.3 V DC</td>
              <td>Salida del regulador LM1117-3.3 (TO-220)</td>
              <td>Alimentación del microcontrolador y sensores de 3.3V.</td>
            </tr>
            <tr>
              <td><code>GND</code></td>
              <td>Masa Común</td>
              <td>0 V</td>
              <td>Barra de GND en estrella</td>
              <td>Retorno común de lógica y comunicación.</td>
            </tr>
            <tr>
              <td><code>GPIO 8</code></td>
              <td>I2C SDA</td>
              <td>3.3V TTL</td>
              <td>Pines SDA de ADS1115, MCP4725, AHT20, BMP280</td>
              <td>Bus de datos serie I2C Fast-Mode (400 kHz). Pull-ups internos y en módulos.</td>
            </tr>
            <tr>
              <td><code>GPIO 9</code></td>
              <td>I2C SCL</td>
              <td>3.3V TTL</td>
              <td>Pines SCL de ADS1115, MCP4725, AHT20, BMP280</td>
              <td>Línea de reloj serie I2C (400 kHz).</td>
            </tr>
            <tr>
              <td><code>GPIO 18</code></td>
              <td>SPI SCK</td>
              <td>3.3V TTL</td>
              <td>Pines SCK de los 4 módulos MAX6675</td>
              <td>Reloj SPI compartido para digitalización de termopares.</td>
            </tr>
            <tr>
              <td><code>GPIO 19</code></td>
              <td>SPI MISO (SO)</td>
              <td>3.3V TTL</td>
              <td>Pines SO de los 4 módulos MAX6675</td>
              <td>Datos SPI recibidos desde los termopares hacia el ESP32 (Half-Duplex).</td>
            </tr>
            <tr>
              <td><code>GPIO 5</code></td>
              <td>CS Tina 1</td>
              <td>3.3V TTL</td>
              <td>Pin CS del MAX6675 Tina 1 (Desengrase Alcalino)</td>
              <td>Chip Select activo en nivel BAJO para lectura de Tina 1.</td>
            </tr>
            <tr>
              <td><code>GPIO 4</code></td>
              <td>CS Tina 2</td>
              <td>3.3V TTL</td>
              <td>Pin CS del MAX6675 Tina 2 (Decapado Alcalino)</td>
              <td>Chip Select activo en nivel BAJO para lectura de Tina 2.</td>
            </tr>
            <tr>
              <td><code>GPIO 13</code></td>
              <td>CS Tina 3</td>
              <td>3.3V TTL</td>
              <td>Pin CS del MAX6675 Tina 3 (Zincado Celda Hull)</td>
              <td>Chip Select activo en nivel BAJO para lectura de Tina 3.</td>
            </tr>
            <tr>
              <td><code>GPIO 14</code></td>
              <td>CS Tina 4</td>
              <td>3.3V TTL</td>
              <td>Pin CS del MAX6675 Tina 4 (Niquelado sobre Zinc)</td>
              <td>Chip Select activo en nivel BAJO para lectura de Tina 4.</td>
            </tr>
            <tr>
              <td><code>GPIO 17</code></td>
              <td>UART2 TX</td>
              <td>3.3V TTL</td>
              <td>Pin <code>RX (D0)</code> del Arduino Nano</td>
              <td>Transmisión asíncrona a 9600 bps de las tramas de potencia para los TRIACs.</td>
            </tr>
            <tr>
              <td><code>GPIO 20</code></td>
              <td>Disparo ZCS Relé</td>
              <td>3.3V TTL</td>
              <td>Entradas puenteadas <code>IN1</code> e <code>IN2</code> del Módulo de Relés</td>
              <td>Control de aislamiento galvánico de la celda (Active-LOW: 0V conecta, 3.3V aísla).</td>
            </tr>
            <tr>
              <td><code>GPIO 48</code></td>
              <td>WS2812 DIN</td>
              <td>3.3V TTL</td>
              <td>Baliza LED RGB Neopixel industrial</td>
              <td>Secuencia de datos unidireccional para los 13 códigos de estado lumínico.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 1.2.5 PINOUT ARDUINO NANO -->
      <h4 style="color:#e2e8f0; margin-top:24px; margin-bottom:10px;">1.2.5 Pinout del Nodo Esclavo Arduino Nano (Control AC de Calefacción)</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Pin Arduino Nano</th>
              <th>Función de Firmware</th>
              <th>Módulo / Dispositivo Conectado</th>
              <th>Descripción Operativa</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>5V</code></td>
              <td>Alimentación</td>
              <td>Salida +5.0V del regulador LM7805</td>
              <td>Alimentación del microcontrolador ATmega328P @ 16 MHz.</td>
            </tr>
            <tr>
              <td><code>GND</code></td>
              <td>Masa</td>
              <td>Barra de GND común</td>
              <td>Referencia de potencial común con el ESP32.</td>
            </tr>
            <tr>
              <td><code>Pin D0 (RX)</code></td>
              <td>UART RX Hardware</td>
              <td>Pin <code>GPIO 17</code> del ESP32-S3</td>
              <td>Recepción de tramas CSV de consignas de potencia térmica (9600 baud).</td>
            </tr>
            <tr>
              <td><code>Pin D3 (INT1)</code></td>
              <td>Cruce por Cero (ZC)</td>
              <td>Salida del optoacoplador 4N35 de placa MDAC4C</td>
              <td>Interrupción externa por flanco de bajada al ocurrir el cruce por cero de la red AC 60 Hz.</td>
            </tr>
            <tr>
              <td><code>Pin D7</code></td>
              <td>Gate Tina 1</td>
              <td>Opto-TRIAC 1 (MOC3021) / Calefactor 450W Tina 1</td>
              <td>Pulso de 80 &mu;s de disparo por ángulo de fase para Tina 1 (Desengrase).</td>
            </tr>
            <tr>
              <td><code>Pin D8</code></td>
              <td>Gate Tina 2</td>
              <td>Opto-TRIAC 2 (MOC3021) / Calefactor 450W Tina 2</td>
              <td>Pulso de 80 &mu;s de disparo por ángulo de fase para Tina 2 (Decapado).</td>
            </tr>
            <tr>
              <td><code>Pin D9</code></td>
              <td>Gate Tina 3</td>
              <td>Opto-TRIAC 3 (MOC3021) / Calefactor 18W Tina 3</td>
              <td>Pulso de 80 &mu;s de disparo por ángulo de fase para Tina 3 (Celda Hull).</td>
            </tr>
            <tr>
              <td><code>Pin D10</code></td>
              <td>Gate Tina 4</td>
              <td>Opto-TRIAC 4 (MOC3021) / Calefactor 450W Tina 4</td>
              <td>Pulso de 80 &mu;s de disparo por ángulo de fase para Tina 4 (Niquelado).</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 1.2.6 CONVERSIÓN ANALÓGICA ADS1115 -->
      <h4 style="color:#e2e8f0; margin-top:24px; margin-bottom:10px;">1.2.6 Mapa de Canales del Convertidor ADC ADS1115 (16 Bits - Dirección 0x48)</h4>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Canal ADS1115</th>
              <th>Variable Sensada</th>
              <th>Módulo / Origen Físico</th>
              <th>Rango Típico de Tensión</th>
              <th>Conversión a Variable Física</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>Canal A0</code></td>
              <td>Sonda pH Tina 1 (Zincado)</td>
              <td>Pin <code>Po</code> del módulo PH-4502C #1</td>
              <td>1.00 V a 3.00 V (Offset ~1.765 V)</td>
              <td>$\text{pH} = 7.0 - (V - V_{\text{offset}}) / S(T)$</td>
            </tr>
            <tr>
              <td><code>Canal A1</code></td>
              <td>Sonda pH Tina 2 (Niquelado)</td>
              <td>Pin <code>Po</code> del módulo PH-4502C #2</td>
              <td>1.00 V a 3.00 V (Offset ~1.765 V)</td>
              <td>$\text{pH} = 7.0 - (V - V_{\text{offset}}) / S(T)$</td>
            </tr>
            <tr>
              <td><code>Canal A2</code></td>
              <td>Corriente Rama Shunt 1 ($I_1$)</td>
              <td><code>HEADER SH1</code> de la placa casera VCSS</td>
              <td>0.00 V a 3.50 V ($1.0\text{ V/A}$)</td>
              <td>$I_1 = V_{s1} / 1.0\,\Omega$</td>
            </tr>
            <tr>
              <td><code>Canal A3</code></td>
              <td>Corriente Rama Shunt 2 ($I_2$)</td>
              <td><code>HEADER SH2</code> de la placa casera VCSS</td>
              <td>0.00 V a 3.50 V ($1.0\text{ V/A}$)</td>
              <td>$I_2 = V_{s2} / 1.0\,\Omega \quad \longrightarrow \quad I_{\text{total}} = I_1 + I_2$</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>"""

new_content = content.replace(target_marker, wiring_guide_html)

with open(manual_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Wiring guide successfully inserted into manual! Length: {len(new_content)} characters.")

# Lista de Materiales y Componentes (Bill of Materials - BOM)

🌐 **Idiomas / Languages**: [Español](BOM.md)

Este documento detalla la lista completa de componentes electrónicos, módulos de sensores, elementos de potencia, circuitos analógicos, disipadores térmicos y protecciones contra transitorios (TVS) necesarios para construir la planta modular de electrodeposición y galvanoplastia.

> [!NOTE]
> **Precios y Proveedores**: Los costos presentados son valores de referencia estimados en el mercado nacional e internacional (MXN / USD, tasa de cambio de referencia ≈ 18.5 MXN/USD, fecha base 2026) y están explícitamente marcados como **[a verificar con cotización formal]**. Las alternativas compatibles permiten mantener la funcionalidad ante contingencias de cadena de suministro.

---

## 1. Microcontroladores y Procesamiento

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Función en el Proyecto |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | **ESP32-S3-WROOM-1** (N16R8, 16MB Flash / 8MB PSRAM o N4 4MB Flash) | Espressif / Mouser / Emexbit | $130 MXN<br>($7.00 USD) | ESP32-S3-DevKitC-1, ESP32-WROOM-32 (requiere remapeo de GPIOs y ajuste de FreeRTOS SMP) | **Nodo Maestro Autónomo**: Servidor Web, Lazo PI Térmico, Control VCSS, NVS y Telemetría. Operación inalámbrica SoftAP sin cable USB de planta. |
| 1 | **Arduino Nano (ATmega328P)** | Arduino / RobotDyn / Emexbit | $85 MXN<br>($4.60 USD) | Arduino Pro Mini 5V 16MHz, Seeeduino Nano, ATmega328PB en placa dedicada | **Nodo Esclavo de Potencia**: Dimmer de 4 canales por Tiempo Proporcional en ventanas fijas de 3000 ms (firmware Nano2 con Watchdog de hardware `WDTO_1S` y tramas UART con CRC8). |

---

## 2. Sensores y Conversores de Señal Analógica/Digital

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Interfaz / Bus | Descripción / Función |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **ADS1115** | Texas Instruments / Adafruit / Emexbit | $95 MXN<br>($5.10 USD) | ADS1015 (12 bits), MCP3424 (18 bits I2C), ADS1118 (SPI) | I2C (`0x48`) | ADC de 16 bits (4 canales) a 860 SPS para lectura de pH (A0-A1) y shunts de corriente VCSS (A2 y A3 en modo single-ended). |
| 1 | **MCP4725** | Microchip / Adafruit / Emexbit | $65 MXN<br>($3.50 USD) | DAC8571 (16 bits I2C), DAC081C081, MCP4728 (cuádruple I2C) | I2C (`0x60`) | DAC de 12 bits para control analógico del sumidero de corriente (0–3.50V clamped). |
| 4 | **MAX6675** | Maxim Integrated / Analog Devices / AliExpress | $220 MXN<br>($11.90 USD lote 4) | MAX31855K (SPI, rango ampliado), MAX31856 (universal), MCP9600 (I2C) | SPI (SCK/SO) | Conversores de termopar Tipo K con compensación de junta fría (0–1024 °C). |
| 4 | **Termopares Tipo K** | Steren / Emexbit / Omega Engineering | $280 MXN<br>($15.10 USD lote 4) | Sondas RTD PT100/PT1000 (requiere circuito MAX31865), NTC 100k blindadas (limitadas a 120 °C) | Analógico | Sondas de temperatura para las 4 tinas químicas (vainas de acero inoxidable 316). |
| 2 | **PH-4502C** | DFRobot / Emexbit / AliExpress | $340 MXN<br>($18.40 USD lote 2) | DFRobot Gravity Analog pH Sensor v2, E-201-C con preamp INA128 | Analógico | Módulos acondicionadores analógicos con electrodos de vidrio conector BNC para pH. |
| 1 | **AHT20 + BMP280** | ASAIR / Bosch Sensortec / Emexbit | $80 MXN<br>($4.30 USD) | BME280 (I2C/SPI), SHT31 + BMP280 en módulos separados | I2C (`0x38`/`0x77`) | Módulo combinado ambiental (Temperatura, Humedad Relativa y Presión atmosférica). |

---

## 3. Etapa Analógica del Sumidero de Corriente (Circuito Proteus)

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Encapsulado / Valor | Función en el Circuito |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **LM358N** | Texas Instruments / STMicroelectronics / Emexbit | $16 MXN<br>($0.85 USD) | MCP6002 (Rail-to-Rail 5V), TLV2372, LM2904 | DIP-8 / SOIC-8 | Amplificador operacional dual en retroalimentación negativa para control del sumidero VCSS. |
| 2 | **IRLZ44Z / IRLZ44N** | Infineon / Vishay / Emexbit | $65 MXN<br>($3.50 USD par) | FQP30N06L, STP40NF10L, IRL3803, IRLZ34N (Logic Level 5V $V_{GS(th)} \le 2.0\text{V}$) | TO-220 | Transistores MOSFET de potencia N-Channel con disparo a nivel lógico (5V). |
| 2 | **Resistencias de Shunt 1.0 $\Omega$ / 10W (Cerámicas de Cemento)** | Yageo / Ohmite / Emexbit | $40 MXN<br>($2.15 USD par) | Resistencias con disipador metálico en aluminio 25W/50W (tipo Dale RH-25), Shunt manganina 4 hilos | Cerámica SQP 10W (Wirewound ignífuga) | Sensores de corriente Kelvin de retroalimentación en lazo cerrado del sumidero VCSS (caída 1.0 V/A). |
| 2 | **Resistencias 100 $\Omega$** | Genérico / Steren | $4 MXN<br>($0.20 USD par) | Resistencias película metálica 47 $\Omega$ a 220 $\Omega$ (1/4W) | 1/4W (Película metálica 1%) | Resistencias de amortiguamiento y protección de Gate contra oscilaciones parásitas. |
| 2 | **Disipadores Térmicos TO-220 ($R_{\theta SA} \le 5.0\ ^\circ\text{C/W}$)** | Fischer Elektronik / Aavid Thermalloy / Emexbit | $50 MXN<br>($2.70 USD par) | Bloque de aluminio extruido común con aisladores Sil-Pad ($R_{\theta SA} \le 2.5\ ^\circ\text{C/W}$) | Aleteado TO-220 (25×34×12 mm o superior) | Disipación térmica de los MOSFETs IRLZ44N para evitar fuga térmica y deriva de $g_m$. |

---

### 3.1 Justificación Técnica de Resistencias de 10W (Cerámicas Blancas de Cemento)
En el sumidero de corriente VCSS, la consigna está limitada rígidamente por firmware a $I_{\text{total}} = 3.50\text{ A}$ (máximo $I_{\text{rama}} = 1.75\text{ A}$ por rama balanceada). La potencia máxima en régimen continuo por resistencia es:
$$P = I_{\text{rama}}^2 \cdot R = (1.75\text{ A})^2 \cdot 1.0\,\Omega = 3.06\text{ W}$$
Operando a $3.06\text{ W}$ frente a los **10W nominales** de cada resistencia cerámica blanca (tipo SQP / alambre devanado ignífugo), se garantiza un factor de derating térmico seguro del **69.4%** sin sobrecalentamiento crítico.

---

### 3.2 Especificación Térmica y Dimensionamiento de Disipadores para MOSFETs (TO-220)
Los transistores MOSFET IRLZ44N operan en región activa lineal como sumidero de corriente controlado por tensión (VCSS). A corriente máxima de régimen:
- Corriente de rama balanceada: $I_{\text{rama}} = 1.75\text{ A}$.
- Tensión de alimentación de celda: $V_{DD} = 12.0\text{ V}$.
- Caída de tensión típica en celda electroquímica Hull: $V_{\text{celda}} \approx 6.0\text{--}8.0\text{ V}$ (dependiendo de conductividad del baño de zincado).
- Caída en resistencia de shunt: $V_{\text{shunt}} = 1.75\text{ A} \times 1.0\,\Omega = 1.75\text{ V}$.
- Caída en cableado y contactos de relé: $V_{\text{cable}} \approx 0.25\text{ V}$.
- Tensión Drain-Source nominal:
  $$V_{DS} = V_{DD} - V_{\text{celda}} - V_{\text{shunt}} - V_{\text{cable}} \approx 12.0\text{V} - 7.0\text{V} - 1.75\text{V} - 0.25\text{V} = 3.0\text{ V}$$
- En el caso más desfavorable de baja impedancia en celda (arranque en frío o solución de alta salinidad con $V_{\text{celda}} \approx 6.0\text{ V}$):
  $$V_{DS,\text{max}} = 12.0 - 6.0 - 1.75 - 0.25 = 4.0\text{ V}$$
  $$P_{D,\text{transistor}} \approx 1.75\text{ A} \times 2.0\text{ V} \text{ (nominal)} \quad \text{hasta} \quad 3.50\text{ W} \text{ (peor caso continuo)}$$

#### Ecuación de Resistencia Térmica y Margen de Juntura:
Para disipar $P_D = 3.50\text{ W}$ en encapsulado TO-220:
- Resistencia unión-cápsula: $R_{\theta JC} = 1.8\ ^\circ\text{C/W}$ (IRLZ44N según fabricante).
- Resistencia cápsula-disipador con almohadilla de mica o Sil-Pad con grasa térmica: $R_{\theta CS} = 0.5\ ^\circ\text{C/W}$.
- Temperatura ambiente máxima en planta/gabinete: $T_A = 40.0\ ^\circ\text{C}$.
- Límite de diseño para temperatura de juntura: $T_{J,\text{max}} \le 85.0\ ^\circ\text{C}$ (derating amplio frente al máximo absoluto de $175\ ^\circ\text{C}$).

$$\Delta T = T_{J,\text{max}} - T_A = 85.0\ ^\circ\text{C} - 40.0\ ^\circ\text{C} = 45.0\ ^\circ\text{C}$$
$$R_{\theta JA,\text{total}} = \frac{\Delta T}{P_D} = \frac{45.0\ ^\circ\text{C}}{3.50\text{ W}} = 12.86\ ^\circ\text{C/W}$$
$$R_{\theta SA} = R_{\theta JA,\text{total}} - R_{\theta JC} - R_{\theta CS} = 12.86 - 1.80 - 0.50 = 10.56\ ^\circ\text{C/W}$$

> [!IMPORTANT]
> **Requerimiento Normativo del Disipador**:
> Para garantizar estabilidad térmica ante flujo de aire restringido en gabinete cerrado, **se especifica un disipador con $R_{\theta SA} \le 5.0\ ^\circ\text{C/W}$** (por ejemplo modelo Fischer Elektronik SK 129 / Aavid 577002 o equivalente aleteado de 25×34×12 mm). Con esta especificación:
> $$T_J = 40.0\ ^\circ\text{C} + 3.50\text{ W} \cdot (1.8 + 0.5 + 5.0)\ ^\circ\text{C/W} = 40.0 + 25.55 = 65.55\ ^\circ\text{C}$$
> El silicio opera a $< 66\ ^\circ\text{C}$, garantizando que el punto de operación permanezca estable sin embalamiento térmico ni degradación prematura.

---

### 3.3 Distribución de Clemas y Pines en la Placa Casera VCSS
La placa casera cuenta con 3 pares de clemas de tornillo y 2 pines header macho para su interconexión:
* **Clema 1 (Referencias):**
  * `GND`: Conectado a la masa común de potencia y retorno del sistema.
  * `RefGND`: Cable GND de referencia proveniente del DAC MCP4725 para evitar bucles de masa.
* **Clema 2 (Control y Alimentación):**
  * `VREF`: Entrada de consigna analógica (0–3.50V) desde el pin `VOUT` del DAC MCP4725.
  * `VDD`: Entrada +12V DC de la fuente SMPS. Alimenta internamente el pin V+ del operacional LM358N.
* **Clema 3 (Salidas hacia Celda):**
  * `OUT+`: Conectado internamente al riel VDD (+12V); va al terminal `COM 1` del Módulo de Relés.
  * `OUT-`: Conectado a los Drains de los MOSFETs IRLZ44N (sumidero de corriente); va al terminal `COM 2` del Módulo de Relés.
* **Headers Macho de Sensado:**
  * `HEADER SH1` y `HEADER SH2`: Caídas de tensión en las resistencias de shunt cerámicas de 10W; van conectados directamente a los canales `A2` y `A3` (modo single-ended) del ADC ADS1115 de 16 bits.

---

## 4. Etapa de Potencia, Conmutación y Calefacción AC/DC

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Especificación / Enlace | Función |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | [**Módulo de 2 Relevadores 5V Optoacoplado**](https://emexbit.com/product/modulo-2-relevadores-5v/) | Songle / Emexbit | $55 MXN<br>($3.00 USD) | Módulo SSR DC (Fotek DC-DC 10A, Crydom D1D12), relé Omron G5LE | Bobina 5V DC / Contactos 10A 250VAC / 10A 30VDC (Active-LOW, Optos PC817) | **Aislamiento Galvánico +12V VDD**: Entradas IN1 e IN2 puenteadas a GPIO 20 (ESP32-S3) con contactos COM/NO en paralelo para conmutación ZCS (Zero-Current Switching) con retardo de 30 ms. |
| 3 | **Resistencias de Inmersión 450W** | Blindadas en acero inoxidable / Emexbit / MercadoLibre | $450 MXN<br>($24.30 USD lote 3) | Calentadores tubulares con recubrimiento de Teflón/PTFE o Titanio (recomendado para baños con cloruros) | 110V / 220V AC (Blindadas en acero inoxidable 304/316) | Calentadores para Tina 1 (Desengrase Alcalino), Tina 2 (Decapado Alcalino), Tina 4 (Niquelado sobre Zinc). |
| 1 | **Calentador de Celda Hull 18W** | Cartucho de precisión / Emexbit / Amazon | $140 MXN<br>($7.50 USD) | Resistencia de cartucho blindada 12V DC / 24W, placa calefactora PTC 12V | 110V / 220V AC (Cartucho blindado de precisión) | Calentador para Tina 3 (Celda Hull 267 mL - Zincado Ácido). |
| 1 | **Placa Propia de Potencia TRIAC (4 Canales AC)** | STMicroelectronics / Emexbit / Fabricación propia | $260 MXN<br>($14.00 USD) | Módulos comerciales SSR cuádruples SSR-25DA, módulo dimmer optoacoplado RobotDyn | 4x TRIACs BTA24-800BW (TO-220 con disipador) + 4x Optoacopladores MOC3021 | Conmutación de potencia para los 4 calentadores mediante control por **Tiempo Proporcional (Burst Firing)** en ventanas fijas de 3000 ms escalonadas con desfase de 750 ms por canal en Arduino Nano. |
| 1 | **Línea D3 Reservada (Entrada Hardware ZC)** | Vishay / Emexbit | $15 MXN<br>($0.80 USD) | Optoacoplador H11AA1 (AC input bidireccional), PC817 con puente de diodos | Optoacoplador 4N35 conectado a pin D3 (INT1) del Arduino Nano | Entrada de hardware reservada con ISR hook para sincronización en cruce por cero de red (pendiente de validación en banco según S11). |

---

## 5. Sistema de Alimentación (Fuente Única 12V, Buck y LDOs) y Conectividad

El sistema opera a partir de **una única fuente de alimentación conmutada principal de 12V / 10A DC**. Para alimentar las etapas lógicas y de control sin sobrecalentar los reguladores lineales, se implementó una **topología híbrida de dos etapas** (Pre-regulador conmutado Buck + Post-reguladores lineales LDO):

1. Un **módulo Buck LM2596 con voltímetro digital** reduce eficientemente los 12V a **6.80V DC**, absorbiendo la mayor parte de la caída de tensión sin disipar calor excesivo.
2. A partir de los 6.80V, un regulador **LM7805 (TO-220)** genera los **+5V DC** limpios con un drop-out óptimo de apenas $\Delta V = 6.80\text{V} - 5.00\text{V} = 1.80\text{V}$ (en lugar de $7.0\text{V}$ directos desde 12V, lo que quemaría el encapsulado). Además, el LM7805 actúa como filtro activo eliminando el rizo de conmutación de 150 kHz del Buck.
3. Un regulador **LM1117T-3.3 (TO-220)** deriva finalmente los **+3.3V DC** para el ESP32-S3 y sensores.

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Encapsulado / Enlace | Función / Descripción |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Fuente Conmutada 12V / 10A DC (SMPS)** | Mean Well / Emexbit / Steren | $340 MXN<br>($18.40 USD) | Mean Well LRS-150-12, RS-150-12, fuente industrial carril DIN MDR-100-12 | Chasis metálico industrial (120W) | **Fuente Primaria Única del Sistema**: Suministra los 12V de potencia al ánodo de la celda Hull, al sumidero de corriente VCSS y a la entrada del módulo step-down. |
| 1 | [**Módulo Step-Down LM2596 con Display LED**](https://emexbit.com/product/modulo-bajador-de-voltaje-con-display-lm2596-step-down/) | Texas Instruments / XLSEMI / Emexbit | $65 MXN<br>($3.50 USD) | Módulo step-down XL4015 (5A), MP1584EN ultra-compacto, LM2596S estándar | Módulo PCB con voltímetro integrado • [Ver en Emexbit](https://emexbit.com/product/modulo-bajador-de-voltaje-con-display-lm2596-step-down/) | **Pre-regulador Buck Conmutado (12V $\rightarrow$ 6.80V DC)**: Regulador reductor de alta eficiencia (150 kHz) ajustado a 6.80V con display de monitoreo. Reduce la tensión de entrada al LM7805 para evitar su sobrecalentamiento térmico. |
| 1 | **Regulador Lineal LM7805 (Serie LM)** | STMicroelectronics / ON Semi / Emexbit | $12 MXN<br>($0.65 USD) | L7805CV, LM1084IT-5.0 (LDO 5A), Traco Power TSR 1-2450 (drop-in switching) | TO-220 (con disipador) | **Post-regulador Lineal +5V DC**: Regula a partir de los 6.80V pre-reducidos ($\Delta V = 1.80\text{V}$, disipación $< 1\text{ W}$) y filtra el rizo conmutado para alimentar Arduino Nano, bobinas de relés, LM358N y PH-4502C. |
| 1 | **Regulador Lineal LM1117T-3.3 / LM317 (Serie LM)** | Texas Instruments / Diodes Inc / Emexbit | $14 MXN<br>($0.75 USD) | AMS1117-3.3, LD1117V33, AP1117-33 | TO-220 (con disipador) | **Línea de +3.3V DC**: Regulación a partir de +5V para alimentar el ESP32-S3, sensores I2C (ADS1115, AHT20/BMP280, MCP4725) y conversores SPI MAX6675. |
| 4 | **Capacitores de Filtro y Desacoplo** | Nichicon / KEMET / Steren | $25 MXN<br>($1.35 USD lote) | Capacitores de polímero sólido baja ESR, tantalio 10 $\mu$F | Electrolíticos / Cerámicos ($100\,\mu\text{F}$, $10\,\mu\text{F}$, $100\text{ nF}$) | Rechazo de rizo de conmutación y estabilidad transitoria en la cascada de regulación. |
| 1 | **Placa PCB / Circuito de Distribución e Interconexión** | Fabricación propia / Protoboard de potencia | $85 MXN<br>($4.60 USD) | PCB FR-4 de 2 capas industrial (JLCPCB / PCBWay) | PCB con pistas reforzadas | Ruteo de rieles (+12V, +6.80V, +5V, +3.3V, GND en estrella), buses I2C (400 kHz), SPI, UART2 (9600 baud) y disparo de relé ZCS. |

---

## 6. Protecciones Contra Transitorios (TVS) y Supresión de Ruido Inductivo

Para proteger los semiconductores sensibles (ESP32-S3, conversores I2C/SPI, MOSFETs y op-amps) ante transitorios inductivos provocados por la apertura de relés mecánicos, desconexión de celdas electroquímicas y picos de conmutación de red:

| Cantidad | Componente / Modelo | Proveedor de Referencia | Costo Estimado [a verificar] | Alternativa Compatible | Encapsulado / Parámetros | Ubicación y Función de Protección |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Diodo TVS Riel +12V (1.5KE15A / SMBJ15A)** | Littelfuse / ST / Emexbit | $18 MXN<br>($1.00 USD) | P6KE15A, SMAJ15A, TVS 600W 15V | DO-201 / SMB ($V_{BR} = 15.0\text{--}16.7\text{V}$, $V_{\text{clamp}} \le 21.2\text{V}$, 1500W pico) | Conectado en paralelo entre +12V VDD y GND en la entrada del sumidero VCSS y salida SMPS. Suprime sobretensiones y picos de inductive kickback. |
| 1 | **Diodo TVS / Supresor en Bornes de Celda (1.5KE18CA o MBR360)** | ON Semiconductor / Vishay / Emexbit | $22 MXN<br>($1.20 USD) | SMBJ15CA (bidireccional), SB360 (Schottky 3A 60V) | DO-201 / SMB (Bidireccional, $V_{BR} = 17.1\text{--}19.0\text{V}$) | Conectado entre los terminales `OUT+` y `OUT-` de la celda de electrodeposición. Absorbe fuerzas contraelectromotrices generadas por reactancia química del electrolito y cables largos al abrir el relé ZCS. |
| 4 | **Varistores MOV en Líneas AC (14D201K / 10D201K)** | Bourns / TDK / Emexbit | $28 MXN<br>($1.50 USD lote 4) | S14K130, TVS bidireccional AC AK3-076C | Disco 14 mm (200V pico AC, 4500A pico) | Conectados en paralelo con cada calentador de inmersión y terminales MT1-MT2 de los TRIACs BTA24-800BW para amortiguar picos de red eléctrica y transitorios de conmutación. |
| 4 | **Supresores ESD en Líneas de Comunicación (ESD5V0 / TVS Array)** | Nexperia / ST / Emexbit | $25 MXN<br>($1.35 USD lote) | USBLC6-2SC6, PRTR5V0U2X, diodos zener 5.1V ultra-rápidos | SOT-23 / SOT-143 (Capacitancia $< 3\text{ pF}$, 5V) | Instalados en clemas externas y líneas SDA/SCL, SPI y UART2 para prevenir daños por descargas electrostáticas al conectar sondas de pH o manipular termopares. |

---

## 7. Resumen de Presupuesto Consolidado de Hardware

| Subsistema / Módulo | Componentes Principales | Costo Estimado (MXN) [a verificar] | Costo Estimado (USD) [a verificar] |
| :--- | :--- | :---: | :---: |
| **1. Procesamiento y Lógica** | ESP32-S3 + Arduino Nano | $215 MXN | $11.60 USD |
| **2. Sensores e Instrumentación** | ADS1115 + MCP4725 + 4x MAX6675 + 4x Termopares + 2x pH + AHT20/BMP280 | $1,080 MXN | $58.40 USD |
| **3. Sumidero de Corriente VCSS** | LM358N + 2x IRLZ44N + 2x Shunts 10W + Resistencias + Disipadores $R_{\theta SA} \le 5 ^\circ\text{C/W}$ | $175 MXN | $9.45 USD |
| **4. Potencia AC y Calefacción** | Módulo 2 Relés + 3x Calentadores 450W + 1x Calentador 18W + Placa 4 TRIACs + Opto ZC | $920 MXN | $49.70 USD |
| **5. Fuente y Regulación** | SMPS 12V 10A + Buck LM2596 + LM7805 + LM1117-3.3 + Capacitores + PCB interconexión | $540 MXN | $29.20 USD |
| **6. Protecciones Eléctricas TVS/MOV** | TVS 12V + TVS Celda + 4x Varistores MOV AC + Arrays ESD comunicaciones | $93 MXN | $5.05 USD |
| **TOTAL HARDWARE ELECTRÓNICO Y CONTROL** | **Planta completa integrada (prototipo TRL 4)** | **$3,023 MXN** | **$163.40 USD** |

> [!NOTE]
> Este presupuesto cubre exclusivamente la electrónica, sensores, potencia y actuadores del sistema. No incluye reactivos químicos (NaOH, ZnCl₂, NiSO₄, etc.), placas metálicas de sacrificio (Al 6061, Zn, Ni), tinas acrílicas/PP ni instrumentos analógicos de calibración externa (balanza analítica, medidor de espesores XRF).

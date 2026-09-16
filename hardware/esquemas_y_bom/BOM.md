# Lista de Materiales y Componentes (Bill of Materials - BOM)

🌐 **Idiomas / Languages**: [Español](BOM.md)

Este documento detalla la lista completa de componentes electrónicos, módulos de sensores, elementos de potencia y circuitos analógicos necesarios para construir la planta modular de electrodeposición y galvanoplastia.

---

## 1. Microcontroladores y Procesamiento

| Cantidad | Componente / Modelo | Descripción | Función en el Proyecto |
| :---: | :--- | :--- | :--- |
| 1 | **ESP32-S3-WROOM-1** | Microcontrolador Dual-Core 240MHz, 4MB Flash, Wi-Fi / Bluetooth | **Nodo Maestro**: Servidor Web, Lazo PI Térmico, Maestro I2C/SPI, NVS |
| 1 | **Arduino Nano (ATmega328P)** | Microcontrolador 16MHz, 32KB Flash | **Nodo Esclavo**: Detección de cruce por cero y disparo de TRIACs |

---

## 2. Sensores y Conversores de Señal Analógica/Digital

| Cantidad | Componente / Modelo | Interfaz / Bus | Descripción / Función |
| :---: | :--- | :--- | :--- |
| 1 | **ADS1115** | I2C (`0x48`) | ADC de 16 bits (4 canales) a 860 SPS para lectura de electrodos de pH |
| 1 | **MCP4725** | I2C (`0x60`) | DAC de 12 bits para control analógico del sumidero de corriente (0-3.3V) |
| 4 | **MAX6675** | SPI (SCK/SO) | Conversores de termopar Tipo K con compensación de junta fría (0-1024°C) |
| 4 | **Termopares Tipo K** | Analógico | Sondas de temperatura para las 4 tinas químicas |
| 2 | **PH-4502C** | Analógico | Módulos acondicionadores analógicos con electrodos de vidrio para pH |
| 1 | **AHT20 + BMP280** | I2C (`0x38`/`0x77`) | Módulo combinado ambiental (Temperatura, Humedad Relativa y Presión) |

---

## 3. Etapa Analógica del Sumidero de Corriente (Circuito Proteus)

| Cantidad | Componente / Modelo | Encapsulado / Valor | Función en el Circuito |
| :---: | :--- | :--- | :--- |
| 1 | **LM358N** | DIP-8 / SOIC-8 | Amplificador operacional dual en retroalimentación negativa |
| 2 | **IRLZ44Z** | TO-220 | Transistores MOSFET de potencia N-Channel (Nivel Lógico 5V) |
| 2 | **Resistencias de Shunt 1 $\Omega$ / 10W (Cerámicas de Cemento)** | Cerámica de Cemento 10W (Wirewound blanca rectangular) | Sensores de corriente de retroalimentación de precisión en lazo cerrado del sumidero VCSS (disipación segura hasta 10W por rama, caída 1.0 V/A) |
| 2 | **Resistencias 100 $\Omega$** | 1/4W (Película metálica) | Resistencias de protección de Gate para MOSFETs |

> [!NOTE]
> **Justificación Técnica de Resistencias de 10W (Cerámicas Blancas de Cemento)**:
> En el sumidero de corriente VCSS, cada rama MOSFET maneja hasta $I_{\text{rama}} = 3.50\text{ A}$ (o $I_{\text{total}} = 7.00\text{ A}$ repartidas). La potencia instantánea disipada es:
> $$P = I^2 \cdot R = (3.50\text{ A})^2 \cdot 1.0\,\Omega = 12.25\text{ W (pico transitorio)}$$
> $$P_{\text{nom}} = (2.50\text{ A})^2 \cdot 1.0\,\Omega = 6.25\text{ W (régimen continuo medio)}$$
> El uso de resistencias cerámicas blancas de cemento de **10W** (tipo SQP / alambre devanado encapsulado en cerámica ignífuga blanca) evita el sobrecalentamiento crítico y la deriva del coeficiente térmico que ocurría con resistencias convencionales de 5W.

### 3.1 Distribución de Clemas y Pines en la Placa Casera VCSS
La placa casera cuenta con 3 pares de clemas de tornillo y 2 pines header macho para su interconexión:
* **Clema 1 (Referencias):**
  * `GND`: Conectado a la masa común de potencia y retorno del sistema.
  * `RefGND`: Cable GND de referencia proveniente del DAC MCP4725 para evitar bucles de masa.
* **Clema 2 (Control y Alimentación):**
  * `VREF`: Entrada de consigna analógica (0–3.53V) desde el pin `VOUT` del DAC MCP4725.
  * `VDD`: Entrada +12V DC de la fuente SMPS. Alimenta internamente el pin V+ del operacional LM358N.
* **Clema 3 (Salidas hacia Celda):**
  * `OUT+`: Conectado internamente al riel VDD (+12V); va al terminal `COM 1` del Módulo de Relés.
  * `OUT-`: Conectado a los Drains de los MOSFETs IRLZ44N (sumidero de corriente); va al terminal `COM 2` del Módulo de Relés.
* **Headers Macho de Sensado:**
  * `HEADER SH1` y `HEADER SH2`: Caídas de tensión en las resistencias de shunt cerámicas de 10W; van conectados directamente a los canales `A2` y `A3` del ADC ADS1115 de 16 bits.

---

## 4. Etapa de Potencia, Conmutación y Calefacción AC/DC

| Cantidad | Componente / Modelo | Especificación / Enlace | Función |
| :---: | :--- | :--- | :--- |
| 1 | [**Módulo de 2 Relevadores 5V Optoacoplado**](https://emexbit.com/product/modulo-2-relevadores-5v/) | Bobina 5V DC / Contactos 10A 250VAC / 10A 30VDC (Active-LOW, Optoacopladores PC817, LEDs indicadores) • [Ver en Emexbit](https://emexbit.com/product/modulo-2-relevadores-5v/) | **Aislamiento Galvánico +12V VDD**: Entradas IN1 e IN2 puenteadas a GPIO 20 (ESP32-S3) con contactos COM/NO en paralelo para conmutación ZCS (Zero-Current Switching) de alta corriente y redundancia de conmutación sin arco voltaico |
| 3 | **Resistencias de Inmersión 450W** | 110V / 220V AC (Blindadas en acero inoxidable) | Calentadores para Tina 1 (Desengrase Alcalino), Tina 2 (Decapado Alcalino), Tina 4 (Niquelado sobre Zinc) |
| 1 | **Calentador de Celda Hull 18W** | 110V / 220V AC (Cartucho de precisión) | Calentador para Tina 3 (Celda Hull 267 mL - Zincado Ácido) |
| 4 | **Módulos TRIAC (ej. BTA24 + MOC3021)** | Optoacoplado (MDAC4C) | Conmutación por control de ángulo de fase desde Arduino Nano |
| 1 | **Detector de Cruce por Cero (Zero-Cross)** | Optoacoplado (4N35 / INT1 Pin 3) | Sincronización de frecuencia de red AC (60 Hz / 8.33 ms) |

---

## 5. Sistema de Alimentación (Fuente Única 12V, Pre-Regulación Buck y LDOs) y Conectividad

El sistema opera a partir de **una única fuente de alimentación conmutada principal de 12V / 10A DC**. Para alimentar las etapas lógicas y de control sin sobrecalentar los reguladores lineales, se implementó una **topología híbrida de dos etapas** (Pre-regulador conmutado Buck + Post-reguladores lineales LDO):

1. Un **módulo Buck LM2596 con voltímetro digital** reduce eficientemente los 12V a **6.80V DC**, absorbiendo la mayor parte de la caída de tensión sin disipar calor excesivo.
2. A partir de los 6.80V, un regulador **LM7805 (TO-220)** genera los **+5V DC** limpios con un drop-out óptimo de apenas $\Delta V = 6.80\text{V} - 5.00\text{V} = 1.80\text{V}$ (en lugar de $7.0\text{V}$ directos desde 12V, lo que quemaría el encapsulado). Además, el LM7805 actúa como filtro activo eliminando el rizo de conmutación de 150 kHz del Buck.
3. Un regulador **LM1117T-3.3 (TO-220)** deriva finalmente los **+3.3V DC** para el ESP32-S3 y sensores.

| Cantidad | Componente / Modelo | Encapsulado / Enlace | Función / Descripción |
| :---: | :--- | :--- | :--- |
| 1 | **Fuente Conmutada 12V / 10A DC (SMPS)** | Chasis metálico industrial | **Fuente Primaria Única del Sistema**: Suministra los 12V de potencia al ánodo de la celda Hull, al sumidero de corriente VCSS y a la entrada del módulo step-down |
| 1 | [**Módulo Step-Down LM2596 con Display LED**](https://emexbit.com/product/modulo-bajador-de-voltaje-con-display-lm2596-step-down/) | Módulo PCB con voltímetro integrado • [Ver en Emexbit](https://emexbit.com/product/modulo-bajador-de-voltaje-con-display-lm2596-step-down/) | **Pre-regulador Buck Conmutado (12V $\rightarrow$ 6.80V DC)**: Regulador reductor de alta eficiencia (150 kHz) ajustado a 6.80V con display de monitoreo. Reduce la tensión de entrada al LM7805 para evitar su sobrecalentamiento térmico |
| 1 | **Regulador Lineal LM7805 (Serie LM)** | TO-220 (con disipador) | **Post-regulador Lineal +5V DC**: Regula a partir de los 6.80V pre-reducidos ($\Delta V = 1.80\text{V}$, disipación $< 1\text{ W}$) y filtra el rizo conmutado para alimentar Arduino Nano, bobinas de relés, LM358N y PH-4502C |
| 1 | **Regulador Lineal LM1117T-3.3 / LM317 (Serie LM)** | TO-220 (con disipador) | **Línea de +3.3V DC**: Regulación a partir de +5V para alimentar el ESP32-S3 N16R8, sensores I2C (ADS1115, AHT20/BMP280, MCP4725) y conversores SPI MAX6675 |
| 4 | **Capacitores de Filtro y Desacoplo** | Electrolíticos / Cerámicos | Capacitores de entrada y salida ($100\,\mu\text{F}$, $10\,\mu\text{F}$, $100\text{ nF}$) para rechazo de rizo y estabilidad transitoria en la cascada de regulación |
| 1 | **Placa PCB / Circuito de Distribución e Interconexión** | PCB / Protoboard de potencia | Ruteo de rieles (+12V, +6.80V, +5V, +3.3V, GND en estrella), buses I2C (400 kHz), SPI, UART2 (9600 baud) y disparo de relé ZCS |

> [!TIP]
> **Ventaja de la Topología Híbrida (LM2596 Buck @ 6.80V + LM7805 LDO @ 5.0V)**:
> Si el LM7805 se conectara directamente a los 12V principales con una carga de ~0.5A (Nano + relés energizados + display + op-amps):
> $$P_{\text{directo}} = (12\text{V} - 5\text{V}) \times 0.5\text{A} = 3.50\text{ W} \quad (\text{temperatura del encapsulado } > 85^\circ\text{C sin ventilador})$$
> Con el módulo LM2596 intercalado a 6.80V:
> $$P_{\text{LM7805}} = (6.80\text{V} - 5.00\text{V}) \times 0.5\text{A} = 0.90\text{ W} \quad (\text{operación tibia y totalmente segura})$$
> El módulo LM2596 conmuta con alta eficiencia sin quemar potencia, y el LM7805 lineal elimina los armónicos de conmutación de 150 kHz, entregando una alimentación limpia para los conversores analógicos.

---

### 5.1 Balance de Potencia y Presupuesto de Corriente (*Current Budget*)

A menudo se señala que el módulo Buck LM2596 tiene un límite comercial de $2.5\text{ A}$ (con un límite térmico continuo real en PCB sin disipador de $\approx 1.8\text{--}2.0\text{ A}$), y que cada regulador LM tiene un límite nominal de $1.5\text{ A}$. El análisis de consumo real demuestra que la instrumentación y periféricos operan muy lejos de saturar este cuello de botella:

| Carril de Alimentación | Consumidores Conectados | Consumo Típico | Consumo Máximo (Pico) |
| :--- | :--- | :---: | :---: |
| **Línea +3.3V**<br>*(Regulador LM1117-3.3)* | • ESP32-S3 N16R8 (CPU @ 240 MHz + SoftAP Wi-Fi)<br>• ADC ADS1115 (16-bit, 4 canales)<br>• DAC MCP4725 (12-bit)<br>• Sensor AHT20 + BMP280 (I2C)<br>• 4x Módulos Termopar MAX6675 (SPI)<br>• Baliza Neopixel WS2812 (GPIO 48) | $\approx 140\text{ mA}$ | $\approx 280\text{ mA}$<br>*(Ráfagas de transmisión Wi-Fi)* |
| **Línea +5.0V**<br>*(Regulador LM7805)* | • Arduino Nano (ATmega328P @ 16 MHz)<br>• 2x Bobinas de Relé 5V (Songle energizadas simultáneas)<br>• 2x Acondicionadores analógicos PH-4502C<br>• Amplificador operacional dual LM358N (VCSS)<br>• Disparadores de opto-TRIACs (MOC3021)<br>• Corriente derivada a la etapa de 3.3V | $\approx 360\text{ mA}$ | $\approx 550\text{ mA}$<br>*(Relés pegados + Wi-Fi TX pleno)* |
| **Entrada 6.80V**<br>*(Salida Módulo Buck LM2596)* | • Demanda total requerida por el regulador serie LM7805<br>• Display LED voltímetro del módulo Buck | $\approx 380\text{ mA}$ | **$\approx 570\text{ mA}$** |

#### Conclusión de Capacidad y Derating:
* **Módulo Buck LM2596:** Suministra $\approx 0.57\text{ A}$ de pico frente a su capacidad real de $2.0\text{ A}$ (**utilización del $28.5\%$**).
* **Regulador LM7805 (1.5A máx.):** Conduce $\approx 0.55\text{ A}$ (**utilización del $36.6\%$**).
* **Regulador LM1117-3.3 (0.8–1.0A máx.):** Conduce $\approx 0.28\text{ A}$ (**utilización del $28.0\%$**).

> [!NOTE]
> Todo el tren de regulación opera con un factor de reducción de carga (*derating*) superior al **$60\%$**, por lo que el sistema trabaja en una zona de alta estabilidad térmica y sin caída de tensión por sobrecarga.



# Hojas de Datos de Componentes Electrónicos (Datasheets)
### Planta Piloto de Electrodeposición y Galvanoplastia

Este directorio contiene las referencias técnicas y especificaciones oficiales de los circuitos integrados, sensores y semiconductores de potencia empleados en la instrumentación y control del sistema.

> [!NOTE]
> Para mantener el repositorio de GitHub ligero y optimizado, los archivos binarios PDF de terceros se mantienen localmente en el entorno de desarrollo y están respaldados a través de sus fuentes oficiales de fabricante listadas a continuación.

---

## 1. Microcontroladores y Procesamiento

| Componente | Fabricante | Función en Planta | Enlace Oficial al Datasheet |
| :--- | :--- | :--- | :--- |
| **ESP32-S3-WROOM-1** | Espressif Systems | SoC Maestro Dual-Core Xtensa LX7 @ 240 MHz (Core 0: Red/HTTP, Core 1: FreeRTOS Tiempo Real) | [Espressif Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) |
| **ATmega328P** | Microchip / Atmel | Coprocesador Nano2 @ 16 MHz para modulación Burst Firing ZCS de 4x TRIACs | [Microchip ATmega328P](https://www.microchip.com/en-us/product/ATmega328P) |

---

## 2. Conversión A/D, D/A e Instrumentación

| Componente | Fabricante | Función en Planta | Enlace Oficial al Datasheet |
| :--- | :--- | :--- | :--- |
| **ADS1115** | Texas Instruments | Convertidor ADC Delta-Sigma de 16 bits I2C (Canal A1 dedicado a pH @ 860 SPS, A2/A3 monitoreo de shunts) | [TI ADS1115](https://www.ti.com/product/ADS1115) |
| **MCP4725** | Microchip | Convertidor DAC de 12 bits con EEPROM I2C (Consigna de corriente VCSS analógica 0–3.3V) | [Microchip MCP4725](https://www.microchip.com/en-us/product/MCP4725) |
| **MAX6675** | Maxim Integrated / ADI | Digitalizador SPI con compensación de unión fría para termopares tipo K (Tinas 1 a 4) | [Analog Devices MAX6675](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6675.pdf) |
| **LM358N** | Texas Instruments | Amplificador operacional dual de precisión (Lazo analógico de transconductancia VCSS Gm = 2.0 S) | [TI LM358](https://www.ti.com/product/LM358) |

---

## 3. Sensores Ambientales y de Proceso

| Componente | Fabricante | Función en Planta | Enlace Oficial al Datasheet |
| :--- | :--- | :--- | :--- |
| **BMP280** | Bosch Sensortec | Sensor barométrico y térmico I2C para cálculo de presión de vapor y evaporación en cabina | [Bosch Sensortec BMP280](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/) |
| **AHT20** | Aosong (ASAIR) | Sensor de humedad relativa y temperatura ambiental I2C | [Aosong AHT20](http://www.aosong.com/en/products-32.html) |

---

## 4. Etapa de Potencia y Conmutación

| Componente | Fabricante | Función en Planta | Enlace Oficial al Datasheet |
| :--- | :--- | :--- | :--- |
| **IRLZ44N** | Infineon / IR | MOSFET de potencia canal N de compuerta a nivel lógico (Ramas de corriente VCSS) | [Infineon IRLZ44N](https://www.infineon.com/cms/en/product/power/mosfet/n-channel/irlz44n/) |
| **TIP122** | STMicroelectronics | Transistor Darlington NPN de potencia para actuadores auxiliares | [ST TIP122](https://www.st.com/resource/en/datasheet/tip122.pdf) |
| **PC817** | Sharp | Optoacoplador de aislamiento galvánico para señales digitales | [Sharp PC817](https://global.sharp/products/device/lineup/data/pdf/datasheet/pc817xnnsz_e.pdf) |

---

## 5. Regulación y Gestión de Alimentación

| Componente | Fabricante | Función en Planta | Enlace Oficial al Datasheet |
| :--- | :--- | :--- | :--- |
| **LM2596** | Texas Instruments | Regulador reductor conmutado Step-Down 3A (Conversión 12V a 6.80V para etapa analógica) | [TI LM2596](https://www.ti.com/product/LM2596) |
| **LM1117** | Texas Instruments | Regulador lineal LDO 800 mA (Alimentación estabilizada de 3.3V / 5V) | [TI LM1117](https://www.ti.com/product/LM1117) |
| **LM7805** | Fairchild / onsemi | Regulador lineal positivo de 5V para etapas lógicas y relés | [onsemi LM7805](https://www.onsemi.com/pdf/datasheet/mc7800-d.pdf) |

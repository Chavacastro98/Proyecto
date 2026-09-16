# 🛠️ Guía de Instalación, Compilación y Puesta en Marcha (Versión 2.0)

> **Sistema Automatizado de Electrodeposición y Galvanoplastia (ESP32-S3 N16R8 RTOS 2.0 + Arduino Nano)**  
> *Manual de Instalación de Dependencias, Compilación de Firmware y Telemetría.*

---

## 🏛️ Aclaración Arquitectural: Evolución hasta RTOS 2.0

Es fundamental comprender la evolución del código fuente dentro de la carpeta [`firmware/esp32/`](../../firmware/esp32/):

> [!NOTE]
> **Estabilidad y Evolución Arquitectural:**
> Las versiones históricas **v3.5**, **v4.0** y la familia **RTOS (1.0 a 1.4)** son versiones estables y funcionales archivadas en `firmware/esp32/historico/`.
>
> La versión insignia, activa y definitiva en producción es **RTOS 2.0** (`firmware/esp32/RTOS2.0/`):
> 1. **Sensor de pH Dedicado en Canal A1 (RTOS 2.0)**: Eliminación total del Canal A0 para suprimir el multiplexado en el convertidor analógico-digital ADS1115. El sensor potenciométrico de pH opera con el 100% de disponibilidad del bus I2C a 860 SPS continuos.
> 2. **Calibración NVS por Modo**: Persistencia desacoplada en memoria Flash NVS de los puntos de calibración independientes por modo (Ácido, Neutro, Básico). Panel de offset analógico de hardware calibrado para un único voltímetro digital y aguja para el módulo PH-4502C.
> 3. **Lazo Cerrado Híbrido VCSS (Single-Writer)**: Máquina de estados PI con Rampa Soft-Start (500 ms), Blanking anti-inrush acelerado a 300 ms (estabilización en <2.5s), PI discreto con Anti-Windup y banda muerta $\pm 10\text{ mA}$, muestreo estroboscópico ETS (16 puntos) y diagnóstico continuo de salud de celda (`SaludCelda_t`).
> 4. **Procesamiento Paralelo (FreeRTOS SMP Dual-Core)**: Core 0 dedicado a la pila de comunicaciones (Wi-Fi, HTTP, mDNS, OTA) y Core 1 al control en tiempo real determinista.
>
> **RTOS 2.0** es la versión **definitiva y congelada** recomendada para la tesis y operación de la planta piloto.

---

## ⚡ 1. Inicio Rápido en 1 Clic (Sin Complicaciones)

Para facilitar la preparación del entorno sin necesidad de ingresar comandos en la terminal, el proyecto incluye ejecutables automatizados en la raíz del repositorio:

| Archivo | Función |
| :--- | :--- |
| **[`Iniciar_Telemetria_2.0.bat`](../../Iniciar_Telemetria_2.0.bat)** | 🚀 **Lanzador Directo**: Inicia la aplicación SCADA / Telemetría 2.0 en vivo (RTOS 2.0). |
| **[`Iniciar_Sistema.bat`](../../Iniciar_Sistema.bat)** | 🎛️ **Panel Maestro**: Menú centralizado para lanzar Telemetría 2.0, Exportador de Gráficas, Manual Químico o Diagramas. |
| **[`Ver_Diagramas.bat`](../../Ver_Diagramas.bat)** | 🧭 **Visor de Arquitectura**: Despliega la suite de diagramas interactivos de hardware y concurrencia RTOS 2.0. |
| **[`instalar_python_y_librerias.bat`](instaladores/instalar_python_y_librerias.bat)** | 📦 **Instalador Python**: Detecta o descarga e instala Python oficial para Windows (agregándolo al PATH) e instala dependencias (`requests`, `matplotlib`, `pandas`, `openpyxl`, etc.). |
| **[`instalar_librerias_arduino.bat`](instaladores/instalar_librerias_arduino.bat)** | 🔌 **Instalador de Hardware**: Descarga e instala directamente todas las librerías C++ para ESP32 en tu carpeta `%USERPROFILE%\Documents\Arduino\libraries`. |

---

## 🐍 2. Configuración del Entorno de Telemetría (Python)

Si prefieres realizar la instalación manualmente desde la línea de comandos:

1. **Instalar Python 3.9 o superior**:
   - Descárgalo desde [python.org/downloads](https://www.python.org/downloads/).
   - ⚠️ **MUY IMPORTANTE**: Marca la casilla **`Add python.exe to PATH`** durante la instalación.
2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Iniciar la Telemetría 2.0**:
   ```bash
   cd software
   python -m telemetria2.0
   ```
   > **Nota**: Puedes activar la casilla **`🎮 Modo Demo`** en la barra superior para interactuar con la interfaz, probar temporizadores de etapas ISA-88, balanza gravimétrica asistida, osciloscopio de TRIACs y monitores de error sin necesidad de tener el microcontrolador físico conectado.

---

## 🧠 3. Compilación y Carga del Firmware del ESP32-S3 (RTOS 2.0 Definitivo)

El código fuente del nodo maestro se encuentra en **[`firmware/esp32/RTOS2.0/`](../../firmware/esp32/RTOS2.0/)**.

### Paso 1: Configurar Arduino IDE para ESP32
1. Abre **Arduino IDE** (versión 2.x recomendada).
2. Ve a `File` (Archivo) → `Preferences` (Preferencias).
3. En el campo **"Additional boards manager URLs"**, pega la URL oficial de Espressif:
   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Ve a `Tools` → `Board` → `Boards Manager...`, busca **`esp32`** (por *Espressif Systems*) e instala la versión más reciente.

### Paso 2: Instalar Librerías Requeridas
Ejecuta el script **[`instalar_librerias_arduino.bat`](instaladores/instalar_librerias_arduino.bat)** o instálalas manualmente desde el **Library Manager** (`Sketch` → `Include Library` → `Manage Libraries...`):
- `Adafruit ADS1X15`
- `Adafruit AHTX0`
- `Adafruit BMP280 Library`
- `Adafruit MCP4725`
- `MAX6675 library` (por Adafruit)
- `Adafruit BusIO` (se instala automáticamente como dependencia)
- `Adafruit Unified Sensor` (se instala automáticamente como dependencia)

### Paso 3: Configuración de la Placa para ESP32-S3 N16R8
Abre el archivo principal **[`firmware/esp32/RTOS2.0/RTOS2.0.ino`](../../firmware/esp32/RTOS2.0/RTOS2.0.ino)** y en el menú `Tools` (Herramientas), establece los siguientes parámetros para el módulo **ESP32-S3 N16R8**:

| Parámetro en Menú `Tools` | Valor Seleccionado | Justificación Técnica |
| :--- | :--- | :--- |
| **Board** | `ESP32S3 Dev Module` | Target para microcontroladores serie ESP32-S3 Dual Xtensa LX7. |
| **Flash Size** | `16MB (128Mb)` | Tamaño físico de memoria Flash del módulo N16. |
| **Partition Scheme** | `16M Flash (3MB APP/9.9MB FATFS)` | Habilita dos ranuras de app de 3.0MB para OTA con amplio margen y 9.9MB de sistema de archivos. *(También es válido `16M Flash (3MB APP/9.9MB SPIFFS)`)*. |
| **PSRAM** | `OPI PSRAM` | Activa la memoria Octal-SPI PSRAM de alta velocidad (8MB del módulo R8). |
| **Flash Mode** | `QIO 80MHz` / `OPI 80MHz` | Transferencia de datos en cuádruple/óctuple canal a 80 MHz. |
| **USB CDC On Boot** | `Enabled` | Permite consola serie directa mediante el puerto USB-C nativo del ESP32-S3. |
| **USB Mode** | `Hardware CDC and JTAG` | Modo de depuración y comunicación directa estándar. |
| **Upload Speed** | `921600` | Velocidad de subida rápida por puerto USB. |
| **Port** | *Selecciona el puerto COM asignado* | Puerto asignado por el sistema operativo al conectar el cable USB. |

Haz clic en **Upload** (Subir) para compilar y flashear el firmware.

---

## ⚡ 4. Compilación y Carga del Arduino Nano (Control de TRIACs)

El firmware del módulo de potencia se encuentra en **[`firmware/arduino_nano/nano/nano.ino`](../../firmware/arduino_nano/nano/nano.ino)**.

1. Abre **[`firmware/arduino_nano/nano/nano.ino`](../../firmware/arduino_nano/nano/nano.ino)** en Arduino IDE.
2. En el menú `Tools`, selecciona:
   - **Board**: `Arduino Nano`.
   - **Processor**: `ATmega328P` (o `ATmega328P (Old Bootloader)` si el clon utiliza bootloader clásico).
   - **Port**: Selecciona el puerto COM del Arduino Nano.
3. Haz clic en **Upload** (Subir).
   > **Nota**: El Arduino Nano no requiere librerías externas; utiliza registros directos AVR y la librería estándar `<Arduino.h>`. Su rutina de cruce por cero corre en ~8 µs bajo interrupción de hardware `INT1`.

---

## 🌐 5. Conexión y Operación del Sistema

1. Al energizar el sistema, el ESP32 crea automáticamente su red Wi-Fi en modo SoftAP:
   - **SSID**: `Uli`
   - **Contraseña**: `12345678`
2. Conecta tu computadora a la red `Uli`.
3. Tienes dos vías de supervisión y operación del proceso:
   - **Vía Web Browser**: Abre `http://192.168.4.1` o `http://interfaz.local` en tu navegador para ver la interfaz MVC responsiva y ejecutar calibraciones de pH en Canal A1 o actualización inalámbrica OTA.
   - **Vía Aplicación SCADA**: Ejecuta [`Iniciar_Telemetria_2.0.bat`](../../Iniciar_Telemetria_2.0.bat) o [`Iniciar_Sistema.bat`](../../Iniciar_Sistema.bat) para control asistido de recetas ISA-88, balanza gravimétrica analítica (4 decimales), culombimetría instantánea $Q=\int Idt$, y generación de figuras científicas a 300 DPI.

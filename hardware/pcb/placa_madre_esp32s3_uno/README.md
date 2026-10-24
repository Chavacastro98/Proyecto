# ⚡ Placa Madre Industrial: ESP32-S3 + Arduino Nano (Rev 5.0)
### Módulo Central de Control Ciberfísico, Aislamiento Galvánico y Telemetría

La **Placa Madre Industrial Rev 5.0** es el circuito impreso maestro de **E.L.E.C.T.R.O.D.O-32**, diseñado específicamente para operar en entornos de laboratorio electroquímico con presencia de ruido electromagnético severo (conmutación de TRIACs a 1.37 kW) y corrientes galvánicas continuas o pulsadas de hasta 3.50 A.

---

## 🛠️ 1. Especificaciones de Fabricación (JLCPCB)

| Parámetro | Especificación Técnica | Justificación de Ingeniería |
| :--- | :--- | :--- |
| **Dimensiones** | $100\text{ mm} \times 100\text{ mm}$ (Formato Estándar Económico) | Optimización de costo en panelizado y encaje en gabinete DIN. |
| **Número de Capas** | **2 Capas** (Top: Señales / Bottom: Plano de Tierra Masivo) | Disipación térmica, inmunidad EMI y retorno de baja impedancia. |
| **Material Base** | **FR-4 TG155** (Alta Temperatura) | Resistencia a proximidad de disipadores térmicos de MOSFETs y TRIACs. |
| **Grosor de Placa** | $1.6\text{ mm} \pm 10\%$ | Rigidez mecánica ante inserción de borneras y módulos. |
| **Grosor de Cobre** | **1 oz ($35\ \mu\text{m}$)** externo | Suficiente para pistas de potencia ensanchadas (>2.5 mm con estañado). |
| **Acabado Superficial** | **HASL con plomo** o **ENIG (Electroless Nickel Immersion Gold)** | Excelente soldabilidad y resistencia a la corrosión por vapores ácidos. |
| **Color de Máscara / Serigrafía** | Azul Industrial / Blanco | Contraste de lectura en serigrafía para rotulado de bornes y jumpers. |

---

## 🧩 2. Módulos y Arquitectura Integrada en la Placa

1. **Zócalo para ESP32-S3 DevKitC-1 (44 pines):**
   * Orquestador maestro dual-core a 240 MHz (FreeRTOS SMP).
   * Servidor Web SoftAP "Uli" a 10 Hz + enlaces SPI/I2C/UART aislados.
2. **Zócalo para Arduino Nano (ATmega328P @ 16 MHz):**
   * Coprocesador esclavo de ráfagas para modulación por tiempo proporcional (3000 ms) de los 4 TRIACs.
   * Watchdog por hardware de 1.0 s para fail-safe térmico indestructible.
3. **Sección Analógica e Instrumentación (Aislamiento Faraday):**
   * Zócalo para módulo **ADC ADS1115 (16-bit I2C)**: Canales A0-A1 para pH pseudo-diferencial; Canales A2-A3 para lectura de corriente en shunts Kelvin de bajo ruido.
   * Zócalo para **DAC MCP4725 (12-bit I2C)**: Generador de consigna continua o pulsada ($0\text{--}3.53\text{ V}$) hacia la fuente VCSS.
   * Conector para **Acondicionador de pH PH-4502C** con conector BNC blindado.
   * Zócalos para 4x módulos **MAX6675 SPI** para termopares Tipo K de inmersión.
4. **Sección de Potencia y Seguridad Activa:**
   * Etapa sumidero de corriente constante **VCSS** ($G_m = 2.0\text{ S}$) con 2x MOSFETs de potencia **IRLZ44N** y amplificador operacional **LM358N**.
   * Relé de corte bipolar para aislamiento físico total de ánodo (+) y cátodo (-) con protocolo **Zero-Current Switching (ZCS)**.

---

## 📦 3. Archivos de Fabricación y Producción

* **Esquemático KiCad:** [`placa_madre_esp32s3_uno.kicad_sch`](placa_madre_esp32s3_uno.kicad_sch) | [Esquemático en PDF](placa_madre_esp32s3_uno_sch.pdf)
* **Diseño de PCB KiCad:** [`placa_madre_esp32s3_uno.kicad_pcb`](placa_madre_esp32s3_uno.kicad_pcb)
* **Gerbers Listos para Producción (Rev 5.0):** [`GERBERS_PLACA_MADRE_ESP32S3_UNO_REV5.zip`](GERBERS_PLACA_MADRE_ESP32S3_UNO_REV5.zip)
* **Lista de Materiales JLCPCB (BOM):** [`BOM_JLCPCB_ESP32S3_UNO_REV5.csv`](BOM_JLCPCB_ESP32S3_UNO_REV5.csv)
* **Coordenadas Pick & Place (CPL):** [`CPL_JLCPCB_ESP32S3_UNO_REV5.csv`](CPL_JLCPCB_ESP32S3_UNO_REV5.csv)
* **Modelo 3D CAD Completo:** [`placa_madre_esp32s3_uno_3d.step`](placa_madre_esp32s3_uno_3d.step)
* **Renders Fotorrealistas 3D:**
  * Vista Isométrica: [`render_3d_placa_madre_esp32s3_uno_iso.png`](render_3d_placa_madre_esp32s3_uno_iso.png)
  * Vista Superior (Top): [`render_3d_placa_madre_esp32s3_uno_top.png`](render_3d_placa_madre_esp32s3_uno_top.png)
* **Reporte de Reglas de Diseño (DRC):** [`DRC_REPORT_ESP32S3_UNO.json`](DRC_REPORT_ESP32S3_UNO.json) (0 Violaciones de aislamiento / 0 pistas no conectadas).

---

*Regresar al [Índice de Hardware](../../README.md).*

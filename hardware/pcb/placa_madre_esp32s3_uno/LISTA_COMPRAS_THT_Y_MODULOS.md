# 📋 Guía Maestra de Compras y Ensamble Manual de Taller
## Placa Madre Industrial ESP32-S3 + Coprocesador Nano V3
**Proyecto:** Automatización de Celda Hull - Monitoreo Electroquímico y Control Térmico
**Dimensiones PCB:** 180 x 140 mm (4 Capas) | **Revisión:** REV5 Final

> [!IMPORTANT]
> **Separación de BOMs para Ensamblado:**
> 1. **BOM SMT para JLCPCB (`BOM_JLCPCB_SMT_ONLY.csv` + `CPL_JLCPCB_SMT_ONLY.csv`):** Contiene exclusivamente los **97 componentes SMD** (circuitos integrados, resistores/capacitores 0805, diodos, transistores SOT-23, inductores y LEDs). Se ordena con el servicio económico de PCBA automatizado SMT.
> 2. **Esta Lista (`LISTA_COMPRAS_THT_Y_MODULOS.md` / `BOM_MANUAL_THT_Y_MODULOS.csv`):** Contiene los componentes Through-Hole (THT), zócalos, borneras industriales, disipadores y módulos comerciales plug-in para compra y soldadura manual en banco de trabajo. **No subir a la cotización SMT de JLCPCB**.

---

## 1. Resumen Cuantitativo de Componentes THT por Categoría

| Categoría | Componentes Clave | Cantidad Total | Método de Montaje |
| :--- | :--- | :---: | :--- |
| **Potencia y Conmutación** | MOSFETs IRLZ44N, TRIACs BTA24-800BW | 6 | THT + Disipador TO-220 M3 |
| **Resistencias de Shunt** | Resistores de Cemento 10W 1.0Ω 5% | 2 | THT Axial (Separar 3mm de PCB) |
| **Aislamiento Galvánico** | Optoacopladores MOC3021M, 4N35 | 5 | DIP-6 (Zócalo o soldadura directa) |
| **Relés Electromecánicos** | Songle SRD-05VDC-SL-C 10A 250VAC | 2 | THT Form C 5 Pines |
| **Borneras Industriales** | Phoenix MKDS 1,5 paso 5.08mm (2P, 3P, 8P) | 7 | THT Tornillo con jaula de presión |
| **Zócalos Microcontroladores** | Headers hembra 2.54mm (1x20 para S3, 1x15 para Nano) | 4 tiras | THT Hembra 2.54mm Vertical |
| **Zócalos Sensores** | Headers hembra 1x04 (I2C) y 1x06 (pH) | 2 tiras | THT Hembra 2.54mm Vertical |

---

## 2. Lista Detallada de Compras THT para la Placa

| Ref PCB | Componente / Valor | Encapsulado | Cant. | Fabricante / N° Parte | Código LCSC | Distribuidores Recomendados | Notas de Función |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **`J_CELL, J_PWR_12V`** | Bornera de Conexión por Tornillo 2 Polos 5.08mm 17.5A | `Phoenix MKDS 1,5/2-5.08 Horizontal` | **2** | Phoenix Contact / Cixi | `C8461` | Mouser / LCSC / Tienda Local | Bornera industrial para entrada 12V 10A (J_PWR_12V) y salida a Celda Hull (J_CELL). |
| **`J_AC_IN, J_METER_I, J_METER_V`** | Bornera de Conexión por Tornillo 3 Polos 5.08mm 17.5A | `Phoenix MKDS 1,5/3-5.08 Horizontal` | **3** | Phoenix Contact / Cixi | `C8462` | Mouser / LCSC / Tienda Local | Bornera para Red AC (L, N, GND) y puertos de voltímetros/amperímetros de panel (J_METER_V, J_METER_I). |
| **`J_HEATERS, J_TC`** | Bornera de Conexión por Tornillo 8 Polos 5.08mm 17.5A | `Phoenix MKDS 1,5/8-5.08 Horizontal` | **2** | Phoenix Contact / Cixi | `C8465` | Mouser / LCSC / Tienda Local | Bornera para 4x pares de Termopares K (J_TC) y 4x salidas de potencia Calentadores AC (J_HEATERS). |
| **`Q_VCSS1, Q_VCSS2`** | MOSFET N Potencia Lógico 55V 47A Rds(on)=22mΩ | `TO-220-3 Vertical` | **2** | Infineon / International Rectifier | `C111590` | Mouser / LCSC / Tienda Local | Transistor de potencia sumidero VCSS (Control corriente celda Hull). Requiere disipador térmico. |
| **`U_OPT1, U_OPT2, U_OPT3, U_OPT4`** | Optoacoplador Salida TRIAC Random-Phase 400V | `DIP-6 Paso 2.54mm` | **4** | onsemi / Fairchild | `C116220` | Mouser / LCSC / Tienda Local | Aislamiento galvánico 5000Vrms entre lógica microcontrolador y compuerta de TRIACs AC. |
| **`U_ZC`** | Optoacoplador Salida Transistor Cruce por Cero | `DIP-6 Paso 2.54mm` | **1** | Vishay / Lite-On | `C18613` | Mouser / LCSC / Tienda Local | Detector de cruce por cero de la red AC 50/60Hz para disparo sincronizado de calentadores. |
| **`K_ZCS, K_ZCS2`** | Relé Electromecánico SPDT 5VDC 10A 250VAC | `Relay Form C 5 Pines (19x15.5x15mm)` | **2** | Songle / Sanyou | `C39864` | AliExpress / LCSC / Tienda Local | Relé de aislamiento y conmutación en frío (ZCS) para protección de sumidero VCSS. |
| **`R_SH1, R_SH2`** | Resistencia de Cemento Bobinada 1.0 Ω 10W 5% | `Axial Cerámico 50x9x9mm (Paso 55.88mm)` | **2** | RoyalOhm / Yageo | `C25394` | Mouser / LCSC / Tienda Local | Shunt de medición de corriente en celda y sumidero con tomas Kelvin. Montar separado 3mm de la placa. |
| **`TR1, TR2, TR3, TR4`** | TRIAC Snubberless 25A 800V Ig=50mA | `TO-220-3 Vertical (Aislado)` | **4** | STMicroelectronics | `C128264` | Mouser / LCSC / Tienda Local | Control conmutación AC 4 canales de calentadores por cruce por cero. Requiere disipador térmico. |
| **`J_ENV`** | Tira de Pines Hembra 1x04 Pines Recta Paso 2.54mm | `PinSocket 1x04 Vertical Paso 2.54mm` | **1** | BOOMELE / Estándar | `C224355` | LCSC / Cualquier tienda de electrónica | Zócalo enchufable para módulo sensor de ambiente I2C (AHT20 + BMP280 o BME280). |
| **`J_PH4502C`** | Tira de Pines Hembra 1x06 Pines Recta Paso 2.54mm | `PinSocket 1x06 Vertical Paso 2.54mm` | **1** | BOOMELE / Estándar | `C224357` | LCSC / Cualquier tienda de electrónica | Zócalo enchufable para módulo acondicionador analógico de electrodo pH PH-4502C. |
| **`J_S3_L, J_S3_R`** | Tira de Pines Hembra 1x20 Pines Recta Paso 2.54mm | `PinSocket 1x20 Vertical Paso 2.54mm` | **2** | BOOMELE / Estándar | `C2838502` | LCSC / Cualquier tienda de electrónica | Par de zócalos de 20 pines para montar tarjeta ESP32-S3-DevKitC-1 extraíble. |
| **`U_NANO`** | Zócalo Hembra 2x 1x15 Pines Recto Paso 2.54mm | `PinSocket 1x15 Vertical Paso 2.54mm (x2)` | **1** | BOOMELE / Estándar | `C124378` | LCSC / Cualquier tienda de electrónica | Zócalo para insertar módulo microcontrolador Arduino Nano V3 extraíble. |

---

## 3. Lista de Módulos Plug-in Externos y Accesorios de Taller

Estos módulos se adquieren por separado y se enchufan en los zócalos hembra soldados previamente en la placa:

| Ítem | Módulo / Accesorio | Especificaciones Técnicas Clave | Cant. | Proveedores Sugeridos | Propósito en el Sistema |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **ESP32-S3-DevKitC-1** | MCU Dual-Core 240MHz, 16MB Flash, 8MB Octal PSRAM, USB-C (N16R8) | Estándar comercial | **1** | Espressif / Mouser / AliExpress | Microcontrolador maestro RTOS, servidor Web, WebSockets, control PID y telemetría. |
| **Arduino Nano V3 (ATmega328P)** | MCU 8-Bit 16MHz 5V con conector Type-C o Mini-USB (CH340 o FTDI) | Estándar comercial | **1** | Arduino / Tienda Local / AliExpress | Coprocesador dedicado en tiempo real para muestreo analógico de pH e interrupciones. |
| **Módulo Sensor pH PH-4502C** | Placa acondicionadora con conector BNC + potenciómetros de offset/ganancia | Estándar comercial | **1** | DFRobot / AliExpress / Amazon | Módulo analógico que acondiciona la señal de milivoltios del electrodo de pH. |
| **Electrodo de pH de Vidrio con BNC** | Sonda electroquímica 0-14 pH con cable coaxial y conector BNC macho | Estándar comercial | **1** | Amazon / AliExpress / Suministro Químico | Sensor de inmersión en la solución electrolítica de la Celda Hull. |
| **Módulo Ambiental I2C AHT20 + BMP280 (o BME280)** | Sensor dual temperatura, humedad y presión barométrica I2C 3.3V/5V | Estándar comercial | **1** | Adafruit / SparkFun / AliExpress | Monitoreo de temperatura y humedad ambiente del gabinete y celda. |
| **Termopar Tipo K de Inmersión (x4)** | Sonda termopar cromel-alumel 0-400°C con cable mallado metálico 1m | Estándar comercial | **4** | Mouser / Amazon / Omega Engineering | Sensores de temperatura para zonas 1 a 4 del baño y cámara de calentamiento. |
| **Medidores Digitales de Panel 3 Hilos (x2)** | Display 3 dígitos 0.28" (1x Voltímetro 0-100V, 1x Amperímetro con shunt interno) | Estándar comercial | **2** | Amazon / AliExpress / Tienda Local | Indicación visual directa de tensión y corriente en el panel frontal. |
| **Disipador de Aluminio TO-220 Aletado (x6)** | Disipador perfil extruido aletado ~25x15x30mm resistencia térmica <= 15°C/W | Estándar comercial | **6** | Aavid / Assmann / Tienda Local | Disipación para 2x MOSFETs IRLZ44N (VCSS) y 4x TRIACs BTA24-800BW. |
| **Kits de Montaje Aislante TO-220 M3 (x6)** | Tornillo M3x10mm + tuerca + arandela aislante plástico (pasamuros) + almohadilla de silicona/mica | Estándar comercial | **6** | Mouser / Ferretería / Tienda Electrónica | Aislamiento eléctrico entre lengüeta de transistores y disipadores. |

---

## 4. Guía de Ensamble y Soldadura Manual en Taller

Para asegurar una alta fiabilidad eléctrica, evitar tensiones mecánicas y facilitar la inspección visual, siga estrictamente el siguiente orden secuencial de soldadura:

### Fase 1: Componentes de Bajo Perfil (Altura < 8 mm)
1. **Optoacopladores DIP-6 (`U_OPT1` a `U_OPT4`, `U_ZC`):**
   - *Opcional:* Puede utilizar zócalos DIP-6 torneados de precisión si desea poder reemplazar los optoacopladores sin desoldar.
   - Verifique cuidadosamente la orientación de la muesca / punto del Pin 1 según la serigrafía.
2. **Zócalos Hembra de Pines 2.54 mm:**
   - `J_ENV` (1x04) y `J_PH4502C` (1x06).
   - `J_S3_L` y `J_S3_R` (2x 1x20 para ESP32-S3 DevKit).
   - `U_NANO` (2x 1x15 para Arduino Nano).
   - *Técnica recomendada:* Inserte los módulos físicos de desarrollo en los headers antes de soldar para garantizar que las dos filas queden exactamente paralelas a 90° respecto al PCB.

### Fase 2: Componentes de Perfil Medio (Altura 8 - 16 mm)
3. **Relés SPDT 5V (`K_ZCS`, `K_ZCS2`):**
   - Presione el cuerpo del relé firmemente contra la superficie de la PCB antes de soldar los 5 terminales.
   - Aplique suficiente soldadura y temperatura (~340°C) para asegurar que el estaño fluya completamente por los orificios metalizados de potencia.
4. **Borneras de Conexión MKDS 1,5 (Paso 5.08 mm):**
   - `J_PWR_12V` (2P), `J_CELL` (2P), `J_AC_IN` (3P), `J_METER_V` (3P), `J_METER_I` (3P), `J_TC` (8P) y `J_HEATERS` (8P).
   - Asegúrese de que las bocas de inserción de cables apunten hacia el borde exterior de la placa.

### Fase 3: Componentes de Potencia y Disipación Térmica
5. **Resistores de Cemento Bobinados 10W (`R_SH1`, `R_SH2`):**
   - > [!WARNING]
   - > **Separación Térmica Obligatoria:** No monte los cuerpos cerámicos pegados a la PCB. Deje una luz de **2.5 a 3.5 mm** entre el fondo del resistor y el plano de masa superior. Esto evita la transferencia directa de calor al sustrato FR-4 durante ensayos de corriente máxima (10A).
6. **Semiconductores TO-220 con Disipadores (`Q_VCSS1`, `Q_VCSS2`, `TR1` a `TR4`):**
   - > [!IMPORTANT]
   - > **Atornillar ANTES de Soldar:** Fije primero mecánicamente el componente TO-220 a su respectivo disipador de aluminio mediante tornillo M3x10, arandela aislante pasamuros de nylon y lámina de mica/silicona con grasa térmica. Luego inserte el conjunto en la PCB, asiente la base del disipador plano y proceda a soldar los 3 pines. Esto previene esfuerzos mecánicos y fracturas por fatiga en las pistas de cobre.

---

## 5. Protocolo de Inspección y Prueba Pre-Encendido

Antes de conectar la fuente de 12VDC o la red de 110/220VAC:
1. **Inspección Visual con Lupa o Microscopio:**
   - Verifique la ausencia de puentes de estaño entre los pines adyacentes de las borneras de 5.08mm y los terminales de los TRIACs.
   - Confirme la polaridad correcta de los zócalos de microcontrolador.
2. **Prueba de Continuidad con Multímetro (Placa desenergizada):**
   - Medir resistencia entre `+12V_IN` y `GND_PWR`: Debe marcar alta impedancia (> 100 kΩ tras cargarse los capacitores electrolíticos).
   - Medir resistencia entre `+5V` y `GND`: No debe existir cortocircuito (resistencia esperada > 1 kΩ).
   - Medir resistencia entre `+3V3` y `GND`: Resistencia esperada > 500 Ω.
   - Medir aislamiento entre `L_AC` / `N_AC` y `GND` de señal: Debe marcar resistencia infinita (aislamiento galvánico de optoacopladores intacto).
3. **Primer Encendido (Sin Módulos Conectados):**
   - Aplique 12VDC en `J_PWR_12V` (sin conectar la red AC).
   - El LED rojo `LED_12V` debe encenderse inmediatamente.
   - Mida con multímetro la salida del regulador buck `U_BUCK`: debe registrar exactamente **5.00V ± 0.1V** (y `LED_5V` verde encendido).
   - Mida con multímetro la salida del regulador LDO `U_REG3V3`: debe registrar exactamente **3.30V ± 0.05V** (y `LED_3V3` verde encendido).
4. **Inserción de Módulos:**
   - Desenergice la placa.
   - Inserte el ESP32-S3 DevKit y el Arduino Nano V3 asegurando que el conector USB coincida con la serigrafía.
   - Enchufe el módulo sensor I2C en `J_ENV` y el módulo pH en `J_PH4502C`.
   - Conecte nuevamente 12VDC y proceda a la carga del firmware.

---
*Documento generado automáticamente y validado contra el diseño CAD KiCad 10.0*
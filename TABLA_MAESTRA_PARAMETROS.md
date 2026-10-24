# 📐 Tabla Maestra de Parámetros de Ingeniería y Planta (Fuente Única de Verdad — SSOT)

🌐 **Documento Maestro de Referencia Ciberfísica y Metrológica**  
Sistema de Control Automático de Recubrimientos Electrolíticos · **E.L.E.C.T.R.O.D.O-32**  
*Base de Diseño: Firmware RTOS 2.0 (ESP32-S3) + nano2.ino (ATmega328P) + Placa Madre Rev 5.0 (JLCPCB)*  
*Última verificación y auditoría cruzada: Octubre 2026*

---

## 📌 Propósito del Documento
Este documento constituye la **Fuente Única de Verdad (Single Source of Truth — SSOT)** de la plataforma de telemetría y control ciberfísico. Resuelve cualquier discrepancia histórica entre versiones de firmware, prototipos previos y manuales de usuario, consolidando los valores numéricos exactos de operación, dimensionamiento físico y umbrales de seguridad.

---

## ⚡ 1. Dominio Eléctrico, Potencia y Dimensionamiento de PCB

| Subsistema / Parámetro | Valor Nominal | Rango Operativo Seguro | Límite Físico / Disparo | Componente / Hardware Asociado | Justificación Técnica & Normativa |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Alimentación Principal DC** | `12.0 VDC` | `11.5 – 12.8 VDC` | `15.0 V` (Diodo TVS) | Fuente conmutada industrial 12V / 10A (Jack 5.5×2.1 mm) | Alimenta lógica vía Buck y ánodo de celda Hull. |
| **Pre-Regulador Buck Lógico** | `6.80 VDC` | `6.75 – 6.85 VDC` | `7.50 V` | LM2596S-ADJ con voltímetro LED digital | Alivio térmico óptimo para LDOs lineales (VIN de ESP32 y Nano). |
| **Riel de Alimentación 5V** | `+5.00 VDC` | `4.85 – 5.15 VDC` | `5.50 V` | Regulador LM7805CT (TO-220) | Polariza Nano, relé, op-amps y búfer 74HCT541. |
| **Riel de Sensores 3.3V** | `+3.30 VDC` | `3.25 – 3.35 VDC` | `3.60 V` | Regulador LDO AMS1117-3.3 (SOT-223) | Tensión ultralimpia para ESP32-S3, ADS1115, MCP4725 y SPI. |
| **Red Eléctrica AC Calefactores** | `120 VAC` | `108 – 132 VAC` (60 Hz) | Fusible 15A | Acometida monofásica trifilar (Fase, Neutro, Tierra) | Alimenta resistencias sumergibles de las tinas térmicas. |
| **Calentador Tina 1 (Desengrase)** | **`450 W`** | `0 – 450 W` (Burst Firing) | `3.75 A RMS` | Resistencia blindada acero inox. 316L (Tina 2.5 L) | $I_{\text{RMS}} = 450\text{ W} / 120\text{ V} = 3.75\text{ A}$. |
| **Calentador Tina 2 (Decapado)** | **`450 W`** | `0 – 450 W` (Burst Firing) | `3.75 A RMS` | Resistencia blindada acero inox. 316L (Tina 2.5 L) | $I_{\text{RMS}} = 450\text{ W} / 120\text{ V} = 3.75\text{ A}$. |
| **Calentador Tina 3 (Celda Hull)** | **`18 W`** | `0 – 18 W` (o ambiente) | `0.15 A RMS` | Calefactor de precisión miniatura (Celda 267 mL) | Volumen pequeño (267 mL); 450 W causaría sobretiro violento. |
| **Calentador Tina 4 (Niquelado)** | **`450 W`** | `0 – 450 W` (Burst Firing) | `3.75 A RMS` | Resistencia blindada titanio/cuarzo (Tina 2.5 L) | $I_{\text{RMS}} = 450\text{ W} / 120\text{ V} = 3.75\text{ A}$. |
| **Potencia Total Térmica Nominal** | **`1.368 kW`** | `0 – 1.37 kW` | Max Inrush 11.4A | 3× 450W + 1× 18W en conmutación ZCS escalonada | Interlock INT-17 desfasa disparos (0, 750, 1500, 2250 ms). |
| **TRIACs de Potencia AC** | `25 A RMS` | `0 – 3.75 A RMS` (15% carga) | `800 V` pico | 4× STMicroelectronics BTA24-800BW (TO-220) | 85% de derating térmico; disipadores extruidos de aluminio. |
| **Optoacopladores de Disparo** | `1.2 V LED` | `10 – 15 mA` compuerta | Aislamiento 7.5 kV | 4× MOC3021M con snubber RC (39 Ω 1W + 100 nF 400V) | Aislamiento galvánico total entre 120 VAC y lógica 5V. |
| **Pistas PCB de Potencia AC** | `1.80 – 2.00 mm` | `0 – 3.75 A` | Capacidad 6.0 A | Cobre 1 oz ($35\ \mu\text{m}$) en capas Top/Bottom | Cumple IPC-2152 ($\Delta T \le 20^\circ\text{C}$ con margen >45%). |
| **Sumidero Lineal VCSS (MOSFETs)** | `47 A` (pulso 160A) | `0.00 – 3.50 A` (nominal) | `55 V` $V_{DS}$ | 2× Infineon IRLZ44NPBF (TO-220 en paralelo) | $R_{DS(on)} = 0.022\ \Omega$; conmutación lineal libre de EMI. |
| **Resistencias Shunt de Retorno** | **`0.50 Ω eq.`** | `0 – 3.50 A` | Disipación máx 20W | 2× 1.0 Ω 10W cerámicas SQP en paralelo con lazos Kelvin | A $3.50\text{ A}$, disipan $P = I^2 R = 6.12\text{ W}$ (<31% capacidad). |
| **Transconductancia VCSS ($G_m$)** | **`2.00 S`** (A/V) | `0.00 – 1.75 V` en DAC | Clamp en 1.75V | Amplificador de error operacional OPA2171 / LM358 | $I_{\text{out}} = V_{\text{DAC}} \times G_m = 1.75\text{ V} \times 2.0\text{ A/V} = 3.50\text{ A}$. |

---

## 📌 2. Dominio de Pines, Buses y Protocolos de Comunicación

| Señal / Función | Pin Microcontrolador | Nivel Lógico | Bus / Protocolo | Dispositivo / Dirección | Función Específica |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **I2C SDA (Datos)** | `GPIO 8` (ESP32-S3) | 3.3V TTL | I2C Fast-Mode (400 kHz) | Bus común (Pull-ups 4.7k a 3.3V) | Canal bidireccional de instrumentación analógica y ambiente. |
| **I2C SCL (Reloj)** | `GPIO 9` (ESP32-S3) | 3.3V TTL | I2C Fast-Mode (400 kHz) | Bus común (Pull-ups 4.7k a 3.3V) | Generación de reloj determinista libre de contención. |
| **ADC 16-bit (pH & Corriente)** | Bus I2C | 3.3V | I2C (`0x48`) | ADS1115 (860 SPS continuo) | **Canal A1:** Electrodo pH (Po). **Canales A2-A3:** Shunts VCSS. |
| **DAC 12-bit (Consigna VCSS)** | Bus I2C | 3.3V | I2C (`0x60`) | MCP4725 (EEPROM persistente) | Consigna analógica continua ($0\text{--}3.50\text{ A}$) o pulsada a 10 Hz. |
| **Sensor Clima Ambiente** | Bus I2C | 3.3V | I2C (`0x38` / `0x76`) | AHT20 (Humedad) + BMP280 (Presión) | Compensación barométrica y trazabilidad de laboratorio. |
| **SPI SCK (Reloj Compartido)** | `GPIO 18` (ESP32-S3) | 3.3V TTL | SPI Half-Duplex (4 MHz) | 4× MAX6675 en bus compartido | Reloj síncrono común hacia los digitalizadores de termopar. |
| **SPI MISO/SO (Datos)** | `GPIO 19` (ESP32-S3) | 3.3V TTL | SPI Half-Duplex | 4× MAX6675 línea compartida | Lectura de tramas de 12 bits de temperatura sin línea MOSI. |
| **Chip Select Tina 1 (CS0)** | `GPIO 5` (ESP32-S3) | 3.3V Active-LOW | SPI Chip Select | MAX6675 U3 (Tina 1 Desengrase) | Habilitación de lectura térmica de Desengrase. |
| **Chip Select Tina 2 (CS1)** | `GPIO 4` (ESP32-S3) | 3.3V Active-LOW | SPI Chip Select | MAX6675 U4 (Tina 2 Decapado) | Habilitación de lectura térmica de Decapado. |
| **Chip Select Tina 3 (CS2)** | `GPIO 13` (ESP32-S3) | 3.3V Active-LOW | SPI Chip Select | MAX6675 U5 (Tina 3 Celda Hull) | Habilitación de lectura térmica de Celda Hull. |
| **Chip Select Tina 4 (CS3)** | `GPIO 14` (ESP32-S3) | 3.3V Active-LOW | SPI Chip Select | MAX6675 U6 (Tina 4 Niquelado) | Habilitación de lectura térmica de Niquelado. |
| **Relé ZCS Celda Bipolar** | `GPIO 20` (ESP32-S3) | 3.3V Active-LOW | Disparo directo por hardware | Transistor AO3401A $\rightarrow$ Relé 5V Songle | Aislamiento físico bipolar (+12V y retorno) en $I=0.00\text{ A}$. |
| **Baliza Neopixel WS2812B** | `GPIO 48` (ESP32-S3) | 5.0V DIN | Protocolo monocable 800 kHz | LED RGB direccionable 5050 | Señalización visual industrial ISA-18.2 de estados y alarmas. |
| **Enlace UART2 TX Maestro** | `GPIO 17` (ESP32-S3) | 3.3V $\rightarrow$ 5V | UART Asíncrono (9600 bps) | Divisor resistivo $\rightarrow$ Pin RX0 Nano | Envío de tramas de potencia térmica con checksum CRC-8. |
| **Detector Cruce por Cero (ZC)**| `Pin D3` / INT1 (Nano) | 5V Pulsante (120 Hz)| Interrupción externa de hardware| Optoacoplador 4N35 conectado a red AC | Sincronización de paquetes de ciclo a $\pm 50\ \mu\text{s}$ de $V_{\text{AC}}=0$. |
| **Disparo TRIACs D7–D10** | `D7, D8, D9, D10` (Nano)| 5V Lógico | Disparo por compuerta | 4× MOC3021M hacia TRIACs BTA24 | Modulación proporcional por ráfagas (Ventana 3000 ms). |

---

## 🧪 3. Dominio Químico, Tinas y Fases de Proceso (ANSI/ISA-88)

| Tina / Proceso | Capacidad | Composición Química Principal | Temperatura Nominal | pH de Proceso | Corriente / Densidad | Sustrato / Probeta |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| **Tina 1: Desengrase Alcalino** | `2.5 L` | $\text{Na}_3\text{PO}_4 \cdot 12\text{H}_2\text{O}$ (25 g/L) + Carbonato de Sodio (20 g/L) + Tensoactivo | **$85.0\ ^\circ\text{C}$** ($80\text{--}90^\circ\text{C}$) | $11.0 – 12.5$ | N/A (Termoquímico) | Al 6061-T6 (1.0 dm² sumergido) |
| **Tina 2: Decapado Alcalino** | `2.5 L` | $\text{Na}_3\text{PO}_4$ suave (30 g/L) para remoción controlada de alúmina $\text{Al}_2\text{O}_3$ | **$65.0\ ^\circ\text{C}$** ($60\text{--}70^\circ\text{C}$) | $10.5 – 11.5$ | N/A (Termoquímico) | Sin picaduras intermetálicas (*pitting*) |
| **Tina 3: Celda Hull Zincado** | **`267 mL`** (ASTM) | Baño ácido: $\text{ZnCl}_2$ (60 g/L) + $\text{KCl}$ (200 g/L) + $\text{H}_3\text{BO}_3$ (25 g/L) | **$25.0\ ^\circ\text{C}$** (Ambiente) | **`4.8 – 5.2`** | **$0.00 – 3.00\text{ A}$** (DC o Pulsado 10 Hz) | Ánodo de Zinc (99.99%) $\rightarrow$ Cátodo Al 6061 |
| **Tina 4: Niquelado sobre Zinc**| `2.5 L` | Formulación Watts: $\text{NiSO}_4 \cdot 6\text{H}_2\text{O}$ (240 g/L) + $\text{NiCl}_2$ (45 g/L) + $\text{H}_3\text{BO}_3$ (30 g/L) | **$50.0\ ^\circ\text{C}$** ($45\text{--}55^\circ\text{C}$) | **`4.0 – 4.5`** | **$0.50 – 3.00\text{ A}$** (DC galvanostático) | Ánodo de Níquel $\rightarrow$ Cátodo con capa Zn |

---

## 🛡️ 4. Dominio de Seguridad Funcional, Interlocks y Límites Fail-Safe

| ID Interlock | Nombre del Mecanismo | Condición Numérica de Disparo | Acción Automática del Firmware | Código Error | Tipo de Rearme |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **INT-01** | **Sobretemperatura Sostenida** | $T_{\text{medida}} > SP + 3.0\ ^\circ\text{C}$ durante $> 3.0\text{ s}$ consecutivos. | Dispara Fail-Safe: TRIACs al 0%, DAC a 0V, abre relé bipolar GPIO20. | `14` (`ERR_TEMP_OVERHEAT`) | **Latch Manual** (POST `/failsafe_reset`) |
| **INT-02** | **Termopar Abierto / Fallido** | MAX6675 reporta `NAN`, $T < 0^\circ\text{C}$ o $T > 150^\circ\text{C}$ con canal activo. | Apaga de inmediato los 4 calentadores a 0%, abre relé VCSS y baliza en Rojo. | `11` (`ERR_TERMOPAR_DESCONECTADO`) | **Latch Manual** tras reconexión física |
| **INT-03** | **Tope de Consigna Térmica** | Solicitud $SP > 60^\circ\text{C}$ en Celda Hull o $SP > 95^\circ\text{C}$ en tinas generales. | Rechazo HTTP 400 Bad Request; clamp en límites de seguridad en NVS. | N/A (HTTP 400) | **Automático** (Rechazo sin alterar planta) |
| **INT-04** | **Clamp de Corriente VCSS** | Consigna solicita $I > 3.50\text{ A}$ (DAC $> 2030\text{ LSB}$). | Saturación estricta por firmware a **$3.50\text{ A}$**. Protege shunts de 10W. | N/A (Clamp activo) | **Automático** (Opera al límite seguro) |
| **INT-05** | **Sobrecorriente Medida VCSS** | Corriente en shunts $I_{\text{medida}} > 3.50\text{ A}$ sostenida $> 200\text{ ms}$. | Corte ZCS inmediato (<35 ms), relé abierto, calentadores a 0%. | `22` (`ERR_VCSS_OVERCURRENT`) | **Latch Manual** (POST `/failsafe_reset`) |
| **INT-06** | **Celda Abierta / Falsa Carga** | $I_{\text{medida}} < 0.05\text{ A}$ con $SP > 0.30\text{ A}$ durante $> 1000\text{ ms}$ en DC. | Desenergiza DAC, abre relé para evitar voltajes flotantes en circuito abierto. | `23` (`ERR_VCSS_OPEN_CIRCUIT`) | **Latch Manual** tras verificar bornes |
| **INT-07** | **Validación Previa I2C del DAC** | Intento de energizar celda (`setEstadoFuente(true)`) con DAC ausente. | Rechaza la activación, mantiene relé abierto y devuelve error al llamador. | `21` (`ERR_I2C_DAC_LOST`) | **Automático** (Hasta detectar chip I2C) |
| **INT-08** | **Secuencia Zero-Current (ZCS)** | Orden de apagado de celda o disparo de cualquier interlock. | DAC a 0V $\rightarrow$ espera $30\text{ ms}$ para extinción de arco $\rightarrow$ abre contactos relé. | N/A (Secuencia ZCS) | **Automático** (Transición determinista) |
| **INT-09** | **Pérdida de Bus I2C** | 3 fallos consecutivos en I2C; al 2º fallo ejecuta recuperación de 9 pulsos SCL. | Dispara Fail-Safe general, abre relé, apaga TRIACs y baliza en Rojo. | `20` / `21` (`ERR_I2C_LOST`) | **Latch Manual** tras restablecer bus |
| **INT-10** | **Watchdog FreeRTOS Maestro** | Cualquier tarea RTOS (Supervisor, Térmico, Fuente, Sensado) congelada $> 5000\text{ ms}$. | Supervisor enclava Fail-Safe general y fuerza corte de todos los actuadores. | `10` (`ERR_WATCHDOG_TIMEOUT`) | **Latch Manual** / Reinicio de CPU |
| **INT-11** | **Aislamiento Galvánico pH** | Intento de muestrear pH con celda VCSS o calefactores conduciendo corriente. | Suspende la medición de pH para evitar lazos de tierra galvánicos espurios. | N/A (Bloqueo lógico) | **Automático** (Reanuda con planta en reposo) |
| **INT-12** | **Protección de Firmware OTA** | Solicitud de carga OTA con fuente VCSS o calentadores activos. | Rechaza con HTTP 403 Forbidden impidiendo que reinicios ocurran bajo carga. | N/A (HTTP 403) | **Automático** (Permite OTA solo en standby) |
| **INT-13** | **Watchdog de Hardware Nano2** | Bucle `loop()` del ATmega328P bloqueado $> 1.0\text{ s}$ (`WDTO_1S`). | Reset físico por temporizador interno AVR; compuertas D7–D10 forzadas a `LOW`. | Hardware Reset AVR | **Automático** (Reinicio en frío en <15 ms) |
| **INT-14** | **Watchdog de Enlace UART Nano2** | Nano2 no recibe trama válida desde ESP32-S3 durante $> 4000\text{ ms}$. | Apaga inmediatamente los 4 canales de potencia (potencias al 0%). | Silencio de potencia | **Automático** (Reanuda al recibir trama) |
| **INT-15** | **Checksum CRC-8 en UART** | Trama serie con bytes corruptos o CRC inválido ($P(x) = x^8 + x^2 + x + 1$). | El esclavo descarta silenciosamente la trama sin alterar las consignas. | Depuración serie | **Automático** (Admite solo datos válidos) |
| **INT-16** | **Reset Sincronizado Maestro-Slave**| Reinicio del ESP32-S3 (encendido, watchdog o comando de usuario). | ESP32 envía trama `RST*crc\n`; Nano2 ejecuta auto-reset mediante `WDTO_15MS`. | Sincronización CPU | **Automático** (Ambos arrancan en estado cero) |
| **INT-17** | **Escalonamiento Burst Firing** | Modulación simultánea de múltiples canales térmicos de 450 W. | Desfase determinista de 750 ms por canal: $\{0, 750, 1500, 2250\}\text{ ms}$ en ciclo 3 s. | Gestión de carga | **Automático** (Evita sobrecarga simultánea) |
| **INT-18** | **Autenticación en Rutas REST** | Peticiones HTTP a `/act_t`, `/act_f`, `/set_f`, `/set_t` sin token válido. | Rechazo inmediato HTTP 401 Unauthorized impidiendo manipulación no autorizada. | HTTP 401 Unauthorized | **Automático** (Exige `X-Auth-Token` válido) |

---

*Fin del Documento Maestro · E.L.E.C.T.R.O.D.O-32 · Universidad de Guadalajara (CUCEI)*

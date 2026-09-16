# 📜 Registro de Cambios (Changelog)

> **Sistema Automatizado de Electrodeposición y Galvanoplastia (ESP32-S3 N16R8 + Arduino Nano)**  
> *Tesis de Grado en Ingeniería / Química de Procesos Electroquímicos*  
> *Automatización, Instrumentación y Control de Línea Piloto para Procesos de Zincado (Celda Hull) y Niquelado.*

Todas las notas notables de cambios para este proyecto están documentadas en este archivo. El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto se adhiere a la nomenclatura de versiones semánticas.

---

> [!IMPORTANT]
> **Nota de Estabilidad Arquitectural (Versión 3.5 en Adelante):**  
> Las versiones **v3.5**, **v4.0** y **RTOS 1.0** son **versiones plenamente estables y operativas**. Cada una de ellas implementa las mismas funcionalidades de proceso electroquímico y ofrece una experiencia funcional completa.
> 
> Las diferencias fundamentales entre ellas **no son modificaciones directas ni cosméticas de cara al usuario**, sino **transformaciones profundas en la arquitectura interna de software**:
> * **Gestión de Memoria y Flash**: Desacoplamiento de las escrituras Flash NVS fuera de secciones críticas y adopción del patrón *Atomic Snapshot* para lectura coherente entre núcleos.
> * **Procesamiento Paralelo Real (FreeRTOS SMP Dual-Core)**: Superación definitiva del *Super-Loop* secuencial de v3.5/v4.0 para ejecutar en paralelo físico determinista el control en tiempo real (Core 1) y los servicios de red / HTTP / OTA (Core 0).
> * **Hardware Target**: Transición de chips clásicos de 4MB a la plataforma de alto rendimiento **ESP32-S3 N16R8** (16MB Flash con ranuras duales OTA de 3MB y 8MB Octal PSRAM).

---

## 📊 Matriz Comparativa de las Versiones del Proyecto

| Módulo / Característica | 🏆 v3.5 (Super-Loop) | 🚀 RTOS 1.0 (SMP Inicial) | ⚡ RTOS 1.3 (VCSS / ETS) | ⭐ RTOS 2.0 (Flagship Activo) |
| :--- | :--- | :--- | :--- | :--- |
| **Hardware Target** | ESP32-S3 / ESP32 | ESP32-S3 N16R8 (16M/8M) | ESP32-S3 N16R8 (16M/8M) | **ESP32-S3 N16R8 (16MB Flash / 8MB PSRAM OPI)** |
| **Arquitectura ESP32** | Lazo Cerrado VCSS | FreeRTOS SMP Dual-Core | FreeRTOS SMP Dual-Core | **FreeRTOS Dual-Core SMP (Single-Writer VCSS)** |
| **Particionamiento Flash**| Minimal SPIFFS (1.9MB)| 16M Flash (3MB APP/FATFS)| 16M Flash (3MB APP/FATFS)| **16M Flash (3MB APP / 9.9MB FATFS con OTA)** |
| **I2C Bus Clock** | 100 kHz | 400 kHz Fast Mode | 400 kHz Fast Mode | **400 kHz Fast Mode (`Wire.setClock(400000)`)** |
| **Canal Sonda pH** | Multiplexado A0/A1 | Multiplexado A0/A1 | Multiplexado A0/A1 | **Canal A1 DEDICADO ADS1115 (A0 Eliminado)** |
| **Muestreo de pH** | TDM 25 Hz | TDM 50 Hz | TDM 50 Hz | **Continuo 860 SPS (100% de bus I2C sin demoras)**|
| **Calibración pH NVS** | Volátil / Única | Global | Global | **Persistencia NVS Independiente por Modo** |
| **Offset Hardware pH** | Doble potenciómetro | Doble potenciómetro | Doble potenciómetro | **Voltímetro y aguja única para PH-4502C** |
| **Lazo VCSS Blanking** | No | 2000 ms | 2000 ms | **300 ms (Asentamiento ultrarrápido <2.5s)** |
| **Control de Potencia** | Delay micros | INT1 (~8µs) + LUT | INT1 (~8µs) + LUT + WDT | **INT1 Hardware (~8µs) + LUT PROGMEM + WDT** |
| **SCADA Activo** | telemetria (v3.5) | telemetria (v1.0) | telemetria (v1.3) | **Telemetría 2.0 (`telemetria2.0` / ISA-88)** |
| **Culombimetría / Balanza**| No | Asistida 4 decimales | Asistida 4 decimales | **Balanza 4 decimales + $Q = \int I dt$ + $\eta\%$** |
| **Figuras Científicas** | 3 Gráficas (300 DPI) | 5 Figuras (300 DPI) | 5 Figuras (300 DPI) | **8 Figuras HD (300 DPI) Offline / Online** |
| **Previews Web** | v3.5 Estáticas | RTOS 1.0 Pestañas | RTOS 1.3 | **RTOS 2.0 (Simulador A1 Dedicado + NVS)** |

---

## 🚀 [RTOS 2.0.0] - Firmware Flagship, Sensor de pH Dedicado en Canal A1 y SCADA Telemetría 2.0 (2026)
**Ubicación del código:** `firmware/esp32/RTOS2.0/` | **Nano:** `firmware/arduino_nano/nano/` | **Telemetría:** `software/telemetria2.0/` | **Diagramas:** `visualizacion/diagramas/` | **Manual Químico:** `documentos/manuales/MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md`

### 🌟 Added & Enhanced (Sensor de pH Dedicado, Calibración por Modos y SCADA 2.0)
- **Eliminación Definitiva del Canal A0 de pH y Dedicación Exclusiva del Canal A1**:
  - Eliminación total de todas las referencias al Canal A0 en el firmware (`RTOS2.0.ino`, `Modulo_PH.cpp/.h`, `Controller_PH.cpp/.h`, `Task_Sensado.cpp/.h`).
  - El sensor de pH opera de forma continua y dedicada en el Canal A1 del ADS1115 con el 100% de uso del bus I2C, eliminando tiempos de multiplexación temporal (TDM) y demoras de reconfiguración analógica. Muestreo potenciométrico continuo a 860 SPS.
- **Calibración Metrológica Independiente en Flash NVS por Modo**:
  - Almacenamiento desacoplado en Flash NVS de los puntos de calibración (Ácido, Neutro, Básico) individualizados por modo de operación (Modo 0: Nernst teórico con offset calibrado, Modo 1: Lineal 2 puntos, Modo 2: Dual-slope segmentado 3 puntos).
  - Panel de ajuste de offset de hardware adaptado a un único voltímetro digital y aguja para el módulo acondicionador PH-4502C.
- **Optimización de Tiempos de Respuesta del Lazo Cerrado VCSS**:
  - Reducción del periodo de Blanking anti-inrush de $2000\text{ ms}$ a **$300\text{ ms}$** (`VCSS_PI_BLANKING_MS`), reduciendo el tiempo total de estabilización analógica de 30 s a $< 2.5\text{ s}$ sin riesgo de sobretiro ni oscilaciones de corriente.
  - Mantenimiento del arranque suave determinista de $500\text{ ms}$ (`VCSS_SOFT_START_MS`) y control PI discreto con Anti-Windup ($K_p = 0.12, K_i = 0.04$, banda muerta $\pm 10\text{ mA}$).
- **SCADA Telemetría 2.0 en Producción (`software/telemetria2.0/`)**:
  - Despliegue de la suite modular Telemetría 2.0 con soporte directo para el Canal A1 dedicado de pH.
  - Ejecución de la matriz de 32 recetas experimentales bajo protocolo ISA-88 (diseño Taguchi para Al 6061-T6 con Desengrase Alcalino, Decapado Alcalino, Celda Hull de 267 mL y Niquelado sobre Zinc).
  - Balanza analítica asistida de 4 decimales ($P_{\text{ini}}$ y $P_{\text{fin}}$), integración culombimétrica en línea $Q = \int I dt$, cálculo automático de eficiencia Faradaica $\eta\%$ y espesor medio en $\mu\text{m}$.
- **Exportador Científico Offline de 8 Figuras a 300 DPI (`software/exportar_graficas_offline.py`)**:
  - Generador independiente de figuras científicas para la memoria de tesis, incluyendo perfiles térmicos, índices IAE, control de TRIACs, plano de fase $\dot{e}(t)$ vs $e(t)$, cronograma Gantt de etapas, reconstrucción estroboscópica ETS a 100 Hz y distribución longitudinal de corriente en Celda Hull.
- **Simulador Web y Previews RTOS 2.0 (`visualizacion/preview/RTOS2.0/`)**:
  - Portales interactivos con simulación en tiempo real del módulo de pH en Canal A1 dedicado, monitoreo térmico, control de fuentes VCSS y diagnóstico de sensores.

---

## 🚀 [RTOS 1.3.0] - Firmware Algoritmos Avanzados VCSS y Química VUGR (2026)
**Ubicación del código:** `firmware/esp32/historico/RTOS1.3/` | **Nano:** `firmware/arduino_nano/nano/` | **Telemetría:** `software/telemetria/`

### 🌟 Added & Enhanced (Control VCSS, Algoritmos Deterministas y Química Experimental)
- **Máquina de Estados de 3 Fases para el Lazo VCSS (`Modulo_Fuentes.cpp`)**:
  - `PI_STATE_RAMP`: Rampa lineal suave anti-inrush durante $500\text{ ms}$ ($V_{\text{target}} \times t / 500$) para eliminar transitorios inductivos.
  - `PI_STATE_BLANKING`: Supresión de acción integral y estabilización capacitiva de doble capa electroquímica durante $2000\text{ ms}$.
  - `PI_STATE_STEADY`: Lazos cerrados discretos PI ($K_p = 0.12, K_i = 0.03$) con limitador de pendiente $\pm 4\text{ LSB/ciclo}$, banda muerta $\pm 10\text{ mA}$ y anti-windup $\pm 0.15\text{ A}$.
- **Reconstrucción Estroboscópica ETS (Equivalent Time Sampling)**:
  - Muestreo en tiempo equivalente de 16 puntos (`s_ondaETS`) en modo pulsado (1 a 100 Hz), capturando la forma de onda completa sin saturar el bus I2C (ocupación $\le 2.5\%$).
- **Diagnóstico y Supervisión en Tiempo Real de Salud de Celda (`SaludCelda_t`)**:
  - Detección automática de impedancia anómala: `FALLA_RESISTENCIA_ALTA` ($R > 10\,\Omega$), `FALLA_CORRIENTE_CERO` ($I < 20\text{ mA}$ con DAC activo), `FALLA_DESCONEXION` y `FALLA_SATURACION`.
- **Calibración Precisa del Carril Analógico**:
  - Referencia ajustada a $V_{\text{REF}} = 3.53\text{ V}$ nominales ($G_m = 2.00\text{ S}$, rango $0\text{--}7.06\text{ A}$, DAC a $0.862\text{ mV/LSB}$).
- **Filtrado Adaptativo de pH Dual (`Modulo_PH.cpp`)**:
  - Coeficiente $\alpha$ dinámico ($\alpha=0.30$ en perturbaciones transitorias $|\Delta\text{pH}|>0.50$, $\alpha=0.08$ en estado estable) con $V_{\text{offset}} = 1.765\text{ V}$.
- **Alineación Química con Protocolo VUGR / Memoria SMEQ26**:
  - Erradicación definitiva de "decapado ácido": Tina 2 formalizada como **Decapado Alcalino** ($\text{Na}_3\text{PO}_4 \cdot 12\text{H}_2\text{O}$ a $85^\circ\text{C}$).
  - Tina 4 formalizada como **Niquelado sobre Zinc** con $\text{Na}_2\text{SO}_4$ para inhibir desplazamiento galvánico espontáneo.
- **Hardware y Alimentación Híbrida**:
  - Fuente conmutada principal única de 12V / 10A DC.
  - Pre-regulador conmutado Buck LM2596 con display (12V $\rightarrow$ 6.80V) para alivio térmico del LM7805 ($\Delta V = 1.80\text{V}$, disipación $< 1\text{ W}$).
  - Resistencias de shunt actualizadas a **10W (cerámica de cemento wirewound blanca)** con margen térmico $> 60\%$.
- **Nuevo Manual Técnico para Químicos**:
  - Incorporación de [`MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md`](MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md) con recetas completas, procedimientos SOP, cálculos de Faraday y troubleshooting.

---

## 🚀 [RTOS 1.0.0] - Firmware Inicial FreeRTOS Dual-Core & Telemetría SCADA con Gravimetría (2026)
**Ubicación del código:** `esp32/RTOS1.0/` | **Nano:** `arduino_nano/nano/` | **Telemetría:** `telemetria/` | **Diagramas:** `diagramas/`

### 🌟 Added (Hardware ESP32-S3 N16R8 y Concurrencia de Bajo Nivel)
- **Soporte Nativo para Hardware ESP32-S3 N16R8**:
  - Configurado para 16 MB de memoria Flash externa y 8 MB de memoria Octal-SPI PSRAM (`OPI PSRAM`).
  - Esquema de partición `16M Flash (3MB APP/9.9MB FATFS)` con ranuras duales de aplicación de 3.0 MB que eliminan las restricciones de espacio del antiguo esquema de 1.9 MB (`Minimal SPIFFS`).
- **Sincronización Atómica Cross-Core (Dual-Core SMP)**:
  - Patrón *Atomic Snapshot*: En `Task_Sensado.cpp` y `Modulo_Fuentes.cpp`, las variables compartidas (`phModuloActivo`, `fuenteActiva`, `modoPulsado`) se leen bajo `xDataMutex` en copias locales antes de cada iteración, garantizando coherencia de memoria entre Core 0 y Core 1 sin colisiones ni condiciones de carrera.
- **Desacoplamiento de Persistencia NVS Flash**:
  - En `Controller_Fuente.cpp` y `Modulo_PH.cpp`, las llamadas a `memoria.putInt()` y `memoria.putFloat()` se extrajeron fuera de las secciones críticas del mutex (`xDataMutex`). Esto previene bloqueos de ~50-100 ms en el Core 1 durante operaciones de borrado de sector Flash.
- **Elevación de Velocidad del Bus I2C a 400 kHz (Fast Mode)**:
  - Configurado en `config.h` y `RTOS1.0.ino` (`Wire.setClock(400000)`), reduciendo el tiempo de conversión y lectura del ADS1115 (16 bits) y DAC MCP4725 (12 bits) a menos de $1.2\text{ ms}$.
- **Endpoint Unificado de Telemetría (`/data_all`)**:
  - Consolida el snapshot térmico (4 tinas), fuente VCSS, módulo pH, variables ambientales y estado fail-safe en una única carga JSON de ~1 KB, reduciendo el tráfico HTTP en un 75% respecto a v3.5.
- **Firmware de Alta Velocidad para Arduino Nano (ATmega328P)**:
  - Interrupción de cruce por cero en pin `INT1` ejecutada en ~8 µs mediante manipulación directa de registros `PORTD`/`PORTB`.
  - Tabla de 101 valores de coseno inverso precalculada en memoria de programa Flash PROGMEM (`lut_triac`).
  - Watchdog de comunicación UART de 3 segundos que apaga las 4 cargas por seguridad si se pierde la conexión con el ESP32.

### 🧭 Suite Completa de Diagramas Técnicos RTOS 1.0 (`diagramas/`)
- Modernización de los 11 diagramas Mermaid para reflejar la arquitectura Dual-Core SMP, asignación de núcleos, jerarquía de 5 tareas FreeRTOS, mapa de pines del ESP32-S3 N16R8, máquina de estados con Fail-Safe Latch ISA-18.2 y protocolo de balanza gravimétrica asistida.

### ⚖️ Balanza Gravimétrica Asistida (ISA-88) y Culombimetría
- **Flujo Interactivo de Pesaje**:
  - Solicita el **Peso Inicial ($P_{\text{ini}}$)** antes de arrancar el temporizador de la Etapa 1 (Limpieza).
  - Solicita el **Peso Final ($P_{\text{fin}}$)** al terminar la Etapa 4 (Niquelado Watts).
  - Soporta balanzas analíticas de laboratorio con hasta 6 cifras significativas / 4 decimales (ej. `25.4321` g o `8.1234` g).
  - Calcula automáticamente $\Delta m_{\text{real}}$, $m_{\text{teo}} = \frac{Q \cdot M}{z \cdot F}$, rendimiento de corriente Faradaico $\eta\%$ y espesor estimado en $\mu\text{m}$.
  - Persiste los resultados en `resumen_receta.txt` y en las columnas del CSV de telemetría.

### 🌀 Retrato de Fase y Control en el Espacio de Estados
- **Monitoreo en el Plano de Estados $\dot{e}(t)$ vs $e(t)$**:
  - Implementado en `VentanaErrores` para evaluar la estabilidad del control térmico en las 4 tinas.
  - Zona atractora de alta estabilidad centrada en $(0,0)$ con bandas $\pm 0.5\,{}^\circ\text{C}$ y $\pm 0.05\,{}^\circ\text{C/s}$.

### 📊 Suite de 5 Figuras Científicas a 300 DPI (`graficar_datos.py`)
1. `01_perfil_electroquimico_termico.png`: Perfiles térmicos multizona y corriente galvánica real.
2. `02_seguimiento_errores_control.png`: Errores instantáneos $e(t)$ e índices IAE acumulados.
3. `03_actuadores_triacs_potencia.png`: Ángulos de fase $\alpha$ (°), retardos de gate ($\mu\text{s}$) y potencia activa RMS en Watts.
4. `04_analisis_faraday_plano_fase.png`: Carga acumulada $Q(t)$ vs masa teórica/real y Retrato de Fase $\dot{e}(t)$ vs $e(t)$.
5. `05_diagnostico_integral_resumen.png`: **Dashboard Ejecutivo** de 4 cuadrantes (IAE global, consumo energético en Wh / kWh de las 4 tinas, balance gravimétrico y condiciones ambientales de laboratorio).

---

## 🏆 [3.5.0] - Versión 3.5 (Lazo Cerrado VCSS, Relé ZCS & SCADA Inicial)
- Versión estable bajo arquitectura Super-Loop asíncrono.
- Sumidero de corriente en lazo cerrado con sensado diferencial en shunts (ADS1115 Canales A2/A3).
- Relé de aislamiento galvánico de +12V con conmutación ZCS (GPIO 20).
- Calibración automática de transconductancia $G_m$ con almacenamiento en NVS Flash.
- Gestor de recetas ISA-88 con matriz de 32 placas experimentales desde Excel.
- Osciloscopio virtual de disparo de fase y paquetes de ciclos (Burst Firing) para TRIACs.

---

## ⚡ [3.0.0 / 3.1.0] - Versión 3.0 (OTA Web & Diagnóstico de Sensores)
- Actualización de firmware vía Wi-Fi por página web `/update` con particionamiento `Minimal SPIFFS (1.9MB APP with OTA)`.
- Endpoint `/sensores` y `/data_env` para monitoreo de 8 periféricos I2C/SPI.
- Filtrado digital por mediana móvil de 3 puntos en lectura de pH.

---

## 🟢 [2.0.0] - Versión 2.0 (pH Tri-Modo & Interlocks)
- Calibración de pH en 1, 2 y 3 puntos con compensación Nernst.
- Interlock de hardware para aislamiento de celda durante calibración de pH.

---

## 🔵 [1.0.0] - Versión 1.0 (Modular Inicial)
- Separación de módulos térmicos, fuente y pH.
- Algoritmo PI con Anti-Windup condicional para control térmico.

# Planta Piloto de Electrodeposición y Galvanoplastia
### Control Ciberfísico en Tiempo Real (ESP32-S3 RTOS 2.0 + ATmega328P + SCADA PC)

> **Desarrollado y Diseñado por: Salvador² C Dev Team**  
> *Automatización, Instrumentación Industrial y Control Metrológico de Procesos Electroquímicos.*  
> *Línea experimental para Zincado Ácido en Celda Hull (267 mL) y Niquelado Electrolítico sobre Sustrato de Aluminio Al 6061-T6.*

---

## 1. De qué trata este sistema

La galvanoplastia sobre aluminio es un proceso notoriamente delicado: el aluminio forma espontáneamente una película pasivante de óxido que arruina la adherencia, mientras que los electrolitos ácidos y las altas corrientes de deposición generan ruido electromagnético y caídas de tensión parásitas que desestabilizan cualquier sensor estándar.

Este proyecto resuelve ese reto construyendo una **planta piloto automatizada de 4 tinas**, gobernada por una arquitectura distribuida donde el hardware, el firmware en tiempo real y el software de supervisión en PC trabajan como una sola unidad:

1. **Etapa 1 — Desengrase Alcalino (85-90 °C, 240 s):** Limpieza termoquímica superficial con Na3PO4, Na2SiO4 y PEG-400.
2. **Etapa 2 — Decapado y Activación (85-90 °C, 120 s):** Remoción selectiva de alúmina sin atacar el metal base.
3. **Etapa 3 — Zincado en Celda Hull (25 °C o 40 °C, 120 o 300 s):** Electrodeposición en celda trapezoidal de 267 mL con corriente continua (1.50 A DC) o pulsada (10 Hz / 20% duty cycle) para evaluar el rango de densidad de corriente sobre toda la longitud de la probeta.
4. **Etapa 4 — Niquelado Electrolítico (30-40 °C, 600 s):** Capa protectora con baño Watt modificado estabilizado con Na2SO4 para prevenir desplazamiento galvánico espontáneo.

---

## 2. Arquitectura Técnica (Versión RTOS 2.0)

El sistema opera con la versión de producción **RTOS 2.0**, diseñada para garantizar determinismo temporal y aislamiento total de ruido:

### Nodo Maestro ESP32-S3 (Dual-Core @ 240 MHz, 16 MB Flash, 8 MB PSRAM)
* **Concurrencia Simétrica FreeRTOS:**
  * **Core 1 (Tiempo Real Estricto):** Lazos de control térmico PI (1 Hz), modulación analógica de corriente VCSS, muestreo continuo a 860 SPS en ADC ADS1115 y máquina de seguridad Fail-Safe (50 Hz).
  * **Core 0 (Comunicaciones y Red):** Servidor HTTP embebido, endpoints REST JSON (`/data_all`, `/data_f`, `/data_t`, `/ph`), servidor de telemetría y actualización OTA.
* **Medición de pH en Canal A1 (ADS1115):**  
  La señal potenciométrica del módulo PH-4502C se adquiere de forma directa y continua a través del **Canal A1** del convertidor ADS1115 a **860 SPS**. Aplica un filtro en cascada en Core 1: promedio por bloques, mediana móvil y filtro pasabajas IIR adaptativo (α = 0.30 en transitorios, α = 0.08 en reposo), con calibración multipunto independiente por modo persistida en Flash NVS.
* **Lazo de Corriente VCSS (Sumidero Analógico Gm = 2.00 S):**  
  Modulación directa por DAC MCP4725 de 12 bits sobre dos ramas MOSFET con dos shunts cerámicos de 1.0 Ω / 10W en paralelo (resistencia equivalente de 0.50 Ω con 20W de disipación térmica combinada, garantizando seguridad industrial contra sobrecalentamiento e incendio en régimen DC y pulsado a 10 Hz). Monitoreo continuo de corriente por rama (A2/A3) y diagnóstico de salud de celda (`SaludCelda_t`).
* **Secuencia ZCS (Zero-Current Switching):**  
  Al detener la fuente o finalizar el cronómetro de la etapa, el firmware reduce la consigna del DAC a 0V, espera 30 ms para disipación de corriente remanente en la celda y abre el relé mecánico de aislamiento de +12V a corriente cero, eliminando arcos eléctricos y desgaste de contactos.

### Coprocesador de Potencia AC (Arduino Nano ATmega328P @ 16 MHz)
* Control de fase de 60 Hz para 4 calentadores de inmersión de 450 W.
* Sincronizado por interrupción externa de cruce por cero (INT1, pin 3).
* Linealización senoidal trigonométrica de potencia RMS (retardo de compuerta entre 0 y 8333 μs) y watchdog UART para apagado automático en caso de pérdida de enlace con el ESP32.

### SCADA Telemetría 2.0 (Python / Windows)
* **Gestión de Recetas ISA-88 desde Excel:** Carga dinámica de la matriz experimental (`matriz_experimentos.xlsx`) para 32 probetas, con selección automática de tiempos, consignas de temperatura y modos de corriente (DC continuo o Pulsado a 10 Hz / 20% duty cycle, con soporte para columnas personalizadas de frecuencia y ciclo de trabajo).
* **Culombimetría Faradaica en Lazo Cerrado:** Integración activa únicamente durante la cuenta del cronómetro de etapas galvánicas (`etapa_corriendo == True` y `act == 1`), ponderando por ciclo de trabajo en corriente pulsada (`I_efectiva = I_pico × Duty/100`) y congelando la acumulación al llegar a 00:00 o en pausas.
* **Modelo Aditivo Bicapa Zn + Ni:** Cálculo de masa teórica total `m_teo = Q_Zn × 0.33880 mg/C + Q_Ni × 0.30414 mg/C` acoplado con pesaje en balanza analítica para determinar la eficiencia catódica global (η%) y los espesores individuales y totales de película (μm).
* **Motor de Exportación Científica:** Generación de figuras publication-ready a 300 DPI y registro en CSV estructurado con marcas ISA-88 y tiempos muertos de transferencia.

---

## 3. Estructura del Repositorio

El árbol de archivos está organizado de manera modular, separando firmware, software de escritorio, ingeniería de hardware y pruebas:

```text
Proyecto/
├── Iniciar_Sistema.bat        <- Lanzador interactivo principal (doble clic)
├── Iniciar_Telemetria_2.0.bat <- Acceso directo a la estacion SCADA en vivo
├── launcher.py                <- Panel maestro de inicio en Python (GUI y consola)
├── README.md                  <- Documentacion tecnica y de arquitectura
├── AGENTS.md                  <- Estandares de codificacion, estilo y formato
├── requirements.txt           <- Dependencias oficiales de Python
├── pytest.ini                 <- Configuracion de la suite de pruebas unitarias
├── conftest.py                <- Resolucion limpia de rutas para tests
├── .gitignore                 <- Reglas de exclusion y proteccion de datos sensibles
│
├── firmware/                  <- Codigo fuente de microcontroladores
│   ├── esp32/
│   │   ├── RTOS2.0/           <- Firmware de produccion activo (FreeRTOS Dual-Core SMP)
│   │   └── historico/         <- Registro historico de versiones (RTOS 1.0-1.4 y Superloop)
│   └── arduino_nano/
│       ├── nano/              <- Dimmer AC 60Hz activo con control de fase por interrupcion
│       └── historico/         <- Versiones previas de prueba
│
├── software/                  <- Software SCADA y procesamiento en PC
│   ├── telemetria2.0/         <- SCADA activo (Matriz ISA-88, Faraday, Balanza analitica)
│   ├── telemetria/            <- SCADA base v1.0 (referencia)
│   └── exportar_graficas_offline.py <- Generador de figuras cientificas a 300 DPI
│
├── tests/                     <- Suite de pruebas automatizadas (Pytest)
│   ├── test_calculos.py       <- Culombimetria de Faraday, duty cycle y linealizacion del TRIAC
│   ├── test_interlocks.py     <- Validacion de interlocks ISA-88 y secuencia ZCS
│   └── test_telemetria_json.py <- Esquemas y contratos JSON entre ESP32 y SCADA
│
├── hardware/                  <- Documentacion fisica y electronica
│   ├── esquemas_y_bom/        <- Lista de materiales (BOM.md) y diagramas de conexion
│   └── control_matlab/        <- Modelado termico y cinetico en MATLAB
│
├── documentos/                <- Documentacion tecnica y manuales de operacion
│   ├── manuales/              <- Manual interactivo de operacion quimica (HTML y Markdown)
│   ├── guias/                 <- Guia de configuracion y compilacion de herramientas
│   ├── datasheets/            <- Hojas de datos de componentes electronicos y sensores
│   ├── imagenes/              <- Capturas de interfaz y diagramas
│   └── instaladores/          <- Scripts de configuracion de dependencias
│
└── visualizacion/             <- Diagramas y simuladores
    ├── diagramas/             <- Visor interactivo y modelos Mermaid de arquitectura
    └── preview/               <- Simuladores web offline de las interfaces del ESP32
```

---

## 4. Aseguramiento de Calidad y Pruebas Automatizadas

El proyecto cuenta con una suite de **25 pruebas unitarias automatizadas** que se ejecutan en menos de 0.05 segundos con `pytest`:

```bash
python -m pytest -v
```

* **Física y Metrología ([tests/test_calculos.py](tests/test_calculos.py)):** Verificación matemática de la masa teórica faradaica en DC y pulsado ponderado por ciclo de trabajo, inmunidad de integración en reposo, modelo bicapa aditivo Zn+Ni, espesores micrométricos y linealización de retardo TRIAC de 60 Hz (0 a 8333 μs).
* **Interlocks de Seguridad ([tests/test_interlocks.py](tests/test_interlocks.py)):** Verificación del aislamiento entre electrodo de pH y lazo de corriente, enclavamiento por Fail-Safe, restricciones de calibración y conmutación ZCS.
* **Contratos de Telemetría ([tests/test_telemetria_json.py](tests/test_telemetria_json.py)):** Validación de rangos del DAC (0 a 4095), transconductancia Gm, resolución de sensores y manejo defensivo ante pérdidas parciales de paquetes.
* **Pre-Commit Hook (.git/hooks/pre-commit):** Cada commit en Git corre automáticamente la suite completa; si se introduce una regresión matemática o lógica, el commit se detiene.

---

## 5. Puesta en Marcha

### Requisitos:
* Sistema operativo Windows 10 u 11.
* Python 3.9 o superior.

### Instalación en 2 pasos:
1. Clonar el repositorio e instalar las dependencias:
   ```bash
   git clone https://github.com/Chavacastro98/Proyecto.git
   cd Proyecto
   pip install -r requirements.txt
   ```
2. Ejecutar el panel de control:
   * Hacer doble clic en [`Iniciar_Sistema.bat`](Iniciar_Sistema.bat), o
   * Ejecutar en terminal:
     ```bash
     python launcher.py
     ```

Para iniciar directamente la estación de monitoreo SCADA en vivo, haz doble clic en [`Iniciar_Telemetria_2.0.bat`](Iniciar_Telemetria_2.0.bat).

---

## 6. Generación de Figuras Científicas (300 DPI)

Para generar el paquete de figuras científicas de alta resolución para la memoria de resultados:

```bash
python software/exportar_graficas_offline.py
```

Genera automáticamente las 8 figuras normalizadas:
1. **01:** Perfil electroquímico y térmico simultáneo de las 4 tinas.
2. **02:** Error de seguimiento térmico instantáneo `e(t) = SP - PV` con bandas de tolerancia de ±0.5 °C e índice IAE.
3. **03:** Ángulos de disparo del TRIAC α (°), retardos de compuerta (μs) y potencia RMS calculada.
4. **04:** Culombimetría faradaica integrada `Q(t) = ∫ I dt`, comparación gravimétrica y plano de fase.
5. **05:** Diagnóstico integral de proceso (consumo energético acumulado en Wh, gravimetría y condiciones meteorológicas).
6. **06:** Diagrama de Gantt de fases operativas ISA-88 y tiempos muertos de transferencia.
7. **07:** Reconstrucción ETS (Equivalent Time Sampling) de la forma de onda de corriente a 100 Hz.
8. **08:** Distribución longitudinal de densidad de corriente J(x) en Celda Hull y perfil de espesor de zinc.

---

**Salvador² C Dev Team**  
*Ingeniería de Procesos Electroquímicos, Sistemas Embebidos e Instrumentación Científica.*

# Planta Piloto de Electrodeposición y Galvanoplastia
### Control Ciberfísico en Tiempo Real (ESP32-S3 RTOS 2.0 + ATmega328P + SCADA PC)

[![Status: WIP](https://img.shields.io/badge/Status-Work%20In%20Progress%20(WIP)-amber?style=for-the-badge&logo=git)](https://github.com/Chavacastro98/Proyecto)
[![Showcase: Live](https://img.shields.io/badge/Showcase%20Web-GitHub%20Pages-0ea5e9?style=for-the-badge&logo=github)](https://chavacastro98.github.io/Proyecto/)
[![Tests: 25 Passed](https://img.shields.io/badge/Tests-25%20Passed-10b981?style=for-the-badge&logo=pytest)](tests/)
[![MCU: ESP32-S3 + Nano](https://img.shields.io/badge/Hardware-ESP32--S3%20%7C%20ATmega328P-8b5cf6?style=for-the-badge)](firmware/)

> [!WARNING]
> ### 🚧 Repositorio en Desarrollo Activo / Work In Progress (WIP)
> **Este repositorio se encuentra actualmente en proceso de desarrollo, documentación y reestructuración activa.**  
> El equipo técnico se encuentra trabajando en:
> 1. **Elaboración y estandarización del Manual Técnico y Operativo de Laboratorio.**
> 2. **Consolidación y limpieza estructural de las páginas web públicas (GitHub Pages) y herramientas de despliegue.**
>
> 🌐 **Showcase Técnico Interactivo (GitHub Pages):** [https://chavacastro98.github.io/Proyecto/](https://chavacastro98.github.io/Proyecto/)  
> 📁 **Repositorio Oficial de Código (GitHub):** [https://github.com/Chavacastro98/Proyecto](https://github.com/Chavacastro98/Proyecto)  
> 📑 **Cartel Científico SMEQ 2026 — Folio CTS-C51:** *Optimización Electroquímica de Recubrimientos de Zinc sobre Aluminio 6061 T-6.*

---

## 1. De qué trata este sistema

La galvanoplastia sobre aluminio es un proceso notoriamente delicado: el aluminio forma espontáneamente una película pasivante de óxido que arruina la adherencia, mientras que los electrolitos ácidos y las altas corrientes de deposición generan ruido electromagnético y caídas de tensión parásitas que desestabilizan cualquier sensor estándar.

Este proyecto resuelve ese reto construyendo una **planta piloto automatizada de 3 tinas de tratamiento químico + Celda Hull (267 mL)**, gobernada por una arquitectura distribuida donde el hardware, el firmware en tiempo real y el software de supervisión en PC trabajan como una sola unidad:

1. **Etapa 1 — Desengrase Alcalino (85-90 °C, 240 s):** Limpieza termoquímica superficial con Na₃PO₄, Na₂SiO₃ y PEG-400.
2. **Etapa 2 — Decapado y Activación Alcalina (85-90 °C, 120 s):** Remoción selectiva de la película pasivante de alúmina sin atacar el metal base.
3. **Etapa 3 — Zincado en Celda Hull (25 °C o 40 °C, 120 o 300 s):** Electrodeposición en celda trapezoidal normalizada de 267 mL con corriente continua (1.50 A DC) o pulsada (10 Hz / 20% duty cycle) para evaluar el gradiente de densidad de corriente sobre toda la longitud de la probeta.
4. **Etapa 4 — Niquelado Electrolítico sobre Zinc (30-40 °C, 600 s):** Depósito protector final a 1.13 A DC con baño estabilizado para inhibir el desplazamiento galvánico espontáneo sobre el zinc subyacente.

---

## 2. Arquitectura Técnica (Versión RTOS 2.0)

El sistema opera con la versión de producción **RTOS 2.0**, diseñada para garantizar determinismo temporal y aislamiento total de ruido:

### Nodo Maestro ESP32-S3 (Dual-Core @ 240 MHz, 16 MB Flash, 8 MB PSRAM)
* **Concurrencia Simétrica FreeRTOS:**
  * **Core 1 (Tiempo Real Estricto):** Lazos de control térmico PI (1 Hz), modulación analógica de corriente VCSS, muestreo continuo a 860 SPS en ADC ADS1115 y máquina de seguridad Fail-Safe (50 Hz).
  * **Core 0 (Comunicaciones y Red):** Servidor HTTP embebido, endpoints REST JSON (`/data_all`, `/data_f`, `/data_t`, `/ph`), servidor de telemetría y actualización OTA (Over-The-Air) a través del punto de acceso Wi-Fi SoftAP ("Uli"). Esto permite operación totalmente autónoma e inalámbrica, eliminando la conexión de cables USB a la computadora durante los ensayos electroquímicos.
* **Medición de pH en Canal A1 (ADS1115):**  
  La señal potenciométrica del módulo PH-4502C se adquiere de forma directa y continua a través del **Canal A1** del convertidor ADS1115 a **860 SPS**. Aplica un filtro en cascada en Core 1: promedio por bloques, mediana móvil y filtro pasabajas IIR adaptativo (α = 0.30 en transitorios, α = 0.08 en reposo), con calibración multipunto independiente por modo persistida en Flash NVS.
* **Lazo de Corriente VCSS (Sumidero Analógico Gm = 2.00 S):**  
  Modulación directa por DAC MCP4725 de 12 bits sobre dos ramas MOSFET con dos shunts cerámicos de 1.0 Ω / 10W en paralelo (resistencia equivalente de 0.50 Ω con 20W de disipación térmica combinada, garantizando seguridad industrial contra sobrecalentamiento e incendio en régimen DC y pulsado a 10 Hz). Monitoreo continuo de corriente por rama (A2/A3) y diagnóstico de salud de celda (`SaludCelda_t`).
* **Secuencia ZCS (Zero-Current Switching):**  
  Al detener la fuente o finalizar el cronómetro de la etapa, el firmware reduce la consigna del DAC a 0V, espera 30 ms para disipación de corriente remanente en la celda y abre el relé mecánico de aislamiento de +12V a corriente cero, eliminando arcos eléctricos y desgaste de contactos.

### Coprocesador de Potencia AC (Arduino Nano ATmega328P @ 16 MHz)
* **Módulo de TRIACs de Fabricación Propia:** Etapa de potencia de 4 canales diseñada por el equipo con 4x TRIACs BTA24-800BW y optoacopladores MOC3021, gobernando 3 resistencias de inmersión de 450 W (Tinas 1, 2 y 4) y 1 calentador de cartucho de 18 W (Tina 3 - Celda Hull de 267 mL).
* **Firmware Nano2 (Tiempo Proporcional / Burst Firing):** Modula la potencia térmica a ciclos completos de 60 Hz en ventanas temporales fijas de 3000 ms mediante la librería `JELDimmer2`, conmutando exclusivamente en cruces por cero. Esta estrategia suprime la interferencia electromagnética (EMI) por conmutación abrupta sobre los sensores de pH y termopares.
* **Seguridad por Perro Guardián UART:** Si el enlace serie con el ESP32 se interrumpe por más de 4000 ms, el Nano apaga inmediatamente todas las compuertas de los TRIACs.

### SCADA Telemetría 2.0 (Python / Windows)
* **Gestión de Recetas ISA-88 desde Excel:** Carga dinámica de la matriz experimental (`matriz_experimentos.xlsx`) para 32 probetas, con selección automática de tiempos, consignas de temperatura y modos de corriente (DC continuo o Pulsado a 10 Hz / 20% duty cycle, con soporte para columnas personalizadas de frecuencia y ciclo de trabajo).
* **Culombimetría Faradaica en Lazo Cerrado:** Integración activa únicamente durante la cuenta del cronómetro de etapas galvánicas (`etapa_corriendo == True` y `act == 1`), ponderando por ciclo de trabajo en corriente pulsada (`I_efectiva = I_pico × Duty/100`) y congelando la acumulación al llegar a 00:00 o en pausas.
* **Modelo Aditivo Bicapa Zn + Ni:** Cálculo de masa teórica total `m_teo = Q_Zn × 0.33880 mg/C + Q_Ni × 0.30414 mg/C` acoplado con pesaje en balanza analítica para determinar la eficiencia catódica global (η%) y los espesores individuales y totales de película (μm).
* **Motor de Exportación Científica:** Generación de figuras publication-ready a 300 DPI y registro en CSV estructurado con marcas ISA-88 y tiempos muertos de transferencia.
* **Datos Demostrativos y Validación Funcional:** Las curvas y registros CSV incluidos actualmente en el repositorio corresponden a corridas de validación funcional en banco para estandarización del manual operativo y del showcase científico (SMEQ 2026). La campaña experimental formal de 32 probetas completas se encuentra bajo custodia del equipo de investigación de tesis.

---

## 3. Estructura del Repositorio

El árbol de archivos está organizado de manera modular, separando firmware, software de escritorio, ingeniería de hardware, pruebas y despliegue web:

```text
Proyecto/
├── Iniciar_Sistema.bat        <- Lanzador interactivo principal (doble clic)
├── Iniciar_Telemetria_2.0.bat <- Acceso directo a la estacion SCADA en vivo
├── launcher.py                <- Panel maestro de inicio en Python (GUI y consola)
├── README.md                  <- Documentacion tecnica y de arquitectura (WIP)
├── AGENTS.md                  <- Estandares de codificacion, estilo y formato
├── requirements.txt           <- Dependencias oficiales de Python
├── pytest.ini                 <- Configuracion de la suite de pruebas unitarias
├── conftest.py                <- Resolucion limpia de rutas para tests
├── .gitignore                 <- Reglas de exclusion y proteccion de datos sensibles
│
├── docs/                      <- Publicacion web oficial GitHub Pages (Arquitectura modular)
│   ├── index.html             <- Punto de entrada del Showcase Tecnico e Interactivo
│   ├── css/                   <- Estilos CSS modulares (tokens, layout, components, responsive)
│   ├── js/                    <- Modulos de logica JS (app, simuladores, galeria, telemetria)
│   └── assets/                <- Evidencia fotografica, diagramas e instrumentacion
│
├── firmware/                  <- Codigo fuente de microcontroladores
│   ├── esp32/
│   │   ├── RTOS2.0/           <- Firmware de produccion activo (FreeRTOS Dual-Core SMP)
│   │   └── historico/         <- Registro historico de versiones (RTOS 1.0-1.4 y Superloop)
│   └── arduino_nano/
│       ├── nano2/             <- Firmware de calentamiento activo: Tiempo proporcional (Burst Firing 3s)
│       ├── nano/              <- Variante alternativa con control por recorte de fase (LUT 60Hz)
│       └── historico/         <- Prototipos previos (Nano Beta)
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
├── herramientas/              <- Utilidades de automatizacion y soporte CI/CD
│   └── sincronizar_pages.py   <- Pipeline automatico de empaquetado y despliegue a docs/
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

## 7. Equipo de Investigación y Contacto

Proyecto de Titulación / Tesis de Licenciatura e Investigación Científica aplicada en Automatización e Ingeniería Electroquímica:

* **Víctor Ulises Gutiérrez Ramírez**  
  * Correo Institucional: [victor.gutierrez7221@alumnos.udg.mx](mailto:victor.gutierrez7221@alumnos.udg.mx)  
  * Rol: Desarrollo de Firmware RTOS 2.0, Control Ciberfísico e Instrumentación Electrónica.

* **Salvador Castro Pérez**  
  * Correo Institucional: [salvador.castro7435@alumnos.udg.mx](mailto:salvador.castro7435@alumnos.udg.mx)  
  * Rol: Automatización Industrial, Arquitectura SCADA Telemetría 2.0 y Modelado Físico-Matemático.

* **Fernando Salvador Samayoa Martínez**  
  * Correo Institucional: [fernando.samayoa0621@alumnos.udg.mx](mailto:fernando.samayoa0621@alumnos.udg.mx)  
  * Rol: Ingeniería Electroquímica, Formulación de Baños y Análisis Gravimétrico/Faradaico.

### Directores y Asesores de Tesis
* **Dr. Omar Alejandro González Meza** — Profesor Investigador, CUCEI, Universidad de Guadalajara.
* **Dr. Norberto Casillas Santana** — Profesor Investigador, Departamento de Química, CUCEI, Universidad de Guadalajara.

---

**Salvador² C Dev Team**  
*Ingeniería de Procesos Electroquímicos, Sistemas Embebidos e Instrumentación Científica.*  
*Centro Universitario de Ciencias Exactas e Ingenierías (CUCEI) — Universidad de Guadalajara.*

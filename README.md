# Sistema Automatizado de Electrodeposición y Galvanoplastia (ESP32-S3 N16R8 RTOS 2.0 + Arduino Nano)

> **Tesis de Licenciatura en Ingeniería / Química de Procesos Electroquímicos**  
> *Automatización, Instrumentación y Control de Línea Piloto para Procesos de Zincado (Celda Hull 267 mL) y Niquelado sobre Zinc con Lazo VCSS, Supervisión SCADA y Balanza Gravimétrica (Ley de Faraday).*

---

## 1. Arquitectura del Sistema (Versión RTOS 2.0)

El proyecto preserva las versiones previas en sus respectivas carpetas históricas. La versión de producción activa es **RTOS 2.0**, estructurada en los siguientes módulos de control:

1. **Medición de pH Pseudo-Diferencial (Canales A1 y A0 Kelvin Ground)**: El canal A1 adquiere la señal acondicionada del electrodo de vidrio (Po), mientras que el canal A0 toma la referencia analógica local aislada (Kelvin Ground) para suprimir ruidos de modo común y caídas óhmicas causadas por las corrientes galvánicas de celda. Muestreo continuo a 860 SPS en el convertidor ADS1115 con filtrado digital en cascada (promedio de bloque de 10 muestras, mediana móvil de 3 puntos y filtro pasabajas adaptativo IIR).
2. **Calibración Metrológica NVS por Modo**: Almacenamiento desacoplado en memoria Flash NVS de los coeficientes de calibración independientes por modo (Teórico, 2 Puntos Ácido y 3 Puntos Asimétrico). Acondicionamiento analógico para voltímetro digital y módulo PH-4502C.
3. **Control de Corriente VCSS (Single-Writer)**: Conducción por escalón directo calibrado al convertidor DAC MCP4725. La capacitancia de la doble capa electroquímica (Cdl) en la interfase electrodo/electrolito amortigua transitorios naturalmente y proporciona la sobretensión necesaria para una nucleación homogénea del zinc. Incluye monitoreo analógico de transconductancia (Gm = 2.0 S) con shunts de corriente y diagnóstico continuo de estado (`SaludCelda_t`).
4. **Concurrencia FreeRTOS SMP Dual-Core**: Asignación simétrica de núcleos (Core 0 para pila TCP/IP, servidor HTTP, endpoints JSON y OTA; Core 1 para lazos de control en tiempo real y muestreo determinista). Sincronización mediante mutexes dedicados (`xI2CMutex`, `xSPIMutex`, `xDataMutex`, `xLogMutex`) y parada de emergencia segura con corte previo en cero corriente (ZCS).
5. **Coprocesador de Potencia AC (Arduino Nano ATmega328P)**: Control de fase de 60 Hz para 4 calentadores de 450W mediante interrupción externa de cruce por cero (INT1 en pin 3), tabla de retardo trigonométrico para linealización de potencia RMS y desconexión automática por perro guardián serie UART.
6. **SCADA Telemetría 2.0**: Supervisión en PC optimizada para Windows 10/11 con matriz ISA-88, culombimetría faradaica continua integrada con pesaje de balanza analítica (4 decimales) y generación automática de reportes y figuras a 300 DPI.

---

## 2. Guía de Puesta en Marcha

### Opciones de Inicio:
* **Panel de Control Maestro**: Ejecutar [`launcher.py`](launcher.py) o hacer doble clic en [`Iniciar_Sistema.bat`](Iniciar_Sistema.bat). Despliega el menú para acceder a Telemetría 2.0, visor de diagramas, manual químico y suite de gráficas.
* **Telemetría Directa (SCADA en Vivo)**: Doble clic en [`Iniciar_Telemetria_2.0.bat`](Iniciar_Telemetria_2.0.bat).
* **Lanzadores por Módulo**: En la carpeta [`herramientas/lanzadores/`](herramientas/lanzadores/) se encuentran accesos directos independientes para cada herramienta.

---

## 3. Especificaciones del Hardware Maestro (ESP32-S3 N16R8)

| Parámetro | Especificación | Configuración en Arduino IDE |
| :--- | :--- | :--- |
| **Microcontrolador** | ESP32-S3 Dual-Core Xtensa LX7 @ 240 MHz | `ESP32S3 Dev Module` |
| **Memoria Flash Externa** | 16 MB (128 Mbit) Quad/Octal SPI | `16MB (128Mb)` |
| **Memoria RAM / PSRAM** | 512 KB SRAM interna + 8 MB Octal-SPI PSRAM | `OPI PSRAM` |
| **Esquema de Partición** | 16 MB (3.0 MB APP / 9.9 MB FATFS) con soporte OTA | `16M Flash (3MB APP/9.9MB FATFS)` |
| **Frecuencia Bus I2C** | 400 kHz (Fast Mode) en GPIO 8 (SDA) y GPIO 9 (SCL) | `Wire.setClock(400000)` |
| **Comunicaciones USB** | USB-C Nativo con CDC activo en arranque | `USB CDC On Boot: Enabled` |
| **Nodo de Potencia AC** | Arduino Nano (ATmega328P @ 16 MHz) vía UART2 (TX GPIO 17) | `9600 bps, 8N1` |

---

## 4. Estructura del Repositorio

```text
Proyecto/
├── Iniciar_Sistema.bat        <- Lanzador interactivo principal (doble clic)
├── Iniciar_Telemetria_2.0.bat <- Lanzador directo de Telemetria 2.0
├── launcher.py                <- Panel maestro de inicio en Python (GUI / CLI)
├── README.md                  <- Documentacion general y arquitectura
├── AGENTS.md                  <- Reglas de estilo y desarrollo
├── requirements.txt           <- Dependencias de Python (requests, matplotlib, pandas, etc.)
│
├── firmware/                  <- Codigo fuente de microcontroladores
│   ├── esp32/                 <- Nodo maestro ESP32-S3
│   │   ├── RTOS2.0/           <- Firmware activo (FreeRTOS SMP Dual-Core)
│   │   └── historico/         <- Archivo de versiones previas (RTOS 1.0-1.4 y Super-Loop)
│   └── arduino_nano/          <- Nodo de potencia (Dimmer AC 60Hz ATmega328P)
│       ├── nano/              <- Firmware activo con control de fase por interrupcion
│       └── historico/         <- Versiones previas de prueba
│
├── software/                  <- Aplicaciones SCADA y procesamiento en PC
│   ├── telemetria2.0/         <- SCADA activo (Matriz ISA-88, Faraday, Balanza analitica)
│   ├── telemetria/            <- SCADA v1.0 (Version base de referencia)
│   └── exportar_graficas_offline.py <- Generador de figuras cientificas a 300 DPI
│
├── hardware/                  <- Documentacion electronica y modelado
│   ├── esquemas_y_bom/        <- Lista de materiales (BOM.md) y diagramas esquematicos
│   └── control_matlab/        <- Modelado termico y cinetico en MATLAB
│
├── documentos/                <- Documentacion tecnica, quimica y academica
│   ├── academicos/            <- Tesis de licenciatura, cartel y protocolo experimental
│   ├── manuales/              <- Manual interactivo de operacion quimica (HTML y Markdown)
│   ├── guias/                 <- Guia de compilacion y configuracion del entorno
│   ├── datasheets/            <- Hojas de datos tecnicas de componentes y sensores
│   ├── imagenes/              <- Capturas de telemetria y diagramas
│   └── instaladores/          <- Scripts de configuracion de dependencias
│
├── visualizacion/             <- Diagramas tecnicos y simuladores web
│   ├── diagramas/             <- Visor interactivo y diagramas Mermaid de arquitectura
│   └── preview/               <- Simuladores web de interfaces de usuario
│
└── herramientas/              <- Utilidades y scripts auxiliares
    ├── lanzadores/            <- Accesos directos independientes por modulo
    └── scratch/               <- Scripts de prueba y verificacion experimental
```

---

## 5. Protocolo de Ensayo y Metrología Faradaica (ISA-88)

El software SCADA [`telemetria2.0`](software/telemetria2.0/) integra el flujo automatizado para el ensayo experimental de galvanoplastia sobre sustrato de aluminio Al 6061-T6:

1. **Selección de Receta**: Selección de placa experimental según la matriz de variables (pH 2 o 4, temperatura de 25 °C o 40 °C, corriente continua DC o pulsada).
2. **Registro de Peso Inicial**: Captura asistida del peso de la probeta virgen en balanza analítica (P_ini con resolución de 0.0001 g).
3. **Secuencia de Fases (Protocolo VUGR)**:
   - **Etapa 1 (Desengrase Alcalino)**: 240 s @ 85-90 °C (0.00 A, Na3PO4 + Na2SiO4 + PEG-400).
   - **Etapa 2 (Decapado Alcalino)**: 120 s @ 85-90 °C (0.00 A, Na3PO4 · 12H2O 37.5 g/L). Remoción controlada de óxido de aluminio sin degradación superficial.
   - **Etapa 3 (Zincado en Celda Hull 267 mL)**: 120 s / 300 s @ 25 °C / 40 °C (1.50 A DC o Pulsado 10 Hz / 20%, baño ZnSO4).
   - **Etapa 4 (Niquelado sobre Zinc)**: 600 s (10 min) @ 30-40 °C (1.13 A DC, NiSO4 + Na2SO4). El sulfato de sodio estabiliza el potencial y evita el desplazamiento galvánico espontáneo.
4. **Registro de Peso Final**: Al terminar la secuencia, se registra el peso seco de la pieza electrodepositada (P_fin en gramos).
5. **Cálculos Faradaicos**:
   - Masa real depositada: `Δm_real = P_fin - P_ini` (mg)
   - Masa teórica esperada: `m_teo = (Q_total · M) / (z · F)` (mg)
   - Eficiencia de corriente: `η = (Δm_real / m_teo) · 100%`
   - Espesor medio de capa: `e = (Δm_real / (ρ · A)) · 10^4` (μm)

---

## 6. Generación de Figuras Científicas (300 DPI)

El script [`exportar_graficas_offline.py`](software/exportar_graficas_offline.py) genera la suite estandarizada de 8 figuras para la memoria de tesis:

| Figura | Archivo PNG | Descripción |
| :---: | :--- | :--- |
| **Fig. 1** | `01_perfil_electroquimico_termico.png` | Perfil térmico de las 4 tinas y respuesta de corriente real en la celda. |
| **Fig. 2** | `02_seguimiento_errores_control.png` | Errores térmicos instantáneos e(t) = SP - PV con bandas de tolerancia de ±0.5 °C e índice IAE. |
| **Fig. 3** | `03_actuadores_triacs_potencia.png` | Esfuerzo de control %, ángulos de disparo α (°), retardos de compuerta (μs) y potencia RMS calculada. |
| **Fig. 4** | `04_analisis_faraday_plano_fase.png` | Carga total integrada Q(t) = ∫ I dt, comparación de masa teórica vs real y plano de fase de error. |
| **Fig. 5** | `05_diagnostico_integral_resumen.png` | Resumen general: IAE térmico global, consumo energético acumulado en Wh, gravimetría y condiciones ambientales. |
| **Fig. 6** | `06_tiempos_muertos_gantt_fases.png` | Cronograma de ejecución por fases ISA-88 y registro de tiempos de transferencia. |
| **Fig. 7** | `07_forma_onda_pulsada_ets.png` | Reconstrucción estroboscópica ETS (Equivalent Time Sampling) de la corriente pulsada a 100 Hz. |
| **Fig. 8** | `08_correlacion_espesor_densidad.png` | Distribución longitudinal de densidad de corriente J(x) en Celda Hull y perfil de espesor local de zinc. |

---

## 7. Manual de Operación y Protocolo de Laboratorio

* **Acceso directo**: Doble clic en [`Iniciar_Sistema.bat`](Iniciar_Sistema.bat) (Opción 4) o en [`herramientas/lanzadores/Manual_de_Uso.bat`](herramientas/lanzadores/Manual_de_Uso.bat).
* **Documento fuente**: [`documentos/manuales/MANUAL_DE_OPERACION_QUIMICA.html`](documentos/manuales/MANUAL_DE_OPERACION_QUIMICA.html). Funciona en cualquier navegador de forma local sin dependencias de internet y es exportable a PDF con `Ctrl+P`.

---

## 8. Instalación y Requisitos

Para ejecutar el entorno en cualquier equipo con Windows 10 u 11:
1. Asegúrate de tener Python 3.9 o superior instalado.
2. Instala las librerías necesarias:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicia la aplicación:
   ```bash
   python launcher.py
   ```
   *(O simplemente haz doble clic en `Iniciar_Sistema.bat`).*

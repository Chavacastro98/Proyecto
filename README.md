# 🧪 Sistema Automatizado de Electrodeposición y Galvanoplastia (ESP32-S3 N16R8 RTOS 2.0 + Arduino Nano)

> **Tesis de Grado en Ingeniería / Química de Procesos Electroquímicos**  
> *Automatización, Instrumentación y Control de Línea Piloto para Procesos de Zincado (Celda Hull 267 mL) y Niquelado sobre Zinc con Lazo Cerrado VCSS, Supervisión SCADA y Balanza Gravimétrica (Ley de Faraday).*

---

## 🏛️ Aclaración Arquitectural: Estabilidad y Evolución hasta RTOS 2.0

> [!IMPORTANT]
> **Versiones Estables y Evolución Interna de Software:**  
> Las versiones **v3.5**, **v4.0** y la familia **RTOS (1.0 a 1.4)** son versiones estables y funcionales preservadas en el archivo histórico. La versión activa, insignia y definitiva en producción es **RTOS 2.0**:
> 1. **Sensor de pH Dedicado en Canal A1 (RTOS 2.0)**: Eliminación total del antiguo Canal A0. La sonda potenciométrica de pH opera con dedicación exclusiva en el Canal A1 del ADC ADS1115 con el 100% de uso del bus I2C, alcanzando muestreo continuo a 860 SPS sin retrasos de conmutación ni crosstalk.
> 2. **Calibración Metrológica NVS por Modo**: Almacenamiento desacoplado en memoria Flash NVS de los puntos de calibración independientes por modo (Ácido, Neutro, Básico). Panel de offset analógico de hardware calibrado para un único voltímetro digital y aguja para el módulo PH-4502C.
> 3. **Lazo Cerrado Híbrido VCSS (Single-Writer)**: Máquina de estados PI con Rampa Soft-Start (500 ms), Blanking anti-inrush optimizado a 300 ms (estabilización en <2.5s), PI discreto con Anti-Windup y banda muerta $\pm 10\text{ mA}$, muestreo estroboscópico ETS (Equivalent Time Sampling de 16 puntos) y diagnóstico continuo de salud de celda (`SaludCelda_t`).
> 4. **Manejo de Memoria y Concurrencia FreeRTOS SMP**: Copias coherentes (*Atomic Snapshots*) bajo `xDataMutex`, desacoplamiento de escrituras Flash fuera de secciones críticas y asignación simétrica de núcleos (Core 0 para red/HTTP/SSE/OTA y Core 1 para lazos de control deterministas).
> 5. **SCADA Telemetría 2.0 y Hardware**: Optimizado para **ESP32-S3 N16R8**, topología de alimentación híbrida (Fuente única 12V 10A + Pre-regulador Buck LM2596 a 6.80V + LDOs serie LM), matriz completa ISA-88, culombimetría faradaica continua, registro gravimétrico asistido (balanza analítica de 4 decimales) y suite científica offline de hasta 8 figuras a 300 DPI.

---

## 🌟 Guía Rápida: Puesta en Marcha en 1 Clic

Si eres el **elaborador de la tesis**, **asesor** o **revisor** y deseas interactuar con el sistema:

### 1. Panel de Control Maestro:
* **Lanzador Central**: Haz doble clic en **[`Iniciar_Sistema.bat`](Iniciar_Sistema.bat)**. Despliega un menú interactivo para abrir Telemetría 2.0, Telemetría 1.0, el Exportador de Gráficas, el Manual Químico, el Visor de Diagramas o las carpetas académicas.
* **Telemetría Directa (SCADA Activo)**: Haz doble clic en **[`Iniciar_Telemetria_2.0.bat`](Iniciar_Telemetria_2.0.bat)** para monitoreo en vivo inmediato (RTOS 2.0).
* **Lanzadores Individuales**: En la carpeta **[`herramientas/lanzadores/`](herramientas/lanzadores/)** dispones de accesos directos independientes para cada componente.

---

## ⚙️ Especificaciones Técnicas del Hardware Maestro (ESP32-S3 N16R8)

| Parámetro | Especificación | Configuración en Arduino IDE |
| :--- | :--- | :--- |
| **Microcontrolador** | ESP32-S3 Dual-Core Xtensa LX7 @ 240 MHz | `ESP32S3 Dev Module` |
| **Memoria Flash Externa** | 16 MB (128 Mbit) Quad/Octal SPI | `16MB (128Mb)` |
| **Memoria RAM / PSRAM** | 512 KB SRAM interna + 8 MB Octal-SPI PSRAM | `OPI PSRAM` |
| **Esquema de Partición** | 16 MB con ranuras duales de aplicación de 3.0 MB para OTA | `16M Flash (3MB APP/9.9MB FATFS)` |
| **Velocidad del Bus I2C** | 400 kHz (Fast Mode) en GPIO 8 (SDA) y GPIO 9 (SCL) | `Wire.setClock(400000)` |
| **Comunicaciones USB** | USB-C Nativo con CDC activo en arranque | `USB CDC On Boot: Enabled` |
| **Nodo de Potencia AC** | Arduino Nano (ATmega328P @ 16 MHz) vía UART2 (TX GPIO 17) | `9600 bps, 8N1` |

---

## 📁 Estructura del Repositorio

El repositorio se encuentra categorizado por dominios funcionales de ingeniería para facilitar la navegación y eliminar archivos sueltos:

```text
Proyecto/
├── Iniciar_Sistema.bat        <-- 🚀 PANEL MAESTRO: Menú interactivo para todos los módulos
├── Iniciar_Telemetria_2.0.bat <-- 🚀 EJECUTABLE DIRECTO: Doble clic para SCADA activo (RTOS 2.0)
├── README.md                  <-- 📘 Manual general y arquitectura del sistema (Versión 2.0)
├── AGENTS.md                  <-- 📜 Reglas de estilo y desarrollo
├── requirements.txt           <-- 📦 Dependencias de Python (requests, matplotlib, pandas, etc.)
│
├── firmware/                  <-- 🧠 CÓDIGO FUENTE DE MICROCONTROLADORES
│   ├── esp32/                 <-- Nodo Maestro ESP32-S3
│   │   ├── RTOS2.0/           <-- ⭐ FIRMWARE ACTIVO (Canal A1 dedicado ADS1115, FreeRTOS SMP)
│   │   └── historico/         <-- Archivo consolidado de versiones previas (RTOS 1.0-1.4 y Super-Loop)
│   └── arduino_nano/          <-- Nodo de Potencia (Dimmer AC 60Hz ATmega328P)
│       ├── nano/              <-- Firmware activo con Watchdog
│       └── historico/         <-- Prototipos previos (Nano Beta, nano2)
│
├── software/                  <-- 📊 APLICACIONES SCADA, TELEMETRÍA Y PROCESAMIENTO
│   ├── telemetria2.0/         <-- ⭐ SCADA ACTIVO (Matriz ISA-88, Culombimetría, Balanza analítica)
│   ├── telemetria/            <-- SCADA v1.0 (Versión base de referencia)
│   └── exportar_graficas_offline.py <-- Generador offline de 8 figuras científicas (300 DPI)
│
├── hardware/                  <-- 🔌 ELECTRÓNICA, ESQUEMAS Y MODELADO
│   ├── esquemas_y_bom/        <-- Lista de materiales (BOM.md), diagrama de bloques y sumidero VCSS
│   └── control_matlab/        <-- Modelado matemático en MATLAB (Control_termico.m y graficar_matlab.m)
│
├── documentos/                <-- 📚 DOCUMENTACIÓN TÉCNICA, QUÍMICA Y ACADÉMICA
│   ├── academicos/            <-- Tesis de licenciatura, Cartel, Protocolo VUGR y Plantilla SMEQ26
│   ├── manuales/              <-- Manual de operación química interactivo (HTML, PDF y Markdown)
│   ├── guias/                 <-- Guía de compilación Arduino IDE, Changelog y generador PDF
│   ├── datasheets/            <-- 15 hojas de datos oficiales de sensores y componentes
│   ├── imagenes/              <-- Figuras científicas HD y capturas del SCADA
│   └── instaladores/          <-- Scripts de instalación desatendida (Python y librerías Arduino)
│
├── visualizacion/             <-- 🌐 INTERFACES WEB Y DIAGRAMAS TÉCNICOS
│   ├── diagramas/             <-- Visor interactivo y diagramas de arquitectura del firmware
│   └── preview/               <-- Hub de previews y simuladores web de las pantallas del ESP32
│
└── herramientas/              <-- 🛠️ UTILIDADES Y SCRIPTS AUXILIARES
    ├── lanzadores/            <-- Accesos directos .bat individuales para cada componente
    └── scratch/               <-- Banco de pruebas y scripts de verificación experimental
```

---

## ⚖️ Flujo Asistido de Ensayo y Gravimetría (ISA-88)

El software SCADA [`telemetria2.0`](software/telemetria2.0/) (ejecutable directo **[`Iniciar_Telemetria_2.0.bat`](Iniciar_Telemetria_2.0.bat)**) incorpora un flujo automatizado para el registro experimental y el cálculo electroquímico:

1. **Selección de Receta**: Escoge la placa (1 a 32) según el filtro de condición deseado ($\text{pH } 2\text{ o } 4$, $25^\circ\text{C}\text{ o }40^\circ\text{C}$, $\text{DC o Pulsado}$).
2. **Registro de Peso Inicial**: Al presionar *"Iniciar Etapa"* en la Etapa 1 (Limpieza), un cuadro modal solicita el peso de la placa virgen en la balanza analítica ($P_{\text{ini}}$ con hasta 4 decimales, ej. `25.4321` g).
3. **Ejecución Automática de Etapas (Protocolo VUGR - Sustrato Al 6061-T6)**:
   - **Etapa 1 (Desengrase Alcalino)**: $240\text{ s @ } 85\text{--}90^\circ\text{C}$ ($0.00\text{ A}$, $\text{Na}_3\text{PO}_4 + \text{Na}_2\text{SiO}_4 + \text{PEG-400}$).
   - **Etapa 2 (Decapado Alcalino)**: $120\text{ s @ } 85\text{--}90^\circ\text{C}$ ($0.00\text{ A}$, $\text{Na}_3\text{PO}_4 \cdot 12\text{H}_2\text{O}\ 37.5\text{ g/L}$). Disolución controlada de alúmina sin ataque ácido agresivo.
   - **Etapa 3 (Zincado Celda Hull 267 mL)**: $120\text{ s / } 300\text{ s @ } 25^\circ\text{C} / 40^\circ\text{C}$ ($1.50\text{ A DC o Pulsado 10Hz/20\%}$, baño ácido $\text{ZnSO}_4$).
   - **Etapa 4 (Niquelado sobre Zinc)**: $600\text{ s (10 min) @ } 30\text{--}40^\circ\text{C}$ ($1.13\text{ A DC}$, $\text{NiSO}_4 + \text{Na}_2\text{SO}_4$). El $\text{Na}_2\text{SO}_4$ evita el desplazamiento galvánico espontáneo.
4. **Registro de Peso Final y Balanza**: Al concluir la Etapa 4, suena la alarma industrial y el sistema solicita el peso final ($P_{\text{fin}}$ en gramos).
5. **Cálculos y Reporte Inmediato**:
   - $\Delta m_{\text{real}} = P_{\text{fin}} - P_{\text{ini}}$ (mg y g)
   - $m_{\text{teo}} = \frac{Q_{\text{total}} \cdot M}{z \cdot F}$ (mg)
   - $\text{Eficiencia Faradaica: } \eta = \left(\frac{\Delta m_{\text{real}}}{m_{\text{teo}}}\right) \times 100\%$
   - $\text{Espesor Medio: } e = \frac{\Delta m_{\text{real}}}{\rho \cdot A} \times 10^4 \text{ (\mu m)}$
6. **Exportación de Figuras Científicas HD**: El sistema permite compilar de inmediato la suite de figuras científicas a 300 DPI dentro de la carpeta del ensayo.

---

## 📊 Paquete de Figuras Científicas a 300 DPI ([`exportar_graficas_offline.py`](software/exportar_graficas_offline.py))

Las figuras generadas automáticamente para la memoria de tesis abarcan:

| Figura | Archivo PNG | Descripción |
| :---: | :--- | :--- |
| **Fig. 1** | `01_perfil_electroquimico_termico.png` | Perfil térmico multizona (4 tinas) y respuesta dinámica de corriente galvánica real. |
| **Fig. 2** | `02_seguimiento_errores_control.png` | Errores instantáneos $e(t) = \text{SP} - \text{PV}$ con bandas de tolerancia $\pm 0.5^\circ\text{C}$ e índice IAE acumulado. |
| **Fig. 3** | `03_actuadores_triacs_potencia.png` | Esfuerzo de control %, ángulos de disparo $\alpha$ (°), retardos de gate ($\mu\text{s}$) y potencia activa RMS en Watts. |
| **Fig. 4** | `04_analisis_faraday_plano_fase.png` | Culombimetría de proceso $Q(t) = \int I dt$ con masa teórica/real y **Retrato de Fase** $\dot{e}(t)$ vs $e(t)$ con atractor de estabilidad. |
| **Fig. 5** | `05_diagnostico_integral_resumen.png` | **Dashboard Ejecutivo**: IAE global, balance energético (Wh / kWh consumidos por las resistencias), gravimetría y condiciones ambientales. |
| **Fig. 6** | `06_tiempos_muertos_gantt_fases.png` | Diagrama cronológico Gantt de ejecución de fases ISA-88 y tiempos muertos de transferencia. |
| **Fig. 7** | `07_forma_onda_pulsada_ets.png` | Reconstrucción estroboscópica ETS (Equivalent Time Sampling) de la onda de corriente pulsada a 100 Hz. |
| **Fig. 8** | `08_correlacion_espesor_densidad.png` | Distribución longitudinal de densidad de corriente $J(x)$ en Celda Hull y espesor local de zinc. |

---

## 🧪 Manual de Operación Química y Protocolo de Laboratorio

Para químicos, analistas y operadores de laboratorio, el proyecto incluye un **Manual Interactivo Standalone** en formato HTML con calculadora de masas de reactivos en tiempo real, capturas HD de la interfaz SCADA, metrología de Faraday y resolución de anomalías:

- **Lanzador directo**: Doble clic en **[`Iniciar_Sistema.bat`](Iniciar_Sistema.bat)** (Opción 4) o en **[`herramientas/lanzadores/Manual_de_Uso.bat`](herramientas/lanzadores/Manual_de_Uso.bat)**.
- **Archivo fuente**: [`documentos/manuales/MANUAL_DE_OPERACION_QUIMICA.html`](documentos/manuales/MANUAL_DE_OPERACION_QUIMICA.html) (compatible con cualquier navegador web sin requerir dependencias; exportable a PDF con `Ctrl+P`).
- **Versión de referencia técnica**: [`documentos/manuales/MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md`](documentos/manuales/MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md).

---

## 🛠️ Requisitos e Instalación

Para ejecutar la aplicación en cualquier PC con Windows 10/11:
1. Asegúrate de tener Python 3.9 o superior.
2. Abre una terminal en la carpeta del proyecto e instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta el monitor SCADA:
   ```bash
   cd software
   python -m telemetria2.0
   ```
   *(O simplemente haz doble clic en `Iniciar_Telemetria_2.0.bat` o en `Iniciar_Sistema.bat`).*


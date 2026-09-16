# 📊 Visor y Catálogo Modular de Diagramas Técnicos: Super-Loop (v4.0) y FreeRTOS (RTOS 2.0)

> **Proyecto**: *Sistema Automatizado de Electrodeposición y Galvanoplastia (ESP32-S3 / Arduino Nano / SCADA)*  
> **Ubicación**: Carpeta [`diagramas/`](./)  
> **Protocolo Experimental**: *Validación de Recubrimientos de Zinc-Níquel sobre Aluminio 6061-T6 (Protocolo VUGR / Memoria Técnica SMEQ26)*

---

## 🌟 Arquitectura Modular de Diagramas

Los diagramas están organizados en **dos suites independientes y completas**, eliminando scripts monolíticos mediante archivos fuente puros de Mermaid (`.mmd`) y catálogos de metadatos (`catalogo.json`):

1. **`diagramas/superloop/` (v4.0)**:
   - Colección completa de diagramas para la arquitectura basada en *Super-Loop* asíncrono, patrón MVC desacoplado, secciones críticas con spinlocks `portMUX_TYPE` y métricas dinámicas de error IAE/ISE.
2. **`diagramas/rtos/` (RTOS 2.0)**:
   - Colección completa para la arquitectura multitarea simétrica (**FreeRTOS SMP Dual-Core** en ESP32-S3 N16R8), separación de dominios entre Core 0 (Comunicaciones/Web) y Core 1 (Control determinista en tiempo real).
   - **Canal A1 Dedicado para pH (RTOS 2.0)**: Eliminación total del Canal A0, dedicación exclusiva del Canal A1 en el conversor ADS1115 con 100% de uso del bus I2C a 860 SPS sin retrasos de conmutación multiplexada.
   - **Calibración NVS por Modo**: Persistencia desacoplada de puntos de calibración por modo (Ácido, Neutro, Básico) y adaptación de offset de hardware con voltímetro y aguja única para el módulo PH-4502C.
   - **Controlador PI discreto VCSS con Anti-Windup**: Protección **Anti-Inrush (Soft-Start 500 ms + Blanking Time optimizado a 300 ms)**, **Muestreo Estroboscópico ETS de 16 puntos**, diagnóstico continuo de salud de celda (`SaludCelda_t`), cerrojos mutex semafóricos, alarma Fail-Safe Latch (ISA-18.2).
   - **SCADA Telemetría 2.0**: Pesaje asistido con balanza analítica (4 decimales), culombimetría faradaica $Q = \int I dt$ y balances electroquímicos según la Ley de Faraday.
   - **Terminología de Proceso Corregida (Protocolo VUGR)**: 
     - Tina 1: Desengrase Alcalino ($Na_3PO_4 + Na_2SiO_4 + \text{PEG}$ a $80\text{--}95^\circ\text{C}$).
     - Tina 2: Decapado Alcalino ($Na_3PO_4\ 37.5\text{ g/L}$ a $80\text{--}95^\circ\text{C}$ para remoción controlada de $Al_2O_3$).
     - Tina 3: Celda Hull - Zincado en Medio Ácido ($267\text{ mL}$, $ZnSO_4$, $25\text{--}40^\circ\text{C}$ + VCSS 0-3.5A).
     - Tina 4: Niquelado sobre Zinc ($NiSO_4 + Na_2SO_4$ a $\text{pH } 5.6\text{--}5.9$ y $20\text{--}40^\circ\text{C}$).

---

## 🚀 Formas de Uso Rápido (1 Clic)

### 1. Aplicación de Escritorio Python con Selector Dinámico
* Ejecuta **[`iniciar_visor_diagramas.bat`](iniciar_visor_diagramas.bat)** (o el lanzador raíz **[`Ver_Diagramas.bat`](../Ver_Diagramas.bat)**).
* **Selector en Vivo**: Permite alternar en cualquier momento entre **Super-Loop (v4.0)** y **FreeRTOS SMP (RTOS 2.0)** mediante el desplegable en la cabecera.
* **Funciones**:
  * 🪟 **Abrir Todos en Ventanas Separadas**: Despliega los 11 diagramas simultáneamente en ventanas flotantes para comparación multimonitor.
  * 🔍 **Zoom & Paneo Fluido**: Acercar/alejar con la rueda del ratón (`Scroll`), arrastrar con `Clic + Arrastre` y ajustar tamaño.
  * 💾 **Exportar Suite a HD**: Descarga y guarda todos los diagramas de la arquitectura activa en alta resolución (PNG y SVG).
  * 📄 **Ver Código Mermaid**: Inspecciona y copia directamente la sintaxis fuente `.mmd`.

### 2. Visor Web Interactivo (`index.html`)
* Abre **[`diagramas/index.html`](index.html)** en cualquier navegador.
* **Selector de Arquitectura**: Cambia al instante entre Super-Loop y FreeRTOS sin recargar la página.
* Renderizado dinámico en tiempo real con **Mermaid.js**, control vectorial con `svg-pan-zoom`, modo Claro/Oscuro y descarga directa de SVG/PNG.
* Funciona 100% offline (sin problemas de CORS local).

### 3. Comandos de Consola / CLI:
```bash
# Exportar diagramas de la suite RTOS 2.0 a PNG y SVG
python diagramas/visor_diagramas.py --suite rtos --exportar

# Exportar diagramas de la suite Super-Loop v4.0 a PNG y SVG
python diagramas/visor_diagramas.py --suite superloop --exportar

# Exportar ambas suites completas (22 diagramas en total)
python diagramas/visor_diagramas.py --exportar-todo

# Sincronizar catálogo para el visor web (catalogos_data.js)
python diagramas/visor_diagramas.py --sync-web
```

---

## 📁 Estructura del Módulo de Diagramas

```text
diagramas/
├── superloop/                         # 🔬 SUITE VERSIÓN 4.0 (SUPER-LOOP)
│   ├── fuentes/                      # Archivos fuente individuales Mermaid (.mmd)
│   │   ├── 01_arquitectura_general.mmd
│   │   ├── 02_topologia_buses_datos.mmd
│   │   ├── 03_concurrencia_superloop.mmd
│   │   ├── 04_interlocks_estados.mmd
│   │   ├── 05_control_termico_pi.mmd
│   │   ├── 06_sumidero_corriente_vcss.mmd
│   │   ├── 07_secuencia_zcs_rele.mmd
│   │   ├── 08_filtro_ph_tri_modo.mmd
│   │   ├── 09_control_triacs_ac60hz.mmd
│   │   ├── 10_arquitectura_mvc_web.mmd
│   │   └── 11_supervision_scada_isa88.mmd
│   ├── catalogo.json                 # Metadatos estructurados (título, categoría, badge, desc)
│   └── imagenes/                     # PNG (HD) y vectores SVG para v4.0
│
├── rtos/                              # ⚡ SUITE RTOS 2.0 (ESP32-S3 N16R8 SMP)
│   ├── fuentes/                      # Archivos fuente individuales Mermaid (.mmd)
│   │   ├── 01_arquitectura_general.mmd
│   │   ├── 02_topologia_buses_datos.mmd
│   │   ├── 03_concurrencia_free_rtos.mmd
│   │   ├── 04_interlocks_estados.mmd
│   │   ├── 05_control_termico_pi.mmd
│   │   ├── 06_sumidero_corriente_vcss.mmd
│   │   ├── 07_secuencia_zcs_rele.mmd
│   │   ├── 08_filtro_ph_tri_modo.mmd
│   │   ├── 09_control_triacs_ac60hz.mmd
│   │   ├── 10_arquitectura_mvc_web.mmd
│   │   └── 11_supervision_scada_isa88.mmd
│   ├── catalogo.json                 # Metadatos estructurados (título, categoría, badge, desc)
│   └── imagenes/                     # PNG (HD) y vectores SVG para RTOS 2.0
│
├── visor_diagramas.py                 # 🖥️ Motor visual Python modular con selector bi-suite
├── index.html                         # 🌐 Visor Web modular con selector en tiempo real
├── catalogos_data.js                  # 📦 Sincronización offline de datos para el visor web
├── iniciar_visor_diagramas.bat        # 🚀 Lanzador de escritorio
├── exportar_imagenes.bat              # 💾 Lanzador de exportación masiva
└── README.md                          # 📘 Este documento
```

---

## 📋 Catálogo Comparativo de Diagramas

| # | Archivo | Suite Super-Loop (v4.0) | Suite FreeRTOS (RTOS 2.0) |
| :-: | :--- | :--- | :--- |
| **01** | `01_arquitectura_general` | Master-Slave Super-Loop asíncrono + FPU 32-bit | Dual-Core SMP, Core 0 (Web/Red) vs Core 1 (Control Real-Time), Sensor pH A1 Dedicado, Soft-Start, ETS y balanza 4 decimales en Telemetría 2.0 |
| **02** | `02_topologia_buses_datos` | ESP32-S3 estándar, I2C 400kHz, SPI, UART | ESP32-S3 N16R8 (16MB Flash, 8MB PSRAM OPI), Riel calibrado 3.53V / 7.06A, Neopixel GPIO 48, relé ZCS, Canal A1 dedicado para pH |
| **03** | `03_concurrencia_*` | Concurrencia con spinlocks `portMUX_TYPE` | 5 tareas SMP con prioridades, mutexes semafóricos, Heartbeats Watchdog (5000ms), variables de salud |
| **04** | `04_interlocks_estados` | Exclusión mutua química (HTTP 409) y modo OTA | Exclusión mutua química + Alarma **Fail-Safe Latch** (ISA-18.2) + Subestados VCSS (RAMP/BLANKING/LOCKED) |
| **05** | `05_control_termico_pi` | Control PI 1 Hz + Rampa Soft-Start 5 Hz | Control PI 1 Hz + Rampa Soft-Start 5 Hz (4 reactores químicos con sintonización analítica) |
| **06** | `06_sumidero_corriente_vcss`| Lazo analógico VCSS + Outer loop digital 2 Hz | **Lazo PI Discreto Anti-Windup (2 Hz)** + Anti-Inrush (Soft-Start 500ms + Blanking 300ms) + Diagnóstico Celda |
| **07** | `07_secuencia_zcs_rele` | Conmutación ZCS clásica (80/30 ms) | Conmutación ZCS + Rampa Soft-Start (500 ms) + Asentamiento Blanking Time (300 ms) |
| **08** | `08_filtro_ph_tri_modo` | TDM 25 Hz, Mediana-3, Calibración 3 modos | **Canal A1 Dedicado ADS1115 @ 860 SPS** (A0 eliminado), Offset analógico calibrado, Flash NVS por modo, Filtro Adaptativo |
| **09** | `09_control_triacs_ac60hz` | Cruce por cero INT1 (~8 µs), LUT 101 pts, Watchdog | Cruce por cero INT1 (~8 µs), LUT 101 pts, Watchdog UART (3.0 s) |
| **10** | `10_arquitectura_mvc_web` | Patrón MVC en Flash PROGMEM | Patrón MVC en Core 0, `/data_all` integral con shunts y salud, endpoints `/modo_f`, `/set_comp_f`, calibración pH A1 |
| **11** | `11_supervision_scada_isa88`| Gestor ISA-88 Taguchi, SCADA multihilo, IAE/ISE | Protocolo VUGR: Taguchi 32 placas, Telemetría 2.0, balanza analítica asistida y culombimetría faradaica |

# 🗺️ Mapa Maestro del Proyecto: E.L.E.C.T.R.O.D.O-32
### Guía de Arquitectura, Navegación y Fuentes de Verdad

Este documento sirve como el **índice central de ingeniería** para el ecosistema **E.L.E.C.T.R.O.D.O-32** (*Equipo de Laboratorio para Experimentación y Control en Tiempo Real con Obtención de Datos Operativos*).

---

## 🧭 1. Resumen de Ubicación de Recursos

| Subsistema / Recurso | Ruta en Disco | Propósito Principal | Documento Clave |
| :--- | :--- | :--- | :--- |
| **Repositorio Base (Producción)** | [`ELECTRODO_32/`](README.md) | Versión estable RTOS 2.0 (ESP32-S3 + Nano + SCADA PC Windows). | [README.md](README.md) |
| **Repositorio Edge (Next-Gen)** | [`ELECTRODO_32_Uno/`](../ELECTRODO_32_Uno/README.md) | Versión Edge Computing (Arduino UNO Q - MPU Linux + MCU STM32U585). | [PROYECTO_UNO_BLUEPRINT.md](../ELECTRODO_32_Uno/PROYECTO_UNO_BLUEPRINT.md) |
| **PCB Placa Madre (Rev 5.0)** | [`hardware/pcb/placa_madre_esp32s3_uno/`](hardware/pcb/placa_madre_esp32s3_uno/) | Diseño KiCad, Gerbers JLCPCB, BOM y 3D STEP de la tarjeta madre. | [README Técnico](hardware/pcb/placa_madre_esp32s3_uno/README.md) |
| **PCB Carrier Shield (Rev 5.1)** | [`ELECTRODO_32_Uno/hardware/pcb/carrier_shield_uno_q/`](../ELECTRODO_32_Uno/hardware/pcb/carrier_shield_uno_q/) | Shield industrial 4 capas para acoplamiento de sensores con Uno Q. | [README Shield](../ELECTRODO_32_Uno/hardware/pcb/carrier_shield_uno_q/README.md) |
| **Eventos: Innovafest 2026** | [`eventos/innovafest/`](eventos/innovafest/) | Expediente de postulación, video pitch 3 min, ficha técnica y fotos. | [README Innovafest](eventos/innovafest/README.md) |
| **Eventos: SMEQ 2026** | [`eventos/smeq_2026/`](eventos/smeq_2026/) | Cartel científico **Folio CTS-C51**, memoria in extenso y hoja QR. | [README SMEQ](eventos/smeq_2026/README.md) |
| **SCADA Telemetría 2.0** | [`software/telemetria2.0/`](software/telemetria2.0/) | Aplicación de monitoreo en tiempo real, culombimetría y recetas ISA-88. | [constantes_sistema.json](software/telemetria2.0/utilidades/constantes_sistema.json) |
| **Firmware ESP32-S3** | [`firmware/esp32/RTOS2.0/`](firmware/esp32/RTOS2.0/) | Control en tiempo real (Core 1) y servidor HTTP/JSON SoftAP (Core 0). | [RTOS2.0.ino](firmware/esp32/RTOS2.0/RTOS2.0.ino) |
| **Firmware Arduino Nano2** | [`firmware/arduino_nano/nano2/`](firmware/arduino_nano/nano2/) | Disparo determinista de 4 TRIACs por tiempo proporcional (3000 ms). | [nano2.ino](firmware/arduino_nano/nano2/nano2.ino) |
| **Manual de Operación Química** | [`documentos/manuales/`](documentos/manuales/) | Protocolos de preparación de soluciones, seguridad química y Celda Hull. | [MANUAL_DE_OPERACION.md](documentos/manuales/MANUAL_DE_OPERACION_QUIMICA_Y_LABORATORIO.md) |
| **Showcase Web (GitHub Pages)** | [`docs/`](docs/) | Aplicación web pública con simulador interactivo y dashboard móvil. | [index.html](docs/index.html) |
| **Suite de Pruebas (pytest)** | [`tests/`](tests/) | 62 pruebas de metrología, interlocks, JSON y validación web (95% cov). | [pytest.ini](pytest.ini) |

---

## ⚡ 2. Matriz Cruzada de Hardware y PCBs

```
C:\Proyecto\
├── ELECTRODO_32\hardware\pcb\placa_madre_esp32s3_uno\
│   ├── placa_madre_esp32s3_uno.kicad_pcb        <- Diseño de pistas KiCad (2 capas, 100x100mm)
│   ├── placa_madre_esp32s3_uno.kicad_sch        <- Esquemático con desacoplamiento ZCS y optos
│   ├── placa_madre_esp32s3_uno_sch.pdf          <- Diagrama esquemático imprimible en alta definición
│   ├── placa_madre_esp32s3_uno_3d.step          <- Modelo 3D universal para ensamble mecánico
│   ├── GERBERS_PLACA_MADRE_ESP32S3_UNO_REV5.zip <- Paquete de manufactura para JLCPCB
│   ├── BOM_JLCPCB_ESP32S3_UNO_REV5.csv          <- Lista de componentes y números de parte LCSC
│   ├── CPL_JLCPCB_ESP32S3_UNO_REV5.csv          <- Archivo Pick and Place (coordenadas SMD)
│   └── renders/                                 <- Renders fotorrealistas isométricos y topológicos
│
└── ELECTRODO_32_Uno\hardware\pcb\carrier_shield_uno_q\
    ├── carrier_shield_uno_q.kicad_pcb           <- Circuito impreso apilable para Uno Q (4 capas)
    ├── carrier_shield_uno_q.kicad_sch           <- Esquemático con acondicionamiento BNC y TVS
    ├── carrier_shield_uno_q_sch.pdf             <- Esquemático completo en PDF
    ├── carrier_shield_uno_q_3d.step             <- Modelo 3D STEP del shield
    ├── GERBERS_CARRIER_SHIELD_UNO_Q_REV5.zip    <- Gerbers listos para ensamble industrial
    ├── BOM_JLCPCB_CARRIER_SHIELD_UNO_Q_REV5.csv <- Lista de materiales
    └── CPL_JLCPCB_CARRIER_SHIELD_UNO_Q_REV5.csv <- Coordenadas CPL
```

---

## 🏆 3. Matriz de Eventos y Divulgación Científica

```
ELECTRODO_32\eventos\
├── innovafest\
│   ├── documentos_oficiales/
│   │   ├── 01_DOCUMENTO_OFICIAL_POSTULACION.pdf   <- Memoria técnica de registro en el concurso
│   │   ├── Ficha_Innovafest_2026_ELECTRODO32.pdf  <- Ficha infográfica ejecutiva de producto
│   │   └── 03_RESPUESTAS_FORMULARIO_WEB.md        <- Argumentación técnica ante comités evaluadores
│   ├── pitch_y_presentaciones/
│   │   ├── pitch_innovafest_3min.mp4              <- Video oficial de pitch de 3 minutos
│   │   └── video_raw.mp4                          <- Tomas de laboratorio de la planta en operación
│   └── galeria/
│       ├── 01_montaje_celdas/                     <- Bancada física y corte de tinas de acrílico
│       ├── 02_pruebas_quimicas/                   <- Soluciones electroquímicas y celda trapezoidal
│       ├── 03_prototipo_final/                    <- Integración final de electrónica y sensores
│       ├── 04_sesion_pitch/                       <- Equipo de trabajo y demostraciones en vivo
│       └── whatsapp/                              <- Registro fotográfico continuo del proceso
│
└── smeq_2026\
    ├── cartel_cientifico/
    │   ├── Cartel PModular 044.pptx.pdf           <- Cartel en formato oficial para exposición
    │   ├── cartel_con_qr_preview.png              <- Render de alta resolución con código QR incrustado
    │   └── HOJA_QR_MESA_SMEQ2026.pdf              <- Hoja de mesa interactiva para los asistentes
    └── documentos_oficiales/
        ├── PLANTILLA-Memoria-extenso-SMEQ26.docx  <- Artículo de investigación en extenso
        ├── ReporteFinal_044.pdf                   <- Resultados analíticos de recubrimiento Zn/Ni
        └── Protocolo_VUGR.pdf                     <- Protocolo de laboratorio y seguridad química
```

---

## 🚀 4. Guía Rápida de Lanzadores y Comandos

| Acción | Método de Ejecución |
| :--- | :--- |
| **Panel Maestro Unificado** | Doble clic en [`Iniciar_Sistema.bat`](Iniciar_Sistema.bat) o `python launcher.py` |
| **SCADA Telemetría 2.0 Directo** | Doble clic en [`Iniciar_Telemetria_2.0.bat`](Iniciar_Telemetria_2.0.bat) |
| **Ejecutar Suite de Pruebas (62 tests)** | `python -m pytest -v` (en la raíz de `ELECTRODO_32`) |
| **Pruebas de Validación Cruzada Uno Q** | `python -m pytest -v` (en la raíz de `ELECTRODO_32_Uno`) |
| **Exportar Figuras a 300 DPI** | `python software/exportar_graficas_offline.py` |
| **Sincronizar GitHub Pages** | Doble clic en [`actualizar_y_subir_web.bat`](actualizar_y_subir_web.bat) |

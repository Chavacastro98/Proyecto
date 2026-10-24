# ⚙️ Subsistema de Hardware: E.L.E.C.T.R.O.D.O-32
### Instrumentación, Circuitos Impresos (PCB) y Control Eléctrico de Potencia

Este directorio contiene todo el diseño eléctrico, de circuitos impresos y modelos de control físico para la planta piloto de electrodeposición **E.L.E.C.T.R.O.D.O-32**.

---

## 📂 Organización del Directorio

```
hardware/
├── pcb/
│   └── placa_madre_esp32s3_uno/   <- Circuito impreso maestro Rev 5.0 (KiCad, Gerbers JLCPCB, BOM, CPL, 3D STEP)
├── esquemas_electricos/           <- Diagramas de alambrado industrial, conexionado de red AC 127V y Celda Hull
└── control_matlab/                <- Modelos matemáticos de transferencia de calor y sintonización de la planta
```

---

## 🔗 Enlaces Rápidos

* **[Documentación Técnica de la Placa Madre Rev 5.0](pcb/placa_madre_esp32s3_uno/README.md)**
* **[Diagramas Eléctricos y Lista de Materiales (BOM)](esquemas_electricos/BOM.md)**
* **[Simulaciones y Modelos de Control](control_matlab/)**

*Para la versión basada en Arduino UNO Q, consulta [ELECTRODO_32_Uno/hardware/pcb/](../../Proyecto_Uno/hardware/pcb/carrier_shield_uno_q).*

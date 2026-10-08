# 📋 Instrucciones de Operación del Showcase Técnico (CTS-C51 | SMEQ 2026)

**Para:** Fernando Salvador Samayoa Martínez & Equipo de Instrumentación  
**Proyecto:** Sistema de Control In-Operando, Automatización y Monitoreo Térmico/Electroquímico (Celda Hull & Reactor VUGR)  
**Congreso:** XLI Congreso Nacional de la Sociedad Mexicana de Electroquímica (SMEQ 2026)

---

## 🚀 1. Cómo Iniciar el Servidor Local (1 Clic)

Todo el showcase está **100% autocontenido** en esta carpeta. Para iniciarlo:

1. Da **doble clic** en el archivo:
   ```text
   iniciar_servidor.bat
   ```
2. Se abrirá una ventana de terminal negra y ocurrirá lo siguiente de forma automática:
   - Detecta la dirección IP de tu computadora en la red Wi-Fi local (ejemplo: `192.168.100.43`).
   - Genera el código QR en la imagen `qr_acceso_movil.png`.
   - **Imprime el código QR directamente en la consola** para escanearlo al instante.
   - Abre tu navegador predeterminado en la computadora en `http://localhost:8000/index.html`.

---

## 📱 2. Cómo Conectar el Samsung Galaxy (o cualquier smartphone)

1. Asegúrate de que tu **Samsung Galaxy** y la **laptop/PC** estén conectados a la **misma red Wi-Fi**.
2. Abre la cámara de tu Samsung Galaxy y apunta al código QR que aparece en la terminal (o abre el archivo de imagen `qr_acceso_movil.png`).
3. Toca la notificación del enlace web que aparece en la pantalla del teléfono (`http://<TU_IP>:8000/index.html`).
4. ¡Listo! La web cargará instantáneamente en el navegador móvil con diseño responsivo, pestañas táctiles con desplazamiento fluido y simuladores interactivos.

---

## 🌐 3. ¿Qué hacer si en el laboratorio o auditorio NO hay Wi-Fi?

Si no tienen una red Wi-Fi disponible en el lugar de la presentación:

1. En tu **Samsung Galaxy**, activa la opción **Zona Móvil / Punto de Acceso Wi-Fi (Hotspot)**.
2. Conecta la laptop a la red Wi-Fi creada por tu teléfono.
3. Ejecuta `iniciar_servidor.bat`.
4. El script detectará la IP de la laptop en la red del teléfono y creará el código QR exacto. Al escanearlo, navegarás a toda velocidad sin gastar tus datos móviles (la comunicación es local directa por Wi-Fi).

---

## 💻 4. Uso Local Directo sin Servidor (Modo Standalone)

Si solo quieres abrir el showcase en una laptop o PC para proyectar en cañón:
- Simplemente da **doble clic en `index.html`**.
- Se abre en Google Chrome, Microsoft Edge, Firefox, etc., cargando todos los estilos y scripts locales de inmediato.

---

## 📁 5. Estructura Modular de Archivos

El proyecto ha sido **modularizado** para máxima velocidad de renderizado, caché y facilidad de edición:

```text
showcase_web/
│
├── index.html                  <-- Estructura semántica pura (HTML5, 1,139 líneas)
├── iniciar_servidor.bat        <-- Lanzador rápido de 1 clic para Windows
├── servidor_showcase.py        <-- Script servidor Python + detección IP + generador QR
├── qr_acceso_movil.png         <-- Imagen generada del QR para imprimir o proyectar
├── INSTRUCCIONES_FERNANDO.md   <-- Este manual de operación
│
├── css/                        <-- Estilos modulares optimizados
│   ├── variables.css           <-- Tokens de color, dark mode, fuentes tipográficas
│   ├── layout.css              <-- Header, pestañas táctiles móviles, contenedor, footer
│   └── components.css          <-- Tarjetas, tablas, fórmulas, sliders táctiles, modal HD
│
├── js/                         <-- Lógica matemática y simuladores interactivos
│   ├── app.js                  <-- Controlador de pestañas, lightbox modal y ciclo de vida
│   ├── simuladores.js          <-- Ley de Faraday, sumidero VCSS (SOA) y conmutación ZCS TRIACs
│   └── calibracion_ph.js       <-- Modelo de 3 puntos Nernst con doble pendiente asimétrica
│
└── assets/                     <-- Fotografías de alta resolución de las placas físicas
    ├── sistema.png             <-- Diagrama de bloques de arquitectura de hardware
    ├── planta_placa_principal.jpg  <-- Foto limpia del microcontrolador ESP32-S3 y Nano
    ├── planta_modulo_triacs.jpg    <-- Foto limpia de la etapa de potencia TRIACs
    ├── planta_conexion_triacs.jpg  <-- Foto limpia del conexionado AC
    ├── planta_buses_termopares.jpg <-- Foto macro de los módulos MAX6675 SPI
    ├── planta_vcss_potencia.jpg    <-- Foto limpia del sumidero lineal VCSS (Shunts 10W)
    ├── planta_bus_adc.jpg          <-- Foto macro del ADC ADS1115 con filtros pasabajas RC
    ├── planta_sockets_zcs_ph.jpg   <-- Foto limpia de cabezales ZCS y AGND Kelvin
    ├── circuito_vcss.png           <-- Esquemático de simulación Proteus del sumidero
    ├── onda_zcs_tiempo_proporcional.jpg <-- Oscilogramas de modulación térmica
    ├── metrologia_pulsado_10hz.jpg      <-- Gráficas de calibración estroboscópica ETS
    ├── estados_isa88.jpg           <-- Diagrama de estados de control industrial
    ├── scada_01_principal.jpg      <-- Capturas del SCADA PyQt6
    └── web_01_hub.jpg ...          <-- Capturas de la interfaz web embebida ESP32
```

---

## 🛠️ 6. Créditos y Responsables de Planta

- **Víctor Ulises Gutiérrez Ramírez:** Tesista / Autor de Metodología y Ensayos DOE (`victor.gutierrez7221@alumnos.udg.mx` | 📞 3321905415)
- **Salvador Castro Pérez:** Instrumentación, Hardware, Firmware y Control Térmico (`salvador.castro7435@alumnos.udg.mx`)
- **Fernando Salvador Samayoa Martínez:** Instrumentación, Firmware y SCADA (`fernando.samayoa0621@alumnos.udg.mx` | Alt: `fsamayoamarinez@gmail.com` | 📞 3311534114)
- **Dr. Omar Alejandro González Meza & Dr. Norberto Casillas Santana:** Directores de Tesis (Electroquímica UdeG)

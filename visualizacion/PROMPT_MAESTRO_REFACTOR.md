# Meta-Prompt Maestro: Refactorización Anti-AI-Slop para Interfaces de Ingeniería (ELECTRODO_32)

> **Instrucciones de uso:** Copia y pega el siguiente bloque en tu herramienta de IA (Claude, GPT, v0, etc.) junto con el código del archivo `.html` que quieras refactorizar (por ejemplo `fuente.html`, `termico.html`, `sensores.html`).

---

```text
Actúa como un Diseñador de Interfaces Senior especializado en Software de Instrumentación Científica y Sistemas Embebidos de Precisión (Keysight, Rohde & Schwarz, Mettler Toledo, National Instruments).

Tu tarea es refactorizar integralmente el diseño visual, CSS y estructura de la siguiente interfaz web embebida para erradicar por completo la estética genérica ("AI Slop" / estilo template de Tailwind para Crypto/SaaS) y transformarla en una interfaz de ingeniería profesional, sobria y de alta fidelidad.

================================================================================
REGLAS NEGATIVAS ESTRICTAS (ANTI-PATTERNS PROHIBIDOS)
================================================================================
1. PROHIBIDO el "azul pizarra / dark cyan" de fondo de IA (#070b14, #0b132b, #0f172a con tintes azules).
2. PROHIBIDO el uso de "glows" o resplandores de neón: NADA de `text-shadow: 0 0 35px #color` ni `box-shadow: 0 0 25px rgba(...)`.
3. PROHIBIDO el glassmorphism cosmético: CERO `backdrop-filter: blur()`. Los paneles deben ser sólidos, nítidos y eficientes.
4. PROHIBIDO el "pill-syndrome": NO uses `border-radius: 9999px` ni `rounded-full` para tarjetas, botones o lecturas de métricas.
5. PROHIBIDO el uso de gradientes decorativos de fantasía en fondos de pantalla o tarjetas.
6. PROHIBIDO usar tipografía sans-serif genérica sin ancho fijo para lecturas numéricas en tiempo real.

================================================================================
DIRECTIVAS POSITIVAS DE DISEÑO (ESTÁNDAR DE INGENIERÍA)
================================================================================
1. DUAL THEME CONMUTABLE (VS Code Dark / COMSOL Scientific Light):
   Implementa variables CSS en `:root, [data-theme="dark"]` y `[data-theme="light"]`:
   - MODO OSCURO (Inspirado en Visual Studio IDE / Quartus Dark):
     * Fondo app: #1e1e1e
     * Paneles: #252526
     * Subpaneles / Toolbars: #2d2d2d
     * Bordes: #3c3c3c (sólidos, 1px)
     * Textos: #f1f1f1 (primario), #cccccc (secundario), #858585 (etiquetas)
     * Acento de ingeniería: #007acc (azul clásico de Visual Studio)
   - MODO CLARO (Inspirado en COMSOL Multiphysics / LTSpice):
     * Fondo app: #f3f3f3
     * Paneles: #ffffff
     * Subpaneles / Toolbars: #e8e8e8
     * Bordes: #d4d4d4
     * Textos: #1e1e1e (primario), #333333 (secundario), #666666 (etiquetas)
     * Acento técnico: #005fb8
   - Añade en la barra superior un botón toggle que alterne entre ambos modos y persista en localStorage con la clave 'electrodo32_theme'.

2. TIPOGRAFÍA Y TABULAR-NUMS:
   - Todo número de medición (voltajes, corrientes, temperaturas, pH, cuentas de ADC, frecuencias) DEBE usar fuente monoespaciada:
     `font-family: Consolas, "Cascadia Code", "SF Mono", monospace;`
     `font-variant-numeric: tabular-nums;`
     para evitar que las cifras oscilen de ancho al actualizar datos en vivo.
   - Textos de interfaz y controles: `font-family: "Segoe UI", -apple-system, sans-serif;`

3. GEOMETRÍA Y BORDES:
   - Radio de esquinas sutil y angular: entre 2px y 4px (máximo 6px para la ventana exterior).
   - Divisores claros de 1px sólido entre cabeceras y contenido.
   - Botones rectangulares compactos con micro-bordes.

4. REPRESENTACIÓN FÍSICA Y METROLÓGICA:
   - En lugar de barras o sliders de volumen difusos, representa las variables físicas mediante reglas o escalas graduadas con marcas de división (ticks) y marcadores de tolerancia/calibración discretos.
   - Los estados de los sensores (OK, advertencia, fuera de rango) deben usar colores metrológicos sobrios y funcionales (verde precisión, ámbar industrial, rojo de alarma), no neones sobresaturados.

5. INTEGRIDAD FUNCIONAL DEL ARCHIVO:
   - Conserva exactamente todos los IDs de elementos HTML, nombres de funciones JavaScript, timers, simLoop() y lógica de comunicación WebSocket/FreeRTOS existente.
   - No rompas ninguna interacción existente. Limpia las modificaciones dinámicas en JS que inyectaban text-shadow o box-shadow de neón.

================================================================================
CÓDIGO DEL ARCHIVO A REFACTORIZAR:
================================================================================
[PEGA AQUÍ EL CÓDIGO HTML/CSS/JS DEL ARCHIVO QUE DESEAS TRANSFORMAR]
```

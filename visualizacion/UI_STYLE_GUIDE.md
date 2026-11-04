# Guía de Estilo y Diseño de Interfaces: ELECTRODO_32
**Estándar de Instrumentación y Software de Ingeniería (Anti-AI-Slop)**

---

## 1. Manifiesto: Erradicación del "AI Slop" Visual

Las herramientas de generación de interfaces por IA convergen sistemáticamente en un mismo patrón predecible: fondos azul pizarra oscuro (`#0b132b`, `#0f172a`), acentos de cian neón (`#38bdf8`), efectos excesivos de vidrio (`backdrop-filter: blur`), resplandores difusos (`box-shadow: 0 0 25px`) y botones con forma de cápsula (`border-radius: 9999px`). Este estilo pertenece al marketing de criptomonedas o dashboards SaaS genéricos, no a herramientas de instrumentación científica ni a sistemas embebidos en tiempo real (FreeRTOS).

El proyecto **ELECTRODO_32** adopta una identidad visual basada en **software de ingeniería y metrología real**:
- **Modo Oscuro**: Inspirado en el entorno de desarrollo y telemetría de **Visual Studio IDE / Quartus Dark**.
- **Modo Claro**: Inspirado en software de simulación física y diseño científico como **COMSOL Multiphysics / LTSpice / Multisim**.
- **Métricas**: Tipografía monoespaciada con ancho fijo (`tabular-nums`) para evitar oscilaciones en pantalla al adquirir lecturas del ADS1115.
- **Geometría**: Bordes nítidos de 1px a 2px, radios angulares sobrios (2px a 4px), y cero sombras difusas o desenfoques artificiales.

---

## 2. Paleta Cromática y Variables CSS

La suite utiliza variables CSS nativas vinculadas al atributo `data-theme` en la raíz `<html>`:

```css
:root, [data-theme="dark"] {
    /* Paleta Base Visual Studio Dark */
    --ui-bg: #1e1e1e;              /* Fondo de aplicación principal */
    --ui-panel: #252526;           /* Contenedor de tarjeta/panel */
    --ui-subpanel: #2d2d2d;        /* Cabeceras internas y subpaneles */
    --ui-border: #3c3c3c;         /* Bordes de división precisos (1px) */
    --ui-border-subtle: #2f2f2f;  /* Divisores internos secundarios */
    
    /* Tipografía y Textos */
    --text-primary: #f1f1f1;       /* Lecturas numéricas y títulos */
    --text-secondary: #cccccc;     /* Texto regular y valores de campo */
    --text-muted: #858585;         /* Etiquetas, unidades y pie de página */
    --text-disabled: #555555;      /* Canales o estados inactivos */

    /* Acentos de Ingeniería */
    --accent-primary: #007acc;     /* Azul clásico de Visual Studio */
    --accent-hover: #1f8ad2;       /* Hover en controles */
    --accent-active: #0e639c;      /* Seleccionado / Prensado */

    /* Metrología y Estados Funcionales (Desaturados, sin neón) */
    --metro-ok: #4ec9b0;           /* Verde de calibración / neutralidad */
    --metro-warn: #d7ba7d;         /* Ámbar de advertencia / ajuste */
    --metro-err: #f14c4c;          /* Rojo de error / ácido fuerte */
    --metro-basic: #569cd6;        /* Azul de pH alcalino / básico */
    
    /* Display de Instrumento */
    --disp-bg: #181818;            /* Fondo de pantalla de medición */
    --disp-border: #333333;        /* Marco de instrumento */
    --disp-val: #ffffff;           /* Valor numérico principal */
}

[data-theme="light"] {
    /* Paleta Base COMSOL Multiphysics / LTSpice */
    --ui-bg: #f3f3f3;              /* Fondo gris laboratorio estándar */
    --ui-panel: #ffffff;           /* Paneles técnicos blancos */
    --ui-subpanel: #e8e8e8;        /* Cabeceras de paneles y toolbars */
    --ui-border: #d4d4d4;         /* Bordes de división definidos */
    --ui-border-subtle: #e1e4e8;  /* Divisores sutiles */

    /* Tipografía y Textos */
    --text-primary: #1e1e1e;       /* Títulos y lecturas principales */
    --text-secondary: #333333;     /* Texto de control */
    --text-muted: #666666;         /* Etiquetas metrológicas y unidades */
    --text-disabled: #a0a0a0;

    /* Acentos de Ingeniería */
    --accent-primary: #005fb8;     /* Azul técnico COMSOL / Windows CAD */
    --accent-hover: #106ebe;
    --accent-active: #004578;

    /* Metrología y Estados Funcionales */
    --metro-ok: #2e7d32;           /* Verde de precisión */
    --metro-warn: #b45309;         /* Ámbar industrial */
    --metro-err: #c62828;          /* Rojo de alarma / zona ácida */
    --metro-basic: #1565c0;        /* Azul químico básico */

    /* Display de Instrumento */
    --disp-bg: #f9f9fb;            /* Caja de display LCD técnico */
    --disp-border: #b8b8b8;        /* Marco metálico/plástico biselado */
    --disp-val: #111111;
}
```

---

## 3. Tipografía y Representación Numérica

1. **Lecturas de Instrumentación (pH, voltajes ADC, SPS, coeficientes NVS)**:
   - Familia: `Consolas, "Cascadia Code", "SF Mono", "Fira Code", monospace`.
   - Propiedad obligatoria: `font-variant-numeric: tabular-nums;`.
   - Justificación: Las cifras (0-9) deben compartir exactamente el mismo ancho. Esto evita que los números oscilen horizontalmente al recibir telemetría continua del microcontrolador.
2. **Textos de Interfaz (Etiquetas, Botones, Menús)**:
   - Familia: `"Segoe UI", -apple-system, BlinkMacSystemFont, Arial, sans-serif`.
   - Peso: `600` para títulos de panel, `700` para botones y acentos de control.

---

## 4. Reglas Geométricas (Anti-Slop Constraints)

| Componente | ❌ Prohibido (AI Slop) | ✅ Permitido (Ingeniería ELECTRODO_32) |
| :--- | :--- | :--- |
| **Bordes redondeados** | `border-radius: 9999px` o `24px` | `border-radius: 2px` a `4px` (máximo `6px` para la ventana exterior) |
| **Sombras y Luces** | `box-shadow: 0 0 25px #00f` (glows) | `box-shadow: none` o `box-shadow: 0 1px 3px rgba(0,0,0,0.15)` |
| **Fondos translúcidos** | `backdrop-filter: blur(20px)` | Fondos sólidos (`var(--ui-panel)`, `var(--disp-bg)`) |
| **Bordes** | `border: 1px solid rgba(255,255,255,0.08)` | `border: 1px solid var(--ui-border)` sólido y definido |
| **Escala de pH** | Slider de volumen difuso o barra arcoíris con cursor flotante de neón | Regla graduada con marcas de división (ticks) y marcadores para Buffers 4.01, 7.00 y 10.01 |
| **Badges de estado** | Cápsulas infladas semi-transparentes | Etiquetas rectangulares compactas con borde de 1px (`padding: 2px 6px; border-radius: 3px`) |

---

## 5. Componente: Regla Graduada Metrológica (0 - 14 pH)

En lugar de un slider genérico, la representación del pH se realiza mediante una escala con divisiones metrológicas:

```html
<div class="metro-scale-wrap">
    <!-- Puntos de referencia de buffer -->
    <div class="scale-buffer-marks">
        <span class="buf-tick" style="left:28.64%">4.01</span>
        <span class="buf-tick is-iso" style="left:50.00%">7.00</span>
        <span class="buf-tick" style="left:71.50%">10.01</span>
    </div>
    
    <!-- Barra física calibrada con marcas -->
    <div class="metro-track">
        <div class="metro-ticks"></div>
        <div class="metro-needle" id="metro-needle"></div>
    </div>
    
    <div class="metro-labels">
        <span>0 ÁCIDO FUERTE</span>
        <span>7 NEUTRO ISOELÉCTRICO</span>
        <span>14 BASE FUERTE</span>
    </div>
</div>
```

---

## 6. Mecanismo de Cambio de Tema

Todas las interfaces de la suite `preview/RTOS2.0/` deben incluir en su barra superior el selector de tema:

```html
<button class="theme-toggle" onclick="toggleTheme()" title="Alternar entre VS Dark y COMSOL Light">
    <span id="theme-icon">☀️ Modo Día (COMSOL)</span>
</button>
```

```javascript
function initTheme() {
    var saved = localStorage.getItem('electrodo32_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeBtn(saved);
}

function toggleTheme() {
    var cur = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = (cur === 'dark') ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('electrodo32_theme', next);
    updateThemeBtn(next);
}

function updateThemeBtn(th) {
    var btn = document.getElementById('theme-icon');
    if (!btn) return;
    btn.innerText = (th === 'dark') ? '☀️ Modo Día (COMSOL)' : '🌙 Modo Noche (VS Dark)';
}

document.addEventListener('DOMContentLoaded', initTheme);
```

---

## 7. Mapeo de Vistas en `C:\Proyecto\ELECTRODO_32\visualizacion\preview\RTOS2.0\`

1. `ph.html`: Módulo de pH dedicado (ADS1115 Canal A1, calibración 1/2/3 puntos, ajuste offset PH-4502C).
2. `fuente.html`: Control de fuente de corriente / tensión de precisión.
3. `fuente_pulsado.html`: Control de generación de pulsos y cronoamperometría.
4. `sensores.html`: Monitoreo general de canales ADC auxiliares y termopar.
5. `termico.html`: Control PID de temperatura y etapas térmicas.
6. `consola.html`: Terminal serial interactivo FreeRTOS CLI.
7. `update.html`: Actualización OTA de firmware para ESP32.
8. `index.html`: Hub central de navegación de la suite de previsualización.

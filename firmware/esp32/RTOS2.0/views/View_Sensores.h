#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MATRIZ DE SENSORES Y SUPERVISOR DE BALIZA (View_Sensores.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Tarjetas sólidas de instrumentación tipo multímetro sin resplandores de neón.
 *   • Supervisor de baliza LED RGB rectangular sobrio.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_SENSORES[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Diagn&oacute;stico de Sensores &middot; RTOS 2.0</title>
<style>

    /* ==========================================================================
       VARIABLES DE TEMA: VS Dark & COMSOL Light (Instrumentación)
       ========================================================================== */
    :root, [data-theme="dark"] {
      --ui-bg: #1e1e1e;
      --ui-panel: #252526;
      --ui-subpanel: #2d2d2d;
      --ui-border: #3c3c3c;
      --ui-border-subtle: #2f2f2f;
      
      --text-primary: #f1f1f1;
      --text-secondary: #cccccc;
      --text-muted: #858585;
      --text-disabled: #555555;

      --accent-primary: #007acc;
      --accent-hover: #1f8ad2;
      --accent-active: #0e639c;

      --metro-ok: #4ec9b0;
      --metro-ok-bg: rgba(78, 201, 176, 0.12);
      --metro-ok-border: #2e8b75;
      --metro-warn: #d7ba7d;
      --metro-warn-bg: rgba(215, 186, 125, 0.12);
      --metro-warn-border: #a88a4d;
      --metro-err: #f14c4c;
      --metro-err-bg: rgba(241, 76, 76, 0.12);
      --metro-err-border: #aa3333;

      --disp-bg: #141414;
      --disp-border: #333333;
      --disp-panel: #1b1b1c;

      --btn-bg: #2d2d2d;
      --btn-border: #3c3c3c;
      --btn-text: #cccccc;
      --btn-hover-bg: #383838;
    }

    [data-theme="light"] {
      --ui-bg: #f3f3f3;
      --ui-panel: #ffffff;
      --ui-subpanel: #e8e8e8;
      --ui-border: #d4d4d4;
      --ui-border-subtle: #e5e5e5;

      --text-primary: #1e1e1e;
      --text-secondary: #333333;
      --text-muted: #666666;
      --text-disabled: #a0a0a0;

      --accent-primary: #005fb8;
      --accent-hover: #106ebe;
      --accent-active: #004578;

      --metro-ok: #2e7d32;
      --metro-ok-bg: #e8f5e9;
      --metro-ok-border: #81c784;
      --metro-warn: #b45309;
      --metro-warn-bg: #fffbeb;
      --metro-warn-border: #fcd34d;
      --metro-err: #c62828;
      --metro-err-bg: #ffebee;
      --metro-err-border: #ef9a9a;

      --disp-bg: #f9f9fb;
      --disp-border: #b8b8b8;
      --disp-panel: #f0f0f4;

      --btn-bg: #e8e8e8;
      --btn-border: #cccccc;
      --btn-text: #222222;
      --btn-hover-bg: #dedede;
    }

    /* ==========================================================================
       RESET & TIPOGRAFÍA DE INGENIERÍA
       ========================================================================== */
    *{margin:0;padding:0;box-sizing:border-box;}
    body{
      font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,Helvetica,Arial,sans-serif;
      background:var(--ui-bg);
      color:var(--text-secondary);
      min-height:100vh;
      padding:0;
      transition:background 0.2s ease, color 0.2s ease;
    }
    .container{max-width:860px;margin:0 auto;padding:14px 14px 40px;}

    .mono{
      font-family:Consolas,"Cascadia Code","SF Mono","Fira Code",monospace;
      font-variant-numeric:tabular-nums;
    }

    /* Hub Nav */
    .hub-bar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:12px;
    }
    .hub-link{
      display:inline-flex;
      align-items:center;
      gap:6px;
      color:var(--accent-primary);
      text-decoration:none;
      font-size:0.75em;
      font-weight:700;
      padding:4px 10px;
      background:var(--ui-panel);
      border-radius:3px;
      border:1px solid var(--ui-border);
      transition:background 0.15s, border-color 0.15s;
    }
    .hub-link:hover{
      background:var(--btn-hover-bg);
      border-color:var(--accent-primary);
    }

    /* Theme Toggle Button */
    .theme-btn{
      display:inline-flex;
      align-items:center;
      gap:6px;
      background:var(--ui-panel);
      color:var(--text-secondary);
      border:1px solid var(--ui-border);
      padding:4px 10px;
      font-size:0.75em;
      font-weight:700;
      border-radius:3px;
      cursor:pointer;
      transition:all 0.15s;
    }
    .theme-btn:hover{
      border-color:var(--accent-primary);
      color:var(--text-primary);
    }

    /* Header Toolbar */
    .hdr{
      display:flex;
      align-items:center;
      justify-content:space-between;
      margin-bottom:14px;
      padding:12px 16px;
      background:var(--ui-panel);
      border-radius:4px;
      border:1px solid var(--ui-border);
      border-top:2px solid var(--accent-primary);
    }
    .nav-back{
      color:var(--accent-primary);
      text-decoration:none;
      font-weight:700;
      font-size:0.8em;
      display:inline-flex;
      align-items:center;
      gap:4px;
    }
    .nav-back:hover{text-decoration:underline;}
    .hdr-title{
      font-size:1.1em;
      color:var(--text-primary);
      font-weight:700;
      letter-spacing:0.2px;
    }
    .hdr-sub{
      font-size:0.68em;
      color:var(--text-muted);
      font-weight:600;
      display:block;
      margin-top:2px;
      letter-spacing:0.6px;
      font-family:Consolas,monospace;
    }
    .hdr-hb{
      display:flex;
      align-items:center;
      gap:6px;
      font-size:0.68em;
      font-weight:700;
      color:var(--text-muted);
      font-family:Consolas,monospace;
      background:var(--disp-panel);
      padding:4px 8px;
      border-radius:2px;
      border:1px solid var(--ui-border);
    }
    .hb-dot{
      width:7px;
      height:7px;
      border-radius:2px;
      background:var(--metro-ok);
    }

    /* Summary Bar */
    .summary{
      display:flex;
      align-items:center;
      justify-content:space-between;
      margin-bottom:14px;
      padding:14px 18px;
      background:var(--ui-panel);
      border-radius:4px;
      border:1px solid var(--ui-border);
      flex-wrap:wrap;
      gap:12px;
    }
    .sum-left{text-align:left;}
    .sum-count{
      font-family:Consolas,"Cascadia Code","SF Mono",monospace;
      font-size:2.2em;
      font-weight:700;
      letter-spacing:-1px;
      font-variant-numeric:tabular-nums;
      line-height:1;
      color:var(--metro-ok);
    }
    .sum-label{
      font-size:0.75em;
      color:var(--text-muted);
      font-weight:600;
      margin-top:4px;
      font-family:Consolas,monospace;
    }

    /* Botón de Escaneo */
    .btn-scan{
      padding:8px 16px;
      cursor:pointer;
      border-radius:3px;
      border:1px solid var(--ui-border);
      background:var(--btn-bg);
      color:var(--text-secondary);
      font-weight:700;
      font-size:0.8em;
      transition:all 0.15s;
      letter-spacing:0.3px;
      display:inline-flex;
      align-items:center;
      gap:6px;
      font-family:Consolas,monospace;
    }
    .btn-scan:hover:not(:disabled){
      background:var(--btn-hover-bg);
      border-color:var(--accent-primary);
      color:var(--text-primary);
    }
    .btn-scan:active{transform:scale(0.99);}
    .btn-scan.scanning{opacity:0.6;cursor:wait;}

    .scan-progress{
      height:3px;
      background:var(--ui-subpanel);
      border-radius:1px;
      margin-top:6px;
      overflow:hidden;
      display:none;
    }
    .scan-progress.active{display:block;}
    .scan-prog-fill{
      height:100%;
      width:0%;
      background:var(--accent-primary);
      animation:scan-sweep 1.2s ease-in-out infinite;
    }
    @keyframes scan-sweep{
      0%{width:0%;margin-left:0;}
      50%{width:50%;margin-left:25%;}
      100%{width:0%;margin-left:100%;}
    }

    /* Barra de Filtro de Subsistemas */
    .filter-bar{
      display:flex;
      align-items:center;
      gap:6px;
      margin-bottom:12px;
      flex-wrap:wrap;
      font-size:0.72em;
      color:var(--text-muted);
      font-family:Consolas,monospace;
    }
    .filter-pill{
      padding:2px 8px;
      border-radius:2px;
      border:1px solid var(--ui-border);
      background:var(--ui-panel);
      display:inline-flex;
      align-items:center;
      gap:5px;
    }
    .cat-dot{
      width:6px;
      height:6px;
      border-radius:1px;
      display:inline-block;
    }

    /* Grid de Sensores */
    .grid{
      display:grid;
      grid-template-columns:repeat(auto-fit, minmax(185px, 1fr));
      gap:10px;
    }

    /* Sensor Card */
    .s-card{
      background:var(--ui-panel);
      border-radius:4px;
      padding:12px 14px;
      border:1px solid var(--ui-border);
      border-left:3px solid var(--ui-border);
      transition:all 0.15s;
      text-align:center;
      position:relative;
    }
    .s-card:hover{
      border-color:var(--accent-primary);
    }
    .s-card.ok{border-left-color:var(--metro-ok);}
    .s-card.fail{border-left-color:var(--metro-err);}

    .s-cat-tag{
      display:inline-block;
      font-size:0.62em;
      font-weight:700;
      letter-spacing:0.5px;
      padding:2px 6px;
      border-radius:2px;
      margin-bottom:6px;
      text-transform:uppercase;
      font-family:Consolas,monospace;
    }
    .s-icon{font-size:22px;margin-bottom:4px;line-height:1;}
    .s-name{
      font-size:0.9em;
      color:var(--text-primary);
      font-weight:700;
      letter-spacing:0.1px;
    }
    .s-bus{
      font-size:0.65em;
      color:var(--text-muted);
      font-weight:600;
      margin-top:2px;
      font-family:Consolas,monospace;
    }
    .s-addr{
      font-size:0.7em;
      color:var(--text-secondary);
      font-weight:700;
      margin-top:3px;
      font-family:Consolas,monospace;
    }
    .s-status{
      margin-top:8px;
      padding:2px 6px;
      border-radius:2px;
      font-size:0.68em;
      font-weight:700;
      display:inline-block;
      font-family:Consolas,monospace;
      border:1px solid transparent;
    }
    .st-ok{
      background:var(--metro-ok-bg);
      color:var(--metro-ok);
      border-color:var(--metro-ok-border);
    }
    .st-fail{
      background:var(--metro-err-bg);
      color:var(--metro-err);
      border-color:var(--metro-err-border);
    }

    /* Timestamp */
    .ts{
      text-align:center;
      margin:12px 0 20px;
      font-size:0.7em;
      color:var(--text-muted);
      font-family:Consolas,monospace;
    }

    /* Sección Códigos de Baliza LED RGB */
    .led-box{
      background:var(--ui-panel);
      border-radius:4px;
      border:1px solid var(--ui-border);
      padding:16px;
    }
    .led-hdr{
      display:flex;
      align-items:center;
      justify-content:space-between;
      margin-bottom:14px;
      padding-bottom:10px;
      border-bottom:1px solid var(--ui-border-subtle);
      flex-wrap:wrap;
      gap:8px;
    }
    .led-title{
      font-size:0.92em;
      font-weight:700;
      color:var(--text-primary);
    }
    .led-sub{
      font-size:0.65em;
      color:var(--text-muted);
      font-weight:700;
      letter-spacing:0.5px;
      font-family:Consolas,monospace;
    }
    .led-hint{
      font-size:0.7em;
      color:var(--accent-primary);
      font-weight:700;
      font-family:Consolas,monospace;
    }
    .led-list{
      display:grid;
      grid-template-columns:1fr;
      gap:8px;
    }
    @media(min-width:620px){.led-list{grid-template-columns:1fr 1fr;}}
    .led-item{
      display:flex;
      align-items:flex-start;
      gap:10px;
      background:var(--disp-panel);
      border-radius:3px;
      padding:10px 12px;
      border:1px solid var(--ui-border);
      transition:all 0.15s;
      position:relative;
      cursor:pointer;
    }
    .led-item:hover{
      background:var(--btn-hover-bg);
      border-color:var(--accent-primary);
    }
    .led-item.active-led{
      border:2px solid var(--accent-primary) !important;
      background:var(--ui-panel) !important;
    }
    .active-pill{display:none;}
    .led-item.active-led .active-pill{
      display:inline-flex;
      align-items:center;
      gap:4px;
      background:var(--accent-primary);
      color:#ffffff;
      padding:1px 5px;
      border-radius:2px;
      font-size:0.62em;
      font-weight:700;
      font-family:Consolas,monospace;
    }
    .led-dot{
      width:10px;
      height:10px;
      border-radius:2px;
      flex-shrink:0;
      margin-top:3px;
      border:1px solid rgba(0,0,0,0.3);
    }
    .led-info{flex:1;}
    .led-state{
      font-size:0.76em;
      font-weight:700;
      color:var(--text-primary);
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:6px;
    }
    .led-tag{
      font-size:0.66em;
      padding:1px 5px;
      border-radius:2px;
      font-weight:700;
      font-family:Consolas,monospace;
    }
    .led-desc{
      font-size:0.68em;
      color:var(--text-muted);
      margin-top:2px;
      line-height:1.35;
    }

    /* LED Solid / Crisp Blink */
    .dot-red-fast{background:#ef4444;animation:strobe 0.25s infinite;}
    .dot-red-slow{background:#ef4444;animation:blink 1s infinite;}
    .dot-white-fast{background:#ffffff;animation:strobe 0.2s infinite;}
    .dot-purple{background:#a855f7;}
    .dot-fuchsia{background:#ec4899;}
    .dot-cyan-pulse{background:#007acc;animation:strobe 0.4s infinite;}
    .dot-cyan-solid{background:#007acc;}
    .dot-blue-dark{background:#1e40af;}
    .dot-blue-pulse{background:#0284c7;animation:strobe 0.4s infinite;}
    .dot-blue-light{background:#0284c7;}
    .dot-amber{background:#f59e0b;}
    .dot-green-solid{background:#10b981;}
    .dot-green-beacon{background:#10b981;animation:beacon 2.5s infinite;}

    @keyframes strobe{0%,100%{opacity:1;}50%{opacity:0.2;}}
    @keyframes blink{0%,49%{opacity:1;}50%,100%{opacity:0.2;}}
    @keyframes beacon{0%,10%{opacity:1;}15%,100%{opacity:0.25;}}

    /* Toast Notifications */
    .toast-container{
      position:fixed;
      bottom:16px;
      right:16px;
      display:flex;
      flex-direction:column;
      gap:6px;
      z-index:9999;
      pointer-events:none;
    }
    .toast{
      padding:8px 12px;
      border-radius:3px;
      font-size:0.75em;
      font-weight:700;
      color:var(--text-primary);
      background:var(--ui-panel);
      border:1px solid var(--ui-border);
      pointer-events:auto;
      max-width:320px;
      display:flex;
      align-items:center;
      gap:6px;
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
      font-family:Consolas,monospace;
    }
    .toast.out{opacity:0;transition:opacity 0.2s;}
    .toast-ok{border-left:3px solid var(--metro-ok);}
    .toast-info{border-left:3px solid var(--accent-primary);}

    @media(max-width:480px){
      .summary{flex-direction:column;align-items:flex-start;}
      .btn-scan{width:100%;justify-content:center;}
      .grid{grid-template-columns:repeat(2,1fr);}
    }
  
</style>
</head>
<body>

  <div class='container'>
    <div class='hub-bar'>
      <a href='../index.html' class='hub-link'>&larr; Hub de Versiones (Tesis)</a>
      <button class='theme-btn' onclick='toggleTheme()' title='Alternar Modo Día / Noche'>
        <span id='theme-btn-lbl'>Modo D&iacute;a</span>
      </button>
    </div>

    <div class='hdr'>
      <a href='index.html' class='nav-back'>&larr; Men&uacute;</a>
      <div>
        <div class='hdr-title'>Diagn&oacute;stico de Sensores</div>
        <span class='hdr-sub'>SUPERVISIÓN DE PERIFÉRICOS</span>
      </div>
      <div class='hdr-hb'>
        <span class='hb-dot' id='hb-dot'></span>
        <span id='hb-txt'>Baliza: OK</span>
      </div>
    </div>

    <div class='summary'>
      <div class='sum-left'>
        <div class='sum-count' id='sum-count'>8 / 8</div>
        <div class='sum-label'>Sensores y M&oacute;dulos Operativos</div>
      </div>
      <div>
        <button class='btn-scan' id='btn-scan' onclick='escanear()'>
          <span></span> ESCANEAR SENSORES
        </button>
        <div class='scan-progress' id='scan-bar'><div class='scan-prog-fill'></div></div>
      </div>
    </div>

    <!-- Leyenda de colores por subsistema -->
    <div class='filter-bar'>
      <span>SUBSISTEMAS:</span>
      <span class='filter-pill'><span class='cat-dot' style='background:#007acc'></span> Ambiental (I2C)</span>
      <span class='filter-pill'><span class='cat-dot' style='background:#a855f7'></span> Sensor de pH</span>
      <span class='filter-pill'><span class='cat-dot' style='background:#f59e0b'></span> Potencia VCSS</span>
      <span class='filter-pill'><span class='cat-dot' style='background:#ea580c'></span> Termopares de Tinas</span>
    </div>

    <div class='grid' id='grid'></div>
    <div class='ts' id='ts'>&Uacute;ltimo escaneo: Sistema en ejecuci&oacute;n continua (SMP Core 1)</div>

    <!-- SECCIÓN CÓDIGOS DE BALIZA LED RGB (13 Estados de Supervisor FreeRTOS) -->
    <div class='led-box'>
      <div class='led-hdr'>
        <div>
          <span class='led-title'>Baliza LED RGB &mdash; C&oacute;digo de Estados</span>
          <span class='led-sub' style='display:block;margin-top:2px;'>SUPERVISOR FREERTOS EN TIEMPO REAL (CORE 1)</span>
        </div>
        <span class='led-hint'>Haga clic en un estado para simularlo &rarr;</span>
      </div>
      <div class='led-list'>
        <div class='led-item' id='led-critical' onclick="selectLed('critical', 'Peligro Crítico', '#ef4444')">
          <div class='led-dot dot-red-fast'></div>
          <div class='led-info'>
            <div class='led-state'><span>Peligro F&iacute;sico Cr&iacute;tico</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(239,68,68,0.15);color:var(--metro-err)'>Rojo (4 Hz)</span></div></div>
            <div class='led-desc'>Sobrecalentamiento (&gt;SP+5&deg;C), sobrecorriente VCSS (&gt;3.5A) o watchdog FreeRTOS disparado.</div>
          </div>
        </div>

        <div class='led-item' id='led-fault' onclick="selectLed('fault', 'Falla Sensor/Enlace', '#ef4444')">
          <div class='led-dot dot-red-slow'></div>
          <div class='led-info'>
            <div class='led-state'><span>Falla Sensor / Enlace</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(239,68,68,0.15);color:var(--metro-err)'>Rojo (1 Hz)</span></div></div>
            <div class='led-desc'>Termopar abierto (TC0..TC3), p&eacute;rdida I2C (ADS1115/MCP4725) o timeout con Arduino Nano.</div>
          </div>
        </div>

        <div class='led-item' id='led-ota' onclick="selectLed('ota', 'Actualización OTA', '#ffffff')">
          <div class='led-dot dot-white-fast'></div>
          <div class='led-info'>
            <div class='led-state'><span>Actualizaci&oacute;n OTA</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:var(--ui-subpanel);color:var(--text-primary)'>Blanco (R&aacute;pido)</span></div></div>
            <div class='led-desc'>Actualizando firmware v&iacute;a Web. &iexcl;No apagar ni desconectar la alimentaci&oacute;n!</div>
          </div>
        </div>

        <div class='led-item' id='led-testbench' onclick="selectLed('testbench', 'Banco de Pruebas', '#a855f7')">
          <div class='led-dot dot-purple'></div>
          <div class='led-info'>
            <div class='led-state'><span>Modo Banco de Pruebas</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(168,85,247,0.15);color:#a855f7'>P&uacute;rpura</span></div></div>
            <div class='led-desc'>Placa en desarrollo: 0 sensores de planta detectados y conexi&oacute;n USB Serial activa.</div>
          </div>
        </div>

        <div class='led-item' id='led-ph' onclick="selectLed('ph', 'Calibración pH', '#ec4899')">
          <div class='led-dot dot-fuchsia'></div>
          <div class='led-info'>
            <div class='led-state'><span>Calibraci&oacute;n de pH</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(236,72,153,0.15);color:#ec4899'>Magenta</span></div></div>
            <div class='led-desc'>Sonda en soluci&oacute;n tamp&oacute;n; ajuste de offset y pendiente en curso.</div>
          </div>
        </div>

        <div class='led-item' id='led-term_pulse' onclick="selectLed('term_pulse', 'Térmico + VCSS Pulsado', '#007acc')">
          <div class='led-dot dot-cyan-pulse'></div>
          <div class='led-info'>
            <div class='led-state'><span>T&eacute;rmico + VCSS Pulsado</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(0,122,204,0.15);color:var(--accent-primary)'>Azul Pulsante</span></div></div>
            <div class='led-desc'>Sistema t&eacute;rmico activo + corriente modulada en tren de pulsos.</div>
          </div>
        </div>

        <div class='led-item' id='led-term_dc' onclick="selectLed('term_dc', 'Térmico + VCSS Continuo', '#007acc')">
          <div class='led-dot dot-cyan-solid'></div>
          <div class='led-info'>
            <div class='led-state'><span>T&eacute;rmico + VCSS Continuo</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(0,122,204,0.15);color:var(--accent-primary)'>Azul (Fijo)</span></div></div>
            <div class='led-desc'>Sistema t&eacute;rmico activo + salida de corriente continua (DC).</div>
          </div>
        </div>

        <div class='led-item' id='led-term_only' onclick="selectLed('term_only', 'Sistema Térmico', '#1e40af')">
          <div class='led-dot dot-blue-dark'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sistema T&eacute;rmico Activo</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(30,64,175,0.15);color:#3b82f6'>Azul Cobalto</span></div></div>
            <div class='led-desc'>Control t&eacute;rmico PI activo en los reactores/tinas.</div>
          </div>
        </div>

        <div class='led-item' id='led-pulse_only' onclick="selectLed('pulse_only', 'VCSS Pulsado', '#0284c7')">
          <div class='led-dot dot-blue-pulse'></div>
          <div class='led-info'>
            <div class='led-state'><span>Salida de Corriente Pulsada</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(2,132,199,0.15);color:#0284c7'>Celeste Pulsante</span></div></div>
            <div class='led-desc'>Electrodeposici&oacute;n por pulsos activa.</div>
          </div>
        </div>

        <div class='led-item' id='led-dc_only' onclick="selectLed('dc_only', 'VCSS Continuo', '#0284c7')">
          <div class='led-dot dot-blue-light'></div>
          <div class='led-info'>
            <div class='led-state'><span>Salida de Corriente Continua (DC)</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(2,132,199,0.15);color:#0284c7'>Celeste (Fijo)</span></div></div>
            <div class='led-desc'>Corriente continua estable VCSS activa (DAC MCP4725).</div>
          </div>
        </div>

        <div class='led-item' id='led-env_missing' onclick="selectLed('env_missing', 'Sensores Ambientales Ausentes', '#f59e0b')">
          <div class='led-dot dot-amber'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sensores Ambientales Ausentes</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(245,158,11,0.15);color:var(--metro-warn)'>&Aacute;mbar (Fijo)</span></div></div>
            <div class='led-desc'>Sensores ambientales AHT20/BMP280 no detectados; sistema operable.</div>
          </div>
        </div>

        <div class='led-item active-led' id='led-standby_connected' onclick="selectLed('standby_connected', 'Reposo Conectado', '#10b981')">
          <div class='led-dot dot-green-solid'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sistema en Reposo (Conectado)</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(16,185,129,0.15);color:var(--metro-ok)'>Verde (Fijo)</span></div></div>
            <div class='led-desc'>Todo OK. Operador conectado por Wi-Fi; planta en espera sin comandos activos.</div>
          </div>
        </div>

        <div class='led-item' id='led-standby_beacon' onclick="selectLed('standby_beacon', 'Espera Wi-Fi', '#10b981')">
          <div class='led-dot dot-green-beacon'></div>
          <div class='led-info'>
            <div class='led-state'><span>En Espera de Conexi&oacute;n Wi-Fi</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(16,185,129,0.15);color:var(--metro-ok)'>Verde (Destello)</span></div></div>
            <div class='led-desc'>Red Wi-Fi SoftAP "Uli" emitiendo baliza; esperando conexi&oacute;n del usuario.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class='toast-container' id='toast-box'></div>

  
<script>
var sensores=[
  {key:'aht', name:'AHT20', bus:'I2C', addr:'0x38', desc:'Temp / Humedad', cat:'Ambiental', color:'#06b6d4'},
  {key:'bmp', name:'BMP280', bus:'I2C', addr:'0x76/77', desc:'Presión Atm.', cat:'Ambiental', color:'#06b6d4'},
  {key:'ads', name:'ADS1115', bus:'I2C', addr:'0x48', desc:'ADC pH 16-bit', cat:'pH / Sondas', color:'#a855f7'},
  {key:'dac', name:'MCP4725', bus:'I2C', addr:'0x60', desc:'DAC Corriente', cat:'Potencia VCSS', color:'#f59e0b'},
  {key:'tc0', name:'MAX6675 #0', bus:'SPI', addr:'Canal 1', desc:'Limpieza', cat:'Térmico', color:'#f97316'},
  {key:'tc1', name:'MAX6675 #1', bus:'SPI', addr:'Canal 2', desc:'Decapado', cat:'Térmico', color:'#f97316'},
  {key:'tc2', name:'MAX6675 #2', bus:'SPI', addr:'Canal 3', desc:'Celda Hull', cat:'Térmico', color:'#f97316'},
  {key:'tc3', name:'MAX6675 #3', bus:'SPI', addr:'Canal 4', desc:'Niquelado', cat:'Térmico', color:'#f97316'}
];

var lastOk = Date.now();

/* ==========================================================================
   GESTIÓN DE TEMA DUAL
   ========================================================================== */
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
    var btn = document.getElementById('theme-btn-lbl');
    if (!btn) return;
    btn.innerHTML = (th === 'dark') ? 'Modo D&iacute;a' : 'Modo Noche';
}

initTheme();

function showToast(msg, type){
    var box = document.getElementById('toast-box');
    var t = document.createElement('div');
    t.className = 'toast toast-' + (type || 'info');
    t.innerHTML = msg;
    box.appendChild(t);
    setTimeout(function(){
        t.classList.add('out');
        setTimeout(function(){ t.remove(); }, 300);
    }, 3500);
}

function highlightLedState(code){
    if(!code) return;
    var items = document.querySelectorAll('.led-item');
    for(var i = 0; i < items.length; i++){
        items[i].classList.remove('active-led');
    }
    var target = document.getElementById('led-' + code);
    if(target){
        target.classList.add('active-led');
    }
}

function buildGrid(data){
    var ok = 0, total = 8;
    var h = '';
    for(var i = 0; i < sensores.length; i++){
        var s = sensores[i];
        var estado = -1;
        if(data){
            if(s.key === 'aht') estado = data.aht;
            else if(s.key === 'bmp') estado = data.bmp;
            else if(s.key === 'ads') estado = data.ads;
            else if(s.key === 'dac') estado = data.dac;
            else if(s.key === 'tc0') estado = (data.tc && data.tc[0] !== undefined) ? data.tc[0] : 0;
            else if(s.key === 'tc1') estado = (data.tc && data.tc[1] !== undefined) ? data.tc[1] : 0;
            else if(s.key === 'tc2') estado = (data.tc && data.tc[2] !== undefined) ? data.tc[2] : 0;
            else if(s.key === 'tc3') estado = (data.tc && data.tc[3] !== undefined) ? data.tc[3] : 0;
            if(estado === 1) ok++;
        }
        var cls = estado === -1 ? 'wait' : (estado === 1 ? 'ok' : 'fail');
        var icon = estado === -1 ? '&#9898;' : (estado === 1 ? '&#10003;' : '&#10007;');
        var txt = estado === -1 ? 'PENDIENTE' : (estado === 1 ? 'ONLINE' : 'ERROR / AUSENTE');
        
        h += '<div class="scard ' + cls + '">' +
            '<div class="scard-top">' +
                '<span class="scard-name">' + s.name + '</span>' +
                '<span class="bus-badge bus-' + s.bus + '">' + s.bus + '</span>' +
            '</div>' +
            '<div class="scard-addr">' + s.addr + '</div>' +
            '<div class="scard-desc">' + s.desc + '</div>' +
            '<div class="scard-footer">' +
                '<span class="scard-cat">' + s.cat + '</span>' +
                '<span class="scard-st ' + cls + '">' + icon + ' ' + txt + '</span>' +
            '</div>' +
        '</div>';
    }
    document.getElementById('grid').innerHTML = h;

    var pill = document.getElementById('sum-pill');
    if(!data){
        pill.className = 'sum-pill';
        pill.innerHTML = '&#9898; Esperando diagn&oacute;stico inicial...';
    } else if(ok === total){
        pill.className = 'sum-pill ok';
        pill.innerHTML = '&#10003; Todos los dispositivos online (' + ok + '/' + total + ')';
    } else {
        pill.className = 'sum-pill fail';
        pill.innerHTML = '&#9888; ' + (total - ok) + ' sensor(es) con falla (' + ok + '/' + total + ' online)';
    }
}

function updHb(){
    var d = Date.now() - lastOk;
    var dot = document.getElementById('hb-dot');
    var txt = document.getElementById('hb-txt');
    if(!dot || !txt) return;
    if(d > 6000){
        dot.className = 'hb-dot off';
        txt.innerText = 'DESCONECTADO';
        txt.style.color = 'var(--metro-err)';
    } else {
        dot.className = 'hb-dot';
        var s = Math.floor(d / 1000);
        txt.innerText = (s < 2) ? 'CONECTADO' : 'Hace ' + s + 's';
        txt.style.color = 'var(--text-muted)';
    }
}

function escanear(){
    var btn = document.getElementById('btn-scan');
    btn.className = 'btn-scan scanning';
    btn.innerHTML = 'ESCANEANDO BUS...';
    btn.disabled = true;
    var prog = document.getElementById('scan-prog');
    if(prog) prog.className = 'scan-progress active';

    fetch('/data_sensors')
        .then(function(r){ return r.json(); })
        .then(function(data){
            lastOk = Date.now();
            buildGrid(data);
            if(data && data.led) highlightLedState(data.led);
            var now = new Date();
            var timeStr = now.toLocaleTimeString();
            document.getElementById('ts').innerText = 'Último escaneo: ' + timeStr;
            showToast('&#10003; Escaneo de sensores completado', 'ok');
        })
        .catch(function(err){
            document.getElementById('ts').innerText = 'Error de comunicación con ESP32';
            showToast('&#9888; Error al comunicar con ESP32', 'err');
        })
        .finally(function(){
            btn.className = 'btn-scan';
            btn.innerHTML = 'ESCANEAR SENSORES';
            btn.disabled = false;
            if(prog) prog.className = 'scan-progress';
            updHb();
        });
}

buildGrid(null);
escanear();

setInterval(function(){
    fetch('/data_sensors')
        .then(function(r){ return r.json(); })
        .then(function(d){
            lastOk = Date.now();
            if(d && d.led) highlightLedState(d.led);
        })
        .catch(function(){});
}, 2500);

setInterval(updHb, 1000);
</script>
</body>
</html>
)rawliteral";

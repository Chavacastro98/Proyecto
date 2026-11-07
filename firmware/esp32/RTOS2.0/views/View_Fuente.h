#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: SALIDA DE CORRIENTE VCSS (View_Fuente.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Osciloscopio técnico con retícula 10x6 sobria sin distorsiones ni scanlines falsos.
 *   • Botones de preset rectangulares industriales y lecturas métricas monoespaciadas.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_FUENTE[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Salida de Corriente &middot; RTOS 2.0</title>
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
            --disp-val: #4ec9b0;
            --disp-panel: #1b1b1c;

            --btn-bg: #2d2d2d;
            --btn-border: #3c3c3c;
            --btn-text: #cccccc;
            --btn-hover-bg: #383838;

            --scale-track: #2a2a2a;
            --scale-tick: #555555;
            --scale-needle: #ffffff;
            
            --crt-bg: #090d12;
            --crt-border: #1e293b;
            --crt-grid: rgba(78, 201, 176, 0.15);
            --crt-trace: #4ec9b0;
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
            --disp-val: #005fb8;
            --disp-panel: #f0f0f4;

            --btn-bg: #e8e8e8;
            --btn-border: #cccccc;
            --btn-text: #222222;
            --btn-hover-bg: #dedede;

            --scale-track: #e0e0e0;
            --scale-tick: #999999;
            --scale-needle: #005fb8;
            
            --crt-bg: #f8fafc;
            --crt-border: #cbd5e1;
            --crt-grid: rgba(0, 95, 184, 0.12);
            --crt-trace: #005fb8;
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
        .container{max-width:640px;margin:0 auto;padding:14px 14px 40px;}

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
            margin-bottom:16px;
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
        }
        .hb-dot{
            width:7px;
            height:7px;
            border-radius:2px;
            background:var(--metro-ok);
        }
        .hb-dot.off{background:var(--metro-err);}

        /* Tarjeta Principal */
        .card{
            background:var(--ui-panel);
            border-radius:4px;
            padding:18px 20px;
            border:1px solid var(--ui-border);
            margin-bottom:16px;
            text-align:center;
        }

        /* Botón de Alimentación / Master Switch */
        .btn-pwr{
            width:100%;
            font-size:0.95em;
            padding:12px;
            border-radius:3px;
            font-weight:700;
            cursor:pointer;
            border:1px solid transparent;
            transition:all 0.15s ease;
            letter-spacing:0.5px;
            display:flex;
            align-items:center;
            justify-content:center;
            gap:8px;
            font-family:Consolas,monospace;
        }
        .btn-pwr:active{transform:scale(0.99);}
        .btn-pwr-off{
            background:var(--metro-ok);
            color:#ffffff;
            border-color:var(--metro-ok-border);
        }
        .btn-pwr-off:hover{
            filter:brightness(1.08);
        }
        .btn-pwr-on{
            background:var(--metro-err);
            color:#ffffff;
            border-color:var(--metro-err-border);
        }
        .btn-pwr-on:hover{
            filter:brightness(1.08);
        }

        /* Status Badge */
        .status-badge{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:3px 10px;
            border-radius:2px;
            font-weight:700;
            font-size:0.74em;
            margin:12px 0 10px;
            letter-spacing:0.5px;
            font-family:Consolas,monospace;
            border:1px solid transparent;
        }
        .status-on{
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border-color:var(--metro-ok-border);
        }
        .status-off{
            background:var(--ui-subpanel);
            color:var(--text-muted);
            border-color:var(--ui-border);
        }

        /* Display de Amperímetro Digital */
        .meter-box{
            background:var(--disp-bg);
            border-radius:4px;
            padding:16px 14px 14px;
            margin:10px 0;
            border:1px solid var(--disp-border);
            position:relative;
        }
        .meter-sub{
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:700;
            letter-spacing:0.8px;
            text-transform:uppercase;
            margin-bottom:6px;
            font-family:Consolas,monospace;
        }
        .amp-box{
            font-family:Consolas,"Cascadia Code","SF Mono",monospace;
            font-size:58px;
            font-weight:700;
            letter-spacing:-1px;
            font-variant-numeric:tabular-nums;
            line-height:1;
            color:var(--disp-val);
            transition:color 0.2s;
        }
        .amp-box span{
            font-size:0.5em;
            color:var(--text-muted);
            font-weight:600;
            margin-left:4px;
        }

        /* Barra VU Graduada con Ticks Físicos */
        .vu-wrap{
            margin:14px 0 10px;
            padding:0 4px;
        }
        .vu-bar-bg{
            height:10px;
            background:var(--scale-track);
            border-radius:2px;
            overflow:hidden;
            position:relative;
            border:1px solid var(--ui-border);
        }
        .vu-bar-fill{
            height:100%;
            border-radius:1px;
            transition:width 0.2s ease-out;
            background:linear-gradient(90deg, var(--accent-primary), var(--metro-ok) 50%, var(--metro-warn) 80%, var(--metro-err) 100%);
        }
        .vu-labels{
            display:flex;
            justify-content:space-between;
            font-size:0.65em;
            color:var(--text-muted);
            font-weight:700;
            margin-top:4px;
            padding:0 2px;
            font-family:Consolas,monospace;
        }

        /* Indicador de Cadencia de Pulso */
        .pulse-ind{
            margin:6px 0 8px;
            font-size:0.72em;
            font-weight:700;
            letter-spacing:0.5px;
            color:var(--text-muted);
            height:20px;
            display:flex;
            align-items:center;
            justify-content:center;
            gap:6px;
            font-family:Consolas,monospace;
        }
        .pulse-dot{
            display:inline-block;
            width:7px;
            height:7px;
            border-radius:2px;
            background:var(--accent-primary);
        }
        .pulse-dot.beating{
            animation:pulse-beat var(--pulse-period,0.1s) ease-in-out infinite;
        }
        @keyframes pulse-beat{
            0%,100%{opacity:1;}
            50%{opacity:0.2;}
        }

        /* Metadatos del Instrumento */
        .meter-meta{
            display:flex;
            justify-content:center;
            gap:14px;
            margin-top:12px;
            padding-top:10px;
            border-top:1px solid var(--ui-border-subtle);
            font-size:0.74em;
            color:var(--text-muted);
            font-weight:600;
            font-family:Consolas,monospace;
            flex-wrap:wrap;
        }
        .meter-meta b{color:var(--text-primary);}

        /* Selector Segmentado de Modo (DC / Pulsado) */
        .btn-mode-wrap{
            display:flex;
            gap:4px;
            margin:14px 0;
            background:var(--disp-panel);
            border-radius:3px;
            padding:3px;
            border:1px solid var(--ui-border);
        }
        .btn-m{
            flex:1;
            padding:8px 10px;
            border-radius:2px;
            border:1px solid transparent;
            font-weight:700;
            font-size:0.76em;
            cursor:pointer;
            transition:all 0.15s;
            letter-spacing:0.3px;
            font-family:Consolas,monospace;
        }
        .btn-m.act{
            background:var(--accent-primary);
            color:#ffffff;
            border-color:var(--accent-primary);
        }
        .btn-m.inact{
            background:transparent;
            color:var(--text-muted);
        }
        .btn-m.inact:hover{
            color:var(--text-primary);
            background:var(--btn-hover-bg);
        }

        /* Controles y Sliders Técnicos */
        .ctrl-group{
            background:var(--disp-panel);
            padding:12px 14px;
            border-radius:3px;
            margin-top:10px;
            text-align:left;
            border:1px solid var(--ui-border);
        }
        .ctrl-group label{
            font-weight:700;
            font-size:0.75em;
            color:var(--text-muted);
            display:flex;
            justify-content:space-between;
            margin-bottom:6px;
            font-family:Consolas,monospace;
        }
        .ctrl-group b{color:var(--text-primary);}
        input[type=range]{
            width:100%;
            accent-color:var(--accent-primary);
            margin:6px 0 4px;
            cursor:pointer;
            height:5px;
            background:var(--scale-track);
            border-radius:2px;
        }

        /* Presets de Corriente */
        .preset-wrap{
            display:flex;
            gap:4px;
            margin-top:8px;
            flex-wrap:wrap;
        }
        .btn-preset{
            flex:1;
            min-width:38px;
            padding:5px 4px;
            border-radius:2px;
            background:var(--ui-panel);
            border:1px solid var(--ui-border);
            color:var(--text-secondary);
            font-size:0.72em;
            font-weight:700;
            cursor:pointer;
            transition:all 0.15s;
            text-align:center;
            font-family:Consolas,monospace;
        }
        .btn-preset:hover{
            background:var(--btn-hover-bg);
            border-color:var(--accent-primary);
            color:var(--text-primary);
        }
        .btn-preset.active{
            background:var(--accent-primary);
            border-color:var(--accent-primary);
            color:#ffffff;
        }

        /* Osciloscopio Técnico de Precisión */
        .crt-bezel{
            background:var(--crt-bg);
            border-radius:4px;
            padding:10px;
            border:1px solid var(--crt-border);
            margin:12px 0;
            text-align:left;
        }
        .crt-hdr{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:6px;
            font-size:0.7em;
            font-weight:700;
            font-family:Consolas,monospace;
        }
        .crt-title{
            color:var(--crt-trace);
            display:flex;
            align-items:center;
            gap:6px;
            letter-spacing:0.5px;
        }
        .crt-led{
            width:6px;
            height:6px;
            border-radius:2px;
            background:var(--crt-trace);
        }
        .crt-stats{
            color:var(--text-muted);
            font-variant-numeric:tabular-nums;
            letter-spacing:0.2px;
        }
        .crt-screen-wrap{
            position:relative;
            border-radius:3px;
            overflow:hidden;
            border:1px solid var(--crt-border);
            background:var(--disp-bg);
        }

        /* Panel VCSS RTOS */
        .vcss-panel{
            background:var(--disp-panel);
            border-radius:4px;
            padding:14px;
            margin-top:14px;
            border:1px solid var(--ui-border);
            text-align:left;
        }
        .vcss-hdr{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:10px;
            font-size:0.72em;
            color:var(--text-muted);
            font-weight:700;
            letter-spacing:0.5px;
            flex-wrap:wrap;
            gap:6px;
            font-family:Consolas,monospace;
        }
        .vcss-badges{display:flex;gap:6px;}
        .vcss-badge{
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border:1px solid var(--metro-ok-border);
            padding:2px 6px;
            border-radius:2px;
            font-size:0.7em;
            font-weight:700;
            font-family:Consolas,monospace;
        }
        .vcss-badge.off{
            background:var(--ui-subpanel);
            color:var(--text-muted);
            border-color:var(--ui-border);
        }
        .vcss-grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:8px;
            margin-bottom:12px;
        }
        .vcss-cell{
            background:var(--ui-panel);
            border-radius:3px;
            padding:8px 10px;
            border:1px solid var(--ui-border);
        }
        .vcss-lbl{
            font-size:0.65em;
            color:var(--text-muted);
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:0.4px;
            font-family:Consolas,monospace;
        }
        .vcss-val{
            font-size:1.05em;
            font-weight:700;
            color:var(--text-primary);
            margin-top:2px;
            font-family:Consolas,monospace;
            font-variant-numeric:tabular-nums;
        }
        .btn-cal{
            width:100%;
            padding:8px 10px;
            background:var(--btn-bg);
            color:var(--text-secondary);
            border:1px solid var(--ui-border);
            border-radius:3px;
            font-weight:700;
            font-size:0.75em;
            cursor:pointer;
            transition:all 0.15s;
            font-family:Consolas,monospace;
        }
        .btn-cal:hover:not(:disabled){
            background:var(--btn-hover-bg);
            border-color:var(--accent-primary);
            color:var(--text-primary);
        }
        .btn-cal:active{transform:scale(0.99);}
        .btn-cal:disabled{opacity:0.5;cursor:wait;}
        .spin{
            display:inline-block;
            width:10px;
            height:10px;
            border:2px solid currentColor;
            border-top-color:transparent;
            border-radius:50%;
            animation:spin-r 0.6s linear infinite;
            vertical-align:middle;
            margin-right:4px;
        }
        @keyframes spin-r{to{transform:rotate(360deg);}}

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
        .toast-err{border-left:3px solid var(--metro-err);}
        .toast-warn{border-left:3px solid var(--metro-warn);}
        .toast-info{border-left:3px solid var(--accent-primary);}
    
        .vcss-val { font-variant-numeric: tabular-nums; }
        .vcss-sub { font-size: 0.75em; color: var(--text-muted); font-family: Consolas, monospace; }
        .meter-meta { display: flex; justify-content: space-between; font-size: 0.8em; color: var(--text-muted); margin-top: 6px; font-family: Consolas, monospace; }

</style>
</head>
<body>

    <div class='container'>
        <div class='hdr'>
            <div style='display:flex;align-items:center;gap:12px;'><a href='/' class='nav-back'>&larr; Men&uacute;</a><button class='theme-btn' id='theme-btn' onclick='toggleTheme()' title='Alternar Tema'><span id='theme-btn-lbl'>Modo D&iacute;a</span></button></div>
            <div style='text-align:center'>
                <span class='hdr-title'>Salida de Corriente</span>
                <span class='hdr-sub'>CONTROL VCSS &middot; SHUNT DUAL &middot; RTOS 2.0</span>
            </div>
            <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span><span id='hb-txt'>...</span></div>
        </div>

        <div class='card'>
            <button class='btn-pwr btn-pwr-off' id='btn-power' onclick='togglePower()'>ENCENDER FUENTE</button>
            
            <div><span class='status-badge status-off' id='status-badge'>ESTADO: EN ESPERA (0.00 A)</span></div>

            <div class='meter-box'>
                <div class='meter-sub'>Salida de Corriente</div>
                <div class='amp-box' id='amp-display'><span id='amp-amps'>0.00</span> A</div>
                <div class='meter-meta'>
                    <span>Consigna: <b id='amp-calc'>1.77</b> A</span>
                    <span>Modo: <b id='modo-str'>Continua (DC)</b></span>
                </div>
            </div>

            <!-- VU Meter -->
            <div class='vu-wrap'>
                <div class='vu-bar-bg'><div class='vu-bar-fill' id='vu-fill' style='width:0%'></div></div>
                <div class='vu-labels'><span>0A</span><span>1A</span><span>2A</span><span>3A</span><span>4A</span></div>
            </div>

            <!-- Pulse Indicator -->
            <div class='pulse-ind' id='pulse-ind'></div>

            <div class='btn-mode-wrap'>
                <button class='btn-m act' id='btn-dc' onclick='setModo(0)'>CONTINUA (DC)</button>
                <button class='btn-m inact' id='btn-pulsed' onclick='setModo(1)'>PULSADA (1-100 Hz)</button>
            </div>

            <div class='ctrl-group'>
                <label>
                    <span>Amplitud: <b id='amp-bits'>1024</b> bits</span>
                    <span>(<span id='amp-calc2'>1.77</span> A)</span>
                </label>
                <input type='range' id='slide-amp' min='0' max='4095' value='1024' oninput='onAmpInput(this.value)' onchange='onAmpChange(this.value)'>
                <div class='preset-wrap'>
                    <button class='btn-preset' id='pre-0' onclick='setPreset(0)'>0 A</button>
                    <button class='btn-preset' id='pre-05' onclick='setPreset(0.5)'>0.5 A</button>
                    <button class='btn-preset' id='pre-1' onclick='setPreset(1.0)'>1 A</button>
                    <button class='btn-preset' id='pre-113' onclick='setPreset(1.13)'>1.13 A</button>
                    <button class='btn-preset' id='pre-15' onclick='setPreset(1.5)'>1.5 A</button>
                    <button class='btn-preset' id='pre-3' onclick='setPreset(3.0)'>3 A</button>
                    <button class='btn-preset' id='pre-max' onclick='setPreset(7.06)'>M&Aacute;X</button>
                </div>
            </div>

            <div id='pulsed-options' style='display:none;'>
                <!-- Osciloscopio CRT Verde Retro -->
                <div class='crt-bezel'>
                    <div class='crt-hdr'>
                        <span class='crt-title'>
                            <span class='crt-led'></span>
                            OSCILOSCOPIO CRT &middot; CH1
                        </span>
                        <span id='wave-stats' class='crt-stats'>T = 100.0 ms | t_on = 50.0 ms</span>
                    </div>
                    <div class='crt-screen-wrap'>
                        <canvas id='wave-canvas' width='520' height='120' style='width:100%;height:120px;display:block;'></canvas>
                        <div class='crt-glass-glare'></div>
                        <div class='crt-scanlines'></div>
                    </div>
                </div>
                <div class='ctrl-group'>
                    <label><span>Frecuencia</span><b id='freq-val'>10 Hz</b></label>
                    <input type='range' id='slide-freq' min='1' max='100' value='10' oninput='document.getElementById("freq-val").innerText=this.value+" Hz";drawPulseWave();sendParam("f", this.value);'>
                </div>
                <div class='ctrl-group'>
                    <label><span>Ciclo de Trabajo</span><b id='duty-val'>50 %</b></label>
                    <input type='range' id='slide-duty' min='1' max='99' value='50' oninput='document.getElementById("duty-val").innerText=this.value+" %";drawPulseWave();sendParam("d", this.value);'>
                </div>
            </div>

            <!-- Panel Sensado VCSS -->
            <div class='vcss-panel'>
                <div class='vcss-hdr'>
                    <span>MONITOREO DE CORRIENTE</span>
                    <div class='vcss-badges'>
                        <span class='vcss-badge' id='rele-badge'>REL&Eacute; +12V: AISLADO</span>
                        <span class='vcss-badge' id='comp-badge'>CONTROL AUTOM&Aacute;TICO: ACTIVO</span>
                    </div>
                </div>
                <div class='vcss-grid'>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Rama 1 (MOSFET 1)</div>
                        <div class='vcss-val' id='i1-val'>0.00 A</div>
                        <div class='vcss-sub' id='v1-val'>0.000 V</div>
                    </div>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Rama 2 (MOSFET 2)</div>
                        <div class='vcss-val' id='i2-val'>0.00 A</div>
                        <div class='vcss-sub' id='v2-val'>0.000 V</div>
                    </div>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Total Medido</div>
                        <div class='vcss-val' id='itot-val' style='color:#34d399;'>0.00 A</div>
                        <div class='vcss-sub' id='gm-val'>Gm: 2.000 S</div>
                    </div>
                </div>
                <div class='vcss-actions'>
                    <button class='btn-vcss' id='btn-comp' onclick='toggleComp()'>Desactivar Control Autom&aacute;tico</button>
                    <button class='btn-vcss btn-cal' id='btn-cal' onclick='calibrarVCSS()'>Auto-Calibrar</button>
                    <button class='btn-vcss btn-reset' id='btn-rst' onclick='resetCalibrarVCSS()'>Ganancia Predeterminada</button>
                </div>
            </div>
        </div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    
<script>

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
            drawPulseWave();
        }

        function updateThemeBtn(th) {
            var btn = document.getElementById('theme-btn-lbl');
            if (!btn) return;
            btn.innerHTML = (th === 'dark') ? 'Modo D&iacute;a' : 'Modo Noche';
        }

        initTheme();


        var fuenteActiva = false;
        var isDragging = false;
        var compActivo = true;
        var lastOk = Date.now();
        var prevAmps = 0;

        function showToast(msg,type){var box=document.getElementById('toast-box');var t=document.createElement('div');t.className='toast toast-'+(type||'info');t.innerHTML=msg;box.appendChild(t);setTimeout(function(){t.classList.add('out');setTimeout(function(){t.remove();},300);},3500);}

        function ampColor(a){
            var isDark = (document.documentElement.getAttribute('data-theme') !== 'light');
            if(a < 0.05) return isDark ? '#858585' : '#888888';
            if(a < 2.0) return isDark ? '#4ec9b0' : '#2e7d32';
            if(a < 3.5) return isDark ? '#d7ba7d' : '#b45309';
            return isDark ? '#f14c4c' : '#c62828';
        }

        function animateValue(el, start, end, dur) {
            if(Math.abs(end-start)<0.005){el.innerText=end.toFixed(2);return;}
            var range=end-start;
            var t0=null;
            function step(ts){
                if(!t0) t0=ts;
                var p=Math.min((ts-t0)/dur,1);
                var v=start+range*p;
                el.innerText=v.toFixed(2);
                if(p<1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        }

        function updHb(){
            var d=Date.now()-lastOk;
            var dot=document.getElementById('hb-dot');
            var txt=document.getElementById('hb-txt');
            if(d>6000){dot.className='hb-dot off';txt.innerText='Sin conexi\u00f3n';}
            else{dot.className='hb-dot';var s=Math.floor(d/1000);txt.innerText=s<2?'OK':'Hace '+s+'s';}
        }

        function loadFuenteData(){
            if (isDragging) return;
            fetch('/data_f').then(function(r){return r.json();}).then(function(d){
                lastOk=Date.now();
                fuenteActiva = (d.act == 1);
                compActivo = (d.comp == 1);
                var btnPwr = document.getElementById('btn-power');
                var badge = document.getElementById('status-badge');
                var ampVal = parseFloat(d.amps).toFixed(2);
                var ampNum = parseFloat(d.amps);
                var ampDisplay = document.getElementById('amp-display');
                var col = ampColor(fuenteActiva ? ampNum : 0);
                
                if (fuenteActiva) {
                    btnPwr.innerText = "APAGAR FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-on";
                    badge.innerText = "ESTADO: ACTIVA (" + ampVal + " A)";
                    badge.className = "status-badge status-on";
                    animateValue(document.getElementById('amp-amps'), prevAmps, ampNum, 350);
                    ampDisplay.style.color = col;
                } else {
                    btnPwr.innerText = "ENCENDER FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-off";
                    badge.innerText = "ESTADO: EN ESPERA (0.00 A)";
                    badge.className = "status-badge status-off";
                    document.getElementById('amp-amps').innerText = "0.00";
                    ampDisplay.style.color = '#38bdf8';
                }
                prevAmps = fuenteActiva ? ampNum : 0;

                // VU meter
                var vuPct = Math.min((ampNum / 4.0) * 100, 100);
                document.getElementById('vu-fill').style.width = (fuenteActiva ? vuPct : 0) + '%';

                // Pulse indicator
                var isPulsed = (d.modo == 1);
                var pulseEl = document.getElementById('pulse-ind');
                if(isPulsed && fuenteActiva){
                    var freq = parseInt(d.freq) || 10;
                    var period = (1.0/freq);
                    pulseEl.innerHTML = "<span class='pulse-dot beating' style='--pulse-period:"+period+"s'></span> Pulsando a "+freq+" Hz (Duty: "+d.duty+"%)";
                    pulseEl.style.color='#38bdf8';
                } else if(fuenteActiva){
                    pulseEl.innerHTML = "Corriente Continua (DC)";
                    pulseEl.style.color='#22c55e';
                } else {
                    pulseEl.innerHTML = "";
                }

                document.getElementById('btn-dc').className = isPulsed ? "btn-m inact" : "btn-m act";
                document.getElementById('btn-pulsed').className = isPulsed ? "btn-m act" : "btn-m inact";
                document.getElementById('pulsed-options').style.display = isPulsed ? "block" : "none";
                document.getElementById('modo-str').innerText = isPulsed ? "Pulsada (" + d.freq + " Hz)" : "Continua (DC)";

                document.getElementById('slide-amp').value = d.sp;
                document.getElementById('amp-bits').innerText = d.sp;
                document.getElementById('amp-calc').innerText = ampVal;
                var calcEl = document.getElementById('amp-calc2');
                if(calcEl) calcEl.innerText = ampVal;

                document.getElementById('slide-freq').value = d.freq;
                document.getElementById('freq-val').innerText = d.freq + " Hz";

                document.getElementById('slide-duty').value = d.duty;
                document.getElementById('duty-val').innerText = d.duty + " %";

                // VCSS
                document.getElementById('i1-val').innerText = d.i1.toFixed(2) + " A";
                document.getElementById('v1-val').innerText = d.vs1.toFixed(3) + " V";
                document.getElementById('i2-val').innerText = d.i2.toFixed(2) + " A";
                document.getElementById('v2-val').innerText = d.vs2.toFixed(3) + " V";
                document.getElementById('itot-val').innerText = d.i_real.toFixed(2) + " A";
                document.getElementById('gm-val').innerText = "Gm: " + (d.gm * 2.0).toFixed(3) + " S (" + d.gm.toFixed(3) + "x)";

                var releBadge = document.getElementById('rele-badge');
                if (d.rele == 1) {
                    releBadge.innerText = "RELÉ +12V: CERRADO (ACTIVO)";
                    releBadge.className = "vcss-badge";
                } else {
                    releBadge.innerText = "RELÉ +12V: AISLADO (0V)";
                    releBadge.className = "vcss-badge off";
                }

                var compBadge = document.getElementById('comp-badge');
                var btnComp = document.getElementById('btn-comp');
                if (d.comp == 1) {
                    compBadge.innerText = "CONTROL AUTOMÁTICO: ACTIVO";
                    compBadge.className = "vcss-badge";
                    btnComp.innerHTML = "Desactivar Control Autom&aacute;tico";
                } else {
                    compBadge.innerText = "CONTROL AUTOMÁTICO: INACTIVO";
                    compBadge.className = "vcss-badge off";
                    btnComp.innerHTML = "Activar Control Autom&aacute;tico";
                }

                // Interlock de botones de calibración: inhabilitar mientras la fuente esté encendida
                var btnCal = document.getElementById('btn-cal');
                var btnRst = document.getElementById('btn-rst');
                if (btnCal) {
                    btnCal.disabled = fuenteActiva;
                    btnCal.title = fuenteActiva ? "Apague la fuente antes de autocalibrar los shunts" : "";
                    btnCal.style.opacity = fuenteActiva ? '0.4' : '1.0';
                    btnCal.style.cursor = fuenteActiva ? 'not-allowed' : 'pointer';
                }
                if (btnRst) {
                    btnRst.disabled = fuenteActiva;
                    btnRst.title = fuenteActiva ? "Apague la fuente antes de restablecer" : "";
                    btnRst.style.opacity = fuenteActiva ? '0.4' : '1.0';
                    btnRst.style.cursor = fuenteActiva ? 'not-allowed' : 'pointer';
                }

                drawPulseWave();
                updHb();
            }).catch(function(){ updHb(); });
        }

        function updatePresetHighlight(currentAmps) {
            var presets = [
                { id: 'pre-0', val: 0.0 },
                { id: 'pre-05', val: 0.5 },
                { id: 'pre-1', val: 1.0 },
                { id: 'pre-113', val: 1.13 },
                { id: 'pre-15', val: 1.5 },
                { id: 'pre-3', val: 3.0 },
                { id: 'pre-max', val: 7.06 }
            ];
            presets.forEach(function(p){
                var el = document.getElementById(p.id);
                if(!el) return;
                var diff = Math.abs(currentAmps - p.val);
                if(diff < 0.05 || (p.val >= 7.0 && currentAmps >= 6.8)){
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
        }

        function onAmpInput(val) {
            isDragging = true;
            document.getElementById('amp-bits').innerText = val;
            var a = ((val / 4095.0) * 7.06).toFixed(2);
            document.getElementById('amp-calc').innerText = a;
            var calcEl = document.getElementById('amp-calc2');
            if(calcEl) calcEl.innerText = a;
            updatePresetHighlight(parseFloat(a));
            drawPulseWave();
            sendParam("a", val, 0);
        }

        
        function drawPulseWave(){
            var cv = document.getElementById('wave-canvas');
            if(!cv) return;
            var ctx = cv.getContext('2d');
            var w = cv.width, h = cv.height;
            ctx.clearRect(0, 0, w, h);
            
            var isDark = (document.documentElement.getAttribute('data-theme') !== 'light');
            var gridColor = isDark ? 'rgba(78, 201, 176, 0.15)' : 'rgba(0, 95, 184, 0.15)';
            var traceColor = isDark ? '#4ec9b0' : '#005fb8';
            var textColor = isDark ? '#858585' : '#666666';

            // Retícula métrica técnica (10x6)
            var numDivX = 10, numDivY = 6;
            var stepX = w / numDivX, stepY = h / numDivY;
            
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            for(var x = stepX; x < w; x += stepX){
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
            }
            for(var y = stepY; y < h; y += stepY){
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
            }
            
            // Eje base (cero)
            var padBottom = 16, padTop = 18;
            var yZero = h - padBottom;
            ctx.strokeStyle = gridColor;
            ctx.beginPath(); ctx.moveTo(0, yZero); ctx.lineTo(w, yZero); ctx.stroke();
            
            var freq = parseInt(document.getElementById('slide-freq') ? document.getElementById('slide-freq').value : 10) || 10;
            var duty = parseInt(document.getElementById('slide-duty') ? document.getElementById('slide-duty').value : 50) || 50;
            var curBits = parseInt(document.getElementById('slide-amp') ? document.getElementById('slide-amp').value : 1024) || 0;
            var aCalc = ((curBits / 4095.0) * 7.06) || 0.0;
            
            var scaleMax = (aCalc > 3.8) ? 7.06 : 4.0;
            var availableHeight = yZero - padTop;
            var pulseHeight = (aCalc / scaleMax) * availableHeight;
            if(pulseHeight < 0) pulseHeight = 0;
            if(pulseHeight > availableHeight) pulseHeight = availableHeight;
            var yHigh = yZero - pulseHeight;
            
            var periodMs = (1000.0 / freq);
            var tonMs = periodMs * (duty / 100.0);
            var toffMs = periodMs - tonMs;
            var statsEl = document.getElementById('wave-stats');
            if(statsEl) statsEl.innerText = 'T = ' + periodMs.toFixed(1) + ' ms | t_on = ' + tonMs.toFixed(1) + ' ms | t_off = ' + toffMs.toFixed(1) + ' ms';
            
            var numCycles = Math.max(1.2, Math.min(16.0, 1.0 + Math.pow(freq / 100.0, 0.75) * 14.0));
            var cycleWidth = w / numCycles;
            var highWidth = cycleWidth * (duty / 100.0);
            
            ctx.beginPath();
            ctx.moveTo(0, yZero);
            for(var c = 0; c < numCycles + 1; c++){
                var startX = c * cycleWidth;
                var downX = startX + highWidth;
                var endX = startX + cycleWidth;
                
                ctx.lineTo(startX, yZero);
                ctx.lineTo(startX, yHigh);
                ctx.lineTo(downX, yHigh);
                ctx.lineTo(downX, yZero);
                ctx.lineTo(endX, yZero);
            }
            
            ctx.strokeStyle = traceColor;
            ctx.lineWidth = 1.8;
            ctx.stroke();
            
            ctx.fillStyle = textColor;
            ctx.font = '10px Consolas, monospace';
            ctx.fillText('CH1: ' + (scaleMax / 4.0 * 1.0).toFixed(1) + ' A/DIV', 8, 13);
            ctx.fillText('0.00 A', 8, h - 4);
            if(aCalc > 0.05){
                ctx.fillStyle = traceColor;
                ctx.fillText('\u25b2 ' + aCalc.toFixed(2) + ' A', 8, yHigh - 4 > 14 ? yHigh - 4 : 24);
            }
        }

            for(var y = stepY; y < h; y += stepY){
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
            }
            
            // Sub-ticks centrales tipo mira de calibración CRT
            var midX = w / 2, midY = h / 2;
            ctx.strokeStyle = 'rgba(74, 222, 128, 0.35)';
            for(var sx = 0; sx < w; sx += (stepX / 5)){
                ctx.beginPath(); ctx.moveTo(sx, midY - 2); ctx.lineTo(sx, midY + 2); ctx.stroke();
            }
            for(var sy = 0; sy < h; sy += (stepY / 5)){
                ctx.beginPath(); ctx.moveTo(midX - 2, sy); ctx.lineTo(midX + 2, sy); ctx.stroke();
            }
            
            // Eje base (cero)
            var padBottom = 16, padTop = 18;
            var yZero = h - padBottom;
            ctx.strokeStyle = 'rgba(74, 222, 128, 0.4)';
            ctx.beginPath(); ctx.moveTo(0, yZero); ctx.lineTo(w, yZero); ctx.stroke();
            
            // Parámetros actuales
            var freq = parseInt(document.getElementById('slide-freq') ? document.getElementById('slide-freq').value : 10) || 10;
            var duty = parseInt(document.getElementById('slide-duty') ? document.getElementById('slide-duty').value : 50) || 50;
            var aCalc = parseFloat(document.getElementById('amp-calc') ? document.getElementById('amp-calc').innerText : 1.13) || 0.0;
            
            updatePresetHighlight(aCalc);
            
            // Escala vertical calibrada (rango 0 a 4.0 A estándar, o 7.06 A extendido)
            var scaleMax = (aCalc > 3.8) ? 7.06 : 4.0;
            var availableHeight = yZero - padTop;
            var pulseHeight = (aCalc / scaleMax) * availableHeight;
            if(pulseHeight < 0) pulseHeight = 0;
            if(pulseHeight > availableHeight) pulseHeight = availableHeight;
            var yHigh = yZero - pulseHeight;
            
            // Rótulo estadístico OSD
            var periodMs = (1000.0 / freq);
            var tonMs = periodMs * (duty / 100.0);
            var toffMs = periodMs - tonMs;
            var statsEl = document.getElementById('wave-stats');
            if(statsEl) statsEl.innerText = 'T = ' + periodMs.toFixed(1) + ' ms | t_on = ' + tonMs.toFixed(1) + ' ms | t_off = ' + toffMs.toFixed(1) + ' ms';
            
            // Frecuencia dinámica: número de ciclos visibles según frecuencia
            var numCycles = Math.max(1.2, Math.min(16.0, 1.0 + Math.pow(freq / 100.0, 0.75) * 14.0));
            var cycleWidth = w / numCycles;
            var highWidth = cycleWidth * (duty / 100.0);
            
            // Trazo de onda cuadrada
            ctx.beginPath();
            ctx.moveTo(0, yZero);
            for(var c = 0; c < numCycles + 1; c++){
                var startX = c * cycleWidth;
                var downX = startX + highWidth;
                var endX = startX + cycleWidth;
                
                ctx.lineTo(startX, yZero);
                ctx.lineTo(startX, yHigh);
                ctx.lineTo(downX, yHigh);
                ctx.lineTo(downX, yZero);
                ctx.lineTo(endX, yZero);
            }
            
            // Resplandor del haz de fósforo verde CRT (Bloom)
            ctx.strokeStyle = '#22c55e';
            ctx.lineWidth = 3.2;
            ctx.shadowColor = '#4ade80';
            ctx.shadowBlur = 9;
            ctx.stroke();
            
            // Núcleo brillante del haz de electrones
            ctx.strokeStyle = '#bbf7d0';
            ctx.lineWidth = 1.1;
            ctx.shadowBlur = 0;
            ctx.stroke();
            
            // Rótulos OSD en pantalla fósforo verde
            ctx.fillStyle = '#86efac';
            ctx.font = '9px ui-monospace, SFMono-Regular, Menlo, monospace';
            ctx.fillText('CH1: ' + (scaleMax / 4.0 * 1.0).toFixed(1) + ' A/DIV', 8, 12);
            ctx.fillText('0.00 A', 8, h - 4);
            if(aCalc > 0.05){
                ctx.fillText('\u25b2 ' + aCalc.toFixed(2) + ' A', 8, yHigh - 4 > 14 ? yHigh - 4 : 22);
            }
        }

        function onAmpChange(val) {
            onAmpInput(val);
            sendParam("a", val, 1);
            setTimeout(function(){ isDragging = false; }, 300);
        }

        function setPreset(amps) {
            var val;
            if(amps >= 7.0) {
                val = 4095;
            } else if(amps <= 0.01) {
                val = 0;
            } else {
                val = Math.round((amps / 7.06) * 4095.0);
            }
            if(val > 4095) val = 4095;
            if(val < 0) val = 0;
            document.getElementById('slide-amp').value = val;
            onAmpChange(val);
            var lbl = (amps >= 7.0) ? 'M\u00c1X (7.06 A)' : (amps <= 0.01 ? '0.00 A' : amps.toFixed(2) + ' A');
            showToast('Consigna: ' + lbl, 'info');
        }

        function sendParam(param, val, save) {
            var s = (save !== undefined) ? ('&s=' + save) : '';
            fetch('/set_f?p=' + param + '&v=' + val + s).then(function(){
                loadFuenteData();
            });
        }

        function setModo(modo) {
            fetch('/modo_f?v=' + modo).then(function(){
                showToast(modo==1?'Modo Pulsado activado':'Modo DC activado','info');
                loadFuenteData();
            });
        }

        function togglePower() {
            var nuevoEstado = fuenteActiva ? 0 : 1;
            fetch('/act_f?run=' + nuevoEstado).then(function(r){
                if(r.status === 403){
                    showToast('&#9888; Bloqueado por Interlock — Apague el pH primero','err');
                } else {
                    showToast(nuevoEstado==1?'Fuente ENCENDIDA':'Fuente APAGADA','ok');
                }
                loadFuenteData();
            }).catch(function(){showToast('Error de comunicaci\u00f3n','err');});
        }

        function toggleComp() {
            var nuevoComp = compActivo ? 0 : 1;
            fetch('/set_comp_f?v=' + nuevoComp).then(function(){
                showToast(nuevoComp==1?'Control Autom\u00e1tico activado':'Control Autom\u00e1tico desactivado','info');
                loadFuenteData();
            });
        }

        function calibrarVCSS() {
            if (fuenteActiva) {
                showToast('&#9888; Calibraci\u00f3n bloqueada: Apague la fuente antes de autocalibrar los shunts', 'err');
                return;
            }
            if(!confirm("¿Iniciar auto-calibración de corriente?\nSe aplicará una corriente de prueba de 1.50 A durante 1 segundo para calibrar los sensores.")) return;
            var btn=document.getElementById('btn-cal');
            btn.disabled=true;btn.innerHTML="<span class='spin'></span> Calibrando...";
            fetch('/cal_vcss').then(function(r){
                if (r.status === 403) {
                    return r.json().then(function(errJson){ throw new Error(errJson.err || 'Bloqueado por interlock'); });
                }
                return r.json();
            }).then(function(res){
                if(res.ok == 1){
                    showToast('&#10003; Calibraci\u00f3n exitosa — Gm: '+res.gm.toFixed(4),'ok');
                } else {
                    showToast('&#10007; Error: ' + (res.err || 'Corriente fuera de rango'),'err');
                }
                loadFuenteData();
            }).catch(function(err){
                showToast(err.message || 'Error de comunicaci\u00f3n durante calibraci\u00f3n','err');
            }).finally(function(){
                btn.disabled=false;btn.innerHTML="Auto-Calibrar";
                loadFuenteData();
            });
        }

        function resetCalibrarVCSS() {
            if (fuenteActiva) {
                showToast('&#9888; Operación bloqueada: Apague la fuente antes de restablecer', 'err');
                return;
            }
            if(!confirm("¿Restablecer a la ganancia predeterminada (2.00 S)?\nEsto sobreescribe en Flash NVS el factor a 1.0000 y fija la transconductancia nominal.")) return;
            var btn=document.getElementById('btn-rst');
            btn.disabled=true;btn.innerHTML="<span class='spin'></span> Restableciendo...";
            fetch('/reset_cal_vcss').then(function(r){
                if (r.status === 403) {
                    return r.json().then(function(errJson){ throw new Error(errJson.err || 'Bloqueado por interlock'); });
                }
                return r.json();
            }).then(function(res){
                if(res.ok == 1){
                    showToast('&#10003; Ganancia predeterminada restablecida (2.000 S)','ok');
                } else {
                    showToast('&#10007; Error: ' + (res.err || 'Operación rechazada'), 'err');
                }
                loadFuenteData();
            }).catch(function(err){
                showToast(err.message || 'Error de comunicaci\u00f3n','err');
            }).finally(function(){
                btn.disabled=false;btn.innerHTML="Ganancia Predeterminada";
                loadFuenteData();
            });
        }

        setInterval(loadFuenteData, 1500); loadFuenteData();
        setInterval(updHb, 1000);
    
</script>
)rawliteral";

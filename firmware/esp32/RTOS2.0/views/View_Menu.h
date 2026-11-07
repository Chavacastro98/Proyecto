#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MENÚ PRINCIPAL Y DASHBOARD GENERAL (View_Menu.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Métrica ambiental con números tabulares monoespaciados de alta legibilidad.
 *   • Enlaces a procesos industriales en tarjetas sólidas sin resplandores de neón.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_MENU[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Hub de Operaci&oacute;n &middot; RTOS 2.0</title>
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
            display:flex;
            align-items:center;
            justify-content:center;
            padding:16px 14px;
            transition:background 0.2s ease, color 0.2s ease;
        }
                /* Responsive Layout: PC / Desktop vs Móvil */
        .container{
            width:100%;
            max-width:960px;
            margin:0 auto;
            transition:max-width 0.2s ease;
        }

        .content-grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:16px;
            margin-top:10px;
            text-align:left;
        }

        .section-col{
            display:flex;
            flex-direction:column;
            gap:8px;
        }

        .section-hdr{
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:700;
            letter-spacing:0.8px;
            text-transform:uppercase;
            font-family:Consolas,monospace;
            display:flex;
            align-items:center;
            gap:8px;
            margin-bottom:2px;
        }
        .section-hdr::after{
            content:'';
            flex:1;
            height:1px;
            background:var(--ui-border-subtle);
        }

        @media(max-width:768px){
            .container{max-width:520px;}
            .content-grid{
                grid-template-columns:1fr;
                gap:14px;
            }
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

        /* Menu Card */
        .menu-card{
            background:var(--ui-panel);
            padding:20px;
            border-radius:4px;
            border:1px solid var(--ui-border);
            border-top:2px solid var(--accent-primary);
            text-align:center;
        }

        /* Top Bar */
        .top-bar{
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:12px;
            padding-bottom:10px;
            border-bottom:1px solid var(--ui-border-subtle);
        }
        .sys-badge{
            display:inline-flex;
            align-items:center;
            gap:6px;
            font-size:0.7em;
            padding:3px 8px;
            border-radius:2px;
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border:1px solid var(--metro-ok-border);
            font-weight:700;
            letter-spacing:0.4px;
            font-family:Consolas,monospace;
        }
        .sys-badge .dot{
            width:6px;
            height:6px;
            border-radius:2px;
            background:var(--metro-ok);
        }
        .sys-badge.offline{
            background:var(--metro-err-bg);
            color:var(--metro-err);
            border-color:var(--metro-err-border);
        }
        .sys-badge.offline .dot{
            background:var(--metro-err);
        }
        .chip-tag{
            font-size:0.68em;
            color:var(--accent-primary);
            font-weight:700;
            letter-spacing:0.4px;
            background:var(--disp-panel);
            padding:3px 8px;
            border-radius:2px;
            border:1px solid var(--ui-border);
            font-family:Consolas,monospace;
        }

        /* Brand Header */
        .brand-header{
            display:flex;
            align-items:center;
            justify-content:center;
            gap:14px;
            margin-bottom:6px;
        }
        .brand-text{text-align:left;}
        .brand-text h1{
            font-size:1.4em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:0.4px;
            margin:0 0 2px 0;
            line-height:1.2;
        }
        .brand-text .sub-title{
            color:var(--text-muted);
            font-size:0.75em;
            font-weight:600;
            margin:0;
            font-family:Consolas,monospace;
        }
        .last-update{
            color:var(--text-muted);
            font-size:0.68em;
            font-weight:600;
            margin-bottom:14px;
            font-family:Consolas,monospace;
        }

        /* FailSafe Banner */
        .failsafe-banner{
            background:var(--metro-err-bg);
            border:1px solid var(--metro-err-border);
            color:var(--metro-err);
            padding:10px 14px;
            border-radius:3px;
            margin-bottom:14px;
            font-size:0.78em;
            font-weight:700;
            display:none;
            text-align:left;
            font-family:Consolas,monospace;
        }
        .failsafe-banner button{
            margin-top:6px;
            padding:5px 10px;
            background:var(--metro-err);
            color:#fff;
            border:none;
            border-radius:2px;
            font-weight:700;
            cursor:pointer;
            font-size:0.8em;
            font-family:Consolas,monospace;
        }

        /* Environmental Box */
        .env-box{
            display:grid;
            grid-template-columns:repeat(3, 1fr);
            gap:6px;
            background:var(--disp-panel);
            padding:10px 8px;
            border-radius:3px;
            margin-bottom:14px;
            border:1px solid var(--ui-border);
        }
        .env-item{
            font-size:0.65em;
            color:var(--text-muted);
            font-weight:700;
            letter-spacing:0.3px;
            text-transform:uppercase;
            display:flex;
            flex-direction:column;
            align-items:center;
            gap:4px;
            font-family:Consolas,monospace;
        }
        .env-lbl{
            font-size:0.95em;
            color:var(--text-muted);
            font-weight:700;
            letter-spacing:0.4px;
        }
        .env-val{
            font-size:1.2em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:-0.5px;
            font-variant-numeric:tabular-nums;
            font-family:Consolas,monospace;
            transition:color 0.2s;
        }
        .env-val.flash{color:var(--accent-primary);}

        /* Process List */
        .proc-list{display:flex;flex-direction:column;gap:8px;}
        .btn-proc{
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:12px 14px;
            background:var(--disp-panel);
            color:var(--text-primary);
            text-decoration:none;
            border-radius:3px;
            border:1px solid var(--ui-border);
            transition:all 0.15s;
        }
        .btn-proc:hover{
            border-color:var(--accent-primary);
            background:var(--btn-hover-bg);
        }
        .btn-proc:active{transform:scale(0.99);}
        .proc-main{display:flex;align-items:center;gap:10px;text-align:left;flex:1;}
        .proc-ico{
            width:46px;
            height:30px;
            border-radius:2px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:0.75em;
            font-weight:700;
            font-family:Consolas,monospace;
            letter-spacing:0.5px;
            flex-shrink:0;
            background:var(--ui-subpanel);
            border:1px solid var(--ui-border);
        }
        .ico-fuente{color:var(--accent-primary);}
        .ico-termico{color:var(--metro-warn);}
        .ico-ph{color:var(--metro-ok);}
        .proc-info h3{
            font-size:0.88em;
            font-weight:700;
            color:var(--text-primary);
            letter-spacing:0.1px;
        }
        .proc-info p{
            font-size:0.68em;
            color:var(--text-muted);
            margin-top:2px;
            font-family:Consolas,monospace;
        }
        .proc-right{display:flex;flex-direction:column;align-items:flex-end;gap:3px;}
        .proc-badge{
            font-size:0.68em;
            padding:2px 6px;
            border-radius:2px;
            font-weight:700;
            letter-spacing:0.3px;
            white-space:nowrap;
            background:var(--ui-panel);
            color:var(--accent-primary);
            border:1px solid var(--ui-border);
            font-family:Consolas,monospace;
        }
        .proc-live{
            font-size:0.68em;
            font-weight:700;
            color:var(--text-muted);
            white-space:nowrap;
            font-variant-numeric:tabular-nums;
            font-family:Consolas,monospace;
            transition:color 0.2s;
        }
        .proc-live.active{color:var(--metro-ok);}

        /* Separator */
        .sep{
            height:1px;
            background:var(--ui-border-subtle);
            margin:14px 0 12px;
        }

        /* Tools Grid */
        .tools-grid{display:flex;flex-direction:column;gap:6px;}
        .btn-tool{
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:10px 14px;
            background:var(--disp-panel);
            color:var(--text-secondary);
            text-decoration:none;
            border-radius:3px;
            border:1px solid var(--ui-border);
            transition:all 0.15s;
            font-size:0.78em;
            font-weight:700;
            font-family:Consolas,monospace;
        }
        .btn-tool:hover{
            border-color:var(--accent-primary);
            background:var(--btn-hover-bg);
            color:var(--text-primary);
        }
        .btn-tool:active{transform:scale(0.99);}
        .tool-left{display:flex;align-items:center;gap:10px;}
        .tool-tag{
            font-family:Consolas,monospace;
            font-size:0.72em;
            font-weight:700;
            padding:2px 6px;
            border-radius:2px;
            background:var(--ui-subpanel);
            border:1px solid var(--ui-border);
            color:var(--text-muted);
            min-width:54px;
            text-align:center;
            letter-spacing:0.4px;
        }

        /* Footer */
        .ver-foot{
            margin-top:16px;
            padding-top:12px;
            border-top:1px solid var(--ui-border-subtle);
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:600;
            display:flex;
            align-items:center;
            justify-content:space-between;
            font-family:Consolas,monospace;
        }
        .dev-by{
            color:var(--accent-primary);
            font-weight:700;
        }

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

        @media(max-width:440px){
            .menu-card{padding:16px 12px;}
            .ver-foot{flex-direction:column;gap:6px;}
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

        <div class='menu-card'>
            <div class='top-bar'>
                <div class='sys-badge' id='sys-badge'><span class='dot'></span>Simulador RTOS 2.0</div>
                <div class='chip-tag'>ESP32-S3 Dual-Core</div>
            </div>

            <div class='brand-header'>
                <svg class='brand-icon' viewBox="0 0 120 120" width="46" height="46" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="shieldG" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#2a2d32"/>
                            <stop offset="100%" stop-color="#141518"/>
                        </linearGradient>
                        <linearGradient id="fluidG" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#104e5b" stop-opacity="0.8"/>
                            <stop offset="100%" stop-color="#0a2a32" stop-opacity="0.95"/>
                        </linearGradient>
                    </defs>
                    <!-- Ondas Wi-Fi -->
                    <g stroke="#38bdf8" stroke-linecap="round" fill="none">
                        <path d="M 40 12 A 28 28 0 0 1 80 12" stroke-width="2.5" opacity="0.45"/>
                        <path d="M 46 18 A 20 20 0 0 1 74 18" stroke-width="2.5" opacity="0.75"/>
                        <path d="M 52 24 A 12 12 0 0 1 68 24" stroke-width="2.5"/>
                        <circle cx="60" cy="28" r="2" fill="#38bdf8"/>
                    </g>
                    <!-- Pads ESP32 -->
                    <g fill="#d7ba7d">
                        <rect x="14" y="46" width="3" height="5" rx="1"/>
                        <rect x="14" y="56" width="3" height="5" rx="1"/>
                        <rect x="14" y="66" width="3" height="5" rx="1"/>
                        <rect x="14" y="76" width="3" height="5" rx="1"/>
                        <rect x="14" y="86" width="3" height="5" rx="1"/>
                        <rect x="103" y="46" width="3" height="5" rx="1"/>
                        <rect x="103" y="56" width="3" height="5" rx="1"/>
                        <rect x="103" y="66" width="3" height="5" rx="1"/>
                        <rect x="103" y="76" width="3" height="5" rx="1"/>
                        <rect x="103" y="86" width="3" height="5" rx="1"/>
                    </g>
                    <!-- Chasis ESP32 -->
                    <rect x="17" y="34" width="86" height="78" rx="4" fill="#0d1117" stroke="#30363d" stroke-width="1.5"/>
                    <rect x="21" y="46" width="78" height="63" rx="3" fill="url(#shieldG)" stroke="#484f58" stroke-width="1.5"/>
                    <rect x="25" y="50" width="70" height="55" rx="3" fill="#0a0c10" stroke="#21262d" stroke-width="1.2"/>
                    <!-- Onda Cuadrada VCSS -->
                    <path d="M 28 58 H 36 V 52 H 46 V 58 H 56 V 52 H 66 V 58 H 76 V 52 H 84 V 58 H 92" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" fill="none"/>
                    <!-- Tina y Electrolito -->
                    <path d="M 33 66 V 96 A 4 4 0 0 0 37 100 H 83 A 4 4 0 0 0 87 96 V 66" stroke="#4ec9b0" stroke-width="1.8" fill="none"/>
                    <path d="M 34 74 C 46 72, 52 76, 64 74 C 76 72, 80 76, 86 74 V 96 A 3 3 0 0 1 83 99 H 37 A 3 3 0 0 1 34 96 Z" fill="url(#fluidG)"/>
                    <!-- Ánodo (+) y Cátodo (-) -->
                    <rect x="41" y="62" width="5.5" height="32" rx="1.5" fill="#e06c75"/>
                    <rect x="58" y="62" width="6.5" height="32" rx="1.5" fill="#61afef"/>
                    <rect x="56.5" y="68" width="1.5" height="24" fill="#98c379"/>
                    <!-- Termómetro -->
                    <rect x="74.5" y="64" width="4" height="26" rx="2" fill="#1e2024" stroke="#d7ba7d" stroke-width="1"/>
                    <circle cx="76.5" cy="93" r="4.5" fill="#1e2024" stroke="#d7ba7d" stroke-width="1"/>
                    <rect x="75.5" y="75" width="2" height="15" fill="#d7ba7d"/>
                    <circle cx="76.5" cy="93" r="3.2" fill="#d7ba7d"/>
                </svg>
                <div class='brand-text'>
                    <h1>ELECTRODO-32</h1>
                    <div class='sub-title'>Sistema de Electrodeposici&oacute;n &middot; RTOS 2.0</div>
                </div>
            </div>
            <div class='last-update' id='last-upd'>Conectado (Simulado)</div>
            
            <div class='failsafe-banner' id='fs-box'>
                <div><b>[FAIL-SAFE] PARADA ACTIVADA:</b> <span id='fs-reason'></span></div>
                <button onclick='resetFailSafe()'>DESBLOQUEAR SISTEMA</button>
            </div>

            <div class='env-box'>
                <div class='env-item'>
                    <span class='env-lbl'>TEMP. AMBIENTE</span>
                    <span class='env-val' id='amb_t'>24.6 &deg;C</span>
                </div>
                <div class='env-item'>
                    <span class='env-lbl'>HUMEDAD</span>
                    <span class='env-val' id='amb_h'>48 %</span>
                </div>
                <div class='env-item'>
                    <span class='env-lbl'>PRESI&Oacute;N</span>
                    <span class='env-val' id='amb_p'>1013 hPa</span>
                </div>
            </div>

                                    <div class='content-grid'>
                <!-- Columna Izquierda: Procesos Principales -->
                <div class='section-col'>
                    <div class='section-hdr'>PROCESOS DE CONTROL</div>
                    <div class='proc-list'>
                        <a href='fuente.html' class='btn-proc'>
                            <div class='proc-main'>
                                <div class='proc-ico ico-fuente'>VCSS</div>
                                <div class='proc-info'>
                                    <h3>Salida de Corriente</h3>
                                </div>
                            </div>
                            <div class='proc-right'>
                                <span class='proc-badge'>Entrar &rarr;</span>
                                <span class='proc-live active' id='live-fuente'>2.40 A DC</span>
                            </div>
                        </a>

                        <a href='termico.html' class='btn-proc'>
                            <div class='proc-main'>
                                <div class='proc-ico ico-termico'>TEMP</div>
                                <div class='proc-info'>
                                    <h3>Control T&eacute;rmico</h3>
                                </div>
                            </div>
                            <div class='proc-right'>
                                <span class='proc-badge'>Entrar &rarr;</span>
                                <span class='proc-live active' id='live-termico'>2/4 tinas activas</span>
                            </div>
                        </a>

                        <a href='ph.html' class='btn-proc'>
                            <div class='proc-main'>
                                <div class='proc-ico ico-ph'>pH</div>
                                <div class='proc-info'>
                                    <h3>M&oacute;dulo de pH</h3>
                                </div>
                            </div>
                            <div class='proc-right'>
                                <span class='proc-badge'>Entrar &rarr;</span>
                                <span class='proc-live active' id='live-ph'>pH: 7.04</span>
                            </div>
                        </a>
                    </div>
                </div>

                <!-- Columna Derecha: Sistema y Diagnóstico -->
                <div class='section-col'>
                    <div class='section-hdr'>SISTEMA Y DIAGN&Oacute;STICO</div>
                    <div class='tools-grid'>
                        <a href='sensores.html' class='btn-tool'>
                            <div class='tool-left'>
                                <span class='tool-tag'>SENSOR</span>
                                <span>Estado de Sensores</span>
                            </div>
                            <span>&rarr;</span>
                        </a>
                        <a href='wifi.html' class='btn-tool'>
                            <div class='tool-left'>
                                <span class='tool-tag'>WIFI</span>
                                <span>Red Wi-Fi</span>
                            </div>
                            <span>&rarr;</span>
                        </a>
                        <a href='consola.html' class='btn-tool'>
                            <div class='tool-left'>
                                <span class='tool-tag'>LOG</span>
                                <span>Consola de Diagn&oacute;stico</span>
                            </div>
                            <span>&rarr;</span>
                        </a>
                        <a href='update.html' class='btn-tool'>
                            <div class='tool-left'>
                                <span class='tool-tag'>OTA</span>
                                <span>Actualizar Firmware</span>
                            </div>
                            <span>&rarr;</span>
                        </a>
                    </div>
                </div>
            </div>

            <div class='ver-foot'>
                <div>Firmware v<span id='fw-v'>2.0.0</span> &middot; 2026-11-06 &middot; ESP32-S3</div>
                <div class='dev-by'>Developed by Salvador&sup2; C</div>
            </div>
        </div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    
<script>
        var prevEnv = {t:null, h:null, p:null};
        var lastOk = Date.now();
        var errCount = 0;

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

        function flashVal(el){
            if(!el) return;
            el.classList.add('flash');
            setTimeout(function(){ el.classList.remove('flash'); }, 600);
        }

        function timeAgo(ms){
            var s = Math.floor(ms / 1000);
            if(s < 2) return 'Ahora mismo';
            if(s < 60) return 'Hace ' + s + 's';
            return 'Hace ' + Math.floor(s / 60) + 'm';
        }

        function updConnStatus(){
            var diff = Date.now() - lastOk;
            var badge = document.getElementById('sys-badge');
            var upd = document.getElementById('last-upd');
            if(diff > 6000){
                badge.className = 'sys-badge offline';
                badge.innerHTML = "<span class='dot'></span>Sin Conexión";
                if(upd){
                    upd.innerText = 'Sin respuesta del ESP32';
                    upd.style.color = 'var(--metro-err)';
                }
            } else {
                badge.className = 'sys-badge';
                badge.innerHTML = "<span class='dot'></span>Sistema Activo";
                if(upd){
                    upd.innerText = 'Actualizado ' + timeAgo(diff);
                    upd.style.color = 'var(--text-muted)';
                }
            }
        }

        function updEnv(){
            fetch('/data_env').then(function(r){ return r.json(); }).then(function(d){
                lastOk = Date.now();
                errCount = 0;

                var elT = document.getElementById('amb_t');
                var elH = document.getElementById('amb_h');
                var elP = document.getElementById('amb_p');

                if(prevEnv.t !== null && prevEnv.t !== d.t) flashVal(elT);
                if(prevEnv.h !== null && prevEnv.h !== d.h) flashVal(elH);
                if(prevEnv.p !== null && prevEnv.p !== d.p) flashVal(elP);

                if(elT) elT.innerHTML = d.t + ' &deg;C';
                if(elH) elH.innerText = d.h + ' %';
                if(elP) elP.innerText = d.p + ' hPa';
                prevEnv = {t: d.t, h: d.h, p: d.p};

                var fsBox = document.getElementById('fs-box');
                if(fsBox){
                    if(d.fs && d.fs.latched){
                        fsBox.style.display = 'block';
                        fsBox.className = 'failsafe-banner active';
                        document.getElementById('fs-reason').innerText = d.fs.reason;
                    } else {
                        fsBox.style.display = 'none';
                        fsBox.className = 'failsafe-banner';
                    }
                }
                updConnStatus();
            }).catch(function(){
                errCount++;
                updConnStatus();
            });
        }

        function updLiveStatus(){
            fetch('/data_f').then(function(r){ return r.json(); }).then(function(d){
                var el = document.getElementById('live-fuente');
                if(!el) return;
                if(d.act == 1){
                    el.innerText = parseFloat(d.amps).toFixed(2) + ' A ' + (d.modo == 1 ? 'Pulsada' : 'DC');
                    el.className = 'proc-live active';
                } else {
                    el.innerText = 'En reposo';
                    el.className = 'proc-live';
                }
            }).catch(function(){});

            fetch('/data_t').then(function(r){ return r.json(); }).then(function(d){
                var el = document.getElementById('live-termico');
                if(!el) return;
                var running = 0;
                for(var i = 0; i < d.length; i++){ if(d[i].run == 1) running++; }
                if(running > 0){
                    el.innerText = running + '/4 tinas activas';
                    el.className = 'proc-live active';
                } else {
                    el.innerText = 'En reposo';
                    el.className = 'proc-live';
                }
            }).catch(function(){});

            fetch('/get_ph').then(function(r){ return r.json(); }).then(function(d){
                var el = document.getElementById('live-ph');
                if(!el) return;
                if(d.on == 1){
                    var pVal = d.p !== undefined ? d.p : d.p1;
                    el.innerText = 'pH: ' + parseFloat(pVal).toFixed(2);
                    el.className = 'proc-live active';
                } else {
                    el.innerText = 'Standby';
                    el.className = 'proc-live';
                }
            }).catch(function(){});

            fetch('/wifi_status').then(function(r){ return r.json(); }).then(function(d){
                var el = document.getElementById('live-wifi');
                if(el && d.status === 'ok'){
                    el.innerText = d.stations + (d.stations === 1 ? ' disp.' : ' disp.');
                    el.style.color = 'var(--metro-ok)';
                }
            }).catch(function(){});
        }

        function resetFailSafe(){
            fetch('/failsafe_reset').then(function(){
                showToast('&#10003; Sistema desbloqueado', 'ok');
                updEnv();
            }).catch(function(){
                showToast('&#10007; Error de comunicación', 'err');
            });
        }

        function updVer(){
            fetch('/ota_check').then(function(r){ return r.json(); }).then(function(d){
                var fw = document.getElementById('fw-v');
                if(fw && d.ver) fw.innerText = d.ver;
            }).catch(function(){});
        }

        setInterval(updEnv, 3000); updEnv();
        setInterval(updLiveStatus, 4000); updLiveStatus();
        setInterval(updConnStatus, 1000);
        updVer();
</script>
</body>
</html>
)rawliteral";

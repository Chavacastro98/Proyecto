#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONTROL TÉRMICO (View_Termico.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Tipografía técnica monoespaciada con números tabulares (tabular-nums).
 *   • Cuadrícula 2x2 modular de precisión con barras métricas sin resplandores.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control T&eacute;rmico &middot; RTOS 2.0</title>
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

            --bar-track: #2a2a2a;
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

            --bar-track: #e0e0e0;
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
        }
        .hb-dot{
            width:7px;
            height:7px;
            border-radius:2px;
            background:var(--metro-ok);
        }
        .hb-dot.off{background:var(--metro-err);}

        /* Barra de Resumen / Status Toolbar */
        .sum-bar{
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:8px 14px;
            margin-bottom:14px;
            background:var(--ui-panel);
            border-radius:3px;
            border:1px solid var(--ui-border);
            font-size:0.75em;
            font-weight:700;
            color:var(--text-muted);
            font-family:Consolas,monospace;
        }
        .sum-pill{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:3px 8px;
            border-radius:2px;
            font-size:0.9em;
            font-weight:700;
            border:1px solid transparent;
        }
        .sum-pill.active{
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border-color:var(--metro-ok-border);
        }
        .sum-pill.idle{
            background:var(--ui-subpanel);
            color:var(--text-muted);
            border-color:var(--ui-border);
        }

        /* Botones de Control Maestro */
        .btn-group{
            display:flex;
            gap:10px;
            justify-content:center;
            margin-bottom:16px;
        }
        .btn-pwr{
            flex:1;
            max-width:260px;
            padding:10px 16px;
            cursor:pointer;
            border-radius:3px;
            border:1px solid transparent;
            font-weight:700;
            font-size:0.8em;
            transition:all 0.15s;
            letter-spacing:0.5px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-family:Consolas,monospace;
        }
        .btn-pwr:active{transform:scale(0.99);}
        .btn-act{
            background:var(--metro-ok);
            color:#ffffff;
            border-color:var(--metro-ok-border);
        }
        .btn-act:hover{filter:brightness(1.08);}
        .btn-stop{
            background:var(--metro-err);
            color:#ffffff;
            border-color:var(--metro-err-border);
        }
        .btn-stop:hover{filter:brightness(1.08);}

        /* Grid Simétrico 2x2 */
        .grid{
            display:grid;
            grid-template-columns:repeat(2, 1fr);
            gap:14px;
        }
        @media(max-width:680px){
            .grid{grid-template-columns:1fr;}
            .btn-group{flex-direction:column;}
            .btn-pwr{max-width:100%;}
        }

        /* Tarjeta de Tina Térmica */
        .card{
            background:var(--ui-panel);
            border-radius:4px;
            padding:14px 16px;
            border:1px solid var(--ui-border);
            border-left:3px solid var(--accent-primary);
            transition:border-color 0.2s;
            position:relative;
        }
        .card-head{
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:10px;
            padding-bottom:8px;
            border-bottom:1px solid var(--ui-border-subtle);
        }
        .card-name{
            font-size:0.85em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:0.2px;
        }

        /* Tendencia de Temperatura */
        .trend{
            display:inline-flex;
            align-items:center;
            gap:4px;
            font-size:0.7em;
            font-weight:700;
            padding:2px 6px;
            border-radius:2px;
            font-family:Consolas,monospace;
            border:1px solid transparent;
        }
        .trend-up{
            color:var(--metro-warn);
            background:var(--metro-warn-bg);
            border-color:var(--metro-warn-border);
        }
        .trend-down{
            color:var(--accent-primary);
            background:rgba(0, 122, 204, 0.12);
            border-color:var(--accent-primary);
        }
        .trend-stable{
            color:var(--metro-ok);
            background:var(--metro-ok-bg);
            border-color:var(--metro-ok-border);
        }

        /* Display de Temperatura */
        .temp-wrap{
            padding:6px 0 8px;
            text-align:center;
        }
        .temp-val{
            font-family:Consolas,"Cascadia Code","SF Mono",monospace;
            font-size:2.2em;
            font-weight:700;
            letter-spacing:-1px;
            font-variant-numeric:tabular-nums;
            line-height:1;
            margin-bottom:4px;
            color:var(--text-primary);
            transition:color 0.2s;
        }
        .temp-unit{
            font-size:0.5em;
            color:var(--text-muted);
            font-weight:600;
            margin-left:3px;
        }

        /* Barra de Progreso a Setpoint */
        .sp-prog-lbl{
            text-align:center;
            font-size:0.65em;
            font-weight:700;
            color:var(--text-muted);
            margin-bottom:4px;
            font-family:Consolas,monospace;
        }
        .sp-progress{
            margin:2px auto 8px;
            height:5px;
            border-radius:2px;
            background:var(--bar-track);
            overflow:hidden;
            max-width:180px;
            border:1px solid var(--ui-border);
        }
        .sp-prog-fill{
            height:100%;
            border-radius:1px;
            transition:width 0.3s ease-out, background 0.3s;
        }

        /* Barra de Potencia ZCS / PWM */
        .pwm-wrap{
            margin:8px 0 10px;
            background:var(--disp-panel);
            padding:8px 10px;
            border-radius:3px;
            border:1px solid var(--ui-border);
        }
        .pwm-lbl-row{
            display:flex;
            justify-content:space-between;
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:700;
            margin-bottom:4px;
            font-family:Consolas,monospace;
        }
        .pwm-bar-bg{
            height:5px;
            background:var(--bar-track);
            border-radius:1px;
            overflow:hidden;
            border:1px solid var(--ui-border);
        }
        .pwm-bar-fill{
            height:100%;
            background:var(--accent-primary);
            width:0%;
            transition:width 0.3s ease-out;
        }

        /* Caja de Ajuste de Setpoint */
        .sp-box{
            background:var(--disp-panel);
            padding:8px 10px;
            border-radius:3px;
            display:flex;
            align-items:center;
            justify-content:space-between;
            border:1px solid var(--ui-border);
        }
        .sp-lbl-wrap{display:flex;flex-direction:column;}
        .sp-lbl{
            font-size:0.62em;
            color:var(--text-muted);
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:0.5px;
            font-family:Consolas,monospace;
        }
        .sp-val{
            font-size:1.05em;
            font-weight:700;
            color:var(--text-primary);
            font-family:Consolas,monospace;
            font-variant-numeric:tabular-nums;
        }
        .btn-step{
            background:var(--ui-panel);
            color:var(--text-primary);
            border:1px solid var(--ui-border);
            width:28px;
            height:28px;
            border-radius:2px;
            font-weight:700;
            cursor:pointer;
            font-size:1.1em;
            display:flex;
            align-items:center;
            justify-content:center;
            transition:all 0.15s;
        }
        .btn-step:hover:not(:disabled){
            background:var(--btn-hover-bg);
            border-color:var(--accent-primary);
            color:var(--accent-primary);
        }
        .btn-step:active{transform:scale(0.96);}
        .btn-step:disabled{opacity:0.35;cursor:not-allowed;}

        /* Fila de Estado */
        .status-row{
            margin-top:10px;
            font-size:0.72em;
            font-weight:700;
            display:flex;
            align-items:center;
            justify-content:space-between;
            font-family:Consolas,monospace;
            color:var(--text-muted);
        }
        .st-pill{
            display:inline-flex;
            align-items:center;
            gap:5px;
            padding:2px 6px;
            border-radius:2px;
            font-size:0.9em;
            border:1px solid transparent;
        }
        .st-active{
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border-color:var(--metro-ok-border);
        }
        .st-standby{
            background:var(--ui-subpanel);
            color:var(--text-muted);
            border-color:var(--ui-border);
        }
        .badge-error{
            background:var(--metro-err-bg);
            color:var(--metro-err);
            border:1px solid var(--metro-err-border);
            padding:2px 6px;
            border-radius:2px;
            font-size:0.9em;
            font-weight:700;
            display:inline-flex;
            align-items:center;
            gap:4px;
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
        .toast-err{border-left:3px solid var(--metro-err);}
        .toast-warn{border-left:3px solid var(--metro-warn);}
        .toast-info{border-left:3px solid var(--accent-primary);}
    
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
                <div class='hdr-title'>Control T&eacute;rmico</div>
                <span class='hdr-sub'>REGULACIÓN TÉRMICA EN 4 TINAS</span>
            </div>
            <div class='hdr-hb'>
                <span class='hb-dot' id='hb-dot'></span>
                <span style='font-family:Consolas,monospace;font-size:0.85em;'>En l&iacute;nea</span>
            </div>
        </div>

        <div class='sum-bar'>
            <span>ESTADO GENERAL DEL SISTEMA:</span>
            <span class='sum-pill active' id='sum-pill'>&#9679; 2/4 tinas activas</span>
        </div>

        <div class='btn-group'>
            <button class='btn-pwr btn-act' onclick='toggleT(1)'>ACTIVAR CALENTAMIENTO</button>
            <button class='btn-pwr btn-stop' onclick='toggleT(0)'>PARAR SISTEMA</button>
        </div>

        <div class='grid' id='t-cards'></div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    
<script>
        var nombres = ["Limpieza (450W)", "Decapado (450W)", "Zincado (Celda Hull 18W)", "Niquelado (450W)"];
        var prevTemps = [25.0, 25.0, 25.0, 25.0];
        var lastOk = Date.now();

        var defaultData = [
            { t: 0.0, sp: 60.0, p: 0, run: 0 },
            { t: 0.0, sp: 45.0, p: 0, run: 0 },
            { t: 0.0, sp: 30.0, p: 0, run: 0 },
            { t: 0.0, sp: 55.0, p: 0, run: 0 }
        ];

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
            loadThermal();
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

        function spProgressColor(pv, sp){
            var diff = Math.abs(pv - sp);
            if(diff <= 1.0) return 'var(--metro-ok)';
            if(diff <= 5.0) return 'var(--metro-warn)';
            return 'var(--metro-err)';
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

        function renderThermal(data){
            var h = '';
            var running = 0;
            var isDark = (document.documentElement.getAttribute('data-theme') !== 'light');

            data.forEach(function(c, i){
                if(c.run == 1) running++;
                var esError = (c.t <= 0.0 || c.t >= 150.0);
                var tempDisplay = esError ? "DESC" : (c.t.toFixed(1) + '<span class="temp-unit">&deg;C</span>');
                var colorTemp = esError ? "var(--metro-err)" : 
                                (c.run == 1 ? (Math.abs(c.t - c.sp) < 1.5 ? "var(--metro-ok)" : "var(--metro-warn)") : "var(--text-muted)");
                var colorBorde = esError ? "var(--metro-err-border)" : (c.run == 1 ? "var(--metro-ok-border)" : "var(--accent-primary)");

                var diff = esError ? 0 : (c.t - prevTemps[i]);
                var tArrow = '';
                if(c.run == 1 && !esError){
                    if(diff > 0.08) tArrow = '<span class="trend trend-up">&uarr; +' + diff.toFixed(1) + '&deg;C</span>';
                    else if(diff < -0.08) tArrow = '<span class="trend trend-down">&darr; ' + diff.toFixed(1) + '&deg;C</span>';
                    else tArrow = '<span class="trend trend-stable">&rarr; Estable</span>';
                }

                var estadoHtml = esError ? '<span class="badge-error">&#9888; FALLA TERMOPAR</span>' :
                                 (c.run == 1 ? '<span class="st-pill st-active">&#9679; REGULANDO</span>' :
                                 '<span class="st-pill st-standby">&#9675; STANDBY</span>');

                var spPct = esError ? 0 : Math.min(Math.max((c.t / c.sp) * 100, 0), 100);
                var spCol = esError ? 'var(--metro-err)' : spProgressColor(c.t, c.sp);
                var spDist = esError ? '---' : (Math.abs(c.t - c.sp).toFixed(1) + '°C ' + (c.t < c.sp ? 'por debajo' : (c.t > c.sp + 1 ? 'por encima' : 'en objetivo')));

                h += '<div class="card" style="border-left-color:' + colorBorde + '">' +
                    '<div class="card-head">' +
                        '<span class="card-name">' + nombres[i] + '</span>' +
                        tArrow +
                    '</div>' +
                    '<div class="temp-wrap">' +
                        '<div class="temp-val" style="color:' + colorTemp + '">' + tempDisplay + '</div>' +
                    '</div>' +
                    '<div class="sp-bar-wrap">' +
                        '<div class="sp-bar-labels">' +
                            '<span>0&deg;C</span>' +
                            '<span>SP: ' + c.sp.toFixed(1) + '&deg;C (' + spDist + ')</span>' +
                            '<span>100&deg;C</span>' +
                        '</div>' +
                        '<div class="sp-bar-track">' +
                            '<div class="sp-bar-fill" style="width:' + spPct + '%;background:' + spCol + '"></div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="card-footer">' +
                        estadoHtml +
                        '<div class="pwr-val">' + (esError ? 0 : c.p) + '%</div>' +
                    '</div>' +
                    '<div class="pwr-bar">' +
                        '<div class="pwr-fill" style="width:' + (esError ? 0 : c.p) + '%;background:' + (c.run == 1 ? 'var(--metro-ok)' : 'var(--text-disabled)') + '"></div>' +
                    '</div>' +
                    '<div class="sp-ctrl">' +
                        '<button class="sp-btn" onclick="setSP(' + i + ',' + (c.sp - 5) + ')">-5</button>' +
                        '<button class="sp-btn" onclick="setSP(' + i + ',' + (c.sp - 1) + ')">-1</button>' +
                        '<span class="sp-lbl">SP: ' + c.sp.toFixed(0) + '&deg;C</span>' +
                        '<button class="sp-btn" onclick="setSP(' + i + ',' + (c.sp + 1) + ')">+1</button>' +
                        '<button class="sp-btn" onclick="setSP(' + i + ',' + (c.sp + 5) + ')">+5</button>' +
                    '</div>' +
                '</div>';
                if(!esError) prevTemps[i] = c.t;
            });

            document.getElementById('t-cards').innerHTML = h;

            var pill = document.getElementById('sum-pill');
            if(running > 0){
                pill.className = 'sum-pill active';
                pill.innerHTML = '&#9679; Regulando Activo (' + running + '/4)';
            } else {
                pill.className = 'sum-pill idle';
                pill.innerHTML = '&#9675; En Reposo (0/4)';
            }
        }

        function loadThermal(){
            fetch('/data_t').then(function(r){ return r.json(); }).then(function(data){
                lastOk = Date.now();
                renderThermal(data);
                updHb();
            }).catch(function(){ updHb(); });
        }

        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch('/set_t?id=' + id + '&v=' + val).then(function(r){
                if(r.status === 403) showToast('Detenga el sistema térmico primero para cambiar el setpoint.', 'warn');
                else showToast('SP T' + (id + 1) + ' = ' + val + '&deg;C', 'info');
                loadThermal();
            }); 
        }

        function toggleT(run){ 
            fetch('/act_t?run=' + run).then(function(r){
                if(r.status === 403){
                    showToast('&#9888; Bloqueado por Interlock — Apague el pH primero', 'err');
                } else {
                    showToast(run == 1 ? 'Sistema térmico ENCENDIDO' : 'Sistema térmico APAGADO', 'ok');
                }
                loadThermal();
            }); 
        }

        renderThermal(defaultData);
        setInterval(loadThermal, 2000); 
        loadThermal();
        setInterval(updHb, 1000);
    </script>
</body>
</html>
)rawliteral";

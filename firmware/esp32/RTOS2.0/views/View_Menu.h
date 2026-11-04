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
        .container{
            width:100%;
            max-width:540px;
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

        /* Title */
        h1{
            font-size:1.35em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:0.1px;
            margin-bottom:2px;
        }
        .sub-title{
            color:var(--text-muted);
            font-size:0.75em;
            font-weight:600;
            margin-bottom:4px;
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
            gap:2px;
            font-family:Consolas,monospace;
        }
        .env-item span.icon{font-size:1.1em;}
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
            width:32px;
            height:32px;
            border-radius:2px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.05em;
            flex-shrink:0;
            background:var(--ui-panel);
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
        .tool-left{display:flex;align-items:center;gap:8px;}
        .tool-left span.ico{font-size:1.1em;}

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
                <span id='theme-btn-lbl'>&#9728; Modo D&iacute;a</span>
            </button>
        </div>

        <div class='menu-card'>
            <div class='top-bar'>
                <div class='sys-badge' id='sys-badge'><span class='dot'></span>Simulador RTOS 2.0</div>
                <div class='chip-tag'>ESP32-S3 Dual-Core</div>
            </div>

            <h1>Panel de Control</h1>
            <div class='sub-title'>Sistema de Electrodeposici&oacute;n &middot; RTOS 2.0</div>
            <div class='last-update' id='last-upd'>Conectado (Simulado)</div>
            
            <div class='failsafe-banner' id='fs-box'>
                <div><b>&#9888; PARADA FAIL-SAFE ACTIVADA:</b> <span id='fs-reason'></span></div>
                <button onclick='resetFailSafe()'>DESBLOQUEAR SISTEMA</button>
            </div>

            <div class='env-box'>
                <div class='env-item'>
                    <span class='icon'>&#127777;&#65039;</span>
                    <span>Temp. Amb.</span>
                    <span class='env-val' id='amb_t'>24.6 &deg;C</span>
                </div>
                <div class='env-item'>
                    <span class='icon'>&#128167;</span>
                    <span>Humedad</span>
                    <span class='env-val' id='amb_h'>48 %</span>
                </div>
                <div class='env-item'>
                    <span class='icon'>&#129517;</span>
                    <span>Presi&oacute;n</span>
                    <span class='env-val' id='amb_p'>1013 hPa</span>
                </div>
            </div>

            <div class='proc-list'>
                <a href='fuente.html' class='btn-proc'>
                    <div class='proc-main'>
                        <div class='proc-ico ico-fuente'>&#9889;</div>
                        <div class='proc-info'>
                            <h3>Salida de Corriente</h3>
                            <p>Control VCSS &middot; DC / Pulsada</p>
                        </div>
                    </div>
                    <div class='proc-right'>
                        <span class='proc-badge'>Entrar &rarr;</span>
                        <span class='proc-live active' id='live-fuente'>2.40 A DC</span>
                    </div>
                </a>

                <a href='termico.html' class='btn-proc'>
                    <div class='proc-main'>
                        <div class='proc-ico ico-termico'>&#128293;</div>
                        <div class='proc-info'>
                            <h3>Control T&eacute;rmico</h3>
                            <p>Control PI &middot; Termopares MAX6675</p>
                        </div>
                    </div>
                    <div class='proc-right'>
                        <span class='proc-badge'>Entrar &rarr;</span>
                        <span class='proc-live active' id='live-termico'>2/4 tinas activas</span>
                    </div>
                </a>

                <a href='ph.html' class='btn-proc'>
                    <div class='proc-main'>
                        <div class='proc-ico ico-ph'>&#129514;</div>
                        <div class='proc-info'>
                            <h3>M&oacute;dulo de pH</h3>
                            <p>Sensor Dedicado Canal A1 &middot; RTOS 2.0</p>
                        </div>
                    </div>
                    <div class='proc-right'>
                        <span class='proc-badge'>Entrar &rarr;</span>
                        <span class='proc-live active' id='live-ph'>pH: 7.04</span>
                    </div>
                </a>
            </div>

            <div class='sep'></div>

            <div class='tools-grid'>
                <a href='sensores.html' class='btn-tool'>
                    <div class='tool-left'>
                        <span class='ico'>&#128269;</span>
                        <span>Estado de Sensores (I2C/SPI)</span>
                    </div>
                    <span>&rarr;</span>
                </a>
                <a href='wifi.html' class='btn-tool'>
                    <div class='tool-left'>
                        <span class='ico'>&#128246;</span>
                        <span>Red Wi-Fi SoftAP</span>
                    </div>
                    <span>&rarr;</span>
                </a>
                <a href='consola.html' class='btn-tool'>
                    <div class='tool-left'>
                        <span class='ico'>&#128187;</span>
                        <span>Consola de Diagn&oacute;stico</span>
                    </div>
                    <span>&rarr;</span>
                </a>
                <a href='update.html' class='btn-tool'>
                    <div class='tool-left'>
                        <span class='ico'>&#128230;</span>
                        <span>Actualizar Firmware (OTA)</span>
                    </div>
                    <span>&rarr;</span>
                </a>
            </div>

            <div class='ver-foot'>
                <div>Firmware v<span id='fw-v'>2.0.0 (Sensor pH Dedicado A1)</span> &middot; ESP32</div>
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
            btn.innerHTML = (th === 'dark') ? '&#9728; Modo D&iacute;a' : '&#9790; Modo Noche';
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
                    upd.innerText = '✓ Actualizado ' + timeAgo(diff);
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

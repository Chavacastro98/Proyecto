#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONFIGURACIÓN DE RED WI-FI SOFTAP (View_WiFi.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Paneles métricos rectangulares para SoftAP y credenciales NVS.
 *   • Sin desenfoques difusos ni resplandores de neón.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_WIFI[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Configuraci&oacute;n Wi-Fi &middot; RTOS 2.0</title>
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
                .container{
            width:100%;
            max-width:960px;
            margin:0 auto;
            padding:14px 14px 40px;
            transition:max-width 0.2s ease;
        }
        .wifi-grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:16px;
            align-items:start;
        }
        .wifi-col{
            display:flex;
            flex-direction:column;
            gap:12px;
        }
        @media(max-width:768px){
            .container{max-width:540px;}
            .wifi-grid{
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

        /* Status Box */
        .status-box{
            background:var(--ui-panel);
            border-radius:4px;
            padding:16px;
            margin-bottom:14px;
            border:1px solid var(--ui-border);
        }
        .status-top{
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:12px;
            padding-bottom:8px;
            border-bottom:1px solid var(--ui-border-subtle);
            flex-wrap:wrap;
            gap:8px;
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
        .chip-tag{
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:700;
            background:var(--disp-panel);
            padding:3px 8px;
            border-radius:2px;
            border:1px solid var(--ui-border);
            font-family:Consolas,monospace;
        }

        /* Live Metrics Grid */
        .metrics-grid{
            display:grid;
            grid-template-columns:repeat(auto-fit, minmax(130px, 1fr));
            gap:8px;
        }
        .metric-cell{
            background:var(--disp-panel);
            padding:10px;
            border-radius:3px;
            border:1px solid var(--ui-border);
            text-align:center;
        }
        .m-label{
            font-size:0.65em;
            color:var(--text-muted);
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:0.4px;
            margin-bottom:3px;
            font-family:Consolas,monospace;
        }
        .m-val{
            font-size:1.1em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:-0.2px;
            font-family:Consolas,monospace;
            font-variant-numeric:tabular-nums;
        }
        .m-val.highlight{color:var(--accent-primary);}
        .m-val.success{color:var(--metro-ok);}

        /* Form Box */
        .form-box{
            background:var(--ui-panel);
            border-radius:4px;
            padding:16px;
            margin-bottom:14px;
            border:1px solid var(--ui-border);
        }
        .form-title{
            font-size:0.95em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:0.1px;
            margin-bottom:2px;
        }
        .form-desc{
            font-size:0.7em;
            color:var(--text-muted);
            margin-bottom:14px;
            font-family:Consolas,monospace;
        }
        .form-group{
            margin-bottom:12px;
            text-align:left;
        }
        .form-label{
            display:block;
            font-size:0.72em;
            font-weight:700;
            color:var(--text-muted);
            margin-bottom:4px;
            text-transform:uppercase;
            letter-spacing:0.4px;
            font-family:Consolas,monospace;
        }
        .input-wrap{
            position:relative;
            display:flex;
            align-items:center;
        }
        .input-field{
            width:100%;
            padding:8px 10px;
            border-radius:3px;
            border:1px solid var(--ui-border);
            background:var(--disp-panel);
            color:var(--text-primary);
            font-size:0.85em;
            font-weight:600;
            font-family:Consolas,monospace;
            outline:none;
            transition:border-color 0.15s;
        }
        .input-field:focus{
            border-color:var(--accent-primary);
        }
        .pass-btn{
            position:absolute;
            right:6px;
            background:transparent;
            border:none;
            color:var(--text-muted);
            cursor:pointer;
            font-size:0.85em;
            padding:4px;
        }
        .pass-btn:hover{color:var(--text-primary);}
        .pass-hint{
            font-size:0.68em;
            color:var(--text-muted);
            margin-top:4px;
            display:flex;
            align-items:center;
            gap:4px;
            font-family:Consolas,monospace;
        }
        .pass-hint.invalid{color:var(--metro-err);}
        .pass-hint.valid{color:var(--metro-ok);}

        /* Button Grid */
        .btn-grid{
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:8px;
            margin-top:14px;
        }
        .btn-act{
            padding:9px 12px;
            border-radius:3px;
            font-weight:700;
            font-size:0.78em;
            cursor:pointer;
            border:1px solid transparent;
            transition:all 0.15s;
            display:inline-flex;
            align-items:center;
            justify-content:center;
            gap:6px;
            font-family:Consolas,monospace;
        }
        .btn-act:active{transform:scale(0.99);}
        .btn-save{
            background:var(--btn-bg);
            color:var(--text-primary);
            border-color:var(--accent-primary);
            grid-column:1 / -1;
        }
        .btn-save:hover{background:var(--btn-hover-bg);border-color:var(--accent-hover);color:var(--text-primary);}
        .btn-save:disabled{opacity:0.4;cursor:not-allowed;}
        .btn-reset{
            background:var(--btn-bg);
            color:var(--text-secondary);
            border-color:var(--ui-border);
        }
        .btn-reset:hover{background:var(--btn-hover-bg);color:var(--text-primary);}
        .btn-reboot{
            background:var(--metro-err);
            color:#fff;
            border-color:var(--metro-err-border);
        }
        .btn-reboot:hover{filter:brightness(1.08);}

        /* Status Banner */
        .status-msg{
            display:none;
            padding:8px 12px;
            border-radius:3px;
            font-size:0.75em;
            font-weight:700;
            margin-top:10px;
            text-align:left;
            font-family:Consolas,monospace;
        }
        .msg-ok{background:var(--metro-ok-bg);color:var(--metro-ok);border:1px solid var(--metro-ok-border);}
        .msg-err{background:var(--metro-err-bg);color:var(--metro-err);border:1px solid var(--metro-err-border);}

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
        .toast-info{border-left:3px solid var(--accent-primary);}
    
        .status-box { background: var(--ui-panel); border: 1px solid var(--ui-border); padding: 16px 20px; margin-bottom: 20px; border-radius: 4px; }
        .status-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid var(--ui-border-subtle); padding-bottom: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
        .metric-cell { background: var(--ui-subpanel); border: 1px solid var(--ui-border); padding: 10px 12px; border-radius: 2px; }
        .m-label { font-size: 0.72em; text-transform: uppercase; color: var(--text-muted); font-family: Consolas, monospace; margin-bottom: 4px; }
        .m-val { font-size: 1.15em; font-weight: 700; font-family: Consolas, monospace; font-variant-numeric: tabular-nums; color: var(--text-primary); }
        .m-val.success { color: var(--metro-ok); }
        .m-val.highlight { color: var(--accent-primary); }
        .form-box { background: var(--ui-panel); border: 1px solid var(--ui-border); padding: 20px; border-radius: 4px; }
        .form-title { font-size: 1.1em; font-weight: 700; margin-bottom: 6px; color: var(--text-primary); }
        .form-desc { font-size: 0.85em; color: var(--text-muted); margin-bottom: 18px; }
        .field-group { margin-bottom: 16px; }
        .field-label { display: block; font-size: 0.82em; font-weight: 600; margin-bottom: 6px; color: var(--text-secondary); }
        .input-wrapper { display: flex; align-items: center; position: relative; }
        .input-field { width: 100%; background: var(--disp-bg); border: 1px solid var(--ui-border); color: var(--text-primary); padding: 8px 12px; font-family: Consolas, monospace; font-size: 0.95em; border-radius: 2px; outline: none; }
        .input-field:focus { border-color: var(--accent-primary); }
        .btn-toggle-eye { background: var(--ui-subpanel); border: 1px solid var(--ui-border); border-left: none; color: var(--text-muted); padding: 8px 12px; cursor: pointer; border-radius: 0 2px 2px 0; }
        .btn-toggle-eye:hover { background: var(--btn-hover-bg); color: var(--text-primary); }
        .info-banner { display: flex; gap: 10px; background: var(--ui-subpanel); border: 1px solid var(--ui-border); padding: 12px; margin: 16px 0; border-radius: 2px; font-size: 0.82em; color: var(--text-secondary); }
        .info-banner .ico { color: var(--accent-primary); font-size: 1.2em; }
        .btn-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
        .chip-tag { font-size: 0.75em; font-family: Consolas, monospace; color: var(--text-muted); background: var(--ui-subpanel); border: 1px solid var(--ui-border); padding: 2px 8px; border-radius: 2px; }

</style>
</head>
<body>

<div class='container'>
    <!-- Header -->
    <div class='hdr'>
        <div style='display:flex;align-items:center;gap:12px;'><a href='/' class='nav-back'>&larr; Men&uacute; Principal</a><button class='theme-btn' id='theme-btn' onclick='toggleTheme()' title='Alternar Tema'><span id='theme-btn-lbl'>Modo D&iacute;a</span></button></div>
        <div style='text-align:right;'>
            <div class='hdr-title'>Red Wi-Fi SoftAP</div>
            <span class='hdr-sub'>CONFIGURACIÓN DE RED LOCAL</span>
        </div>
    </div>

    <!-- Live Status Card -->
        <div class='wifi-grid'>
        <!-- Columna 1: Estado y Telemetría Wi-Fi -->
        <div class='wifi-col'>
            <div class='status-box'>
        <div class='status-top'>
            <div class='sys-badge'><span class='dot'></span>Punto de Acceso Activo</div>
            <div class='chip-tag'>Canal 1 &middot; 2.4 GHz</div>
        </div>
        <div class='metrics-grid'>
            <div class='metric-cell'>
                <div class='m-label'>Dispositivos Conectados</div>
                <div class='m-val success' id='m-clients'>--</div>
            </div>
            <div class='metric-cell'>
                <div class='m-label'>Nombre de Red (SSID)</div>
                <div class='m-val highlight' id='m-ssid'>--</div>
            </div>
            <div class='metric-cell'>
                <div class='m-label'>Direcci&oacute;n IP Gateway</div>
                <div class='m-val' id='m-ip'>192.168.4.1</div>
            </div>
            <div class='metric-cell'>
                <div class='m-label'>Direcci&oacute;n MAC SoftAP</div>
                <div class='m-val' id='m-mac' style='font-size:0.85em;'>--</div>
            </div>
        </div>
    </div>

    <!-- Formulario de Reconfiguración -->
        </div>
        <!-- Columna 2: Parámetros y Credenciales -->
        <div class='wifi-col'>
            <div class='form-box'>
        <div class='form-title'>Reconfigurar Credenciales Wi-Fi</div>
        <div class='form-desc'>Las credenciales se almacenan permanentemente en la memoria Flash (NVS) del ESP32.</div>

        <form id='form-wifi' onsubmit='guardarWifi(event)'>
            <div class='field-group'>
                <label class='field-label'>Nuevo Nombre de Red (SSID)</label>
                <div class='input-wrapper'>
                    <input type='text' id='inp-ssid' class='input-field' maxlength='32' required placeholder='Ej. Planta_Galvanica_01'>
                </div>
            </div>

            <div class='field-group'>
                <label class='field-label'>Nueva Contrase&ntilde;a WPA2-PSK (M&iacute;nimo 8 Caracteres)</label>
                <div class='input-wrapper'>
                    <input type='password' id='inp-pass' class='input-field' minlength='8' maxlength='64' required placeholder='M&iacute;nimo 8 caracteres'>
                    <button type='button' class='btn-toggle-eye' onclick='togglePassVisual()' title='Mostrar / Ocultar'>VER</button>
                </div>
            </div>

            <div class='field-group'>
                <label class='field-label'>Token de Autorizaci&oacute;n REST</label>
                <div class='input-wrapper'>
                    <input type='text' id='inp-token' class='input-field' value='admin' required placeholder='Token de seguridad'>
                </div>
            </div>

            <div class='info-banner'>
                <span class='ico'>&#9432;</span>
                <div>
                    <b>Importante:</b> Tras guardar las credenciales, el ESP32 mantendrá la red actual hasta su próximo reinicio. Puedes pulsar <b>Reiniciar ESP32</b> a continuación para activar el nuevo nombre y contraseña inmediatamente.
                </div>
            </div>

            <div class='btn-grid'>
                <button type='submit' id='btn-submit' class='btn btn-primary'>
                    Guardar Credenciales en NVS
                </button>
                <button type='button' class='btn btn-secondary' onclick='restaurarDefecto()'>
                    <span>&#8635;</span> Valores por Defecto
                </button>
                <button type='button' class='btn btn-danger' onclick='solicitarReinicio()'>
                    Reiniciar ESP32
                </button>
            </div>
        </form>
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
    }

    function updateThemeBtn(th) {
        var btn = document.getElementById('theme-btn-lbl');
        if (!btn) return;
        btn.innerHTML = (th === 'dark') ? 'Modo D&iacute;a' : 'Modo Noche';
    }

    initTheme();


    var currentDefSSID = "Uli";
    var currentDefPass = "12345678";

    function showToast(msg, type){
        var box = document.getElementById('toast-box');
        var t = document.createElement('div');
        t.className = 'toast toast-' + (type || 'info');
        t.innerHTML = msg;
        box.appendChild(t);
        setTimeout(function(){
            t.style.animation = 'toast-out 0.3s cubic-bezier(.4,0,.2,1) forwards';
            setTimeout(function(){ if(t.parentNode) t.parentNode.removeChild(t); }, 300);
        }, 3500);
    }

    function togglePassVisual(){
        var inp = document.getElementById('inp-pass');
        inp.type = (inp.type === 'password') ? 'text' : 'password';
    }

    function cargarEstadoWifi(){
        fetch('/wifi_status')
        .then(function(res){ return res.json(); })
        .then(function(d){
            if(d.status === 'ok'){
                document.getElementById('m-clients').textContent = d.stations + (d.stations === 1 ? ' disp.' : ' disp.');
                document.getElementById('m-ssid').textContent = d.ssid || '--';
                document.getElementById('m-ip').textContent = d.ip || '192.168.4.1';
                document.getElementById('m-mac').textContent = d.mac || '--';
                
                // Si el formulario aún no ha sido editado, prellenar con los valores actuales
                var inpS = document.getElementById('inp-ssid');
                var inpP = document.getElementById('inp-pass');
                if(!inpS.dataset.touched && d.ssid){
                    inpS.value = d.ssid;
                }
                if(!inpP.dataset.touched && d.pass){
                    inpP.value = d.pass;
                }
                if(d.default_ssid) currentDefSSID = d.default_ssid;
                if(d.default_pass) currentDefPass = d.default_pass;
                if(d.token && document.getElementById('inp-token').value === '') {
                    document.getElementById('inp-token').value = d.token;
                }
            }
        })
        .catch(function(err){
            console.warn('Error consultando wifi_status:', err);
        });
    }

    // Marcar campos como tocados al escribir para evitar sobreescritura durante polling
    document.getElementById('inp-ssid').addEventListener('input', function(){ this.dataset.touched = 'true'; });
    document.getElementById('inp-pass').addEventListener('input', function(){ this.dataset.touched = 'true'; });

    function guardarWifi(ev){
        ev.preventDefault();
        var ssid = document.getElementById('inp-ssid').value.trim();
        var pass = document.getElementById('inp-pass').value;
        var token = document.getElementById('inp-token').value.trim();

        if(ssid.length < 1){
            showToast('El SSID no puede estar vac&iacute;o', 'err');
            return;
        }
        if(pass.length < 8){
            showToast('La contrase&ntilde;a debe tener al menos 8 caracteres', 'err');
            return;
        }

        var btn = document.getElementById('btn-submit');
        btn.disabled = true;
        btn.innerHTML = 'Guardando...';

        var body = 'ssid=' + encodeURIComponent(ssid) + '&pass=' + encodeURIComponent(pass);

        fetch('/wifi_cfg', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Auth-Token': token
            },
            body: body
        })
        .then(function(res){
            if(!res.ok){
                if(res.status === 401) throw new Error('Token inv&aacute;lido (401 Unauthorized)');
                throw new Error('Error ' + res.status);
            }
            return res.json();
        })
        .then(function(d){
            btn.disabled = false;
            btn.innerHTML = 'Guardar Credenciales en NVS';
            showToast(d.msg || 'Credenciales guardadas con &eacute;xito en NVS', 'ok');
            cargarEstadoWifi();
        })
        .catch(function(err){
            btn.disabled = false;
            btn.innerHTML = 'Guardar Credenciales en NVS';
            showToast('Fallo al guardar: ' + err.message, 'err');
        });
    }

    function restaurarDefecto(){
        if(confirm('¿Deseas restablecer el SSID a "' + currentDefSSID + '" y contrase\u00f1a a "' + currentDefPass + '"?')){
            document.getElementById('inp-ssid').value = currentDefSSID;
            document.getElementById('inp-pass').value = currentDefPass;
            document.getElementById('inp-ssid').dataset.touched = 'true';
            document.getElementById('inp-pass').dataset.touched = 'true';
            showToast('Valores por defecto cargados en el formulario. Pulsa Guardar para aplicar.', 'info');
        }
    }

    function solicitarReinicio(){
        if(confirm('¿Deseas reiniciar el ESP32 ahora mismo?\n\nLa conexi\u00f3n Wi-Fi se interrumpir\u00e1 moment\u00e1neamente y el microcontrolador aplicar\u00e1 las credenciales guardadas en NVS.')){
            var token = document.getElementById('inp-token').value.trim();
            showToast('Enviando comando de reinicio al ESP32...', 'info');
            fetch('/system_restart', {
                method: 'POST',
                headers: { 'X-Auth-Token': token }
            })
            .then(function(){
                showToast('ESP32 reiniciando. Reconecta tu dispositivo en 5 segundos.', 'ok');
            })
            .catch(function(){
                showToast('Comando enviado. El microcontrolador se est\u00e1 reiniciando...', 'ok');
            });
        }
    }

    // Inicialización y ciclo de polling ligero cada 3 segundos
    cargarEstadoWifi();
    setInterval(cargarEstadoWifi, 3000);

</script>
)rawliteral";

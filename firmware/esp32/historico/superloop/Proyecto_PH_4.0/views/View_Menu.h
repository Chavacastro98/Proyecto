#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MENÚ PRINCIPAL (View_Menu.h) — Versión 4.0
 * =================================================================================
 * Contiene el código HTML/CSS/JS del panel principal de navegación y
 * visualización meteorológica ambiental. Almacenado en PROGMEM (Flash).
 */

const char HTML_MENU[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control Galvanoplastia</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}
.menu-card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));padding:32px 28px;border-radius:20px;box-shadow:0 12px 40px rgba(0,0,0,0.5);width:100%;max-width:480px;border:1px solid rgba(56,189,248,0.1);text-align:center;}
.sep{height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.15),transparent);margin:16px 0 12px;}
.btn-ota{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;margin:10px 0;background:linear-gradient(135deg,rgba(30,41,59,0.6),rgba(15,23,42,0.5));color:#94a3b8;text-decoration:none;font-weight:700;border-radius:12px;border:1px solid rgba(251,191,36,0.12);transition:all 0.25s;font-size:0.82em;}
.btn-ota:hover{border-color:#fbbf24;background:linear-gradient(135deg,rgba(120,53,15,0.3),rgba(146,64,14,0.2));color:#fcd34d;transform:translateY(-2px);box-shadow:0 6px 20px rgba(251,191,36,0.15);}
.btn-ota .badge{font-size:0.7em;background:rgba(251,191,36,0.12);color:#fbbf24;padding:4px 8px;border-radius:6px;font-weight:800;}
.ver-foot{margin-top:18px;padding-top:14px;border-top:1px solid rgba(51,65,85,0.3);font-size:0.68em;color:#475569;font-weight:600;letter-spacing:0.5px;}
h2{font-size:1.4em;color:#fff;font-weight:800;letter-spacing:-0.5px;}
.sub-title{color:#64748b;font-size:0.82em;font-weight:600;margin-top:4px;margin-bottom:24px;}
.env-box{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;background:rgba(15,23,42,0.6);padding:14px;border-radius:14px;margin-bottom:24px;border:1px solid rgba(51,65,85,0.4);}
.env-item{font-size:0.68em;color:#38bdf8;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;}
.env-val{font-size:1.25em;display:block;color:#f8fafc;font-weight:800;margin-top:4px;letter-spacing:-0.5px;}
.btn-menu{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;margin:12px 0;background:linear-gradient(135deg,#1e293b,#0f172a);color:#f1f5f9;text-decoration:none;font-weight:700;border-radius:12px;border:1px solid rgba(56,189,248,0.12);transition:all 0.25s;font-size:0.9em;}
.btn-menu:hover{border-color:#38bdf8;background:linear-gradient(135deg,#1e3a8a,#1e40af);color:#fff;transform:translateY(-2px);box-shadow:0 6px 20px rgba(59,130,246,0.25);}
.btn-menu .badge{font-size:0.7em;background:rgba(56,189,248,0.15);color:#38bdf8;padding:4px 8px;border-radius:6px;font-weight:800;}
</style></head>
<body>
    <div class='menu-card'>
        <h2>Panel de Control</h2>
        <div class='sub-title'>Sistema de Electrodeposici&oacute;n</div>
        <div class='env-box'>
            <div class='env-item'>Temp. Amb.<span class='env-val' id='amb_t'>0.0 &deg;C</span></div>
            <div class='env-item'>Humedad<span class='env-val' id='amb_h'>0 %</span></div>
            <div class='env-item'>Presi&oacute;n<span class='env-val' id='amb_p'>0 hPa</span></div>
        </div>
        <a href='/termico' class='btn-menu'>Control T&eacute;rmico</a>
        <a href='/fuente' class='btn-menu'>Fuente de Corriente</a>
        <a href='/ph' class='btn-menu'>M&oacute;dulo de pH</a>
        <div class='sep'></div>
        <a href='/sensores' class='btn-ota'>Estado de Sensores</a>
        <a href='/update' class='btn-ota'>Actualizar Firmware</a>
        <div class='ver-foot'>
            <div>Firmware v<span id='fw-v'>...</span> &middot; ESP32-S3</div>
            <div style='margin-top:5px;color:#38bdf8;font-weight:700;font-size:0.95em;'>Developed by Salvador&sup2; C</div>
        </div>
    </div>
    <script>
        function updEnv(){
            fetch('/data_env').then(function(r){return r.json();}).then(function(d){
                document.getElementById('amb_t').innerHTML=d.t+' &deg;C';
                document.getElementById('amb_h').innerText=d.h+' %';
                document.getElementById('amb_p').innerText=d.p+' hPa';
            }).catch(function(){});
        }
        function updVer(){
            fetch('/ota_check').then(function(r){return r.json();}).then(function(d){
                document.getElementById('fw-v').innerText=d.ver;
            }).catch(function(){});
        }
        setInterval(updEnv, 3000); updEnv(); updVer();
    </script>
</body></html>
)rawliteral";

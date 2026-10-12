#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONFIGURACIÓN WI-FI SOFTAP (View_WiFi.h) — Versión RTOS 2.0
 * =================================================================================
 * Panel interactivo para visualizar el estado del Punto de Acceso (SoftAP) del ESP32-S3,
 * monitorear clientes/dispositivos conectados en tiempo real y reconfigurar el SSID
 * y la contraseña WPA2 guardándolos de forma permanente en memoria Flash (NVS).
 * 
 * CARACTERÍSTICAS:
 *   • Estética Glassmorphism oscura con acentos cian (#38bdf8) y esmeralda (#34d399)
 *   • Tipografía de sistema de alto rendimiento 100% offline
 *   • Visualización de clientes conectados en tiempo real con polling continuo
 *   • Formulario de actualización con validación de contraseña (mínimo 8 caracteres)
 *   • Visualizador/ocultador de contraseña con botón toggle
 *   • Botón de restablecimiento rápido a valores por defecto (Uli / 12345678)
 *   • Botón de reinicio remoto del ESP32 para aplicar cambios inmediatamente
 * 
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_WIFI[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Red Wi-Fi &middot; FreeRTOS RTOS 2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#070b14;background-image:radial-gradient(circle at 50% 0%,rgba(56,189,248,0.08) 0,transparent 50%),radial-gradient(circle at 90% 90%,rgba(52,211,153,0.05) 0,transparent 50%);color:#e2e8f0;min-height:100vh;padding:16px 14px 36px;}
.container{max-width:680px;margin:0 auto;}

/* Header - Frosted Glassmorphism */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding:16px 20px;background:rgba(15,23,42,0.65);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-radius:16px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 24px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;display:inline-flex;align-items:center;gap:6px;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Status Card - Live Network Metrics */
.status-box{background:rgba(15,23,42,0.7);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-radius:18px;padding:22px 20px;margin-bottom:18px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 10px 30px rgba(0,0,0,0.45),inset 0 1px 0 rgba(255,255,255,0.08);}
.status-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px;}
.sys-badge{display:inline-flex;align-items:center;gap:6px;font-size:0.7em;padding:4px 12px;border-radius:20px;background:rgba(52,211,153,0.12);color:#34d399;border:1px solid rgba(52,211,153,0.3);font-weight:800;letter-spacing:0.5px;text-transform:uppercase;}
.sys-badge .dot{width:7px;height:7px;border-radius:50%;background:#34d399;box-shadow:0 0 6px #34d399;animation:hb-pulse 2s ease-in-out infinite;}
@keyframes hb-pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.4;transform:scale(0.75);}}
.chip-tag{font-size:0.68em;color:#94a3b8;font-weight:700;background:rgba(2,6,23,0.6);padding:4px 10px;border-radius:8px;border:1px solid rgba(51,65,85,0.4);}

/* Live Metrics Grid */
.metrics-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:6px;}
.metric-cell{background:rgba(2,6,23,0.55);padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,0.05);text-align:center;}
.m-label{font-size:0.65em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;}
.m-val{font-size:1.15em;color:#f8fafc;font-weight:900;letter-spacing:-0.3px;font-variant-numeric:tabular-nums;word-break:break-all;}
.m-val.highlight{color:#38bdf8;}
.m-val.success{color:#34d399;}

/* Form Card */
.form-box{background:rgba(15,23,42,0.7);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-radius:18px;padding:22px 20px;margin-bottom:18px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 10px 30px rgba(0,0,0,0.45),inset 0 1px 0 rgba(255,255,255,0.08);}
.form-title{font-size:1.05em;color:#fff;font-weight:800;letter-spacing:-0.2px;margin-bottom:4px;}
.form-desc{font-size:0.75em;color:#94a3b8;margin-bottom:18px;font-weight:600;}

.field-group{margin-bottom:16px;}
.field-label{display:block;font-size:0.72em;color:#cbd5e1;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;}
.input-wrapper{position:relative;display:flex;align-items:center;}
.input-field{width:100%;padding:12px 14px;background:rgba(2,6,23,0.7);border:1px solid rgba(51,65,85,0.6);border-radius:12px;color:#f8fafc;font-size:0.92em;font-weight:700;outline:none;transition:all 0.25s;}
.input-field:focus{border-color:#38bdf8;box-shadow:0 0 0 3px rgba(56,189,248,0.2);background:rgba(2,6,23,0.9);}
.input-field::placeholder{color:#475569;font-weight:500;}

.btn-toggle-eye{position:absolute;right:10px;background:transparent;border:none;color:#64748b;font-size:1.1em;cursor:pointer;padding:6px;border-radius:6px;transition:color 0.2s;}
.btn-toggle-eye:hover{color:#38bdf8;}

/* Info Alert */
.info-banner{background:rgba(30,58,138,0.25);border:1px solid rgba(56,189,248,0.3);border-radius:12px;padding:12px 14px;margin-bottom:20px;font-size:0.75em;color:#93c5fd;line-height:1.5;display:flex;gap:10px;align-items:flex-start;}
.info-banner span.ico{font-size:1.25em;line-height:1;}

/* Buttons Toolbar */
.btn-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;}
.btn{padding:12px 18px;border-radius:12px;font-size:0.85em;font-weight:800;cursor:pointer;border:none;transition:all 0.25s;display:inline-flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;letter-spacing:0.3px;}
.btn:active{transform:scale(0.97);}
.btn-primary{background:linear-gradient(135deg,#0284c7,#2563eb);color:#fff;box-shadow:0 4px 14px rgba(37,99,235,0.35);border:1px solid rgba(56,189,248,0.25);grid-column:1 / -1;}
.btn-primary:hover{background:linear-gradient(135deg,#0369a1,#1d4ed8);box-shadow:0 6px 18px rgba(37,99,235,0.45);transform:translateY(-1px);}
.btn-secondary{background:rgba(30,41,59,0.7);color:#94a3b8;border:1px solid rgba(51,65,85,0.6);}
.btn-secondary:hover{background:#334155;color:#f1f5f9;border-color:#64748b;}
.btn-danger{background:rgba(185,28,28,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);}
.btn-danger:hover{background:rgba(220,38,38,0.35);color:#fff;border-color:#ef4444;}

/* Toast Notifications */
.toast-container{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none;}
.toast{padding:12px 18px;border-radius:12px;font-size:0.82em;font-weight:700;color:#fff;pointer-events:auto;animation:toast-in 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 8px 24px rgba(0,0,0,0.4);max-width:320px;display:flex;align-items:center;gap:8px;}
.toast-ok{background:linear-gradient(135deg,#059669,#047857);border:1px solid #34d399;}
.toast-err{background:linear-gradient(135deg,#b91c1c,#991b1b);border:1px solid #ef4444;}
.toast-info{background:linear-gradient(135deg,#1e40af,#1e3a8a);border:1px solid #38bdf8;}
@keyframes toast-in{from{opacity:0;transform:translateY(20px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
@keyframes toast-out{to{opacity:0;transform:translateY(-10px) scale(0.95);}}

@media(max-width:480px){
  .btn-grid{grid-template-columns:1fr;}
  .btn-primary{grid-column:1;}
  .metrics-grid{grid-template-columns:1fr 1fr;}
}
</style></head>
<body>
<div class='container'>
    <!-- Header -->
    <div class='hdr'>
        <a href='/' class='nav-back'>&larr; Men&uacute; Principal</a>
        <div style='text-align:right;'>
            <div class='hdr-title'>Red Wi-Fi SoftAP</div>
            <span class='hdr-sub'>ESP32-S3 FreeRTOS RTOS 2.0</span>
        </div>
    </div>

    <!-- Live Status Card -->
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
                    <button type='button' class='btn-toggle-eye' onclick='togglePassVisual()' title='Mostrar / Ocultar'>&#128065;</button>
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
                    <span>&#128190;</span> Guardar Credenciales en NVS
                </button>
                <button type='button' class='btn btn-secondary' onclick='restaurarDefecto()'>
                    <span>&#8635;</span> Valores por Defecto
                </button>
                <button type='button' class='btn btn-danger' onclick='solicitarReinicio()'>
                    <span>&#9889;</span> Reiniciar ESP32
                </button>
            </div>
        </form>
    </div>
</div>

<div class='toast-container' id='toast-box'></div>

<script>
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
        btn.innerHTML = '<span>&#8987;</span> Guardando...';

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
            btn.innerHTML = '<span>&#128190;</span> Guardar Credenciales en NVS';
            showToast(d.msg || 'Credenciales guardadas con &eacute;xito en NVS', 'ok');
            cargarEstadoWifi();
        })
        .catch(function(err){
            btn.disabled = false;
            btn.innerHTML = '<span>&#128190;</span> Guardar Credenciales en NVS';
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
</body></html>
)rawliteral";

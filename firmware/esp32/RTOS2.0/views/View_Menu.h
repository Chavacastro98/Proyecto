#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MENÚ PRINCIPAL (View_Menu.h) — Versión RTOS 2.0
 * =================================================================================
 * Panel maestro de navegación y monitoreo ambiental para el sistema de
 * electrodeposición automatizada basado en ESP32-S3 FreeRTOS Dual-Core SMP.
 * 
 * MEJORAS v2.0:
 *   • Estética Glassmorphism clásica con desenfoque de fondo y acentos cian
 *   • Tipografía offline de sistema de alto rendimiento
 *   • Heartbeat de conectividad con timestamp de última actualización
 *   • Estado en vivo de cada módulo en las tarjetas de navegación
 *   • Micro-animaciones táctiles en botones y enlaces (:active scale)
 *   • Micro-flash animado en valores ambientales al detectar cambio
 *   • Vibración CSS del banner fail-safe para mayor urgencia
 *   • Toast notifications para feedback de acciones
 * 
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_MENU[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Panel de Control &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#070b14;background-image:radial-gradient(circle at 50% 0%,rgba(56,189,248,0.08) 0,transparent 50%),radial-gradient(circle at 90% 90%,rgba(52,211,153,0.05) 0,transparent 50%);color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px 14px;}
.menu-card{background:rgba(15,23,42,0.7);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);padding:28px 24px 24px;border-radius:24px;box-shadow:0 16px 45px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.08);width:100%;max-width:520px;border:1px solid rgba(255,255,255,0.08);text-align:center;position:relative;overflow:hidden;}
.menu-card::before{content:'';position:absolute;top:-80px;right:-80px;width:180px;height:180px;background:radial-gradient(circle,rgba(56,189,248,0.12),transparent 70%);border-radius:50%;pointer-events:none;}

/* Top Bar */
.top-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.sys-badge{display:inline-flex;align-items:center;gap:6px;font-size:0.68em;padding:4px 10px;border-radius:20px;background:rgba(52,211,153,0.12);color:#34d399;border:1px solid rgba(52,211,153,0.25);font-weight:800;letter-spacing:0.5px;text-transform:uppercase;}
.sys-badge .dot{width:7px;height:7px;border-radius:50%;background:#34d399;box-shadow:0 0 6px #34d399;animation:hb-pulse 2s ease-in-out infinite;}
.sys-badge.offline{background:rgba(239,68,68,0.12);color:#f87171;border-color:rgba(239,68,68,0.25);}
.sys-badge.offline .dot{background:#ef4444;box-shadow:0 0 6px #ef4444;animation:none;}
.chip-tag{font-size:0.65em;color:#64748b;font-weight:700;letter-spacing:0.5px;background:rgba(15,23,42,0.6);padding:4px 9px;border-radius:8px;border:1px solid rgba(51,65,85,0.4);}

/* Heartbeat pulse */
@keyframes hb-pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.4;transform:scale(0.75);}}

/* Title */
h1{font-size:1.45em;color:#fff;font-weight:900;letter-spacing:-0.5px;margin-bottom:3px;}
.sub-title{color:#94a3b8;font-size:0.78em;font-weight:600;margin-bottom:6px;letter-spacing:0.3px;}
.last-update{color:#475569;font-size:0.62em;font-weight:600;margin-bottom:16px;transition:color 0.3s;}

/* FailSafe Banner */
.failsafe-banner{background:linear-gradient(135deg,rgba(185,28,28,0.35),rgba(220,38,38,0.2));border:1px solid #ef4444;color:#fca5a5;padding:12px 16px;border-radius:12px;margin-bottom:18px;font-size:0.8em;font-weight:800;display:none;text-align:left;}
.failsafe-banner.active{animation:shake 0.5s ease-in-out,pulse 2s ease-in-out infinite 0.5s;}
.failsafe-banner button{margin-top:8px;padding:7px 14px;background:#ef4444;color:#fff;border:none;border-radius:8px;font-weight:800;cursor:pointer;font-size:0.8em;transition:all 0.25s;}
.failsafe-banner button:hover{background:#dc2626;transform:scale(1.03);}
@keyframes shake{0%,100%{transform:translateX(0);}10%,30%,50%,70%,90%{transform:translateX(-3px);}20%,40%,60%,80%{transform:translateX(3px);}}

/* Environmental Bar */
.env-box{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;background:rgba(2,6,23,0.55);padding:12px 10px;border-radius:14px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.06);box-shadow:inset 0 1px 3px rgba(0,0,0,0.3);}
.env-item{font-size:0.65em;color:#64748b;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;display:flex;flex-direction:column;align-items:center;gap:3px;}
.env-item span.icon{font-size:1.15em;}
.env-val{font-size:1.3em;color:#f8fafc;font-weight:900;letter-spacing:-0.5px;font-variant-numeric:tabular-nums;transition:color 0.3s,text-shadow 0.3s;}
.env-val.flash{color:#38bdf8;text-shadow:0 0 12px rgba(56,189,248,0.6);}

/* Primary Process Cards */
.proc-list{display:flex;flex-direction:column;gap:10px;}
.btn-proc{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:rgba(30,41,59,0.7);color:#f1f5f9;text-decoration:none;border-radius:14px;border:1px solid rgba(255,255,255,0.06);transition:all 0.25s cubic-bezier(.4,0,.2,1);box-shadow:0 3px 12px rgba(0,0,0,0.25);}
.btn-proc:hover{border-color:#38bdf8;background:rgba(30,58,138,0.35);transform:translateY(-2px);box-shadow:0 8px 24px rgba(56,189,248,0.2);}
.btn-proc:active{transform:scale(0.97);}
.proc-main{display:flex;align-items:center;gap:12px;text-align:left;flex:1;}
.proc-ico{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2em;flex-shrink:0;}
.ico-fuente{background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.25);}
.ico-termico{background:rgba(249,115,22,0.12);color:#fb923c;border:1px solid rgba(249,115,22,0.25);}
.ico-ph{background:rgba(168,85,247,0.12);color:#c084fc;border:1px solid rgba(168,85,247,0.25);}
.proc-info h3{font-size:0.92em;font-weight:800;color:#fff;letter-spacing:-0.2px;}
.proc-info p{font-size:0.68em;color:#94a3b8;margin-top:2px;font-weight:600;}
.proc-right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;}
.proc-badge{font-size:0.7em;padding:4px 8px;border-radius:8px;font-weight:800;letter-spacing:0.3px;white-space:nowrap;}
.pb-fuente{background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.25);}
.pb-termico{background:rgba(249,115,22,0.12);color:#fb923c;border:1px solid rgba(249,115,22,0.25);}
.pb-ph{background:rgba(168,85,247,0.12);color:#c084fc;border:1px solid rgba(168,85,247,0.25);}
.proc-live{font-size:0.62em;font-weight:700;color:#64748b;white-space:nowrap;font-variant-numeric:tabular-nums;transition:color 0.3s;}
.proc-live.active{color:#34d399;}

/* Separator */
.sep{height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.15),transparent);margin:18px 0 14px;}

/* Tools Grid */
.tools-grid{display:flex;flex-direction:column;gap:8px;}
.btn-tool{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(15,23,42,0.55);color:#94a3b8;text-decoration:none;border-radius:12px;border:1px solid rgba(51,65,85,0.4);transition:all 0.2s;font-size:0.82em;font-weight:700;}
.btn-tool:hover{border-color:#38bdf8;background:rgba(30,41,59,0.7);color:#f1f5f9;transform:translateY(-1px);box-shadow:0 4px 14px rgba(0,0,0,0.3);}
.btn-tool:active{transform:scale(0.97);}
.tool-left{display:flex;align-items:center;gap:10px;}
.tool-left span.ico{font-size:1.15em;}

/* Footer */
.ver-foot{margin-top:20px;padding-top:14px;border-top:1px solid rgba(51,65,85,0.35);font-size:0.68em;color:#64748b;font-weight:600;display:flex;align-items:center;justify-content:space-between;}
.dev-by{color:#38bdf8;font-weight:800;letter-spacing:0.3px;}

/* Toast Notifications */
.toast-container{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none;}
.toast{padding:12px 18px;border-radius:12px;font-size:0.82em;font-weight:700;color:#fff;pointer-events:auto;animation:toast-in 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 8px 24px rgba(0,0,0,0.4);max-width:320px;display:flex;align-items:center;gap:8px;}
.toast.out{animation:toast-out 0.3s cubic-bezier(.4,0,.2,1) forwards;}
.toast-ok{background:linear-gradient(135deg,#059669,#047857);border:1px solid #34d399;}
.toast-err{background:linear-gradient(135deg,#b91c1c,#991b1b);border:1px solid #ef4444;}
.toast-warn{background:linear-gradient(135deg,#b45309,#92400e);border:1px solid #f59e0b;}
.toast-info{background:linear-gradient(135deg,#1e40af,#1e3a8a);border:1px solid #38bdf8;}
@keyframes toast-in{from{opacity:0;transform:translateY(20px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
@keyframes toast-out{to{opacity:0;transform:translateY(-10px) scale(0.95);}}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.65;}}

@media(max-width:440px){
  .menu-card{padding:20px 16px;}
  .ver-foot{flex-direction:column;gap:6px;}
  .toast-container{left:14px;right:14px;}
  .toast{max-width:100%;}
}
</style></head>
<body>
    <div class='menu-card'>
        <div class='top-bar'>
            <div class='sys-badge' id='sys-badge'><span class='dot'></span>Sistema Activo</div>
            <div class='chip-tag'>ESP32-S3 Dual-Core</div>
        </div>

        <h1>Panel de Control</h1>
        <div class='sub-title'>Sistema de Electrodeposici&oacute;n &middot; RTOS 2.0</div>
        <div class='last-update' id='last-upd'>Conectando...</div>
        
        <div class='failsafe-banner' id='fs-box'>
            <div><b>&#9888; PARADA FAIL-SAFE ACTIVADA:</b> <span id='fs-reason'></span></div>
            <button onclick='resetFailSafe()'>DESBLOQUEAR SISTEMA</button>
        </div>

        <div class='env-box'>
            <div class='env-item'>
                <span class='icon'>&#127777;&#65039;</span>
                <span>Temp. Amb.</span>
                <span class='env-val' id='amb_t'>0.0 &deg;C</span>
            </div>
            <div class='env-item'>
                <span class='icon'>&#128167;</span>
                <span>Humedad</span>
                <span class='env-val' id='amb_h'>0 %</span>
            </div>
            <div class='env-item'>
                <span class='icon'>&#129517;</span>
                <span>Presi&oacute;n</span>
                <span class='env-val' id='amb_p'>0 hPa</span>
            </div>
        </div>

        <div class='proc-list'>
            <a href='/fuente' class='btn-proc'>
                <div class='proc-main'>
                    <div class='proc-ico ico-fuente'>&#9889;</div>
                    <div class='proc-info'>
                        <h3>Salida de Corriente</h3>
                        <p>Control VCSS &middot; DC / Pulsada</p>
                    </div>
                </div>
                <div class='proc-right'>
                    <span class='proc-badge pb-fuente'>Entrar &rarr;</span>
                    <span class='proc-live' id='live-fuente'>En reposo</span>
                </div>
            </a>

            <a href='/termico' class='btn-proc'>
                <div class='proc-main'>
                    <div class='proc-ico ico-termico'>&#128293;</div>
                    <div class='proc-info'>
                        <h3>Control T&eacute;rmico</h3>
                        <p>Control PI &middot; Termopares MAX6675</p>
                    </div>
                </div>
                <div class='proc-right'>
                    <span class='proc-badge pb-termico'>Entrar &rarr;</span>
                    <span class='proc-live' id='live-termico'>En reposo</span>
                </div>
            </a>

            <a href='/ph' class='btn-proc'>
                <div class='proc-main'>
                    <div class='proc-ico ico-ph'>&#129514;</div>
                    <div class='proc-info'>
                        <h3>M&oacute;dulo de pH</h3>
                        <p>Sensor Dedicado Canal A1 &middot; RTOS 2.0</p>
                    </div>
                </div>
                <div class='proc-right'>
                    <span class='proc-badge pb-ph'>Entrar &rarr;</span>
                    <span class='proc-live' id='live-ph'>Standby</span>
                </div>
            </a>
        </div>

        <div class='sep'></div>

        <div class='tools-grid'>
            <a href='/sensores' class='btn-tool'>
                <div class='tool-left'>
                    <span class='ico'>&#128269;</span>
                    <span>Estado de Sensores</span>
                </div>
                <span>&rarr;</span>
            </a>
            <a href='/consola' class='btn-tool'>
                <div class='tool-left'>
                    <span class='ico'>&#128187;</span>
                    <span>Consola de Diagn&oacute;stico</span>
                </div>
                <span>&rarr;</span>
            </a>
            <a href='/update' class='btn-tool'>
                <div class='tool-left'>
                    <span class='ico'>&#128230;</span>
                    <span>Actualizar Firmware</span>
                </div>
                <span>&rarr;</span>
            </a>
        </div>

        <div class='ver-foot'>
            <div>Firmware v<span id='fw-v'>...</span> &middot; ESP32</div>
            <div class='dev-by'>Developed by Salvador&sup2; C</div>
        </div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    <script>
        var prevEnv={t:null,h:null,p:null};
        var lastOk=Date.now();
        var errCount=0;

        function showToast(msg, type){
            var box=document.getElementById('toast-box');
            var t=document.createElement('div');
            t.className='toast toast-'+(type||'info');
            t.innerHTML=msg;
            box.appendChild(t);
            setTimeout(function(){t.classList.add('out');setTimeout(function(){t.remove();},300);},3500);
        }

        function flashVal(el){
            el.classList.add('flash');
            setTimeout(function(){el.classList.remove('flash');},600);
        }

        function timeAgo(ms){
            var s=Math.floor(ms/1000);
            if(s<2) return 'Ahora mismo';
            if(s<60) return 'Hace '+s+'s';
            return 'Hace '+Math.floor(s/60)+'m';
        }

        function updConnStatus(){
            var diff=Date.now()-lastOk;
            var badge=document.getElementById('sys-badge');
            var upd=document.getElementById('last-upd');
            if(diff>6000){
                badge.className='sys-badge offline';
                badge.innerHTML="<span class='dot'></span>Sin Conexi\u00f3n";
                upd.innerText='Sin respuesta del ESP32';
                upd.style.color='#ef4444';
            }else{
                badge.className='sys-badge';
                badge.innerHTML="<span class='dot'></span>Sistema Activo";
                upd.innerText='\u2713 Actualizado '+timeAgo(diff);
                upd.style.color='#475569';
            }
        }

        function updEnv(){
            fetch('/data_env').then(function(r){return r.json();}).then(function(d){
                lastOk=Date.now();
                errCount=0;

                var elT=document.getElementById('amb_t');
                var elH=document.getElementById('amb_h');
                var elP=document.getElementById('amb_p');

                if(prevEnv.t!==null && prevEnv.t!==d.t) flashVal(elT);
                if(prevEnv.h!==null && prevEnv.h!==d.h) flashVal(elH);
                if(prevEnv.p!==null && prevEnv.p!==d.p) flashVal(elP);

                elT.innerHTML=d.t+' &deg;C';
                elH.innerText=d.h+' %';
                elP.innerText=d.p+' hPa';
                prevEnv={t:d.t,h:d.h,p:d.p};

                var fsBox = document.getElementById('fs-box');
                if(d.fs && d.fs.latched){
                    fsBox.style.display = 'block';
                    fsBox.className = 'failsafe-banner active';
                    document.getElementById('fs-reason').innerText = d.fs.reason;
                } else {
                    fsBox.style.display = 'none';
                    fsBox.className = 'failsafe-banner';
                }
                updConnStatus();
            }).catch(function(){
                errCount++;
                updConnStatus();
            });
        }

        function updLiveStatus(){
            fetch('/data_f').then(function(r){return r.json();}).then(function(d){
                var el=document.getElementById('live-fuente');
                if(d.act==1){
                    el.innerText=parseFloat(d.amps).toFixed(2)+' A '+(d.modo==1?'Pulsada':'DC');
                    el.className='proc-live active';
                }else{
                    el.innerText='En reposo';
                    el.className='proc-live';
                }
            }).catch(function(){});
            fetch('/data_t').then(function(r){return r.json();}).then(function(d){
                var el=document.getElementById('live-termico');
                var running=0;
                for(var i=0;i<d.length;i++){if(d[i].run==1)running++;}
                if(running>0){
                    el.innerText=running+'/4 tinas activas';
                    el.className='proc-live active';
                }else{
                    el.innerText='En reposo';
                    el.className='proc-live';
                }
            }).catch(function(){});
            fetch('/get_ph').then(function(r){return r.json();}).then(function(d){
                var el=document.getElementById('live-ph');
                if(d.on==1){
                    var pVal = d.p !== undefined ? d.p : d.p1;
                    el.innerText='pH: ' + parseFloat(pVal).toFixed(2);
                    el.className='proc-live active';
                }else{
                    el.innerText='Standby';
                    el.className='proc-live';
                }
            }).catch(function(){});
        }

        function resetFailSafe(){
            fetch('/failsafe_reset').then(function(){
                showToast('&#10003; Sistema desbloqueado','ok');
                updEnv();
            }).catch(function(){
                showToast('&#10007; Error de comunicaci\u00f3n','err');
            });
        }
        function updVer(){
            fetch('/ota_check').then(function(r){return r.json();}).then(function(d){
                document.getElementById('fw-v').innerText=d.ver;
            }).catch(function(){});
        }
        setInterval(updEnv, 3000); updEnv();
        setInterval(updLiveStatus, 4000); updLiveStatus();
        setInterval(updConnStatus, 1000);
        updVer();
    </script>
</body></html>
)rawliteral";

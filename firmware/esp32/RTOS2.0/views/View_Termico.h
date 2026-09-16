#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONTROL TÉRMICO (View_Termico.h) — Versión RTOS 2.0
 * =================================================================================
 * MEJORAS v2.0:
 *   • Distribución de tinas en cuadrícula simétrica 2x2 responsiva
 *   • Estética Glassmorphism clásica con desenfoque de fondo y acentos cian
 *   • Tipografía offline de sistema de alto rendimiento
 *   • Micro-animaciones táctiles en pulsación de botones (:active scale)
 *   • Indicador de tendencia (↑↓→) con memoria del valor anterior
 *   • Barra de progreso hacia setpoint con gradiente de color dinámico
 *   • Heartbeat de conectividad en header
 *   • Toast notifications reemplazando alert() nativos
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control T&eacute;rmico &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#070b14;background-image:radial-gradient(circle at 50% 0%,rgba(56,189,248,0.08) 0,transparent 50%),radial-gradient(circle at 90% 90%,rgba(52,211,153,0.05) 0,transparent 50%);color:#e2e8f0;min-height:100vh;padding:16px 14px 32px;}
.container{max-width:820px;margin:0 auto;}

/* Header - Classic Frosted Glassmorphism */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding:16px 20px;background:rgba(15,23,42,0.65);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-radius:16px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 8px 24px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}
.hdr-hb{display:flex;align-items:center;gap:6px;font-size:0.65em;font-weight:700;color:#475569;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 5px #34d399;animation:hb-p 2s ease-in-out infinite;}
.hb-dot.off{background:#ef4444;box-shadow:0 0 5px #ef4444;animation:none;}
@keyframes hb-p{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.7);}}

/* Summary Bar */
.sum-bar{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;margin-bottom:16px;background:rgba(15,23,42,0.65);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-radius:14px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 6px 20px rgba(0,0,0,0.25);font-size:0.78em;font-weight:700;color:#94a3b8;flex-wrap:wrap;gap:8px;}
.sum-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:800;}
.sum-pill.active{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.35);}
.sum-pill.idle{background:rgba(71,85,105,0.2);color:#94a3b8;border:1px solid #475569;}

/* Master Action Controls */
.btn-group{display:flex;gap:12px;justify-content:center;margin-bottom:20px;}
.btn-pwr{flex:1;max-width:240px;padding:14px 20px;cursor:pointer;border-radius:12px;border:none;font-weight:800;font-size:0.85em;transition:all 0.25s cubic-bezier(.4,0,.2,1);letter-spacing:0.5px;display:flex;align-items:center;justify-content:center;}
.btn-pwr:active{transform:scale(0.96);}
.btn-act{background:linear-gradient(135deg,#059669,#047857);color:#fff;box-shadow:0 4px 18px rgba(5,150,105,0.35);}
.btn-act:hover{background:linear-gradient(135deg,#10b981,#059669);transform:translateY(-1px);box-shadow:0 6px 24px rgba(5,150,105,0.45);}
.btn-stop{background:linear-gradient(135deg,#b91c1c,#991b1b);color:#fff;box-shadow:0 4px 18px rgba(185,28,28,0.35);}
.btn-stop:hover{background:linear-gradient(135deg,#dc2626,#b91c1c);transform:translateY(-1px);box-shadow:0 6px 24px rgba(220,38,38,0.45);}

/* Symmetric 2x2 Grid */
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}
@media(max-width:680px){
  .grid{grid-template-columns:1fr;}
  .btn-group{flex-direction:column;}
  .btn-pwr{max-width:100%;}
  .toast-container{left:14px;right:14px;}
}

/* Card - Classic Frosted Glassmorphism */
.card{background:rgba(15,23,42,0.65);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-radius:20px;padding:20px;border:1px solid rgba(255,255,255,0.08);box-shadow:0 12px 32px rgba(0,0,0,0.45),inset 0 1px 0 rgba(255,255,255,0.08);transition:all 0.3s cubic-bezier(.4,0,.2,1);position:relative;border-left:4px solid #38bdf8;}
.card:hover{border-color:rgba(56,189,248,0.3);transform:translateY(-2px);box-shadow:0 16px 40px rgba(0,0,0,0.55);}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.card-name{font-size:0.92em;color:#f1f5f9;font-weight:800;letter-spacing:-0.2px;}

/* Trend Arrow */
.trend{display:inline-flex;align-items:center;gap:4px;font-size:0.72em;font-weight:800;padding:3px 8px;border-radius:6px;letter-spacing:0.3px;}
.trend-up{color:#f59e0b;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.25);}
.trend-down{color:#38bdf8;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.25);}
.trend-stable{color:#34d399;background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.25);}

/* Temp Display */
.temp-wrap{padding:8px 0;text-align:center;}
.temp-val{font-size:2.4em;font-weight:900;letter-spacing:-1.5px;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:4px;transition:color 0.5s;}
.temp-unit{font-size:0.45em;color:#94a3b8;font-weight:700;margin-left:3px;}

/* SP Progress Ring */
.sp-progress{margin:4px auto 8px;height:6px;border-radius:3px;background:#1e293b;overflow:hidden;max-width:160px;}
.sp-prog-fill{height:100%;border-radius:3px;transition:width 0.5s ease-out,background 0.5s;}
.sp-prog-lbl{text-align:center;font-size:0.62em;font-weight:700;color:#64748b;margin-bottom:4px;}

/* Power Bar */
.pwm-wrap{margin:10px 0 14px;background:rgba(2,6,23,0.55);padding:8px 10px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);}
.pwm-lbl-row{display:flex;justify-content:space-between;font-size:0.68em;color:#94a3b8;font-weight:700;margin-bottom:5px;}
.pwm-bar-bg{height:6px;background:#1e293b;border-radius:3px;overflow:hidden;}
.pwm-bar-fill{height:100%;background:linear-gradient(90deg,#38bdf8,#f59e0b,#ef4444);width:0%;transition:width 0.4s ease-out;}

/* Setpoint Box */
.sp-box{background:rgba(2,6,23,0.55);padding:10px 14px;border-radius:12px;display:flex;align-items:center;justify-content:space-between;border:1px solid rgba(255,255,255,0.06);}
.sp-lbl-wrap{display:flex;flex-direction:column;}
.sp-lbl{font-size:0.65em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;}
.sp-val{font-size:1.15em;font-weight:900;color:#fff;font-variant-numeric:tabular-nums;}
.btn-step{background:#1e293b;color:#38bdf8;border:1px solid #334155;width:34px;height:34px;border-radius:8px;font-weight:900;cursor:pointer;font-size:1.1em;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.btn-step:hover:not(:disabled){background:#38bdf8;color:#0f172a;box-shadow:0 0 10px rgba(56,189,248,0.4);}
.btn-step:active{transform:scale(0.90);}
.btn-step:disabled{opacity:0.3;cursor:not-allowed;}

/* Status Row */
.status-row{margin-top:12px;font-size:0.75em;font-weight:800;display:flex;align-items:center;justify-content:space-between;}
.st-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:20px;font-size:0.72em;letter-spacing:0.3px;}
.st-active{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.st-standby{background:rgba(71,85,105,0.2);color:#94a3b8;border:1px solid #475569;}
.badge-error{background:rgba(220,38,38,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);padding:4px 10px;border-radius:8px;font-size:0.72em;font-weight:800;display:inline-flex;align-items:center;gap:6px;animation:pulse 2s infinite;}

/* Toast */
.toast-container{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none;}
.toast{padding:12px 18px;border-radius:12px;font-size:0.82em;font-weight:700;color:#fff;pointer-events:auto;animation:toast-in 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 8px 24px rgba(0,0,0,0.4);max-width:340px;}
.toast.out{animation:toast-out 0.3s forwards;}
.toast-ok{background:linear-gradient(135deg,#059669,#047857);border:1px solid #34d399;}
.toast-err{background:linear-gradient(135deg,#b91c1c,#991b1b);border:1px solid #ef4444;}
.toast-warn{background:linear-gradient(135deg,#b45309,#92400e);border:1px solid #f59e0b;}
.toast-info{background:linear-gradient(135deg,#1e40af,#1e3a8a);border:1px solid #38bdf8;}
@keyframes toast-in{from{opacity:0;transform:translateY(20px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
@keyframes toast-out{to{opacity:0;transform:translateY(-10px) scale(0.95);}}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.65;}}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <div style='text-align:center'>
                <span class='hdr-title'>Control T&eacute;rmico</span>
                <span class='hdr-sub'>4 CANALES PI &middot; TERMOPARES MAX6675 &middot; RTOS 2.0</span>
            </div>
            <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span><span id='hb-txt'>...</span></div>
        </div>

        <div class='sum-bar'>
            <span>Estado General:</span>
            <span class='sum-pill idle' id='sum-pill'>&#9675; En Reposo (0/4)</span>
        </div>

        <div class='btn-group'>
            <button class='btn-pwr btn-act' onclick='toggleT(1)'>ENCENDER SISTEMA</button>
            <button class='btn-pwr btn-stop' onclick='toggleT(0)'>APAGAR SISTEMA</button>
        </div>

        <div class='grid' id='t-cards'></div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    <script>
        var nombres = ["Limpieza (450W)", "Decapado (450W)", "Zincado (Celda Hull 18W)", "Niquelado (450W)"];
        var prevTemps = [null,null,null,null];
        var lastOk = Date.now();

        var defaultData = [
            { t: 0.0, sp: 60.0, p: 0, run: 0 },
            { t: 0.0, sp: 45.0, p: 0, run: 0 },
            { t: 0.0, sp: 30.0, p: 0, run: 0 },
            { t: 0.0, sp: 55.0, p: 0, run: 0 }
        ];

        function showToast(msg,type){var box=document.getElementById('toast-box');var t=document.createElement('div');t.className='toast toast-'+(type||'info');t.innerHTML=msg;box.appendChild(t);setTimeout(function(){t.classList.add('out');setTimeout(function(){t.remove();},300);},3500);}

        function trendArrow(i, cur){
            var prev = prevTemps[i];
            if(prev===null) return "<span class='trend trend-stable'>&rarr; ---</span>";
            var diff = cur - prev;
            if(diff > 0.3) return "<span class='trend trend-up'>&uarr; +"+diff.toFixed(1)+"&deg;</span>";
            if(diff < -0.3) return "<span class='trend trend-down'>&darr; "+diff.toFixed(1)+"&deg;</span>";
            return "<span class='trend trend-stable'>&rarr; Estable</span>";
        }

        function spProgressColor(pv, sp){
            var diff = Math.abs(pv - sp);
            if(diff <= 1.0) return '#10b981';
            if(diff <= 5.0) return '#fbbf24';
            if(pv < sp) return '#38bdf8';
            return '#ef4444';
        }

        function updHb(){
            var d=Date.now()-lastOk;
            var dot=document.getElementById('hb-dot');
            var txt=document.getElementById('hb-txt');
            if(d>6000){dot.className='hb-dot off';txt.innerText='Sin conexi\u00f3n';}
            else{dot.className='hb-dot';var s=Math.floor(d/1000);txt.innerText=s<2?'OK':'Hace '+s+'s';}
        }

        function renderThermal(data) {
            var h = '';
            var running = 0;
            data.forEach(function(c, i){
                var esError = (c.t <= 0.0 || c.t >= 150.0);
                var colorBorde = esError ? '#ef4444' : (c.run==1?'#10b981':'#38bdf8');
                var colorTemp = esError ? '#ef4444' : (c.run==1 && c.t < c.sp ? '#f59e0b' : (c.run==1 ? '#10b981' : '#38bdf8'));
                if(c.run==1 && !esError) running++;
                
                var estadoHtml = esError ? 
                    '<span class="badge-error">&#9888; FALLA TERMOPAR</span>' : 
                    (c.run==1 ? '<span class="st-pill st-active">&#9679; Activo ('+c.p+'%)</span>' : '<span class="st-pill st-standby">&#9675; En Reposo</span>');

                var tempDisplay = esError ? 'ERROR' : c.t.toFixed(1) + '<span class="temp-unit">&deg;C</span>';

                var tArrow = esError ? '' : trendArrow(i, c.t);

                var spPct = esError ? 0 : Math.min(Math.max((c.t / c.sp) * 100, 0), 100);
                var spCol = esError ? '#ef4444' : spProgressColor(c.t, c.sp);
                var spDist = esError ? '---' : (Math.abs(c.t - c.sp).toFixed(1) + '\u00b0C ' + (c.t < c.sp ? 'por debajo' : (c.t > c.sp + 1 ? 'por encima' : 'en objetivo')));

                h += '<div class="card" style="border-left-color:'+colorBorde+'">' +
                    '<div class="card-head">' +
                        '<span class="card-name">' + nombres[i] + '</span>' +
                        tArrow +
                    '</div>' +
                    '<div class="temp-wrap">' +
                        '<div class="temp-val" style="color:' + colorTemp + '">' + tempDisplay + '</div>' +
                    '</div>' +
                    '<div class="sp-prog-lbl">' + spDist + '</div>' +
                    '<div class="sp-progress"><div class="sp-prog-fill" style="width:'+spPct+'%;background:'+spCol+'"></div></div>' +
                    '<div class="pwm-wrap">' +
                        '<div class="pwm-lbl-row">' +
                            '<span>Potencia Aplicada</span>' +
                            '<span>' + c.p + '%</span>' +
                        '</div>' +
                        '<div class="pwm-bar-bg">' +
                            '<div class="pwm-bar-fill" style="width:' + c.p + '%;"></div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="sp-box">' +
                        '<div class="sp-lbl-wrap">' +
                            '<span class="sp-lbl">Setpoint</span>' +
                            '<span class="sp-val">' + c.sp.toFixed(1) + ' &deg;C</span>' +
                        '</div>' +
                        '<div style="display:flex;gap:6px;">' +
                            '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp-1) + ')">&minus;</button>' +
                            '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp+1) + ')">&plus;</button>' +
                        '</div>' +
                    '</div>' +
                    '<div class="status-row"><span>Estado:</span>' + estadoHtml + '</div>' +
                '</div>';

                if(!esError) prevTemps[i] = c.t;
            });
            document.getElementById('t-cards').innerHTML = h;

            var sumPill = document.getElementById('sum-pill');
            if(running > 0){
                sumPill.className = 'sum-pill active';
                sumPill.innerHTML = '&#9679; ' + running + '/4 tinas activas';
            } else {
                sumPill.className = 'sum-pill idle';
                sumPill.innerHTML = '&#9675; En Reposo (0/4)';
            }
        }

        function loadThermal(){
            fetch('/data_t').then(function(r){return r.json();}).then(function(data){
                lastOk = Date.now();
                renderThermal(data);
                updHb();
            }).catch(function(){ updHb(); });
        }

        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch('/set_t?id=' + id + '&v=' + val).then(function(r){
                if(r.status === 403) showToast('Detenga el sistema t\u00e9rmico primero para cambiar el setpoint.','warn');
                else showToast('SP T'+(id+1)+' = '+val+'\u00b0C','info');
                loadThermal();
            }); 
        }

        function toggleT(run){ 
            fetch('/act_t?run=' + run).then(function(r){
                if(r.status === 403){
                    showToast('&#9888; Bloqueado por Interlock — Apague el pH primero','err');
                } else {
                    showToast(run==1?'&#128293; Sistema t\u00e9rmico ENCENDIDO':'Sistema t\u00e9rmico APAGADO','ok');
                }
                loadThermal();
            }); 
        }

        renderThermal(defaultData);
        setInterval(loadThermal, 2000); 
        loadThermal();
        setInterval(updHb, 1000);
    </script>
</body></html>
)rawliteral";

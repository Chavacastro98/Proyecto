#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONTROL TÉRMICO (View_Termico.h) — Versión RTOS 1.0
 * =================================================================================
 * Panel de control y monitoreo en tiempo real para el sistema de control térmico PI
 * basado en sensores de temperatura SPI (MAX6675) y control de potencia de calentadores.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control T&eacute;rmico &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px 32px;}
.container{max-width:800px;margin:0 auto;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Master Action Controls */
.btn-group{display:flex;gap:12px;justify-content:center;margin-bottom:24px;}
.btn-pwr{flex:1;max-width:240px;padding:14px 20px;cursor:pointer;border-radius:12px;border:none;font-weight:800;font-size:0.85em;transition:all 0.25s cubic-bezier(.4,0,.2,1);letter-spacing:0.5px;display:flex;align-items:center;justify-content:center;}
.btn-act{background:linear-gradient(135deg,#059669,#047857);color:#fff;box-shadow:0 4px 18px rgba(5,150,105,0.35);}
.btn-act:hover{background:linear-gradient(135deg,#10b981,#059669);transform:translateY(-2px);box-shadow:0 6px 24px rgba(5,150,105,0.45);}
.btn-stop{background:linear-gradient(135deg,#b91c1c,#991b1b);color:#fff;box-shadow:0 4px 18px rgba(185,28,28,0.35);}
.btn-stop:hover{background:linear-gradient(135deg,#dc2626,#b91c1c);transform:translateY(-2px);box-shadow:0 6px 24px rgba(220,38,38,0.45);}

/* Grid */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;}

/* Card */
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:20px;border:1px solid rgba(56,189,248,0.1);box-shadow:0 6px 24px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);transition:all 0.3s;position:relative;border-left:4px solid #38bdf8;}
.card:hover{border-color:rgba(56,189,248,0.25);transform:translateY(-2px);box-shadow:0 10px 32px rgba(0,0,0,0.5);}
.card-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.card-name{font-size:0.92em;color:#f1f5f9;font-weight:800;letter-spacing:-0.2px;}

/* Temp Display */
.temp-wrap{padding:8px 0;text-align:center;}
.temp-val{font-size:2.4em;font-weight:900;letter-spacing:-1.5px;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:4px;}
.temp-unit{font-size:0.45em;color:#94a3b8;font-weight:700;margin-left:3px;}

/* Power Bar */
.pwm-wrap{margin:10px 0 14px;background:rgba(15,23,42,0.6);padding:8px 10px;border-radius:8px;border:1px solid rgba(51,65,85,0.35);}
.pwm-lbl-row{display:flex;justify-content:space-between;font-size:0.68em;color:#94a3b8;font-weight:700;margin-bottom:5px;}
.pwm-bar-bg{height:6px;background:#1e293b;border-radius:3px;overflow:hidden;}
.pwm-bar-fill{height:100%;background:linear-gradient(90deg,#38bdf8,#f59e0b,#ef4444);width:0%;transition:width 0.4s ease-out;}

/* Setpoint Box */
.sp-box{background:rgba(15,23,42,0.6);padding:10px 14px;border-radius:12px;display:flex;align-items:center;justify-content:space-between;border:1px solid rgba(51,65,85,0.4);}
.sp-lbl-wrap{display:flex;flex-direction:column;}
.sp-lbl{font-size:0.65em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;}
.sp-val{font-size:1.15em;font-weight:900;color:#fff;font-variant-numeric:tabular-nums;}
.btn-step{background:#1e293b;color:#38bdf8;border:1px solid #334155;width:34px;height:34px;border-radius:8px;font-weight:900;cursor:pointer;font-size:1.1em;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.btn-step:hover:not(:disabled){background:#38bdf8;color:#0f172a;box-shadow:0 0 10px rgba(56,189,248,0.4);}
.btn-step:disabled{opacity:0.3;cursor:not-allowed;}

/* Status Row */
.status-row{margin-top:12px;font-size:0.75em;font-weight:800;display:flex;align-items:center;justify-content:space-between;}
.st-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:20px;font-size:0.72em;letter-spacing:0.3px;}
.st-active{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.st-standby{background:rgba(71,85,105,0.2);color:#94a3b8;border:1px solid #475569;}
.badge-error{background:rgba(220,38,38,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);padding:4px 10px;border-radius:8px;font-size:0.72em;font-weight:800;display:inline-flex;align-items:center;gap:6px;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.65;}}

@media(max-width:440px){
  .btn-group{flex-direction:column;}
  .btn-pwr{max-width:100%;}
  .grid{grid-template-columns:1fr;}
}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <div style='text-align:center'>
                <span class='hdr-title'>Control T&eacute;rmico</span>
                <span class='hdr-sub'>CONTROL T&Eacute;RMICO PI &middot; TERMOPARES MAX6675</span>
            </div>
            <div></div>
        </div>

        <div class='btn-group'>
            <button class='btn-pwr btn-act' onclick='toggleT(1)'>ENCENDER SISTEMA</button>
            <button class='btn-pwr btn-stop' onclick='toggleT(0)'>APAGAR SISTEMA</button>
        </div>

        <div class='grid' id='t-cards'></div>
    </div>
    <script>
        const nombres = ["Limpieza (450W)", "Decapado (450W)", "Zincado (Celda Hull 18W)", "Niquelado (450W)"];
        let defaultData = [
            { t: 0.0, sp: 60.0, p: 0, run: 0 },
            { t: 0.0, sp: 45.0, p: 0, run: 0 },
            { t: 0.0, sp: 30.0, p: 0, run: 0 },
            { t: 0.0, sp: 55.0, p: 0, run: 0 }
        ];

        function renderThermal(data) {
            let h = '';
            data.forEach(function(c, i){
                let esError = (c.t <= 0.0 || c.t >= 150.0);
                let colorBorde = esError ? '#ef4444' : (c.run==1?'#10b981':'#38bdf8');
                let colorTemp = esError ? '#ef4444' : (c.run==1 && c.t < c.sp ? '#f59e0b' : (c.run==1 ? '#10b981' : '#38bdf8'));
                
                let estadoHtml = esError ? 
                    '<span class="badge-error">&#9888; FALLA TERMOPAR</span>' : 
                    (c.run==1 ? '<span class="st-pill st-active">&#9679; Activo ('+c.p+'%)</span>' : '<span class="st-pill st-standby">&#9675; En Reposo</span>');

                let tempDisplay = esError ? 'ERROR' : c.t.toFixed(1) + '<span class="temp-unit">&deg;C</span>';

                h += '<div class="card" style="border-left-color:'+colorBorde+'">' +
                    '<div class="card-head">' +
                        '<span class="card-name">' + nombres[i] + '</span>' +
                    '</div>' +
                    '<div class="temp-wrap">' +
                        '<div class="temp-val" style="color:' + colorTemp + '">' + tempDisplay + '</div>' +
                    '</div>' +
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
            });
            document.getElementById('t-cards').innerHTML = h;
        }

        function loadThermal(){
            fetch('/data_t').then(function(r){return r.json();}).then(function(data){
                renderThermal(data);
            }).catch(function(){});
        }

        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch('/set_t?id=' + id + '&v=' + val).then(function(r){
                if(r.status === 403) alert('Detenga el sistema térmico primero para cambiar el setpoint.');
                loadThermal();
            }); 
        }

        function toggleT(run){ 
            fetch('/act_t?run=' + run).then(function(r){
                if(r.status === 403) alert('¡Bloqueado por Interlock!\nEl módulo de pH está activo.\nDebes apagar el módulo de pH antes de encender el sistema térmico.');
                loadThermal();
            }); 
        }

        renderThermal(defaultData);
        setInterval(loadThermal, 2000); 
        loadThermal();
    </script>
</body></html>
)rawliteral";

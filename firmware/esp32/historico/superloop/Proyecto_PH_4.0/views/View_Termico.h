#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: CONTROL TÉRMICO (View_Termico.h) — Versión 4.0
 * =================================================================================
 * Contiene el código HTML/CSS/JS del panel de control de temperatura de las
 * 4 tinas de electrodeposición. Almacenado en PROGMEM (Flash).
 */

const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control T&eacute;rmico</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px;}
.container{max-width:760px;margin:0 auto;}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;}
.nav-back:hover{color:#7dd3fc;}
.hdr-t{font-size:1.1em;font-weight:800;color:#fff;}
.btn-group{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}
.btn{padding:12px 22px;cursor:pointer;border-radius:10px;border:none;font-weight:800;font-size:0.85em;transition:all 0.2s;letter-spacing:0.3px;}
.btn-act{background:#059669;color:#fff;box-shadow:0 4px 14px rgba(5,150,105,0.3);}
.btn-act:hover{background:#10b981;}
.btn-stop{background:#dc2626;color:#fff;box-shadow:0 4px 14px rgba(220,38,38,0.3);}
.btn-stop:hover{background:#ef4444;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;}
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:16px;padding:18px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 20px rgba(0,0,0,0.35);border-left:4px solid #38bdf8;transition:border-color 0.3s;}
.card h3{font-size:0.92em;color:#94a3b8;margin-bottom:10px;font-weight:700;}
.temp-val{font-size:1.8em;font-weight:900;color:#38bdf8;letter-spacing:-1px;margin:6px 0;}
.sp-box{margin-top:12px;background:rgba(15,23,42,0.6);padding:10px;border-radius:10px;display:flex;align-items:center;justify-content:space-between;border:1px solid rgba(51,65,85,0.4);}
.sp-lbl{font-size:0.75em;color:#94a3b8;font-weight:600;}
.sp-val{font-size:1em;font-weight:800;color:#fff;}
.btn-step{background:#1e293b;color:#38bdf8;border:1px solid #334155;width:32px;height:32px;border-radius:6px;font-weight:900;cursor:pointer;font-size:1.1em;display:flex;align-items:center;justify-content:center;transition:0.2s;}
.btn-step:hover:not(:disabled){background:#38bdf8;color:#0f172a;}
.btn-step:disabled{opacity:0.3;cursor:not-allowed;}
.status-row{margin-top:10px;font-size:0.75em;font-weight:700;}
.badge-error{background:rgba(220,38,38,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);padding:4px 8px;border-radius:6px;font-size:0.75em;font-weight:800;display:inline-block;}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <span class='hdr-t'>Lazos de Control T&eacute;rmico</span>
            <div></div>
        </div>
        <div class='btn-group'>
            <button class='btn btn-act' onclick='toggleT(1)'>ENCENDER SISTEMA</button>
            <button class='btn btn-stop' onclick='toggleT(0)'>APAGAR SISTEMA</button>
        </div>
        <div class='grid' id='t-cards'></div>
    </div>
    <script>
        const nombres = ["Limpieza", "Decapado", "Zincado (Celda Hull)", "Niquelado"];
        function loadThermal(){
            fetch('/data_t').then(function(r){return r.json();}).then(function(data){
                let h = '';
                data.forEach(function(c, i){
                    let esError = (c.t <= 0.0 || c.t >= 150.0);
                    let colorBorde = esError ? '#ef4444' : (c.run==1?'#10b981':'#38bdf8');
                    let estadoHtml = esError ? 
                        '<div class="badge-error">FALLA TERMOPAR (PARADA)</div>' : 
                        (c.run==1?'<span style="color:#10b981">Activo</span>':'<span style="color:#ef4444">Bloqueado</span>');

                    h += '<div class="card" style="border-left-color:'+colorBorde+'">' +
                        '<h3>' + nombres[i] + '</h3>' +
                        '<div class="temp-val" style="color:' + (esError?'#ef4444':'#38bdf8') + '">' + (esError?'ERROR':c.t.toFixed(1)+' &deg;C') + '</div>' +
                        '<div class="sp-box">' +
                            '<div><span class="sp-lbl">Setpoint: </span><span class="sp-val">' + c.sp + ' &deg;C</span></div>' +
                            '<div style="display:flex;gap:4px;">' +
                                '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp-1) + ')">-</button>' +
                                '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp+1) + ')">+</button>' +
                            '</div>' +
                        '</div>' +
                        '<div class="status-row">Estado: ' + estadoHtml + '</div>' +
                    '</div>';
                });
                document.getElementById('t-cards').innerHTML = h;
            }).catch(function(){});
        }
        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch('/set_t?id=' + id + '&v=' + val).then(function(r){
                if(r.status === 403) alert('Detenga el sistema termico primero para cambiar el setpoint.');
                loadThermal();
            }); 
        }
        function toggleT(run){ 
            fetch('/act_t?run=' + run).then(function(r){
                if(r.status === 403) alert('¡Bloqueado por Interlock!\nEl módulo de pH está activo.\nDebes apagar el pH manualmente en su menú antes de encender la calefacción.');
                loadThermal();
            }); 
        }
        setInterval(loadThermal, 2000); loadThermal();
    </script>
</body></html>
)rawliteral";

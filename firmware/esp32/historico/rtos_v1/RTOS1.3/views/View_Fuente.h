#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: FUENTE DE CORRIENTE VCSS (View_Fuente.h) — Versión RTOS 1.1
 * =================================================================================
 * MEJORAS v1.1:
 *   • Amperímetro con barra VU analógica y colores dinámicos por rango
 *   • Animación de conteo suave en valores numéricos (animateValue)
 *   • Indicador de pulso visual en modo pulsado (parpadeo rítmico)
 *   • Toast notifications reemplazando alert() nativos
 *   • Heartbeat de conectividad en header
 *   • Botón de encendido con glow pulsante cuando activo
 *   • Loading spinner en botones de calibración
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_FUENTE[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Salida de Corriente &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px 32px;}
.container{max-width:560px;margin:0 auto;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}
.hdr-hb{display:flex;align-items:center;gap:6px;font-size:0.65em;font-weight:700;color:#475569;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 5px #34d399;animation:hb-p 2s ease-in-out infinite;}
.hb-dot.off{background:#ef4444;box-shadow:0 0 5px #ef4444;animation:none;}
@keyframes hb-p{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.7);}}

/* Main Instrument Card */
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.92));border-radius:22px;padding:24px 20px;border:1px solid rgba(56,189,248,0.12);box-shadow:0 12px 40px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.04);text-align:center;}

/* Power Switch */
.btn-pwr{width:100%;font-size:1.02em;padding:16px;border-radius:14px;font-weight:800;cursor:pointer;border:none;transition:all 0.25s cubic-bezier(.4,0,.2,1);letter-spacing:0.5px;display:flex;align-items:center;justify-content:center;gap:8px;}
.btn-pwr-off{background:linear-gradient(135deg,#059669,#047857);color:#fff;box-shadow:0 4px 20px rgba(5,150,105,0.35);}
.btn-pwr-off:hover{background:linear-gradient(135deg,#10b981,#059669);transform:translateY(-1px);box-shadow:0 6px 24px rgba(5,150,105,0.45);}
.btn-pwr-on{background:linear-gradient(135deg,#b91c1c,#991b1b);color:#fff;box-shadow:0 4px 20px rgba(185,28,28,0.35);animation:glow-red 2.5s ease-in-out infinite;}
.btn-pwr-on:hover{background:linear-gradient(135deg,#dc2626,#b91c1c);transform:translateY(-1px);box-shadow:0 6px 24px rgba(220,38,38,0.45);}
@keyframes glow-red{0%,100%{box-shadow:0 4px 20px rgba(185,28,28,0.35);}50%{box-shadow:0 4px 28px rgba(239,68,68,0.55);}}

/* Status Badge */
.status-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 16px;border-radius:20px;font-weight:800;font-size:0.78em;margin:16px 0 10px;letter-spacing:0.3px;transition:all 0.4s;}
.status-on{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.35);}
.status-off{background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.35);}

/* Digital Ammeter Display */
.meter-box{background:#020617;border-radius:16px;padding:18px 14px;margin:12px 0 8px;border:1px solid rgba(56,189,248,0.15);box-shadow:inset 0 2px 8px rgba(0,0,0,0.7);position:relative;overflow:hidden;}
.meter-box::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.4),transparent);}
.meter-sub{font-size:0.68em;color:#64748b;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.amp-box{font-size:54px;font-weight:900;letter-spacing:-2px;font-variant-numeric:tabular-nums;line-height:1;transition:color 0.5s;}
.amp-box span{transition:color 0.5s;}
.meter-meta{display:flex;justify-content:center;gap:16px;margin-top:10px;font-size:0.75em;color:#94a3b8;font-weight:700;}
.meter-meta b{color:#38bdf8;}

/* VU Meter Bar */
.vu-wrap{margin:10px 0 12px;padding:0 4px;}
.vu-bar-bg{height:8px;background:#1e293b;border-radius:4px;overflow:hidden;position:relative;}
.vu-bar-fill{height:100%;border-radius:4px;transition:width 0.4s ease-out;background:linear-gradient(90deg,#38bdf8,#22c55e 35%,#fbbf24 65%,#ef4444 100%);}
.vu-labels{display:flex;justify-content:space-between;font-size:0.58em;color:#475569;font-weight:700;margin-top:3px;padding:0 2px;}

/* Pulse Indicator */
.pulse-ind{margin:6px 0;font-size:0.72em;font-weight:800;letter-spacing:0.5px;color:#475569;height:18px;display:flex;align-items:center;justify-content:center;gap:6px;}
.pulse-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#38bdf8;box-shadow:0 0 8px #38bdf8;}
.pulse-dot.beating{animation:pulse-beat var(--pulse-period,0.1s) ease-in-out infinite;}
@keyframes pulse-beat{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.15;transform:scale(0.6);}}

/* Mode Selector */
.btn-mode-wrap{display:flex;gap:6px;margin-bottom:18px;background:#0f172a;border-radius:12px;padding:4px;border:1px solid rgba(51,65,85,0.4);}
.btn-m{flex:1;padding:10px 8px;border-radius:9px;border:none;font-weight:800;font-size:0.78em;cursor:pointer;transition:all 0.25s;letter-spacing:0.3px;}
.btn-m.act{background:linear-gradient(135deg,#1d4ed8,#2563eb);color:#fff;box-shadow:0 2px 10px rgba(37,99,235,0.4);}
.btn-m.inact{background:transparent;color:#64748b;}
.btn-m.inact:hover{color:#94a3b8;background:rgba(30,41,59,0.5);}

/* Controls & Sliders */
.ctrl-group{background:rgba(15,23,42,0.6);padding:14px 16px;border-radius:14px;margin-top:12px;text-align:left;border:1px solid rgba(51,65,85,0.4);}
.ctrl-group label{font-weight:700;font-size:0.8em;color:#94a3b8;display:flex;justify-content:space-between;margin-bottom:6px;}
.ctrl-group b{color:#38bdf8;}
input[type=range]{width:100%;accent-color:#38bdf8;margin:8px 0 4px;cursor:pointer;height:6px;background:#1e293b;border-radius:3px;}

/* Presets */
.preset-wrap{display:flex;gap:6px;margin-top:8px;}
.btn-preset{flex:1;padding:6px 4px;border-radius:7px;background:#1e293b;border:1px solid #334155;color:#94a3b8;font-size:0.7em;font-weight:800;cursor:pointer;transition:0.2s;}
.btn-preset:hover{background:#334155;color:#38bdf8;border-color:#38bdf8;}

/* Panel VCSS RTOS */
.vcss-panel{background:rgba(15,23,42,0.6);border-radius:16px;padding:18px 16px;margin-top:18px;border:1px solid rgba(56,189,248,0.15);text-align:left;}
.vcss-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;font-size:0.7em;color:#94a3b8;font-weight:800;letter-spacing:0.5px;flex-wrap:wrap;gap:8px;}
.vcss-badges{display:flex;gap:6px;}
.vcss-badge{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);padding:3px 8px;border-radius:6px;font-size:0.75em;font-weight:800;transition:all 0.3s;}
.vcss-badge.off{background:rgba(71,85,105,0.2);color:#94a3b8;border-color:#475569;}
.vcss-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;}
.vcss-item{background:#0b1120;padding:12px 8px;border-radius:12px;text-align:center;border:1px solid rgba(51,65,85,0.4);box-shadow:inset 0 1px 3px rgba(0,0,0,0.3);}
.vcss-lbl{font-size:0.62em;color:#64748b;font-weight:800;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.3px;}
.vcss-val{font-size:1.15em;font-weight:900;color:#38bdf8;font-variant-numeric:tabular-nums;transition:color 0.4s;}
.vcss-sub{font-size:0.68em;color:#94a3b8;font-weight:700;margin-top:4px;}
.vcss-actions{display:flex;gap:8px;flex-wrap:wrap;}
.btn-vcss{flex:1;min-width:120px;padding:10px 8px;background:#1e293b;border:1px solid #334155;color:#cbd5e1;border-radius:9px;font-size:0.72em;font-weight:800;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;justify-content:center;gap:6px;}
.btn-vcss:hover{background:#334155;color:#fff;}
.btn-vcss:disabled{opacity:0.5;cursor:wait;}
.btn-cal{border-color:rgba(251,191,36,0.3);color:#fbbf24;}
.btn-cal:hover{background:rgba(217,119,6,0.2);color:#fcd34d;}
.btn-reset{border-color:rgba(56,189,248,0.35);color:#38bdf8;}
.btn-reset:hover{background:rgba(56,189,248,0.15);color:#7dd3fc;}
.spin{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin-r 0.6s linear infinite;}
@keyframes spin-r{to{transform:rotate(360deg);}}

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

@media(max-width:440px){
  .amp-box{font-size:42px;}
  .vcss-grid{grid-template-columns:1fr;}
  .toast-container{left:14px;right:14px;}
}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <div style='text-align:center'>
                <span class='hdr-title'>Salida de Corriente</span>
                <span class='hdr-sub'>CONTROL VCSS &middot; SHUNT DUAL &middot; LAZO CERRADO</span>
            </div>
            <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span><span id='hb-txt'>...</span></div>
        </div>

        <div class='card'>
            <button class='btn-pwr btn-pwr-off' id='btn-power' onclick='togglePower()'>ENCENDER FUENTE</button>
            
            <div><span class='status-badge status-off' id='status-badge'>ESTADO: EN ESPERA (0.00 A)</span></div>

            <div class='meter-box'>
                <div class='meter-sub'>Salida de Corriente</div>
                <div class='amp-box' id='amp-display'><span id='amp-amps'>0.00</span> A</div>
                <div class='meter-meta'>
                    <span>Consigna: <b id='amp-calc'>1.77</b> A</span>
                    <span>Modo: <b id='modo-str'>Continua (DC)</b></span>
                </div>
            </div>

            <!-- VU Meter -->
            <div class='vu-wrap'>
                <div class='vu-bar-bg'><div class='vu-bar-fill' id='vu-fill' style='width:0%'></div></div>
                <div class='vu-labels'><span>0A</span><span>1A</span><span>2A</span><span>3A</span><span>4A</span></div>
            </div>

            <!-- Pulse Indicator -->
            <div class='pulse-ind' id='pulse-ind'></div>

            <div class='btn-mode-wrap'>
                <button class='btn-m act' id='btn-dc' onclick='setModo(0)'>CONTINUA (DC)</button>
                <button class='btn-m inact' id='btn-pulsed' onclick='setModo(1)'>PULSADA (1-100 Hz)</button>
            </div>

            <div class='ctrl-group'>
                <label>
                    <span>Amplitud: <b id='amp-bits'>1024</b> bits</span>
                    <span>(<span id='amp-calc2'>1.77</span> A)</span>
                </label>
                <input type='range' id='slide-amp' min='0' max='4095' value='1024' oninput='onAmpChange(this.value)'>
                <div class='preset-wrap'>
                    <button class='btn-preset' onclick='setPreset(0.5)'>0.50 A</button>
                    <button class='btn-preset' onclick='setPreset(1.0)'>1.00 A</button>
                    <button class='btn-preset' onclick='setPreset(1.5)'>1.50 A</button>
                    <button class='btn-preset' onclick='setPreset(2.0)'>2.00 A</button>
                </div>
            </div>

            <div id='pulsed-options' style='display:none;'>
                <div class='ctrl-group'>
                    <label><span>Frecuencia</span><b id='freq-val'>10 Hz</b></label>
                    <input type='range' id='slide-freq' min='1' max='100' value='10' oninput='sendParam("f", this.value)'>
                </div>
                <div class='ctrl-group'>
                    <label><span>Ciclo de Trabajo</span><b id='duty-val'>50 %</b></label>
                    <input type='range' id='slide-duty' min='1' max='99' value='50' oninput='sendParam("d", this.value)'>
                </div>
            </div>

            <!-- Panel Sensado VCSS -->
            <div class='vcss-panel'>
                <div class='vcss-hdr'>
                    <span>MONITOREO DE CORRIENTE</span>
                    <div class='vcss-badges'>
                        <span class='vcss-badge' id='rele-badge'>REL&Eacute; +12V: AISLADO</span>
                        <span class='vcss-badge' id='comp-badge'>CONTROL AUTOM&Aacute;TICO: ACTIVO</span>
                    </div>
                </div>
                <div class='vcss-grid'>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Rama 1 (MOSFET 1)</div>
                        <div class='vcss-val' id='i1-val'>0.00 A</div>
                        <div class='vcss-sub' id='v1-val'>0.000 V</div>
                    </div>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Rama 2 (MOSFET 2)</div>
                        <div class='vcss-val' id='i2-val'>0.00 A</div>
                        <div class='vcss-sub' id='v2-val'>0.000 V</div>
                    </div>
                    <div class='vcss-item'>
                        <div class='vcss-lbl'>Total Medido</div>
                        <div class='vcss-val' id='itot-val' style='color:#34d399;'>0.00 A</div>
                        <div class='vcss-sub' id='gm-val'>Gm: 2.000 S</div>
                    </div>
                </div>
                <div class='vcss-actions'>
                    <button class='btn-vcss' id='btn-comp' onclick='toggleComp()'>Desactivar Control Autom&aacute;tico</button>
                    <button class='btn-vcss btn-cal' id='btn-cal' onclick='calibrarVCSS()'>Auto-Calibrar</button>
                    <button class='btn-vcss btn-reset' id='btn-rst' onclick='resetCalibrarVCSS()'>Ganancia Predeterminada</button>
                </div>
            </div>
        </div>
    </div>

    <div class='toast-container' id='toast-box'></div>

    <script>
        var fuenteActiva = false;
        var isDragging = false;
        var compActivo = true;
        var lastOk = Date.now();
        var prevAmps = 0;

        function showToast(msg,type){var box=document.getElementById('toast-box');var t=document.createElement('div');t.className='toast toast-'+(type||'info');t.innerHTML=msg;box.appendChild(t);setTimeout(function(){t.classList.add('out');setTimeout(function(){t.remove();},300);},3500);}

        function ampColor(a){
            if(a<0.05) return '#38bdf8';
            if(a<1.0) return '#38bdf8';
            if(a<2.0) return '#22c55e';
            if(a<3.0) return '#fbbf24';
            return '#ef4444';
        }

        function animateValue(el, start, end, dur) {
            if(Math.abs(end-start)<0.005){el.innerText=end.toFixed(2);return;}
            var range=end-start;
            var t0=null;
            function step(ts){
                if(!t0) t0=ts;
                var p=Math.min((ts-t0)/dur,1);
                var v=start+range*p;
                el.innerText=v.toFixed(2);
                if(p<1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        }

        function updHb(){
            var d=Date.now()-lastOk;
            var dot=document.getElementById('hb-dot');
            var txt=document.getElementById('hb-txt');
            if(d>6000){dot.className='hb-dot off';txt.innerText='Sin conexi\u00f3n';}
            else{dot.className='hb-dot';var s=Math.floor(d/1000);txt.innerText=s<2?'OK':'Hace '+s+'s';}
        }

        function loadFuenteData(){
            if (isDragging) return;
            fetch('/data_f').then(function(r){return r.json();}).then(function(d){
                lastOk=Date.now();
                fuenteActiva = (d.act == 1);
                compActivo = (d.comp == 1);
                var btnPwr = document.getElementById('btn-power');
                var badge = document.getElementById('status-badge');
                var ampVal = parseFloat(d.amps).toFixed(2);
                var ampNum = parseFloat(d.amps);
                var ampDisplay = document.getElementById('amp-display');
                var col = ampColor(fuenteActiva ? ampNum : 0);
                
                if (fuenteActiva) {
                    btnPwr.innerText = "APAGAR FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-on";
                    badge.innerText = "ESTADO: ACTIVA (" + ampVal + " A)";
                    badge.className = "status-badge status-on";
                    animateValue(document.getElementById('amp-amps'), prevAmps, ampNum, 350);
                    ampDisplay.style.color = col;
                } else {
                    btnPwr.innerText = "ENCENDER FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-off";
                    badge.innerText = "ESTADO: EN ESPERA (0.00 A)";
                    badge.className = "status-badge status-off";
                    document.getElementById('amp-amps').innerText = "0.00";
                    ampDisplay.style.color = '#38bdf8';
                }
                prevAmps = fuenteActiva ? ampNum : 0;

                // VU meter
                var vuPct = Math.min((ampNum / 4.0) * 100, 100);
                document.getElementById('vu-fill').style.width = (fuenteActiva ? vuPct : 0) + '%';

                // Pulse indicator
                var isPulsed = (d.modo == 1);
                var pulseEl = document.getElementById('pulse-ind');
                if(isPulsed && fuenteActiva){
                    var freq = parseInt(d.freq) || 10;
                    var period = (1.0/freq);
                    pulseEl.innerHTML = "<span class='pulse-dot beating' style='--pulse-period:"+period+"s'></span> Pulsando a "+freq+" Hz (Duty: "+d.duty+"%)";
                    pulseEl.style.color='#38bdf8';
                } else if(fuenteActiva){
                    pulseEl.innerHTML = "Corriente Continua (DC)";
                    pulseEl.style.color='#22c55e';
                } else {
                    pulseEl.innerHTML = "";
                }

                document.getElementById('btn-dc').className = isPulsed ? "btn-m inact" : "btn-m act";
                document.getElementById('btn-pulsed').className = isPulsed ? "btn-m act" : "btn-m inact";
                document.getElementById('pulsed-options').style.display = isPulsed ? "block" : "none";
                document.getElementById('modo-str').innerText = isPulsed ? "Pulsada (" + d.freq + " Hz)" : "Continua (DC)";

                document.getElementById('slide-amp').value = d.sp;
                document.getElementById('amp-bits').innerText = d.sp;
                document.getElementById('amp-calc').innerText = ampVal;
                var calcEl = document.getElementById('amp-calc2');
                if(calcEl) calcEl.innerText = ampVal;

                document.getElementById('slide-freq').value = d.freq;
                document.getElementById('freq-val').innerText = d.freq + " Hz";

                document.getElementById('slide-duty').value = d.duty;
                document.getElementById('duty-val').innerText = d.duty + " %";

                // VCSS
                document.getElementById('i1-val').innerText = d.i1.toFixed(2) + " A";
                document.getElementById('v1-val').innerText = d.vs1.toFixed(3) + " V";
                document.getElementById('i2-val').innerText = d.i2.toFixed(2) + " A";
                document.getElementById('v2-val').innerText = d.vs2.toFixed(3) + " V";
                document.getElementById('itot-val').innerText = d.i_real.toFixed(2) + " A";
                document.getElementById('gm-val').innerText = "Gm: " + (d.gm * 2.0).toFixed(3) + " S (" + d.gm.toFixed(3) + "x)";

                var releBadge = document.getElementById('rele-badge');
                if (d.rele == 1) {
                    releBadge.innerText = "RELÉ +12V: CERRADO (ACTIVO)";
                    releBadge.className = "vcss-badge";
                } else {
                    releBadge.innerText = "RELÉ +12V: AISLADO (0V)";
                    releBadge.className = "vcss-badge off";
                }

                var compBadge = document.getElementById('comp-badge');
                var btnComp = document.getElementById('btn-comp');
                if (d.comp == 1) {
                    compBadge.innerText = "CONTROL AUTOMÁTICO: ACTIVO";
                    compBadge.className = "vcss-badge";
                    btnComp.innerHTML = "Desactivar Control Autom&aacute;tico";
                } else {
                    compBadge.innerText = "CONTROL AUTOMÁTICO: INACTIVO";
                    compBadge.className = "vcss-badge off";
                    btnComp.innerHTML = "Activar Control Autom&aacute;tico";
                }

                // Interlock de botones de calibración: inhabilitar mientras la fuente esté encendida
                var btnCal = document.getElementById('btn-cal');
                var btnRst = document.getElementById('btn-rst');
                if (btnCal) {
                    btnCal.disabled = fuenteActiva;
                    btnCal.title = fuenteActiva ? "Apague la fuente antes de autocalibrar los shunts" : "";
                    btnCal.style.opacity = fuenteActiva ? '0.4' : '1.0';
                    btnCal.style.cursor = fuenteActiva ? 'not-allowed' : 'pointer';
                }
                if (btnRst) {
                    btnRst.disabled = fuenteActiva;
                    btnRst.title = fuenteActiva ? "Apague la fuente antes de restablecer" : "";
                    btnRst.style.opacity = fuenteActiva ? '0.4' : '1.0';
                    btnRst.style.cursor = fuenteActiva ? 'not-allowed' : 'pointer';
                }

                updHb();
            }).catch(function(){ updHb(); });
        }

        function onAmpChange(val) {
            isDragging = true;
            document.getElementById('amp-bits').innerText = val;
            var a = ((val / 4095.0) * 7.06).toFixed(2);
            document.getElementById('amp-calc').innerText = a;
            var calcEl = document.getElementById('amp-calc2');
            if(calcEl) calcEl.innerText = a;
            sendParam("a", val);
            setTimeout(function(){ isDragging = false; }, 300);
        }

        function setPreset(amps) {
            var val = Math.round((amps / 7.06) * 4095.0);
            if(val > 4095) val = 4095;
            document.getElementById('slide-amp').value = val;
            onAmpChange(val);
            showToast('Consigna: '+amps.toFixed(2)+' A','info');
        }

        function sendParam(param, val) {
            fetch('/set_f?p=' + param + '&v=' + val).then(function(){
                loadFuenteData();
            });
        }

        function setModo(modo) {
            fetch('/modo_f?v=' + modo).then(function(){
                showToast(modo==1?'Modo Pulsado activado':'Modo DC activado','info');
                loadFuenteData();
            });
        }

        function togglePower() {
            var nuevoEstado = fuenteActiva ? 0 : 1;
            fetch('/act_f?run=' + nuevoEstado).then(function(r){
                if(r.status === 403){
                    showToast('&#9888; Bloqueado por Interlock — Apague el pH primero','err');
                } else {
                    showToast(nuevoEstado==1?'&#9889; Fuente ENCENDIDA':'Fuente APAGADA','ok');
                }
                loadFuenteData();
            }).catch(function(){showToast('Error de comunicaci\u00f3n','err');});
        }

        function toggleComp() {
            var nuevoComp = compActivo ? 0 : 1;
            fetch('/set_comp_f?v=' + nuevoComp).then(function(){
                showToast(nuevoComp==1?'Control Autom\u00e1tico activado':'Control Autom\u00e1tico desactivado','info');
                loadFuenteData();
            });
        }

        function calibrarVCSS() {
            if (fuenteActiva) {
                showToast('&#9888; Calibraci\u00f3n bloqueada: Apague la fuente antes de autocalibrar los shunts', 'err');
                return;
            }
            if(!confirm("¿Iniciar auto-calibración de corriente?\nSe aplicará una corriente de prueba de 1.50 A durante 1 segundo para calibrar los sensores.")) return;
            var btn=document.getElementById('btn-cal');
            btn.disabled=true;btn.innerHTML="<span class='spin'></span> Calibrando...";
            fetch('/cal_vcss').then(function(r){
                if (r.status === 403) {
                    return r.json().then(function(errJson){ throw new Error(errJson.err || 'Bloqueado por interlock'); });
                }
                return r.json();
            }).then(function(res){
                if(res.ok == 1){
                    showToast('&#10003; Calibraci\u00f3n exitosa — Gm: '+res.gm.toFixed(4),'ok');
                } else {
                    showToast('&#10007; Error: ' + (res.err || 'Corriente fuera de rango'),'err');
                }
                loadFuenteData();
            }).catch(function(err){
                showToast(err.message || 'Error de comunicaci\u00f3n durante calibraci\u00f3n','err');
            }).finally(function(){
                btn.disabled=false;btn.innerHTML="Auto-Calibrar";
                loadFuenteData();
            });
        }

        function resetCalibrarVCSS() {
            if (fuenteActiva) {
                showToast('&#9888; Operación bloqueada: Apague la fuente antes de restablecer', 'err');
                return;
            }
            if(!confirm("¿Restablecer a la ganancia predeterminada (2.00 S)?\nEsto sobreescribe en Flash NVS el factor a 1.0000 y fija la transconductancia nominal.")) return;
            var btn=document.getElementById('btn-rst');
            btn.disabled=true;btn.innerHTML="<span class='spin'></span> Restableciendo...";
            fetch('/reset_cal_vcss').then(function(r){
                if (r.status === 403) {
                    return r.json().then(function(errJson){ throw new Error(errJson.err || 'Bloqueado por interlock'); });
                }
                return r.json();
            }).then(function(res){
                if(res.ok == 1){
                    showToast('&#10003; Ganancia predeterminada restablecida (2.000 S)','ok');
                } else {
                    showToast('&#10007; Error: ' + (res.err || 'Operación rechazada'), 'err');
                }
                loadFuenteData();
            }).catch(function(err){
                showToast(err.message || 'Error de comunicaci\u00f3n','err');
            }).finally(function(){
                btn.disabled=false;btn.innerHTML="Ganancia Predeterminada";
                loadFuenteData();
            });
        }

        setInterval(loadFuenteData, 1500); loadFuenteData();
        setInterval(updHb, 1000);
    </script>
</body></html>
)rawliteral";

#ifndef VIEW_CONSOLA_H
#define VIEW_CONSOLA_H

/**
 * =================================================================================
 * VISTA DE CONSOLA Y DIAGNÓSTICO EN VIVO (View_Consola.h) — Versión RTOS 2.0
 * =================================================================================
 * Terminal Web interactiva de alta fidelidad para monitoreo inalámbrico de logs
 * del Kernel FreeRTOS, telemetría y eventos del ESP32-S3.
 * 
 * MEJORAS v2.0:
 *   • Estética Glassmorphism clásica con desenfoque de fondo y acentos cian
 *   • Tipografía offline monospace de alto rendimiento
 *   • Heartbeat animado con indicador de latencia
 *   • Animación de entrada para nuevos registros
 *   • Visual de reconexión automática
 * =================================================================================
 */

#include <Arduino.h>

const char HTML_CONSOLA[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Consola de Diagn&oacute;stico &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono',monospace;background:#070b14;background-image:radial-gradient(circle at 50% 0%,rgba(56,189,248,0.08) 0,transparent 50%),radial-gradient(circle at 90% 90%,rgba(52,211,153,0.05) 0,transparent 50%);color:#e2e8f0;min-height:100vh;display:flex;flex-direction:column;padding:16px 14px;}
.container{max-width:960px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;}

/* Header Box - Classic Frosted Glassmorphism */
.header-box{background:rgba(15,23,42,0.65);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);padding:16px 20px;border-radius:18px;border:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;box-shadow:0 8px 30px rgba(0,0,0,0.45),inset 0 1px 0 rgba(255,255,255,0.08);}
.title-group{display:flex;align-items:center;gap:14px;}
.mac-dots{display:flex;gap:6px;}
.mac-dot{width:11px;height:11px;border-radius:50%;}
.mac-red{background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,0.5);}
.mac-yellow{background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,0.5);}
.mac-green{background:#10b981;box-shadow:0 0 6px rgba(16,185,129,0.5);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.title-group h2{font-size:1.05em;color:#fff;font-weight:800;letter-spacing:-0.2px;display:flex;align-items:center;gap:8px;}

/* Actions Toolbar */
.actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.btn{padding:7px 14px;border-radius:8px;font-size:0.75em;font-weight:700;border:1px solid #334155;background:rgba(30,41,59,0.7);color:#94a3b8;cursor:pointer;transition:all 0.2s;}
.btn:hover{background:#334155;color:#fff;}
.btn:active{transform:scale(0.95);}
.btn.active{background:linear-gradient(135deg,#0284c7,#2563eb);color:#fff;border-color:#38bdf8;box-shadow:0 2px 8px rgba(37,99,235,0.3);}
.status-pill{display:inline-flex;align-items:center;gap:6px;font-size:0.72em;padding:4px 12px;border-radius:20px;background:rgba(52,211,153,0.12);color:#34d399;border:1px solid rgba(52,211,153,0.3);font-weight:800;letter-spacing:0.3px;}

/* Terminal Chassis */
.term-container{flex:1;background:rgba(2,6,23,0.85);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-radius:18px;border:1px solid rgba(56,189,248,0.2);padding:18px 20px;overflow-y:auto;display:flex;flex-direction:column;gap:6px;box-shadow:inset 0 4px 24px rgba(0,0,0,0.8);min-height:460px;max-height:calc(100vh - 140px);position:relative;}
.term-container::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.3),transparent);}

/* Log Rows */
.log-row{font-size:0.82em;line-height:1.6;display:flex;gap:10px;word-break:break-all;border-bottom:1px solid rgba(255,255,255,0.03);padding-bottom:4px;align-items:baseline;}
.log-row:hover{background:rgba(255,255,255,0.02);}
.log-time{color:#64748b;min-width:70px;font-weight:600;font-variant-numeric:tabular-nums;}
.log-tag{font-weight:800;min-width:80px;padding:1px 6px;border-radius:5px;font-size:0.88em;text-align:center;}
.tag-INFO{background:rgba(56,189,248,0.12);color:#38bdf8;border:1px solid rgba(56,189,248,0.25);}
.tag-WARN{background:rgba(245,158,11,0.12);color:#fbbf24;border:1px solid rgba(245,158,11,0.25);}
.tag-ERR{background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3);}
.log-msg{color:#f1f5f9;flex:1;}
.msg-ERR{color:#fca5a5;font-weight:700;}
.log-row.new{animation:log-in 0.3s cubic-bezier(.4,0,.2,1);}
@keyframes log-in{from{opacity:0;transform:translateX(-8px);}to{opacity:1;transform:translateX(0);}}
.empty-hint{color:#475569;text-align:center;margin-top:80px;font-size:0.9em;font-weight:600;}
.hdr-hb{display:flex;align-items:center;gap:5px;font-size:0.62em;font-weight:700;color:#475569;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 5px #34d399;animation:hb-p 2s ease-in-out infinite;}
.hb-dot.off{background:#ef4444;box-shadow:0 0 5px #ef4444;animation:none;}
@keyframes hb-p{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.7);}}
.latency{font-size:0.7em;font-weight:700;color:#475569;padding:3px 8px;border-radius:6px;background:rgba(15,23,42,0.5);}

@media(max-width:600px){
  .header-box{flex-direction:column;align-items:flex-start;}
  .actions{width:100%;justify-content:space-between;}
}
</style></head>
<body>
  <div class='container'>
    <div class='header-box'>
      <div class='title-group'>
        <div class='mac-dots'>
          <div class='mac-dot mac-red'></div>
          <div class='mac-dot mac-yellow'></div>
          <div class='mac-dot mac-green'></div>
        </div>
        <a href='/' class='nav-back'>&larr; Men&uacute;</a>
        <h2>Consola de Diagn&oacute;stico</h2>
      </div>
      <div class='actions'>
        <span class='status-pill' id='st-pill'>&#9679; EN L&Iacute;NEA</span>
        <span class='latency' id='latency'>--ms</span>
        <button class='btn active' id='btn-scroll' onclick='toggleScroll()'>Auto-Scroll: ON</button>
        <button class='btn' id='btn-pause' onclick='togglePause()'>Pausar</button>
        <button class='btn' onclick='clearScreen()'>Limpiar</button>
      </div>
      <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span></div>
    </div>

    <div class='term-container' id='term'>
      <div class='empty-hint' id='empty'>Cargando registros del sistema y eventos de FreeRTOS...</div>
    </div>
  </div>

  <script>
    var autoScroll = true;
    var pausado = false;
    var lastTimestamp = 0;
    var inFlight = false;
    var failCount = 0;
    var lastSuccess = Date.now();
    var term = document.getElementById('term');
    var empty = document.getElementById('empty');
    var stPill = document.getElementById('st-pill');

    function toggleScroll(){
      autoScroll = !autoScroll;
      var btn = document.getElementById('btn-scroll');
      btn.innerText = 'Auto-Scroll: ' + (autoScroll ? 'ON' : 'OFF');
      btn.className = autoScroll ? 'btn active' : 'btn';
    }

    function togglePause(){
      pausado = !pausado;
      var btn = document.getElementById('btn-pause');
      btn.innerText = pausado ? 'Reanudar' : 'Pausar';
      btn.className = pausado ? 'btn active' : 'btn';
    }

    function clearScreen(){
      term.innerHTML = '';
      lastTimestamp = 0;
    }

    function fetchLogs(){
      if(pausado || inFlight) return;
      inFlight = true;
      var t0 = Date.now();
      fetch('/logs')
        .then(function(r){
          if(!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function(logs){
          inFlight = false;
          failCount = 0;
          lastSuccess = Date.now();
          var lat = Date.now() - t0;
          document.getElementById('latency').innerText = lat + 'ms';
          document.getElementById('latency').style.color = lat < 200 ? '#34d399' : (lat < 500 ? '#fbbf24' : '#ef4444');
          document.getElementById('hb-dot').className = 'hb-dot';
          stPill.innerText = '● EN LÍNEA';
          stPill.style.color = '#34d399';

          if(logs.length > 0 && empty) {
            empty.remove();
            empty = null;
          }

          if(term.children.length === 0 || (logs.length > 0 && logs[0].t < lastTimestamp && logs.length > 1)){
            term.innerHTML = '';
          }

          for(var i = 0; i < logs.length; i++){
            var l = logs[i];
            if(term.children.length < logs.length || l.t > lastTimestamp){
              var row = document.createElement('div');
              row.className = 'log-row new';
              
              var lvlClass = (l.lvl === 2) ? 'ERR' : ((l.lvl === 1) ? 'WARN' : 'INFO');
              var tSec = (l.t / 1000).toFixed(3);

              row.innerHTML = 
                "<span class='log-time'>[" + tSec + "s]</span>" +
                "<span class='log-tag tag-" + lvlClass + "'>" + l.tag + "</span>" +
                "<span class='log-msg msg-" + lvlClass + "'>" + escapeHtml(l.msg) + "</span>";
              
              term.appendChild(row);
              setTimeout(function(r){return function(){r.classList.remove('new');};}(row), 350);
            }
          }

          if(logs.length > 0){
            lastTimestamp = logs[logs.length - 1].t;
          }

          if(autoScroll){
            term.scrollTop = term.scrollHeight;
          }
        })
        .catch(function(err){
          inFlight = false;
          failCount++;
          if(failCount >= 3 || (Date.now() - lastSuccess) > 4000){
            document.getElementById('hb-dot').className = 'hb-dot off';
            document.getElementById('latency').innerText = '--ms';
            document.getElementById('latency').style.color = '#ef4444';
            stPill.innerText = '○ SIN CONEXIÓN';
            stPill.style.color = '#ef4444';
          }
        });
    }

    function escapeHtml(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    setInterval(fetchLogs, 1500);
    fetchLogs();
  </script>
</body></html>
)rawliteral";

#endif // VIEW_CONSOLA_H

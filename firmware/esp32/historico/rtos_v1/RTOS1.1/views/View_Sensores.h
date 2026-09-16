#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: ESTADO DE SENSORES (View_Sensores.h) — Versión RTOS 1.1
 * =================================================================================
 * Panel de diagnóstico bajo demanda para los 8 periféricos del sistema (I2C + SPI)
 * y matriz de códigos de estado de la baliza LED RGB del supervisor FreeRTOS.
 * 
 * MEJORAS v1.1:
 *   • Animación de entrada escalonada en tarjetas de sensores
 *   • Heartbeat de conectividad
 *   • Barra de progreso durante escaneo
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_SENSORES[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Estado de Sensores &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px 36px;}
.container{max-width:800px;margin:0 auto;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Summary Box */
.summary{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding:20px 24px;background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;border:1px solid rgba(56,189,248,0.12);box-shadow:0 6px 24px rgba(0,0,0,0.4);flex-wrap:wrap;gap:14px;}
.sum-left{text-align:left;}
.sum-count{font-size:2.5em;font-weight:900;letter-spacing:-2px;font-variant-numeric:tabular-nums;line-height:1;}
.sum-label{font-size:0.75em;color:#94a3b8;font-weight:700;margin-top:4px;letter-spacing:0.3px;}

/* Scan Button */
.btn-scan{padding:14px 28px;cursor:pointer;border-radius:12px;border:1px solid rgba(56,189,248,0.25);background:linear-gradient(135deg,#0284c7,#2563eb);color:#fff;font-weight:800;font-size:0.88em;transition:all 0.25s;letter-spacing:0.5px;box-shadow:0 4px 16px rgba(37,99,235,0.3);display:inline-flex;align-items:center;gap:8px;}
.btn-scan:hover{background:linear-gradient(135deg,#0369a1,#1d4ed8);transform:translateY(-1px);box-shadow:0 6px 22px rgba(37,99,235,0.45);}
.btn-scan:active{transform:translateY(0);}
.btn-scan.scanning{opacity:0.6;cursor:wait;}

/* Grid */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;}

/* Sensor Card */
.s-card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:14px;padding:16px 14px;border:1px solid rgba(51,65,85,0.4);box-shadow:0 4px 18px rgba(0,0,0,0.3);transition:all 0.3s;text-align:center;border-left:4px solid #334155;position:relative;animation:card-in 0.4s cubic-bezier(.4,0,.2,1) both;}
.s-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.45);}
@keyframes card-in{from{opacity:0;transform:translateY(12px) scale(0.96);}to{opacity:1;transform:translateY(0) scale(1);}}
.s-card.ok{border-left-color:#10b981;}
.s-card.fail{border-left-color:#ef4444;animation:pulse-fail 2s ease-in-out infinite;}
.s-card.wait{border-left-color:#334155;}

.s-cat-tag{display:inline-block;font-size:0.62em;font-weight:800;letter-spacing:0.5px;padding:2px 8px;border-radius:10px;margin-bottom:8px;text-transform:uppercase;}
.s-icon{font-size:24px;margin-bottom:6px;line-height:1;}
.s-name{font-size:0.88em;color:#f1f5f9;font-weight:800;letter-spacing:-0.2px;}
.s-bus{font-size:0.65em;color:#64748b;font-weight:700;margin-top:3px;letter-spacing:0.3px;}
.s-addr{font-size:0.68em;color:#94a3b8;font-weight:600;margin-top:4px;}
.s-status{margin-top:10px;padding:4px 10px;border-radius:8px;font-size:0.68em;font-weight:800;display:inline-block;letter-spacing:0.3px;}
.st-ok{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.st-fail{background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);}
.st-wait{background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;}

/* Timestamp */
.ts{text-align:center;margin:16px 0 28px;font-size:0.72em;color:#64748b;font-weight:700;}
.hdr-hb{display:flex;align-items:center;gap:5px;font-size:0.62em;font-weight:700;color:#475569;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 5px #34d399;animation:hb-p 2s ease-in-out infinite;}
.hb-dot.off{background:#ef4444;box-shadow:0 0 5px #ef4444;animation:none;}
@keyframes hb-p{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.7);}}
.scan-progress{height:3px;background:#0f172a;border-radius:2px;margin-top:8px;overflow:hidden;display:none;}
.scan-progress.active{display:block;}
.scan-prog-fill{height:100%;width:0%;background:linear-gradient(90deg,#38bdf8,#22c55e);animation:scan-sweep 1.5s ease-in-out infinite;border-radius:2px;}
@keyframes scan-sweep{0%{width:0%;margin-left:0;}50%{width:60%;margin-left:20%;}100%{width:0%;margin-left:100%;}}

/* LED Legend Section */
.led-box{background:rgba(15,23,42,0.7);border-radius:18px;border:1px solid rgba(56,189,248,0.12);padding:22px 20px;}
.led-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid rgba(51,65,85,0.4);}
.led-title{font-size:0.95em;font-weight:800;color:#fff;}
.led-sub{font-size:0.62em;color:#64748b;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;}
.led-list{display:grid;grid-template-columns:1fr;gap:10px;}
@media(min-width:620px){.led-list{grid-template-columns:1fr 1fr;}}
.led-item{display:flex;align-items:flex-start;gap:12px;background:rgba(30,41,59,0.55);border-radius:12px;padding:12px 14px;border:1px solid rgba(51,65,85,0.35);transition:all 0.25s cubic-bezier(.4,0,.2,1);position:relative;}
.led-item:hover{background:rgba(30,41,59,0.75);border-color:rgba(56,189,248,0.2);}
.led-item.active-led{background:linear-gradient(135deg,rgba(56,189,248,0.2),rgba(15,23,42,0.85)) !important;border:2px solid #38bdf8 !important;box-shadow:0 0 22px rgba(56,189,248,0.4),inset 0 0 12px rgba(56,189,248,0.12) !important;transform:scale(1.015);}
.active-pill{display:none;}
.led-item.active-led .active-pill{display:inline-flex;align-items:center;gap:4px;background:linear-gradient(135deg,#0284c7,#0369a1);color:#f0f9ff;border:1px solid #38bdf8;padding:2px 7px;border-radius:12px;font-size:0.62em;font-weight:900;letter-spacing:0.5px;box-shadow:0 0 10px rgba(56,189,248,0.6);animation:glow-pulse 2s infinite;}
@keyframes glow-pulse{0%,100%{box-shadow:0 0 8px rgba(56,189,248,0.5);}50%{box-shadow:0 0 16px rgba(56,189,248,0.9);border-color:#7dd3fc;}}
.led-dot{width:14px;height:14px;border-radius:50%;flex-shrink:0;margin-top:2px;}
.led-info{flex:1;}
.led-state{font-size:0.78em;font-weight:800;color:#f8fafc;display:flex;align-items:center;justify-content:space-between;gap:6px;}
.led-tag{font-size:0.68em;padding:2px 6px;border-radius:6px;font-weight:700;letter-spacing:0.3px;}
.led-desc{font-size:0.68em;color:#94a3b8;margin-top:3px;line-height:1.4;}

/* Animations */
.dot-red-fast{background:#ef4444;box-shadow:0 0 10px #ef4444;animation:strobe 0.25s infinite;}
.dot-red-slow{background:#ef4444;box-shadow:0 0 8px #ef4444;animation:blink 1s infinite;}
.dot-white-fast{background:#fff;box-shadow:0 0 10px #fff;animation:strobe 0.2s infinite;}
.dot-purple{background:#a855f7;box-shadow:0 0 10px #a855f7;animation:breath 3.5s infinite;}
.dot-fuchsia{background:#ec4899;box-shadow:0 0 10px #ec4899;animation:breath 2s infinite;}
.dot-cyan-pulse{background:#06b6d4;box-shadow:0 0 10px #06b6d4;animation:strobe 0.4s infinite;}
.dot-cyan-solid{background:#06b6d4;box-shadow:0 0 8px #06b6d4;}
.dot-blue-dark{background:#2563eb;box-shadow:0 0 8px #2563eb;}
.dot-blue-pulse{background:#38bdf8;box-shadow:0 0 10px #38bdf8;animation:strobe 0.4s infinite;}
.dot-blue-light{background:#38bdf8;box-shadow:0 0 8px #38bdf8;}
.dot-amber{background:#f59e0b;box-shadow:0 0 8px #f59e0b;}
.dot-green-solid{background:#10b981;box-shadow:0 0 8px #10b981;}
.dot-green-beacon{background:#10b981;box-shadow:0 0 8px #10b981;animation:beacon 2.5s infinite;}

@keyframes strobe{0%,100%{opacity:1;}50%{opacity:0.1;}}
@keyframes blink{0%,49%{opacity:1;}50%,100%{opacity:0.15;}}
@keyframes breath{0%,100%{opacity:0.35;transform:scale(0.9);}50%{opacity:1;transform:scale(1.15);}}
@keyframes beacon{0%,8%{opacity:1;transform:scale(1.25);box-shadow:0 0 14px #10b981;}12%,100%{opacity:0.25;transform:scale(0.9);box-shadow:0 0 3px #10b981;}}
@keyframes pulse-fail{0%,100%{opacity:1;}50%{opacity:0.7;}}

@media(max-width:480px){
  .summary{flex-direction:column;align-items:flex-start;}
  .btn-scan{width:100%;justify-content:center;}
  .grid{grid-template-columns:repeat(2,1fr);}
}
</style></head>
<body>
  <div class='container'>
    <div class='hdr'>
      <a href='/' class='nav-back'>&larr; Men&uacute;</a>
      <div style='text-align:center'>
        <span class='hdr-title'>Estado de Sensores</span>
        <span class='hdr-sub'>I2C &middot; SPI &middot; 8 PERIF&Eacute;RICOS</span>
      </div>
      <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span><span id='hb-txt'>...</span></div>
    </div>

    <div class='summary'>
      <div class='sum-left'>
        <div class='sum-count' id='sum-count' style='color:#475569'>- / 8</div>
        <div class='sum-label'>Sensores Operativos</div>
      </div>
      <button class='btn-scan' id='btn-scan' onclick='escanear()'>ESCANEAR SENSORES</button>
      <div class='scan-progress' id='scan-prog'><div class='scan-prog-fill'></div></div>
    </div>

    <div style='display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;font-size:0.75em;color:#94a3b8;font-weight:700;'>
      <span style='color:#64748b;'>Subsistemas:</span>
      <span style='padding:3px 9px;border-radius:12px;border:1px solid rgba(51,65,85,0.5);background:rgba(15,23,42,0.6);display:inline-flex;align-items:center;gap:5px;'><span style='width:8px;height:8px;border-radius:50%;background:#06b6d4;display:inline-block;'></span> Ambiental</span>
      <span style='padding:3px 9px;border-radius:12px;border:1px solid rgba(51,65,85,0.5);background:rgba(15,23,42,0.6);display:inline-flex;align-items:center;gap:5px;'><span style='width:8px;height:8px;border-radius:50%;background:#a855f7;display:inline-block;'></span> pH</span>
      <span style='padding:3px 9px;border-radius:12px;border:1px solid rgba(51,65,85,0.5);background:rgba(15,23,42,0.6);display:inline-flex;align-items:center;gap:5px;'><span style='width:8px;height:8px;border-radius:50%;background:#f59e0b;display:inline-block;'></span> Potencia (DAC)</span>
      <span style='padding:3px 9px;border-radius:12px;border:1px solid rgba(51,65,85,0.5);background:rgba(15,23,42,0.6);display:inline-flex;align-items:center;gap:5px;'><span style='width:8px;height:8px;border-radius:50%;background:#f97316;display:inline-block;'></span> T&eacute;rmico</span>
    </div>

    <div class='grid' id='grid'></div>
    <div class='ts' id='ts'>Presione el bot&oacute;n para escanear</div>

    <!-- SECCIÓN CÓDIGOS DE BALIZA LED RGB -->
    <div class='led-box'>
      <div class='led-hdr'>
        <div>
          <span class='led-title'>Baliza LED RGB &mdash; C&oacute;digo de Estados</span>
          <span class='led-sub' style='display:block;margin-top:2px;'>SUPERVISOR FREERTOS EN TIEMPO REAL (CORE 1)</span>
        </div>
      </div>
      <div class='led-list'>
        <div class='led-item' id='led-critical'>
          <div class='led-dot dot-red-fast'></div>
          <div class='led-info'>
            <div class='led-state'><span>Peligro F&iacute;sico Cr&iacute;tico</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(239,68,68,0.2);color:#f87171'>Rojo (4 Hz)</span></div></div>
            <div class='led-desc'>Sobrecalentamiento (&gt;SP+5&deg;C), sobrecorriente VCSS (&gt;3.5A) o watchdog FreeRTOS disparado.</div>
          </div>
        </div>
        <div class='led-item' id='led-fault'>
          <div class='led-dot dot-red-slow'></div>
          <div class='led-info'>
            <div class='led-state'><span>Falla Sensor / Enlace</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(239,68,68,0.15);color:#fca5a5'>Rojo (1 Hz)</span></div></div>
            <div class='led-desc'>Termopar abierto (TC0..TC3), p&eacute;rdida I2C (ADS/DAC) o timeout con Arduino Nano.</div>
          </div>
        </div>
        <div class='led-item' id='led-ota'>
          <div class='led-dot dot-white-fast'></div>
          <div class='led-info'>
            <div class='led-state'><span>Actualizaci&oacute;n OTA</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(255,255,255,0.2);color:#fff'>Blanco (R&aacute;pido)</span></div></div>
            <div class='led-desc'>Actualizando firmware v&iacute;a Web. &iexcl;No apagar ni desconectar la alimentaci&oacute;n!</div>
          </div>
        </div>
        <div class='led-item' id='led-testbench'>
          <div class='led-dot dot-purple'></div>
          <div class='led-info'>
            <div class='led-state'><span>Modo Banco de Pruebas</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(168,85,247,0.2);color:#c084fc'>P&uacute;rpura</span></div></div>
            <div class='led-desc'>Placa en desarrollo: 0 sensores de planta detectados y conexi&oacute;n USB Serial activa.</div>
          </div>
        </div>
        <div class='led-item' id='led-ph'>
          <div class='led-dot dot-fuchsia'></div>
          <div class='led-info'>
            <div class='led-state'><span>Calibraci&oacute;n de pH</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(236,72,153,0.2);color:#f472b6'>Magenta</span></div></div>
            <div class='led-desc'>Sonda en soluci&oacute;n tamp&oacute;n; ajuste de offset y pendiente en curso.</div>
          </div>
        </div>
        <div class='led-item' id='led-term_pulse'>
          <div class='led-dot dot-cyan-pulse'></div>
          <div class='led-info'>
            <div class='led-state'><span>T&eacute;rmico + VCSS Pulsado</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(6,182,212,0.2);color:#67e8f9'>Cian / Azul</span></div></div>
            <div class='led-desc'>Sistema t&eacute;rmico activo + corriente modulada en tren de pulsos.</div>
          </div>
        </div>
        <div class='led-item' id='led-term_dc'>
          <div class='led-dot dot-cyan-solid'></div>
          <div class='led-info'>
            <div class='led-state'><span>T&eacute;rmico + VCSS Continuo</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(6,182,212,0.2);color:#67e8f9'>Cian (Fijo)</span></div></div>
            <div class='led-desc'>Sistema t&eacute;rmico activo + salida de corriente continua (DC).</div>
          </div>
        </div>
        <div class='led-item' id='led-term_only'>
          <div class='led-dot dot-blue-dark'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sistema T&eacute;rmico Activo</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(37,99,235,0.2);color:#93c5fd'>Azul (Fijo)</span></div></div>
            <div class='led-desc'>Control t&eacute;rmico PI activo en los reactores/tinas.</div>
          </div>
        </div>
        <div class='led-item' id='led-pulse_only'>
          <div class='led-dot dot-blue-pulse'></div>
          <div class='led-info'>
            <div class='led-state'><span>Salida de Corriente Pulsada</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(56,189,248,0.2);color:#7dd3fc'>Celeste (Pulsante)</span></div></div>
            <div class='led-desc'>Electrodeposici&oacute;n por pulsos activa.</div>
          </div>
        </div>
        <div class='led-item' id='led-dc_only'>
          <div class='led-dot dot-blue-light'></div>
          <div class='led-info'>
            <div class='led-state'><span>Salida de Corriente Continua (DC)</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(56,189,248,0.2);color:#7dd3fc'>Celeste (Fijo)</span></div></div>
            <div class='led-desc'>Corriente continua estable VCSS activa.</div>
          </div>
        </div>
        <div class='led-item' id='led-env_missing'>
          <div class='led-dot dot-amber'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sensores Ambientales Ausentes</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(245,158,11,0.2);color:#fcd34d'>&Aacute;mbar (Fijo)</span></div></div>
            <div class='led-desc'>Sensores ambientales AHT20/BMP280 no detectados; sistema operable.</div>
          </div>
        </div>
        <div class='led-item' id='led-standby_connected'>
          <div class='led-dot dot-green-solid'></div>
          <div class='led-info'>
            <div class='led-state'><span>Sistema en Reposo (Conectado)</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(16,185,129,0.2);color:#6ee7b7'>Verde (Fijo)</span></div></div>
            <div class='led-desc'>Todo OK. Operador conectado por Wi-Fi; planta en espera sin comandos activos.</div>
          </div>
        </div>
        <div class='led-item' id='led-standby_beacon'>
          <div class='led-dot dot-green-beacon'></div>
          <div class='led-info'>
            <div class='led-state'><span>En Espera de Conexi&oacute;n Wi-Fi</span><div style='display:flex;align-items:center;gap:6px;'><span class='active-pill'>&#9679; ACTIVO</span><span class='led-tag' style='background:rgba(16,185,129,0.15);color:#a7f3d0'>Verde (Destello)</span></div></div>
            <div class='led-desc'>Red Wi-Fi SoftAP "Uli" emitiendo baliza; esperando conexi&oacute;n del usuario.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

<script>
var sensores=[
  {key:'aht', name:'AHT20',        bus:'I2C', addr:'0x38',        desc:'Temp / Humedad', cat:'Ambiental', color:'#06b6d4'},
  {key:'bmp', name:'BMP280',       bus:'I2C', addr:'0x76/77',     desc:'Presi\u00f3n Atm.', cat:'Ambiental', color:'#06b6d4'},
  {key:'ads', name:'ADS1115',      bus:'I2C', addr:'0x48',        desc:'ADC pH 16-bit', cat:'pH / Sondas', color:'#a855f7'},
  {key:'dac', name:'MCP4725',      bus:'I2C', addr:'0x60',        desc:'DAC Corriente', cat:'Potencia VCSS', color:'#f59e0b'},
  {key:'tc0', name:'MAX6675 #0',   bus:'SPI', addr:'CS GPIO 5',  desc:'Limpieza', cat:'T\u00e9rmico', color:'#f97316'},
  {key:'tc1', name:'MAX6675 #1',   bus:'SPI', addr:'CS GPIO 4',  desc:'Decapado', cat:'T\u00e9rmico', color:'#f97316'},
  {key:'tc2', name:'MAX6675 #2',   bus:'SPI', addr:'CS GPIO 13', desc:'Celda Hull', cat:'T\u00e9rmico', color:'#f97316'},
  {key:'tc3', name:'MAX6675 #3',   bus:'SPI', addr:'CS GPIO 14', desc:'Niquelado', cat:'T\u00e9rmico', color:'#f97316'}
];

function highlightLedState(code){
  if(!code) return;
  var items = document.querySelectorAll('.led-item');
  for(var i=0; i<items.length; i++){
    items[i].classList.remove('active-led');
  }
  var target = document.getElementById('led-' + code);
  if(target){
    target.classList.add('active-led');
  }
}

function buildGrid(data){
  var ok=0,total=8;
  var h='';
  for(var i=0;i<sensores.length;i++){
    var s=sensores[i];
    var estado=-1;
    if(data){
      if(s.key==='aht') estado=data.aht;
      else if(s.key==='bmp') estado=data.bmp;
      else if(s.key==='ads') estado=data.ads;
      else if(s.key==='dac') estado=data.dac;
      else if(s.key==='tc0') estado=data.tc[0];
      else if(s.key==='tc1') estado=data.tc[1];
      else if(s.key==='tc2') estado=data.tc[2];
      else if(s.key==='tc3') estado=data.tc[3];
      if(estado===1) ok++;
    }
    var cls=estado===-1?'wait':(estado===1?'ok':'fail');
    var icon=estado===-1?'&#9898;':(estado===1?'&#9989;':'&#10060;');
    var stCls=estado===-1?'st-wait':(estado===1?'st-ok':'st-fail');
    var stTxt=estado===-1?'ESPERANDO':(estado===1?'EN L\u00cdNEA':'FALLO');

    var delay = i * 60;
    h+='<div class="s-card '+cls+'" style="animation-delay:'+delay+'ms">';
    h+='<div class="s-cat-tag" style="background:'+s.color+'20;color:'+s.color+';border:1px solid '+s.color+'40;">'+s.cat+'</div>';
    h+='<div class="s-icon">'+icon+'</div>';
    h+='<div class="s-name">'+s.name+'</div>';
    h+='<div class="s-bus">'+s.bus+' &middot; '+s.desc+'</div>';
    h+='<div class="s-addr">'+s.addr+'</div>';
    h+='<div class="s-status '+stCls+'">'+stTxt+'</div>';
    h+='</div>';
  }
  document.getElementById('grid').innerHTML=h;

  var sc=document.getElementById('sum-count');
  if(data){
    sc.innerText=ok+' / '+total;
    if(ok===total){sc.style.color='#34d399';}
    else if(ok>=6){sc.style.color='#fbbf24';}
    else{sc.style.color='#ef4444';}
    if(data.led){ highlightLedState(data.led); }
  }else{
    sc.innerText='- / 8';
    sc.style.color='#475569';
  }
}

function updHb(){
  var d=Date.now()-lastOk;
  var dot=document.getElementById('hb-dot');
  var txt=document.getElementById('hb-txt');
  if(d>6000){dot.className='hb-dot off';txt.innerText='Sin conexi\u00f3n';}
  else{dot.className='hb-dot';var s=Math.floor(d/1000);txt.innerText=s<2?'OK':'Hace '+s+'s';}
}
var lastOk=Date.now();

function escanear(){
  var btn=document.getElementById('btn-scan');
  btn.className='btn-scan scanning';
  btn.innerHTML='&#8987; ESCANEANDO...';
  btn.disabled=true;
  document.getElementById('scan-prog').className='scan-progress active';

  fetch('/data_sensors')
    .then(function(r){return r.json();})
    .then(function(data){
      lastOk=Date.now();
      buildGrid(data);
      var now=new Date();
      var timeStr=now.toLocaleTimeString();
      document.getElementById('ts').innerText='\u00daltimo escaneo: '+timeStr;
    })
    .catch(function(err){
      document.getElementById('ts').innerText='Error de comunicaci\u00f3n con ESP32';
    })
    .finally(function(){
      btn.className='btn-scan';
      btn.innerHTML='ESCANEAR SENSORES';
      btn.disabled=false;
      document.getElementById('scan-prog').className='scan-progress';
      updHb();
    });
}

buildGrid(null);
escanear();

setInterval(function(){
  fetch('/data_sensors')
    .then(function(r){return r.json();})
    .then(function(d){
      lastOk=Date.now();
      if(d && d.led) highlightLedState(d.led);
    })
    .catch(function(){});
}, 2500);
setInterval(updHb, 1000);
</script>
</body></html>
)rawliteral";

#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: DIAGNÓSTICO DE SENSORES (View_Sensores.h) — Versión 4.0
 * =================================================================================
 * Contiene el código HTML/CSS/JS del panel de diagnóstico bajo demanda
 * para los 8 periféricos del sistema (4 I2C + 4 SPI).
 * Almacenado en PROGMEM (Flash).
 */

const char HTML_SENSORES[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Estado de Sensores</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px;}
.container{max-width:760px;margin:0 auto;}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;}
.nav-back:hover{color:#7dd3fc;}
.hdr-t{font-size:1.1em;font-weight:800;color:#fff;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.62em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Summary */
.summary{text-align:center;margin-bottom:20px;padding:18px 16px;background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:16px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 20px rgba(0,0,0,0.35);}
.sum-count{font-size:2.4em;font-weight:900;letter-spacing:-2px;font-variant-numeric:tabular-nums;}
.sum-label{font-size:0.75em;color:#64748b;font-weight:700;margin-top:2px;letter-spacing:0.3px;}

/* Scan Button */
.btn-scan{display:block;width:100%;padding:14px 20px;margin-bottom:20px;cursor:pointer;border-radius:12px;border:1px solid rgba(56,189,248,0.2);background:linear-gradient(135deg,rgba(30,58,138,0.4),rgba(30,64,175,0.3));color:#93c5fd;font-weight:800;font-size:0.9em;transition:all 0.25s;letter-spacing:0.3px;}
.btn-scan:hover{background:linear-gradient(135deg,rgba(37,99,235,0.5),rgba(59,130,246,0.4));color:#bfdbfe;border-color:rgba(96,165,250,0.4);transform:translateY(-1px);box-shadow:0 6px 20px rgba(59,130,246,0.2);}
.btn-scan:active{transform:translateY(0);box-shadow:none;}
.btn-scan.scanning{opacity:0.6;cursor:wait;}

/* Grid */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;}

/* Sensor Card */
.s-card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:14px;padding:16px 14px;border:1px solid rgba(51,65,85,0.4);box-shadow:0 4px 16px rgba(0,0,0,0.3);transition:all 0.3s;text-align:center;border-left:4px solid #334155;}
.s-card.ok{border-left-color:#10b981;}
.s-card.fail{border-left-color:#ef4444;animation:pulse-fail 2s ease-in-out infinite;}
.s-card.wait{border-left-color:#334155;}

.s-icon{font-size:28px;margin-bottom:6px;line-height:1;}
.s-name{font-size:0.82em;color:#f1f5f9;font-weight:800;letter-spacing:-0.2px;}
.s-bus{font-size:0.62em;color:#475569;font-weight:700;margin-top:2px;letter-spacing:0.5px;text-transform:uppercase;}
.s-addr{font-size:0.65em;color:#64748b;font-weight:600;margin-top:4px;}
.s-status{margin-top:8px;padding:5px 12px;border-radius:8px;font-size:0.68em;font-weight:800;display:inline-block;letter-spacing:0.3px;}
.st-ok{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.st-fail{background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);}
.st-wait{background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;}

/* Timestamp */
.ts{text-align:center;margin-top:16px;font-size:0.68em;color:#475569;font-weight:600;}

/* Animations */
@keyframes pulse-fail{0%,100%{opacity:1;}50%{opacity:0.7;}}

/* Responsive */
@media(max-width:440px){
  .grid{grid-template-columns:repeat(2,1fr);gap:8px;}
  .s-card{padding:12px 10px;}
  .sum-count{font-size:1.8em;}
  .hdr{flex-wrap:wrap;gap:8px;}
}
</style></head>
<body>
  <div class='container'>
    <div class='hdr'>
      <a href='/' class='nav-back'>&larr; Men&uacute;</a>
      <div style='text-align:center'>
        <span class='hdr-t'>Diagn&oacute;stico de Sensores</span>
        <span class='hdr-sub'>I2C &middot; SPI &middot; 8 PERIF&Eacute;RICOS</span>
      </div>
      <div></div>
    </div>

    <div class='summary'>
      <div class='sum-count' id='sum-count' style='color:#475569'>- / 8</div>
      <div class='sum-label'>Sensores Operativos</div>
    </div>

    <button class='btn-scan' id='btn-scan' onclick='escanear()'>ESCANEAR SENSORES</button>

    <div class='grid' id='grid'></div>
    <div class='ts' id='ts'>Presione el bot&oacute;n para escanear</div>
  </div>

<script>
var sensores=[
  {key:'aht', name:'AHT20',        bus:'I2C', addr:'0x38',    desc:'Temp / Humedad'},
  {key:'bmp', name:'BMP280',       bus:'I2C', addr:'0x76/77', desc:'Presi\u00f3n Atm.'},
  {key:'ads', name:'ADS1115',      bus:'I2C', addr:'0x48',    desc:'ADC pH 16-bit'},
  {key:'dac', name:'MCP4725',      bus:'I2C', addr:'0x60',    desc:'DAC Corriente'},
  {key:'tc0', name:'MAX6675 #0',   bus:'SPI', addr:'CS GPIO 5',  desc:'Limpieza'},
  {key:'tc1', name:'MAX6675 #1',   bus:'SPI', addr:'CS GPIO 4',  desc:'Decapado'},
  {key:'tc2', name:'MAX6675 #2',   bus:'SPI', addr:'CS GPIO 13', desc:'Celda Hull'},
  {key:'tc3', name:'MAX6675 #3',   bus:'SPI', addr:'CS GPIO 14', desc:'Niquelado'}
];

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

    h+='<div class="s-card '+cls+'">';
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
  }else{
    sc.innerText='- / 8';
    sc.style.color='#475569';
  }
}

function escanear(){
  var btn=document.getElementById('btn-scan');
  btn.className='btn-scan scanning';
  btn.innerText='Escaneando...';
  fetch('/data_sensors').then(function(r){return r.json();}).then(function(d){
    buildGrid(d);
    var now=new Date();
    var hh=('0'+now.getHours()).slice(-2);
    var mm=('0'+now.getMinutes()).slice(-2);
    var ss=('0'+now.getSeconds()).slice(-2);
    document.getElementById('ts').innerText='\u00daltimo escaneo: '+hh+':'+mm+':'+ss;
    btn.className='btn-scan';
    btn.innerHTML='RE-ESCANEAR SENSORES';
  }).catch(function(){
    document.getElementById('ts').innerText='Error de comunicaci\u00f3n';
    btn.className='btn-scan';
    btn.innerHTML='REINTENTAR ESCANEO';
  });
}

buildGrid(null);
</script>
</body></html>
)rawliteral";

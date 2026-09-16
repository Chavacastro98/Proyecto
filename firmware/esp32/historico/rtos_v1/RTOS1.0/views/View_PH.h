#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MÓDULO DE PH 2.0 (View_PH.h) — Versión 4.0
 * =================================================================================
 * Contiene el código HTML/CSS/JS del panel de medición de pH dual (ADS1115 Canales A0/A1),
 * selector de modos de calibración (Teórico, 2 Puntos, 3 Puntos Dual-Slope),
 * diagnóstico de % Slope y voltímetro en tiempo real para offset de placa.
 * Almacenado en PROGMEM (Flash).
 */

const char HTML_PH[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>M&oacute;dulo pH 2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:0;}
.page{max-width:760px;margin:0 auto;padding:16px 14px 32px;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Toggle Switch */
.tog-wrap{display:flex;align-items:center;gap:10px;}
.tog{position:relative;width:54px;height:28px;background:#334155;border-radius:14px;cursor:pointer;transition:all 0.35s cubic-bezier(.4,0,.2,1);border:2px solid #475569;outline:none;}
.tog.on{background:#059669;border-color:#34d399;box-shadow:0 0 16px rgba(5,150,105,0.4);}
.tog::after{content:'';position:absolute;width:20px;height:20px;background:#f8fafc;border-radius:50%;top:2px;left:3px;transition:all 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 1px 4px rgba(0,0,0,0.3);}
.tog.on::after{left:27px;}
.tog-lbl{font-size:0.68em;color:#64748b;font-weight:800;letter-spacing:1px;min-width:58px;text-align:right;}
.tog-lbl.act{color:#34d399;}

/* Interlock Alert */
.il-alert{background:linear-gradient(135deg,rgba(127,29,29,0.25),rgba(153,27,27,0.15));border:1px solid rgba(239,68,68,0.4);color:#fca5a5;padding:12px 18px;border-radius:12px;text-align:center;margin-bottom:18px;font-weight:700;font-size:0.82em;display:none;letter-spacing:0.2px;}
.il-alert.vis{display:flex;align-items:center;justify-content:center;gap:8px;animation:pulse 2.5s ease-in-out infinite;}
.il-icon{width:18px;height:18px;background:#ef4444;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;color:white;font-weight:900;flex-shrink:0;}

/* Grid */
.grid{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;margin-bottom:20px;}

/* Card */
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:22px 20px;width:350px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 24px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);transition:all 0.3s;}
.card:hover{border-color:rgba(56,189,248,0.2);box-shadow:0 8px 40px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.05);}
.card-t{display:flex;align-items:center;gap:8px;margin-bottom:14px;}
.card-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.card-dot.t1{background:#38bdf8;box-shadow:0 0 6px rgba(56,189,248,0.5);}
.card-dot.t2{background:#a78bfa;box-shadow:0 0 6px rgba(167,139,250,0.5);}
.card-name{font-size:0.88em;color:#94a3b8;font-weight:700;}

/* pH Display */
.ph-wrap{text-align:center;padding:16px 0 12px;position:relative;}
.ph-ring{width:120px;height:120px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;border:3px solid #1e293b;background:rgba(15,23,42,0.6);transition:all 0.5s;}
.ph-ring.active{border-color:rgba(34,197,94,0.3);box-shadow:0 0 30px rgba(34,197,94,0.08);}
.ph-val{font-size:36px;font-weight:900;font-variant-numeric:tabular-nums;transition:color 0.4s;letter-spacing:-1px;}
.ph-val.off{color:#334155;font-size:28px;}
.ph-label{font-size:0.65em;color:#475569;font-weight:600;margin-top:6px;letter-spacing:0.5px;}

/* Mode Selector */
.mode-sel{display:flex;gap:4px;margin:12px 0;background:#0f172a;border-radius:10px;padding:3px;}
.mode-b{flex:1;padding:8px 4px;border-radius:8px;border:none;background:transparent;color:#64748b;font-size:0.68em;font-weight:800;cursor:pointer;transition:all 0.25s;text-align:center;letter-spacing:0.3px;}
.mode-b.act{background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;box-shadow:0 2px 8px rgba(59,130,246,0.3);}
.mode-b:hover:not(.act){color:#94a3b8;background:rgba(30,41,59,0.5);}

/* Calibration */
.cal-sec{background:rgba(15,23,42,0.5);border-radius:12px;padding:12px 14px;margin-top:12px;border:1px solid rgba(51,65,85,0.4);}
.cal-title{color:#475569;font-size:0.7em;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;text-transform:uppercase;}
.cal-btn{width:100%;padding:10px 12px;margin:4px 0;border-radius:8px;border:none;font-weight:700;cursor:pointer;font-size:0.78em;transition:all 0.2s;display:flex;align-items:center;gap:8px;text-align:left;}
.cal-btn .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.cb7{background:rgba(6,78,59,0.5);color:#6ee7b7;border:1px solid rgba(34,197,94,0.2);}
.cb7 .dot{background:#22c55e;}
.cb4{background:rgba(127,29,29,0.35);color:#fca5a5;border:1px solid rgba(239,68,68,0.2);}
.cb4 .dot{background:#ef4444;}
.cb10{background:rgba(30,58,138,0.35);color:#93c5fd;border:1px solid rgba(59,130,246,0.2);}
.cb10 .dot{background:#3b82f6;}
.cal-btn:hover{filter:brightness(1.3);transform:translateY(-1px);}

/* Calibration Status */
.cal-status-box{margin-top:14px;padding:8px 12px;border-radius:10px;text-align:center;font-size:0.75em;font-weight:700;letter-spacing:0.3px;}
.cs-ok{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.cs-pending{background:rgba(217,119,6,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);}
.cs-theory{background:rgba(30,58,138,0.25);color:#93c5fd;border:1px solid rgba(59,130,246,0.3);}

/* Offset Panel */
.off-panel{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:20px;border:1px solid rgba(251,191,36,0.1);box-shadow:0 4px 24px rgba(0,0,0,0.4);}
.off-hdr{display:flex;align-items:center;justify-content:space-between;}
.off-t{display:flex;align-items:center;gap:8px;font-weight:700;font-size:0.88em;}
.off-t-icon{width:28px;height:28px;border-radius:8px;background:rgba(251,191,36,0.12);display:flex;align-items:center;justify-content:center;font-size:14px;color:#fbbf24;}
.off-t-text{color:#fbbf24;}
.off-tog{background:#1e293b;color:#94a3b8;border:1px solid #334155;padding:7px 16px;border-radius:8px;cursor:pointer;font-size:0.75em;font-weight:800;transition:all 0.2s;letter-spacing:0.5px;}
.off-tog:hover{background:#334155;color:#e2e8f0;}
.off-tog.open{background:rgba(146,64,14,0.4);color:#fcd34d;border-color:rgba(251,191,36,0.3);}
.off-body{display:none;margin-top:16px;}
.off-desc{font-size:0.75em;color:#64748b;line-height:1.5;margin-bottom:14px;padding:10px 12px;background:rgba(15,23,42,0.5);border-radius:8px;border-left:3px solid #fbbf24;}

/* Voltmeter */
.vm-wrap{text-align:center;padding:10px 0;}
.vm-val{font-size:48px;font-weight:900;font-variant-numeric:tabular-nums;letter-spacing:-2px;line-height:1;}
.vm-unit{font-size:18px;color:#64748b;font-weight:600;margin-left:4px;}
.vm-mv{font-size:0.8em;color:#475569;margin-top:4px;}

/* Gauge */
.gauge-wrap{padding:4px 0 0;}
.gauge{position:relative;height:16px;border-radius:8px;overflow:visible;margin:20px 0 24px;background:linear-gradient(90deg,#dc2626 0%,#f59e0b 30%,#22c55e 42%,#22c55e 58%,#f59e0b 70%,#dc2626 100%);}
.gauge-tgt{position:absolute;top:-6px;left:50%;width:2px;height:28px;background:rgba(255,255,255,0.8);transform:translateX(-50%);z-index:2;}
.gauge-tgt::before{content:'1.650V';position:absolute;top:-18px;left:50%;transform:translateX(-50%);font-size:0.6em;color:rgba(255,255,255,0.6);white-space:nowrap;font-weight:700;}
.gauge-ndl{position:absolute;top:-4px;width:8px;height:24px;background:#f8fafc;border-radius:4px;transform:translateX(-50%);transition:left 0.3s ease-out;box-shadow:0 0 8px rgba(255,255,255,0.5),0 2px 4px rgba(0,0,0,0.3);z-index:3;}

/* Diff & Badge */
.off-diff{text-align:center;font-size:1.1em;font-weight:800;margin:8px 0 12px;letter-spacing:-0.5px;}
.off-badge-wrap{text-align:center;}
.off-badge{display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;letter-spacing:0.3px;}

/* Animations */
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}

/* Responsive */
@media(max-width:440px){
  .card{width:100%;}
  .ph-val{font-size:30px;}
  .ph-ring{width:100px;height:100px;}
  .vm-val{font-size:38px;}
  .hdr{flex-wrap:wrap;gap:8px;}
  .hdr-title{font-size:0.95em;}
}
</style></head>
<body>
<div class='page'>

<!-- Header -->
<div class='hdr'>
  <a href='/' class='nav-back'>&larr; Men&uacute;</a>
  <div style='text-align:center'>
    <span class='hdr-title'>M&oacute;dulo de pH</span>
    <span class='hdr-sub'>ADS1115 &middot; 16-BIT &middot; DUAL CHANNEL</span>
  </div>
  <div class='tog-wrap'>
    <span class='tog-lbl' id='tog-lbl'>STANDBY</span>
    <button class='tog' id='ph-tog' onclick='togglePH()'></button>
  </div>
</div>

<!-- Interlock Alert -->
<div class='il-alert' id='il-alert'>
  <span class='il-icon'>!</span>
  INTERLOCK &mdash; Apague el sistema t&eacute;rmico y la fuente antes de activar pH
</div>

<!-- pH Cards -->
<div class='grid'>

  <!-- TINA 1 -->
  <div class='card'>
    <div class='card-t'><span class='card-dot t1'></span><span class='card-name'>Electrodo pH 1 &mdash; Zincado</span></div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring1'>
        <span class='ph-val off' id='ph1'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL 0 &middot; ADS1115</div>
    </div>
    <div class='mode-sel'>
      <button class='mode-b act' id='m1-0' onclick='setMode(1,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m1-1' onclick='setMode(1,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m1-2' onclick='setMode(1,2)'>3 PUNTOS</button>
    </div>
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodos</div>
      <button class='cal-btn cb7' onclick='calibrar(1,7)'><span class='dot'></span>Calibrar Buffer pH 7.0</button>
      <button class='cal-btn cb4' id='cal-1-4' onclick='calibrar(1,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0</button>
      <button class='cal-btn cb10' id='cal-1-10' onclick='calibrar(1,10)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 10.0</button>
    </div>
    <div class='cal-status-box cs-theory' id='cstat1'>Modo Te&oacute;rico (Preconfigurado)</div>
  </div>

  <!-- TINA 2 -->
  <div class='card'>
    <div class='card-t'><span class='card-dot t2'></span><span class='card-name'>Electrodo pH 2 &mdash; Niquelado</span></div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring2'>
        <span class='ph-val off' id='ph2'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL 1 &middot; ADS1115</div>
    </div>
    <div class='mode-sel'>
      <button class='mode-b act' id='m2-0' onclick='setMode(2,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m2-1' onclick='setMode(2,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m2-2' onclick='setMode(2,2)'>3 PUNTOS</button>
    </div>
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodos</div>
      <button class='cal-btn cb7' onclick='calibrar(2,7)'><span class='dot'></span>Calibrar Buffer pH 7.0</button>
      <button class='cal-btn cb4' id='cal-2-4' onclick='calibrar(2,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0</button>
      <button class='cal-btn cb10' id='cal-2-10' onclick='calibrar(2,10)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 10.0</button>
    </div>
    <div class='cal-status-box cs-theory' id='cstat2'>Modo Te&oacute;rico (Preconfigurado)</div>
  </div>
</div>

<!-- Offset Panel -->
<div class='off-panel'>
  <div class='off-hdr'>
    <div class='off-t'>
      <span class='off-t-icon'>&#9881;</span>
      <span class='off-t-text'>Ajuste de Offset de Placa</span>
    </div>
    <button class='off-tog' id='off-tog' onclick='toggleOffset()'>ABRIR</button>
  </div>
  <div class='off-body' id='off-body'>
    <div class='off-desc'>
      Conecte el BNC en cortocircuito (sin sonda). Ajuste el potenci&oacute;metro de la placa PH-4502C
      hasta que el voltaje sea <b style='color:#fbbf24'>1.650 V</b> (&plusmn;10 mV).
    </div>
    <div class='vm-wrap'>
      <span class='vm-val' id='raw-v'>0.000</span><span class='vm-unit'>V</span>
      <div class='vm-mv' id='raw-mv'>0.0 mV</div>
    </div>
    <div class='gauge-wrap'>
      <div class='gauge'>
        <div class='gauge-tgt'></div>
        <div class='gauge-ndl' id='g-ndl' style='left:50%'></div>
      </div>
    </div>
    <div class='off-diff' id='off-diff'>+0.0 mV</div>
    <div class='off-badge-wrap'>
      <span class='off-badge' id='off-badge'
            style='background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;'>
        Esperando lectura...
      </span>
    </div>
  </div>
</div>

</div><!-- /page -->

<script>
var phOn=false,ilAct=false,curM1=0,curM2=0;
var rawIv=null,offOpen=false;

function fetchPH(){
  fetch('/get_ph_dual').then(function(r){return r.json();}).then(function(d){
    phOn=(d.on==1);ilAct=(d.il==1);
    curM1=parseInt(d.m1);curM2=parseInt(d.m2);
    var tg=document.getElementById('ph-tog');
    tg.className=phOn?'tog on':'tog';
    var tl=document.getElementById('tog-lbl');
    tl.innerText=phOn?'ACTIVO':'STANDBY';
    tl.className=phOn?'tog-lbl act':'tog-lbl';
    var ia=document.getElementById('il-alert');
    ia.className=ilAct?'il-alert vis':'il-alert';
    updPH(1,d.p1,phOn);updPH(2,d.p2,phOn);
    updMode(1,curM1);updMode(2,curM2);
    updCal(1,curM1);updCal(2,curM2);
    updCalStatus(1,curM1,d.c1);
    updCalStatus(2,curM2,d.c2);
  }).catch(function(){});
}

function updPH(tina,val,on){
  var el=document.getElementById('ph'+tina);
  var ring=document.getElementById('ring'+tina);
  if(!on){el.innerHTML='&mdash;';el.className='ph-val off';ring.className='ph-ring';return;}
  var v=parseFloat(val);
  if(isNaN(v)||v<0||v>14){el.innerText='ERR';el.className='ph-val';el.style.color='#ef4444';ring.className='ph-ring';return;}
  el.innerText=v.toFixed(2);el.className='ph-val';ring.className='ph-ring active';
  var h;
  if(v<=3)h=0;
  else if(v<=7)h=(v-3)/4*120;
  else if(v<=11)h=120+(v-7)/4*120;
  else{h=240;if(v>11)h+=Math.min((v-11)/3*40,40);}
  el.style.color='hsl('+Math.round(h)+',75%,58%)';
  ring.style.borderColor='hsla('+Math.round(h)+',75%,58%,0.25)';
  ring.style.boxShadow='0 0 24px hsla('+Math.round(h)+',75%,58%,0.1)';
}

function togglePH(){
  if(ilAct&&!phOn){
    alert('¡Bloqueado por Interlock!\nEl sistema térmico o la fuente de corriente están activos.\nDebes apagarlos manualmente en sus menús antes de medir pH.');
    return;
  }
  fetch('/act_ph?run='+(phOn?0:1)).then(function(r){
    if(r.status===403)alert('¡Bloqueado por Interlock!\nDebes apagar el sistema térmico y la fuente de corriente manualmente primero.');
    fetchPH();
  });
}

function setMode(t,m){fetch('/set_cal_mode?id='+t+'&m='+m).then(function(){fetchPH();});}
function updMode(t,m){for(var i=0;i<3;i++){var b=document.getElementById('m'+t+'-'+i);if(b)b.className=(i===m)?'mode-b act':'mode-b';}}

function updCal(t,m){
  var b4=document.getElementById('cal-'+t+'-4');
  var b10=document.getElementById('cal-'+t+'-10');
  if(b4)b4.style.display=(m>=1)?'flex':'none';
  if(b10)b10.style.display=(m===2)?'flex':'none';
}

function calibrar(t,p){
  if(!confirm('Confirmar calibracion pH '+p+'.0 en Tina '+t+'?\nAsegurese de que la sonda este sumergida en el buffer.'))return;
  fetch('/do_cal_ph?id='+t+'&p='+p).then(function(r){return r.json();}).then(function(d){
    if(d.ok==1){
      var info='Punto pH '+p+'.0 guardado en NVS.\nVoltaje medido: '+d.v+' V';
      if(parseFloat(d.slope)!==0) info+='\nPendiente calculada: '+d.slope+' pH/V';
      alert(info);
    }else{alert('Error de calibracion');}
    fetchPH();
  }).catch(function(){alert('Error de comunicacion');});
}

function updCalStatus(t,m,cal){
  var el=document.getElementById('cstat'+t);
  if(!el)return;
  if(m===0){
    el.className='cal-status-box cs-theory';
    el.innerHTML='Modo Te&oacute;rico (Preconfigurado)';
  }else if(m===1){
    if(parseInt(cal)===1){
      el.className='cal-status-box cs-ok';
      el.innerHTML='&#10003; Calibrado 2 Puntos (pH 7 + 4)';
    }else{
      el.className='cal-status-box cs-pending';
      el.innerHTML='Pendiente calibrar pH 7 y 4';
    }
  }else if(m===2){
    if(parseInt(cal)===1){
      el.className='cal-status-box cs-ok';
      el.innerHTML='&#10003; Calibrado 3 Puntos (pH 4, 7, 10)';
    }else{
      el.className='cal-status-box cs-pending';
      el.innerHTML='Pendiente calibrar pH 4, 7 y 10';
    }
  }
}

function toggleOffset(){
  offOpen=!offOpen;
  document.getElementById('off-body').style.display=offOpen?'block':'none';
  var btn=document.getElementById('off-tog');
  btn.innerText=offOpen?'CERRAR':'ABRIR';
  btn.className=offOpen?'off-tog open':'off-tog';
  if(offOpen){rawIv=setInterval(fetchRaw,250);fetchRaw();}
  else{if(rawIv){clearInterval(rawIv);rawIv=null;}}
}

function fetchRaw(){
  fetch('/data_ph_raw').then(function(r){return r.json();}).then(function(d){
    var v=parseFloat(d.v);
    document.getElementById('raw-v').innerText=v.toFixed(3);
    document.getElementById('raw-mv').innerText=d.mv+' mV';
    var pct=(v/3.3)*100;if(pct<0)pct=0;if(pct>100)pct=100;
    document.getElementById('g-ndl').style.left=pct+'%';
    var diff=v-1.650;var diffEl=document.getElementById('off-diff');
    var diffMv=diff*1000;
    diffEl.innerText=(diff>=0?'+':'')+diffMv.toFixed(1)+' mV';
    var badge=document.getElementById('off-badge');
    var ad=Math.abs(diff);
    if(ad<0.010){
      diffEl.style.color='#34d399';
      badge.innerText='Calibrado (\u00b110 mV)';
      badge.style.cssText='background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }else if(ad<0.050){
      diffEl.style.color='#fbbf24';
      badge.innerText='Ajustar potenciometro';
      badge.style.cssText='background:rgba(217,119,6,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }else{
      diffEl.style.color='#ef4444';
      badge.innerText='Fuera de rango';
      badge.style.cssText='background:rgba(220,38,38,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }
  }).catch(function(){});
}

setInterval(fetchPH,1500);fetchPH();
</script>
</body></html>
)rawliteral";

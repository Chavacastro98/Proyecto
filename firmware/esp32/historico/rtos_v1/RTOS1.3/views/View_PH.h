#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: MÓDULO DE PH METROLÓGICO DUAL (View_PH.h) — Versión RTOS 1.2
 * =================================================================================
 * MEJORAS v1.2:
 *   • Doble voltímetro independiente para ajuste de offset de placa en corto (A0 y A1).
 *   • Voltímetros digitales y agujas independientes para calibración de potenciómetros PH-4502C.
 *   • Voltajes analógicos reales medidos en ADC (3.53V) y Sonda (5.0V) en cada tarjeta.
 *   • Modal de calibración con temporizador de estabilización (3s) y aviso de permanencia en buffer.
 *   • Verificación de coherencia de buffers (ácido/neutro/básico) y detección de dispersión.
 *   • Botón de restablecimiento de calibración a valores de fábrica por canal (Flash NVS).
 *   • Mantenimiento estricto del interlock de seguridad con actuadores de potencia.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_PH[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>M&oacute;dulo pH Dual &middot; RTOS 1.2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:0;}
.page{max-width:820px;margin:0 auto;padding:16px 14px 36px;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.15em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}
.hdr-right{display:flex;align-items:center;gap:12px;}
.hdr-hb{display:flex;align-items:center;gap:5px;font-size:0.62em;font-weight:700;color:#475569;}
.hb-dot{width:6px;height:6px;border-radius:50%;background:#34d399;box-shadow:0 0 5px #34d399;animation:hb-p 2s ease-in-out infinite;}
.hb-dot.off{background:#ef4444;box-shadow:0 0 5px #ef4444;animation:none;}
@keyframes hb-p{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.35;transform:scale(0.7);}}

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
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}

/* Card */
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:22px 20px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 24px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);transition:all 0.3s;}
.card:hover{border-color:rgba(56,189,248,0.2);box-shadow:0 8px 40px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.05);}
.card-t{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.card-t-left{display:flex;align-items:center;gap:8px;}
.card-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.card-dot.t1{background:#38bdf8;box-shadow:0 0 6px rgba(56,189,248,0.5);}
.card-dot.t2{background:#a78bfa;box-shadow:0 0 6px rgba(167,139,250,0.5);}
.card-name{font-size:0.88em;color:#94a3b8;font-weight:700;}
.card-slope-badge{font-size:0.65em;padding:3px 8px;border-radius:6px;background:rgba(56,189,248,0.1);color:#38bdf8;font-weight:800;border:1px solid rgba(56,189,248,0.2);}

/* pH Display */
.ph-wrap{text-align:center;padding:14px 0 10px;position:relative;}
.ph-ring{width:118px;height:118px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;border:3px solid #1e293b;background:rgba(15,23,42,0.6);transition:border-color 0.6s ease,box-shadow 0.6s ease;}
.ph-ring.active{border-color:rgba(34,197,94,0.3);box-shadow:0 0 30px rgba(34,197,94,0.08);}
.ph-val{font-size:36px;font-weight:900;font-variant-numeric:tabular-nums;transition:color 0.5s;letter-spacing:-1px;}
.ph-val.off{color:#334155;font-size:28px;}
.ph-label{font-size:0.65em;color:#475569;font-weight:600;margin-top:6px;letter-spacing:0.5px;}

/* pH Scale Indicator */
.ph-scale{display:flex;justify-content:space-between;padding:4px 14px;margin-top:6px;font-size:0.55em;font-weight:700;color:#475569;}
.ph-scale-bar{height:4px;border-radius:2px;margin:0 14px;background:linear-gradient(90deg,#ef4444,#f59e0b,#22c55e,#3b82f6,#8b5cf6);opacity:0.3;transition:opacity 0.3s;}
.ph-scale-bar.on{opacity:0.7;}

/* Mode Selector */
.mode-sel{display:flex;gap:4px;margin:12px 0;background:#0f172a;border-radius:10px;padding:3px;}
.mode-b{flex:1;padding:8px 4px;border-radius:8px;border:none;background:transparent;color:#64748b;font-size:0.68em;font-weight:800;cursor:pointer;transition:all 0.25s;text-align:center;letter-spacing:0.3px;}
.mode-b.act{background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;box-shadow:0 2px 8px rgba(59,130,246,0.3);}
.mode-b:hover:not(.act){color:#94a3b8;background:rgba(30,41,59,0.5);}

/* Calibration */
.cal-sec{background:rgba(15,23,42,0.5);border-radius:12px;padding:12px 14px;margin-top:12px;border:1px solid rgba(51,65,85,0.4);}
.cal-title{color:#475569;font-size:0.7em;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;text-transform:uppercase;}
.cal-btn{width:100%;padding:9px 12px;margin:4px 0;border-radius:8px;border:none;font-weight:700;cursor:pointer;font-size:0.78em;transition:all 0.2s;display:flex;align-items:center;gap:8px;text-align:left;}
.cal-btn .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.cal-btn:disabled{opacity:0.5;cursor:wait;}
.cb7{background:rgba(6,78,59,0.5);color:#6ee7b7;border:1px solid rgba(34,197,94,0.2);}
.cb7 .dot{background:#22c55e;}
.cb4{background:rgba(127,29,29,0.35);color:#fca5a5;border:1px solid rgba(239,68,68,0.2);}
.cb4 .dot{background:#ef4444;}
.cb10{background:rgba(30,58,138,0.35);color:#93c5fd;border:1px solid rgba(59,130,246,0.2);}
.cb10 .dot{background:#3b82f6;}
.cal-btn:hover:not(:disabled){filter:brightness(1.25);transform:translateY(-1px);}

/* Reset Button */
.btn-rst-ph{width:100%;margin-top:8px;padding:7px 10px;background:transparent;border:1px dashed #475569;color:#94a3b8;border-radius:8px;font-size:0.72em;font-weight:700;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;justify-content:center;gap:6px;}
.btn-rst-ph:hover{border-color:#ef4444;color:#fca5a5;background:rgba(239,68,68,0.08);}

/* Calibration Status */
.cal-status-box{margin-top:12px;padding:8px 12px;border-radius:10px;text-align:center;font-size:0.75em;font-weight:700;letter-spacing:0.3px;transition:all 0.3s;}
.cs-ok{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.cs-pending{background:rgba(217,119,6,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);}
.cs-theory{background:rgba(30,58,138,0.25);color:#93c5fd;border:1px solid rgba(59,130,246,0.3);}

/* Diagnostics Voltmeter in Card */
.diag-box{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px;}
.diag-item{background:rgba(15,23,42,0.6);border-radius:8px;padding:7px 8px;border:1px solid rgba(51,65,85,0.3);text-align:center;}
.diag-lbl{font-size:0.58em;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:0.3px;}
.diag-val{font-size:0.88em;color:#f8fafc;font-weight:800;font-variant-numeric:tabular-nums;margin-top:2px;}

/* Dual Hardware Offset Panel */
.off-panel{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:20px;border:1px solid rgba(251,191,36,0.12);box-shadow:0 4px 24px rgba(0,0,0,0.4);}
.off-hdr{display:flex;align-items:center;justify-content:space-between;}
.off-t{display:flex;align-items:center;gap:8px;font-weight:700;font-size:0.88em;}
.off-t-icon{width:28px;height:28px;border-radius:8px;background:rgba(251,191,36,0.12);display:flex;align-items:center;justify-content:center;font-size:14px;color:#fbbf24;}
.off-t-text{color:#fbbf24;}
.off-tog{background:#1e293b;color:#94a3b8;border:1px solid #334155;padding:7px 16px;border-radius:8px;cursor:pointer;font-size:0.75em;font-weight:800;transition:all 0.2s;letter-spacing:0.5px;}
.off-tog:hover{background:#334155;color:#e2e8f0;}
.off-tog.open{background:rgba(146,64,14,0.4);color:#fcd34d;border-color:rgba(251,191,36,0.3);}
.off-body{display:none;margin-top:16px;}
.off-desc{font-size:0.76em;color:#94a3b8;line-height:1.5;margin-bottom:16px;padding:10px 14px;background:rgba(15,23,42,0.6);border-radius:10px;border-left:3px solid #fbbf24;}

/* Dual Voltmeter Columns */
.off-dual-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.off-ch-card{background:rgba(15,23,42,0.7);border-radius:14px;padding:16px 14px;border:1px solid rgba(51,65,85,0.4);text-align:center;position:relative;}
.off-ch-title{display:flex;align-items:center;justify-content:center;gap:6px;font-size:0.75em;font-weight:800;letter-spacing:0.3px;margin-bottom:8px;}
.off-ch-title.c1{color:#38bdf8;}
.off-ch-title.c2{color:#c084fc;}

.vm-wrap{padding:4px 0;}
.vm-val{font-size:38px;font-weight:900;font-variant-numeric:tabular-nums;letter-spacing:-1.5px;line-height:1;transition:color 0.3s;}
.vm-unit{font-size:16px;color:#64748b;font-weight:600;margin-left:3px;}
.vm-mv{font-size:0.75em;color:#64748b;font-weight:700;margin-top:3px;}

.gauge-wrap{padding:6px 4px 0;}
.gauge{position:relative;height:12px;border-radius:6px;overflow:visible;margin:16px 0 20px;background:linear-gradient(90deg,#dc2626 0%,#f59e0b 30%,#22c55e 42%,#22c55e 58%,#f59e0b 70%,#dc2626 100%);}
.gauge-tgt{position:absolute;top:-5px;left:50%;width:2px;height:22px;background:rgba(255,255,255,0.85);transform:translateX(-50%);z-index:2;}
.gauge-tgt::before{content:'1.765V';position:absolute;top:-16px;left:50%;transform:translateX(-50%);font-size:0.55em;color:rgba(255,255,255,0.7);white-space:nowrap;font-weight:700;}
.gauge-ndl{position:absolute;top:-3px;width:6px;height:18px;background:#f8fafc;border-radius:3px;transform:translateX(-50%);transition:left 0.25s ease-out;box-shadow:0 0 8px rgba(255,255,255,0.5);z-index:3;}

.off-diff{font-size:0.95em;font-weight:800;margin:4px 0 8px;letter-spacing:-0.3px;transition:color 0.3s;}
.off-badge{display:inline-block;padding:5px 12px;border-radius:16px;font-weight:800;font-size:0.72em;letter-spacing:0.3px;transition:all 0.3s;}

/* Modal de Calibración con Estabilización */
.modal-backdrop{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.75);backdrop-filter:blur(4px);display:none;align-items:center;justify-content:center;z-index:9998;padding:16px;}
.modal-backdrop.open{display:flex;animation:fade-in 0.25s ease-out;}
.modal-box{background:linear-gradient(165deg,#1e293b,#0f172a);border-radius:20px;border:1px solid rgba(56,189,248,0.25);width:100%;max-width:440px;padding:24px 22px;box-shadow:0 20px 50px rgba(0,0,0,0.6);text-align:center;}
.modal-icon{width:46px;height:46px;border-radius:12px;background:rgba(56,189,248,0.12);color:#38bdf8;font-size:22px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;border:1px solid rgba(56,189,248,0.2);}
.modal-title{font-size:1.15em;font-weight:800;color:#fff;}
.modal-subtitle{font-size:0.75em;color:#94a3b8;font-weight:600;margin-top:3px;}

/* Notice Box */
.buffer-warning-box{background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.35);border-radius:12px;padding:12px 14px;margin:16px 0;text-align:left;font-size:0.76em;line-height:1.45;color:#fde68a;}
.buffer-warning-box b{color:#fbbf24;display:block;margin-bottom:3px;font-size:0.95em;}

/* Progress and Countdown */
.modal-timer-wrap{margin:18px 0 10px;}
.modal-timer-num{font-size:2.4em;font-weight:900;color:#38bdf8;line-height:1;}
.modal-timer-lbl{font-size:0.68em;color:#64748b;font-weight:700;margin-top:2px;text-transform:uppercase;letter-spacing:0.5px;}
.modal-prog-bar{height:6px;background:rgba(51,65,85,0.4);border-radius:3px;margin:12px 10px 8px;overflow:hidden;}
.modal-prog-fill{height:100%;width:0%;background:linear-gradient(90deg,#38bdf8,#3b82f6);border-radius:3px;transition:width 0.1s linear;}
.modal-status-txt{font-size:0.75em;color:#94a3b8;font-weight:600;}

/* Toast */
.toast-container{position:fixed;bottom:20px;right:20px;display:flex;flex-direction:column;gap:8px;z-index:9999;pointer-events:none;}
.toast{padding:12px 18px;border-radius:12px;font-size:0.82em;font-weight:700;color:#fff;pointer-events:auto;animation:toast-in 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 8px 24px rgba(0,0,0,0.4);max-width:360px;}
.toast.out{animation:toast-out 0.3s forwards;}
.toast-ok{background:linear-gradient(135deg,#059669,#047857);border:1px solid #34d399;}
.toast-err{background:linear-gradient(135deg,#b91c1c,#991b1b);border:1px solid #ef4444;}
.toast-warn{background:linear-gradient(135deg,#b45309,#92400e);border:1px solid #f59e0b;}
.toast-info{background:linear-gradient(135deg,#1e40af,#1e3a8a);border:1px solid #38bdf8;}
@keyframes toast-in{from{opacity:0;transform:translateY(20px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
@keyframes toast-out{to{opacity:0;transform:translateY(-10px) scale(0.95);}}
@keyframes fade-in{from{opacity:0;}to{opacity:1;}}

/* Responsive */
@media(max-width:700px){
  .grid{grid-template-columns:1fr;}
  .off-dual-grid{grid-template-columns:1fr;}
  .hdr{flex-wrap:wrap;gap:8px;}
}
</style></head>
<body>
<div class='page'>

<!-- Header -->
<div class='hdr'>
  <a href='/' class='nav-back'>&larr; Men&uacute;</a>
  <div style='text-align:center'>
    <span class='hdr-title'>M&oacute;dulo de pH Metrol&oacute;gico Dual</span>
    <span class='hdr-sub'>ADS1115 &middot; 16-BIT &middot; FREERTOS 1.2</span>
  </div>
  <div class='hdr-right'>
    <div class='hdr-hb'><span class='hb-dot' id='hb-dot'></span><span id='hb-txt'>...</span></div>
    <div class='tog-wrap'>
      <span class='tog-lbl' id='tog-lbl'>STANDBY</span>
      <button class='tog' id='ph-tog' onclick='togglePH()'></button>
    </div>
  </div>
</div>

<!-- Interlock Alert -->
<div class='il-alert' id='il-alert'>
  <span class='il-icon'>!</span>
  INTERLOCK &mdash; Apague el sistema t&eacute;rmico y la fuente antes de activar o calibrar pH
</div>

<!-- pH Cards -->
<div class='grid'>

  <!-- TINA 1 -->
  <div class='card'>
    <div class='card-t'>
      <div class='card-t-left'><span class='card-dot t1'></span><span class='card-name'>Tina Zincado &middot; Canal A0</span></div>
      <span class='card-slope-badge' id='sl-lbl1'>Nernst: 100%</span>
    </div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring1'>
        <span class='ph-val off' id='ph1'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL A0 &middot; TINA ZINCADO</div>
    </div>
    <div class='ph-scale-bar' id='scale1'></div>
    <div class='ph-scale'><span>0 (Ácido)</span><span>4</span><span>7</span><span>10</span><span>14 (Alcalino)</span></div>
    
    <div class='mode-sel'>
      <button class='mode-b act' id='m1-0' onclick='setMode(1,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m1-1' onclick='setMode(1,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m1-2' onclick='setMode(1,2)'>3 PUNTOS</button>
    </div>
    
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodo</div>
      <button class='cal-btn cb7' id='cal-1-7' onclick='iniciarCalibracion(1,7)'><span class='dot'></span>Calibrar Buffer pH 7.0 (Neutro)</button>
      <button class='cal-btn cb4' id='cal-1-4' onclick='iniciarCalibracion(1,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0 (&Aacute;cido)</button>
      <button class='cal-btn cb10' id='cal-1-10' onclick='iniciarCalibracion(1,10)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 10.0 (B&aacute;sico)</button>
      <button class='btn-rst-ph' id='rst-1' onclick='resetCalibracion(1)'>&#8634; Restablecer Calibraci&oacute;n de F&aacute;brica</button>
    </div>
    
    <div class='cal-status-box cs-theory' id='cstat1'>Modo Te&oacute;rico (Preconfigurado)</div>
    
    <div class='diag-box'>
      <div class='diag-item'>
        <div class='diag-lbl'>Voltaje Sonda (5.0V)</div>
        <div class='diag-val' id='vs1' style='color:#38bdf8'>--- V</div>
      </div>
      <div class='diag-item'>
        <div class='diag-lbl'>Voltaje ADC (3.53V)</div>
        <div class='diag-val' id='va1'>--- V</div>
      </div>
    </div>
  </div>

  <!-- TINA 2 -->
  <div class='card'>
    <div class='card-t'>
      <div class='card-t-left'><span class='card-dot t2'></span><span class='card-name'>Tina Niquelado &middot; Canal A1</span></div>
      <span class='card-slope-badge' id='sl-lbl2'>Nernst: 100%</span>
    </div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring2'>
        <span class='ph-val off' id='ph2'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL A1 &middot; TINA NIQUELADO</div>
    </div>
    <div class='ph-scale-bar' id='scale2'></div>
    <div class='ph-scale'><span>0 (Ácido)</span><span>4</span><span>7</span><span>10</span><span>14 (Alcalino)</span></div>
    
    <div class='mode-sel'>
      <button class='mode-b act' id='m2-0' onclick='setMode(2,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m2-1' onclick='setMode(2,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m2-2' onclick='setMode(2,2)'>3 PUNTOS</button>
    </div>
    
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodo</div>
      <button class='cal-btn cb7' id='cal-2-7' onclick='iniciarCalibracion(2,7)'><span class='dot'></span>Calibrar Buffer pH 7.0 (Neutro)</button>
      <button class='cal-btn cb4' id='cal-2-4' onclick='iniciarCalibracion(2,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0 (&Aacute;cido)</button>
      <button class='cal-btn cb10' id='cal-2-10' onclick='iniciarCalibracion(2,10)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 10.0 (B&aacute;sico)</button>
      <button class='btn-rst-ph' id='rst-2' onclick='resetCalibracion(2)'>&#8634; Restablecer Calibraci&oacute;n de F&aacute;brica</button>
    </div>
    
    <div class='cal-status-box cs-theory' id='cstat2'>Modo Te&oacute;rico (Preconfigurado)</div>
    
    <div class='diag-box'>
      <div class='diag-item'>
        <div class='diag-lbl'>Voltaje Sonda (5.0V)</div>
        <div class='diag-val' id='vs2' style='color:#a78bfa'>--- V</div>
      </div>
      <div class='diag-item'>
        <div class='diag-lbl'>Voltaje ADC (3.53V)</div>
        <div class='diag-val' id='va2'>--- V</div>
      </div>
    </div>
  </div>

</div>

<!-- Dual Hardware Offset Panel -->
<div class='off-panel'>
  <div class='off-hdr'>
    <div class='off-t'>
      <span class='off-t-icon'>&#9881;</span>
      <span class='off-t-text'>Ajuste de Offset de Hardware (Placas PH-4502C en Corto)</span>
    </div>
    <button class='off-tog' id='off-tog' onclick='toggleOffset()'>ABRIR</button>
  </div>
  
  <div class='off-body' id='off-body'>
    <div class='off-desc'>
      <b>Instrucciones de Alineaci&oacute;n:</b> Conecte el BNC en cortocircuito (sin electrodo).
      Ajuste el potenci&oacute;metro multivuelta de cada placa PH-4502C hasta que su respectivo volt&iacute;metro marque exactamente
      <b style='color:#fbbf24'>1.765 V (&plusmn;10 mV)</b>. Esto establece el cero anal&oacute;gico neutro en pH 7.00.
    </div>
    
    <div class='off-dual-grid'>
      <!-- Placa 1: Tina Zincado Canal A0 -->
      <div class='off-ch-card'>
        <div class='off-ch-title c1'><span>&#9679;</span> PLACA 1: TINA ZINCADO (ADS1115 A0)</div>
        <div class='vm-wrap'>
          <span class='vm-val' id='raw-v1'>0.000</span><span class='vm-unit'>V</span>
          <div class='vm-mv' id='raw-mv1'>0.0 mV</div>
        </div>
        <div class='gauge-wrap'>
          <div class='gauge'>
            <div class='gauge-tgt'></div>
            <div class='gauge-ndl' id='g-ndl1' style='left:50%'></div>
          </div>
        </div>
        <div class='off-diff' id='off-diff1'>+0.0 mV</div>
        <div>
          <span class='off-badge' id='off-badge1' style='background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;'>
            Esperando lectura...
          </span>
        </div>
      </div>

      <!-- Placa 2: Tina Niquelado Canal A1 -->
      <div class='off-ch-card'>
        <div class='off-ch-title c2'><span>&#9679;</span> PLACA 2: TINA NIQUELADO (ADS1115 A1)</div>
        <div class='vm-wrap'>
          <span class='vm-val' id='raw-v2'>0.000</span><span class='vm-unit'>V</span>
          <div class='vm-mv' id='raw-mv2'>0.0 mV</div>
        </div>
        <div class='gauge-wrap'>
          <div class='gauge'>
            <div class='gauge-tgt'></div>
            <div class='gauge-ndl' id='g-ndl2' style='left:50%'></div>
          </div>
        </div>
        <div class='off-diff' id='off-diff2'>+0.0 mV</div>
        <div>
          <span class='off-badge' id='off-badge2' style='background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;'>
            Esperando lectura...
          </span>
        </div>
      </div>
    </div>
  </div>
</div>

</div><!-- /page -->

<!-- Modal de Estabilización de Calibración -->
<div class='modal-backdrop' id='cal-modal'>
  <div class='modal-box'>
    <div class='modal-icon'>🧪</div>
    <div class='modal-title' id='cal-m-title'>Calibrando pH 7.0</div>
    <div class='modal-subtitle' id='cal-m-sub'>Tina Zincado &middot; Canal A0</div>
    
    <div class='buffer-warning-box'>
      <b>&#9888; ATENCI&Oacute;N METROL&Oacute;GICA:</b>
      Mantenga el electrodo completamente sumergido en la soluci&oacute;n buffer y <b>SIN MOVERLO</b> durante los 3 segundos de muestreo para asegurar la estabilidad electroqu&iacute;mica.
    </div>

    <div class='modal-timer-wrap'>
      <div class='modal-timer-num' id='cal-timer'>3</div>
      <div class='modal-timer-lbl'>Segundos Restantes</div>
    </div>

    <div class='modal-prog-bar'>
      <div class='modal-prog-fill' id='cal-prog'></div>
    </div>

    <div class='modal-status-txt' id='cal-m-status'>Estabilizando lectura y verificando dispersi&oacute;n...</div>
  </div>
</div>

<div class='toast-container' id='toast-box'></div>

<script>
var phOn=false,ilAct=false,curM1=0,curM2=0;
var rawIv=null,offOpen=false;
var lastOk=Date.now();
var calEnProceso=false;

function showToast(msg,type){
  var box=document.getElementById('toast-box');
  var t=document.createElement('div');
  t.className='toast toast-'+(type||'info');
  t.innerHTML=msg;
  box.appendChild(t);
  setTimeout(function(){
    t.classList.add('out');
    setTimeout(function(){t.remove();},300);
  },4000);
}

function updHb(){
  var d=Date.now()-lastOk;
  var dot=document.getElementById('hb-dot');
  var txt=document.getElementById('hb-txt');
  if(d>6000){dot.className='hb-dot off';txt.innerText='Sin conexi\u00f3n';}
  else{dot.className='hb-dot';var s=Math.floor(d/1000);txt.innerText=s<2?'OK':'Hace '+s+'s';}
}

function fetchPH(){
  fetch('/get_ph_dual').then(function(r){return r.json();}).then(function(d){
    lastOk=Date.now();
    phOn=(d.on==1);ilAct=(d.il==1);
    curM1=parseInt(d.m1);curM2=parseInt(d.m2);
    
    var tg=document.getElementById('ph-tog');
    tg.className=phOn?'tog on':'tog';
    var tl=document.getElementById('tog-lbl');
    tl.innerText=phOn?'ACTIVO':'STANDBY';
    tl.className=phOn?'tog-lbl act':'tog-lbl';
    
    var ia=document.getElementById('il-alert');
    ia.className=ilAct?'il-alert vis':'il-alert';
    
    updPH(1, d.p1, d.v1, d.vs1, phOn);
    updPH(2, d.p2, d.v2, d.vs2, phOn);
    
    document.getElementById('sl-lbl1').innerText='Nernst: '+d.sl1+'%';
    document.getElementById('sl-lbl2').innerText='Nernst: '+d.sl2+'%';

    updMode(1,curM1);updMode(2,curM2);
    updCal(1,curM1);updCal(2,curM2);
    updCalStatus(1,curM1,d.c1);
    updCalStatus(2,curM2,d.c2);

    document.getElementById('scale1').className=phOn?'ph-scale-bar on':'ph-scale-bar';
    document.getElementById('scale2').className=phOn?'ph-scale-bar on':'ph-scale-bar';
    updHb();
  }).catch(function(){ updHb(); });
}

function updPH(tina, val, vadcRaw, vsondaRaw, on){
  var el=document.getElementById('ph'+tina);
  var ring=document.getElementById('ring'+tina);
  var vs=document.getElementById('vs'+tina);
  var va=document.getElementById('va'+tina);
  
  if(!on){
    el.innerHTML='&mdash;';el.className='ph-val off';ring.className='ph-ring';ring.style.borderColor='#1e293b';ring.style.boxShadow='none';
    if(vs)vs.innerText='--- V';if(va)va.innerText='--- V';
    return;
  }
  
  var v=parseFloat(val);
  if(isNaN(v)||v<0||v>14){el.innerText='ERR';el.className='ph-val';el.style.color='#ef4444';ring.className='ph-ring';return;}
  
  el.innerText=v.toFixed(2);el.className='ph-val';ring.className='ph-ring active';
  
  var h;
  if(v<=3)h=0;
  else if(v<=7)h=(v-3)/4*120;
  else if(v<=11)h=120+(v-7)/4*120;
  else{h=240;if(v>11)h+=Math.min((v-11)/3*40,40);}
  
  el.style.color='hsl('+Math.round(h)+',75%,58%)';
  ring.style.borderColor='hsla('+Math.round(h)+',75%,58%,0.35)';
  ring.style.boxShadow='0 0 28px hsla('+Math.round(h)+',75%,58%,0.12)';

  // Mediciones analógicas reales provenientes del firmware
  if(va && vadcRaw) va.innerText = parseFloat(vadcRaw).toFixed(3) + ' V';
  if(vs && vsondaRaw) vs.innerText = parseFloat(vsondaRaw).toFixed(2) + ' V';
}

function togglePH(){
  if(ilAct&&!phOn){
    showToast('&#9888; Bloqueado por Interlock — Apague t\u00e9rmico y fuente primero','err');
    return;
  }
  fetch('/act_ph?run='+(phOn?0:1)).then(function(r){
    if(r.status===403) showToast('&#9888; Bloqueado por Interlock','err');
    else showToast(phOn?'M\u00f3dulo pH APAGADO':'M\u00f3dulo pH ACTIVADO','ok');
    fetchPH();
  });
}

function setMode(t,m){
  fetch('/set_cal_mode?id='+t+'&m='+m).then(function(){
    showToast('Modo '+(m==0?'Te\u00f3rico':m==1?'2 Puntos':'3 Puntos')+' seleccionado (Tina '+t+')','info');
    fetchPH();
  });
}

function updMode(t,m){
  for(var i=0;i<3;i++){
    var b=document.getElementById('m'+t+'-'+i);
    if(b)b.className=(i===m)?'mode-b act':'mode-b';
  }
}

function updCal(t,m){
  var b4=document.getElementById('cal-'+t+'-4');
  var b10=document.getElementById('cal-'+t+'-10');
  if(b4)b4.style.display=(m>=1)?'flex':'none';
  if(b10)b10.style.display=(m===2)?'flex':'none';
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

/* ==========================================================================
   PROCESO DE CALIBRACIÓN METROLÓGICA CON TEMPORIZADOR Y ESTABILIZACIÓN
   ========================================================================== */
function iniciarCalibracion(t, p){
  if(calEnProceso) return;
  if(ilAct){
    showToast('&#9888; Calibraci\u00f3n bloqueada por Interlock (fuente o calefactores activos)','err');
    return;
  }
  
  var nombreTina = (t===1?'Tina Zincado (Canal A0)':'Tina Niquelado (Canal A1)');
  var nombreBuf = (p===7?'Buffer pH 7.0 (Neutro)':(p===4?'Buffer pH 4.0 (\u00c1cido)':'Buffer pH 10.0 (B\u00e1sico)'));
  
  if(!confirm('¿Iniciar calibración para '+nombreBuf+' en '+nombreTina+'?\n\nAsegúrese de tener el electrodo sumergido en la solución buffer correspondiente.')) return;
  
  calEnProceso = true;
  var modal = document.getElementById('cal-modal');
  document.getElementById('cal-m-title').innerText = 'Calibrando ' + nombreBuf;
  document.getElementById('cal-m-sub').innerText = nombreTina;
  document.getElementById('cal-m-status').innerText = 'Adquiriendo 25 muestras continuas y evaluando estabilidad...';
  
  var timerEl = document.getElementById('cal-timer');
  var progEl = document.getElementById('cal-prog');
  var segundos = 3;
  timerEl.innerText = segundos;
  progEl.style.width = '0%';
  modal.classList.add('open');

  var startTime = Date.now();
  var duration = 2800; // 2.8s de animación coincidente con muestreo del ESP32

  var animIv = setInterval(function(){
    var elapsed = Date.now() - startTime;
    var pct = Math.min(100, (elapsed / duration) * 100);
    progEl.style.width = pct + '%';
    var rem = Math.max(0, Math.ceil((duration - elapsed) / 1000));
    timerEl.innerText = rem;
    if(elapsed >= duration) clearInterval(animIv);
  }, 100);

  // Ejecutar petición HTTP de calibración hacia el ESP32
  fetch('/do_cal_ph?id=' + t + '&p=' + p)
    .then(function(r){ return r.json(); })
    .then(function(d){
      clearInterval(animIv);
      progEl.style.width = '100%';
      timerEl.innerText = '0';
      modal.classList.remove('open');
      calEnProceso = false;

      if(d.ok === 1){
        var info = '&#10003; Calibrado pH ' + p + '.0 con &eacute;xito (' + d.v + ' V | Estabilidad &plusmn;' + d.estab + ' mV)';
        if(parseFloat(d.slope) !== 0) info += '<br>Pendiente: ' + d.slope + ' pH/V';
        showToast(info, 'ok');
      } else {
        showToast('&#10007; ' + (d.err || 'Error de calibraci\u00f3n'), 'err');
      }
      fetchPH();
    })
    .catch(function(){
      clearInterval(animIv);
      modal.classList.remove('open');
      calEnProceso = false;
      showToast('Error de comunicaci\u00f3n durante la calibraci\u00f3n', 'err');
    });
}

function resetCalibracion(t){
  var nombreTina = (t===1?'Tina Zincado (A0)':'Tina Niquelado (A1)');
  if(!confirm('¿Restablecer calibración a VALORES DE FÁBRICA para ' + nombreTina + '?\n\nEsto borrará los puntos de pH 4, 7 y 10 guardados en la Flash NVS y regresará al modelo teórico predeterminado.')) return;

  fetch('/reset_cal_ph?id=' + t)
    .then(function(r){ return r.json(); })
    .then(function(d){
      if(d.ok === 1){
        showToast('&#8634; Calibraci\u00f3n restablecida a valores de f\u00e1brica (' + nombreTina + ')', 'ok');
      } else {
        showToast('&#10007; ' + (d.err || 'Error al restablecer calibraci\u00f3n'), 'err');
      }
      fetchPH();
    })
    .catch(function(){
      showToast('Error de comunicaci\u00f3n al restablecer', 'err');
    });
}

/* ==========================================================================
   PANEL DUAL DE AJUSTE DE OFFSET DE HARDWARE (EN CORTO)
   ========================================================================== */
function toggleOffset(){
  offOpen = !offOpen;
  document.getElementById('off-body').style.display = offOpen ? 'block' : 'none';
  var btn = document.getElementById('off-tog');
  btn.innerText = offOpen ? 'CERRAR' : 'ABRIR';
  btn.className = offOpen ? 'off-tog open' : 'off-tog';
  
  if(offOpen){
    rawIv = setInterval(fetchRaw, 250);
    fetchRaw();
  } else {
    if(rawIv){ clearInterval(rawIv); rawIv = null; }
  }
}

function fetchRaw(){
  fetch('/data_ph_raw').then(function(r){ return r.json(); }).then(function(d){
    actualizarGaugeOffset(1, parseFloat(d.v1), d.mv1);
    actualizarGaugeOffset(2, parseFloat(d.v2), d.mv2);
  }).catch(function(){});
}

function actualizarGaugeOffset(ch, v, mvStr){
  var vmEl = document.getElementById('raw-v' + ch);
  var mvEl = document.getElementById('raw-mv' + ch);
  var ndl = document.getElementById('g-ndl' + ch);
  var diffEl = document.getElementById('off-diff' + ch);
  var badge = document.getElementById('off-badge' + ch);
  
  if(!vmEl) return;
  vmEl.innerText = v.toFixed(3);
  mvEl.innerText = mvStr + ' mV';
  
  var pct = (v / 3.53) * 100;
  if(pct < 0) pct = 0; if(pct > 100) pct = 100;
  ndl.style.left = pct + '%';
  
  var diff = v - 1.765;
  var diffMv = diff * 1000;
  diffEl.innerText = (diff >= 0 ? '+' : '') + diffMv.toFixed(1) + ' mV';
  
  var ad = Math.abs(diff);
  if(ad <= 0.010){
    diffEl.style.color = '#34d399';
    vmEl.style.color = '#34d399';
    badge.innerHTML = '&#10003; Calibrado (&plusmn;10 mV)';
    badge.style.cssText = 'background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);';
  } else if(ad <= 0.050){
    diffEl.style.color = '#fbbf24';
    vmEl.style.color = '#fbbf24';
    badge.innerText = 'Ajustar potenci\u00f3metro Placa ' + ch;
    badge.style.cssText = 'background:rgba(217,119,6,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);';
  } else {
    diffEl.style.color = '#ef4444';
    vmEl.style.color = '#ef4444';
    badge.innerText = 'Fuera de rango en Placa ' + ch;
    badge.style.cssText = 'background:rgba(220,38,38,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);';
  }
}

setInterval(fetchPH, 1500);
fetchPH();
setInterval(updHb, 1000);
</script>
</body></html>
)rawliteral";

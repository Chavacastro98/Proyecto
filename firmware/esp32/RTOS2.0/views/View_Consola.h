#pragma once
#include <Arduino.h>

/**
 * =================================================================================
 * VISTA: TERMINAL Y CONSOLA DE LOGS EN VIVO (View_Consola.h) — FreeRTOS 2.0
 * =================================================================================
 * Diseño de Instrumento de Ingeniería (Engineering Instrument - Anti-AI Slop)
 *   • Tema dual: VS Dark (predeterminado) & COMSOL Light (Día).
 *   • Aspecto de terminal VS Code / depuración industrial en tiempo real.
 *   • Sin difuminados ni sombras excesivas.
 * Almacenado en PROGMEM (Flash).
 * =================================================================================
 */

const char HTML_CONSOLA[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Consola del Sistema &middot; RTOS 2.0</title>
<style>

    /* ==========================================================================
       VARIABLES DE TEMA: VS Dark & COMSOL Light (Instrumentación)
       ========================================================================== */
    :root, [data-theme="dark"] {
      --ui-bg: #1e1e1e;
      --ui-panel: #252526;
      --ui-subpanel: #2d2d2d;
      --ui-border: #3c3c3c;
      --ui-border-subtle: #2f2f2f;
      
      --text-primary: #f1f1f1;
      --text-secondary: #cccccc;
      --text-muted: #858585;
      --text-disabled: #555555;

      --accent-primary: #007acc;
      --accent-hover: #1f8ad2;
      --accent-active: #0e639c;

      --metro-ok: #4ec9b0;
      --metro-ok-bg: rgba(78, 201, 176, 0.12);
      --metro-ok-border: #2e8b75;
      --metro-warn: #d7ba7d;
      --metro-warn-bg: rgba(215, 186, 125, 0.12);
      --metro-warn-border: #a88a4d;
      --metro-err: #f14c4c;
      --metro-err-bg: rgba(241, 76, 76, 0.12);
      --metro-err-border: #aa3333;

      --disp-bg: #141414;
      --disp-border: #333333;
      --disp-panel: #1b1b1c;

      --btn-bg: #2d2d2d;
      --btn-border: #3c3c3c;
      --btn-text: #cccccc;
      --btn-hover-bg: #383838;
      
      --term-bg: #141414;
      --term-border: #333333;
      --term-text: #f1f1f1;
    }

    [data-theme="light"] {
      --ui-bg: #f3f3f3;
      --ui-panel: #ffffff;
      --ui-subpanel: #e8e8e8;
      --ui-border: #d4d4d4;
      --ui-border-subtle: #e5e5e5;

      --text-primary: #1e1e1e;
      --text-secondary: #333333;
      --text-muted: #666666;
      --text-disabled: #a0a0a0;

      --accent-primary: #005fb8;
      --accent-hover: #106ebe;
      --accent-active: #004578;

      --metro-ok: #2e7d32;
      --metro-ok-bg: #e8f5e9;
      --metro-ok-border: #81c784;
      --metro-warn: #b45309;
      --metro-warn-bg: #fffbeb;
      --metro-warn-border: #fcd34d;
      --metro-err: #c62828;
      --metro-err-bg: #ffebee;
      --metro-err-border: #ef9a9a;

      --disp-bg: #f9f9fb;
      --disp-border: #b8b8b8;
      --disp-panel: #f0f0f4;

      --btn-bg: #e8e8e8;
      --btn-border: #cccccc;
      --btn-text: #222222;
      --btn-hover-bg: #dedede;
      
      --term-bg: #ffffff;
      --term-border: #d4d4d4;
      --term-text: #1e1e1e;
    }

    /* ==========================================================================
       RESET & TIPOGRAFÍA DE INGENIERÍA
       ========================================================================== */
    *{margin:0;padding:0;box-sizing:border-box;}
    body{
      font-family:Consolas,"Cascadia Code","SF Mono","Fira Code",monospace;
      background:var(--ui-bg);
      color:var(--text-secondary);
      min-height:100vh;
      display:flex;
      flex-direction:column;
      padding:14px 14px 30px;
      transition:background 0.2s ease, color 0.2s ease;
    }
    .container{
      max-width:960px;
      width:100%;
      margin:0 auto;
      display:flex;
      flex-direction:column;
      flex:1;
    }

    /* Hub Nav */
    .hub-bar{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-bottom:12px;
    }
    .hub-link{
      display:inline-flex;
      align-items:center;
      gap:6px;
      color:var(--accent-primary);
      text-decoration:none;
      font-size:0.75em;
      font-weight:700;
      padding:4px 10px;
      background:var(--ui-panel);
      border-radius:3px;
      border:1px solid var(--ui-border);
      transition:background 0.15s, border-color 0.15s;
    }
    .hub-link:hover{
      background:var(--btn-hover-bg);
      border-color:var(--accent-primary);
    }

    /* Theme Toggle Button */
    .theme-btn{
      display:inline-flex;
      align-items:center;
      gap:6px;
      background:var(--ui-panel);
      color:var(--text-secondary);
      border:1px solid var(--ui-border);
      padding:4px 10px;
      font-size:0.75em;
      font-weight:700;
      border-radius:3px;
      cursor:pointer;
      transition:all 0.15s;
    }
    .theme-btn:hover{
      border-color:var(--accent-primary);
      color:var(--text-primary);
    }

    /* Header Box */
    .header-box{
      background:var(--ui-panel);
      padding:12px 16px;
      border-radius:4px;
      border:1px solid var(--ui-border);
      border-top:2px solid var(--accent-primary);
      display:flex;
      justify-content:space-between;
      align-items:center;
      flex-wrap:wrap;
      gap:10px;
      margin-bottom:12px;
    }
    .title-group{
      display:flex;
      align-items:center;
      gap:12px;
    }
    .nav-back{
      color:var(--accent-primary);
      text-decoration:none;
      font-weight:700;
      font-size:0.8em;
      transition:0.15s;
    }
    .nav-back:hover{text-decoration:underline;}
    .title-group h2{
      font-size:0.98em;
      color:var(--text-primary);
      font-weight:700;
      letter-spacing:0.2px;
      display:flex;
      align-items:center;
      gap:8px;
    }

    /* Actions Toolbar */
    .actions{
      display:flex;
      gap:6px;
      align-items:center;
      flex-wrap:wrap;
    }
    .btn{
      padding:4px 10px;
      border-radius:2px;
      font-size:0.72em;
      font-weight:700;
      border:1px solid var(--ui-border);
      background:var(--btn-bg);
      color:var(--text-secondary);
      cursor:pointer;
      transition:all 0.15s;
      font-family:Consolas,monospace;
    }
    .btn:hover{
      background:var(--btn-hover-bg);
      border-color:var(--accent-primary);
      color:var(--text-primary);
    }
    .btn:active{transform:scale(0.98);}
    .btn.active{
      background:var(--accent-primary);
      color:#ffffff;
      border-color:var(--accent-primary);
    }
    .status-pill{
      display:inline-flex;
      align-items:center;
      gap:5px;
      font-size:0.7em;
      padding:3px 8px;
      border-radius:2px;
      background:var(--metro-ok-bg);
      color:var(--metro-ok);
      border:1px solid var(--metro-ok-border);
      font-weight:700;
      letter-spacing:0.4px;
    }
    .latency{
      font-size:0.7em;
      font-weight:700;
      color:var(--accent-primary);
      padding:3px 8px;
      border-radius:2px;
      background:var(--disp-panel);
      border:1px solid var(--ui-border);
      font-variant-numeric:tabular-nums;
    }

    /* Terminal Chassis */
    .term-container{
      flex:1;
      background:var(--term-bg);
      border-radius:4px;
      border:1px solid var(--term-border);
      padding:14px 16px;
      overflow-y:auto;
      display:flex;
      flex-direction:column;
      gap:4px;
      min-height:480px;
      max-height:calc(100vh - 150px);
      position:relative;
    }

    /* Log Rows */
    .log-row{
      font-size:0.8em;
      line-height:1.5;
      display:flex;
      gap:8px;
      word-break:break-all;
      border-bottom:1px solid var(--ui-border-subtle);
      padding-bottom:3px;
      align-items:baseline;
    }
    .log-row:hover{
      background:var(--btn-hover-bg);
    }
    .log-time{
      color:var(--text-muted);
      min-width:65px;
      font-weight:600;
      font-variant-numeric:tabular-nums;
    }
    .log-tag{
      font-weight:700;
      min-width:75px;
      padding:1px 5px;
      border-radius:2px;
      font-size:0.88em;
      text-align:center;
    }
    .tag-INFO{
      background:rgba(0,122,204,0.12);
      color:var(--accent-primary);
      border:1px solid var(--accent-primary);
    }
    .tag-WARN{
      background:var(--metro-warn-bg);
      color:var(--metro-warn);
      border:1px solid var(--metro-warn-border);
    }
    .tag-ERR{
      background:var(--metro-err-bg);
      color:var(--metro-err);
      border:1px solid var(--metro-err-border);
    }
    .log-msg{
      color:var(--term-text);
      flex:1;
    }
  
</style>
</head>
<body>

  <div class='container'>
    <div class='hub-bar'>
      <a href='../index.html' class='hub-link'>&larr; Hub de Versiones (Tesis)</a>
      <button class='theme-btn' onclick='toggleTheme()' title='Alternar Modo Día / Noche'>
        <span id='theme-btn-lbl'>&#9728; Modo D&iacute;a</span>
      </button>
    </div>

    <div class='header-box'>
      <div class='title-group'>
        <a href='index.html' class='nav-back'>&larr; Men&uacute;</a>
        <h2>Consola de Diagn&oacute;stico &middot; FreeRTOS CLI (Core 1)</h2>
      </div>
      <div class='actions'>
        <span class='status-pill'>&#9679; SMP DUAL-CORE</span>
        <span class='latency' id='latency'>18ms</span>
        <button class='btn active' id='btn-scroll' onclick='toggleScroll()'>Auto-Scroll: ON</button>
        <button class='btn' id='btn-pause' onclick='togglePause()'>Pausar</button>
        <button class='btn' onclick='clearScreen()'>Limpiar</button>
      </div>
    </div>

    <div class='term-container' id='term'></div>
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

    /* ==========================================================================
       GESTIÓN DE TEMA DUAL
       ========================================================================== */
    function initTheme() {
        var saved = localStorage.getItem('electrodo32_theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        updateThemeBtn(saved);
    }

    function toggleTheme() {
        var cur = document.documentElement.getAttribute('data-theme') || 'dark';
        var next = (cur === 'dark') ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('electrodo32_theme', next);
        updateThemeBtn(next);
    }

    function updateThemeBtn(th) {
        var btn = document.getElementById('theme-btn-lbl');
        if (!btn) return;
        btn.innerHTML = (th === 'dark') ? '&#9728; Modo D&iacute;a' : '&#9790; Modo Noche';
    }

    initTheme();

    function toggleScroll(){
      autoScroll = !autoScroll;
      var btn = document.getElementById('btn-scroll');
      if(btn){
        btn.innerText = 'Auto-Scroll: ' + (autoScroll ? 'ON' : 'OFF');
        btn.className = autoScroll ? 'btn active' : 'btn';
      }
    }

    function togglePause(){
      pausado = !pausado;
      var btn = document.getElementById('btn-pause');
      if(btn){
        btn.innerText = pausado ? 'Reanudar' : 'Pausar';
        btn.className = pausado ? 'btn active' : 'btn';
      }
    }

    function clearScreen(){
      term.innerHTML = '';
      lastTimestamp = 0;
    }

    function escapeHtml(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
          var latEl = document.getElementById('latency');
          if(latEl){
            latEl.innerText = lat + 'ms';
            latEl.style.color = lat < 200 ? 'var(--metro-ok)' : (lat < 500 ? 'var(--metro-warn)' : 'var(--metro-err)');
          }
          var hbDot = document.getElementById('hb-dot');
          if(hbDot) hbDot.className = 'hb-dot';
          if(stPill){
            stPill.innerHTML = '&#9679; EN L&Iacute;NEA';
            stPill.style.color = 'var(--metro-ok)';
          }

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
              row.className = 'log-row';
              
              var lvlClass = (l.lvl === 2) ? 'ERR' : ((l.lvl === 1) ? 'WARN' : 'INFO');
              var tSec = (l.t / 1000).toFixed(3);

              row.innerHTML = 
                "<span class='log-time'>[" + tSec + "s]</span>" +
                "<span class='log-tag tag-" + lvlClass + "'>" + l.tag + "</span>" +
                "<span class='log-msg msg-" + lvlClass + "'>" + escapeHtml(l.msg) + "</span>";
              
              term.appendChild(row);
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
            var hbDot = document.getElementById('hb-dot');
            if(hbDot) hbDot.className = 'hb-dot off';
            var latEl = document.getElementById('latency');
            if(latEl){
              latEl.innerText = '--ms';
              latEl.style.color = 'var(--metro-err)';
            }
            if(stPill){
              stPill.innerHTML = '&#9675; SIN CONEXI&Oacute;N';
              stPill.style.color = 'var(--metro-err)';
            }
          }
        });
    }

    setInterval(fetchLogs, 1500);
    fetchLogs();
</script>
</body>
</html>
)rawliteral";

/**
 * =================================================================================
 * MÓDULO DE ACTUALIZACIÓN INALÁMBRICA OTA (Modulo_OTA.cpp) — Versión RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES DE IMPLEMENTACIÓN:
 * Permite cargar archivos binarios compilados (.bin) directamente desde el navegador.
 *
 * CONDICIONES DE ENCLAVAMIENTO (SAFETY INTERLOCK):
 * El proceso electroquímico debe estar completamente en reposo antes de permitir el
 * flasheo. Si algún canal térmico está encendido, la fuente VCSS activa o el pH en
 * medición, el servidor rechaza de inmediato la carga de firmware con código HTTP 403.
 * =================================================================================
 */

#include "Modulo_OTA.h"
#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "RTOS_Core.h"
#include "config.h"
#include <Update.h>

/**
 * @brief Evalúa si alguna carga de potencia está encendida bajo protección de xDataMutex.
 * @return true si el sistema está operando (calentando, entregando corriente o midiendo pH).
 */
bool otaInterlockActivo() {
  bool termicoOn = false;
  bool fOn = false;
  bool phOn = false;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    for (int i = 0; i < 4; i++) {
      if (canales[i].activo) {
        termicoOn = true;
        break;
      }
    }
    fOn = fuenteActiva;
    phOn = phModuloActivo;
    giveDataMutex();
  }

  return (termicoOn || fOn || phOn);
}


const char HTML_OTA[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Actualizar Firmware &middot; FreeRTOS 2.0</title>
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
        }

        /* ==========================================================================
           RESET & TIPOGRAFÍA DE INGENIERÍA
           ========================================================================== */
        *{margin:0;padding:0;box-sizing:border-box;}
        body{
            font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,Helvetica,Arial,sans-serif;
            background:var(--ui-bg);
            color:var(--text-secondary);
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            padding:16px 14px;
            transition:background 0.2s ease, color 0.2s ease;
        }
        .container{
            width:100%;
            max-width:540px;
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

        /* Main Card */
        .ota-card{
            background:var(--ui-panel);
            padding:20px;
            border-radius:4px;
            border:1px solid var(--ui-border);
            border-top:2px solid var(--accent-primary);
            text-align:center;
        }

        /* Header */
        .hdr{
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin-bottom:14px;
            padding-bottom:10px;
            border-bottom:1px solid var(--ui-border-subtle);
        }
        .nav-back{
            color:var(--accent-primary);
            text-decoration:none;
            font-weight:700;
            font-size:0.8em;
            transition:0.15s;
        }
        .nav-back:hover{text-decoration:underline;}
        .hdr-title{
            font-size:1.05em;
            color:var(--text-primary);
            font-weight:700;
            letter-spacing:0.2px;
        }
        .hdr-sub{
            font-size:0.68em;
            color:var(--text-muted);
            font-weight:600;
            display:block;
            margin-top:2px;
            letter-spacing:0.6px;
            font-family:Consolas,monospace;
        }

        /* Version Info Bar */
        .ver-wrap{
            display:flex;
            align-items:center;
            justify-content:space-between;
            background:var(--disp-panel);
            padding:8px 12px;
            border-radius:3px;
            margin-bottom:14px;
            border:1px solid var(--ui-border);
            font-size:0.75em;
            font-family:Consolas,monospace;
            color:var(--text-muted);
        }
        .ver-badge{
            padding:2px 6px;
            background:var(--ui-panel);
            color:var(--text-primary);
            border-radius:2px;
            font-weight:700;
            border:1px solid var(--ui-border);
        }
        .ver-chip{
            color:var(--accent-primary);
            font-weight:700;
        }

        /* Drop Zone */
        .drop-zone{
            border:1px dashed var(--accent-primary);
            border-radius:4px;
            padding:24px 16px;
            background:var(--disp-panel);
            cursor:pointer;
            transition:all 0.15s;
            margin-bottom:14px;
            position:relative;
        }
        .drop-zone:hover{
            background:var(--btn-hover-bg);
            border-color:var(--accent-hover);
        }
        .box-ico-wrap{
            width:42px;
            height:42px;
            border-radius:3px;
            background:var(--ui-panel);
            border:1px solid var(--ui-border);
            display:flex;
            align-items:center;
            justify-content:center;
            margin:0 auto 10px;
            font-size:20px;
        }
        .drop-text{
            color:var(--text-primary);
            font-size:0.85em;
            font-weight:700;
            letter-spacing:0.1px;
        }
        .drop-sub{
            color:var(--text-muted);
            font-size:0.7em;
            margin-top:4px;
            font-family:Consolas,monospace;
        }

        /* File Info Box */
        .file-info{
            display:none;
            background:var(--disp-panel);
            padding:10px 12px;
            border-radius:3px;
            margin-bottom:14px;
            font-size:0.78em;
            color:var(--text-secondary);
            font-weight:700;
            text-align:left;
            border:1px solid var(--ui-border);
            align-items:center;
            gap:10px;
            font-family:Consolas,monospace;
        }

        /* Upload Button */
        .btn-upld{
            width:100%;
            padding:10px;
            background:var(--btn-bg);
            color:var(--text-primary);
            border:1px solid var(--accent-primary);
            border-radius:3px;
            font-weight:700;
            font-size:0.82em;
            cursor:pointer;
            transition:all 0.15s;
            letter-spacing:0.5px;
            font-family:Consolas,monospace;
        }
        .btn-upld:hover:not(:disabled){
            background:var(--btn-hover-bg);
            border-color:var(--accent-hover);
        }
        .btn-upld:active{transform:scale(0.99);}
        .btn-upld:disabled{
            opacity:0.4;
            cursor:not-allowed;
            background:var(--btn-bg);
            border-color:var(--ui-border);
            color:var(--text-disabled);
        }

        /* Progress Bar */
        .prog-wrap{
            display:none;
            margin-top:14px;
            text-align:left;
        }
        .prog-bar-bg{
            background:var(--disp-panel);
            border-radius:2px;
            height:8px;
            overflow:hidden;
            border:1px solid var(--ui-border);
        }
        .prog-bar{
            background:var(--accent-primary);
            height:100%;
            width:0%;
            transition:width 0.15s;
        }
        .prog-txt{
            font-size:0.72em;
            color:var(--text-muted);
            margin-top:6px;
            display:flex;
            justify-content:space-between;
            font-weight:700;
            font-family:Consolas,monospace;
        }

        /* Status Alerts */
        .st-msg{
            margin-top:14px;
            padding:10px 12px;
            border-radius:3px;
            font-size:0.78em;
            font-weight:600;
            display:none;
            text-align:left;
            line-height:1.4;
            font-family:Consolas,monospace;
        }
        .st-ok{
            background:var(--metro-ok-bg);
            color:var(--metro-ok);
            border:1px solid var(--metro-ok-border);
        }

        .hw-note{
            font-size:0.7em;
            color:var(--text-muted);
            margin-top:14px;
            background:var(--disp-panel);
            padding:8px 12px;
            border-radius:3px;
            border:1px solid var(--ui-border);
            text-align:left;
            line-height:1.35;
            font-family:Consolas,monospace;
        }
    
        .il-warn { display: none; background: var(--metro-err-bg); border: 1px solid var(--metro-err-border); color: var(--metro-err); padding: 10px 14px; margin-bottom: 14px; font-size: 0.82em; font-family: Consolas, monospace; }
        .il-warn.vis { display: flex; align-items: center; gap: 8px; }
        .st-msg { padding: 12px; margin-top: 14px; border-radius: 2px; font-size: 0.85em; font-family: Consolas, monospace; }
        .st-ok { background: var(--metro-ok-bg); border: 1px solid var(--metro-ok-border); color: var(--metro-ok); }
        .st-err { background: var(--metro-err-bg); border: 1px solid var(--metro-err-border); color: var(--metro-err); }
        .dragover { border-color: var(--accent-primary) !important; background: var(--ui-subpanel) !important; }

</style>
</head>

<body>
<div class="card">
    <!-- Header de Instrumentación -->
    <div class="hdr">
        <div style="display:flex;align-items:center;gap:12px;">
            <a href="/" class="nav-back">&larr; Men&uacute; RTOS 2.0</a>
            <button class="theme-btn" id="theme-btn" onclick="toggleTheme()" title="Alternar Modo Día / Noche">
                <span id="theme-btn-lbl">&#9728; Modo D&iacute;a</span>
            </button>
        </div>
        <div style="text-align:right;">
            <span class="hdr-title">Actualizaci&oacute;n OTA</span>
            <span class="hdr-sub">ESP32-S3 Flash Flasher &middot; FreeRTOS 2.0</span>
        </div>
    </div>

    <!-- Alerta de Interlock -->
    <div class="il-warn" id="il-box">
        <span>&#9888;</span>
        <span><b>INTERLOCK ACTIVO:</b> No se permite la actualizaci&oacute;n con fuentes o calefactores en operaci&oacute;n. Ap&aacute;guelos primero.</span>
    </div>

    <!-- Zona de Carga / Drop Zone -->
    <div class="drop-zone" id="dz" onclick="document.getElementById('fi').click()">
        <input type="file" id="fi" accept=".bin" style="display:none;" onchange="onFile(this.files)">
        <div class="dz-icon">&#128229;</div>
        <div class="dz-title">SELECCIONAR ARCHIVO BINARIO DE FIRMWARE</div>
        <div class="dz-sub">Arrastre y suelte el archivo <code>.bin</code> o haga clic aqu&iacute; para examinar</div>
        <div class="dz-formats">FORMATOS SOPORTADOS: BINARIO COMPILADO (.bin) &middot; VERSIÓN INSTALADA: <b id="cur-ver">RTOS 2.0</b></div>
    </div>

    <!-- Información del Archivo Seleccionado -->
    <div class="file-info" id="finfo" style="display:none;"></div>

    <!-- Barra de Progreso -->
    <div class="prog-wrap" id="pw" style="display:none;">
        <div class="prog-head">
            <span class="prog-lbl" id="pt-status">ESCRIBIENDO SECTORES EN FLASH NVS...</span>
            <span class="prog-pct" id="pt-pct">0%</span>
        </div>
        <div class="prog-track">
            <div class="prog-fill" id="pb" style="width:0%;"></div>
        </div>
    </div>

    <!-- Mensaje de Estado -->
    <div class="st-msg" id="sm" style="display:none;"></div>

    <!-- Botón de Flasheo -->
    <button class="btn-upld" id="btn-u" onclick="upload()" disabled>
        <span>&#9889;</span> INICIAR TRANSFERENCIA E INSTALACIÓN OTA
    </button>
</div>

<script>
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

    var selFile = null;
    var dz = document.getElementById('dz');
    ['dragenter','dragover'].forEach(function(e){ dz.addEventListener(e,function(ev){ev.preventDefault();dz.classList.add('dragover');}); });
    ['dragleave','drop'].forEach(function(e){ dz.addEventListener(e,function(ev){ev.preventDefault();dz.classList.remove('dragover');}); });
    dz.addEventListener('drop', function(ev){ if(ev.dataTransfer.files.length) onFile(ev.dataTransfer.files); });

    function onFile(files){
        if(!files.length) return;
        selFile = files[0];
        if(!selFile.name.endsWith('.bin')){ alert('Solo se permiten archivos .bin de firmware compilado.'); selFile=null; return; }
        var fname = selFile.name.toLowerCase();
        if(fname.indexOf('partition') !== -1 || fname.indexOf('bootloader') !== -1 || fname.indexOf('merged') !== -1){
            alert('Archivo no compatible detectado:\n\nHa seleccionado un archivo de particionado, bootloader o imagen merged.\n\nPara actualizar el sistema, seleccione únicamente el binario de aplicación compilada (ej. RTOS2.0.ino.bin).');
            selFile = null;
            return;
        }
        var fi = document.getElementById('finfo');
        fi.style.display = 'flex';
        fi.innerHTML = '<span style="font-size:1.4em">&#128230;</span> <div><b>' + selFile.name + '</b><br><span style="font-size:0.85em;color:var(--text-muted);font-family:Consolas,monospace;">' + (selFile.size/1024).toFixed(1) + ' KB &middot; Archivo Binario V&aacute;lido</span></div>';
        checkIL();
    }

    function checkIL(){
        fetch('/ota_check').then(function(r){return r.json();}).then(function(d){
            var cv = document.getElementById('cur-ver');
            if(cv && d.ver) cv.innerText = d.ver;
            var ilBox = document.getElementById('il-box');
            var btn = document.getElementById('btn-u');
            if(d.il == 1){
                ilBox.className = 'il-warn vis';
                btn.disabled = true;
            } else {
                ilBox.className = 'il-warn';
                btn.disabled = (selFile === null);
            }
        }).catch(function(){});
    }

    var ilInterval = setInterval(checkIL, 2500); checkIL();

    function upload(){
        if(!selFile) return;
        if(!confirm('¿Iniciar la actualización de firmware?\n\nEl ESP32 se reiniciará automáticamente al terminar la transferencia.')) return;

        clearInterval(ilInterval);

        document.getElementById('btn-u').disabled = true;
        document.getElementById('pw').style.display = 'block';
        var sm = document.getElementById('sm');
        sm.style.display = 'none';

        var fd = new FormData();
        fd.append('firmware', selFile);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/update', true);

        xhr.upload.onprogress = function(e){
            if(e.lengthComputable){
                var pct = Math.round((e.loaded / e.total) * 100);
                document.getElementById('pb').style.width = pct + '%';
                document.getElementById('pt-pct').innerText = pct + '%';
                var st = document.getElementById('pt-status');
                if(st) st.innerText = 'TRANSFIRIENDO FLASH: ' + (e.loaded/1024).toFixed(0) + ' / ' + (e.total/1024).toFixed(0) + ' KB';
            }
        };

        xhr.onload = function(){
            if(xhr.status === 200){
                sm.className = 'st-msg st-ok';
                sm.style.display = 'block';
                sm.innerHTML = '&#10003; <b>¡Actualizaci&oacute;n Exitosa!</b><br>Firmware instalado correctamente en Flash. Reiniciando el sistema en 5 segundos...';
                setTimeout(function(){ window.location.href = '/'; }, 6000);
            } else {
                sm.className = 'st-msg st-err';
                sm.style.display = 'block';
                sm.innerHTML = '&#10007; <b>Falla en la Actualizaci&oacute;n:</b><br>' + (xhr.responseText || 'Error en el servidor');
                document.getElementById('btn-u').disabled = false;
                ilInterval = setInterval(checkIL, 2500);
            }
        };

        xhr.onerror = function(){
            sm.className = 'st-msg st-err';
            sm.style.display = 'block';
            sm.innerHTML = '&#10007; Error de conexi&oacute;n durante la transferencia inal&aacute;mbrica.';
            document.getElementById('btn-u').disabled = false;
            ilInterval = setInterval(checkIL, 2500);
        };

        xhr.send(fd);
    }
</script>
</body>
</html>

)rawliteral";

/**
 * @brief Entrega la interfaz gráfica HTML de actualización de firmware desde memoria Flash PROGMEM.
 */
static void handleOTA_GET() {
  server.send_P(200, "text/html", HTML_OTA);
}

/**
 * @brief Endpoint JSON que informa la versión de firmware actual y si el interlock está activo.
 */
static void handleOTACheck() {
  bool il = otaInterlockActivo();
  char json[96];
  snprintf(json, sizeof(json), "{\"ver\":\"%s\",\"il\":%d}", FIRMWARE_VERSION, il ? 1 : 0);
  server.send(200, "application/json", json);
}

/**
 * @brief Respuesta final al concluir la transferencia binaria POST.
 * Si no hubo errores, realiza la parada física de seguridad y reinicia el SoC ESP32-S3.
 */
static void handleOTA_POST() {
  if (Update.hasError()) {
    server.send(500, "text/plain", "Falla de verificacion o escritura en Flash");
  } else {
    server.send(200, "text/plain", "OK");
    // Parada física preventiva de actuadores antes de ceder el control al Bootloader
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    enviarApagadoEmergenciaNano();
    vTaskDelay(pdMS_TO_TICKS(1000));
    ESP.restart();
  }
}

/** @brief Bandera volátil que notifica a las tareas supervisoras que el bus Flash está ocupado */
static volatile bool otaEnProgreso = false;

/**
 * @brief Informa a Task_Supervisor si la memoria Flash está siendo reescrita.
 */
bool isOTAEnProgreso() {
  return otaEnProgreso;
}

/**
 * @brief Manejador de flujo de datos binarios por bloques (Multipart Chunk Stream).
 * Alimenta el Watchdog periódicamente y cede ciclos de CPU a la pila lwIP.
 */
static void handleOTA_Upload() {
  HTTPUpload &upload = server.upload();

  if (upload.status == UPLOAD_FILE_START) {
    Serial.printf("[OTA] Inicio de recepcion: %s\n", upload.filename.c_str());

    if (otaInterlockActivo()) {
      Serial.println("[OTA] [CANCELADO]: Interlock activo.");
      otaEnProgreso = false;
      return;
    }

    otaEnProgreso = true; // Activa inmediatamente la bandera para proteger las tareas supervisoras
    feedHeartbeat(HB_ID_WEB);

    if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
      Update.printError(Serial);
      otaEnProgreso = false;
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    feedHeartbeat(HB_ID_WEB);
    vTaskDelay(pdMS_TO_TICKS(1)); // Cede tiempo a IDLE0 para reiniciar el Watchdog del ESP-IDF y dar respiro a WiFi

    if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
      Update.printError(Serial);
      otaEnProgreso = false;
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    otaEnProgreso = false;
    feedHeartbeat(HB_ID_WEB);
    if (Update.end(true)) {
      Serial.printf("[OTA] Flasheo completado con exito: %u bytes.\n", upload.totalSize);
    } else {
      Update.printError(Serial);
    }
  }
}

/**
 * @brief Registra los endpoints de actualización OTA en el servidor web.
 */
void inicializarOTA() {
  server.on("/update", HTTP_GET, handleOTA_GET);
  server.on("/update", HTTP_POST, handleOTA_POST, handleOTA_Upload);
  server.on("/ota_check", HTTP_GET, handleOTACheck);
  Serial.println("[OTA] Módulo OTA v1.0 registrado en ruta /update.");
}


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
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Actualizar Firmware &middot; FreeRTOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#070b14;background-image:radial-gradient(circle at 50% 0%,rgba(56,189,248,0.08) 0,transparent 50%),radial-gradient(circle at 90% 90%,rgba(52,211,153,0.05) 0,transparent 50%);color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px 14px;}
.ota-card{background:rgba(15,23,42,0.7);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);padding:28px 24px;border-radius:24px;box-shadow:0 16px 45px rgba(0,0,0,0.55),inset 0 1px 0 rgba(255,255,255,0.08);width:100%;max-width:520px;border:1px solid rgba(255,255,255,0.08);text-align:center;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid rgba(51,65,85,0.35);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.15em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.68em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.3px;}

/* Version Info Bar */
.ver-wrap{display:flex;align-items:center;justify-content:space-between;background:rgba(15,23,42,0.6);padding:10px 14px;border-radius:12px;margin-bottom:20px;border:1px solid rgba(51,65,85,0.4);font-size:0.75em;}
.ver-badge{padding:3px 10px;background:rgba(56,189,248,0.12);color:#38bdf8;border-radius:20px;font-weight:800;letter-spacing:0.3px;border:1px solid rgba(56,189,248,0.25);}
.ver-chip{color:#94a3b8;font-weight:700;}

/* Interlock Warning */
.il-warn{background:linear-gradient(135deg,rgba(185,28,28,0.3),rgba(153,27,27,0.2));border:1px solid rgba(239,68,68,0.4);color:#fca5a5;padding:14px 16px;border-radius:14px;margin-bottom:20px;font-size:0.78em;font-weight:700;line-height:1.45;text-align:left;display:none;}
.il-warn.vis{display:flex;align-items:flex-start;gap:10px;animation:pulse 2s infinite;}
.il-icon{font-size:1.4em;flex-shrink:0;}

/* Drop Zone */
.drop-zone{border:2px dashed rgba(56,189,248,0.3);border-radius:18px;padding:32px 18px;background:rgba(15,23,42,0.55);cursor:pointer;transition:all 0.3s;margin-bottom:18px;position:relative;}
.drop-zone:hover,.drop-zone.dragover{border-color:#38bdf8;background:rgba(30,58,138,0.2);transform:scale(1.01);}
.box-ico-wrap{width:64px;height:64px;border-radius:50%;background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.2);display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:32px;box-shadow:0 0 20px rgba(56,189,248,0.15);}
.drop-text{color:#f1f5f9;font-size:0.9em;font-weight:800;letter-spacing:-0.2px;}
.drop-sub{color:#64748b;font-size:0.75em;margin-top:6px;font-weight:600;}

/* File Info Box */
.file-info{display:none;background:rgba(15,23,42,0.85);padding:12px 16px;border-radius:12px;margin-bottom:18px;font-size:0.8em;color:#e2e8f0;font-weight:700;text-align:left;border:1px solid rgba(56,189,248,0.2);align-items:center;gap:10px;}

/* Upload Button */
.btn-upld{width:100%;padding:15px;background:linear-gradient(135deg,#0284c7,#2563eb);color:#fff;border:none;border-radius:14px;font-weight:800;font-size:0.9em;cursor:pointer;transition:all 0.25s;letter-spacing:0.5px;box-shadow:0 4px 18px rgba(37,99,235,0.35);}
.btn-upld:hover:not(:disabled){background:linear-gradient(135deg,#0369a1,#1d4ed8);transform:translateY(-1px);box-shadow:0 6px 24px rgba(37,99,235,0.5);}
.btn-upld:active{transform:scale(0.97);}
.btn-upld:disabled{opacity:0.35;cursor:not-allowed;box-shadow:none;}

/* Progress Bar */
.prog-wrap{display:none;margin-top:20px;text-align:left;}
.prog-bar-bg{background:#1e293b;border-radius:10px;height:12px;overflow:hidden;border:1px solid #334155;}
.prog-bar{background:linear-gradient(90deg,#38bdf8,#34d399);height:100%;width:0%;transition:width 0.2s;}
.prog-txt{font-size:0.75em;color:#94a3b8;margin-top:8px;display:flex;justify-content:space-between;font-weight:700;}

/* Status Alerts */
.st-msg{margin-top:18px;padding:14px;border-radius:12px;font-size:0.82em;font-weight:700;display:none;text-align:left;line-height:1.45;}
.st-ok{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.35);}
.st-err{background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.35);}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.65;}}
</style></head>
<body>
    <div class='ota-card'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <div style='text-align:center'>
                <span class='hdr-title'>Actualizaci&oacute;n de Firmware</span>
                <span class='hdr-sub'>CARGA INAL&Aacute;MBRICA OTA &middot; ESP32-S3 &middot; RTOS 2.0</span>
            </div>
            <div></div>
        </div>

        <div class='ver-wrap'>
            <span class='ver-chip'>ESP32-S3 N16R8 (16MB)</span>
            <span class='ver-badge'>Versi&oacute;n: v<span id='cur-ver'>2.0.0</span></span>
        </div>

        <div class='il-warn' id='il-box'>
            <div class='il-icon'>&#128737;&#65039;</div>
            <div>
                <b>BLOQUEADO POR SEGURIDAD:</b><br>
                Hay actuadores encendidos (control t&eacute;rmico, fuente o pH). Apague todos los m&oacute;dulos antes de actualizar el firmware.
            </div>
        </div>

        <div class='drop-zone' id='dz' onclick='document.getElementById("fi").click()'>
            <div class='box-ico-wrap'>&#128230;</div>
            <div class='drop-text'>Arrastre el archivo de firmware (.bin) aqu&iacute;</div>
            <div class='drop-sub'>Seleccione el binario de aplicaci&oacute;n (ej. RTOS2.0.ino.bin). No cargue partitions.bin ni bootloader.bin.</div>
        </div>
        <input type='file' id='fi' accept='.bin' style='display:none;' onchange='onFile(this.files)'>
        <div class='file-info' id='finfo'></div>

        <button class='btn-upld' id='btn-u' disabled onclick='upload()'>INICIAR ACTUALIZACI&Oacute;N</button>

        <div class='prog-wrap' id='pw'>
            <div class='prog-bar-bg'><div class='prog-bar' id='pb'></div></div>
            <div class='prog-txt'><span id='pt-status'>Subiendo archivo de firmware...</span><span id='pt-pct'>0%</span></div>
        </div>

        <div class='st-msg' id='sm'></div>
    </div>
    <script>
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
            fi.innerHTML = '<span style="font-size:1.4em">&#128230;</span> <div><b>' + selFile.name + '</b><br><span style="font-size:0.85em;color:#94a3b8;">' + (selFile.size/1024).toFixed(1) + ' KB &middot; Archivo Binario Válido</span></div>';
            checkIL();
        }

        function checkIL(){
            fetch('/ota_check').then(function(r){return r.json();}).then(function(d){
                document.getElementById('cur-ver').innerText = d.ver;
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
            if(!confirm('¿Iniciar la actualización de firmware?\nEl ESP32 se reiniciará automáticamente al terminar.')) return;

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
                }
            };

            xhr.onload = function(){
                if(xhr.status === 200){
                    sm.className = 'st-msg st-ok';
                    sm.style.display = 'block';
                    sm.innerHTML = '&#9989; <b>¡Actualización Exitosa!</b><br>Firmware instalado correctamente. Reiniciando el sistema en 5 segundos...';
                    setTimeout(function(){ window.location.href = '/'; }, 6000);
                } else {
                    sm.className = 'st-msg st-err';
                    sm.style.display = 'block';
                    sm.innerHTML = '&#10060; <b>Falla en la Actualización:</b><br>' + (xhr.responseText || 'Error en el servidor');
                    document.getElementById('btn-u').disabled = false;
                    ilInterval = setInterval(checkIL, 2500);
                }
            };

            xhr.onerror = function(){
                sm.className = 'st-msg st-err';
                sm.style.display = 'block';
                sm.innerHTML = '&#10060; Error de conexión durante la transferencia inalámbrica.';
                document.getElementById('btn-u').disabled = false;
                ilInterval = setInterval(checkIL, 2500);
            };

            xhr.send(fd);
        }
    </script>
</body></html>
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
    Serial2.println("0,0,0,0");
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
      Serial.println("[OTA] ❌ Cancelado: Interlock activo.");
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


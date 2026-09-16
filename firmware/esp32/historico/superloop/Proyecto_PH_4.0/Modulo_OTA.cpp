#include "Modulo_OTA.h"
#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "config.h"
#include <Update.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO OTA — Versión 4.0 (Modulo_OTA.cpp)
 * =================================================================================
 */

bool otaInterlockActivo() {
  portENTER_CRITICAL(&muxTermico);
  bool termicoOn = false;
  for (int i = 0; i < 4; i++) {
    if (canales[i].activo) {
      termicoOn = true;
      break;
    }
  }
  portEXIT_CRITICAL(&muxTermico);

  portENTER_CRITICAL(&muxFuente);
  bool fOn = fuenteActiva;
  portEXIT_CRITICAL(&muxFuente);

  portENTER_CRITICAL(&muxPH);
  bool phOn = phModuloActivo;
  portEXIT_CRITICAL(&muxPH);

  return termicoOn || fOn || phOn;
}

const char HTML_OTA[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Actualizar Firmware</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}
.ota-card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));padding:32px 28px;border-radius:20px;box-shadow:0 12px 40px rgba(0,0,0,0.5);width:100%;max-width:500px;border:1px solid rgba(56,189,248,0.1);text-align:center;}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;display:inline-block;margin-bottom:16px;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
h2{font-size:1.3em;color:#fff;font-weight:800;letter-spacing:-0.5px;}
.sub{color:#64748b;font-size:0.78em;font-weight:600;margin-top:4px;margin-bottom:20px;}
.ver-box{background:rgba(15,23,42,0.6);padding:12px 16px;border-radius:12px;margin-bottom:20px;border:1px solid rgba(51,65,85,0.4);display:flex;align-items:center;justify-content:space-between;}
.ver-lbl{font-size:0.72em;color:#64748b;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;}
.ver-val{font-size:1em;color:#38bdf8;font-weight:900;letter-spacing:-0.3px;}

/* Interlock Alert */
.il-box{background:linear-gradient(135deg,rgba(127,29,29,0.25),rgba(153,27,27,0.15));border:1px solid rgba(239,68,68,0.4);color:#fca5a5;padding:14px 18px;border-radius:12px;margin-bottom:18px;font-weight:700;font-size:0.8em;display:none;animation:pulse 2.5s ease-in-out infinite;line-height:1.5;}
.il-box.vis{display:block;}

/* File Input */
.file-wrap{background:rgba(15,23,42,0.5);border:2px dashed rgba(56,189,248,0.2);border-radius:14px;padding:28px 20px;margin-bottom:18px;cursor:pointer;transition:all 0.3s;}
.file-wrap:hover{border-color:rgba(56,189,248,0.5);background:rgba(15,23,42,0.7);}
.file-wrap.drag{border-color:#38bdf8;background:rgba(30,64,175,0.15);}
.file-icon{font-size:2.2em;margin-bottom:8px;}
.file-text{color:#64748b;font-size:0.82em;font-weight:600;}
.file-text b{color:#38bdf8;}
.file-name{color:#34d399;font-weight:800;font-size:0.85em;margin-top:8px;display:none;word-break:break-all;}
input[type=file]{display:none;}

/* Upload Button */
.btn-upload{width:100%;padding:16px;border-radius:12px;border:none;font-weight:800;font-size:0.95em;cursor:pointer;transition:all 0.25s;letter-spacing:0.3px;background:#059669;color:#fff;box-shadow:0 4px 20px rgba(5,150,105,0.35);}
.btn-upload:hover:not(:disabled){background:#10b981;transform:translateY(-1px);}
.btn-upload:disabled{opacity:0.35;cursor:not-allowed;transform:none;}

/* Progress Bar */
.prog-wrap{display:none;margin-top:18px;}
.prog-bar{height:10px;background:#1e293b;border-radius:5px;overflow:hidden;}
.prog-fill{height:100%;background:linear-gradient(90deg,#059669,#34d399);border-radius:5px;transition:width 0.2s ease-out;width:0%;}
.prog-text{font-size:0.78em;color:#94a3b8;font-weight:700;margin-top:8px;}

/* Status Messages */
.status{margin-top:16px;padding:14px;border-radius:10px;font-weight:700;font-size:0.85em;display:none;line-height:1.5;}
.status.ok{display:block;background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.status.err{display:block;background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);}

/* Info */
.info-list{text-align:left;margin-top:20px;padding:14px 16px;background:rgba(15,23,42,0.5);border-radius:10px;border:1px solid rgba(51,65,85,0.3);}
.info-list div{font-size:0.72em;color:#64748b;font-weight:600;padding:4px 0;display:flex;align-items:center;gap:6px;}
.info-list div span{color:#94a3b8;}
.chk{color:#34d399;font-weight:900;}

/* Animations */
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}
@keyframes spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.6s linear infinite;vertical-align:middle;margin-right:6px;}

@media(max-width:440px){
  .ota-card{padding:24px 18px;}
  h2{font-size:1.15em;}
}
</style></head>
<body>
<div class='ota-card'>
  <a href='/' class='nav-back'>&larr; Men&uacute; Principal</a>
  <h2>Actualizar Firmware</h2>
  <div class='sub'>Actualizaci&oacute;n Over-The-Air (OTA)</div>

  <div class='ver-box'>
    <span class='ver-lbl'>Versi&oacute;n Actual</span>
    <span class='ver-val' id='fw-ver'>...</span>
  </div>

  <div class='il-box' id='il-box'>
    INTERLOCK ACTIVO &mdash; Apague el sistema t&eacute;rmico, la fuente de corriente y el m&oacute;dulo pH antes de actualizar. El ESP32 se reiniciar&aacute; al finalizar.
  </div>

  <div class='file-wrap' id='drop-zone' onclick='document.getElementById("fw-file").click()'>
    <div class='file-text'>Arrastre el archivo <b>.bin</b> aqu&iacute; o haga clic para seleccionar</div>
    <div class='file-name' id='file-name'></div>
    <input type='file' id='fw-file' accept='.bin' onchange='onFileSelected(this)'>
  </div>

  <button class='btn-upload' id='btn-upload' disabled onclick='startUpload()'>SUBIR FIRMWARE</button>

  <div class='prog-wrap' id='prog-wrap'>
    <div class='prog-bar'><div class='prog-fill' id='prog-fill'></div></div>
    <div class='prog-text' id='prog-text'>Preparando...</div>
  </div>

  <div class='status' id='status-msg'></div>

  <div class='info-list'>
    <div><span class='chk'>&bull;</span> <span>La calibraci&oacute;n de pH y setpoints se conservan</span></div>
    <div><span class='chk'>&bull;</span> <span>Si falla el upload, el firmware anterior permanece intacto</span></div>
    <div><span class='chk'>&bull;</span> <span>El sistema se reiniciar&aacute; autom&aacute;ticamente al completar</span></div>
    <div><span class='chk'>&bull;</span> <span>Esquema de particiones: Minimal SPIFFS (1.9 MB por app)</span></div>
  </div>
</div>

<script>
var selectedFile = null;
var isLocked = true;

function checkOTA() {
  fetch('/ota_check').then(function(r){return r.json();}).then(function(d){
    document.getElementById('fw-ver').innerText = 'v' + d.ver;
    isLocked = (d.il == 1);
    var ilBox = document.getElementById('il-box');
    ilBox.className = isLocked ? 'il-box vis' : 'il-box';
    updateBtn();
  }).catch(function(){});
}

function onFileSelected(input) {
  if (input.files.length > 0) {
    selectedFile = input.files[0];
    var fn = document.getElementById('file-name');
    fn.innerText = selectedFile.name + ' (' + (selectedFile.size / 1024).toFixed(1) + ' KB)';
    fn.style.display = 'block';
    updateBtn();
  }
}

function updateBtn() {
  var btn = document.getElementById('btn-upload');
  btn.disabled = (!selectedFile || isLocked);
}

function startUpload() {
  if (!selectedFile || isLocked) return;
  if (!confirm('¿Confirmar actualizacion del firmware?\n\nEl sistema se reiniciara automaticamente al finalizar.\nLa calibracion y configuracion se conservaran.')) return;

  var btn = document.getElementById('btn-upload');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Subiendo...';

  var prog = document.getElementById('prog-wrap');
  prog.style.display = 'block';
  var fill = document.getElementById('prog-fill');
  var ptxt = document.getElementById('prog-text');
  var smsg = document.getElementById('status-msg');
  smsg.className = 'status';
  smsg.style.display = 'none';

  var xhr = new XMLHttpRequest();
  var formData = new FormData();
  formData.append('firmware', selectedFile);

  xhr.upload.addEventListener('progress', function(e) {
    if (e.lengthComputable) {
      var pct = Math.round((e.loaded / e.total) * 100);
      fill.style.width = pct + '%';
      ptxt.innerText = 'Subiendo: ' + pct + '% (' + (e.loaded / 1024).toFixed(0) + ' / ' + (e.total / 1024).toFixed(0) + ' KB)';
    }
  });

  xhr.addEventListener('load', function() {
    if (xhr.status === 200) {
      fill.style.width = '100%';
      fill.style.background = 'linear-gradient(90deg,#059669,#34d399)';
      ptxt.innerText = 'Escritura completa. Reiniciando ESP32...';
      smsg.className = 'status ok';
      smsg.innerHTML = '&#10003; Firmware actualizado correctamente.<br>El sistema se reiniciar&aacute; en 3 segundos...';
      smsg.style.display = 'block';
      btn.innerHTML = 'COMPLETADO &#10003;';
      setTimeout(function(){ location.href = '/'; }, 8000);
    } else {
      fill.style.background = 'linear-gradient(90deg,#dc2626,#ef4444)';
      smsg.className = 'status err';
      smsg.innerHTML = '&#10007; Error al actualizar: ' + xhr.responseText;
      smsg.style.display = 'block';
      btn.innerHTML = 'SUBIR FIRMWARE';
      btn.disabled = false;
    }
  });

  xhr.addEventListener('error', function() {
    fill.style.background = 'linear-gradient(90deg,#dc2626,#ef4444)';
    smsg.className = 'status err';
    smsg.innerHTML = '&#10007; Error de conexi&oacute;n. Verifique la red Wi-Fi.';
    smsg.style.display = 'block';
    btn.innerHTML = 'SUBIR FIRMWARE';
    btn.disabled = false;
  });

  xhr.open('POST', '/update', true);
  xhr.send(formData);
}

var dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', function(e){ e.preventDefault(); dz.classList.add('drag'); });
dz.addEventListener('dragleave', function(){ dz.classList.remove('drag'); });
dz.addEventListener('drop', function(e){
  e.preventDefault(); dz.classList.remove('drag');
  if(e.dataTransfer.files.length > 0){
    document.getElementById('fw-file').files = e.dataTransfer.files;
    onFileSelected(document.getElementById('fw-file'));
  }
});

setInterval(checkOTA, 5000);
checkOTA();
</script>
</body></html>
)rawliteral";

void inicializarOTA() {
  server.on("/update", HTTP_GET, []() {
    server.send_P(200, "text/html", HTML_OTA);
  });

  server.on("/ota_check", HTTP_GET, []() {
    char json[80];
    bool il = otaInterlockActivo();
    snprintf(json, sizeof(json),
             "{\"ver\":\"%s\",\"il\":%d}",
             FIRMWARE_VERSION, il ? 1 : 0);
    server.send(200, "application/json", json);
  });

  server.on("/update", HTTP_POST,
    []() {
      if (!Update.hasError()) {
        server.send(200, "text/plain", "OK");
        Serial.println("[OTA] Actualización completada. Reiniciando...");
        delay(1000);

        dac.setVoltage(0, false);   // DAC a 0A
        Serial2.println("0,0,0,0"); // TRIACs a 0%

        esp_restart();
      } else {
        char errBuf[128];
        snprintf(errBuf, sizeof(errBuf),
                 "Error de escritura en flash: %s",
                 Update.errorString());
        server.send(500, "text/plain", errBuf);
        Serial.print("[OTA] Error: ");
        Serial.println(Update.errorString());
      }
    },
    []() {
      HTTPUpload& upload = server.upload();

      if (upload.status == UPLOAD_FILE_START) {
        if (otaInterlockActivo()) {
          Serial.println("[OTA] BLOQUEADO: Interlock activo. Rechazando upload.");
          Update.abort();
          return;
        }

        Serial.printf("[OTA] Recibiendo firmware: %s\n", upload.filename.c_str());

        if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
          Serial.print("[OTA] Error al iniciar Update: ");
          Serial.println(Update.errorString());
        }

      } else if (upload.status == UPLOAD_FILE_WRITE) {
        if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
          Serial.print("[OTA] Error de escritura: ");
          Serial.println(Update.errorString());
        }

      } else if (upload.status == UPLOAD_FILE_END) {
        if (Update.end(true)) {
          Serial.printf("[OTA] Firmware recibido: %u bytes. Verificación OK.\n",
                        upload.totalSize);
        } else {
          Serial.print("[OTA] Error de verificación: ");
          Serial.println(Update.errorString());
        }

      } else if (upload.status == UPLOAD_FILE_ABORTED) {
        Update.abort();
        Serial.println("[OTA] Upload cancelado por el usuario o error de red.");
      }
    }
  );

  Serial.println("[OTA] Módulo OTA inicializado. Acceso: http://192.168.4.1/update");
}

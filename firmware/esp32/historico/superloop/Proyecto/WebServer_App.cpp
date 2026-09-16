#include "WebServer_App.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "config.h"
#include <math.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL SERVIDOR WEB (WebServer_App.cpp)
 * =================================================================================
 * Este archivo contiene toda la lógica del servidor web: las rutas de datos
 * (JSON), las rutas de acción (comandos), y las páginas HTML de la interfaz
 * gráfica.
 *
 * NOTAS TÉCNICAS IMPORTANTES:
 * - Se usan buffers de texto fijos (char buffer[N]) en lugar de la clase String
 *   de Arduino para evitar problemas de memoria después de muchos días
 * encendido.
 * - Se usa fabsf() en vez de abs() para calcular valores absolutos de números
 *   decimales, porque abs() solo funciona correctamente con números enteros.
 * - Se usan secciones críticas (portENTER_CRITICAL) al leer/escribir datos de
 *   los canales térmicos para evitar lecturas corruptas si el servidor web y
 *   el control de temperatura acceden a los mismos datos al mismo tiempo.
 * =================================================================================
 */

void inicializarWebServer() {
  // --- PÁGINA PRINCIPAL ---
  server.on("/", handleMenu);

  // --- PÁGINAS DE CONTROL ---
  server.on("/termico", handleTermico);
  server.on("/fuente", handleFuente);
  server.on("/ph", handlePH);

  // --- RUTAS DE DATOS (responden con JSON para actualización automática) ---

  // Datos ambientales: temperatura, humedad y presión
  server.on("/data_env", []() {
    char json[128];
    snprintf(json, sizeof(json),
             "{\"t\":\"%.1f\",\"h\":\"%.0f\",\"p\":\"%.1f\"}", amb_temp,
             amb_hum, amb_pres);
    server.send(200, "application/json", json);
  });

  // Lecturas de pH de las 2 tinas
  server.on("/get_ph_dual", []() {
    char json[128];
    portENTER_CRITICAL(&muxPH);
    float p1 = phActual1;
    float p2 = phActual2;
    portEXIT_CRITICAL(&muxPH);
    snprintf(json, sizeof(json), "{\"p1\":\"%.2f\",\"p2\":\"%.2f\"}", p1, p2);
    server.send(200, "application/json", json);
  });

  // Datos de los 4 canales térmicos: temperatura actual, setpoint y estado
  server.on("/data_t", []() {
    char json[256];
    int offset = 0;
    offset += snprintf(json + offset, sizeof(json) - offset, "[");

    for (int i = 0; i < 4; i++) {
      // Leer datos del canal dentro de sección crítica para evitar lecturas corruptas
      portENTER_CRITICAL(&muxTermico);
      float temp = canales[i].temperatura;
      float sp = canales[i].setpoint;
      bool act = canales[i].activo;
      portEXIT_CRITICAL(&muxTermico);

      offset += snprintf(json + offset, sizeof(json) - offset,
                         "{\"t\":%.1f,\"sp\":%.1f,\"run\":%d}%s", temp, sp,
                         act ? 1 : 0, (i < 3) ? "," : "");
    }
    snprintf(json + offset, sizeof(json) - offset, "]");
    server.send(200, "application/json", json);
  });

  // Estado actual de la fuente de corriente
  server.on("/data_f", []() {
    char json[160];
    portENTER_CRITICAL(&muxFuente);
    bool act = fuenteActiva;
    bool modo = modoPulsado;
    int amp = amplitudDAC;
    int freq = frecuencia;
    int duty = dutyCycle;
    portEXIT_CRITICAL(&muxFuente);

    float amps = (amp / 4095.0f) * 6.6f;
    snprintf(json, sizeof(json),
             "{\"act\":%d,\"modo\":%d,\"amp\":%d,\"freq\":%d,\"duty\":%d,"
             "\"amps\":%.2f}",
             act ? 1 : 0, modo ? 1 : 0, amp, freq, duty, amps);
    server.send(200, "application/json", json);
  });

  // --- RUTAS DE ACCIÓN (reciben comandos de la interfaz web) ---

  // Cambiar la temperatura objetivo de un canal térmico
  // Parámetros: ?id=0..3 (canal) y ?v=temperatura (en °C)
  server.on("/set_t", []() {
    if (!server.hasArg("id") || !server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetros faltantes");
      return;
    }
    int id = server.arg("id").toInt();
    if (id >= 0 && id < 4) {
      // Solo se permite cambiar el setpoint si el canal está apagado
      portENTER_CRITICAL(&muxTermico);
      bool canalActivo = canales[id].activo;
      portEXIT_CRITICAL(&muxTermico);

      if (!canalActivo) {
        float nuevoSP = server.arg("v").toFloat();

        // Validar que el setpoint esté en el rango operativo válido (0°C a 150°C)
        if (isnan(nuevoSP) || nuevoSP < 0.0f || nuevoSP > 150.0f) {
          server.send(400, "text/plain", "Setpoint fuera de rango (0-150°C)");
          return;
        }

        // Guardar el nuevo setpoint en la estructura del canal
        portENTER_CRITICAL(&muxTermico);
        canales[id].setpoint = nuevoSP;
        portEXIT_CRITICAL(&muxTermico);

        // Guardar en la memoria Flash para que se conserve al reiniciar
        char key[16];
        snprintf(key, sizeof(key), "sp%d", id);
        memoria.putFloat(key, nuevoSP);
        server.send(200, "text/plain", "OK");
      } else {
        server.send(403, "text/plain", "Bloqueado - Canal Activo");
      }
    } else {
      server.send(400, "text/plain", "Error de ID");
    }
  });

  // Encender o apagar el control térmico de todos los canales
  // Parámetro: ?run=1 (encender) o ?run=0 (apagar)
  server.on("/act_t", []() {
    if (!server.hasArg("run")) {
      server.send(400, "text/plain", "Parámetro run faltante");
      return;
    }
    bool estado = (server.arg("run") == "1");

    portENTER_CRITICAL(&muxTermico);
    for (int i = 0; i < 4; i++) {
      canales[i].activo = estado;
      if (!estado) {
        canales[i].limitePotencia =
            0.0;                   // Reiniciar rampa de arranque al apagar
        canales[i].integral = 0.0; // Limpiar acumulador integral
      }
    }
    portEXIT_CRITICAL(&muxTermico);

    server.send(200, "text/plain", "OK");
  });

  // Modificar un parámetro de la fuente de corriente
  // Parámetros: ?p=a (amplitud), ?p=f (frecuencia), ?p=d (duty cycle) y ?v=valor
  server.on("/set_f", []() {
    if (!server.hasArg("p") || server.arg("p").length() == 0 ||
        !server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetros insuficientes");
      return;
    }

    char parametro = server.arg("p")[0];
    int valor = server.arg("v").toInt();

    portENTER_CRITICAL(&muxFuente);
    if (parametro == 'a') {
      amplitudDAC = constrain(valor, 0, 4095); // 0-4095 (12 bits)
      memoria.putInt("dac_amp", amplitudDAC);
    } else if (parametro == 'f') {
      frecuencia = constrain(valor, 1, 100); // 1-100 Hz
      memoria.putInt("dac_freq", frecuencia);
    } else if (parametro == 'd') {
      dutyCycle = constrain(valor, 0, 100); // 0-100 %
      memoria.putInt("dac_duty", dutyCycle);
    }
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // Cambiar entre modo corriente continua (DC) y corriente pulsada
  // Parámetro: ?v=1 (pulsado) o ?v=0 (continua)
  server.on("/modo_f", []() {
    if (!server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetro v faltante");
      return;
    }
    bool usarPulsado = (server.arg("v") == "1");

    portENTER_CRITICAL(&muxFuente);
    modoPulsado = usarPulsado;
    memoria.putBool("dac_modo", usarPulsado);
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // Encender o apagar la salida de corriente
  // Parámetro: ?run=1 (encender) o ?run=0 (apagar)
  server.on("/act_f", []() {
    if (!server.hasArg("run")) {
      server.send(400, "text/plain", "Parámetro run faltante");
      return;
    }
    bool activar = (server.arg("run") == "1");

    portENTER_CRITICAL(&muxFuente);
    fuenteActiva = activar;
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // Ejecutar un punto de calibración de pH (calibración de 2 puntos)
  // Parámetros: ?id=1 o 2 (tina) y ?p=7 o 4 (solución buffer de referencia)
  server.on("/do_cal_ph", []() {
    if (!server.hasArg("id") || !server.hasArg("p")) {
      server.send(400, "text/plain", "Parámetros insuficientes");
      return;
    }

    int id = server.arg("id").toInt();   // 1 = Tina Zincado, 2 = Tina Niquelado
    int punto = server.arg("p").toInt(); // 7 = Buffer pH 7.0, 4 = Buffer pH 4.0

    if (id != 1 && id != 2) {
      server.send(400, "text/plain", "Error de ID de Tina");
      return;
    }

    // Leer el voltaje actual de la sonda de pH (canal 0 para Tina 1, canal 1 para Tina 2)
    float voltajeMedido = leerVoltajePH((uint8_t)(id - 1));

    portENTER_CRITICAL(&muxPH);
    if (id == 1) {
      if (punto == 7) {
        v7_1 = voltajeMedido;
        memoria.putFloat("v7_1", v7_1);
      } else if (punto == 4) {
        v4_1 = voltajeMedido;
        if (fabsf(v4_1 - v7_1) > 0.01f) {
          m_ph1 = (4.0f - 7.0f) / (v4_1 - v7_1); // Pendiente: pH por Voltio
          calibradoPH1 = true;
          memoria.putFloat("v4_1", v4_1);
          memoria.putFloat("mph1", m_ph1);
          memoria.putBool("cal1", true);
        }
      }
    } else if (id == 2) {
      if (punto == 7) {
        v7_2 = voltajeMedido;
        memoria.putFloat("v7_2", v7_2);
      } else if (punto == 4) {
        v4_2 = voltajeMedido;
        if (fabsf(v4_2 - v7_2) > 0.01f) {
          m_ph2 = (4.0f - 7.0f) / (v4_2 - v7_2);
          calibradoPH2 = true;
          memoria.putFloat("v4_2", v4_2);
          memoria.putFloat("mph2", m_ph2);
          memoria.putBool("cal2", true);
        }
      }
    }
    portEXIT_CRITICAL(&muxPH);

    server.send(200, "text/plain", "OK");
  });

  server.begin(); // Poner en marcha el servidor web
}

// =================================================================================
// PÁGINAS WEB DE LA INTERFAZ GRÁFICA (almacenadas en la memoria Flash del
// ESP32)
// =================================================================================
// Las páginas se guardan en la Flash (PROGMEM) en vez de la RAM porque son
// textos grandes y la RAM del ESP32 es limitada. Cada página incluye su HTML,
// CSS y JavaScript.

// --- MENÚ PRINCIPAL ---
const char HTML_MENU[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Control Galvanoplastia</title>
<style>
    body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
    .menu-card{background:#1e293b; padding:30px; border-radius:20px; display:inline-block; box-shadow:0 10px 30px rgba(0,0,0,0.5); width:90%; max-width:500px;}
    .env-box{display:flex; justify-content:space-around; background:#334155; padding:15px; border-radius:15px; margin:20px 0;}
    .env-item{font-size:0.9em; color:#38bdf8;}
    .env-val{font-size:1.4em; display:block; color:white; font-weight:bold;}
    .btn-menu{display:block; padding:18px; margin:15px auto; background:#3b82f6; color:white; text-decoration:none; font-weight:bold; border-radius:10px; transition:0.3s;}
    .btn-menu:hover{background:#2563eb; transform:scale(1.02);}
</style></head>
<body>
    <div class='menu-card'>
        <h2>Panel de Control</h2>
        <p style='color:#94a3b8;'>Tesis de Electrodeposición / Zincado</p>
        <div class='env-box'>
            <div class='env-item'>TEMP. AMB<span class='env-val' id='amb_t'>0.0°C</span></div>
            <div class='env-item'>HUMEDAD<span class='env-val' id='amb_h'>0%</span></div>
            <div class='env-item'>PRESIÓN<span class='env-val' id='amb_p'>0 hPa</span></div>
        </div>
        <a href='/termico' class='btn-menu'>🔥 CONTROL TÉRMICO</a>
        <a href='/fuente' class='btn-menu'>⚡ FUENTE DE CORRIENTE</a>
        <a href='/ph' class='btn-menu'>🧪 MONITOREO DE PH DUAL</a>
    </div>
    <script>
        function updEnv(){
            fetch('/data_env').then(r=>r.json()).then(d=>{
                document.getElementById('amb_t').innerText=d.t+'°C';
                document.getElementById('amb_h').innerText=d.h+'%';
                document.getElementById('amb_p').innerText=d.p+' hPa';
            });
        }
        setInterval(updEnv, 3000); updEnv();
    </script>
</body></html>)rawliteral";

// --- CONTROL TÉRMICO (4 canales) ---
const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Control Térmico</title>
<style>
    body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
    .grid{display:flex; flex-wrap:wrap; justify-content:center; gap:15px; margin-top:20px;}
    .card{background:#1e293b; border-radius:12px; padding:15px; width:220px; border-left:5px solid #38bdf8;}
    .btn{padding:12px 24px; cursor:pointer; border-radius:8px; border:none; margin:10px; font-weight:bold; font-size:1em;}
    .btn-act{background:#22c55e; color:white;} .btn-stop{background:#ef4444; color:white;}
    .nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none; font-weight:bold;}
    .sp-box{margin-top:10px; background:#0f172a; padding:8px; border-radius:8px;}
    .btn-step{background:#3b82f6; color:white; border:none; width:35px; height:35px; border-radius:5px; font-weight:bold; cursor:pointer;}
    .btn-step:disabled{background:#475569; cursor:not-allowed;}
    .badge-error{background:#ef4444; color:white; padding:4px 8px; border-radius:4px; font-size:0.8em; font-weight:bold; display:inline-block; margin-top:5px;}
</style></head>
<body>
    <a href='/' class='nav-back'>⬅ Volver al Menú</a>
    <h2>Lazos de Control Térmico</h2>
    <button class='btn btn-act' onclick='toggleT(1)'>ENCENDER SISTEMA</button>
    <button class='btn btn-stop' onclick='toggleT(0)'>APAGAR SISTEMA</button>
    
    <div class='grid' id='t-cards'></div>

    <script>
        const nombres = ["Limpieza", "Decapado", "Zincado (Celda Hull)", "Niquelado"];
        function loadThermal(){
            fetch('/data_t').then(r=>r.json()).then(data=>{
                let h = '';
                data.forEach((c, i)=>{
                    // Detectar lectura anómala del termopar (desconectado o fuera de rango)
                    let esError = (c.t <= 0.0 || c.t >= 150.0);
                    let colorBorde = esError ? '#ef4444' : (c.run==1?'#22c55e':'#38bdf8');
                    let estadoHtml = esError ? 
                        '<div class="badge-error">⚠️ FALLA TERMOPAR (PARADA)</div>' : 
                        (c.run==1?'<span style="color:#22c55e">Activo</span>':'<span style="color:#ef4444">Bloqueado</span>');

                    h += `<div class='card' style='border-left-color:${colorBorde}'>
                        <h3>${nombres[i]}</h3>
                        <p>Actual: <b style='font-size:1.3em; color:${esError?'#ef4444':'#38bdf8'};'>${esError?'ERROR':c.t.toFixed(1)+'°C'}</b></p>
                        <div class='sp-box'>
                            <span>Setpoint: <b>${c.sp}°C</b></span><br><br>
                            <button class='btn-step' ${c.run==1||esError?'disabled':''} onclick='setSP(${i},${c.sp-1})'>-</button>
                            <button class='btn-step' ${c.run==1||esError?'disabled':''} onclick='setSP(${i},${c.sp+1})'>+</button>
                        </div>
                        <p>Estado: ${estadoHtml}</p>
                    </div>`;
                });
                document.getElementById('t-cards').innerHTML = h;
            });
        }
        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch(`/set_t?id=${id}&v=${val}`).then(r => {
                if(r.status === 403) alert("¡Detén el sistema primero para cambiar el setpoint!");
                loadThermal();
            }); 
        }
        function toggleT(run){ fetch(`/act_t?run=${run}`).then(()=>loadThermal()); }
        setInterval(loadThermal, 2000); loadThermal();
    </script>
</body></html>)rawliteral";

// --- MONITOREO DE PH DUAL ---
const char HTML_PH[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Módulo pH Dual</title>
<style>
    body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
    .grid{display:flex; flex-wrap:wrap; justify-content:center; gap:20px; margin-top:20px;}
    .card{background:#1e293b; border-radius:15px; padding:20px; width:280px; box-shadow:0 8px 20px rgba(0,0,0,0.3);}
    .ph-val{font-size:56px; color:#2ecc71; font-weight:bold; margin:10px 0;}
    .btn{background:#3b82f6; color:white; border:none; padding:12px; border-radius:8px; cursor:pointer; width:100%; font-weight:bold; margin-top:10px; font-size:0.95em;}
    .btn:hover{background:#2563eb;}
    .nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none; font-weight:bold;}
    .cal-menu{background:#0f172a; padding:10px; border-radius:8px; margin-top:10px;}
    .ph-error{color:#ef4444 !important; font-size:36px !important;}
</style></head>
<body>
    <a href='/' class='nav-back'>⬅ Volver al Menú</a>
    <h2>Monitoreo y Calibración ADS1115 (16-Bits)</h2>
    
    <div class='grid'>
        <div class='card'>
            <h3>Electrodo pH 1 (Zincado)</h3>
            <div class='ph-val' id='ph1'>7.00</div>
            <div class='cal-menu'>
                <small>Menú de Calibración</small>
                <button class='btn' onclick='calibrar(1,7)'>Calibrar punto pH 7.0</button>
                <button class='btn' onclick='calibrar(1,4)'>Calibrar punto pH 4.0</button>
            </div>
        </div>
        <div class='card'>
            <h3>Electrodo pH 2 (Niquelado)</h3>
            <div class='ph-val' id='ph2'>7.00</div>
            <div class='cal-menu'>
                <small>Menú de Calibración</small>
                <button class='btn' onclick='calibrar(2,7)'>Calibrar punto pH 7.0</button>
                <button class='btn' onclick='calibrar(2,4)'>Calibrar punto pH 4.0</button>
            </div>
        </div>
    </div>

    <script>
        function readPH(){
            fetch('/get_ph_dual').then(r=>r.json()).then(d=>{
                let p1Val = parseFloat(d.p1);
                let p2Val = parseFloat(d.p2);
                
                let el1 = document.getElementById('ph1');
                let el2 = document.getElementById('ph2');

                // Mostrar error si la lectura está fuera del rango físico (0 a 14)
                if(p1Val < 0 || p1Val > 14 || isNaN(p1Val)){
                    el1.innerText = "⚠️ ERROR";
                    el1.className = "ph-val ph-error";
                } else {
                    el1.innerText = d.p1;
                    el1.className = "ph-val";
                }

                if(p2Val < 0 || p2Val > 14 || isNaN(p2Val)){
                    el2.innerText = "⚠️ ERROR";
                    el2.className = "ph-val ph-error";
                } else {
                    el2.innerText = d.p2;
                    el2.className = "ph-val";
                }
            });
        }
        function calibrar(id, punto){
            if(confirm(`¿Confirmas sumergir el electrodo ${id} en buffer pH ${punto} y calibrar?`)){
                fetch(`/do_cal_ph?id=${id}&p=${punto}`).then(()=>alert('Punto guardado en NVS Preferences.'));
            }
        }
        setInterval(readPH, 2500); readPH();
    </script>
</body></html>)rawliteral";

// --- FUENTE DE CORRIENTE ---
const char HTML_FUENTE[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Fuente de Corriente</title>
<style>
    body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
    .card{background:#1e293b; border-radius:15px; padding:25px; margin:20px auto; max-width:480px; box-shadow:0 10px 25px rgba(0,0,0,0.4);}
    .status-badge{display:inline-block; padding:8px 16px; border-radius:20px; font-weight:bold; font-size:1.1em; margin:10px 0;}
    .status-on{background:#22c55e22; color:#22c55e; border:2px solid #22c55e;}
    .status-off{background:#ef444422; color:#ef4444; border:2px solid #ef4444;}
    .amp-box{font-size:52px; color:#38bdf8; margin:15px 0; font-weight:bold;}
    .btn{padding:14px 20px; cursor:pointer; border-radius:10px; border:none; margin:5px; font-weight:bold; width:46%; font-size:1em; transition:0.2s;}
    .btn-pwr{width:100%; font-size:20px; margin:15px 0 25px 0; padding:18px; border-radius:12px; font-weight:bold; cursor:pointer; border:none; transition:0.2s;}
    .btn-pwr-off{background:#22c55e; color:white; box-shadow:0 4px 15px rgba(34,197,94,0.4);}
    .btn-pwr-on{background:#ef4444; color:white; box-shadow:0 4px 15px rgba(239,68,68,0.4);}
    .btn-pwr:hover{transform:scale(1.02);}
    .active{background:#3b82f6; color:white;} 
    .inactive{background:#334155; color:#94a3b8;}
    .nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none; font-weight:bold;}
    input[type=range]{width:95%; accent-color:#38bdf8; margin:12px 0;}
    .ctrl-group{background:#0f172a; padding:15px; border-radius:10px; margin-top:15px; text-align:left;}
    .ctrl-group label{font-weight:bold; color:#cbd5e1;}
</style></head>
<body>
    <a href='/' class='nav-back'>⬅ Volver al Menú</a>
    <h2>Controlador de Corriente (DAC MCP4725)</h2>
    
    <div class='card'>
        <!-- Botón principal de encendido/apagado -->
        <button class='btn-pwr btn-pwr-off' id='btn-power' onclick='togglePower()'>⚡ ENCENDER FUENTE</button>
        
        <div><span class='status-badge status-off' id='status-badge'>ESTADO: DESACTIVADA (0.00 A)</span></div>
        
        <div class='amp-box'><span id='amp-amps'>0.00</span> A</div>
        
        <button class='btn active' id='btn-dc' onclick='setModo(0)'>CONTINUA (DC)</button>
        <button class='btn inactive' id='btn-pulsed' onclick='setModo(1)'>PULSADA (PWM)</button>
        
        <div class='ctrl-group'>
            <label>Amplitud DAC: <b id='amp-bits' style='color:#38bdf8;'>1024</b> bits (<span id='amp-calc'>1.65</span> A)</label><br>
            <input type='range' id='slide-amp' min='0' max='4095' value='1024' oninput='onAmpChange(this.value)'>
        </div>
        
        <div id='pulsed-options' style='display:none;'>
            <div class='ctrl-group'>
                <label>Frecuencia: <b id='freq-val' style='color:#38bdf8;'>1</b> Hz</label><br>
                <input type='range' id='slide-freq' min='1' max='100' value='1' oninput='sendParam("f", this.value)'>
            </div>
            <div class='ctrl-group'>
                <label>Duty Cycle: <b id='duty-val' style='color:#38bdf8;'>50</b> %</label><br>
                <input type='range' id='slide-duty' min='1' max='99' value='50' oninput='sendParam("d", this.value)'>
            </div>
        </div>
    </div>

    <script>
        let fuenteActiva = false;
        let isDragging = false;

        function loadFuenteData(){
            if (isDragging) return;
            fetch('/data_f').then(r=>r.json()).then(d=>{
                fuenteActiva = (d.act == 1);
                
                let btnPwr = document.getElementById('btn-power');
                let badge = document.getElementById('status-badge');
                let ampVal = parseFloat(d.amps).toFixed(2);
                
                if (fuenteActiva) {
                    btnPwr.innerText = "⏹ APAGAR FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-on";
                    badge.innerText = "⚡ ESTADO: SALIDA ACTIVA (" + ampVal + " A)";
                    badge.className = "status-badge status-on";
                    document.getElementById('amp-amps').innerText = ampVal;
                } else {
                    btnPwr.innerText = "⚡ ENCENDER FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-off";
                    badge.innerText = "⏹ ESTADO: DESACTIVADA (0.00 A)";
                    badge.className = "status-badge status-off";
                    document.getElementById('amp-amps').innerText = "0.00";
                }

                let isPulsed = (d.modo == 1);
                document.getElementById('pulsed-options').style.display = isPulsed ? 'block' : 'none';
                document.getElementById('btn-dc').className = isPulsed ? 'btn inactive' : 'btn active';
                document.getElementById('btn-pulsed').className = isPulsed ? 'btn active' : 'btn inactive';

                document.getElementById('slide-amp').value = d.amp;
                document.getElementById('amp-bits').innerText = d.amp;
                document.getElementById('amp-calc').innerText = ampVal;
                
                document.getElementById('slide-freq').value = d.freq;
                document.getElementById('freq-val').innerText = d.freq;
                
                document.getElementById('slide-duty').value = d.duty;
                document.getElementById('duty-val').innerText = d.duty;
            });
        }

        function togglePower(){
            let nuevoEstado = fuenteActiva ? 0 : 1;
            fetch(`/act_f?run=${nuevoEstado}`).then(() => loadFuenteData());
        }

        function setModo(m){
            document.getElementById('pulsed-options').style.display = (m==1) ? 'block' : 'none';
            document.getElementById('btn-dc').className = (m==1) ? 'btn inactive' : 'btn active';
            document.getElementById('btn-pulsed').className = (m==1) ? 'btn active' : 'btn inactive';
            fetch(`/modo_f?v=${m}`).then(() => loadFuenteData());
        }

        function onAmpChange(v){
            isDragging = true;
            document.getElementById('amp-bits').innerText = v;
            let amps = ((v / 4095.0) * 6.6).toFixed(2);
            document.getElementById('amp-calc').innerText = amps;
            if (fuenteActiva) {
                document.getElementById('amp-amps').innerText = amps;
            }
            sendParam("a", v);
            setTimeout(() => { isDragging = false; }, 1000);
        }

        function sendParam(p, v){
            if(p=='f') document.getElementById('freq-val').innerText = v;
            if(p=='d') document.getElementById('duty-val').innerText = v;
            fetch(`/set_f?p=${p}&v=${v}`);
        }

        setInterval(loadFuenteData, 2000); 
        loadFuenteData();
    </script>
</body></html>)rawliteral";

// --- FUNCIONES QUE ENVÍAN LAS PÁGINAS AL NAVEGADOR ---

void handleMenu() { server.send_P(200, "text/html", HTML_MENU); }

void handleTermico() { server.send_P(200, "text/html", HTML_TERMICO); }

void handleFuente() { server.send_P(200, "text/html", HTML_FUENTE); }

void handlePH() { server.send_P(200, "text/html", HTML_PH); }
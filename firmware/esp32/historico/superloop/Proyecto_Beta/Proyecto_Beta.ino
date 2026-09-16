#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <max6675.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h> 

/******************** CONFIGURACIÓN RED ********************/
const char* ssid = "Uli";
const char* password = "12345678";
WebServer server(80);

Preferences memoria; 

/******************** MÓDULOS AMBIENTALES ********************/
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;
float amb_temp = 0, amb_hum = 0, amb_pres = 0;

/******************** MÓDULO pH (DUAL) ********************/
Adafruit_ADS1115 ads;
float v7_1 = 2.5, v4_1 = 3.0, m_ph1 = -5.405, phActual1 = 7.0;
float v7_2 = 2.5, v4_2 = 3.0, m_ph2 = -5.405, phActual2 = 7.0;
bool calibradoPH1 = false, calibradoPH2 = false;

/******************** MÓDULO FUENTE (DAC) ********************/
Adafruit_MCP4725 dac;
bool modoPulsado = false;
bool fuenteActiva = false; // <-- NUEVA VARIABLE DE ESTADO
int amplitudDAC = 1024, frecuencia = 1, dutyCycle = 50;
const float VREF = 3.3; // <-- ACTUALIZADO A 3.3V

/******************** MÓDULO TÉRMICO ********************/
struct CanalTermico {
  int id; MAX6675* sensor;
  double temperatura, setpoint;
  bool activo;
  const double Kp, Ki, Kd;
  double integral, errorPrevio, limitePotencia;
  
  CanalTermico(int _id, int sck, int cs, int so, double p, double i, double d) 
    : Kp(p), Ki(i), Kd(d) {
    id = _id; sensor = new MAX6675(sck, cs, so);
    setpoint = 60; activo = false; integral = 0; errorPrevio = 0; limitePotencia = 0;
  }
  
  double calcularPID() {
    double input = sensor->readCelsius();
    if (!isnan(input)) {
      temperatura = input;
    }

    if (!activo) {
        integral = 0; 
        return 0; 
    }
    
    double error = setpoint - temperatura;
    if (temperatura >= setpoint) { integral = 0; return 0; }
    integral += error;
    double derivada = error - errorPrevio;
    errorPrevio = error;
    return constrain(Kp * error + Ki * integral + Kd * derivada, 0, 100);
  }
};

#define COMMON_SCK 18
#define COMMON_SO  19
CanalTermico canales[] = {
  CanalTermico(0, COMMON_SCK, 5,  COMMON_SO, 62.65, 0.0897, 0.0),
  CanalTermico(1, COMMON_SCK, 4,  COMMON_SO, 62.65, 0.0897, 0.0),
  CanalTermico(2, COMMON_SCK, 13, COMMON_SO, 16.71, 0.0239, 0.0),
  CanalTermico(3, COMMON_SCK, 14, COMMON_SO, 62.51, 0.0895, 0.0)
};

unsigned long lastPID = 0, lastRamp = 0, lastPH = 0, lastEnv = 0, lastIPMsg = 0;

/******************** FUNCIONES APOYO ********************/
float leerVoltajePH(int canal) {
  long suma = 0;
  for (int i = 0; i < 15; i++) { suma += ads.readADC_SingleEnded(canal); delay(2); }
  return (suma / 15.0) * 0.1875 / 1000.0;
}

/******************** INTERFACES HTML ********************/

void handleMenu() {
  String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
.menu-card{background:#1e293b; padding:30px; border-radius:20px; display:inline-block; box-shadow:0 10px 30px rgba(0,0,0,0.5); width:90%; max-width:500px;}
.env-box{display:flex; justify-content:space-around; background:#334155; padding:15px; border-radius:15px; margin:20px 0;}
.env-item{font-size:0.9em; color:#38bdf8;} .env-val{font-size:1.4em; display:block; color:white; font-weight:bold;}
.btn-menu{display:block; padding:18px; margin:15px auto; background:#3b82f6; color:white; text-decoration:none; font-weight:bold; border-radius:10px; transition:0.3s;}
.btn-menu:hover{background:#2563eb; transform:scale(1.02);}
</style></head><body>
<div class="menu-card">
  <h1>DASHBOARD MAESTRO</h1>
  <p style="color:#94a3b8">Fernando Salvador Samayoa Martinez</p>
  <div class="env-box">
    <div class="env-item">TEMP<span class="env-val" id="et">--</span></div>
    <div class="env-item">HUM<span class="env-val" id="eh">--</span></div>
    <div class="env-item">PRES<span class="env-val" id="ep">--</span></div>
  </div>
  <a href="/termico" class="btn-menu">🔥 CONTROL TÉRMICO</a>
  <a href="/fuente" class="btn-menu">⚡ FUENTE DE CORRIENTE</a>
  <a href="/ph" class="btn-menu">🧪 MONITOR DE pH DUAL</a>
</div>
<script>
function updEnv(){
  fetch('/data_env').then(r=>r.json()).then(d=>{
    document.getElementById('et').innerText = d.t+"°C";
    document.getElementById('eh').innerText = d.h+"%";
    document.getElementById('ep').innerText = d.p+" hPa";
  });
}
setInterval(updEnv, 3000); updEnv();
</script></body></html>)rawliteral";
  server.send(200, "text/html", html);
}

void handleTermico() {
  String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
.grid{display:flex; flex-wrap:wrap; justify-content:center; gap:15px;}
.card{background:#1e293b; border-radius:12px; padding:15px; width:220px; border-left:5px solid #64748b;}
.btn{padding:10px 20px; cursor:pointer; border-radius:8px; border:none; margin:5px; font-weight:bold;}
.nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none;}
.selector{display:flex; align-items:center; justify-content:center; gap:10px; margin-top:10px; background:#0f172a; padding:5px; border-radius:8px;}
.btn-step{background:#3b82f6; color:white; border:none; width:35px; height:35px; border-radius:5px; font-weight:bold; cursor:pointer;}
.btn-step:disabled{background:#475569; cursor:not-allowed;}
</style></head><body>
<a href="/" class="nav-back">⬅ Menú</a>
<h1>CONTROL TÉRMICO</h1>
<button class="btn" style="background:#10b981; color:white;" onclick="control(1)">INICIAR TODO</button>
<button class="btn" style="background:#ef4444; color:white;" onclick="control(0)">PARAR TODO</button>
<div class="grid" id="cont"></div>
<script>
function update(){
  fetch('/data_t').then(res=>res.json()).then(data=>{
    let c = document.getElementById('cont'); c.innerHTML = "";
    data.forEach((d,i)=>{
      let block = d.run ? 'disabled' : ''; // CANDADO VISUAL
      c.innerHTML += `<div class="card" style="border-left-color:${d.run?'#22c55e':'#ef4444'}">
      <h4>R${i+1}</h4><h2 style="color:${d.run?'#22c55e':'white'}">${d.t.toFixed(1)}°C</h2>
      <div class="selector">
        <button class="btn-step" onclick="adj(${i},-1)" ${block}>-</button>
        <span id="sp_${i}">${d.sp}</span>
        <button class="btn-step" onclick="adj(${i},1)" ${block}>+</button>
      </div></div>`;
    });
  });
}
function adj(id, step){
  let el = document.getElementById('sp_'+id);
  let newVal = parseInt(el.innerText) + step;
  if(newVal<0) newVal=0; if(newVal>150) newVal=150;
  el.innerText = newVal;
  fetch(`/set_t?id=${id}&v=${newVal}`).then(res => {
     if(res.status === 403) alert("¡Detén el sistema primero para cambiar la temperatura!");
  });
}
function control(s){ fetch(`/act_t?run=${s}`); }
setInterval(update,1500); update();
</script></body></html>)rawliteral";
  server.send(200, "text/html", html);
}

void handleFuente() {
  float amperios = ((amplitudDAC * VREF) / 4095.0) * 2.0;
  String estado = fuenteActiva ? "ENCENDIDA" : "APAGADA";
  String colorEstado = fuenteActiva ? "#22c55e" : "#ef4444";
  String textoBoton = fuenteActiva ? "APAGAR FUENTE" : "ENCENDER FUENTE";

  String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
.card{background:#1e293b; border-radius:15px; padding:20px; margin:10px auto; max-width:400px;}
.amp{font-size:48px; color:#22c55e; margin: 15px 0;}
.btn{padding:12px 20px; cursor:pointer; border-radius:10px; border:none; margin:5px; font-weight:bold; width:45%;}
.btn-power{background:#3b82f6; color:white; width:95%; font-size:18px; margin-top:20px;}
.estado{font-size:24px; font-weight:bold; margin-bottom:15px;}
.active{background:#22c55e; color:white;}
.inactive{background:#475569; color:#94a3b8;}
.nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none;}
input[type=range]{width:100%; accent-color:#38bdf8;}
.hidden{display:none;}
</style></head><body>
<a href="/" class="nav-back">⬅ Menú</a>
<h1>FUENTE DE CORRIENTE</h1>
<div class="card">
  <div class="estado" style="color:)rawliteral" + colorEstado + R"rawliteral("><b>)rawliteral" + estado + R"rawliteral(</b></div>
  <button id="btnC" class="btn )rawliteral" + String(!modoPulsado ? "active" : "inactive") + R"rawliteral(" onclick="setM(0)">CONTINUA</button>
  <button id="btnP" class="btn )rawliteral" + String(modoPulsado ? "active" : "inactive") + R"rawliteral(" onclick="setM(1)">PULSADA</button>
  <div class="amp"><span id="at">)rawliteral" + String(amperios, 2) + R"rawliteral(</span> A</div>
  
  <input type="range" min="0" max="4095" value=")rawliteral" + String(amplitudDAC) + R"rawliteral(" oninput="upd('a',this.value)">
  
  <div id="cont-pulsada" class=")rawliteral" + String(modoPulsado ? "" : "hidden") + R"rawliteral(">
    <p>Frecuencia: <span id="fv">)rawliteral" + String(frecuencia) + R"rawliteral(</span> Hz</p>
    <input type="range" min="1" max="100" value=")rawliteral" + String(frecuencia) + R"rawliteral(" oninput="upd('f',this.value)">
    <p>Duty Cycle: <span id="dv">)rawliteral" + String(dutyCycle) + R"rawliteral(</span> %</p>
    <input type="range" min="1" max="99" value=")rawliteral" + String(dutyCycle) + R"rawliteral(" oninput="upd('d',this.value)">
  </div>
  
  <button class="btn btn-power" onclick="toggleFuente()">)rawliteral" + textoBoton + R"rawliteral(</button>
</div>
<script>
function setM(m){ 
  fetch("/modo_f?v="+m).then(() => {
    document.getElementById('btnC').className = (m==0)?'btn active':'btn inactive';
    document.getElementById('btnP').className = (m==1)?'btn active':'btn inactive';
    document.getElementById('cont-pulsada').className = (m==1)?'':'hidden';
  });
}
function upd(p,v){
  if(p=='a') document.getElementById('at').innerText = ((v*3.3/4095)*2).toFixed(2);
  else if(p=='f') document.getElementById('fv').innerText = v;
  else if(p=='d') document.getElementById('dv').innerText = v;
  fetch("/set_f?p="+p+"&v="+v);
}
function toggleFuente(){ fetch('/act_f?run=)rawliteral" + String(fuenteActiva ? "0" : "1") + R"rawliteral(').then(()=>location.reload()); }
</script></body></html>)rawliteral";
  server.send(200, "text/html", html);
}

void handlePH() {
  String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{font-family:sans-serif; background:#0f172a; color:white; text-align:center; padding:20px;}
.grid{display:flex; flex-wrap:wrap; justify-content:center; gap:20px;}
.card{background:#1e293b; border-radius:15px; padding:20px; width:300px;}
.ph-val{font-size:60px; color:#2ecc71; font-weight:bold; margin:10px 0;}
.btn{background:#3498db; color:white; border:none; padding:10px; border-radius:8px; cursor:pointer; width:100%; font-weight:bold; margin-top:10px;}
.nav-back{position:absolute; top:20px; left:20px; color:#38bdf8; text-decoration:none;}
.step-box{display:none; background:#334155; padding:15px; border-radius:10px; margin-top:15px;}
</style></head><body>
<a href="/" class="nav-back">⬅ Menú</a>
<h1>MONITOR DE pH DUAL</h1>
<div class="grid">
  <div class="card">
    <h3>Sonda 1</h3>
    <div id="ph1" class="ph-val">--</div>
    <div id="main1"><button class="btn" onclick="startCal(1)">Calibrar</button></div>
    <div id="cal1" class="step-box"><p id="instr1">pH 7</p><button id="btn1" class="btn" onclick="nextStep(1)">LISTO</button></div>
  </div>
  <div class="card">
    <h3>Sonda 2</h3>
    <div id="ph2" class="ph-val">--</div>
    <div id="main2"><button class="btn" onclick="startCal(2)">Calibrar</button></div>
    <div id="cal2" class="step-box"><p id="instr2">pH 7</p><button id="btn2" class="btn" onclick="nextStep(2)">LISTO</button></div>
  </div>
</div>
<script>
let step1=1, step2=1;
setInterval(()=>{ if(step1==1 && step2==1) fetch('/get_ph_dual').then(r=>r.json()).then(d=>{document.getElementById('ph1').innerText=d.p1;document.getElementById('ph2').innerText=d.p2;});}, 1500);
function startCal(id){ if(id==1){step1=2;document.getElementById('main1').style.display='none';document.getElementById('cal1').style.display='block';}else{step2=2;document.getElementById('main2').style.display='none';document.getElementById('cal2').style.display='block';}}
function nextStep(id){
  let s=(id==1)?step1:step2; let p=(s==2)?7:4;
  fetch(`/do_cal_ph?id=${id}&p=${p}`).then(()=>{
    if(p==7){ if(id==1)step1=3;else step2=3; document.getElementById('instr'+id).innerHTML='pH 4'; }
    else { alert('Sonda '+id+' OK'); location.reload(); }
  });
}
</script></body></html>)rawliteral";
  server.send(200, "text/html", html);
}

/******************** SETUP & LOOP ********************/
void setup() {
  Serial.begin(115200);
  delay(1000);
  Wire.begin(8, 9);
  
  // VELOCIDAD SERIAL PARA EL NANO (9600 BAUDIOS)
  Serial2.begin(9600, SERIAL_8N1, -1, 17); 

  // --- CARGAR DATOS DE MEMORIA NVS ---
  memoria.begin("config", false);

  for(int i=0; i<4; i++) {
    double spGuardado = memoria.getDouble(("sp"+String(i)).c_str(), canales[i].setpoint);
    if (spGuardado <= 0 || spGuardado > 150) {
       spGuardado = 60.0; 
    }
    canales[i].setpoint = spGuardado;
  }

  calibradoPH1 = memoria.getBool("cal1", false);
  v7_1 = memoria.getFloat("v7_1", 2.5);
  v4_1 = memoria.getFloat("v4_1", 3.0);
  m_ph1 = memoria.getFloat("mph1", -5.405);

  calibradoPH2 = memoria.getBool("cal2", false);
  v7_2 = memoria.getFloat("v7_2", 2.5);
  v4_2 = memoria.getFloat("v4_2", 3.0);
  m_ph2 = memoria.getFloat("mph2", -5.405);

  amplitudDAC = memoria.getInt("dac_amp", 1024);
  frecuencia = memoria.getInt("dac_freq", 1);
  dutyCycle = memoria.getInt("dac_duty", 50);
  modoPulsado = memoria.getBool("dac_modo", false);
  fuenteActiva = memoria.getBool("f_activa", false); // <-- CARGA ESTADO DE LA FUENTE
  // -----------------------------------

  dac.begin(0x60);
  ads.begin();
  aht.begin();
  bmp.begin(0x77);

  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nIP: " + WiFi.localIP().toString());

  server.on("/", handleMenu);
  server.on("/termico", handleTermico);
  server.on("/fuente", handleFuente);
  server.on("/ph", handlePH);

  server.on("/data_env", [](){
    String j = "{\"t\":\""+String(amb_temp,1)+"\",\"h\":\""+String(amb_hum,0)+"\",\"p\":\""+String(amb_pres,1)+"\"}";
    server.send(200, "application/json", j);
  });

  server.on("/get_ph_dual", [](){
    String j = "{\"p1\":\""+String(phActual1,2)+"\",\"p2\":\""+String(phActual2,2)+"\"}";
    server.send(200, "application/json", j);
  });

  server.on("/data_t", [](){
    String j = "[";
    for(int i=0;i<4;i++) j += "{\"t\":"+String(canales[i].temperatura)+",\"sp\":"+String(canales[i].setpoint)+",\"run\":"+String(canales[i].activo)+ "}" + (i<3?",":"");
    server.send(200, "application/json", j + "]");
  });

  // --- CANDADO DEL SETPOINT EN EL SERVIDOR ---
  server.on("/set_t", [](){
    int id=server.arg("id").toInt();
    if(id>=0 && id<4) {
      if(!canales[id].activo) { // Candado: Solo permite si NO está activo
        canales[id].setpoint = server.arg("v").toDouble();
        memoria.putDouble(("sp"+String(id)).c_str(), canales[id].setpoint);
        server.send(200, "text/plain", "OK");
      } else {
        server.send(403, "text/plain", "Bloqueado - Sistema Activo");
      }
    } else {
      server.send(400, "text/plain", "Error");
    }
  });

  server.on("/act_t", [](){
    bool s=server.arg("run").toInt();
    for(int i=0;i<4;i++){ 
      canales[i].activo=s; 
      if(!s){ canales[i].limitePotencia=0; canales[i].integral=0; } 
    }
    server.send(200, "text/plain", "OK");
  });

  server.on("/set_f", [](){
    char p=server.arg("p")[0]; int v=server.arg("v").toInt();
    if(p=='a') { amplitudDAC=v; memoria.putInt("dac_amp", v); }
    else if(p=='f') { frecuencia=v; memoria.putInt("dac_freq", v); }
    else if(p=='d') { dutyCycle=v; memoria.putInt("dac_duty", v); }
    server.send(200, "text/plain", "OK");
  });

  server.on("/modo_f", [](){ 
    modoPulsado=(server.arg("v")=="1"); 
    memoria.putBool("dac_modo", modoPulsado);
    server.send(200, "text/plain", "OK"); 
  });

  // --- NUEVO ENDPOINT PARA ENCENDER/APAGAR FUENTE ---
  server.on("/act_f", [](){
    fuenteActiva = (server.arg("run") == "1");
    memoria.putBool("f_activa", fuenteActiva);
    server.send(200, "text/plain", "OK");
  });

  server.on("/do_cal_ph", [](){
    int id = server.arg("id").toInt(); int p = server.arg("p").toInt();
    float v = leerVoltajePH(id-1);
    if(id==1){ 
      if(p==7) { v7_1=v; memoria.putFloat("v7_1", v); }
      if(p==4){ 
        v4_1=v; m_ph1=(4.0-7.0)/(v4_1-v7_1); calibradoPH1=true; 
        memoria.putFloat("v4_1", v); memoria.putFloat("mph1", m_ph1); memoria.putBool("cal1", true);
      } 
    } else { 
      if(p==7) { v7_2=v; memoria.putFloat("v7_2", v); }
      if(p==4){ 
        v4_2=v; m_ph2=(4.0-7.0)/(v4_2-v7_2); calibradoPH2=true; 
        memoria.putFloat("v4_2", v); memoria.putFloat("mph2", m_ph2); memoria.putBool("cal2", true);
      }
    }
    server.send(200, "text/plain", "OK");
  });

  server.begin();
}

void loop() {
  server.handleClient();

  // Lectura Ambiental cada 5 seg
  if (millis() - lastEnv >= 5000) {
    lastEnv = millis();
    sensors_event_t h_event, t_event;
    aht.getEvent(&h_event, &t_event);
    amb_temp = t_event.temperature;
    amb_hum = h_event.relative_humidity;
    amb_pres = bmp.readPressure() / 100.0F;
  }

  // Lectura pH cada 2 seg
  if (millis() - lastPH >= 2000) {
    lastPH = millis();
    float v1 = leerVoltajePH(0), v2 = leerVoltajePH(1);
    phActual1 = calibradoPH1 ? (7.0 + (v1 - v7_1) * m_ph1) : (7.0 + (2.5 - v1) / 0.185);
    phActual2 = calibradoPH2 ? (7.0 + (v2 - v7_2) * m_ph2) : (7.0 + (2.5 - v2) / 0.185);
  }

  // PID y Rampa Térmica
  if (millis() - lastRamp >= 200) {
    lastRamp = millis();
    for(int i=0; i<4; i++) if(canales[i].activo && canales[i].limitePotencia < 100) canales[i].limitePotencia++;
  }

  if (millis() - lastPID >= 1000) {
    lastPID = millis();
    String s = "";
    for(int i=0; i<4; i++) {
      double pidCalculado = canales[i].calcularPID();
      int val = (int)min(pidCalculado, canales[i].limitePotencia);
      
      s += String(val);
      if(i<3) s += ",";
    }
    Serial2.println(s); // Envía al Nano a 9600 baudios
  }

  // --- LÓGICA DEL DAC CON ENCENDIDO/APAGADO ---
  int vOut = 0; // Por defecto envía 0 Volts (Apagado)

  if (fuenteActiva) {
    vOut = amplitudDAC;
    if (modoPulsado) {
      unsigned long p = 1000000 / frecuencia;
      vOut = ((micros() % p) < (p * dutyCycle / 100)) ? amplitudDAC : 0;
    }
  }
  
  dac.setVoltage(vOut, false);
}
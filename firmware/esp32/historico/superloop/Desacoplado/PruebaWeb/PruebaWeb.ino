#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "S24 Ultra de Fernando Samayoa";
const char* password = "soy pobre";

WebServer server(80);

float temp[4] = {55.2,52.7,50.8,23.4};
int setpoint[3] = {60,60,60};

void handleRoot()
{
String html = R"rawliteral(

<!DOCTYPE html>
<html>

<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body{
font-family:Arial;
background:#0f172a;
color:white;
text-align:center;
}

h1{
margin-top:10px;
}

.container{
display:flex;
flex-wrap:wrap;
justify-content:center;
}

.card{
background:#1e293b;
border-radius:15px;
padding:20px;
margin:10px;
width:250px;
box-shadow:0 4px 10px rgba(0,0,0,0.4);
}

.temp{
font-size:40px;
font-weight:bold;
color:#22c55e;
}

.sp{
font-size:18px;
margin-top:5px;
}

input[type=range]{
width:100%;
}

</style>

</head>

<body>

<h1>CONTROL TERMICO</h1>

<div class="container">

)rawliteral";

for(int i=0;i<3;i++)
{
html += "<div class='card'>";
html += "<h2>Tanque "+String(i+1)+"</h2>";
html += "<div class='temp'>"+String(temp[i])+" °C</div>";
html += "<div class='sp'>SP: "+String(setpoint[i])+"</div>";

html += "<input type='range' min='0' max='100' value='"+String(setpoint[i])+"' ";
html += "onchange='updateSP("+String(i)+",this.value)'>";

html += "</div>";
}

html += "</div>";

html += "<h2>Ambiente: "+String(temp[3])+" °C</h2>";

html += R"rawliteral(

<script>

function updateSP(tank,value)
{
fetch("/set?t="+tank+"&v="+value);
}

setTimeout(function(){
location.reload();
},2000);

</script>

</body>
</html>

)rawliteral";

server.send(200,"text/html",html);
}

void setSP()
{
int tank = server.arg("t").toInt();
int value = server.arg("v").toInt();

setpoint[tank] = value;

server.send(200,"text/plain","OK");
}

void setup()
{
Serial.begin(115200);

WiFi.begin(ssid,password);

while(WiFi.status()!=WL_CONNECTED)
{
delay(500);
Serial.print(".");
}

Serial.println("");
Serial.println(WiFi.localIP());

server.on("/",handleRoot);
server.on("/set",setSP);

server.begin();
}

void loop()
{
server.handleClient();
}
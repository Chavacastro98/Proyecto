#include <AcPhaseControl.h>

/******************** CONFIGURACIÓN DE PINES ********************/
int ZC_PIN = 3; 
int GATE_PINS[] = {7, 8, 9, 10}; 
int NUM_CANALES = 4;

AcPhaseControl dimmer;

/******************** VARIABLES DE CONTROL ********************/
unsigned long windowSize = 3000; 
unsigned long windowStart = 0;
int potencias[4] = {0, 0, 0, 0}; 

void setup() {
  Serial.begin(9600); 
  // ¡CLAVE! Reducimos el tiempo de espera del puerto serial a solo 50ms para no trabar el ciclo
  Serial.setTimeout(50); 
  
  for(int i = 0; i < NUM_CANALES; i++) {
    dimmer.begin(GATE_PINS[i], ZC_PIN);
  }
  
  windowStart = millis();
}

void loop() {
  // 1. RECEPCIÓN DE DATOS SÚPER RÁPIDA (NO BLOQUEANTE)
  if (Serial.available() > 0) {
    // Leemos todo el mensaje de golpe hasta el salto de línea (ej. "100,0,50,20\n")
    String data = Serial.readStringUntil('\n');
    
    int idx = 0;
    int startIndex = 0;
    for (int i = 0; i < data.length(); i++) {
      if (data.charAt(i) == ',') {
        potencias[idx] = constrain(data.substring(startIndex, i).toInt(), 0, 100);
        startIndex = i + 1;
        idx++;
        if (idx >= 3) break;
      }
    }
    // El último valor después de la última coma
    potencias[3] = constrain(data.substring(startIndex).toInt(), 0, 100);
  }

  // 2. LÓGICA DE TIEMPO (PWM LENTO)
  unsigned long now = millis();
  if (now - windowStart >= windowSize) {
    windowStart = now; 
  }

  // 3. CONTROL DE SALIDAS
  for (int i = 0; i < NUM_CANALES; i++) {
    unsigned long tiempoEncendido = (windowSize * (unsigned long)potencias[i]) / 100;
    
    if (potencias[i] == 0) {
      dimmer.APC_OFF(GATE_PINS[i]);
    } 
    else if ((now - windowStart) < tiempoEncendido) {
      dimmer.APC_ON(GATE_PINS[i]);
    } 
    else {
      dimmer.APC_OFF(GATE_PINS[i]);
    }
  }
}
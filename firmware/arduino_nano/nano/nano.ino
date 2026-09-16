/**
 * =================================================================================
 * FIRMWARE DEL ARDUINO NANO — CONTROL DE TRIACS (nano.ino)
 * =================================================================================
 * Plataforma: Arduino Nano (ATmega328P)
 * Módulo de potencia: MDAC4C (4 canales AC con optoacopladores MOC3021 y TRIACs BTA24)
 *
 * ¿QUÉ HACE ESTE PROGRAMA?
 * Recibe porcentajes de potencia (0-100%) del ESP32 por comunicación serie y los
 * convierte en pulsos de disparo para 4 TRIACs que controlan resistencias de
 * calentamiento de corriente alterna (AC).
 *
 * ¿CÓMO FUNCIONA EL CONTROL DE FASE?
 * 1. La corriente alterna de la red eléctrica (60 Hz) tiene forma de onda senoidal.
 *    Cada semiciclo dura 8.33 ms (8333 µs). Un optoacoplador 4N35 en la placa
 *    MDAC4C detecta el momento exacto en que la onda cruza por cero voltios y
 *    genera una interrupción en el Pin 3 (INT1) del Arduino.
 *
 * 2. Para controlar la potencia, se retrasa el pulso de encendido del TRIAC
 *    después del cruce por cero:
 *      - Retardo 0 µs      = 100% de potencia (TRIAC conduce todo el semiciclo)
 *      - Retardo 8333 µs   = 0% de potencia (TRIAC nunca se enciende)
 *
 * 3. Una tabla de 101 valores precalculados (lut_triac) convierte los porcentajes
 *    (0-100%) en tiempos de retardo en microsegundos, corrigiendo la no-linealidad
 *    de la potencia RMS en una onda senoidal.
 *
 * SEGURIDAD:
 * - Si el ESP32 deja de enviar datos por más de 2 segundos, todos los TRIACs
 *   se apagan automáticamente (perro guardián de comunicación).
 * - El pulso de disparo al gate del TRIAC dura 80 µs para asegurar que la
 *   cadena completa MOC3021 → BTA24-800BW se active correctamente.
 * =================================================================================
 */

#include <Arduino.h>

// =================================================================================
// PINES DEL HARDWARE
// =================================================================================
const int ZC_PIN = 3;                  // Pin de cruce por cero (interrupción INT1, conectado al 4N35)
const int GATE_PINS[] = {7, 8, 9, 10}; // Pines de disparo conectados a los opto-TRIACs (MOC3021)
const int NUM_CANALES = 4;             // Cantidad de canales de potencia

// Máscaras de bits para manipulación directa de los registros PORT del ATmega328P.
// Esto permite apagar los 4 pines de disparo en solo 2 instrucciones de CPU
// en vez de 4 llamadas a digitalWrite() (que son mucho más lentas).
#define GATES_PORTD_MASK 0b10000000    // Pin 7 está en PORTD bit 7
#define GATES_PORTB_MASK 0b00000111    // Pins 8, 9, 10 están en PORTB bits 0, 1, 2

// =================================================================================
// TABLA DE CONVERSIÓN PORCENTAJE → RETARDO EN MICROSEGUNDOS
// =================================================================================
// Convierte un porcentaje de potencia (0 a 100%) en el tiempo de retardo que hay
// que esperar después del cruce por cero para encender el TRIAC.
// La tabla está calculada con la fórmula inversa de potencia RMS de una senoidal:
//   retardo(p) = (arccos(2×p/100 - 1) / π) × 8333 µs
// Se almacena en Flash (PROGMEM) para ahorrar los 202 bytes de RAM que ocuparía.
const uint16_t lut_triac[101] PROGMEM = {
  8333, 7366, 7108, 6924, 6776, 6649, 6538, 6436, 6343, 6256, 
  6176, 6099, 6026, 5956, 5889, 5824, 5763, 5703, 5643, 5586, 
  5531, 5476, 5423, 5371, 5319, 5269, 5221, 5171, 5124, 5076, 
  5029, 4984, 4937, 4892, 4847, 4804, 4759, 4716, 4672, 4629, 
  4587, 4544, 4502, 4459, 4417, 4376, 4334, 4292, 4251, 4207, 
  4167, 4126, 4082, 4041, 3999, 3957, 3916, 3874, 3831, 3789, 
  3746, 3704, 3661, 3617, 3574, 3529, 3486, 3441, 3396, 3349, 
  3304, 3257, 3209, 3162, 3112, 3064, 3014, 2962, 2910, 2857, 
  2802, 2747, 2690, 2630, 2570, 2509, 2444, 2377, 2307, 2234, 
  2157, 2077, 1990, 1897, 1795, 1684, 1557, 1409, 1225, 967, 0
};

// =================================================================================
// DURACIÓN DEL PULSO DE GATE (80 µs)
// =================================================================================
// La cadena de activación del módulo es:
//   Arduino Pin → Resistor → LED MOC3021 → Foto-TRIAC MOC3021 → Gate BTA24-800BW
// Cada etapa tiene un retardo de propagación. El total mínimo teórico es ~10-22 µs,
// pero se usa 80 µs para tener un margen de seguridad amplio (~300%) que cubra
// variaciones por temperatura de operación, tolerancias de componentes e interferencia.
const uint16_t PULSO_GATE_US = 80;

// =================================================================================
// VARIABLES COMPARTIDAS CON LA INTERRUPCIÓN
// =================================================================================
// Se marcan como "volatile" porque la interrupción (ISR) las modifica en cualquier
// momento, y el compilador debe leerlas siempre de RAM (no de una copia en caché).
volatile unsigned long tCruceCero = 0;                        // Marca de tiempo del último cruce por cero (µs)
volatile uint16_t retardos_us[4] = {8333, 8333, 8333, 8333};  // Retardos de disparo (8333 = 0% = apagado)
volatile bool disparado[4] = {true, true, true, true};        // true = ya se disparó en este semiciclo

// Perro guardián: si no llegan datos del ESP32 en este tiempo, se apagan los TRIACs
unsigned long ultimaComunicacionMs = 0;
const unsigned long TIMEOUT_UART_MS = 3000; // 3 segundos de tolerancia (3 paquetes perdidos)

// Buffer para recibir datos serie byte a byte sin usar memoria dinámica
char rxBuf[32];
uint8_t rxPos = 0;

/**
 * Rutina de interrupción que se ejecuta cada vez que la onda AC cruza por cero.
 * Registra el momento del cruce y apaga todos los gates usando manipulación
 * directa de los registros PORT (mucho más rápido que 4× digitalWrite()).
 * Tiempo total de ejecución: ~8 µs.
 */
void alCruzarPorCero() {
  tCruceCero = micros();

  // Apagar todos los gates simultáneamente
  PORTD &= ~GATES_PORTD_MASK;  // Pin 7 → LOW
  PORTB &= ~GATES_PORTB_MASK;  // Pins 8, 9, 10 → LOW

  // Preparar las banderas para el nuevo semiciclo
  for (uint8_t i = 0; i < NUM_CANALES; i++) {
    disparado[i] = (retardos_us[i] >= 8100); // Si el retardo es ≥ 8100 µs, el canal está apagado
  }
}

/**
 * Configuración inicial del Arduino Nano.
 */
void setup() {
  // Comunicación serie con el ESP32 a 9600 baudios
  Serial.begin(9600);
  
  // Pin de cruce por cero como entrada con resistencia pull-up interna
  pinMode(ZC_PIN, INPUT_PULLUP);
  
  // Pines de disparo como salidas, inicialmente apagados
  for (int i = 0; i < NUM_CANALES; i++) {
    pinMode(GATE_PINS[i], OUTPUT);
    digitalWrite(GATE_PINS[i], LOW);
  }

  // Activar interrupción en el flanco ascendente del cruce por cero
  attachInterrupt(digitalPinToInterrupt(ZC_PIN), alCruzarPorCero, RISING);
  
  ultimaComunicacionMs = millis();
}

/**
 * Decodifica la trama CSV recibida del ESP32.
 * Formato esperado: "pot0,pot1,pot2,pot3" (ejemplo: "50,0,100,25")
 * Cada valor es un porcentaje de potencia (0-100%) para un canal.
 */
void procesarTrama(char* str) {
  int p0, p1, p2, p3;
  if (sscanf(str, "%d,%d,%d,%d", &p0, &p1, &p2, &p3) == 4) {
    ultimaComunicacionMs = millis();

    // Desactivar interrupciones para actualizar los 4 retardos de forma atómica.
    // En el ATmega328P (8 bits), escribir un uint16_t (2 bytes) NO es atómico;
    // sin esta protección, la ISR podría leer un valor a medio escribir.
    noInterrupts();
    retardos_us[0] = pgm_read_word(&(lut_triac[constrain(p0, 0, 100)]));
    retardos_us[1] = pgm_read_word(&(lut_triac[constrain(p1, 0, 100)]));
    retardos_us[2] = pgm_read_word(&(lut_triac[constrain(p2, 0, 100)]));
    retardos_us[3] = pgm_read_word(&(lut_triac[constrain(p3, 0, 100)]));
    interrupts();
  }
}

/**
 * Bucle principal. Ejecuta 3 tareas en cada iteración:
 * 1. Recibir datos serie del ESP32 byte a byte (sin bloquear)
 * 2. Verificar si el ESP32 sigue enviando datos (perro guardián)
 * 3. Disparar los TRIACs en el momento preciso según el ángulo de fase
 */
void loop() {
  // --- 1. RECEPCIÓN SERIE (byte a byte, sin bloquear) ---
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      rxBuf[rxPos] = '\0';
      procesarTrama(rxBuf);
      rxPos = 0;
    } else if (c != '\r' && rxPos < sizeof(rxBuf) - 1) {
      rxBuf[rxPos++] = c;
    }
  }

  // --- 2. PERRO GUARDIÁN DE COMUNICACIÓN ---
  // Si no llegan datos del ESP32 en 2 segundos, apagar todo por seguridad
  if (millis() - ultimaComunicacionMs > TIMEOUT_UART_MS) {
    noInterrupts();
    for (int i = 0; i < NUM_CANALES; i++) {
      retardos_us[i] = 8333; // 8333 µs = 0% de potencia = apagado
    }
    interrupts();
    PORTD &= ~GATES_PORTD_MASK;
    PORTB &= ~GATES_PORTB_MASK;
  }

  // --- 3. DISPARO DE TRIACS POR ÁNGULO DE FASE ---
  // Leer la marca de tiempo del cruce por cero de forma atómica.
  // En el ATmega328P (8 bits), leer un unsigned long (4 bytes) no es atómico;
  // sin protección, la ISR podría actualizar el valor entre dos instrucciones
  // de lectura, corrompiendo el resultado.
  noInterrupts();
  unsigned long tCruce_local = tCruceCero;
  interrupts();

  unsigned long tTranscurrido = micros() - tCruce_local;

  // Solo evaluar disparos dentro del semiciclo útil (< 8200 µs)
  if (tTranscurrido < 8200) {
    for (uint8_t i = 0; i < NUM_CANALES; i++) {
      if (!disparado[i] && tTranscurrido >= retardos_us[i]) {
        // Enviar pulso de 80 µs al gate del TRIAC para encenderlo
        digitalWrite(GATE_PINS[i], HIGH);
        delayMicroseconds(PULSO_GATE_US);
        digitalWrite(GATE_PINS[i], LOW);
        disparado[i] = true;
      }
    }
  }
}
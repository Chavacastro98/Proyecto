/**
 * =================================================================================
 * MÓDULO DE CONTROL TÉRMICO PI (Modulo_Termico.cpp) — Versión RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * FUNDAMENTACIÓN MATEMÁTICA DEL CONTROLADOR PI DISCRETO:
 * La ecuación en diferencias evaluada a una tasa de muestreo Delta_t = 1.0 s es:
 *
 *   1. Cálculo del Error de Consigna:
 *        e(k) = T_setpoint - T_medida(k)
 *
 *   2. Acción Proporcional:
 *        P(k) = Kp * e(k)
 *
 *   3. Acción Integral con Anti-Windup:
 *        I(k) = I(k-1) + e(k) * Delta_t
 *        Saturación estricta del término acumulado:
 *          0% <= Ki * I(k) <= 100%
 *        Esto impide el envenenamiento del integrador durante transitorios de arranque
 *        o cambios bruscos de setpoint, eliminando el sobretiro excesivo (overshoot).
 *
 *   4. Señal de Control Resultante:
 *        u(k) = sat[ P(k) + Ki * I(k) ] en el intervalo [0, 100%]
 *
 *   5. Limitación por Rampa de Potencia:
 *        u_final(k) = min( u(k), limitePotencia(k) )
 * =================================================================================
 */

#include "Modulo_Termico.h"
#include "RTOS_Core.h"
#include "config.h"

/**
 * @brief Instanciación de los 4 canales térmicos de proceso con sus correspondientes
 * ganancias sintonizadas analíticamente para cada volumen de electrolito.
 */
CanalTermico canales[] = {
    CanalTermico(0, COMMON_SCK, PIN_CS_TC0, COMMON_SO, 13.92f, 0.0199f), // Canal 0: Limpieza (450W, normalizado %/°C)
    CanalTermico(1, COMMON_SCK, PIN_CS_TC1, COMMON_SO, 13.92f, 0.0199f), // Canal 1: Decapado (450W, normalizado %/°C)
    CanalTermico(2, COMMON_SCK, PIN_CS_TC2, COMMON_SO, 92.83f, 0.1328f), // Canal 2: Celda Hull (18W, normalizado %/°C)
    CanalTermico(3, COMMON_SCK, PIN_CS_TC3, COMMON_SO, 13.89f, 0.0199f)  // Canal 3: Niquelado (450W, normalizado %/°C)
};

/**
 * @brief Inicializa los pines GPIO de Chip Select (CS) del bus SPI y los pone en nivel alto (inactivos).
 */
void inicializarModuloTermico() {
  for (int i = 0; i < 4; i++) {
    pinMode(canales[i].pinCS, OUTPUT);
    digitalWrite(canales[i].pinCS, HIGH); // CS deshabilitado en bus SPI (Lógica invertida)
  }
  Serial.println("[TERMICO] Canales térmicos SPI inicializados en pines CS: 5, 4, 13, 14.");
}

/**
 * @brief Ejecuta el ciclo de lectura de temperatura, validación metrológica y cálculo PI.
 *
 * SECUENCIA DE EJECUCIÓN:
 * 1. Lee el termopar MAX6675 bajo protección de xSPIMutex.
 * 2. Verifica integridad física del sensor (rango 0.0 .. 150.0 °C). Si falla, enclava Fail-Safe.
 * 3. Si la temperatura supera la consigna en +2.0 °C, anula la potencia inmediatamente.
 * 4. Aplica las ecuaciones discretas P + I con saturación anti-windup.
 *
 * @return Porcentaje de potencia calculada en escala 0 a 100%.
 */
int CanalTermico::calcularPI() {
  if (g_failsafe_latched) {
    if (takeDataMutex(pdMS_TO_TICKS(10))) {
      activo = false;
      integral = 0.0f;
      potenciaActual = 0;
      giveDataMutex();
    }
    return 0;
  }

  // 1. Lectura del sensor MAX6675 serializada por xSPIMutex
  float input = 0.0f;
  if (takeSPIMutex(pdMS_TO_TICKS(50))) {
    input = (float)sensor.readCelsius();
    giveSPIMutex();
  } else {
    input = temperatura; // Conservar última lectura si hubo contención temporal en el bus
  }

  // 2. Verificación metrológica y de seguridad industrial
  // Un valor NaN, <= 0.0 °C o >= 150.0 °C indica rotura del termopar o desconexión del cable
  if (isnan(input) || input <= 0.0f || input >= 150.0f) {
    if (activo) {
      char msg[64];
      snprintf(msg, sizeof(msg), "Falla Termopar Canal %d (Lectura: %.1f C)", id, input);
      triggerFailSafe((uint8_t)(ERR_TC0_FAIL + id), msg);
    }

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      activo = false;
      integral = 0.0f;
      temperatura = 0.0f;
      potenciaActual = 0;
      tiempoSobretemperatura = 0;
      giveDataMutex();
    }
    return 0;
  }

  // 3. Copia atómica de variables locales bajo xDataMutex
  float tempLocal = 0.0f;
  float spLocal = 0.0f;
  bool activoLocal = false;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    temperatura = input;
    tempLocal = temperatura;
    spLocal = setpoint;
    activoLocal = activo;
    giveDataMutex();
  } else {
    return 0;
  }

  if (!activoLocal) {
    if (takeDataMutex(pdMS_TO_TICKS(10))) {
      integral = 0.0f;
      potenciaActual = 0;
      tiempoSobretemperatura = 0;
      giveDataMutex();
    }
    return 0;
  }

  // Interlock por sobre-temperatura: si T >= Setpoint + 2.0 °C, corte preventivo inmediato de potencia
  if (tempLocal >= (spLocal + 2.0f)) {
    // Si la condición crítica persiste por encima de Setpoint + TEMP_OVERHEAT_DELTA_C durante TEMP_OVERHEAT_HOLD_MS -> Fail-Safe Latch
    if (tempLocal >= (spLocal + TEMP_OVERHEAT_DELTA_C)) {
      if (tiempoSobretemperatura == 0) {
        tiempoSobretemperatura = millis();
      } else if (millis() - tiempoSobretemperatura >= TEMP_OVERHEAT_HOLD_MS) {
        char msg[64];
        snprintf(msg, sizeof(msg), "Sobretemperatura critica Canal %d (%.1f C >= SP+%.1f C por %u s)",
                 id, tempLocal, TEMP_OVERHEAT_DELTA_C, (unsigned)(TEMP_OVERHEAT_HOLD_MS / 1000));
        triggerFailSafe((uint8_t)ERR_TEMP_OVERHEAT, msg);
      }
    } else {
      tiempoSobretemperatura = 0;
    }
    return 0;
  } else {
    tiempoSobretemperatura = 0;
  }

  // 4. Algoritmo de Control Proporcional-Integral (PI)
  float error = spLocal - tempLocal;
  float P = Kp * error;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    integral += error * 1.0f; // Periodo Delta_t = 1.0 segundo

    // Anti-Windup estricto: evitar que el término integral exceda el rango útil [0, 100%]
    if (Ki > 0.0f) {
      if (integral * Ki > 100.0f) integral = 100.0f / Ki;
      if (integral * Ki < 0.0f)   integral = 0.0f;
    }
    float I = Ki * integral;
    giveDataMutex();

    float salida = P + I;
    return (int)constrain(salida, 0.0f, 100.0f);
  }

  return 0;
}

/**
 * @brief Rampa de arranque suave: incrementa el límite de potencia en +1% cada 200 ms.
 * Evita choques térmicos y transitorios severos en la red eléctrica.
 */
void ejecutarPasoTermico200ms() {
  if (g_failsafe_latched) return;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    for (int i = 0; i < 4; i++) {
      if (canales[i].activo && canales[i].limitePotencia < 100.0f) {
        canales[i].limitePotencia += 1.0f;
      }
    }
    giveDataMutex();
  }
}

static uint8_t s_uart_seq = 0;

/**
 * @brief S7: Calcula el CRC-8 estándar (polinomio 0x07, init 0x00).
 */
uint8_t calcularCRC8(const uint8_t *data, size_t len) {
  uint8_t crc = 0x00;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t b = 0; b < 8; b++) {
      if (crc & 0x80) {
        crc = (crc << 1) ^ 0x07;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc;
}

/**
 * @brief Envía la orden de reinicio sincronizado "RST*crc\n" hacia el Arduino Nano.
 */
void enviarResetNano() {
  uint8_t crc = calcularCRC8((const uint8_t*)"RST", 3);
  char trama[16];
  snprintf(trama, sizeof(trama), "RST*%02X", crc);
  Serial2.println(trama);
}

/**
 * @brief Ciclo maestro de control térmico a 1 Hz:
 * - Evalúa calcularPI() para los 4 canales.
 * - Aplica el recorte por rampa de potencia.
 * - S7: Construye y transmite la trama serie estructurada UART2 con secuencia y CRC8:
 *       "p0,p1,p2,p3,seq*crc\n" hacia el Arduino Nano esclavo.
 */
void ejecutarPasoTermico1000ms() {
  if (g_failsafe_latched) {
    char carga[32];
    snprintf(carga, sizeof(carga), "0,0,0,0,%u", s_uart_seq++);
    uint8_t crc = calcularCRC8((const uint8_t*)carga, strlen(carga));
    char trama[40];
    snprintf(trama, sizeof(trama), "%s*%02X", carga, crc);
    Serial2.println(trama);
    return;
  }

  int potencias[4] = {0, 0, 0, 0};

  for (int i = 0; i < 4; i++) {
    int u_pi = canales[i].calcularPI();

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      float limLocal = canales[i].limitePotencia;
      int pot = (int)min((float)u_pi, limLocal);
      canales[i].potenciaActual = pot;
      potencias[i] = pot;
      giveDataMutex();
    }
  }

  // S7: Transmisión UART2 al Arduino Nano esclavo: "p0,p1,p2,p3,seq*crc"
  char cargaUtil[32];
  snprintf(cargaUtil, sizeof(cargaUtil), "%d,%d,%d,%d,%u",
           potencias[0], potencias[1], potencias[2], potencias[3], s_uart_seq++);
  uint8_t crc = calcularCRC8((const uint8_t*)cargaUtil, strlen(cargaUtil));
  char tramaCompleta[40];
  snprintf(tramaCompleta, sizeof(tramaCompleta), "%s*%02X", cargaUtil, crc);
  Serial2.println(tramaCompleta);

  // Acumulación de energía térmica disipada en reactores (Wh, Ts = 1.0 s)
  float wTotal = (potencias[0] * 4.5f) + (potencias[1] * 4.5f) + 
                 (potencias[2] * 0.18f) + (potencias[3] * 4.5f);
  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    energiaTermicaTotal_Wh += (wTotal / 3600.0f);
    giveDataMutex();
  }
}


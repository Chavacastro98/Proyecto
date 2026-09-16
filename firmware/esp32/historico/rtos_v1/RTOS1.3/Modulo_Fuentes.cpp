/**
 * =================================================================================
 * MÓDULO DE SALIDA DE CORRIENTE VCSS (Modulo_Fuentes.cpp) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES DEL CONTROLADOR DE POTENCIA:
 * Este módulo implementa el control de un sumidero de corriente lineal gobernado por
 * tensión (VCSS - Voltage-Controlled Current Sink).
 *
 * ESPECIFICACIONES ELÉCTRICAS Y TEORÍA DE DISEÑO:
 * 1. Convertidor DAC MCP4725: Resolución de 12 bits (4096 pasos, 0.806 mV/bit @ 3.3V).
 * 2. Transconductancia ($G_m$):
 *    - Dos ramas idénticas en paralelo para repartición térmica del calor disipado.
 *    - Cada rama consta de un operacional LM358 + MOSFET IRLZ44Z + Resistencia shunt de 1.0 Ohm (1%, 10W cerámica de cemento).
 *    - Transconductancia teórica por rama: $g_{m1} = g_{m2} = \frac{1}{R_{\text{shunt}}} = 1.0\text{ Siemens}$.
 *    - Transconductancia total: $G_m = g_{m1} + g_{m2} = 2.000\text{ Siemens}$.
 * 3. Relación Tensión-Corriente:
 *    - Con $V_{\text{DAC}} = 1.65\text{ V}$, la corriente de salida es: $I = 1.65\text{ V} \times 2.0\text{ S} = 3.30\text{ A}$.
 *    - A fondo de escala ($V_{\text{DAC}} = 3.30\text{ V}$), $I_{\text{max}} = 6.60\text{ A}$.
 * 4. Protocolo ZCS (Zero-Current Switching):
 *    - La apertura y cierre de los contactos mecánicos del relé de +12V (GPIO 20)
 *      se ejecuta estrictamente a corriente cero ($V_{\text{DAC}} = 0\text{ V}$), suprimiendo
 *      la formación de arco voltaico y multiplicando la vida útil del componente.
 * =================================================================================
 */

#include "Modulo_Fuentes.h"
#include "RTOS_Core.h"
#include "config.h"

/** @brief Último código digital de 12 bits enviado al DAC para evitar escrituras redundantes */
static uint16_t ultimoCodigoDAC = 0xFFFF;

/** @brief Bandera que valida la detección física y comunicación I2C con el MCP4725 */
static bool dacInicializado = false;

/**
 * @brief Configura pines de control, realiza sondeo I2C del DAC MCP4725 y restaura calibración.
 */
void inicializarFuente() {
  pinMode(PIN_RELE_VCSS, OUTPUT);
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO); // Estado inicial: Desenergizado (0V)
  estadoReleVDD = false;

  if (takeI2CMutex(pdMS_TO_TICKS(100))) {
    uint8_t dacAddr = 0;
    uint8_t posibles[] = {0x60, 0x61, 0x62, 0x63};
    for (uint8_t i = 0; i < 4; i++) {
      Wire.beginTransmission(posibles[i]);
      if (Wire.endTransmission() == 0) {
        if (Wire.requestFrom((int)posibles[i], 3) == 3) {
          uint8_t b1 = Wire.read();
          Wire.read(); Wire.read();
          if ((b1 & 0x80) != 0 && b1 != 0xFF) {
            dacAddr = posibles[i];
            break;
          }
        }
      }
      delayMicroseconds(200);
    }

    if (dacAddr != 0) {
      dacInicializado = dac.begin(dacAddr);
      if (dacInicializado) {
        dac.setVoltage(0, false);
        ultimoCodigoDAC = 0;
        Serial.printf("[FUENTE] DAC MCP4725 (12-bit) en línea en I2C 0x%02X.\n", dacAddr);
      }
    } else {
      dacInicializado = false;
      Serial.println("[FUENTE] ❌ Error: DAC MCP4725 no detectado en I2C (0x60..0x63).");
    }
    giveI2CMutex();
  }

  // Cargar factor de calibración de transconductancia y estado de compensación desde Flash NVS
  if (memoria.isKey("gvcss")) {
    factorGananciaVCSS = memoria.getFloat("gvcss", 1.000f);
    Serial.printf("[FUENTE] Factor de Ganancia VCSS cargado de NVS: %.4f\n", factorGananciaVCSS);
  } else {
    factorGananciaVCSS = 1.000f;
  }

  if (memoria.isKey("comp_f")) {
    compensacionLazoCerrado = memoria.getBool("comp_f", false);
  } else {
    compensacionLazoCerrado = false;
  }
}

/**
 * @brief Retorna si el DAC MCP4725 está operativo en el bus I2C.
 */
bool isDACInicializado() {
  return dacInicializado;
}

/**
 * @brief Enciende o apaga la etapa de potencia aplicando la secuencia ZCS estricta.
 *
 * SECUENCIA DE ENCENDIDO SEGURO:
 * 1. Fijar DAC a 0V (corriente nula garantizada).
 * 2. Cerrar físicamente los contactos del relé de +12V.
 * 3. Pausa de asentamiento mecánico (80 ms) para disipar el rebote de láminas.
 * 4. Aplicar la consigna analógica deseada en el DAC.
 *
 * SECUENCIA DE APAGADO SEGURO:
 * 1. Bajar DAC a 0V (extinción completa de la corriente de celda).
 * 2. Pausa de descarga capacitiva e inductiva (30 ms).
 * 3. Abrir físicamente el relé de potencia sin presencia de arco eléctrico.
 *
 * @param encender true para energizar la salida; false para aislarla por completo.
 */
// Variables internas del lazo PI de corriente y rampa Soft-Start (RTOS 1.3)
static uint32_t s_tiempoEncendidoFuente = 0;
static float    s_integralPI = 0.0f;

void setEstadoFuente(bool encender) {
  if (g_failsafe_latched && encender) {
    Serial.println("[FUENTE] ❌ Rechazado: Sistema bloqueado por enclavamiento fail-safe.");
    return;
  }

  if (encender) {
    // --- SECUENCIA DE ENCENDIDO SEGURO (ZCS) CON SOFT-START ---
    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(0, false);
      ultimoCodigoDAC = 0;
      giveI2CMutex();
    }

    // Cerrar relé de +12V
    digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      estadoReleVDD = true;
      giveDataMutex();
    }

    // Retardo de asentamiento mecánico de contactos (80 ms)
    vTaskDelay(pdMS_TO_TICKS(80));

    s_tiempoEncendidoFuente = millis();
    s_integralPI = 0.0f; // Reiniciar integrador para evitar cualquier inrush

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      fuenteActiva = true;
      if (modoPulsado) {
        float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
        amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
        estadoPICorriente = PI_STATE_OFF;
      } else {
        amplitudDAC = 0; // Arranca en 0 para que la rampa Soft-Start suba progresivamente
        estadoPICorriente = PI_STATE_RAMP;
      }
      estadoSaludCelda = CELDA_OK;
      giveDataMutex();
    }
  } else {
    // --- SECUENCIA DE APAGADO SEGURO (ZCS) ---
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      fuenteActiva = false;
      amplitudDAC = 0;
      corrienteReal_R1 = 0.0f;
      corrienteReal_R2 = 0.0f;
      corrienteTotalReal = 0.0f;
      voltajeShunt1_raw = 0.0f;
      voltajeShunt2_raw = 0.0f;
      estadoPICorriente = PI_STATE_OFF;
      giveDataMutex();
    }

    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(0, false);
      ultimoCodigoDAC = 0;
      giveI2CMutex();
    }

    // Pausa para disipación de corriente remanente (30 ms)
    vTaskDelay(pdMS_TO_TICKS(30));

    // Abrir contactos del relé mecánico a corriente cero
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      estadoReleVDD = false;
      giveDataMutex();
    }
  }
}

/**
 * @brief Configura la intensidad objetivo para modo continuo (DC).
 * Aplica la calibración de transconductancia para corregir tolerancias en shunts.
 *
 * @param amperios Corriente continua solicitada en Amperios.
 */
void setCorrienteContinua(float amperios) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    modoPulsado = false;
    int dacVal = (int)constrain((amperios / VCSS_IMAX_NOMINAL) * 4095.0f, 0.0f, 4095.0f);
    amplitudDAC_Setpoint = dacVal;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    giveDataMutex();
  }
}

/**
 * @brief Configura los parámetros de la onda pulsada de corriente.
 *
 * @param amperiosPico Amplitud en nivel alto (Amperios).
 * @param hz Frecuencia de repetición de pulsos (Hz).
 * @param duty Porcentaje del periodo en nivel alto (%).
 */
void setConfigPulsado(float amperiosPico, float hz, float duty) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    int dacVal = (int)constrain((amperiosPico / VCSS_IMAX_NOMINAL) * 4095.0f, 0.0f, 4095.0f);
    amplitudDAC_Setpoint = dacVal;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    frecuencia = (hz > 0.0f) ? (int)hz : 1;
    dutyCycle = (int)constrain(duty, 0.0f, 100.0f);
    estadoPICorriente = PI_STATE_OFF; // En pulsado el PI no opera
    giveDataMutex();
  }
}

/**
 * @brief Conmuta el modo de modulación (Pulsado vs Continuo).
 * @param usarPulsado true para onda cuadrada pulsada; false para corriente continua constante.
 */
void conmutarModoFuente(bool usarPulsado) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    modoPulsado = usarPulsado;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    if (usarPulsado) {
      estadoPICorriente = PI_STATE_OFF;
    }
    giveDataMutex();
  }
}

/**
 * @brief Habilita o deshabilita el lazo digital de compensación automática de ganancia.
 * @param habilitar true para activar el ajuste continuo a 2 Hz; false para usar ganancia estática.
 */
void setCompensacionLazoCerrado(bool habilitar) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    compensacionLazoCerrado = habilitar;
    giveDataMutex();
  }
  memoria.putBool("comp_f", habilitar);
}

/**
 * @brief Transmite la consigna de voltaje al MCP4725 aplicando rampa de Soft-Start (Modo DC).
 */
void actualizarFuenteDAC() {
  if (!dacInicializado) return;

  if (g_failsafe_latched) {
    if (ultimoCodigoDAC != 0) {
      if (takeI2CMutex(pdMS_TO_TICKS(20))) {
        dac.setVoltage(0, false);
        ultimoCodigoDAC = 0;
        giveI2CMutex();
      }
    }
    return;
  }

  bool localActiva = false;
  int localAmplitud = 0;

  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    localActiva = fuenteActiva;
    localAmplitud = amplitudDAC;
    giveDataMutex();
  } else {
    return;
  }

  int targetAmplitud = localActiva ? localAmplitud : 0;
  uint16_t codigoDAC = 0;

  if (localActiva) {
    uint32_t tiempoActiva = millis() - s_tiempoEncendidoFuente;
    if (tiempoActiva < VCSS_SOFT_START_MS) {
      // 1. Rampa Soft-Start de 500 ms para eliminar inrush current inductivo
      float factorRampa = (float)tiempoActiva / (float)VCSS_SOFT_START_MS;
      codigoDAC = (uint16_t)constrain((int)roundf(targetAmplitud * factorRampa), 0, targetAmplitud);
      estadoPICorriente = PI_STATE_RAMP;
    } else {
      codigoDAC = (uint16_t)constrain(targetAmplitud, 0, 4095);
      if (tiempoActiva < (VCSS_SOFT_START_MS + VCSS_PI_BLANKING_MS)) {
        estadoPICorriente = PI_STATE_BLANKING; // Asentamiento seguro en lazo abierto
      }
    }
  } else {
    codigoDAC = 0;
    estadoPICorriente = PI_STATE_OFF;
  }

  if (codigoDAC != ultimoCodigoDAC) {
    if (takeI2CMutex(pdMS_TO_TICKS(20))) {
      dac.setVoltage(codigoDAC, false);
      ultimoCodigoDAC = codigoDAC;
      giveI2CMutex();
    }
  }
}

/**
 * @brief Realiza la adquisición analógica de los shunts (canales A2 y A3 del ADS1115).
 * En modo continuo (DC) y tras superar el periodo de Soft-Start y Blanking Time (2s),
 * ejecuta el lazo PI incremental suave con anti-windup para eliminar cualquier error estático.
 */
void actualizarSensadoVCSS() {
  // Snapshot atómico de banderas compartidas bajo xDataMutex
  bool localActiva = false;
  bool localPH = false;
  bool localPulsado = false;
  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    localActiva = fuenteActiva;
    localPH = phModuloActivo;
    localPulsado = modoPulsado;
    giveDataMutex();
  }

  // En standby, enclavamiento fail-safe, calibración de pH o modo pulsado no se adquiere aquí
  if (g_failsafe_latched || !localActiva || localPH || localPulsado) {
    if (localPulsado) estadoPICorriente = PI_STATE_OFF;
    return;
  }

  int16_t raw2 = 0, raw3 = 0;
  bool okADS = false;

  if (takeI2CMutex(pdMS_TO_TICKS(40))) {
    raw2 = ads.readADC_SingleEnded(2);
    raw3 = ads.readADC_SingleEnded(3);
    okADS = true;
    giveI2CMutex();
  }

  if (!okADS) return;

  // Conversión de código ADC a caída de tensión en el shunt (0.1875 mV por bit a Gain 2/3)
  float vs1 = max(0.0f, raw2 * 0.0001875f);
  float vs2 = max(0.0f, raw3 * 0.0001875f);

  // Resistencia shunt nominal = 1.0 Ohm -> I = V / R = V / 1.0
  float i1 = vs1 / 1.0f;
  float i2 = vs2 / 1.0f;
  float i_total = i1 + i2; // Corriente física total entregada a la celda de deposición

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    voltajeShunt1_raw = vs1;
    voltajeShunt2_raw = vs2;
    corrienteReal_R1 = i1;
    corrienteReal_R2 = i2;
    corrienteTotalReal = i_total;

    // Diagnóstico de salud de la celda de electrodeposición
    if (fuenteActiva && i_total > 0.05f) {
      float desbalance = fabsf(i1 - i2);
      float i_esperada = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
      if (i_total < (i_esperada * 0.70f) && amplitudDAC >= 3800) {
        estadoSaludCelda = CELDA_SATURADA; // Voltaje de cumplimiento alcanzado (pasivación de ánodo)
      } else if (desbalance > 0.35f) {
        estadoSaludCelda = CELDA_DESBALANCE; // Desbalance de corriente entre ramas MOSFET
      } else {
        estadoSaludCelda = CELDA_OK;
      }
    } else {
      estadoSaludCelda = CELDA_OK;
    }

    // =========================================================================
    // CONTROLADOR PI SUAVE CON PROTECCIÓN ANTI-INRUSH (RTOS 1.3)
    // =========================================================================
    // Solo en continua (DC), con consigna activa y superado el tiempo de gracia (2.5s)
    if (compensacionLazoCerrado && !modoPulsado && fuenteActiva) {
      uint32_t tiempoActiva = millis() - s_tiempoEncendidoFuente;

      if (tiempoActiva >= (VCSS_SOFT_START_MS + VCSS_PI_BLANKING_MS)) {
        float i_target = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;

        if (i_target >= 0.10f) {
          float error = i_target - i_total;

          // Banda muerta suave de +-10 mA: dentro de ella no se perturba la salida
          if (fabsf(error) < 0.010f) {
            estadoPICorriente = PI_STATE_LOCKED;
          } else {
            estadoPICorriente = PI_STATE_BLANKING;

            // Integrador discreto con Anti-Windup estricto (+-0.15 A)
            s_integralPI += error * 0.5f; // Ts = 0.5s (2 Hz)
            s_integralPI = constrain(s_integralPI, -0.15f, 0.15f);

            float correccionAmps = (VCSS_PI_KP * error) + (VCSS_PI_KI * s_integralPI);
            int deltaDAC = (int)roundf((correccionAmps / VCSS_IMAX_NOMINAL) * 4095.0f);

            // Limitador estricto de pendiente (máximo +-4 LSB por ciclo, ~3.4 mV)
            // Impide cualquier salto o sobreimpulso que pudiera oscilar la celda
            deltaDAC = constrain(deltaDAC, -4, 4);

            amplitudDAC = constrain(amplitudDAC + deltaDAC, 0, 4095);
          }
        }
      }
    } else {
      if (!fuenteActiva || modoPulsado) {
        estadoPICorriente = PI_STATE_OFF;
      }
    }
    giveDataMutex();
  }
}

/**
 * @brief Modela analíticamente el pico de corriente cuando el muestreo I2C no puede
 * completarse dentro del ancho del pulso (frecuencias altas > 30 Hz).
 */
void actualizarTelemetriaPulsada() {
  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    if (!fuenteActiva || !modoPulsado) {
      giveDataMutex();
      return;
    }
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    float iPico = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
    corrienteReal_R1 = iPico / 2.0f;
    corrienteReal_R2 = iPico / 2.0f;
    voltajeShunt1_raw = corrienteReal_R1 * 1.0f; // Caída teórica V = I * R
    voltajeShunt2_raw = corrienteReal_R2 * 1.0f;
    corrienteTotalReal = iPico; // Corriente de cresta para la visualización en la interfaz
    giveDataMutex();
  }
}

/**
 * @brief Rutina de calibración metrológica de transconductancia.
 *
 * PROCEDIMIENTO EXPERIMENTAL:
 * 1. Cierra el relé ZCS de +12V.
 * 2. Inyecta una consigna patrón de 1.50 A (DAC ≈ 931 bits).
 * 3. Permite 600 ms de estabilización térmica y de reactancias.
 * 4. Adquiere 5 muestras secuenciales en los shunts A2/A3 vía ADS1115 y promedia.
 * 5. Si la corriente medida se ubica entre 0.50A y 3.00A, calcula el factor de escala:
 *      nuevoFactor = i_medida / 1.50 A
 * 6. Guarda el nuevo factor en memoria Flash NVS y restaura el estado previo.
 *
 * @return true si la calibración fue exitosa; false ante anomalías de lectura.
 */
bool autoCalibrarVCSS() {
  if (g_failsafe_latched || phModuloActivo) return false;

  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }

  // Interlock estricto: la fuente DEBE estar apagada previamente
  if (activa) {
    Serial.println("[VCSS] ❌ Calibración rechazada: La fuente está encendida. Apague la fuente antes de autocalibrar los shunts.");
    return false;
  }

  Serial.println("[VCSS] Iniciando auto-calibración de transconductancia (RTOS)...");

  // Asegurar relé mecánico cerrado a 0A
  digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
  vTaskDelay(pdMS_TO_TICKS(80));

  // Consigna patrón de prueba: 1.50 A
  uint16_t dacPrueba = (uint16_t)roundf((1.50f / VCSS_IMAX_NOMINAL) * 4095.0f);
  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    dac.setVoltage(dacPrueba, false);
    giveI2CMutex();
  }

  // Tiempo de estabilización en celda
  vTaskDelay(pdMS_TO_TICKS(600));

  float sumI = 0.0f;
  const int MUESTRAS = 5;
  for (int i = 0; i < MUESTRAS; i++) {
    int16_t r2 = 0, r3 = 0;
    if (takeI2CMutex(pdMS_TO_TICKS(40))) {
      r2 = ads.readADC_SingleEnded(2);
      r3 = ads.readADC_SingleEnded(3);
      giveI2CMutex();
    }
    float v1 = max(0.0f, r2 * 0.0001875f);
    float v2 = max(0.0f, r3 * 0.0001875f);
    sumI += (v1 + v2);
    vTaskDelay(pdMS_TO_TICKS(40));
  }

  // Retornar a reposo seguro con protocolo ZCS (DAC = 0V, Relé Abierto)
  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    dac.setVoltage(0, false);
    ultimoCodigoDAC = 0;
    giveI2CMutex();
  }
  vTaskDelay(pdMS_TO_TICKS(30));
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    estadoReleVDD = false;
    giveDataMutex();
  }

  float i_medida_promedio = sumI / (float)MUESTRAS;

  if (i_medida_promedio >= 0.50f && i_medida_promedio <= 3.00f) {
    float nuevoFactor = i_medida_promedio / 1.50f;
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      factorGananciaVCSS = nuevoFactor;
      float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
      amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
      giveDataMutex();
    }
    memoria.putFloat("gvcss", nuevoFactor);
    Serial.printf("[VCSS] Calibración exitosa! Factor Gm=%.4f (Guardado en Flash NVS)\n", nuevoFactor);
    return true;
  } else {
    Serial.printf("[VCSS] ❌ Error de calibración: Corriente fuera de rango (%.3f A)\n", i_medida_promedio);
    return false;
  }
}

/**
 * @brief Restablece el factor de ganancia de transconductancia a su valor de diseño nominal (1.0000x).
 */
void resetCalibracionVCSS() {
  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }
  if (activa) {
    Serial.println("[VCSS] ❌ Restablecimiento rechazado: La fuente está encendida.");
    return;
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    factorGananciaVCSS = 1.000f; // Nominal: Gm = 2.000 S
    amplitudDAC = constrain(amplitudDAC_Setpoint, 0, 4095);
    giveDataMutex();
  }
  memoria.putFloat("gvcss", 1.000f);

  // Actualizar salida analógica DAC inmediatamente
  actualizarFuenteDAC();

  Serial.println("[VCSS] Ganancia restablecida a nominal (Gm = 2.000 S, Factor = 1.0000). NVS actualizada.");
}


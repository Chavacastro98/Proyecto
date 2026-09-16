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
 *    - Cada rama consta de un operacional LM358 + MOSFET IRLZ44Z + Resistencia shunt de 1.0 Ohm (1%, 5W).
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
void setEstadoFuente(bool encender) {
  if (g_failsafe_latched && encender) {
    Serial.println("[FUENTE] ⚠️ No se puede encender la fuente: Sistema en estado FAIL-SAFE.");
    return;
  }

  if (encender) {
    // --- SECUENCIA DE ENCENDIDO SEGURO (ZCS) ---
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

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      fuenteActiva = true;
      amplitudDAC = amplitudDAC_Setpoint;
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
 * @brief Transmite la consigna de voltaje al MCP4725 si hubo modificaciones (Modo DC).
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

  int vOut = localActiva ? localAmplitud : 0;
  uint16_t codigoDAC = (uint16_t)constrain(vOut, 0, 4095);

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
 * Calcula la corriente real en cada rama, la corriente total de celda y ejecuta
 * el ajuste progresivo de ganancia digital si la compensación está activa.
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
  if (g_failsafe_latched || !localActiva || localPH || localPulsado) return;

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

    // Ajuste progresivo de la transconductancia Gm (solo en continua con consigna >= 100 mA)
    if (compensacionLazoCerrado && !modoPulsado && fuenteActiva) {
      float i_target = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
      if (i_target >= 0.10f) {
        float error = i_target - i_total;

        // Margen de histéresis +-20 mA: dentro de esta banda no se perturba la salida
        if (fabsf(error) > 0.020f) {
          float factorActual = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
          float ajuste = 1.0f - (0.05f * (error / i_target)); // Corrección suave al 5% por ciclo (2 Hz)
          float nuevoFactor = constrain(factorActual * ajuste, 0.70f, 1.30f);
          factorGananciaVCSS = nuevoFactor;

          // Recalcular la amplitud del DAC según el nuevo factor de ganancia
          int dacCalibrado = (int)roundf(amplitudDAC_Setpoint / nuevoFactor);
          amplitudDAC = constrain(dacCalibrado, 0, 4095);
        }
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

  Serial.println("[VCSS] Iniciando auto-calibración de transconductancia (RTOS)...");

  bool estabaActiva = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    estabaActiva = fuenteActiva;
    giveDataMutex();
  }

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

  // Restaurar estado previo aplicando protocolo ZCS
  if (estabaActiva) {
    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(amplitudDAC, false);
      giveI2CMutex();
    }
  } else {
    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(0, false);
      giveI2CMutex();
    }
    vTaskDelay(pdMS_TO_TICKS(30));
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      estadoReleVDD = false;
      giveDataMutex();
    }
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


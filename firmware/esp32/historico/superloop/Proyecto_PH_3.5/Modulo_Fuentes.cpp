#include "Modulo_Fuentes.h"
#include "config.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DE LA FUENTE DE CORRIENTE (v3.5) — Modulo_Fuentes.cpp
 * =================================================================================
 * En la versión 3.5, se añade:
 * 1. Control de Relé de Aislamiento Galvánico en la línea VDD (+12V):
 *    - Corta físicamente el positivo de 12V cuando la fuente está apagada,
 *      dejando la celda y electrodos a 0.00V respecto a GND.
 *    - Protocolo Zero-Current Switching (ZCS): Conmutación sin chispa mecánica.
 * 2. Sensado de corriente en tiempo real a través de las 2 resistencias shunt
 *    (canales A2 y A3 del convertidor ADS1115 de 16 bits).
 * 3. Monitoreo de balance y simetría entre ambas ramas del sumidero VCSS.
 * 4. Lazo de compensación digital suave (Outer Loop @ 2 Hz con banda muerta de 30mA).
 * 5. Calibración automática de transconductancia (Gm) guardada en NVS.
 * =================================================================================
 */

// Caché del último valor enviado al DAC (evita escrituras I2C repetidas)
static uint16_t ultimoCodigoDAC = 0xFFFF;

// Indica si el DAC se encontró correctamente al arrancar
static bool dacInicializado = false;

/**
 * Inicializa el DAC MCP4725, el pin del relé de aislamiento y recupera NVS.
 */
void inicializarFuente() {
  // Configuración del pin del relé de +12V
  pinMode(PIN_RELE_VCSS, OUTPUT);
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO); // Iniciar aislado (Relé abierto a 0V)
  estadoReleVDD = false;

  dacInicializado = dac.begin(0x60);
  if (!dacInicializado) {
    Serial.println("[FUENTE] ❌ Error: DAC MCP4725 no detectado en dirección I2C 0x60.");
  } else {
    dac.setVoltage(0, false); // Salida a 0V al encender
    ultimoCodigoDAC = 0;
    Serial.println("[FUENTE] DAC MCP4725 (12-bit) en línea en dirección 0x60.");
  }

  // Cargar factor de calibración de transconductancia y estado de compensación
  if (memoria.isKey("gvcss")) {
    factorGananciaVCSS = memoria.getFloat("gvcss", 1.000f);
    Serial.printf("[FUENTE] Factor de Ganancia VCSS cargado de NVS: %.4f\n", factorGananciaVCSS);
  } else {
    factorGananciaVCSS = 1.000f;
  }

  if (memoria.isKey("comp_f")) {
    compensacionLazoCerrado = memoria.getBool("comp_f", true);
  } else {
    compensacionLazoCerrado = true;
  }
}

/**
 * Control del estado de la fuente con protocolo Zero-Current Switching (ZCS):
 * Evita arcos eléctricos en los contactos del relé y picos destructivos en la celda.
 */
void setEstadoFuente(bool encender) {
  if (encender) {
    // --- SECUENCIA DE ENCENDIDO SEGURO (ZCS) ---
    // 1. Garantizar DAC a 0V antes de cerrar relé
    dac.setVoltage(0, false);
    ultimoCodigoDAC = 0;

    // 2. Cerrar relé de +12V (conmutación en frío a corriente cero)
    digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
    portENTER_CRITICAL(&muxFuente);
    estadoReleVDD = true;
    portEXIT_CRITICAL(&muxFuente);

    // 3. Retardo de asentamiento de contactos mecánicos (80 ms)
    vTaskDelay(pdMS_TO_TICKS(80));

    // 4. Activar fuente con consigna programada
    portENTER_CRITICAL(&muxFuente);
    fuenteActiva = true;
    amplitudDAC = amplitudDAC_Setpoint;
    portEXIT_CRITICAL(&muxFuente);
  } else {
    // --- SECUENCIA DE APAGADO SEGURO (ZCS) ---
    // 1. Cortar corriente instantáneamente en el DAC
    portENTER_CRITICAL(&muxFuente);
    fuenteActiva = false;
    amplitudDAC = 0;
    portEXIT_CRITICAL(&muxFuente);
    dac.setVoltage(0, false);
    ultimoCodigoDAC = 0;

    // 2. Retardo breve para asegurar corriente nula en el circuito (30 ms)
    vTaskDelay(pdMS_TO_TICKS(30));

    // 3. Abrir relé (aislamiento galvánico total de la línea de 12V)
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    portENTER_CRITICAL(&muxFuente);
    estadoReleVDD = false;
    portEXIT_CRITICAL(&muxFuente);
  }
}

/**
 * Convierte Amperios a valor digital del DAC y activa el modo continuo.
 */
void setCorrienteContinua(float amperios) {
  portENTER_CRITICAL(&muxFuente);
  modoPulsado = false;
  int dacVal = (int)constrain((amperios / 6.6f) * 4095.0f, 0.0f, 4095.0f);
  amplitudDAC_Setpoint = dacVal;
  float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
  amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Configura los parámetros de frecuencia y ciclo de trabajo para corriente pulsada.
 */
void setConfigPulsado(float amperiosPico, float hz, float duty) {
  portENTER_CRITICAL(&muxFuente);
  int dacVal = (int)constrain((amperiosPico / 6.6f) * 4095.0f, 0.0f, 4095.0f);
  amplitudDAC_Setpoint = dacVal;
  float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
  amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
  frecuencia = (hz > 0.0f) ? (int)hz : 1;
  dutyCycle = (int)constrain(duty, 0.0f, 100.0f);
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Cambia entre corriente continua y corriente pulsada.
 */
void conmutarModoFuente(bool usarPulsado) {
  portENTER_CRITICAL(&muxFuente);
  modoPulsado = usarPulsado;
  float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
  amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Habilita o deshabilita la compensación en lazo cerrado y persiste en NVS.
 */
void setCompensacionLazoCerrado(bool habilitar) {
  portENTER_CRITICAL(&muxFuente);
  compensacionLazoCerrado = habilitar;
  portEXIT_CRITICAL(&muxFuente);
  memoria.putBool("comp_f", habilitar);
}

/**
 * Genera la señal de salida del DAC en tiempo real (se llama en cada ciclo del loop).
 */
void actualizarFuente() {
  if (!dacInicializado)
    return;

  int vOut = 0;

  portENTER_CRITICAL(&muxFuente);
  bool localActiva = fuenteActiva;
  bool localPulsado = modoPulsado;
  int localAmplitud = amplitudDAC;
  int localFreq = frecuencia;
  int localDuty = dutyCycle;
  portEXIT_CRITICAL(&muxFuente);

  if (localActiva) {
    vOut = localAmplitud;

    if (localPulsado) {
      int freqVal = constrain(localFreq, 1, 100);
      unsigned long periodoMicros = 1000000UL / (unsigned long)freqVal;
      if (periodoMicros == 0) periodoMicros = 1;

      unsigned long tiempoCiclo = micros() % periodoMicros;
      unsigned long tiempoAlto = (periodoMicros * (unsigned long)localDuty) / 100UL;

      vOut = (tiempoCiclo < tiempoAlto) ? localAmplitud : 0;
    }
  }

  uint16_t codigoDAC = (uint16_t)constrain(vOut, 0, 4095);

  if (codigoDAC != ultimoCodigoDAC) {
    dac.setVoltage(codigoDAC, false);
    ultimoCodigoDAC = codigoDAC;
  }
}

/**
 * Sensado de corriente en ambos shunts (Canales A2 y A3 del ADS1115)
 * y compensación digital suave outer loop.
 */
void actualizarSensadoVCSS() {
  // Solo muestrear si la fuente está activa en modo DC y el módulo de pH está apagado
  if (!fuenteActiva || phModuloActivo || modoPulsado) return;

  // Leer canales A2 (Shunt 1) y A3 (Shunt 2) del ADS1115
  int16_t raw2 = ads.readADC_SingleEnded(2);
  int16_t raw3 = ads.readADC_SingleEnded(3);

  float vs1 = max(0.0f, raw2 * 0.0001875f);
  float vs2 = max(0.0f, raw3 * 0.0001875f);

  // R_shunt nominal = 1.0 Ohm -> I = V / 1.0
  float i1 = vs1 / 1.0f;
  float i2 = vs2 / 1.0f;
  float i_total = i1 + i2; // Corriente física real en shunts

  portENTER_CRITICAL(&muxFuente);
  voltajeShunt1_raw = vs1;
  voltajeShunt2_raw = vs2;
  corrienteReal_R1 = i1;
  corrienteReal_R2 = i2;
  corrienteTotalReal = i_total;

  // Ajuste periódico de ganancia de transconductancia (Solo DC continuo con consigna >= 100 mA)
  if (compensacionLazoCerrado && !modoPulsado && fuenteActiva) {
    float i_target = (amplitudDAC_Setpoint / 4095.0f) * 6.6f;

    if (i_target >= 0.10f) {
      float error = i_target - i_total;

      // Margen de tolerancia +-20 mA (+-0.020 A): dentro de rango no se aplica ajuste
      if (fabsf(error) > 0.020f) {
        float factorActual = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
        float ajuste = 1.0f - (0.05f * (error / i_target));
        float nuevoFactor = constrain(factorActual * ajuste, 0.70f, 1.30f);
        factorGananciaVCSS = nuevoFactor;

        int dacCalibrado = (int)roundf(amplitudDAC_Setpoint / nuevoFactor);
        amplitudDAC = constrain(dacCalibrado, 0, 4095);
      }
    }
  }
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Ciclo de auto-calibración de transconductancia VCSS:
 * Aplica una corriente de prueba de 1.50 A, promedia 5 lecturas de corriente real
 * y calcula el factor de corrección de transconductancia exacto para guardarlo en NVS.
 */
bool autoCalibrarVCSS() {
  if (phModuloActivo) return false;

  Serial.println("[VCSS] Iniciando auto-calibración de transconductancia...");

  // Guardar estado original
  portENTER_CRITICAL(&muxFuente);
  bool estabaActiva = fuenteActiva;
  portEXIT_CRITICAL(&muxFuente);

  // Asegurar relé cerrado
  digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
  vTaskDelay(pdMS_TO_TICKS(80));

  // Consigna de prueba: 1.50 A (DAC = 931)
  uint16_t dacPrueba = (uint16_t)roundf((1.50f / 6.6f) * 4095.0f);
  dac.setVoltage(dacPrueba, false);
  vTaskDelay(pdMS_TO_TICKS(600)); // Esperar estabilización térmica y de carga

  float sumI = 0.0f;
  const int MUESTRAS = 5;
  for (int i = 0; i < MUESTRAS; i++) {
    int16_t r2 = ads.readADC_SingleEnded(2);
    int16_t r3 = ads.readADC_SingleEnded(3);
    float v1 = max(0.0f, r2 * 0.0001875f);
    float v2 = max(0.0f, r3 * 0.0001875f);
    sumI += (v1 + v2);
    vTaskDelay(pdMS_TO_TICKS(40));
  }

  // Restaurar salida según estado previo con ZCS
  if (estabaActiva) {
    portENTER_CRITICAL(&muxFuente);
    int targetDac = amplitudDAC;
    portEXIT_CRITICAL(&muxFuente);
    dac.setVoltage(targetDac, false);
  } else {
    dac.setVoltage(0, false);
    vTaskDelay(pdMS_TO_TICKS(30));
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    portENTER_CRITICAL(&muxFuente);
    estadoReleVDD = false;
    portEXIT_CRITICAL(&muxFuente);
  }

  float i_medida_promedio = sumI / (float)MUESTRAS;

  if (i_medida_promedio >= 0.50f && i_medida_promedio <= 3.00f) {
    float nuevoFactor = i_medida_promedio / 1.50f;
    portENTER_CRITICAL(&muxFuente);
    factorGananciaVCSS = nuevoFactor;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    portEXIT_CRITICAL(&muxFuente);

    memoria.putFloat("gvcss", nuevoFactor);
    Serial.printf("[VCSS] Calibración exitosa! I_medida=%.3f A -> Factor Gm=%.4f (Guardado en NVS)\n",
                  i_medida_promedio, nuevoFactor);
    return true;
  } else {
    Serial.printf("[VCSS] ❌ Error de calibración: I_medida fuera de rango (%.3f A)\n", i_medida_promedio);
    return false;
  }
}
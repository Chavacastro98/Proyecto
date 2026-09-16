/**
 * =================================================================================
 * TAREA FREERTOS: SALIDA DE CORRIENTE VCSS (Task_Fuente.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Controla el sumidero de corriente lineal (VCSS - Voltage-Controlled Current Sink)
 * en Core 1 con prioridad 4. Genera formas de onda continua (DC) y pulsada (1..100 Hz).
 *
 * DETALLES DE HARDWARE Y TEORÍA DE CIRCUITOS:
 * - El convertidor MCP4725 entrega una tensión de control analógica (0..3.3V).
 * - Dos amplificadores operacionales LM358 configuran lazos de retroalimentación
 *   negativa cerrados con transistores MOSFET de nivel lógico IRLZ44Z.
 * - Cada rama dispone de una resistencia shunt de precisión de 1.0 Ohm conectada a masa.
 * - Con dos ramas en paralelo, la transconductancia combinada equivalente es:
 *     Gm = 1 / R_shunt1 + 1 / R_shunt2 = 1 / 1.0 + 1 / 1.0 = 2.000 Siemens (A/V).
 * - La corriente entregada es proporcional a la tensión del DAC:
 *     I_total = V_DAC * Gm = V_DAC * 2.000 S.
 *
 * ESTRATEGIA DE CONMUTACIÓN ZCS (ZERO-CURRENT SWITCHING):
 * El relé mecánico de +12V (GPIO 20) jamás interrumpe corriente viva. Antes de abrirlo
 * o cerrarlo, la tarea fuerza V_DAC = 0V (0 Amperios). Esto anula cualquier formación
 * de arco eléctrico ionizante en los contactos, garantizando máxima fiabilidad.
 * =================================================================================
 */

#include "Task_Fuente.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "RTOS_Core.h"

/**
 * @brief Bucle de ejecución de la tarea de salida de corriente (Core 1, Prioridad 4).
 */
void taskFuenteFunc(void *pvParameters) {
  Serial.println("[TASK_FUENTE] Tarea iniciada en Core 1 (Prioridad 4).");

  uint32_t lastHB = millis();
  static uint16_t ultimoCodigoPulsado = 0xFFFF;
  static uint16_t s_contadorPulsos = 0;

  for (;;) {
    // -----------------------------------------------------------------------------
    // PROTECCIÓN DE SEGURIDAD ANTE ENCLAVAMIENTO (FAIL-SAFE LATCH)
    // -----------------------------------------------------------------------------
    if (g_failsafe_latched) {
      if (ultimoCodigoPulsado != 0) {
        if (takeI2CMutex(pdMS_TO_TICKS(20))) {
          if (isDACInicializado()) {
            dac.setVoltage(0, false);
          }
          ultimoCodigoPulsado = 0;
          giveI2CMutex();
        }
      }
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }

    // Snapshot atómico de parámetros bajo cerrojo de datos (xDataMutex)
    bool localActiva = false;
    bool localPulsado = false;
    int localAmplitud = 0;
    int localFreq = 1;
    int localDuty = 50;

    if (takeDataMutex(pdMS_TO_TICKS(10))) {
      localActiva = fuenteActiva;
      localPulsado = modoPulsado;
      localAmplitud = amplitudDAC;
      localFreq = frecuencia;
      localDuty = dutyCycle;
      giveDataMutex();
    }

    // =============================================================================
    // MODULACIÓN EN MODO PULSADO (ONDA CUADRADA 1..100 Hz)
    // =============================================================================
    if (localActiva && localPulsado) {
      int freqVal = constrain(localFreq, 1, 100);
      uint32_t periodo_ms = 1000UL / (uint32_t)freqVal;
      if (periodo_ms == 0) periodo_ms = 1;

      uint32_t tAlto_ms = (periodo_ms * (uint32_t)localDuty) / 100UL;
      if (tAlto_ms == 0) tAlto_ms = 1;
      uint32_t tBajo_ms = (periodo_ms > tAlto_ms) ? (periodo_ms - tAlto_ms) : 1;

      s_contadorPulsos++;

      // 1. Transición al Flanco de Subida y Nivel ALTO (DAC a amplitud consignada)
      if (takeI2CMutex(pdMS_TO_TICKS(10))) {
        if (isDACInicializado()) {
          dac.setVoltage((uint16_t)constrain(localAmplitud, 0, 4095), false);
        }
        ultimoCodigoPulsado = (uint16_t)localAmplitud;
        giveI2CMutex();
      }

      /**
       * =================================================================================
       * MUESTREO ESTROBOSCÓPICO SINCRONIZADO (STROBE / WINDOW SAMPLING)
       * =================================================================================
       * En un proceso electroquímico pulsado (ej. 10 Hz @ 20% Duty Cycle -> tAlto = 20 ms,
       * tBajo = 80 ms), un muestreo analógico asíncrono desde otra tarea caería el 80%
       * del tiempo en el valle de 0A, introduciendo aliasing y lecturas incoherentes.
       *
       * ARQUITECTURA DE LA SOLUCIÓN METROLÓGICA:
       * 1. Sincronización en Fase Alta: La medición analógica se dispara estrictamente
       *    DENTRO del tiempo en nivel ALTO (tAlto) gobernado por esta tarea, garantizando
       *    que el sensor mide exclusivamente el pico real de corriente de celda.
       * 2. Decimación Temporal (1 Muestra por Segundo): Para preservar el determinismo
       *    y no saturar el bus I2C (Wire), no se muestrea en cada pulso; se adquiere
       *    exactamente 1 pulso cada segundo (al cumplirse 'freqVal' pulsos acumulados).
       * 3. Dinámica de Tiempos y Asentamiento:
       *    - Se introduce una pausa de 2 ms para estabilización del lazo analógico
       *      del operacional LM358 y los transistores MOSFET IRLZ44Z.
       *    - La lectura secuencial de los dos shunts (A2 y A3) en el ADC ADS1115 a 860 SPS
       *      toma ~2.4 ms (1.16 ms por canal).
       *    - En total se consumen ~5 ms. Si tAlto >= 5 ms, existe margen suficiente y
       *      se descuentan los 5 ms del retardo en nivel alto restante.
       * 4. CONDICIÓN DE BORDE / FALLBACK ANALÍTICO DE SEGURIDAD:
       *    El ADS1115 tiene un límite físico de 860 SPS. Si la frecuencia supera ~30 Hz
       *    o el duty cycle es tan bajo que tAlto_ms < 5 ms, el tiempo no alcanza para
       *    completar la conversión A/D antes de que caiga el pulso. En ese caso, el sistema
       *    desactiva el muestreo I2C y aplica automáticamente un fallback analítico
       *    (actualizarTelemetriaPulsada()), protegiendo la integridad de la forma de onda.
       * =================================================================================
       */
      bool tocaMedirEsteSegundo = (s_contadorPulsos >= (uint16_t)freqVal);
      bool puedeMuestrearEnAlto = (tAlto_ms >= 5) && isADSConectado();

      if (tocaMedirEsteSegundo) {
        s_contadorPulsos = 0;

        if (puedeMuestrearEnAlto) {
          // Asentamiento de la respuesta analógica LM358 + MOSFET
          vTaskDelay(pdMS_TO_TICKS(2));

          int16_t raw2 = 0, raw3 = 0;
          bool lecturaOK = false;

          // Adquisición analógica de los dos shunts de corriente bajo cerrojo I2C
          if (takeI2CMutex(pdMS_TO_TICKS(10))) {
            raw2 = ads.readADC_SingleEnded(2);
            raw3 = ads.readADC_SingleEnded(3);
            giveI2CMutex();
            lecturaOK = true;
          }

          if (lecturaOK) {
            float vs1 = max(0.0f, raw2 * 0.0001875f);
            float vs2 = max(0.0f, raw3 * 0.0001875f);
            float i1 = vs1 / 1.0f; // Resistencia de shunt = 1.0 Ohm (Ley de Ohm: I = V / R)
            float i2 = vs2 / 1.0f;
            float iTotalPico = i1 + i2;

            if (takeDataMutex(pdMS_TO_TICKS(10))) {
              voltajeShunt1_raw = vs1;
              voltajeShunt2_raw = vs2;
              corrienteReal_R1 = i1;
              corrienteReal_R2 = i2;
              corrienteTotalReal = iTotalPico; // Corriente física real de pico entregada
              giveDataMutex();
            }
          }

          // Descontar los ~5 ms invertidos en la medición del tiempo en alto total
          uint32_t tRestanteAlto = (tAlto_ms > 5) ? (tAlto_ms - 5) : 0;
          if (tRestanteAlto > 0) {
            vTaskDelay(pdMS_TO_TICKS(tRestanteAlto));
          }
        } else {
          // Fallback analítico si tAlto < 5 ms (frecuencias elevadas > 30 Hz)
          actualizarTelemetriaPulsada();
          vTaskDelay(pdMS_TO_TICKS(tAlto_ms));
        }
      } else {
        vTaskDelay(pdMS_TO_TICKS(tAlto_ms));
      }

      // 2. Transición al Flanco de Bajada y Nivel BAJO (DAC a 0V)
      if (takeI2CMutex(pdMS_TO_TICKS(10))) {
        if (isDACInicializado()) {
          dac.setVoltage(0, false);
        }
        ultimoCodigoPulsado = 0;
        giveI2CMutex();
      }
      vTaskDelay(pdMS_TO_TICKS(tBajo_ms));

    } else {
      // =============================================================================
      // MODO CONTINUO (DC) O STANDBY
      // =============================================================================
      s_contadorPulsos = 0;
      actualizarFuenteDAC();
      vTaskDelay(pdMS_TO_TICKS(50));
    }

    // Alimentación del Watchdog por Software cada ~1000 ms
    if (millis() - lastHB >= 1000) {
      lastHB = millis();
      feedHeartbeat(HB_ID_FUENTE);
    }
  }
}

/**
 * @brief Crea la tarea de la fuente en FreeRTOS ligada a Core 1 con prioridad 4 y stack de 3584 bytes.
 */
void iniciarTaskFuente() {
  xTaskCreatePinnedToCore(
      taskFuenteFunc,
      "Task_Fuente",
      STACK_TASK_FUENTE,
      NULL,
      PRIO_TASK_FUENTE,
      &hTaskFuente,
      CORE_REALTIME
  );
}


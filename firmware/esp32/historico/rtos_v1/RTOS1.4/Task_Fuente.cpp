/**
 * =================================================================================
 * TAREA FREERTOS: SALIDA DE CORRIENTE VCSS (Task_Fuente.cpp) — RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA SINGLE-WRITER (PROPIETARIO EXCLUSIVO):
 * Task_Fuente ejecuta en Core 1 con prioridad 4 y es el ÚNICO hilo del sistema que
 * interactúa con el DAC MCP4725 y los shunts de corriente durante la operación:
 * 1. Modo Continuo (DC): invoca ejecutarCicloFuenteDC() a 10 Hz (cada 100 ms).
 * 2. Modo Pulsado: invoca ejecutarCicloFuentePulsada() con temporización precisa (1..100 Hz).
 * 3. Modo Standby / Failsafe: garantiza tensión cero (0V / 0A) sin sobrecarga de bus.
 * =================================================================================
 */

#include "Task_Fuente.h"
#include "Modulo_Fuentes.h"
#include "Modulo_Fuente_DC.h"
#include "Modulo_Fuente_Pulsado.h"
#include "RTOS_Core.h"

/**
 * @brief Bucle de ejecución de la tarea de salida de corriente (Core 1, Prioridad 4).
 */
void taskFuenteFunc(void *pvParameters) {
  Serial.println("[TASK_FUENTE] Tarea iniciada en Core 1 (Prioridad 4) — RTOS 1.4.");

  uint32_t lastHB = millis();

  for (;;) {
    // -----------------------------------------------------------------------------
    // PROTECCIÓN DE SEGURIDAD ANTE ENCLAVAMIENTO (FAIL-SAFE LATCH)
    // -----------------------------------------------------------------------------
    if (g_failsafe_latched) {
      if (takeI2CMutex(pdMS_TO_TICKS(20))) {
        if (isDACInicializado()) {
          dac.setVoltage(0, false);
        }
        giveI2CMutex();
      }
      vTaskDelay(pdMS_TO_TICKS(100));
      continue;
    }

    // Snapshot atómico de estado de fuente bajo cerrojo de datos (xDataMutex)
    bool localActiva = false;
    bool localPulsado = false;

    if (takeDataMutex(pdMS_TO_TICKS(10))) {
      localActiva = fuenteActiva;
      localPulsado = modoPulsado;
      giveDataMutex();
    }

    if (localActiva) {
      if (localPulsado) {
        // =========================================================================
        // EJECUCIÓN MODO PULSADO (1..100 Hz + MUESTREO ETS ESTROBOSCÓPICO)
        // =========================================================================
        ejecutarCicloFuentePulsada();
      } else {
        // =========================================================================
        // EJECUCIÓN MODO CONTINUO (DC: SOFT-START + LAZO PI ADAPTATIVO A 10 Hz)
        // =========================================================================
        ejecutarCicloFuenteDC();
        vTaskDelay(pdMS_TO_TICKS(100)); // Cadencia determinista de 10 Hz (100 ms)
      }
    } else {
      // ===========================================================================
      // MODO STANDBY (FUENTE APAGADA): DAC EN REPOSO A 0V
      // ===========================================================================
      escribirDAC_DC(0);
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
 * @brief Crea la tarea de la fuente en FreeRTOS ligada a Core 1 con prioridad 4.
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

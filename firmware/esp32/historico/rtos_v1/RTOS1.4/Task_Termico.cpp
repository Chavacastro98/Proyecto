/**
 * =================================================================================
 * TAREA FREERTOS: CONTROL TÉRMICO PI (Task_Termico.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Ejecuta en Core 1 con prioridad 5. Emplea la primitiva determinista `vTaskDelayUntil`
 * para garantizar un periodo exacto de 100 ms sin acumulación de deriva temporal (jitter).
 *
 * SUBDIVISIÓN TEMPORAL DE SUB-RUTINAS:
 * - Cada 2 ticks (200 ms): Ejecuta la rampa de arranque suave (ejecutarPasoTermico200ms),
 *   incrementando el límite de potencia en +1% hasta alcanzar el 100%.
 * - Cada 10 ticks (1000 ms): Ejecuta la adquisición de termopares MAX6675 vía SPI,
 *   evalúa el algoritmo de control PI anti-windup, actualiza las potencias requeridas,
 *   transmite la trama serie UART2 hacia el Arduino Nano y alimenta el watchdog de la tarea.
 * =================================================================================
 */

#include "Task_Termico.h"
#include "Modulo_Termico.h"
#include "RTOS_Core.h"

/**
 * @brief Bucle de ejecución del lazo térmico (Core 1, Prioridad 5).
 */
void taskTermicoFunc(void *pvParameters) {
  Serial.println("[TASK_TERMICO] Tarea iniciada en Core 1 (Prioridad 5).");

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = pdMS_TO_TICKS(100); // Base estricta de 100 ms

  uint32_t contadorTicks = 0;

  for (;;) {
    // Garantiza cadencia determinista sin deriva temporal respecto al reloj base
    vTaskDelayUntil(&xLastWakeTime, xFrequency);
    contadorTicks++;

    // 1. Rampa de arranque suave cada 200 ms (2 ticks = 5 Hz)
    if (contadorTicks % 2 == 0) {
      ejecutarPasoTermico200ms();
    }

    // 2. Cálculo PI, transmisión serie y Watchdog cada 1000 ms (10 ticks = 1 Hz)
    if (contadorTicks % 10 == 0) {
      ejecutarPasoTermico1000ms();
      feedHeartbeat(HB_ID_TERMICO);
      contadorTicks = 0; // Reiniciar para evitar desbordamiento aritmético
    }
  }
}

/**
 * @brief Crea la tarea térmica en FreeRTOS ligada a Core 1 con prioridad 5 y stack de 3584 bytes.
 */
void iniciarTaskTermico() {
  xTaskCreatePinnedToCore(
      taskTermicoFunc,
      "Task_Termico",
      STACK_TASK_TERMICO,
      NULL,
      PRIO_TASK_TERMICO,
      &hTaskTermico,
      CORE_REALTIME
  );
}


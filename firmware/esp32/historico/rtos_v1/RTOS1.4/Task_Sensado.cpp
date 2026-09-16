/**
 * =================================================================================
 * TAREA FREERTOS: ADQUISICIÓN ANALÓGICA Y SENSADO I2C (Task_Sensado.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Ejecuta en Core 1 con prioridad 3. Emplea un reloj base de 20 ms (50 Hz) regulado
 * por `vTaskDelayUntil`. Implementa un planificador de sub-frecuencias (multi-rate scheduler)
 * para realizar lecturas analógicas escalonadas sin saturar el bus I2C:
 * - 50 Hz (cada 20 ms): Adquisición de pH (si phModuloActivo = true).
 * - 2 Hz  (cada 500 ms): Medición de corriente DC en shunts VCSS (actualizarSensadoVCSS).
 * - 1 Hz  (cada 1000 ms): Confirmación de actividad Watchdog (feedHeartbeat).
 * - 0.2 Hz (cada 5000 ms): Adquisición de meteorología ambiental (temperatura, humedad, presión).
 * =================================================================================
 */

#include "Task_Sensado.h"
#include "Modulo_PH.h"
#include "Modulo_Fuentes.h"
#include "Modulo_Ambiental.h"
#include "RTOS_Core.h"

/**
 * @brief Bucle de ejecución de la tarea de sensado (Core 1, Prioridad 3).
 */
void taskSensadoFunc(void *pvParameters) {
  Serial.println("[TASK_SENSADO] Tarea iniciada en Core 1 (Prioridad 3).");

  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = pdMS_TO_TICKS(20); // Base determinista de 20 ms (50 Hz)

  uint32_t tickCount = 0;

  for (;;) {
    vTaskDelayUntil(&xLastWakeTime, xFrequency);
    tickCount++;

    // Snapshot atómico de banderas de control compartidas entre núcleos bajo xDataMutex
    bool localPH = false;
    bool localFuente = false;
    bool localPulsado = false;
    if (takeDataMutex(pdMS_TO_TICKS(5))) {
      localPH = phModuloActivo;
      localFuente = fuenteActiva;
      localPulsado = modoPulsado;
      giveDataMutex();
    }

    // 1. Muestreo de sondas de pH cada 20 ms (1 tick = 50 Hz)
    if (localPH) {
      procesarLecturaPH();
    }

    // 2. NOTA ARQUITECTÓNICA (RTOS 1.4):
    // El sensado analógico de los shunts VCSS (A2/A3) y el lazo PI han sido transferidos
    // al 100% a Task_Fuente (Single-Writer Pattern). Task_Sensado queda completamente
    // liberada de la etapa de potencia, suprimiendo cualquier riesgo de colisión I2C.

    // 3. Alimentación del Watchdog por Software cada 1000 ms (50 ticks = 1 Hz)
    if (tickCount % 50 == 0) {
      feedHeartbeat(HB_ID_SENSADO);
    }

    // 4. Adquisición Meteorológica Ambiental cada 5000 ms (250 ticks = 0.2 Hz)
    if (tickCount % 250 == 0) {
      procesarLecturaAmbiental();
      tickCount = 0; // Reiniciar contador para evitar desbordamiento
    }
  }
}

/**
 * @brief Crea la tarea de sensado en FreeRTOS ligada a Core 1 con prioridad 3 y stack de 3584 bytes.
 */
void iniciarTaskSensado() {
  xTaskCreatePinnedToCore(
      taskSensadoFunc,
      "Task_Sensado",
      STACK_TASK_SENSADO,
      NULL,
      PRIO_TASK_SENSADO,
      &hTaskSensado,
      CORE_REALTIME
  );
}


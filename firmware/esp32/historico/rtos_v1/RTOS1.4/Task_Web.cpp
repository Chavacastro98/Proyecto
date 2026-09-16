/**
 * =================================================================================
 * TAREA FREERTOS: SERVIDOR WEB HTTP Y TELEMETRÍA REST (Task_Web.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Ejecuta en Core 0 con prioridad 2. Se encarga de atender a los clientes que se
 * conectan a la red Wi-Fi SoftAP "Uli" mediante su navegador web en http://192.168.4.1
 * o http://interfaz.local.
 *
 * COOPERACIÓN CON EL SUBSISTEMA DE RED (lwIP):
 * Tras despachar los sockets HTTP activos con `server.handleClient()`, la tarea
 * ejecuta un `vTaskDelay(pdMS_TO_TICKS(5))` obligatorio. Este retardo cede el control
 * del procesador a la tarea IDLE0 y a las colas de paquetes de la pila lwIP,
 * impidiendo el desbordamiento del buffer de sockets y reseteando el watchdog del ESP-IDF.
 * =================================================================================
 */

#include "Task_Web.h"
#include "RTOS_Core.h"

/**
 * @brief Bucle de atención de peticiones del servidor web (Core 0, Prioridad 2).
 */
void taskWebFunc(void *pvParameters) {
  Serial.println("[TASK_WEB] Servidor Web HTTP iniciado en Core 0 (Prioridad 2).");

  uint32_t lastHB = millis();

  for (;;) {
    // Despacho de solicitudes HTTP entrantes (HTML, REST JSON, Comandos)
    server.handleClient();

    // Alimentación del Watchdog por Software cada ~1000 ms
    if (millis() - lastHB >= 1000) {
      lastHB = millis();
      feedHeartbeat(HB_ID_WEB);
    }

    // Ceder CPU a la pila lwIP y tarea IDLE de Core 0
    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

/**
 * @brief Crea la tarea del servidor web en FreeRTOS ligada a Core 0 con prioridad 2 y stack de 5120 bytes.
 */
void iniciarTaskWeb() {
  xTaskCreatePinnedToCore(
      taskWebFunc,
      "Task_Web",
      STACK_TASK_WEB,
      NULL,
      PRIO_TASK_WEB,
      &hTaskWeb,
      CORE_COMMS
  );
}


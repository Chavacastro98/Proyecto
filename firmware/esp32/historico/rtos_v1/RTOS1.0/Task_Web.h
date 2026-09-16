#ifndef TASK_WEB_H
#define TASK_WEB_H

/**
 * =================================================================================
 * TAREA FREERTOS: SERVIDOR WEB HTTP Y TELEMETRÍA REST (Task_Web.h)
 * =================================================================================
 * Asignación SMP: Core 0 (CORE_COMMS)
 * Prioridad RTOS: 2 (Baja, cooperativa con la pila TCP/IP de lwIP)
 *
 * RESPONSABILIDADES Y FUNCIONES:
 * 1. Despacho HTTP No Bloqueante:
 *    Invoca periódicamente `server.handleClient()` para procesar solicitudes de páginas
 *    web, endpoints de telemetría unificada (`/data_all`) y comandos de control.
 * 2. Aislamiento Asimétrico Dual-Core:
 *    Al ejecutar en Core 0, absorbe toda la latencia inducida por transferencias TCP/IP,
 *    retransmisiones Wi-Fi y recepción de archivos binarios OTA sin interferir con el
 *    determinismo ni la precisión temporal de las tareas de control en Core 1.
 * 3. Watchdog Heartbeat: Emite confirmación periódica a Task_Supervisor cada 1000 ms.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Crea y lanza la tarea del servidor web fijada a Core 0 con prioridad 2.
 */
void iniciarTaskWeb();

/**
 * @brief Bucle principal de atención de clientes HTTP (ejecuta indefinidamente).
 * @param pvParameters Parámetros pasados a la tarea (NULL).
 */
void taskWebFunc(void *pvParameters);

#endif // TASK_WEB_H


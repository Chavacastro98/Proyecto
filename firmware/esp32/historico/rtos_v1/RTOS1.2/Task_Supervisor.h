#ifndef TASK_SUPERVISOR_H
#define TASK_SUPERVISOR_H

/**
 * =================================================================================
 * TAREA FREERTOS: SUPERVISOR DE SEGURIDAD Y TELEMETRÍA (Task_Supervisor.h)
 * =================================================================================
 * Asignación SMP: Core 1 (CORE_REALTIME)
 * Prioridad RTOS: 6 (Máxima prioridad del sistema de control)
 * Periodo Base: 50 ms (20 Hz)
 *
 * RESPONSABILIDADES Y FUNCIONES:
 * 1. Watchdog por Software (Heartbeat Monitor): Evalúa periódicamente cada 1000 ms
 *    que todas las tareas concurrentes (Térmico, Fuente, Sensado, Web) reporten
 *    actividad. En caso de inanición o bloqueo (> 5000 ms), dispara el Fail-Safe Latch.
 * 2. Baliza Visual RGB (LED Neopixel Integrado): Controla un árbol estricto de 9
 *    niveles de prioridad visual según el estándar internacional ISA-18.2:
 *    - P0: Emergencia Crítica (Estroboscópico Rojo 4 Hz)
 *    - P1: Falla de Sensores o Alarma No Crítica (Rojo Pulsante 1 Hz)
 *    - P2: Actualización de Firmware OTA en Curso (Blanco Rápido 10 Hz)
 *    - P3: Modo Banco de Pruebas USB (Púrpura respiración suave)
 *    - P4: Modo Calibración de pH (Fucsia Neón)
 *    - P5: Proceso de Electrodeposición Activo (Familia de Azules y Cian)
 *    - P6: Advertencia Menor / Modo Degradado (Ámbar)
 *    - P7: Sistema Operativo y Conectado a Web (Verde respiración)
 *    - P8: Sistema en Reposo esperando conexión Wi-Fi (Destello Faro Verde cada 2.5s)
 * 3. Monitoreo de Recursos: Diagnóstico periódico de Uptime, Heap libre y PSRAM.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Crea y lanza la tarea del supervisor fijada a Core 1 con prioridad 6.
 */
void iniciarTaskSupervisor();

/**
 * @brief Bucle principal de la tarea del supervisor (ejecuta indefinidamente).
 * @param pvParameters Parámetros pasados a la tarea (NULL).
 */
void taskSupervisorFunc(void *pvParameters);

/**
 * @brief Retorna la clave de texto del estado actual de la baliza LED para telemetría web.
 */
const char* obtenerEstadoLedActual();

#endif // TASK_SUPERVISOR_H


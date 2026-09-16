#ifndef TASK_TERMICO_H
#define TASK_TERMICO_H

/**
 * =================================================================================
 * TAREA FREERTOS: CONTROL TÉRMICO PI (Task_Termico.h)
 * =================================================================================
 * Asignación SMP: Core 1 (CORE_REALTIME)
 * Prioridad RTOS: 5 (Alta)
 * Periodo Base: 100 ms (sincronizado con vTaskDelayUntil para tiempo real estricto)
 *
 * RESPONSABILIDADES Y FUNCIONES:
 * 1. Rampa de Arranque Suave (Soft-Start Ramp):
 *    Incrementa progresivamente el límite superior de potencia a razón de +1% cada
 *    200 ms (2 ticks de 100 ms), tardando 20 segundos en habilitar el 100% de potencia.
 *    Esto evita choques térmicos en cubas de vidrio de borosilicato y picos de corriente
 *    en la acometida monofásica de 120V AC al conectar resistencias de 450W.
 * 2. Lazos de Control Proporcional-Integral (PI):
 *    Calcula cada 1000 ms (10 ticks) la potencia requerida para cada uno de los 4
 *    reactores con algoritmo anti-windup estricto para evitar saturación del integrador.
 * 3. Puente Serie UART2 con Arduino Nano Esclavo:
 *    Transmite la trama formateada "P0,P1,P2,P3\n" en GPIO 17 (9600 bps). El Arduino
 *    Nano sincroniza el disparo por cruce por cero de los TRIACs de potencia.
 * 4. Watchdog Heartbeat: Emite confirmación periódica a Task_Supervisor cada 1000 ms.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Crea y lanza la tarea de control térmico fijada a Core 1 con prioridad 5.
 */
void iniciarTaskTermico();

/**
 * @brief Bucle principal de control térmico en tiempo real (ejecuta indefinidamente).
 * @param pvParameters Parámetros pasados a la tarea (NULL).
 */
void taskTermicoFunc(void *pvParameters);

#endif // TASK_TERMICO_H


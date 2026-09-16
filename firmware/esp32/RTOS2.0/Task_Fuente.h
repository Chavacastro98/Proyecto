#ifndef TASK_FUENTE_H
#define TASK_FUENTE_H

/**
 * =================================================================================
 * TAREA FREERTOS: SALIDA DE CORRIENTE VCSS (Task_Fuente.h)
 * =================================================================================
 * Asignación SMP: Core 1 (CORE_REALTIME)
 * Prioridad RTOS: 4 (Media-Alta)
 *
 * RESPONSABILIDADES Y FUNCIONES:
 * 1. Modulación de Corriente Continua (DC) y Pulsada (1..100 Hz):
 *    Gobierna el convertidor Digital-Analógico MCP4725 (12-bit I2C) con arbitraje
 *    estricto por xI2CMutex, regulando la tensión de control hacia el operacional
 *    LM358 y los transistores de potencia MOSFET IRLZ44Z.
 * 2. Conmutación Segura en Cruce por Cero de Corriente (Zero-Current Switching, ZCS):
 *    Coordina el cierre y apertura del relé de aislamiento de +12V (GPIO 20)
 *    estrictamente cuando la salida del DAC está fijada en 0V (0 Amperios).
 *    Esta estrategia extingue cualquier arco eléctrico en los contactos mecánicos,
 *    impidiendo la carbonización prematura del relé y preservando su vida útil.
 * 3. Muestreo Estroboscópico Sincronizado (Strobe Sampling):
 *    En modo pulsado, adquiere las corrientes de los shunts A2/A3 únicamente durante
 *    la ventana de nivel ALTO (tAlto) del pulso, evitando el aliasing de valle (0A).
 * 4. Watchdog Heartbeat: Emite confirmación periódica a Task_Supervisor cada 1000 ms.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Crea y lanza la tarea de la fuente fijada a Core 1 con prioridad 4.
 */
void iniciarTaskFuente();

/**
 * @brief Bucle principal de la tarea de la fuente VCSS (ejecuta indefinidamente).
 * @param pvParameters Parámetros pasados a la tarea (NULL).
 */
void taskFuenteFunc(void *pvParameters);

#endif // TASK_FUENTE_H


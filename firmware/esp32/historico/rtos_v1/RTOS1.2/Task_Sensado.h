#ifndef TASK_SENSADO_H
#define TASK_SENSADO_H

/**
 * =================================================================================
 * TAREA FREERTOS: ADQUISICIÓN ANALÓGICA Y SENSADO I2C (Task_Sensado.h)
 * =================================================================================
 * Asignación SMP: Core 1 (CORE_REALTIME)
 * Prioridad RTOS: 3 (Media)
 * Periodo Base: 20 ms (50 Hz, temporizado con vTaskDelayUntil)
 *
 * RESPONSABILIDADES Y FUNCIONES:
 * 1. Muestreo de Sondas de pH Dual (ADS1115 A0/A1 @ 860 SPS):
 *    Cuando el módulo de pH está activo (phModuloActivo = true), ejecuta lecturas
 *    cada 20 ms (1 tick) alternando canales, promediando 10 muestras y aplicando
 *    un filtro no lineal de mediana de 3 puntos junto con suavizado exponencial.
 * 2. Sensado de Corriente de Carga en Shunts VCSS (ADS1115 A2/A3):
 *    En modo continuo (DC), realiza la adquisición periódica cada 500 ms (25 ticks),
 *    computando la corriente total entregada a la celda y aplicando el recorte de
 *    ganancia por lazo cerrado si está habilitado por el operador.
 * 3. Telemetría Ambiental (AHT20 + BMP280):
 *    Adquiere temperatura de laboratorio, humedad relativa y presión barométrica
 *    cada 5000 ms (250 ticks).
 * 4. Watchdog Heartbeat: Emite confirmación periódica a Task_Supervisor cada 1000 ms.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Crea y lanza la tarea de sensado analógico fijada a Core 1 con prioridad 3.
 */
void iniciarTaskSensado();

/**
 * @brief Bucle principal de adquisición analógica (ejecuta indefinidamente).
 * @param pvParameters Parámetros pasados a la tarea (NULL).
 */
void taskSensadoFunc(void *pvParameters);

#endif // TASK_SENSADO_H


#ifndef MODULO_OTA_H
#define MODULO_OTA_H

/**
 * =================================================================================
 * MÓDULO DE ACTUALIZACIÓN INALÁMBRICA OTA (Modulo_OTA.h) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ESPECIFICACIONES DE ACTUALIZACIÓN DE FIRMWARE:
 * Permite la reprogramación completa de la partición de aplicación (app0/app1)
 * a través de la red Wi-Fi sin necesidad de programador USB-JTAG:
 * 1. Protocolo HTTP Multipart Upload con flujo binario transmitido por chunks.
 * 2. Interlock de Seguridad:
 *    Impide estrictamente iniciar o aceptar cualquier actualización si los calentadores
 *    térmicos, la salida de corriente VCSS o el módulo de pH están en operación.
 * 3. Supresión de Falsas Alarmas de Watchdog:
 *    Durante el borrado y escritura de sectores en Flash SPI (que retiene el bus Flash
 *    por decenas de milisegundos), `isOTAEnProgreso()` señala a Task_Supervisor
 *    que suspenda la evaluación de inactividad, evitando disparos involuntarios de Fail-Safe.
 * 4. Secuencia de Reinicio Seguro:
 *    Tras verificar el checksum MD5 del binario flasheado, apaga relés y calentadores
 *    antes de invocar `ESP.restart()`.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra las rutas HTTP `/update` (GET y POST) y `/ota_check` en el servidor web.
 */
void inicializarOTA();

/**
 * @brief Evalúa si existe alguna carga de potencia activa que impida actualizar el firmware.
 * @return true si el interlock está activo (calefacción, fuente o pH encendidos); false si es seguro.
 */
bool otaInterlockActivo();

/**
 * @brief Informa a las tareas supervisoras si se está escribiendo activamente en la memoria Flash.
 * @return true si la transferencia OTA está en curso.
 */
bool isOTAEnProgreso();

#endif // MODULO_OTA_H


#ifndef MODULO_OTA_H
#define MODULO_OTA_H

/**
 * =================================================================================
 * MÓDULO DE ACTUALIZACIÓN OTA (Over-The-Air) — Versión 3.0 (Modulo_OTA.h)
 * =================================================================================
 * Este módulo permite actualizar el firmware del ESP32 de forma inalámbrica,
 * sin necesidad de conectar un cable USB ni desmontar el equipo del laboratorio.
 *
 * FUNCIONAMIENTO:
 * El operador accede a http://192.168.4.1/update desde cualquier navegador,
 * selecciona el archivo .bin del nuevo firmware y lo sube. El ESP32 escribe
 * el binario en la partición OTA de reserva (esquema dual A/B), verifica la
 * integridad del archivo y se reinicia automáticamente con el nuevo firmware.
 *
 * PROTECCIONES DE SEGURIDAD:
 * 1. INTERLOCK DE POTENCIA: No se permite actualizar si el control térmico
 *    o la fuente de corriente están activos. Reiniciar el ESP32 con
 *    resistencias de 450W encendidas sin supervisión es un riesgo inaceptable.
 * 2. INTEGRIDAD: La librería Update.h verifica el checksum del binario.
 *    Si la escritura falla o se interrumpe, el firmware anterior permanece
 *    intacto en la otra partición.
 * 3. NVS INTACTO: La memoria no volátil (calibración de pH, setpoints,
 *    coeficientes) NO se borra durante la actualización OTA.
 *
 * REQUISITO DE COMPILACIÓN:
 * Seleccionar en Arduino IDE:
 *   Tools → Partition Scheme → "Minimal SPIFFS (1.9MB APP with OTA/190KB SPIFFS)"
 * Esto habilita las dos particiones de aplicación necesarias para OTA dual.
 *
 * RUTAS HTTP:
 *   GET  /update   → Página web con formulario de subida y barra de progreso
 *   POST /update   → Recibe el archivo .bin por chunks y lo escribe en flash
 *   GET  /ota_check → JSON con estado del sistema para verificar interlock
 */

#include "config.h"

/** Cadena con la versión del firmware para mostrar en la interfaz web. */
#define FIRMWARE_VERSION "3.5.0-ALPHA"

/**
 * Registra las rutas HTTP del módulo OTA en el servidor web:
 *   GET  /update    → Página HTML con formulario de subida
 *   POST /update    → Handler de recepción del binario
 *   GET  /ota_check → JSON con estado de interlock y versión
 *
 * DEBE llamarse después de inicializarWebServer() en setup().
 */
void inicializarOTA();

/**
 * Verifica si es seguro realizar una actualización OTA.
 * Condiciones de bloqueo (retorna true = BLOQUEADO):
 *   - Algún canal térmico activo (resistencias encendidas)
 *   - Fuente de corriente activa (DAC entregando amperaje)
 *   - Módulo de pH activo (lectura I2C en curso)
 *
 * @return true si hay un interlock activo (NO se debe actualizar)
 */
bool otaInterlockActivo();

#endif // MODULO_OTA_H

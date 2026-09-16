#ifndef CONTROLLER_SYSTEM_H
#define CONTROLLER_SYSTEM_H

/**
 * =================================================================================
 * CONTROLADOR: SISTEMA, AMBIENTE Y SENSORES (Controller_System.h) — Versión 4.0
 * =================================================================================
 * Maneja las rutas HTTP para la navegación principal, telemetría ambiental
 * y diagnóstico en tiempo real de los 8 periféricos conectados (4 I2C + 4 SPI).
 */

#include "config.h"

/** Registra las rutas asociadas al menú principal, ambiente y diagnóstico de sensores. */
void registrarRutasSystem();

#endif // CONTROLLER_SYSTEM_H

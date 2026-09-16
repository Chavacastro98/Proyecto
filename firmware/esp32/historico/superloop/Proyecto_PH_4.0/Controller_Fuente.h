#ifndef CONTROLLER_FUENTE_H
#define CONTROLLER_FUENTE_H

/**
 * =================================================================================
 * CONTROLADOR: FUENTE DE CORRIENTE VCSS (Controller_Fuente.h) — Versión 4.0
 * =================================================================================
 * Maneja las rutas HTTP para el control de corriente continua / pulsada,
 * telemetría de shunts duales (ADS1115 Canales A2/A3), conmutación de lazo cerrado,
 * auto-calibración de transconductancia y encendido seguro con relé ZCS (+12V).
 */

#include "config.h"

/** Registra las rutas asociadas a la fuente de corriente VCSS. */
void registrarRutasFuente();

#endif // CONTROLLER_FUENTE_H

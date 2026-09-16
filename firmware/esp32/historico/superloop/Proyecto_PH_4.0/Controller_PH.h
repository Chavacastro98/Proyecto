#ifndef CONTROLLER_PH_H
#define CONTROLLER_PH_H

/**
 * =================================================================================
 * CONTROLADOR: MÓDULO DE PH DUAL 2.0 (Controller_PH.h) — Versión 4.0
 * =================================================================================
 * Maneja las rutas HTTP para la activación bajo demanda del pH, calibración
 * tri-modo (Teórico, 2 Puntos, 3 Puntos Dual-Slope), telemetría de % Slope,
 * lectura de voltaje crudo para offset de placa e interlocks con potencia.
 */

#include "config.h"

/** Registra las rutas asociadas al módulo de pH. */
void registrarRutasPH();

#endif // CONTROLLER_PH_H

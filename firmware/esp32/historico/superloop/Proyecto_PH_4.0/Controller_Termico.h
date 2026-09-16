#ifndef CONTROLLER_TERMICO_H
#define CONTROLLER_TERMICO_H

/**
 * =================================================================================
 * CONTROLADOR: CONTROL TÉRMICO (Controller_Termico.h) — Versión 4.0
 * =================================================================================
 * Maneja las rutas HTTP para el monitoreo de temperatura de las 4 tinas,
 * ajuste de setpoints y activación/desactivación con interlock condicional.
 */

#include "config.h"

/** Registra las rutas asociadas al módulo térmico. */
void registrarRutasTermico();

#endif // CONTROLLER_TERMICO_H

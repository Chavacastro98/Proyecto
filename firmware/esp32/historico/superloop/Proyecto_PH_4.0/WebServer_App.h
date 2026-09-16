#ifndef WEBSERVER_APP_H
#define WEBSERVER_APP_H

/**
 * =================================================================================
 * SERVIDOR WEB Y API DE CONTROL — Versión 4.0 Modular MVC (WebServer_App.h)
 * =================================================================================
 * Este módulo actúa como el orquestador principal del servidor web HTTP del ESP32.
 * En la versión 4.0, las rutas, vistas y controladores están completamente
 * desacoplados en sus respectivos módulos de dominio:
 *
 * ESTRUCTURA MODULAR MVC:
 * ---------------------------------------------------------------------------------
 * DOMINIO       | CONTROLADOR               | VISTA ASOCIADA
 * ---------------------------------------------------------------------------------
 * Sistema       | Controller_System.h/.cpp  | View_Menu.h, View_Sensores.h
 * Térmico       | Controller_Termico.h/.cpp | View_Termico.h
 * Fuente VCSS   | Controller_Fuente.h/.cpp  | View_Fuente.h
 * Módulo pH     | Controller_PH.h/.cpp      | View_PH.h
 * Actualización | Modulo_OTA.h/.cpp         | (Embebido en Modulo_OTA)
 * ---------------------------------------------------------------------------------
 */

#include "config.h"

/** Configura todas las rutas del servidor web enlazando los controladores e inicia el servicio HTTP. */
void inicializarWebServer();

#endif // WEBSERVER_APP_H

#ifndef WEBSERVER_APP_H
#define WEBSERVER_APP_H

/**
 * =================================================================================
 * SERVIDOR WEB Y API DE CONTROL — Versión 2.0 (WebServer_App.h)
 * =================================================================================
 * Este archivo define las funciones del servidor web integrado en el ESP32.
 * El servidor tiene dos funciones principales:
 *
 * 1. Servir páginas web (HTML) que el operador ve en su navegador para
 * controlar el sistema de electrodeposición desde cualquier dispositivo con
 * Wi-Fi.
 * 2. Responder a peticiones de datos en formato JSON para que las páginas web
 *    puedan actualizarse automáticamente sin recargar (usando
 * JavaScript/Fetch).
 *
 * LISTADO DE RUTAS DISPONIBLES (v2.0):
 * ---------------------------------------------------------------------------------
 * RUTA            | TIPO     | DESCRIPCIÓN
 * ---------------------------------------------------------------------------------
 * "/"             | Página   | Menú principal con datos ambientales
 * "/termico"      | Página   | Control de temperatura de las 4 tinas
 * "/fuente"       | Página   | Control de la fuente de corriente (DC/Pulsada)
 * "/ph"           | Página   | Módulo pH 2.0 (On/Off, calibración, offset)
 * "/data_env"     | JSON     | Temperatura, humedad y presión del ambiente
 * "/get_ph_dual"  | JSON     | pH, estado On/Off, modo, % slope, interlock
 * "/data_ph_raw"  | JSON     | Voltaje crudo de alta resolución (offset placa)
 * "/data_t"       | JSON     | Datos de los 4 canales térmicos
 * "/set_t"        | Comando  | Cambiar temperatura objetivo (?id=0..3&v=temp)
 * "/act_t"        | Comando  | Encender/Apagar control térmico (?run=1/0)
 *                 |          | + Interlock: suspende pH si se enciende
 * "/data_f"       | JSON     | Estado de la fuente de corriente
 * "/set_f"        | Comando  | Modificar parámetro de fuente (?p=a/f/d&v=val)
 * "/modo_f"       | Comando  | Cambiar modo DC/Pulsado (?v=0/1)
 * "/act_f"        | Comando  | Encender/Apagar fuente (?run=1/0)
 *                 |          | + Interlock: suspende pH si se enciende
 * "/act_ph"       | Comando  | Activar/Desactivar módulo pH (?run=1/0)
 *                 |          | Rechaza activación si interlock activo (403)
 * "/set_cal_mode" | Comando  | Seleccionar modo calibración (?id=1/2&m=0..2)
 * "/do_cal_ph"    | Comando  | Calibrar punto pH (?id=1/2&p=4/7/11)
 *                 |          | Retorna JSON con voltaje y pendiente calculada
 * ---------------------------------------------------------------------------------
 */

#include "config.h"

/** Configura todas las rutas del servidor web y lo pone en marcha. */
void inicializarWebServer();

/** Genera la página del Menú Principal ("/") */
void handleMenu();

/** Genera la página de Control Térmico ("/termico") */
void handleTermico();

/** Genera la página de la Fuente de Corriente ("/fuente") */
void handleFuente();

/** Genera la página del Módulo pH 2.0 ("/ph") */
void handlePH();

#endif // WEBSERVER_APP_H

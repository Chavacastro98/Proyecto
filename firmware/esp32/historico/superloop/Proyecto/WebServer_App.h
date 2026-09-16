#ifndef WEBSERVER_APP_H
#define WEBSERVER_APP_H

/**
 * =================================================================================
 * SERVIDOR WEB Y API DE CONTROL (WebServer_App.h)
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
 * LISTADO DE RUTAS DISPONIBLES:
 * ---------------------------------------------------------------------------------
 * RUTA            | TIPO     | DESCRIPCIÓN
 * ---------------------------------------------------------------------------------
 * "/"             | Página   | Menú principal con datos ambientales
 * "/termico"      | Página   | Control de temperatura de las 4 tinas
 * "/fuente"       | Página   | Control de la fuente de corriente (DC/Pulsada)
 * "/ph"           | Página   | Monitoreo y calibración de pH de 2 tinas
 * "/data_env"     | JSON     | Temperatura, humedad y presión del ambiente
 * "/get_ph_dual"  | JSON     | Lecturas actuales de pH (Tina 1 y Tina 2)
 * "/data_t"       | JSON     | Datos de los 4 canales térmicos
 * "/set_t"        | Comando  | Cambiar temperatura objetivo (?id=0..3&v=temp)
 * "/act_t"        | Comando  | Encender/Apagar control térmico (?run=1/0)
 * "/data_f"       | JSON     | Estado de la fuente de corriente
 * "/set_f"        | Comando  | Modificar parámetro de fuente (?p=a/f/d&v=val)
 * "/modo_f"       | Comando  | Cambiar modo DC/Pulsado (?v=0/1)
 * "/act_f"        | Comando  | Encender/Apagar fuente (?run=1/0)
 * "/do_cal_ph"    | Comando  | Calibrar sonda de pH (?id=1/2&p=7/4)
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

/** Genera la página de Monitoreo de pH ("/ph") */
void handlePH();

#endif // WEBSERVER_APP_H
#ifndef RTOS_CORE_H
#define RTOS_CORE_H

/**
 * =================================================================================
 * NÚCLEO DE SINCRONIZACIÓN Y SUPERVISIÓN FREERTOS (RTOS_Core.h) — RTOS 1.0
 * =================================================================================
 * Centraliza las primitivas de sincronización (Mutexes, Semáforos),
 * identificadores de tareas (Task Handles), sistema de Heartbeat y
 * protocolo de seguridad industrial Fail-Safe Latch.
 * =================================================================================
 */

#include "config.h"

/**
 * IDENTIFICADORES DE TAREAS PARA EL SISTEMA DE HEARTBEAT:
 * Cada tarea periódica debe invocar feedHeartbeat(HB_ID_xxx) en cada iteración.
 * El supervisor en Core 1 verifica que ninguna tarea exceda el umbral de inactividad.
 */
#define HB_ID_TERMICO  0  // Tarea de control térmico de reactores
#define HB_ID_FUENTE   1  // Tarea de lazo y conmutación de la fuente VCSS
#define HB_ID_SENSADO  2  // Tarea de adquisición de sensores ambientales e I2C
#define HB_ID_WEB      3  // Tarea servidora HTTP y despachador MVC
#define HB_COUNT       4  // Total de tareas monitoreadas activamente

/**
 * MUTEXES DEL SISTEMA (Primitivas de Exclusión Mutua FreeRTOS):
 * Previenen condiciones de carrera (race conditions) y colisiones en buses compartidos.
 */
extern SemaphoreHandle_t xI2CMutex;   // Mutex de acceso exclusivo al bus I2C (ADS1115, MCP4725, AHT20, BMP280)
extern SemaphoreHandle_t xSPIMutex;   // Mutex de acceso exclusivo a los 4 termopares MAX6675 por SPI
extern SemaphoreHandle_t xDataMutex;  // Mutex de variables globales compartidas de control y estado de planta

/**
 * IDENTIFICADORES DE TAREA (Task Handles de FreeRTOS):
 * Permiten suspender, reanudar o monitorear el consumo de stack de cada tarea.
 */
extern TaskHandle_t hTaskSupervisor;
extern TaskHandle_t hTaskTermico;
extern TaskHandle_t hTaskFuente;
extern TaskHandle_t hTaskSensado;
extern TaskHandle_t hTaskWeb;

/**
 * ESTADO DE SEGURIDAD FAIL-SAFE LATCH:
 * Si ocurre una anomalía crítica (sobrecorriente, sobrecalentamiento, watchdog),
 * el sistema enclava g_failsafe_latched = true, apagando toda la potencia.
 * Requiere intervención manual del operador para rearmar (clearFailSafe()).
 */
extern volatile bool g_failsafe_latched;
extern volatile uint8_t g_failsafe_code;
extern char g_failsafe_reason[64];

/**
 * BUFFER CIRCULAR DE DIAGNÓSTICO EN RAM (RingBuffer):
 * Almacena los últimos 64 eventos del sistema para mostrarlos en la consola web en tiempo real.
 */
#define LOG_LVL_INFO 0
#define LOG_LVL_WARN 1
#define LOG_LVL_ERR  2
#define MAX_LOG_ENTRIES 64

struct LogEntry {
  uint32_t timestampMs;  // Estampa de tiempo relativa al arranque en milisegundos
  uint8_t level;          // Nivel de severidad (INFO, WARN, ERR)
  char tag[12];          // Etiqueta del subsistema emisor (ej. "VCSS", "THRM", "WEB")
  char message[80];      // Mensaje textual descriptivo
};

/**
 * @brief Inicializa los semáforos mutex, resetea temporizadores de heartbeat y limpia el ring buffer.
 */
void rtosInicializarNucleo();

/**
 * @brief Adquiere el mutex del bus I2C con tiempo de espera configurable.
 * @param xTicksToWait Tiempo máximo en ticks FreeRTOS a esperar (por defecto 50 ms).
 * @return true si se obtuvo el control del bus; false si hubo timeout.
 */
bool takeI2CMutex(TickType_t xTicksToWait = pdMS_TO_TICKS(50));

/**
 * @brief Libera el mutex del bus I2C tras finalizar la transacción.
 */
void giveI2CMutex();

/**
 * @brief Adquiere el mutex del bus SPI de termopares MAX6675.
 * @param xTicksToWait Tiempo máximo en ticks FreeRTOS a esperar (por defecto 50 ms).
 * @return true si se obtuvo el bus SPI; false si hubo timeout.
 */
bool takeSPIMutex(TickType_t xTicksToWait = pdMS_TO_TICKS(50));

/**
 * @brief Libera el mutex del bus SPI.
 */
void giveSPIMutex();

/**
 * @brief Adquiere el mutex de protección de memoria para variables globales compartidas.
 * @param xTicksToWait Tiempo máximo en ticks FreeRTOS a esperar (por defecto 50 ms).
 * @return true si se obtuvo el bloqueo; false si hubo timeout.
 */
bool takeDataMutex(TickType_t xTicksToWait = pdMS_TO_TICKS(50));

/**
 * @brief Libera el mutex de datos globales.
 */
void giveDataMutex();

/**
 * @brief Dispara el protocolo de parada de emergencia Fail-Safe con código de error ISA-18.2.
 * @param errCode Código numérico identificador de la falla.
 * @param reason Cadena descriptiva legible del motivo de la parada.
 * @note Desconecta el relé de +12V, fuerza DAC a 0V, apaga calentadores y enclava el sistema.
 */
void triggerFailSafe(uint8_t errCode, const char* reason);

/**
 * @brief Sobrecarga de conveniencia para triggerFailSafe con código ERR_RTOS_HEARTBEAT.
 */
void triggerFailSafe(const char* reason);

/**
 * @brief Desbloquea y restablece el sistema tras una parada Fail-Safe, previa confirmación de operador.
 */
void clearFailSafe();

/**
 * @brief Notifica al supervisor que la tarea indicada está activa y respondiendo.
 * @param taskId Identificador de tarea (HB_ID_TERMICO..HB_ID_WEB).
 */
void feedHeartbeat(uint8_t taskId);

/**
 * @brief Verifica la salud de todas las tareas FreeRTOS registradas en el sistema.
 * @param maxInactivityMs Tiempo máximo sin reporte antes de declarar falla por watchdog (ej. 5000 ms).
 * @return true si todas las tareas reportan en tiempo; false si alguna se congeló.
 */
bool checkHeartbeats(uint32_t maxInactivityMs);

/**
 * @brief Registra un evento en la salida serial USB y en el RingBuffer de memoria RAM.
 * @param level Nivel de severidad (LOG_LVL_INFO, LOG_LVL_WARN, LOG_LVL_ERR).
 * @param tag Nombre del módulo que genera el registro (máx. 11 caracteres).
 * @param fmt Cadena de formato estilo printf y argumentos variables.
 */
void logSistema(uint8_t level, const char* tag, const char* fmt, ...);

/**
 * @brief Vuelca el historial de logs del RingBuffer formateado como un arreglo JSON.
 * @param buffer Puntero al buffer de caracteres destino.
 * @param maxLen Capacidad en bytes del buffer para evitar desbordamientos.
 */
void obtenerLogsJSON(char* buffer, size_t maxLen);

/**
 * @brief Escapa comillas y barras invertidas en cadenas para garantizar validez en payloads JSON.
 */
void escaparJSON(const char* src, char* dst, size_t maxLen);

#endif // RTOS_CORE_H

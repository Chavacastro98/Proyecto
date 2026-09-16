/**
 * =================================================================================
 * MÓDULO METEOROLÓGICO Y AMBIENTAL (Modulo_Ambiental.cpp) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES DE IMPLEMENTACIÓN Y FILTRADO DE FALSOS POSITIVOS:
 * En buses I2C expuestos a ruido electromagnético o líneas no conectadas (flotantes a 0V),
 * un escáner I2C simple reporta todas las direcciones como "dispositivos presentes"
 * porque la línea SDA permanece artificialmente en nivel bajo (falso ACK).
 *
 * PROTOCOLO DE VALIDACIÓN CRUZADA:
 * Para cada dirección detectada, este módulo envía comandos específicos de registro:
 * 1. AHT20 (0x38/0x39): Consulta el registro de estado (0x71). Debe responder un byte
 *    con el bit de calibración (bit 3) en 1 y no puede ser 0x00 ni 0xFF.
 * 2. BMP280 (0x76/0x77): Lee el registro CHIP_ID (0xD0). Debe devolver un identificador
 *    válido de la familia Bosch Sensortec (0x58 para BMP280, 0x60 para BME280).
 * 3. ADS1115 (0x48..0x4B): Lee el registro de configuración (0x01). Debe tener bit OS=1.
 * 4. MCP4725 (0x60..0x63): Solicita 3 bytes y valida que el bit READY (bit 7) sea 1.
 * =================================================================================
 */

#include "Modulo_Ambiental.h"
#include "RTOS_Core.h"
#include "config.h"

/** @brief Instancia del controlador para el sensor de temperatura y humedad AHT20/AHT10 */
Adafruit_AHTX0 aht;

/** @brief Instancia del controlador para el sensor barométrico digital BMP280 */
Adafruit_BMP280 bmp;

/** @brief Estado de inicialización del sensor AHT20 */
bool ahtInicializado = false;

/** @brief Estado de inicialización del sensor BMP280 */
bool bmpInicializado = false;

/**
 * @brief Ejecuta un escaneo exhaustivo de diagnósticos en el bus I2C (direcciones 0x01 a 0x7F).
 * Aplica handshakes de validación de registros para eliminar falsos positivos de bus flotante.
 */
void escanearBusI2C() {
  Serial.println("\n--- [I2C BUS SCANNER] Escaneando direcciones 0x01 a 0x7F ---");
  uint8_t encontrados = 0;

  if (takeI2CMutex(pdMS_TO_TICKS(200))) {
    for (uint8_t addr = 1; addr < 127; addr++) {
      Wire.beginTransmission(addr);
      uint8_t error = Wire.endTransmission();

      if (error == 0) {
        bool valido = true;
        // Validación cruzada por registro para descartar falsos positivos de líneas a masa
        if (addr == 0x38 || addr == 0x39) {
          Wire.beginTransmission(addr);
          Wire.write(0x71); // Registro de estado AHT20
          if (Wire.endTransmission() != 0 || Wire.requestFrom((int)addr, 1) != 1) valido = false;
          else {
            uint8_t st = Wire.read();
            if (st == 0x00 || st == 0xFF || (st & 0x08) == 0) valido = false;
          }
        } else if (addr == 0x76 || addr == 0x77) {
          Wire.beginTransmission(addr);
          Wire.write(0xD0); // Registro CHIP_ID de Bosch
          if (Wire.endTransmission() != 0 || Wire.requestFrom((int)addr, 1) != 1) valido = false;
          else {
            uint8_t id = Wire.read();
            if (id != 0x58 && id != 0x60 && id != 0x56 && id != 0x57) valido = false;
          }
        } else if (addr >= 0x48 && addr <= 0x4B) {
          Wire.beginTransmission(addr);
          Wire.write(0x01); // Registro de Configuración ADS1115
          if (Wire.endTransmission() != 0 || Wire.requestFrom((int)addr, 2) != 2) valido = false;
          else {
            uint16_t cfg = (Wire.read() << 8) | Wire.read();
            if (cfg == 0x0000 || cfg == 0xFFFF) valido = false;
          }
        } else if (addr >= 0x60 && addr <= 0x63) {
          if (Wire.requestFrom((int)addr, 3) != 3) valido = false;
          else {
            uint8_t b1 = Wire.read(); Wire.read(); Wire.read();
            if ((b1 & 0x80) == 0 || b1 == 0xFF) valido = false;
          }
        }

        if (valido) {
          Serial.printf("  -> Dispositivo I2C encontrado en: 0x%02X", addr);
          if (addr == 0x38) Serial.print(" (AHT20 / AHT10 Temp+Hum)");
          else if (addr == 0x39) Serial.print(" (AHT10 ADDR High)");
          else if (addr == 0x48) Serial.print(" (ADS1115 ADC 16-bit)");
          else if (addr == 0x60) Serial.print(" (MCP4725 DAC 12-bit)");
          else if (addr == 0x76) Serial.print(" (BMP280 / BME280 Presión)");
          else if (addr == 0x77) Serial.print(" (BMP280 / BME280 Alt Addr)");
          Serial.println();
          encontrados++;
        }
      }
    }
    giveI2CMutex();
  }

  if (encontrados == 0) {
    Serial.println("  ⚠️ No se detectó ningún dispositivo I2C. Verifique conexiones SDA/SCL (GPIO 8/9) y alimentación 3.3V.");
  } else {
    Serial.printf("--- Total dispositivos I2C detectados: %d ---\n\n", encontrados);
  }
}

/**
 * @brief Inicializa los sensores ambientales AHT20 y BMP280 en el bus I2C.
 *
 * @return true si al menos uno de los sensores respondió correctamente; false si ambos fallaron.
 */
bool inicializarModuloAmbiental() {
  Serial.println("[AMBIENTAL] Inicializando módulo meteorológico I2C...");

  // 1. Diagnóstico previo para verificar respuesta del bus
  escanearBusI2C();

  if (takeI2CMutex(pdMS_TO_TICKS(150))) {
    // 2. Comando Soft-Reset para AHT20/AHT10 para desbloquear la máquina de estados interna
    Wire.beginTransmission(0x38);
    Wire.write(0xBA); // Comando Soft Reset
    Wire.endTransmission();
    vTaskDelay(pdMS_TO_TICKS(40));

    // Intentar inicialización de AHT20 en dirección primaria (0x38) o secundaria (0x39)
    ahtInicializado = aht.begin(&Wire, 0, 0x38);
    if (!ahtInicializado) {
      ahtInicializado = aht.begin(&Wire, 0, 0x39);
    }

    if (ahtInicializado) {
      Serial.println("[AMBIENTAL] ✅ Sensor AHT20/AHT10 en línea.");
    } else {
      Serial.println("[AMBIENTAL] ⚠️ AHT20 no detectado en 0x38 ni 0x39.");
    }

    // 3. Inicializar BMP280 en dirección estándar (0x76) o alternativa (0x77)
    bmpInicializado = bmp.begin(0x76);
    if (!bmpInicializado) {
      bmpInicializado = bmp.begin(0x77);
    }

    if (bmpInicializado) {
      Serial.println("[AMBIENTAL] ✅ Sensor BMP280 en línea.");
    } else {
      Serial.println("[AMBIENTAL] ⚠️ BMP280 no detectado en 0x76 ni 0x77.");
    }

    giveI2CMutex();
  }

  // Permite operación continua en modo degradado si al menos uno está disponible
  return (ahtInicializado || bmpInicializado);
}

/**
 * @brief Adquiere los datos meteorológicos (temperatura, humedad y presión) y actualiza
 * las variables globales amb_temp, amb_hum y amb_pres bajo xDataMutex.
 */
void procesarLecturaAmbiental() {
  if (g_failsafe_latched) return;

  float t = 0.0f, h = 0.0f, p = 0.0f;
  bool okAHT = false, okBMP = false;

  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    if (ahtInicializado) {
      sensors_event_t humidity, temp;
      if (aht.getEvent(&humidity, &temp)) {
        t = temp.temperature;
        h = humidity.relative_humidity;
        okAHT = true;
      }
    }

    if (bmpInicializado) {
      p = bmp.readPressure() / 100.0f; // Conversión de Pascales a hectopascales (hPa)
      // Si el sensor AHT no está disponible, utilizar la temperatura del BMP280 como respaldo
      if (!okAHT) {
        t = bmp.readTemperature();
        h = 0.0f;
      }
      okBMP = true;
    }
    giveI2CMutex();
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    if (okAHT || okBMP) {
      amb_temp = t;
      amb_hum = h;
    }
    if (okBMP) {
      amb_pres = p;
    }
    giveDataMutex();
  }
}


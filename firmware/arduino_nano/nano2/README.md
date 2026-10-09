# Firmware de Potencia AC: Nano2 (Tiempo Proporcional / Burst Firing)

## 📌 Rol en el Sistema
Este es el **firmware activo de producción** para el microcontrolador esclavo **Arduino Nano (ATmega328P @ 16 MHz)** conectado a la **placa de TRIACs de fabricación propia** del laboratorio.

Gobernado por la librería `JELDimmer2`, modula la potencia térmica suministrada a:
- **Tina 1 (Canal 0):** Resistencia de inmersión 450 W — Desengrase Alcalino (85–90 °C)
- **Tina 2 (Canal 1):** Resistencia de inmersión 450 W — Decapado Alcalino (85–90 °C)
- **Tina 3 (Canal 2):** Resistencia de cartucho 18 W — Celda Hull de 267 mL (25 °C / 40 °C)
- **Tina 4 (Canal 3):** Resistencia de inmersión 450 W — Niquelado sobre Zinc (30–35 °C)

---

## ⚡ Principio de Operación: Tiempo Proporcional (Burst Firing)
A diferencia del recorte de ángulo de fase convencional, este módulo utiliza **conmutación a ciclo completo de 60 Hz** en ventanas fijas de **3000 ms**:
- Conmuta los TRIACs únicamente en el **cruce por cero** detectado por el optoacoplador 4N35 en el pin **D3 (INT1)**.
- **Ventaja crítica en planta:** Elimina picos abruptos de dv/dt y di/dt en media onda, suprimiendo las interferencias electromagnéticas (EMI) sobre el electrodo de pH (PH-4502C) y los termopares (MAX6675).

---

## 🔒 Mecanismos de Seguridad
1. **Perro Guardián UART (`TIMEOUT_UART_MS = 4000 ms`):**
   Si el ESP32 deja de enviar la trama serie periódica `p0,p1,p2,p3\n` por más de 4 segundos, todas las salidas de disparo se apagan inmediatamente a nivel bajo (corte seguro).
2. **Apagado inicial:** Todos los canales inician en estado `APC_OFF` al reiniciar el microcontrolador.

---

## 🔌 Asignación de Pines
- **Pin D3 (INT1):** Detección de Cruce por Cero (`ZC_PIN`) con pull-up interno.
- **Pines D7, D8, D9, D10:** Compuertas de disparo de los 4 canales de potencia (`GATE_PINS`).
- **UART (Pin D0 / RX):** Recepción de tramas serie a 9600 bps desde el ESP32-S3 (`PIN_UART2_TX` = GPIO 17).

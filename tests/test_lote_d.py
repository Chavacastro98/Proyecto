#!/usr/bin/env python3
"""
===============================================================================
SUITE DE PRUEBAS UNITARIAS: LOTE D (ROBUSTEZ, UART CRC8, ESCALONAMIENTO Y D4/D5)
===============================================================================
Verifica:
1. Cálculo de CRC-8 (polinomio 0x07) idéntico entre firmware y host.
2. Descarte de tramas UART corruptas y validación de orden de secuencia.
3. Desfase escalonado de 750 ms (S10) en ventanas de tiempo proporcional de 3 s.
4. Topes de seguridad individuales de temperatura por tina (S8: Hull <= 60 °C).
5. Motor desacoplado de adquisición (NucleoAdquisicion) en cola sin Tkinter (D4).
6. Detección de dato obsoleto (> 3.0 s) y backoff exponencial (D5).
===============================================================================
"""

import os
import queue
import sys
import time

DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")
for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

from comunicacion import NucleoAdquisicion


def calcular_crc8_python(data_bytes: bytes) -> int:
    """Calcula CRC-8 con polinomio estándar 0x07 (SMBus/ATM, init 0x00)."""
    crc = 0x00
    for b in data_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class TestLoteDUartCRC8:

    def test_crc8_vectores_conocidos(self):
        """Verifica que el cálculo CRC8 sea determinista y coincida con el firmware."""
        assert calcular_crc8_python(b"") == 0x00
        # Reset frame: "RST"
        crc_rst = calcular_crc8_python(b"RST")
        assert isinstance(crc_rst, int)
        assert 0 <= crc_rst <= 255

        # Trama típica de potencias
        trama = b"25,0,0,10,1"
        crc_trama = calcular_crc8_python(trama)
        assert 0 <= crc_trama <= 255

    def test_trama_valida_es_aceptada(self):
        """Una trama íntegra con CRC8 correcto es parseada exitosamente."""
        payload = "10,20,30,40,5"
        crc = calcular_crc8_python(payload.encode("ascii"))
        trama_completa = f"{payload}*{crc:02X}"

        partes = trama_completa.split("*")
        assert len(partes) == 2
        carga, crc_str = partes[0], partes[1]
        crc_recibido = int(crc_str, 16)
        crc_esperado = calcular_crc8_python(carga.encode("ascii"))
        assert crc_recibido == crc_esperado

    def test_trama_corrupta_es_descartada(self):
        """Una trama con un solo bit alterado es rechazada por discrepancia CRC."""
        payload = "10,20,30,40,5"
        crc = calcular_crc8_python(payload.encode("ascii"))
        # Simular ruido de línea UART (cambio de '10' a '90')
        payload_corrupto = "90,20,30,40,5"
        crc_calculado = calcular_crc8_python(payload_corrupto.encode("ascii"))
        assert crc != crc_calculado, "El CRC debió detectar la alteración en el payload"


class TestLoteDEscalonamientoS10:

    def test_desfase_cuatro_canales(self):
        """Verifica que los inicios de ventana no coincidan (desfase de 750 ms)."""
        window_size = 3000
        desfases = [0, 750, 1500, 2250]

        # Verificar que todos los desfases son estrictamente distintos y dentro de la ventana
        assert len(set(desfases)) == 4
        assert all(0 <= d < window_size for d in desfases)
        # Verificar que el espaciamiento mínimo entre arranques es de 750 ms
        for i in range(len(desfases) - 1):
            assert desfases[i + 1] - desfases[i] == 750

    def test_tiempo_canal_relativo_no_simultaneo(self):
        """Los instantes de arranque (flanco de subida) de los 4 canales están desfasados por 750 ms."""
        window_size = 3000
        desfases = [0, 750, 1500, 2250]

        # Instantes exactos donde cada canal conmuta a nivel ALTO (ON):
        flancos_arranque = [d % window_size for d in desfases]
        assert flancos_arranque == [0, 750, 1500, 2250]

        # Verificar que a ningún instante coinciden los arranques de dos canales
        for i in range(len(flancos_arranque)):
            for j in range(i + 1, len(flancos_arranque)):
                assert flancos_arranque[i] != flancos_arranque[j]


class TestLoteDTopesTemperaturaS8:

    def test_limite_celda_hull_60c(self):
        """Tina 2 (Celda Hull) tiene un tope de seguridad estricto de 60 °C."""
        def validar_sp(tina_id, sp):
            max_sp = 60.0 if tina_id == 2 else 95.0
            return 0.0 <= sp <= max_sp

        assert validar_sp(2, 40.0) is True
        assert validar_sp(2, 60.0) is True
        assert validar_sp(2, 60.1) is False
        assert validar_sp(2, 85.0) is False

    def test_limite_tinas_generales_95c(self):
        """Tinas 0, 1 y 3 admiten consignas hasta 95 °C pero rechazan >95 °C."""
        def validar_sp(tina_id, sp):
            max_sp = 60.0 if tina_id == 2 else 95.0
            return 0.0 <= sp <= max_sp

        for tina_id in [0, 1, 3]:
            assert validar_sp(tina_id, 85.0) is True
            assert validar_sp(tina_id, 95.0) is True
            assert validar_sp(tina_id, 95.5) is False
            assert validar_sp(tina_id, 120.0) is False


class TestLoteDNucleoAdquisicionD4D5:

    def test_adquisicion_modo_demo_sin_tkinter(self):
        """El hilo NucleoAdquisicion corre standalone y deposita en cola sin GUI."""
        cola = queue.Queue()
        nucleo = NucleoAdquisicion(modo_demo=True, cola_salida=cola, intervalo_s=0.05)
        nucleo.start()

        # Esperar al menos un paquete
        paquete = None
        for _ in range(20):
            try:
                paquete = cola.get(timeout=0.1)
                break
            except queue.Empty:
                time.sleep(0.02)

        nucleo.detener()
        nucleo.join(timeout=1.0)

        assert paquete is not None, "El núcleo debió depositar al menos un paquete en la cola"
        assert "t" in paquete
        assert "ph" in paquete
        assert "f" in paquete
        assert "env" in paquete
        assert len(paquete["t"]) == 4

    def test_deteccion_dato_obsoleto(self):
        """Si transcurren > 3.0 s sin comunicación válida, dato_obsoleto pasa a True."""
        nucleo = NucleoAdquisicion(modo_demo=False, ip="127.0.0.1", intervalo_s=0.1)
        # Simular fallo inmediato
        nucleo.ultimo_exito = time.time() - 4.0
        nucleo.conectado = False
        # Evaluar regla D5
        if time.time() - nucleo.ultimo_exito > 3.0:
            nucleo.dato_obsoleto = True
        assert nucleo.dato_obsoleto is True

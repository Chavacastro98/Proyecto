#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
SISTEMA DE ADQUISICIÓN DE DATOS Y TELEMETRÍA (ESP32 Master Node)
===================================================================================
Tesis de Electrodeposición y Galvanoplastia (Zincado / Niquelado)
Autor: 
DESCRIPCIÓN:
Este script se conecta vía Wi-Fi al ESP32 (SSID: 'Uli' en http://192.168.4.1 o
http://interfaz.local) y consulta periódicamente todos los endpoints de telemetría:
  - /data_t       -> Temperaturas y Setpoints de las 4 tinas térmicas
  - /get_ph_dual  -> Lecturas de pH, estado On/Off y % Slope de las 2 tinas
  - /data_f       -> Corriente galvánica (A), modo DC/PWM, amplitud DAC y duty
  - /data_env     -> Variables meteorológicas (Temp, Humedad, Presión)

Los datos se guardan en tiempo real en un archivo CSV formateado con timestamps
precisos y tiempo relativo en segundos para importación directa en MATLAB,
OriginPro, Python (Pandas/Matplotlib) o Microsoft Excel.
===================================================================================
"""

import sys
import time
import os
import csv
import argparse
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ Error: La librería 'requests' no está instalada.")
    print("👉 Instálala ejecutando: pip install requests")
    sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Captura de telemetría en tiempo real para planta piloto de electrodeposición."
    )
    parser.add_argument(
        "--ip",
        type=str,
        default="192.168.4.1",
        help="Dirección IP o dominio del ESP32 (default: 192.168.4.1 o interfaz.local)",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="Intervalo de muestreo en segundos (default: 1.0 s)",
    )
    parser.add_argument(
        "--salida",
        type=str,
        default="",
        help="Nombre personalizado para el archivo CSV (opcional)",
    )
    return parser.parse_args()


try:
    from telemetria.utilidades.calculos import calcular_disparo_triac
except ImportError:
    def calcular_disparo_triac(p_pct, max_watts):
        """Calcula el ángulo de disparo, retardo de fase en microsegundos y potencia activa RMS."""
        p_safe = max(0.0, min(100.0, float(p_pct)))
        if p_safe <= 0.0:
            return 0.0, 180.0, 8333, 0.0
        elif p_safe >= 100.0:
            return 100.0, 0.0, 0, float(max_watts)
        
        import math
        arg = 2.0 * (p_safe / 100.0) - 1.0
        alpha_rad = math.acos(max(-1.0, min(1.0, arg)))
        alpha_deg = round((alpha_rad / math.pi) * 180.0, 1)
        delay_us = int((alpha_rad / math.pi) * 8333.0)
        watts = round(float(max_watts) * (p_safe / 100.0), 1)
        return p_safe, alpha_deg, delay_us, watts



def main():
    args = parse_arguments()
    base_url = f"http://{args.ip}"

    # Generación de nombre de archivo con timestamp ISO
    if args.salida:
        filename = args.salida if args.salida.endswith(".csv") else f"{args.salida}.csv"
    else:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetria_proceso_{timestamp_str}.csv"

    print("=" * 80)
    print("  📊 SISTEMA DE TELEMETRÍA Y ADQUISICIÓN DE DATOS EN TIEMPO REAL (v3.5)")
    print("  Proyecto: Automatización de Planta Piloto de Electrodeposición (ESP32)")
    print("=" * 80)
    print(f"🎯 Conectando a: {base_url}")
    print(f"⏱️  Intervalo de muestreo: {args.intervalo} segundo(s)")
    print(f"📁 Archivo de salida: {filename}")
    print("=" * 80)

    # Crear sesión HTTP persistente (reduce latencia y overhead TCP)
    session = requests.Session()
    session.headers.update({"User-Agent": "CapturaDatosESP32/3.5"})

    # Probar conectividad con el ESP32
    print("\n🔍 Verificando conexión con el ESP32...")
    try:
        r = session.get(f"{base_url}/data_env", timeout=2.5)
        if r.status_code == 200:
            print("✅ Conexión establecida exitosamente con el ESP32.")
        else:
            print(f"⚠️ El ESP32 respondió con código HTTP {r.status_code}.")
    except Exception as e:
        print("\n❌ NO SE PUDO CONECTAR CON EL ESP32.")
        print("👉 Asegúrate de estar conectado a la red Wi-Fi: 'Uli' (Pass: 12345678)")
        print("👉 Verifica que el ESP32 esté encendido y responda en http://192.168.4.1")
        sys.exit(1)

    # Definición de cabeceras de columnas para el CSV (compatibles con MATLAB / Pandas)
    headers = [
        "Timestamp_ISO",
        "Tiempo_Relativo_s",
        # Canal Térmico y TRIAC 1 (Limpieza - 450W)
        "T1_Limpieza_Temp_C", "T1_Limpieza_SP_C", "T1_Limpieza_Activo",
        "T1_TRIAC_Potencia_Pct", "T1_TRIAC_Alpha_Deg", "T1_TRIAC_Delay_us", "T1_TRIAC_Watts_W",
        # Canal Térmico y TRIAC 2 (Decapado - 450W)
        "T2_Decapado_Temp_C", "T2_Decapado_SP_C", "T2_Decapado_Activo",
        "T2_TRIAC_Potencia_Pct", "T2_TRIAC_Alpha_Deg", "T2_TRIAC_Delay_us", "T2_TRIAC_Watts_W",
        # Canal Térmico y TRIAC 3 (Celda Hull - 18W)
        "T3_CeldaHull_Temp_C", "T3_CeldaHull_SP_C", "T3_CeldaHull_Activo",
        "T3_TRIAC_Potencia_Pct", "T3_TRIAC_Alpha_Deg", "T3_TRIAC_Delay_us", "T3_TRIAC_Watts_W",
        # Canal Térmico y TRIAC 4 (Niquelado - 450W)
        "T4_Niquelado_Temp_C", "T4_Niquelado_SP_C", "T4_Niquelado_Activo",
        "T4_TRIAC_Potencia_Pct", "T4_TRIAC_Alpha_Deg", "T4_TRIAC_Delay_us", "T4_TRIAC_Watts_W",
        # Monitoreo de pH Dual (Tina 1: Zincado, Tina 2: Niquelado)
        "pH_Tina1",
        "pH_Tina2",
        "pH_Modulo_Activo",
        "pH_Modo_Cal_T1",
        "pH_Modo_Cal_T2",
        "pH_Slope_Pct_T1",
        "pH_Slope_Pct_T2",
        "pH_Interlock_Activo",
        # Fuente de Corriente Galvánica (DAC MCP4725 + Shunts ADS1115 v3.5)
        "Fuente_Activa",
        "Fuente_Modo_Pulsado",
        "Fuente_Corriente_Consigna_A",
        "Fuente_Corriente_Real_A",
        "Fuente_Corriente_Shunt1_A",
        "Fuente_Corriente_Shunt2_A",
        "Fuente_Voltaje_Shunt1_V",
        "Fuente_Voltaje_Shunt2_V",
        "Fuente_Factor_Gm",
        "Fuente_Compensacion_Activa",
        "Fuente_Rele_VDD",
        "Fuente_Amplitud_DAC",
        "Fuente_Frecuencia_Hz",
        "Fuente_DutyCycle_Pct",
        # Condiciones Meteorológicas Ambientales
        "Ambiente_Temp_C",
        "Ambiente_Humedad_Pct",
        "Ambiente_Presion_hPa",
    ]

    with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        csv_file.flush()

        print("\n🚀 INICIANDO CAPTURA DE DATOS EN TIEMPO REAL (v3.5)")
        print("💡 Presiona Ctrl+C en cualquier momento para detener y finalizar el archivo.\n")
        print(
            f"{'Tiempo':>8} | {'T1 Limp':>8} | {'T2 Decap':>8} | {'T3 Hull':>8} | {'T4 Níquel':>9} | {'pH T1':>6} | {'pH T2':>6} | {'I Real (A)':>10} | {'Ambiente':>10}"
        )
        print("-" * 95)

        t_inicio = time.time()
        muestras_guardadas = 0

        try:
            while True:
                t_iter_start = time.time()
                t_relativo = round(t_iter_start - t_inicio, 3)
                timestamp_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                # 1. RUTA RÁPIDA: Endpoint Unificado (/data_all)
                got_all = False
                t_data = [{"t": 0.0, "sp": 0.0, "p": 0, "run": 0} for _ in range(4)]
                ph_data = {"p1": "0.00", "p2": "0.00", "on": 0, "m1": 0, "m2": 0, "sl1": "100.0", "sl2": "100.0", "c1": 0, "c2": 0, "il": 0}
                f_data = {"act": 0, "modo": 0, "amp": 0, "sp": 0, "freq": 1, "duty": 50, "amps": 0.0, "i_real": 0.0, "i1": 0.0, "i2": 0.0, "vs1": 0.0, "vs2": 0.0, "gm": 1.0, "comp": 0, "rele": 0}
                env_data = {"t": "0.0", "h": "0", "p": "0.0"}

                try:
                    r_all = session.get(f"{base_url}/data_all", timeout=1.0)
                    if r_all.status_code == 200:
                        d_all = r_all.json()
                        t_data = d_all.get("t", t_data)
                        ph_data = d_all.get("ph", ph_data)
                        f_data = d_all.get("f", f_data)
                        env_data = d_all.get("env", env_data)
                        got_all = True
                except Exception:
                    pass

                # 2. FALLBACK RETROCOMPATIBLE (Endpoints individuales)
                if not got_all:
                    try:
                        r_t = session.get(f"{base_url}/data_t", timeout=1.0)
                        if r_t.status_code == 200:
                            t_data = r_t.json()
                    except Exception:
                        pass

                    try:
                        r_ph = session.get(f"{base_url}/get_ph_dual", timeout=1.0)
                        if r_ph.status_code == 200:
                            ph_data = r_ph.json()
                    except Exception:
                        pass

                    try:
                        r_f = session.get(f"{base_url}/data_f", timeout=1.0)
                        if r_f.status_code == 200:
                            f_data = r_f.json()
                    except Exception:
                        pass

                    try:
                        r_env = session.get(f"{base_url}/data_env", timeout=1.0)
                        if r_env.status_code == 200:
                            env_data = r_env.json()
                    except Exception:
                        pass

                i_consigna = float(f_data.get("amps", 0.0))
                i_real = float(f_data.get("i_real", i_consigna))

                # Extraer y calcular variables de TRIACs
                u1 = float(t_data[0].get("p", max(0, (float(t_data[0].get("sp", 0)) - float(t_data[0].get("t", 0))) * 15.0 + 20.0) if t_data[0].get("run") == 1 else 0.0))
                u2 = float(t_data[1].get("p", max(0, (float(t_data[1].get("sp", 0)) - float(t_data[1].get("t", 0))) * 15.0 + 20.0) if t_data[1].get("run") == 1 else 0.0))
                u3 = float(t_data[2].get("p", max(0, (float(t_data[2].get("sp", 0)) - float(t_data[2].get("t", 0))) * 15.0 + 20.0) if t_data[2].get("run") == 1 else 0.0))
                u4 = float(t_data[3].get("p", max(0, (float(t_data[3].get("sp", 0)) - float(t_data[3].get("t", 0))) * 15.0 + 20.0) if t_data[3].get("run") == 1 else 0.0))

                p1_pct, a1_deg, d1_us, w1 = calcular_disparo_triac(u1, 450.0)
                p2_pct, a2_deg, d2_us, w2 = calcular_disparo_triac(u2, 450.0)
                p3_pct, a3_deg, d3_us, w3 = calcular_disparo_triac(u3, 18.0)
                p4_pct, a4_deg, d4_us, w4 = calcular_disparo_triac(u4, 450.0)

                # Construir fila de datos
                row = [
                    timestamp_iso,
                    t_relativo,
                    # T1 y TRIAC 1
                    t_data[0].get("t", 0.0), t_data[0].get("sp", 0.0), t_data[0].get("run", 0),
                    p1_pct, a1_deg, d1_us, w1,
                    # T2 y TRIAC 2
                    t_data[1].get("t", 0.0), t_data[1].get("sp", 0.0), t_data[1].get("run", 0),
                    p2_pct, a2_deg, d2_us, w2,
                    # T3 y TRIAC 3
                    t_data[2].get("t", 0.0), t_data[2].get("sp", 0.0), t_data[2].get("run", 0),
                    p3_pct, a3_deg, d3_us, w3,
                    # T4 y TRIAC 4
                    t_data[3].get("t", 0.0), t_data[3].get("sp", 0.0), t_data[3].get("run", 0),
                    p4_pct, a4_deg, d4_us, w4,
                    # pH
                    ph_data.get("p1", "0.00"),
                    ph_data.get("p2", "0.00"),
                    ph_data.get("on", 0),
                    ph_data.get("m1", 0),
                    ph_data.get("m2", 0),
                    ph_data.get("sl1", "100.0"),
                    ph_data.get("sl2", "100.0"),
                    ph_data.get("il", 0),
                    # Fuente
                    f_data.get("act", 0),
                    f_data.get("modo", 0),
                    i_consigna,
                    i_real,
                    f_data.get("i1", i_real * 0.5),
                    f_data.get("i2", i_real * 0.5),
                    f_data.get("vs1", 0.0),
                    f_data.get("vs2", 0.0),
                    f_data.get("gm", 1.0),
                    f_data.get("comp", 0),
                    f_data.get("rele", 0),
                    f_data.get("amp", 0),
                    f_data.get("freq", 1),
                    f_data.get("duty", 50),
                    # Ambiental
                    env_data.get("t", "0.0"),
                    env_data.get("h", "0"),
                    env_data.get("p", "0.0"),
                ]

                writer.writerow(row)
                csv_file.flush()
                muestras_guardadas += 1

                # Formatear salida en consola
                t1_txt = f"{float(t_data[0].get('t', 0.0)):.1f}°C"
                t2_txt = f"{float(t_data[1].get('t', 0.0)):.1f}°C"
                t3_txt = f"{float(t_data[2].get('t', 0.0)):.1f}°C"
                t4_txt = f"{float(t_data[3].get('t', 0.0)):.1f}°C"
                ph1_txt = str(ph_data.get("p1", "--")) if ph_data.get("on") == 1 else "OFF"
                ph2_txt = str(ph_data.get("p2", "--")) if ph_data.get("on") == 1 else "OFF"
                i_txt = f"{i_real:.2f} A" if f_data.get("act") == 1 else "0.00 A"
                env_txt = f"{env_data.get('t')}°C/{env_data.get('h')}%"

                print(
                    f"{t_relativo:>7.1f}s | {t1_txt:>8} | {t2_txt:>8} | {t3_txt:>8} | {t4_txt:>9} | {ph1_txt:>6} | {ph2_txt:>6} | {i_txt:>10} | {env_txt:>10}"
                )

                # Mantener intervalo constante
                tiempo_transcurrido = time.time() - t_iter_start
                sleep_time = max(0.05, args.intervalo - tiempo_transcurrido)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n" + "=" * 80)
            print("🛑 CAPTURA FINALIZADA POR EL USUARIO")
            print(f"📊 Total de muestras registradas: {muestras_guardadas}")
            print(f"⏱️  Tiempo total registrado: {round(time.time() - t_inicio, 1)} segundos")
            print(f"📁 Archivo CSV guardado en: {os.path.abspath(filename)}")
            print("=" * 80)


if __name__ == "__main__":
    main()

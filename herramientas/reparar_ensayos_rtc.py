#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
RESCATE Y RECONSTRUCCIÓN DE ENSAYOS HISTÓRICOS CON RTC ANIDADO / COMPRIMIDO
===============================================================================
Herramienta para recuperar datos de placas y ensayos donde el RTC del hardware
estuvo anidado al ciclo de adquisición, distorsionando o truncando el eje de tiempo.

Restaura el tiempo verdadero utilizando:
1. Timestamp_ISO (reloj de pared de la PC, independiente del microcontrolador).
2. Cadencia nominal de muestreo analógico (1.0 s/muestra).
3. Recálculo riguroso de culombimetría (Q = integral I dt) y derivadas térmicas (de/dt).
4. Regeneración automática de todo el paquete de gráficas a 300 DPI.
===============================================================================
"""

import os
import sys
import argparse
import shutil
import glob
import pandas as pd
import numpy as np

# Asegurar import de graficar_datos desde telemetria2.0
PROYECTO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TELEMETRIA2_DIR = os.path.join(PROYECTO_ROOT, "software", "telemetria2.0")
if TELEMETRIA2_DIR not in sys.path:
    sys.path.insert(0, TELEMETRIA2_DIR)

try:
    from graficar_datos import generar_todas_las_graficas
except ImportError:
    try:
        from software.telemetria2.graficar_datos import generar_todas_las_graficas
    except ImportError:
        generar_todas_las_graficas = None


def analizar_y_reparar_csv(csv_path, dry_run=False, forzar=False):
    """
    Analiza un archivo telemetria_completa.csv y corrige el eje temporal si presenta
    anomalías por RTC anidado.
    
    Retorna:
        tuple (fue_reparado: bool, razon: str, dur_antigua_min: float, dur_nueva_min: float)
    """
    if not os.path.isfile(csv_path):
        return False, "Archivo no encontrado", 0.0, 0.0

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return False, f"Error leyendo CSV: {e}", 0.0, 0.0

    if len(df) < 5:
        return False, "Dataset vacío o insuficiente (< 5 filas)", 0.0, 0.0

    if "Tiempo_Relativo_s" not in df.columns:
        return False, "Columna Tiempo_Relativo_s ausente", 0.0, 0.0

    t_raw = pd.to_numeric(df["Tiempo_Relativo_s"], errors="coerce").fillna(0.0)
    dur_raw_s = float(t_raw.max() - t_raw.min())
    dur_raw_min = dur_raw_s / 60.0

    # 1. Verificar si hay Timestamp_ISO de la PC
    tiene_iso = False
    dur_iso_s = 0.0
    if "Timestamp_ISO" in df.columns and df["Timestamp_ISO"].notna().any():
        try:
            iso_series = pd.to_datetime(df["Timestamp_ISO"], errors="coerce").ffill()
            dur_iso_s = (iso_series.iloc[-1] - iso_series.iloc[0]).total_seconds()
            tiene_iso = True
        except Exception:
            pass

    # 2. Verificar delta térmico de las tinas
    delta_t = 0.0
    for col in ["T1_Limpieza_Temp_C", "T2_Decapado_Temp_C", "T4_Niquelado_Temp_C"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) > 0:
                delta_t = max(delta_t, float(s.max() - s.min()))

    # Criterio de detección de anomalía RTC:
    # - El tiempo crudo dura menos de 1 minuto pero hay más de 30 filas o delta_t > 10°C
    # - O el Timestamp_ISO indica que el ensayo duró significativamente más que Tiempo_Relativo_s
    es_anomalo = (
        (dur_raw_min < 1.0 and (delta_t > 8.0 or len(df) >= 30)) or
        (tiene_iso and dur_iso_s > 60.0 and dur_raw_s < (dur_iso_s * 0.5))
    )

    if not es_anomalo and not forzar:
        return False, "Tiempo coherente (sin compresión de RTC detectada)", dur_raw_min, dur_raw_min

    # Reconstrucción del tiempo verdadero
    metodo = ""
    if tiene_iso and dur_iso_s > 10.0:
        iso_series = pd.to_datetime(df["Timestamp_ISO"], errors="coerce").ffill()
        t_nuevo_s = (iso_series - iso_series.iloc[0]).dt.total_seconds().values
        metodo = f"Reloj de PC (Timestamp_ISO) -> {dur_iso_s/60.0:.2f} min"
    else:
        # Reconstrucción por cadencia de adquisición nominal (1.0 s por muestra)
        t_nuevo_s = np.arange(len(df)) * 1.0
        metodo = f"Cadencia nominal 1.0 s/fila -> {len(df)/60.0:.2f} min"

    dur_nueva_min = float(t_nuevo_s[-1] - t_nuevo_s[0]) / 60.0

    if dry_run:
        return True, f"[Simulación] Reparable mediante {metodo}", dur_raw_min, dur_nueva_min

    # Crear respaldo del CSV original antes de modificar
    backup_path = csv_path.replace(".csv", "_backup_rtc.csv")
    if not os.path.exists(backup_path):
        shutil.copy2(csv_path, backup_path)

    # Actualizar eje de tiempo
    df["Tiempo_Relativo_s"] = np.round(t_nuevo_s, 2)

    # Si existe columna de corriente, recalcular Carga_Acumulada_Coulombs para consistencia
    col_i = None
    for c in ["Fuente_Corriente_Real_A", "Corriente_A", "Fuente_Corriente_Consigna_A", "Corriente_Real_A"]:
        if c in df.columns and df[c].notna().any():
            col_i = c
            break
    if col_i:
        i_vals = pd.to_numeric(df[col_i], errors="coerce").fillna(0.0).values
        dt_vals = np.diff(t_nuevo_s, prepend=t_nuevo_s[0])
        dt_vals = np.where(dt_vals <= 0, 1.0, dt_vals)
        q_recalc = np.cumsum(i_vals * dt_vals)
        df["Carga_Acumulada_Coulombs"] = np.round(q_recalc, 4)

    # Guardar CSV corregido
    df.to_csv(csv_path, index=False)

    return True, f"Reparado mediante {metodo}", dur_raw_min, dur_nueva_min


def escanear_y_reparar_directorio(dir_experimentos, dry_run=False, regenerar_graficas=True):
    """Escanea recursivamente carpetas de experimentos y repara los CSVs defectuosos."""
    print("=" * 80)
    print(f">> ESCANEANDO ENSAYOS EN: {dir_experimentos}")
    print("=" * 80)

    patron = os.path.join(dir_experimentos, "**", "telemetria_completa.csv")
    archivos = glob.glob(patron, recursive=True)

    if not archivos:
        print(f"No se encontraron archivos telemetria_completa.csv en {dir_experimentos}")
        return

    reparados = 0
    total = len(archivos)

    for csv_file in archivos:
        carpeta_exp = os.path.dirname(csv_file)
        nombre_exp = os.path.basename(carpeta_exp)
        
        fue_rep, razon, d_old, d_new = analizar_y_reparar_csv(csv_file, dry_run=dry_run)
        
        if fue_rep:
            reparados += 1
            print(f"\n[REPARADO] {nombre_exp}")
            print(f"   Razón: {razon}")
            print(f"   Duración corregida: {d_old:.2f} min  --->  {d_new:.2f} min ({d_new*60:.0f} segundos)")
            
            if not dry_run and regenerar_graficas and generar_todas_las_graficas:
                print("   >> Regenerando suite completa de graficas a 300 DPI...")
                try:
                    generar_todas_las_graficas(carpeta_exp)
                    print("   [OK] Graficas regeneradas con exito.")
                except Exception as e:
                    print(f"   [ERROR] Regenerando graficas: {e}")
        else:
            print(f"[OMITIDO] {nombre_exp}: {razon}")

    print("\n" + "=" * 80)
    print(f">> RESUMEN: {reparados} de {total} ensayos reparados.")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Reparador de Ensayos Historicos con RTC Anidado")
    parser.add_argument("--carpeta", type=str, default="", help="Ruta a una carpeta de ensayo especifica o directorio general")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin modificar archivos")
    parser.add_argument("--no-graficas", action="store_true", help="No regenerar graficas png")
    args = parser.parse_args()

    rutas_a_escanear = []
    if args.carpeta:
        rutas_a_escanear.append(os.path.abspath(args.carpeta))
    else:
        # Rutas por defecto del proyecto
        exp1 = os.path.join(PROYECTO_ROOT, "software", "telemetria", "experimentos")
        exp2 = os.path.join(PROYECTO_ROOT, "software", "telemetria2.0", "experimentos")
        if os.path.isdir(exp1):
            rutas_a_escanear.append(exp1)
        if os.path.isdir(exp2):
            rutas_a_escanear.append(exp2)

    for ruta in rutas_a_escanear:
        if os.path.isfile(ruta) and ruta.endswith(".csv"):
            fue_rep, razon, d_old, d_new = analizar_y_reparar_csv(ruta, dry_run=args.dry_run)
            print(f">> Archivo: {ruta} -> {razon} ({d_old:.2f} -> {d_new:.2f} min)")
            if fue_rep and not args.no_graficas and generar_todas_las_graficas:
                generar_todas_las_graficas(os.path.dirname(ruta))
        elif os.path.isdir(ruta):
            escanear_y_reparar_directorio(ruta, dry_run=args.dry_run, regenerar_graficas=not args.no_graficas)


if __name__ == "__main__":
    main()

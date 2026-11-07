#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
GESTOR DE BASE DE DATOS Y SINCRONIZADOR NUBE (gestor_db.py) - RTOS 2.0
=============================================================================
Plataforma: Python 3 / SQLite Local (Offline-First) + Supabase (PostgreSQL Cloud)
Proyecto: E.L.E.C.T.R.O.D.O-32 | Innovafest Guadalajara 2026 & SMEQ 2026
=============================================================================
"""

import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd
import requests

logger = logging.getLogger("SCADA.GestorDB")

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG_NUBE = os.path.join(DIRECTORIO_ACTUAL, "..", "config_nube.json")
RUTA_DB_LOCAL = os.path.join(DIRECTORIO_ACTUAL, "..", "datos", "ensayos_local.db")


def calcular_sha256(ruta_archivo):
    """Calcula el hash SHA-256 de un archivo en bloques de 64 KB (Auditoría D2)."""
    if not os.path.exists(ruta_archivo):
        return None
    sha = hashlib.sha256()
    try:
        with open(ruta_archivo, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()
    except Exception as e:
        logger.error("Error calculando hash SHA-256 de %s: %s", ruta_archivo, e)
        return None


def cargar_config_nube():
    """Carga la configuración de Supabase desde config_nube.json."""
    if not os.path.exists(RUTA_CONFIG_NUBE):
        config_defecto = {
            "supabase_url": "",
            "supabase_key": "",
            "habilitado": False,
            "carpeta_drive_local": ""
        }
        guardar_config_nube(config_defecto)
        return config_defecto
    try:
        with open(RUTA_CONFIG_NUBE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error leyendo config_nube.json: %s", e)
        return {"supabase_url": "", "supabase_key": "", "habilitado": False, "carpeta_drive_local": ""}


def guardar_config_nube(config_dict):
    """Guarda la configuración de Supabase en config_nube.json."""
    try:
        os.makedirs(os.path.dirname(RUTA_CONFIG_NUBE), exist_ok=True)
        with open(RUTA_CONFIG_NUBE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4)
        return True
    except Exception as e:
        logger.error("Error guardando config_nube.json: %s", e)
        return False


class GestorDB:
    def __init__(self, ruta_sqlite=None):
        self.ruta_db = ruta_sqlite or RUTA_DB_LOCAL
        os.makedirs(os.path.dirname(self.ruta_db), exist_ok=True)
        self.inicializar_sqlite()

    def get_connection(self):
        conn = sqlite3.connect(self.ruta_db)
        conn.row_factory = sqlite3.Row
        return conn

    def inicializar_sqlite(self):
        """Crea las tablas en SQLite local si no existen."""
        with self.get_connection() as conn:
            cur = conn.cursor()

            # 1. Tabla Ensayos
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ensayos (
                id TEXT PRIMARY KEY,
                nombre_carpeta TEXT UNIQUE,
                placa_num INTEGER,
                ronda TEXT,
                fecha_hora TEXT,
                duracion_total_s REAL DEFAULT 0.0,
                fuente_datos TEXT DEFAULT 'HARDWARE',
                version_firmware TEXT DEFAULT 'RTOS 2.0',
                peso_inicial_g REAL DEFAULT 0.0,
                peso_final_g REAL DEFAULT 0.0,
                delta_peso_g REAL DEFAULT 0.0,
                area_placa_cm2 REAL DEFAULT 65.0,
                masa_teorica_faraday_mg REAL DEFAULT 0.0,
                rendimiento_faradaico_pct REAL DEFAULT 0.0,
                sha256_telemetria TEXT,
                sha256_metricas TEXT,
                sha256_eventos TEXT,
                sha256_tiempos_muertos TEXT,
                sincronizado_nube INTEGER DEFAULT 0,
                fecha_sincronizacion TEXT,
                observaciones TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 2. Tabla Telemetria 10 Hz
            cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetria_10hz (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ensayo_id TEXT,
                timestamp_iso TEXT,
                tiempo_relativo_s REAL,
                placa_id INTEGER,
                ronda TEXT,
                etapa_num INTEGER,
                etapa_nombre TEXT,
                etapa_tiempo_s REAL,
                etapa_duracion_s REAL,
                corriente_target_a REAL,
                modo_corriente TEXT,
                temp_sp_target_c REAL,
                t1_limpieza_temp_c REAL,
                t1_limpieza_sp_c REAL,
                t1_limpieza_activo INTEGER,
                t1_triac_potencia_pct REAL,
                t1_triac_alpha_deg REAL,
                t1_triac_delay_us INTEGER,
                t1_triac_watts_w REAL,
                t2_decapado_temp_c REAL,
                t2_decapado_sp_c REAL,
                t2_decapado_activo INTEGER,
                t2_triac_potencia_pct REAL,
                t2_triac_alpha_deg REAL,
                t2_triac_delay_us INTEGER,
                t2_triac_watts_w REAL,
                t3_celdahull_temp_c REAL,
                t3_celdahull_sp_c REAL,
                t3_celdahull_activo INTEGER,
                t3_triac_potencia_pct REAL,
                t3_triac_alpha_deg REAL,
                t3_triac_delay_us INTEGER,
                t3_triac_watts_w REAL,
                t4_niquelado_temp_c REAL,
                t4_niquelado_sp_c REAL,
                t4_niquelado_activo INTEGER,
                t4_triac_potencia_pct REAL,
                t4_triac_alpha_deg REAL,
                t4_triac_delay_us INTEGER,
                t4_triac_watts_w REAL,
                ph_tina1 REAL,
                ph_tina2 REAL,
                ph_modulo_activo INTEGER,
                ph_modo_cal_t1 TEXT,
                ph_modo_cal_t2 TEXT,
                ph_slope_pct_t1 REAL,
                ph_slope_pct_t2 REAL,
                ph_interlock_activo INTEGER,
                fuente_activa INTEGER,
                fuente_modo_pulsado INTEGER,
                fuente_corriente_consigna_a REAL,
                fuente_corriente_real_a REAL,
                fuente_corriente_shunt1_a REAL,
                fuente_corriente_shunt2_a REAL,
                fuente_voltaje_shunt1_v REAL,
                fuente_voltaje_shunt2_v REAL,
                fuente_factor_gm REAL,
                fuente_compensacion_activa INTEGER,
                fuente_rele_vdd INTEGER,
                fuente_amplitud_dac INTEGER,
                fuente_frecuencia_hz REAL,
                fuente_dutycycle_pct REAL,
                fuente_pi_estado TEXT,
                fuente_salud_celda TEXT,
                carga_acumulada_coulombs REAL,
                masa_teorica_faraday_mg REAL,
                energia_termica_wh REAL,
                ambiente_temp_c REAL,
                ambiente_humedad_pct REAL,
                ambiente_presion_hpa REAL,
                FOREIGN KEY (ensayo_id) REFERENCES ensayos(id) ON DELETE CASCADE
            )
            """)

            # 3. Tabla Métricas de Control
            cur.execute("""
            CREATE TABLE IF NOT EXISTS metricas_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ensayo_id TEXT,
                timestamp_iso TEXT,
                tiempo_relativo_s REAL,
                etapa_num INTEGER,
                etapa_nombre TEXT,
                error_t1_c REAL,
                error_t2_c REAL,
                error_t3_c REAL,
                error_t4_c REAL,
                error_corriente_a REAL,
                iae_t1 REAL,
                iae_t2 REAL,
                iae_t3 REAL,
                iae_t4 REAL,
                iae_corriente REAL,
                esfuerzo_u1_pct REAL,
                esfuerzo_u2_pct REAL,
                esfuerzo_u3_pct REAL,
                esfuerzo_u4_pct REAL,
                FOREIGN KEY (ensayo_id) REFERENCES ensayos(id) ON DELETE CASCADE
            )
            """)

            # 4. Tabla Eventos y Fallos
            cur.execute("""
            CREATE TABLE IF NOT EXISTS eventos_fallos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ensayo_id TEXT,
                timestamp_iso TEXT,
                tiempo_relativo_s REAL,
                etapa_nombre TEXT,
                tipo_evento TEXT,
                subsistema_sensor TEXT,
                severidad TEXT,
                valor_detectado TEXT,
                descripcion_tecnica TEXT,
                FOREIGN KEY (ensayo_id) REFERENCES ensayos(id) ON DELETE CASCADE
            )
            """)

            # 5. Tabla Tiempos Muertos ISA-88
            cur.execute("""
            CREATE TABLE IF NOT EXISTS tiempos_muertos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ensayo_id TEXT,
                transicion_id TEXT,
                etapa_origen_num INTEGER,
                etapa_origen_nombre TEXT,
                etapa_destino_num INTEGER,
                etapa_destino_nombre TEXT,
                timestamp_inicio TEXT,
                timestamp_fin TEXT,
                tiempo_muerto_s REAL,
                temp_ambiente_c REAL,
                humedad_pct REAL,
                presion_hpa REAL,
                evaporacion_estimada_g_h REAL,
                FOREIGN KEY (ensayo_id) REFERENCES ensayos(id) ON DELETE CASCADE
            )
            """)

            # Índices
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sq_ensayos_placa ON ensayos(placa_num)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sq_tel_ensayo ON telemetria_10hz(ensayo_id)")
            conn.commit()

    def registrar_o_actualizar_ensayo_local(self, ruta_carpeta_ensayo, datos_gravimetria=None):
        """
        Lee los 4 CSVs de una carpeta de ensayo y los vuelca en SQLite local.
        Retorna el ID del ensayo (UUID).
        """
        nombre_carpeta = os.path.basename(os.path.normpath(ruta_carpeta_ensayo))
        csv_tel = os.path.join(ruta_carpeta_ensayo, "telemetria_completa.csv")
        csv_err = os.path.join(ruta_carpeta_ensayo, "metricas_control_errores.csv")
        csv_tm = os.path.join(ruta_carpeta_ensayo, "registro_tiempos_muertos.csv")
        csv_ev = os.path.join(ruta_carpeta_ensayo, "registro_eventos_fallos.csv")

        if not os.path.exists(csv_tel):
            raise FileNotFoundError(f"No se encontró telemetria_completa.csv en {ruta_carpeta_ensayo}")

        # Hashes de integridad
        sha_tel = calcular_sha256(csv_tel)
        sha_err = calcular_sha256(csv_err) if os.path.exists(csv_err) else None
        sha_tm = calcular_sha256(csv_tm) if os.path.exists(csv_tm) else None
        sha_ev = calcular_sha256(csv_ev) if os.path.exists(csv_ev) else None

        df_tel = pd.read_csv(csv_tel)
        duracion = float(df_tel["Tiempo_Relativo_s"].max()) if not df_tel.empty and "Tiempo_Relativo_s" in df_tel else 0.0
        fecha_hora = df_tel["Timestamp_ISO"].iloc[0] if not df_tel.empty and "Timestamp_ISO" in df_tel else datetime.now().isoformat()
        placa_num = int(df_tel["Placa_ID"].iloc[0]) if not df_tel.empty and "Placa_ID" in df_tel else 1
        ronda = str(df_tel["Ronda"].iloc[0]) if not df_tel.empty and "Ronda" in df_tel else "Ronda 1"
        m_teo_max = float(df_tel["Masa_Teorica_Faraday_mg"].max()) if not df_tel.empty and "Masa_Teorica_Faraday_mg" in df_tel else 0.0

        grav = datos_gravimetria or {}
        p_ini = float(grav.get("peso_inicial_g", 0.0))
        p_fin = float(grav.get("peso_final_g", 0.0))
        area = float(grav.get("area_placa_cm2", 65.0))
        delta_p = p_fin - p_ini

        # Rendimiento Faradaico (%) = (delta_p (mg) / m_teo (mg)) * 100
        rendimiento = 0.0
        if m_teo_max > 0 and delta_p > 0:
            rendimiento = round(((delta_p * 1000.0) / m_teo_max) * 100.0, 2)
        elif grav.get("rendimiento_faradaico_pct") is not None:
            rendimiento = float(grav.get("rendimiento_faradaico_pct"))

        obs = grav.get("observaciones", "")

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM ensayos WHERE nombre_carpeta = ?", (nombre_carpeta,))
            row = cur.fetchone()

            if row:
                ensayo_id = row["id"]
                cur.execute("""
                UPDATE ensayos SET
                    peso_inicial_g = ?, peso_final_g = ?, delta_peso_g = ?,
                    area_placa_cm2 = ?, masa_teorica_faraday_mg = ?, rendimiento_faradaico_pct = ?,
                    sha256_telemetria = ?, sha256_metricas = ?, sha256_eventos = ?, sha256_tiempos_muertos = ?,
                    observaciones = ?
                WHERE id = ?
                """, (p_ini, p_fin, delta_p, area, m_teo_max, rendimiento,
                      sha_tel, sha_err, sha_ev, sha_tm, obs, ensayo_id))
            else:
                ensayo_id = str(uuid.uuid4())
                cur.execute("""
                INSERT INTO ensayos (
                    id, nombre_carpeta, placa_num, ronda, fecha_hora, duracion_total_s,
                    peso_inicial_g, peso_final_g, delta_peso_g, area_placa_cm2,
                    masa_teorica_faraday_mg, rendimiento_faradaico_pct,
                    sha256_telemetria, sha256_metricas, sha256_eventos, sha256_tiempos_muertos,
                    sincronizado_nube, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """, (ensayo_id, nombre_carpeta, placa_num, ronda, fecha_hora, duracion,
                      p_ini, p_fin, delta_p, area, m_teo_max, rendimiento,
                      sha_tel, sha_err, sha_ev, sha_tm, obs))

                # Insertar Telemetría 10 Hz
                df_tel.columns = [c.lower() for c in df_tel.columns]
                # Reemplazar NaN por None
                df_tel = df_tel.where(pd.notnull(df_tel), None)
                filas_tel = []
                for _, r in df_tel.iterrows():
                    d = r.to_dict()
                    d["ensayo_id"] = ensayo_id
                    filas_tel.append(d)

                cols_permitidas = [
                    "ensayo_id", "timestamp_iso", "tiempo_relativo_s", "placa_id", "ronda",
                    "etapa_num", "etapa_nombre", "etapa_tiempo_s", "etapa_duracion_s",
                    "corriente_target_a", "modo_corriente", "temp_sp_target_c",
                    "t1_limpieza_temp_c", "t1_limpieza_sp_c", "t1_limpieza_activo",
                    "t1_triac_potencia_pct", "t1_triac_alpha_deg", "t1_triac_delay_us", "t1_triac_watts_w",
                    "t2_decapado_temp_c", "t2_decapado_sp_c", "t2_decapado_activo",
                    "t2_triac_potencia_pct", "t2_triac_alpha_deg", "t2_triac_delay_us", "t2_triac_watts_w",
                    "t3_celdahull_temp_c", "t3_celdahull_sp_c", "t3_celdahull_activo",
                    "t3_triac_potencia_pct", "t3_triac_alpha_deg", "t3_triac_delay_us", "t3_triac_watts_w",
                    "t4_niquelado_temp_c", "t4_niquelado_sp_c", "t4_niquelado_activo",
                    "t4_triac_potencia_pct", "t4_triac_alpha_deg", "t4_triac_delay_us", "t4_triac_watts_w",
                    "ph_tina1", "ph_tina2", "ph_modulo_activo", "ph_modo_cal_t1", "ph_modo_cal_t2",
                    "ph_slope_pct_t1", "ph_slope_pct_t2", "ph_interlock_activo",
                    "fuente_activa", "fuente_modo_pulsado", "fuente_corriente_consigna_a",
                    "fuente_corriente_real_a", "fuente_corriente_shunt1_a", "fuente_corriente_shunt2_a",
                    "fuente_voltaje_shunt1_v", "fuente_voltaje_shunt2_v", "fuente_factor_gm",
                    "fuente_compensacion_activa", "fuente_rele_vdd", "fuente_amplitud_dac",
                    "fuente_frecuencia_hz", "fuente_dutycycle_pct", "fuente_pi_estado", "fuente_salud_celda",
                    "carga_acumulada_coulombs", "masa_teorica_faraday_mg", "energia_termica_wh",
                    "ambiente_temp_c", "ambiente_humedad_pct", "ambiente_presion_hpa"
                ]

                # Inserción por lotes
                placeholders = ", ".join(["?"] * len(cols_permitidas))
                sql_ins = f"INSERT INTO telemetria_10hz ({', '.join(cols_permitidas)}) VALUES ({placeholders})"
                valores_insert = [tuple(f.get(c) for c in cols_permitidas) for f in filas_tel]
                cur.executemany(sql_ins, valores_insert)

                # 3. Métricas
                if os.path.exists(csv_err):
                    df_err = pd.read_csv(csv_err)
                    df_err.columns = [c.lower() for c in df_err.columns]
                    df_err = df_err.where(pd.notnull(df_err), None)
                    cols_err = ["ensayo_id", "timestamp_iso", "tiempo_relativo_s", "etapa_num", "etapa_nombre",
                                "error_t1_c", "error_t2_c", "error_t3_c", "error_t4_c", "error_corriente_a",
                                "iae_t1", "iae_t2", "iae_t3", "iae_t4", "iae_corriente",
                                "esfuerzo_u1_pct", "esfuerzo_u2_pct", "esfuerzo_u3_pct", "esfuerzo_u4_pct"]
                    cols_presentes = [c for c in cols_err if c in df_err.columns or c == "ensayo_id"]
                    placeholders_err = ", ".join(["?"] * len(cols_presentes))
                    sql_err = f"INSERT INTO metricas_control ({', '.join(cols_presentes)}) VALUES ({placeholders_err})"
                    vals_err = []
                    for _, r in df_err.iterrows():
                        d = r.to_dict()
                        d["ensayo_id"] = ensayo_id
                        vals_err.append(tuple(d.get(c) for c in cols_presentes))
                    cur.executemany(sql_err, vals_err)

                # 4. Tiempos Muertos
                if os.path.exists(csv_tm):
                    df_tm = pd.read_csv(csv_tm)
                    df_tm.columns = [c.lower() for c in df_tm.columns]
                    df_tm = df_tm.where(pd.notnull(df_tm), None)
                    cols_tm = ["ensayo_id", "transicion_id", "etapa_origen_num", "etapa_origen_nombre",
                               "etapa_destino_num", "etapa_destino_nombre", "timestamp_inicio", "timestamp_fin",
                               "tiempo_muerto_s", "temp_ambiente_c", "humedad_pct", "presion_hpa", "evaporacion_estimada_g_h"]
                    cols_p_tm = [c for c in cols_tm if c in df_tm.columns or c == "ensayo_id"]
                    placeholders_tm = ", ".join(["?"] * len(cols_p_tm))
                    sql_tm = f"INSERT INTO tiempos_muertos ({', '.join(cols_p_tm)}) VALUES ({placeholders_tm})"
                    vals_tm = []
                    for _, r in df_tm.iterrows():
                        d = r.to_dict()
                        d["ensayo_id"] = ensayo_id
                        vals_tm.append(tuple(d.get(c) for c in cols_p_tm))
                    cur.executemany(sql_tm, vals_tm)

                # 5. Eventos y Fallos
                if os.path.exists(csv_ev):
                    df_ev = pd.read_csv(csv_ev)
                    df_ev.columns = [c.lower() for c in df_ev.columns]
                    df_ev = df_ev.where(pd.notnull(df_ev), None)
                    cols_ev = ["ensayo_id", "timestamp_iso", "tiempo_relativo_s", "etapa_nombre",
                               "tipo_evento", "subsistema_sensor", "severidad", "valor_detectado", "descripcion_tecnica"]
                    cols_p_ev = [c for c in cols_ev if c in df_ev.columns or c == "ensayo_id"]
                    placeholders_ev = ", ".join(["?"] * len(cols_p_ev))
                    sql_ev = f"INSERT INTO eventos_fallos ({', '.join(cols_p_ev)}) VALUES ({placeholders_ev})"
                    vals_ev = []
                    for _, r in df_ev.iterrows():
                        d = r.to_dict()
                        d["ensayo_id"] = ensayo_id
                        vals_ev.append(tuple(d.get(c) for c in cols_p_ev))
                    cur.executemany(sql_ev, vals_ev)

            conn.commit()
            return ensayo_id

    def listar_ensayos_locales(self):
        """Devuelve una lista de diccionarios con todos los ensayos registrados en SQLite."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, nombre_carpeta, placa_num, ronda, fecha_hora, duracion_total_s,
                   peso_inicial_g, peso_final_g, delta_peso_g, rendimiento_faradaico_pct,
                   sincronizado_nube, fecha_sincronizacion
            FROM ensayos
            ORDER BY fecha_hora DESC
            """)
            return [dict(r) for r in cur.fetchall()]


# =============================================================================
# SINCRONIZADOR CON SUPABASE CLOUD (REST API)
# =============================================================================

def limpiar_url_supabase(url):
    if not url:
        return ""
    u = url.strip().rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[:-len("/rest/v1")].rstrip("/")
    return u


class SincronizadorSupabase:
    def __init__(self, db_manager=None):
        self.db = db_manager or GestorDB()
        self.config = cargar_config_nube()

    def recargar_config(self):
        self.config = cargar_config_nube()

    def test_conexion(self, url=None, key=None):
        """Prueba la conexión al endpoint REST de Supabase."""
        u_raw = url if url is not None else self.config.get("supabase_url", "")
        k_raw = key if key is not None else self.config.get("supabase_key", "")
        url_limpia = limpiar_url_supabase(u_raw)
        key_limpia = k_raw.strip() if isinstance(k_raw, str) else ""
        if not url_limpia or not key_limpia:
            return False, "URL o API Key vacía."

        test_endpoint = f"{url_limpia}/rest/v1/ensayos?select=id&limit=1"
        headers = {
            "apikey": key_limpia,
            "Authorization": f"Bearer {key_limpia}"
        }
        try:
            resp = requests.get(test_endpoint, headers=headers, timeout=6)
            if resp.status_code in (200, 206):
                return True, "Conexión exitosa a Supabase (PostgreSQL)."
            return False, f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, f"Fallo de conexión: {str(e)}"

    def subir_ensayo(self, ensayo_id, callback_progreso=None):
        """
        Sube un ensayo y sus 4 tablas relacionadas a Supabase en bloques (chunks).
        """
        self.recargar_config()
        url = limpiar_url_supabase(self.config.get("supabase_url", ""))
        key = self.config.get("supabase_key", "")
        if not url or not key:
            raise ValueError("Faltan credenciales de Supabase en config_nube.json")

        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal"
        }

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM ensayos WHERE id = ?", (ensayo_id,))
            ensayo_row = cur.fetchone()
            if not ensayo_row:
                raise ValueError(f"No existe ensayo con ID {ensayo_id}")

            datos_ensayo = dict(ensayo_row)
            datos_ensayo.pop("sincronizado_nube", None)
            datos_ensayo.pop("fecha_sincronizacion", None)

            if callback_progreso:
                callback_progreso(5, "Subiendo metadatos del ensayo...")

            # 1. Ensayos
            resp_ens = requests.post(f"{url}/rest/v1/ensayos", headers=headers, json=[datos_ensayo], timeout=15)
            if resp_ens.status_code not in (200, 201):
                raise RuntimeError(f"Error al subir ensayo: HTTP {resp_ens.status_code} - {resp_ens.text}")

            # 2. Telemetría 10 Hz por bloques de 500 filas
            cur.execute("SELECT * FROM telemetria_10hz WHERE ensayo_id = ? ORDER BY id ASC", (ensayo_id,))
            filas_tel = [dict(r) for r in cur.fetchall()]
            for f in filas_tel:
                f.pop("id", None)  # Dejar que PostgreSQL asigne BIGSERIAL o maneje clave

            total_tel = len(filas_tel)
            chunk_size = 500
            for i in range(0, total_tel, chunk_size):
                chunk = filas_tel[i:i + chunk_size]
                pct = 10 + int((i / max(1, total_tel)) * 75)
                if callback_progreso:
                    callback_progreso(pct, f"Subiendo telemetría 10Hz ({i + len(chunk)}/{total_tel} filas)...")

                resp_chunk = requests.post(f"{url}/rest/v1/telemetria_10hz", headers=headers, json=chunk, timeout=25)
                if resp_chunk.status_code not in (200, 201):
                    raise RuntimeError(f"Error en bloque telemetría {i}: HTTP {resp_chunk.status_code} - {resp_chunk.text}")

            # 3. Métricas
            if callback_progreso:
                callback_progreso(88, "Subiendo métricas de control...")
            cur.execute("SELECT * FROM metricas_control WHERE ensayo_id = ?", (ensayo_id,))
            filas_err = [dict(r) for r in cur.fetchall()]
            for f in filas_err:
                f.pop("id", None)
            if filas_err:
                resp_err = requests.post(f"{url}/rest/v1/metricas_control", headers=headers, json=filas_err, timeout=15)
                if resp_err.status_code not in (200, 201):
                    raise RuntimeError(f"Error al subir métricas de control: HTTP {resp_err.status_code} - {resp_err.text}")

            # 4. Tiempos Muertos
            if callback_progreso:
                callback_progreso(92, "Subiendo registro de tiempos muertos...")
            cur.execute("SELECT * FROM tiempos_muertos WHERE ensayo_id = ?", (ensayo_id,))
            filas_tm = [dict(r) for r in cur.fetchall()]
            for f in filas_tm:
                f.pop("id", None)
            if filas_tm:
                resp_tm = requests.post(f"{url}/rest/v1/tiempos_muertos", headers=headers, json=filas_tm, timeout=15)
                if resp_tm.status_code not in (200, 201):
                    raise RuntimeError(f"Error al subir tiempos muertos: HTTP {resp_tm.status_code} - {resp_tm.text}")

            # 5. Eventos y Fallos
            if callback_progreso:
                callback_progreso(96, "Subiendo eventos y anomalías...")
            cur.execute("SELECT * FROM eventos_fallos WHERE ensayo_id = ?", (ensayo_id,))
            filas_ev = [dict(r) for r in cur.fetchall()]
            for f in filas_ev:
                f.pop("id", None)
            if filas_ev:
                resp_ev = requests.post(f"{url}/rest/v1/eventos_fallos", headers=headers, json=filas_ev, timeout=15)
                if resp_ev.status_code not in (200, 201):
                    raise RuntimeError(f"Error al subir eventos y fallos: HTTP {resp_ev.status_code} - {resp_ev.text}")

            # Marcar sincronizado en SQLite
            now_iso = datetime.now().isoformat()
            cur.execute("UPDATE ensayos SET sincronizado_nube = 1, fecha_sincronizacion = ? WHERE id = ?", (now_iso, ensayo_id))
            conn.commit()

            if callback_progreso:
                callback_progreso(100, "¡Sincronización completa con Supabase!")
        return True


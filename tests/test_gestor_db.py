#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
PRUEBAS UNITARIAS DE GESTOR_DB Y SINCRONIZADOR NUBE (test_gestor_db.py)
=============================================================================
Pruebas integrales con SQLite en memoria / archivos temporales y mocks
para verificar la lógica Offline-First, SHA-256 e integración REST con Supabase.
=============================================================================
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Incluir rutas del software SCADA para resolver módulos de utilidades
DIR_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_SOFTWARE = os.path.join(DIR_ROOT, "software")
DIR_TEL2 = os.path.join(DIR_SOFTWARE, "telemetria2.0")

for p in [DIR_ROOT, DIR_SOFTWARE, DIR_TEL2]:
    if p not in sys.path:
        sys.path.insert(0, p)

from utilidades.gestor_db import (
    GestorDB,
    SincronizadorSupabase,
    calcular_sha256,
    cargar_config_nube,
    guardar_config_nube,
    limpiar_url_supabase,
)


@pytest.fixture
def temp_env(tmp_path):
    """Crea un entorno temporal con base de datos SQLite y config JSON."""
    db_file = str(tmp_path / "test_ensayos.db")
    config_file = str(tmp_path / "test_config_nube.json")
    return {"tmp_path": tmp_path, "db_file": db_file, "config_file": config_file}


def test_calcular_sha256(tmp_path):
    # Archivo inexistente
    assert calcular_sha256(str(tmp_path / "inexistente.txt")) is None

    # Archivo con contenido
    test_file = tmp_path / "muestra.txt"
    test_file.write_text("ELECTRODO-32 INTEGRIDAD AUDITORIA D2", encoding="utf-8")
    hash_val = calcular_sha256(str(test_file))
    assert hash_val is not None
    assert len(hash_val) == 64


def test_limpiar_url_supabase():
    assert limpiar_url_supabase("") == ""
    assert limpiar_url_supabase("https://xyz.supabase.co/") == "https://xyz.supabase.co"
    assert limpiar_url_supabase("https://xyz.supabase.co/rest/v1") == "https://xyz.supabase.co"
    assert limpiar_url_supabase("https://xyz.supabase.co/rest/v1/") == "https://xyz.supabase.co"


def test_config_nube_crud(temp_env, monkeypatch):
    cfg_file = temp_env["config_file"]
    monkeypatch.setattr("utilidades.gestor_db.RUTA_CONFIG_NUBE", cfg_file)

    # Cargar por defecto si no existe
    cfg = cargar_config_nube()
    assert cfg["habilitado"] is False
    assert cfg["supabase_url"] == ""

    # Guardar nueva config
    cfg["supabase_url"] = "https://proyecto.supabase.co"
    cfg["supabase_key"] = "test-token-jwt"
    cfg["habilitado"] = True
    assert guardar_config_nube(cfg) is True

    # Recargar
    cfg_leida = cargar_config_nube()
    assert cfg_leida["supabase_url"] == "https://proyecto.supabase.co"
    assert cfg_leida["habilitado"] is True


def test_gestor_db_inicializacion(temp_env):
    gestor = GestorDB(ruta_sqlite=temp_env["db_file"])
    with gestor.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = [r[0] for r in cur.fetchall()]
        assert "ensayos" in tablas
        assert "telemetria_10hz" in tablas
        assert "metricas_control" in tablas
        assert "tiempos_muertos" in tablas
        assert "eventos_fallos" in tablas


def test_gestor_db_registro_y_listado(temp_env):
    gestor = GestorDB(ruta_sqlite=temp_env["db_file"])
    carpeta_ensayo = temp_env["tmp_path"] / "Ensayo_P01_Ronda_1_20261028_120000"
    carpeta_ensayo.mkdir()

    # Crear telemetria_completa.csv
    df_tel = pd.DataFrame([{
        "Timestamp_ISO": "2026-10-28T12:00:00",
        "Tiempo_Relativo_s": 0.1,
        "Placa_ID": 1,
        "Ronda": "Ronda 1",
        "Etapa_Num": 1,
        "Etapa_Nombre": "Limpieza",
        "Etapa_Tiempo_s": 0.1,
        "Etapa_Duracion_s": 60.0,
        "Corriente_Target_A": 1.5,
        "Modo_Corriente": "DC",
        "Masa_Teorica_Faraday_mg": 25.4,
        "Fuente_Activa": 1,
        "Fuente_Corriente_Real_A": 1.49
    }, {
        "Timestamp_ISO": "2026-10-28T12:00:01",
        "Tiempo_Relativo_s": 1.0,
        "Placa_ID": 1,
        "Ronda": "Ronda 1",
        "Etapa_Num": 1,
        "Etapa_Nombre": "Limpieza",
        "Etapa_Tiempo_s": 1.0,
        "Etapa_Duracion_s": 60.0,
        "Corriente_Target_A": 1.5,
        "Modo_Corriente": "DC",
        "Masa_Teorica_Faraday_mg": 28.0,
        "Fuente_Activa": 1,
        "Fuente_Corriente_Real_A": 1.50
    }])
    df_tel.to_csv(carpeta_ensayo / "telemetria_completa.csv", index=False)

    # Crear metricas_control_errores.csv
    df_err = pd.DataFrame([{
        "Timestamp_ISO": "2026-10-28T12:00:00",
        "Tiempo_Relativo_s": 0.1,
        "Etapa_Num": 1,
        "Etapa_Nombre": "Limpieza",
        "Error_T1_C": 0.2,
        "IAE_T1": 0.02
    }])
    df_err.to_csv(carpeta_ensayo / "metricas_control_errores.csv", index=False)

    # Crear registro_tiempos_muertos.csv
    df_tm = pd.DataFrame([{
        "Transicion_ID": "T1_T2",
        "Etapa_Origen_Num": 1,
        "Etapa_Origen_Nombre": "Limpieza",
        "Etapa_Destino_Num": 2,
        "Etapa_Destino_Nombre": "Decapado",
        "Tiempo_Muerto_s": 4.5
    }])
    df_tm.to_csv(carpeta_ensayo / "registro_tiempos_muertos.csv", index=False)

    # Crear registro_eventos_fallos.csv
    df_ev = pd.DataFrame([{
        "Timestamp_ISO": "2026-10-28T12:00:00",
        "Tiempo_Relativo_s": 0.5,
        "Etapa_Nombre": "Limpieza",
        "Tipo_Evento": "INFO",
        "Subsistema_Sensor": "TERMO",
        "Severidad": "BAJA",
        "Valor_Detectado": "60.0",
        "Descripcion_Tecnica": "Consigna alcanzada"
    }])
    df_ev.to_csv(carpeta_ensayo / "registro_eventos_fallos.csv", index=False)

    grav = {
        "peso_inicial_g": 10.000,
        "peso_final_g": 10.025,
        "area_placa_cm2": 65.0,
        "observaciones": "Prueba de auditoria"
    }

    # Registro de nuevo ensayo
    ensayo_id = gestor.registrar_o_actualizar_ensayo_local(str(carpeta_ensayo), datos_gravimetria=grav)
    assert ensayo_id is not None

    # Listado
    lista = gestor.listar_ensayos_locales()
    assert len(lista) == 1
    assert lista[0]["id"] == ensayo_id
    assert lista[0]["placa_num"] == 1
    assert lista[0]["rendimiento_faradaico_pct"] > 0

    # Actualización sobre el mismo ensayo
    grav["peso_final_g"] = 10.027
    ensayo_id_2 = gestor.registrar_o_actualizar_ensayo_local(str(carpeta_ensayo), datos_gravimetria=grav)
    assert ensayo_id_2 == ensayo_id

    lista_upd = gestor.listar_ensayos_locales()
    assert len(lista_upd) == 1
    assert lista_upd[0]["delta_peso_g"] == pytest.approx(0.027, rel=1e-3)


def test_gestor_db_error_sin_telemetria(temp_env):
    gestor = GestorDB(ruta_sqlite=temp_env["db_file"])
    carpeta_vacia = temp_env["tmp_path"] / "Carpeta_Vacia"
    carpeta_vacia.mkdir()

    with pytest.raises(FileNotFoundError):
        gestor.registrar_o_actualizar_ensayo_local(str(carpeta_vacia))


def test_sincronizador_supabase_test_conexion(temp_env, monkeypatch):
    gestor = GestorDB(ruta_sqlite=temp_env["db_file"])
    sinc = SincronizadorSupabase(db_manager=gestor)

    # URL o Key vacías
    ok, msg = sinc.test_conexion("", "")
    assert ok is False

    # Conexión mock exitosa (HTTP 200)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp):
        ok, msg = sinc.test_conexion("https://test.supabase.co", "jwt-key")
        assert ok is True
        assert "exitosa" in msg

    # Conexión mock fallida (HTTP 401)
    mock_resp.status_code = 401
    mock_resp.text = "Invalid API key"
    with patch("requests.get", return_value=mock_resp):
        ok, msg = sinc.test_conexion("https://test.supabase.co", "jwt-key")
        assert ok is False
        assert "HTTP 401" in msg

    # Excepción de red
    with patch("requests.get", side_effect=Exception("Timeout en DNS")):
        ok, msg = sinc.test_conexion("https://test.supabase.co", "jwt-key")
        assert ok is False
        assert "Timeout en DNS" in msg


def test_sincronizador_supabase_subir_ensayo(temp_env, monkeypatch):
    cfg_file = temp_env["config_file"]
    monkeypatch.setattr("utilidades.gestor_db.RUTA_CONFIG_NUBE", cfg_file)
    guardar_config_nube({
        "supabase_url": "https://test.supabase.co",
        "supabase_key": "test-jwt-token",
        "habilitado": True
    })

    gestor = GestorDB(ruta_sqlite=temp_env["db_file"])
    sinc = SincronizadorSupabase(db_manager=gestor)

    # Crear ensayo local mínimo
    carpeta_ensayo = temp_env["tmp_path"] / "Ensayo_Upload_Test"
    carpeta_ensayo.mkdir()
    df_tel = pd.DataFrame([{
        "Timestamp_ISO": "2026-10-28T12:00:00",
        "Tiempo_Relativo_s": 0.1,
        "Placa_ID": 1,
        "Ronda": "Ronda 1",
        "Etapa_Num": 1,
        "Etapa_Nombre": "Limpieza",
        "Etapa_Tiempo_s": 0.1,
        "Etapa_Duracion_s": 60.0,
        "Corriente_Target_A": 1.5,
        "Modo_Corriente": "DC",
        "Masa_Teorica_Faraday_mg": 25.4,
        "Fuente_Activa": 1,
        "Fuente_Corriente_Real_A": 1.49
    }])
    df_tel.to_csv(carpeta_ensayo / "telemetria_completa.csv", index=False)
    ensayo_id = gestor.registrar_o_actualizar_ensayo_local(str(carpeta_ensayo))

    # Mock de peticiones POST a Supabase exitosas
    mock_post_ok = MagicMock()
    mock_post_ok.status_code = 201

    progreso_registros = []
    def track_progreso(pct, desc):
        progreso_registros.append((pct, desc))

    with patch("requests.post", return_value=mock_post_ok):
        res = sinc.subir_ensayo(ensayo_id, callback_progreso=track_progreso)
        assert res is True
        assert len(progreso_registros) > 0
        assert progreso_registros[-1][0] == 100

    # Verificar que en SQLite local quedó marcado como sincronizado
    with gestor.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT sincronizado_nube, fecha_sincronizacion FROM ensayos WHERE id = ?", (ensayo_id,))
        row = cur.fetchone()
        assert row["sincronizado_nube"] == 1
        assert row["fecha_sincronizacion"] is not None

    # Error si el ensayo no existe
    with pytest.raises(ValueError):
        sinc.subir_ensayo("uuid-inexistente")

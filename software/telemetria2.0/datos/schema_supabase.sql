-- ============================================================================
-- ESQUEMA DE BASE DE DATOS SUPABASE (POSTGRESQL) - PROYECTO E.L.E.C.T.R.O.D.O-32
-- Innovafest Guadalajara 2026 & SMEQ 2026 (CTS-C51)
-- ============================================================================

-- Habilitar extensión UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. TABLA MAESTRA DE ENSAYOS EXPERIMENTALES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ensayos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_carpeta TEXT NOT NULL UNIQUE,
    placa_num INTEGER NOT NULL,
    ronda TEXT NOT NULL,
    fecha_hora TIMESTAMPTZ NOT NULL,
    duracion_total_s NUMERIC(10, 2) DEFAULT 0.0,
    fuente_datos TEXT DEFAULT 'HARDWARE',
    version_firmware TEXT DEFAULT 'RTOS 2.0',
    
    -- Caracterización Gravimétrica (Balanza Analítica y Ley de Faraday)
    peso_inicial_g NUMERIC(10, 4) DEFAULT 0.0000,
    peso_final_g NUMERIC(10, 4) DEFAULT 0.0000,
    delta_peso_g NUMERIC(10, 4) DEFAULT 0.0000,
    area_placa_cm2 NUMERIC(8, 2) DEFAULT 65.0,
    masa_teorica_faraday_mg NUMERIC(12, 4) DEFAULT 0.0,
    rendimiento_faradaico_pct NUMERIC(6, 2) DEFAULT 0.0,
    
    -- Integridad y Auditoría de Datos (Proveniencia D2)
    sha256_telemetria TEXT,
    sha256_metricas TEXT,
    sha256_eventos TEXT,
    sha256_tiempos_muertos TEXT,
    
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices de búsqueda para ensayos
CREATE INDEX IF NOT EXISTS idx_ensayos_placa ON ensayos(placa_num);
CREATE INDEX IF NOT EXISTS idx_ensayos_fecha ON ensayos(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ensayos_ronda ON ensayos(ronda);

-- ----------------------------------------------------------------------------
-- 2. TABLA DE TELEMETRÍA DE ALTA RESOLUCIÓN (10 Hz)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS telemetria_10hz (
    id BIGSERIAL PRIMARY KEY,
    ensayo_id UUID NOT NULL REFERENCES ensayos(id) ON DELETE CASCADE,
    timestamp_iso TIMESTAMPTZ,
    tiempo_relativo_s NUMERIC(10, 2),
    placa_id INTEGER,
    ronda TEXT,
    etapa_num INTEGER,
    etapa_nombre TEXT,
    etapa_tiempo_s NUMERIC(10, 2),
    etapa_duracion_s NUMERIC(10, 2),
    corriente_target_a NUMERIC(8, 3),
    modo_corriente TEXT,
    temp_sp_target_c NUMERIC(8, 2),
    
    -- T1: Tina de Limpieza
    t1_limpieza_temp_c NUMERIC(8, 2),
    t1_limpieza_sp_c NUMERIC(8, 2),
    t1_limpieza_activo BOOLEAN,
    t1_triac_potencia_pct NUMERIC(6, 2),
    t1_triac_alpha_deg NUMERIC(6, 2),
    t1_triac_delay_us INTEGER,
    t1_triac_watts_w NUMERIC(8, 2),
    
    -- T2: Tina de Decapado / Matizado
    t2_decapado_temp_c NUMERIC(8, 2),
    t2_decapado_sp_c NUMERIC(8, 2),
    t2_decapado_activo BOOLEAN,
    t2_triac_potencia_pct NUMERIC(6, 2),
    t2_triac_alpha_deg NUMERIC(6, 2),
    t2_triac_delay_us INTEGER,
    t2_triac_watts_w NUMERIC(8, 2),
    
    -- T3: Tina de Cincado / Celda Hull
    t3_celdahull_temp_c NUMERIC(8, 2),
    t3_celdahull_sp_c NUMERIC(8, 2),
    t3_celdahull_activo BOOLEAN,
    t3_triac_potencia_pct NUMERIC(6, 2),
    t3_triac_alpha_deg NUMERIC(6, 2),
    t3_triac_delay_us INTEGER,
    t3_triac_watts_w NUMERIC(8, 2),
    
    -- T4: Tina de Niquelado Watts
    t4_niquelado_temp_c NUMERIC(8, 2),
    t4_niquelado_sp_c NUMERIC(8, 2),
    t4_niquelado_activo BOOLEAN,
    t4_triac_potencia_pct NUMERIC(6, 2),
    t4_triac_alpha_deg NUMERIC(6, 2),
    t4_triac_delay_us INTEGER,
    t4_triac_watts_w NUMERIC(8, 2),
    
    -- pH Métrico y Calibración
    ph_tina1 NUMERIC(6, 2),
    ph_tina2 NUMERIC(6, 2),
    ph_modulo_activo BOOLEAN,
    ph_modo_cal_t1 TEXT,
    ph_modo_cal_t2 TEXT,
    ph_slope_pct_t1 NUMERIC(6, 2),
    ph_slope_pct_t2 NUMERIC(6, 2),
    ph_interlock_activo BOOLEAN,
    
    -- VCSS Fuente de Corriente
    fuente_activa BOOLEAN,
    fuente_modo_pulsado BOOLEAN,
    fuente_corriente_consigna_a NUMERIC(8, 3),
    fuente_corriente_real_a NUMERIC(8, 3),
    fuente_corriente_shunt1_a NUMERIC(8, 3),
    fuente_corriente_shunt2_a NUMERIC(8, 3),
    fuente_voltaje_shunt1_v NUMERIC(8, 3),
    fuente_voltaje_shunt2_v NUMERIC(8, 3),
    fuente_factor_gm NUMERIC(8, 4),
    fuente_compensacion_activa BOOLEAN,
    fuente_rele_vdd BOOLEAN,
    fuente_amplitud_dac INTEGER,
    fuente_frecuencia_hz NUMERIC(8, 2),
    fuente_dutycycle_pct NUMERIC(6, 2),
    fuente_pi_estado TEXT,
    fuente_salud_celda TEXT,
    
    -- Acumuladores e Indicadores Globales
    carga_acumulada_coulombs NUMERIC(12, 3),
    masa_teorica_faraday_mg NUMERIC(12, 4),
    energia_termica_wh NUMERIC(12, 4),
    ambiente_temp_c NUMERIC(6, 2),
    ambiente_humedad_pct NUMERIC(6, 2),
    ambiente_presion_hpa NUMERIC(8, 2),
    
    -- Idempotencia: evita duplicados al reintentar cargas interrumpidas
    CONSTRAINT uq_telemetria_ensayo_tiempo UNIQUE(ensayo_id, tiempo_relativo_s)
);

CREATE INDEX IF NOT EXISTS idx_telemetria_ensayo_tiempo ON telemetria_10hz(ensayo_id, tiempo_relativo_s);
CREATE INDEX IF NOT EXISTS idx_telemetria_etapa ON telemetria_10hz(ensayo_id, etapa_num);

-- ----------------------------------------------------------------------------
-- 3. TABLA DE MÉTRICAS DE CONTROL Y ERROR
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metricas_control (
    id BIGSERIAL PRIMARY KEY,
    ensayo_id UUID NOT NULL REFERENCES ensayos(id) ON DELETE CASCADE,
    timestamp_iso TIMESTAMPTZ,
    tiempo_relativo_s NUMERIC(10, 2),
    etapa_num INTEGER,
    etapa_nombre TEXT,
    error_t1_c NUMERIC(8, 2),
    error_t2_c NUMERIC(8, 2),
    error_t3_c NUMERIC(8, 2),
    error_t4_c NUMERIC(8, 2),
    error_corriente_a NUMERIC(8, 3),
    iae_t1 NUMERIC(12, 3),
    iae_t2 NUMERIC(12, 3),
    iae_t3 NUMERIC(12, 3),
    iae_t4 NUMERIC(12, 3),
    iae_corriente NUMERIC(12, 3),
    esfuerzo_u1_pct NUMERIC(6, 2),
    esfuerzo_u2_pct NUMERIC(6, 2),
    esfuerzo_u3_pct NUMERIC(6, 2),
    esfuerzo_u4_pct NUMERIC(6, 2)
);

CREATE INDEX IF NOT EXISTS idx_metricas_ensayo ON metricas_control(ensayo_id);

-- ----------------------------------------------------------------------------
-- 4. TABLA DE REGISTRO DE EVENTOS, ANOMALÍAS Y FALLOS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS eventos_fallos (
    id BIGSERIAL PRIMARY KEY,
    ensayo_id UUID NOT NULL REFERENCES ensayos(id) ON DELETE CASCADE,
    timestamp_iso TIMESTAMPTZ,
    tiempo_relativo_s NUMERIC(10, 2),
    etapa_nombre TEXT,
    tipo_evento TEXT,
    subsistema_sensor TEXT,
    severidad TEXT,
    valor_detectado TEXT,
    descripcion_tecnica TEXT
);

CREATE INDEX IF NOT EXISTS idx_eventos_ensayo ON eventos_fallos(ensayo_id);

-- ----------------------------------------------------------------------------
-- 5. TABLA DE TIEMPOS MUERTOS ENTRE FASES ISA-88
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tiempos_muertos (
    id BIGSERIAL PRIMARY KEY,
    ensayo_id UUID NOT NULL REFERENCES ensayos(id) ON DELETE CASCADE,
    transicion_id TEXT,
    etapa_origen_num INTEGER,
    etapa_origen_nombre TEXT,
    etapa_destino_num INTEGER,
    etapa_destino_nombre TEXT,
    timestamp_inicio TIMESTAMPTZ,
    timestamp_fin TIMESTAMPTZ,
    tiempo_muerto_s NUMERIC(10, 2),
    temp_ambiente_c NUMERIC(6, 2),
    humedad_pct NUMERIC(6, 2),
    presion_hpa NUMERIC(8, 2),
    evaporacion_estimada_g_h NUMERIC(8, 3)
);

CREATE INDEX IF NOT EXISTS idx_tiempos_muertos_ensayo ON tiempos_muertos(ensayo_id);

-- ----------------------------------------------------------------------------
-- HABILITAR SEGURIDAD (ROW LEVEL SECURITY - RLS) Y POLÍTICAS PÚBLICAS ANON
-- ----------------------------------------------------------------------------
ALTER TABLE ensayos ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetria_10hz ENABLE ROW LEVEL SECURITY;
ALTER TABLE metricas_control ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos_fallos ENABLE ROW LEVEL SECURITY;
ALTER TABLE tiempos_muertos ENABLE ROW LEVEL SECURITY;

-- Permitir SELECT e INSERT a la API anon
CREATE POLICY "Permitir select anon a ensayos" ON ensayos FOR SELECT USING (true);
CREATE POLICY "Permitir insert anon a ensayos" ON ensayos FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir update anon a ensayos" ON ensayos FOR UPDATE USING (true);

CREATE POLICY "Permitir select anon a telemetria" ON telemetria_10hz FOR SELECT USING (true);
CREATE POLICY "Permitir insert anon a telemetria" ON telemetria_10hz FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir select anon a metricas" ON metricas_control FOR SELECT USING (true);
CREATE POLICY "Permitir insert anon a metricas" ON metricas_control FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir select anon a eventos" ON eventos_fallos FOR SELECT USING (true);
CREATE POLICY "Permitir insert anon a eventos" ON eventos_fallos FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir select anon a tiempos_muertos" ON tiempos_muertos FOR SELECT USING (true);
CREATE POLICY "Permitir insert anon a tiempos_muertos" ON tiempos_muertos FOR INSERT WITH CHECK (true);


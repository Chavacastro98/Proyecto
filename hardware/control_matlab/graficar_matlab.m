%% ========================================================================= %
%%  GRAFICADOR DE TELEMETRÍA CIENTÍFICA - PLANTA PILOTO DE ELECTRODEPOSICIÓN %
%% ========================================================================= %
% Proyecto: Tesis de Automatización y Control de Línea Piloto de Electrodeposición
% Microcontrolador: ESP32-S3 N16R8 (Firmware v3.5 / RTOS 1.0)
% Propósito: Carga y análisis gráfico de telemetría de ensayos reales o
%            simulados a partir de los archivos CSV generados por Python.
%            Genera figuras en alta resolución (300 DPI) para memoria de tesis.
% Compatibilidad: Firmware v3.1, v3.5, v4.0 y RTOS 1.0 (ESP32-S3)
%% ========================================================================= %

clear; clc; close all;

fprintf('=========================================================================\n');
fprintf('  📊 GRAFICADOR DE TELEMETRÍA EN MATLAB — PLANTA DE ELECTRODEPOSICIÓN\n');
fprintf('  ESP32-S3 N16R8 | Firmware v3.5 / RTOS 1.0 | UdeG\n');
fprintf('=========================================================================\n\n');

%% 1. BÚSQUEDA INTELIGENTE DEL ARCHIVO CSV DE TELEMETRÍA
% Rutas candidatas comunes relativas y absolutas
candidatos_carpetas = {
    fullfile('..', 'telemetria', 'experimentos');
    fullfile('telemetria', 'experimentos');
    fullfile('..', 'experimentos');
    fullfile('experimentos');
    fullfile('..', 'telemetria');
    fullfile('telemetria');
    pwd
};

lista_archivos = [];
for i = 1:length(candidatos_carpetas)
    carpeta = candidatos_carpetas{i};
    if isfolder(carpeta)
        % Búsqueda de telemetría completa o proceso
        archivos_encontrados = dir(fullfile(carpeta, '**', '*.csv'));
        if ~isempty(archivos_encontrados)
            lista_archivos = [lista_archivos; archivos_encontrados]; %#ok<AGROW>
        end
    end
end

% Filtrar archivos que NO son de telemetría (como partitions.csv o metricas de error solas)
archivos_validos = [];
for i = 1:length(lista_archivos)
    nombre = lista_archivos(i).name;
    if ~contains(lower(nombre), 'partitions') && ...
       ~contains(lower(nombre), 'metricas_control_errores') && ...
       lista_archivos(i).bytes > 500
        archivos_validos = [archivos_validos; lista_archivos(i)]; %#ok<AGROW>
    end
end

ruta_completa = '';
if ~isempty(archivos_validos)
    % Seleccionar el archivo más reciente según fecha de modificación
    [~, idx_reciente] = max([archivos_validos.datenum]);
    archivo_sel = archivos_validos(idx_reciente);
    ruta_completa = fullfile(archivo_sel.folder, archivo_sel.name);
    fprintf('📁 Archivo más reciente detectado automáticamente:\n   -> %s\n', ruta_completa);
    
    % Preguntar en consola si se desea usar este archivo o seleccionar otro
    try
        resp = input('   ¿Deseas usar este archivo? [ENTER=Sí / o=otra ruta]: ', 's');
        if isempty(resp)
            resp = 's';
        end
    catch
        resp = 's';
    end
    if strcmpi(resp, 'n') || strcmpi(resp, 'o')
        ruta_completa = '';
    end
end

if isempty(ruta_completa)
    fprintf('📂 Abriendo selector de archivos...\n');
    [nombre_archivo, ruta_dir] = uigetfile('*.csv', 'Selecciona el archivo CSV de telemetría');
    if isequal(nombre_archivo, 0)
        disp('❌ Operación cancelada. No se seleccionó ningún archivo CSV.');
        return;
    end
    ruta_completa = fullfile(ruta_dir, nombre_archivo);
end

fprintf('\n⏳ Cargando datos desde: %s ...\n', ruta_completa);

%% 2. IMPORTACIÓN DE DATOS CON COMPATIBILIDAD UNIVERSAL
try
    opciones = detectImportOptions(ruta_completa);
    if isprop(opciones, 'VariableNamingRule')
        opciones.VariableNamingRule = 'preserve';
    end
    data = readtable(ruta_completa, opciones);
catch
    data = readtable(ruta_completa);
end

n_filas = height(data);
if n_filas == 0
    error('El archivo CSV seleccionado está vacío o no contiene filas de datos.');
end
fprintf('✅ Datos cargados correctamente: %d registros de telemetría.\n', n_filas);

%% 3. EXTRACCIÓN ROBUSTA DE VARIABLES MEDIANTE ALIAS
% 3.1 Tiempo relativo de proceso
[tiempo_s, hay_t] = obtener_columna(data, ...
    {'Tiempo_Relativo_s', 'Tiempo_s', 'tiempo_relativo_s', 'tiempo_s', 'Time_s', 't_s', 'timestamp', 'Tiempo'}, ...
    (0:(n_filas-1))', n_filas);
tiempo_min = tiempo_s / 60.0; % Conversión a minutos para publicación

% 3.2 Temperaturas Reales y Setpoints (°C)
% Tina 1: Desengrase / Limpieza Alcalina (450W)
[t1_temp, ~] = obtener_columna(data, {'T1_Limpieza_Temp_C', 'T1_Temp_C', 'Temp1', 'T1_Temp', 'T1'}, 25.0, n_filas);
[t1_sp,   ~] = obtener_columna(data, {'T1_Limpieza_SP_C', 'T1_SP_C', 'SP1', 'T1_SP'}, 85.0, n_filas);

% Tina 2: Decapado Químico Ácido (450W)
[t2_temp, ~] = obtener_columna(data, {'T2_Decapado_Temp_C', 'T2_Temp_C', 'Temp2', 'T2_Temp', 'T2'}, 25.0, n_filas);
[t2_sp,   ~] = obtener_columna(data, {'T2_Decapado_SP_C', 'T2_SP_C', 'SP2', 'T2_SP'}, 85.0, n_filas);

% Tina 3: Zincado Ácido en Celda Hull (18W)
[t3_temp, ~] = obtener_columna(data, {'T3_CeldaHull_Temp_C', 'T3_Zincado_Temp_C', 'T3_Temp_C', 'Temp3', 'T3'}, 25.0, n_filas);
[t3_sp,   ~] = obtener_columna(data, {'T3_CeldaHull_SP_C', 'T3_Zincado_SP_C', 'T3_SP_C', 'SP3', 'T3_SP'}, 25.0, n_filas);

% Tina 4: Niquelado Watts (450W)
[t4_temp, ~] = obtener_columna(data, {'T4_Niquelado_Temp_C', 'T4_Temp_C', 'Temp4', 'T4_Temp', 'T4'}, 25.0, n_filas);
[t4_sp,   ~] = obtener_columna(data, {'T4_Niquelado_SP_C', 'T4_SP_C', 'SP4', 'T4_SP'}, 30.0, n_filas);

% 3.3 Esfuerzo de Control de TRIACs (u_1..u_4 en % y Watts)
[u_t1, hay_u1] = obtener_columna(data, {'T1_TRIAC_Potencia_Pct', 'Esfuerzo_u1_Pct', 'u1', 'T1_Potencia_Pct'}, max(0, min(100, (t1_sp - t1_temp)*20)), n_filas);
[u_t2, hay_u2] = obtener_columna(data, {'T2_TRIAC_Potencia_Pct', 'Esfuerzo_u2_Pct', 'u2', 'T2_Potencia_Pct'}, max(0, min(100, (t2_sp - t2_temp)*20)), n_filas);
[u_t3, hay_u3] = obtener_columna(data, {'T3_TRIAC_Potencia_Pct', 'Esfuerzo_u3_Pct', 'u3', 'T3_Potencia_Pct'}, max(0, min(100, (t3_sp - t3_temp)*20)), n_filas);
[u_t4, hay_u4] = obtener_columna(data, {'T4_TRIAC_Potencia_Pct', 'Esfuerzo_u4_Pct', 'u4', 'T4_Potencia_Pct'}, max(0, min(100, (t4_sp - t4_temp)*20)), n_filas);

% 3.4 Corriente Galvánica del Sumidero VCSS (Amperes)
% Solución directa al conflicto histórico 'Fuente_Corriente_A' vs 'Fuente_Corriente_Real_A'
[i_real, hay_ireal, col_ireal] = obtener_columna(data, ...
    {'Fuente_Corriente_Real_A', 'Fuente_Corriente_A', 'Corriente_Real_A', 'Corriente_A', 'I_real', 'i_amp'}, ...
    0.0, n_filas);

[i_target, hay_itarget] = obtener_columna(data, ...
    {'Fuente_Corriente_Consigna_A', 'Corriente_Target_A', 'Fuente_Corriente_SP_A', 'Corriente_SP_A', 'I_target', 'I_sp'}, ...
    0.0, n_filas);

[i_shunt1, hay_sh1] = obtener_columna(data, {'Fuente_Corriente_Shunt1_A', 'I_Shunt1_A'}, 0.0, n_filas);
[i_shunt2, hay_sh2] = obtener_columna(data, {'Fuente_Corriente_Shunt2_A', 'I_Shunt2_A'}, 0.0, n_filas);

% 3.5 Monitoreo de pH Dual
[ph1, hay_ph1] = obtener_columna(data, {'pH_Tina1', 'pH1', 'pH_Zincado', 'pH_T1'}, NaN, n_filas);
[ph2, hay_ph2] = obtener_columna(data, {'pH_Tina2', 'pH2', 'pH_Niquelado', 'pH_T2'}, NaN, n_filas);
[ph_on, ~]     = obtener_columna(data, {'pH_Modulo_Activo', 'pH_Interlock_Activo'}, 1, n_filas);

% 3.6 Culombimetría y Rendimiento Faradaico
[q_coulombs, hay_q] = obtener_columna(data, {'Carga_Acumulada_Coulombs', 'Carga_Coulombs', 'Q_Coulombs'}, NaN, n_filas);
if ~hay_q || all(isnan(q_coulombs))
    % Calcular culombimetría numérica acumulada por la regla trapezoidal si no viene en CSV
    dt_arr = [0; diff(tiempo_s)];
    dt_arr(dt_arr < 0 | dt_arr > 10) = 1.0;
    q_coulombs = cumsum(i_real .* dt_arr);
end
% Masa teórica depositada aproximada según Ley de Faraday (mg)
[m_faraday, hay_mf] = obtener_columna(data, {'Masa_Teorica_Faraday_mg', 'Masa_mg'}, q_coulombs * 0.3388, n_filas);

% 3.7 Condiciones Meteorológicas y Ambientales (AHT20 / BMP280)
[t_amb, hay_tamb] = obtener_columna(data, {'Ambiente_Temp_C', 'Temp_Ambiente_C', 'T_Amb_C'}, NaN, n_filas);
[h_amb, hay_hamb] = obtener_columna(data, {'Ambiente_Humedad_Pct', 'Humedad_Pct', 'H_Amb_Pct'}, NaN, n_filas);
[p_amb, hay_pamb] = obtener_columna(data, {'Ambiente_Presion_hPa', 'Presion_hPa'}, NaN, n_filas);

% Metadatos para encabezados
[placa_id, hay_pid] = obtener_columna(data, {'Placa_ID', 'placa_id', 'ID_Placa'}, 1, n_filas);
subtitulo_id = '';
if hay_pid && ~isnan(placa_id(1))
    subtitulo_id = sprintf(' — Ensayo Placa #%d', round(placa_id(1)));
end

%% 4. DEFINICIÓN DE PALETA CROMÁTICA CIENTÍFICA (ESTILO TESIS / IEEE)
c_t1 = [0.85, 0.33, 0.10]; % Terracota - T1 Limpieza Alcalina
c_t2 = [0.93, 0.69, 0.13]; % Ámbar    - T2 Decapado Ácido
c_t3 = [0.00, 0.45, 0.74]; % Cerúleo  - T3 Zincado Celda Hull
c_t4 = [0.49, 0.18, 0.56]; % Púrpura  - T4 Níquel Watts
c_i  = [0.08, 0.64, 0.29]; % Esmeralda- Corriente Galvánica
c_ph1= [0.02, 0.58, 0.85]; % Cian     - pH 1 Zincado
c_ph2= [0.55, 0.15, 0.75]; % Violeta  - pH 2 Níquel

%% =========================================================================
%% FIGURA 1: PERFIL INTEGRAL DE PROCESO Y ACTUADORES DE POTENCIA (3 PANELES)
%% =========================================================================
fig1 = figure('Name', 'Figura 1: Perfil Integral de Proceso y Actuadores', ...
              'Color', [1 1 1], 'Position', [80, 40, 1150, 880], ...
              'NumberTitle', 'off');

% --- SUBPLOT 1: Control Térmico de las 4 Tinas vs Setpoints ---
sp1_1 = subplot(3, 1, 1);
hold on; grid on; box on;
set(sp1_1, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], 'YColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

plot(tiempo_min, t1_temp, '-',  'LineWidth', 2.0, 'Color', c_t1, 'DisplayName', 'T1: Limpieza Alcalina (450W)');
plot(tiempo_min, t1_sp,   '--', 'LineWidth', 1.3, 'Color', [c_t1, 0.6], 'DisplayName', 'SP Limpieza (85°C)');

plot(tiempo_min, t2_temp, '-',  'LineWidth', 2.0, 'Color', c_t2, 'DisplayName', 'T2: Decapado Ácido (450W)');
plot(tiempo_min, t2_sp,   '--', 'LineWidth', 1.3, 'Color', [c_t2, 0.6], 'DisplayName', 'SP Decapado (85°C)');

plot(tiempo_min, t3_temp, '-',  'LineWidth', 2.2, 'Color', c_t3, 'DisplayName', 'T3: Celda Hull Zincado (18W)');
plot(tiempo_min, t3_sp,   '--', 'LineWidth', 1.3, 'Color', [c_t3, 0.6], 'DisplayName', 'SP Celda Hull (25°C)');

plot(tiempo_min, t4_temp, '-',  'LineWidth', 2.0, 'Color', c_t4, 'DisplayName', 'T4: Níquel Watts (450W)');
plot(tiempo_min, t4_sp,   '--', 'LineWidth', 1.3, 'Color', [c_t4, 0.6], 'DisplayName', 'SP Níquel Watts (30°C)');

ylabel('Temperatura (°C)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
title(sprintf('🔥 1. Perfiles Térmicos de las 4 Tinas vs Setpoints (Control PI + Rampa Suave)%s', subtitulo_id), ...
      'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);
y_max_t = max([max(t1_temp, [], 'omitnan'), max(t2_temp, [], 'omitnan'), ...
               max(t3_temp, [], 'omitnan'), max(t4_temp, [], 'omitnan'), 85.0]);
if isnan(y_max_t) || y_max_t < 40, y_max_t = 95.0; end
ylim([15, y_max_t + 8]);

% --- SUBPLOT 2: Esfuerzo de Conducción de TRIACs AC 60Hz (%) ---
sp1_2 = subplot(3, 1, 2);
hold on; grid on; box on;
set(sp1_2, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], 'YColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

plot(tiempo_min, u_t1, '-',  'LineWidth', 1.8, 'Color', c_t1, 'DisplayName', 'u1: Limpieza (450W) [%]');
plot(tiempo_min, u_t2, '--', 'LineWidth', 1.8, 'Color', c_t2, 'DisplayName', 'u2: Decapado (450W) [%]');
plot(tiempo_min, u_t3, '-.', 'LineWidth', 2.0, 'Color', c_t3, 'DisplayName', 'u3: Celda Hull (18W) [%]');
plot(tiempo_min, u_t4, ':',  'LineWidth', 2.0, 'Color', c_t4, 'DisplayName', 'u4: Níquel Watts (450W) [%]');

ylabel('Potencia TRIAC (%)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
title('⚡ 2. Esfuerzo de Control u(t) de Actuadores TRIAC BTA24 (Dimmer AC 60Hz)', ...
      'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);
ylim([-5, 105]);

% --- SUBPLOT 3: Corriente Galvánica del Sumidero VCSS ---
sp1_3 = subplot(3, 1, 3);
hold on; grid on; box on;
set(sp1_3, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], 'YColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

% Área sombreada bajo la curva de corriente real
area(tiempo_min, i_real, 'FaceColor', c_i, 'FaceAlpha', 0.22, ...
     'EdgeColor', c_i, 'LineWidth', 1.8, 'DisplayName', 'Corriente Real Medida I_{real} (A)');

if hay_itarget && any(i_target > 0)
    plot(tiempo_min, i_target, '--', 'LineWidth', 1.5, 'Color', [0.08, 0.45, 0.20], ...
         'DisplayName', 'Consigna Target I_{sp} (A)');
end

if hay_sh1 && any(i_shunt1 > 0)
    plot(tiempo_min, i_shunt1, ':', 'LineWidth', 1.4, 'Color', [0.00, 0.45, 0.74], ...
         'DisplayName', 'Rama Shunt 1 (R1)');
end

if hay_sh2 && any(i_shunt2 > 0)
    plot(tiempo_min, i_shunt2, '-.', 'LineWidth', 1.4, 'Color', [0.55, 0.20, 0.75], ...
         'DisplayName', 'Rama Shunt 2 (R2)');
end

ylabel('Corriente (A)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
xlabel('Tiempo de Proceso (minutos)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
title('🔬 3. Perfil de Corriente Galvánica del Sumidero VCSS (ADS1115 + Doble Shunt)', ...
      'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);
i_max_val = max([max(i_real, [], 'omitnan'), max(i_target, [], 'omitnan'), 1.8]);
if isnan(i_max_val), i_max_val = 2.0; end
ylim([0, i_max_val * 1.25]);

% Sincronizar zoom horizontal entre subplots
linkaxes([sp1_1, sp1_2, sp1_3], 'x');
xlim([0, max([tiempo_min(end) * 1.02, 0.1])]);


%% =========================================================================
%% FIGURA 2: MONITOREO ELECTROQUÍMICO, CULOMBIMETRÍA Y AMBIENTE (3 PANELES)
%% =========================================================================
fig2 = figure('Name', 'Figura 2: Monitoreo Electroquímico y Ambiental', ...
              'Color', [1 1 1], 'Position', [120, 70, 1150, 880], ...
              'NumberTitle', 'off');

% --- SUBPLOT 1: Monitoreo de pH Dual (Tina 1 Zinc vs Tina 2 Níquel) ---
sp2_1 = subplot(3, 1, 1);
hold on; grid on; box on;
set(sp2_1, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], 'YColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

% Bandas sombreadas de pH óptimo según literatura galvánica
t_extremo = [0, max([tiempo_min(end) * 1.02, 0.1])];
fill([t_extremo, fliplr(t_extremo)], [2.0, 2.0, 4.0, 4.0], [0.88, 0.95, 1.00], ...
     'EdgeColor', 'none', 'DisplayName', 'Rango Óptimo Zincado (pH 2.0 - 4.0)');
fill([t_extremo, fliplr(t_extremo)], [4.5, 4.5, 5.5, 5.5], [0.96, 0.91, 1.00], ...
     'EdgeColor', 'none', 'DisplayName', 'Rango Óptimo Níquel Watts (pH 4.5 - 5.5)');

if hay_ph1 && any(~isnan(ph1))
    plot(tiempo_min, ph1, '-', 'LineWidth', 2.2, 'Color', c_ph1, ...
         'DisplayName', sprintf('pH Tina 1: Zincado (Media: %.2f)', mean(ph1, 'omitnan')));
end
if hay_ph2 && any(~isnan(ph2))
    plot(tiempo_min, ph2, '-', 'LineWidth', 2.2, 'Color', c_ph2, ...
         'DisplayName', sprintf('pH Tina 2: Níquel Watts (Media: %.2f)', mean(ph2, 'omitnan')));
end

ylabel('Potencial de Hidrógeno (pH)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
title(sprintf('🧪 1. Monitoreo de pH Dual en Línea (Sondas de Vidrio con Aislamiento Galvánico)%s', subtitulo_id), ...
      'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);
ylim([1.0, 8.0]);

% --- SUBPLOT 2: Culombimetría de Proceso Q(t) y Masa Teórica Faraday ---
sp2_2 = subplot(3, 1, 2);
hold on; grid on; box on;
set(sp2_2, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

yyaxis left
sp2_2.YAxis(1).Color = [0.02, 0.52, 0.78];
area(tiempo_min, q_coulombs, 'FaceColor', [0.02, 0.52, 0.78], 'FaceAlpha', 0.22, ...
     'EdgeColor', [0.02, 0.52, 0.78], 'LineWidth', 1.8, 'DisplayName', 'Carga Acumulada Q(t) [C]');
ylabel('Carga Eléctrica Q (Coulombs)', 'FontWeight', 'bold');
q_final = q_coulombs(end);
if isnan(q_final), q_final = 0.0; end
ylim([0, max([q_final * 1.25, 10.0])]);

yyaxis right
sp2_2.YAxis(2).Color = [0.85, 0.45, 0.05];
plot(tiempo_min, m_faraday, '--', 'LineWidth', 2.0, 'Color', [0.85, 0.45, 0.05], ...
     'DisplayName', sprintf('Masa Faraday m_{teo}(t) [Final = %.2f mg]', m_faraday(end)));
ylabel('Masa Teórica Faraday (mg)', 'FontWeight', 'bold');
m_final = m_faraday(end);
if isnan(m_final), m_final = 0.0; end
ylim([0, max([m_final * 1.25, 5.0])]);

title(sprintf('⚖️ 2. Culombimetría y Electrodeposición: Q_{total} = %.1f C (%.2f mAh) | m_{teo} = %.2f mg', ...
      q_final, (q_final/3600.0)*1000.0, m_final), 'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);

% --- SUBPLOT 3: Condiciones Meteorológicas Ambientales (AHT20/BMP280) ---
sp2_3 = subplot(3, 1, 3);
hold on; grid on; box on;
set(sp2_3, 'Color', [1 1 1], 'XColor', [0.15 0.15 0.15], ...
           'GridColor', [0.75 0.75 0.75], 'GridAlpha', 0.45, 'FontSize', 10, 'LineWidth', 1.1);

yyaxis left
sp2_3.YAxis(1).Color = [0.85, 0.15, 0.15];
if hay_tamb && any(~isnan(t_amb))
    plot(tiempo_min, t_amb, '-', 'LineWidth', 2.0, 'Color', [0.85, 0.15, 0.15], ...
         'DisplayName', sprintf('Temp Ambiente (%.1f ± %.2f °C)', mean(t_amb, 'omitnan'), std(t_amb, 'omitnan')));
else
    plot(tiempo_min, 24.0*ones(size(tiempo_min)), ':', 'LineWidth', 1.2, 'Color', [0.85, 0.15, 0.15], ...
         'DisplayName', 'Temp Ambiente Nominal (24.0°C)');
end
ylabel('Temperatura Ambiente (°C)', 'FontWeight', 'bold');
ylim([15, 40]);

yyaxis right
sp2_3.YAxis(2).Color = [0.05, 0.50, 0.85];
if hay_hamb && any(~isnan(h_amb))
    plot(tiempo_min, h_amb, '--', 'LineWidth', 2.0, 'Color', [0.05, 0.50, 0.85], ...
         'DisplayName', sprintf('Humedad Relativa (%.1f ± %.2f %%)', mean(h_amb, 'omitnan'), std(h_amb, 'omitnan')));
else
    plot(tiempo_min, 55.0*ones(size(tiempo_min)), ':', 'LineWidth', 1.2, 'Color', [0.05, 0.50, 0.85], ...
         'DisplayName', 'Humedad Nominal (55.0%)');
end
ylabel('Humedad Relativa (%)', 'FontWeight', 'bold');
ylim([20, 95]);

xlabel('Tiempo de Proceso (minutos)', 'FontWeight', 'bold', 'Color', [0.12 0.12 0.12]);
title('🌤️ 3. Monitoreo de Condiciones Ambientales de Laboratorio (Sensor I2C AHT20/BMP280)', ...
      'FontSize', 11.5, 'FontWeight', 'bold', 'Color', [0.1 0.1 0.1]);
legend('Location', 'eastoutside', 'FontSize', 8, 'Box', 'on', ...
       'Color', [1 1 1], 'TextColor', [0.12 0.12 0.12], 'EdgeColor', [0.8 0.8 0.8]);

linkaxes([sp2_1, sp2_2, sp2_3], 'x');
xlim([0, max([tiempo_min(end) * 1.02, 0.1])]);


%% =========================================================================
%% 5. EXPORTACIÓN EN ALTA RESOLUCIÓN PARA MEMORIA DE TESIS (300 DPI)
%% =========================================================================
[directorio_csv, nombre_base, ~] = fileparts(ruta_completa);
if isempty(directorio_csv), directorio_csv = pwd; end

% Crear subcarpeta de gráficas si no existe
carpeta_export = fullfile(directorio_csv, 'graficas_matlab');
if ~isfolder(carpeta_export)
    try
        mkdir(carpeta_export);
    catch
        carpeta_export = directorio_csv;
    end
end

ruta_fig1 = fullfile(carpeta_export, sprintf('%s_01_proceso_termico_potencia.png', nombre_base));
ruta_fig2 = fullfile(carpeta_export, sprintf('%s_02_electroquimica_ambiente.png', nombre_base));

fprintf('\n💾 Exportando figuras científicas en alta resolución (300 DPI)...\n');
try
    exportgraphics(fig1, ruta_fig1, 'Resolution', 300, 'BackgroundColor', 'white');
    fprintf('   ✅ [1/2] Figura de Proceso exportada: %s\n', ruta_fig1);
catch ME1
    try
        print(fig1, ruta_fig1, '-dpng', '-r300');
        fprintf('   ✅ [1/2] Figura de Proceso exportada (modo print): %s\n', ruta_fig1);
    catch
        warning('No se pudo exportar Figura 1 automáticamente: %s', ME1.message);
    end
end

try
    exportgraphics(fig2, ruta_fig2, 'Resolution', 300, 'BackgroundColor', 'white');
    fprintf('   ✅ [2/2] Figura de Electroquímica y Ambiente exportada: %s\n', ruta_fig2);
catch ME2
    try
        print(fig2, ruta_fig2, '-dpng', '-r300');
        fprintf('   ✅ [2/2] Figura de Electroquímica exportada (modo print): %s\n', ruta_fig2);
    catch
        warning('No se pudo exportar Figura 2 automáticamente: %s', ME2.message);
    end
end

fprintf('\n🎯 Resumen del Ensayo Procesado:\n');
fprintf('   • Duración Total: %.2f minutos (%.0f s | %d muestras)\n', tiempo_min(end), tiempo_s(end), n_filas);
fprintf('   • Columna de Corriente Identificada: "%s"\n', col_ireal);
fprintf('   • Carga Eléctrica Q Total: %.1f Coulombs (%.3f Ah)\n', q_final, q_final/3600.0);
fprintf('   • Masa Faradaica Teórica Estimada: %.2f mg\n', m_final);
fprintf('   • Temperatura Máxima Registrada: %.1f °C\n', y_max_t);
fprintf('=========================================================================\n\n');


%% =========================================================================
%% FUNCIONES AUXILIARES INTERNAS
%% =========================================================================
function [columna_val, encontrada, nombre_real] = obtener_columna(tabla, lista_alias, valor_defecto, n_filas)
    % Busca de forma insensible a mayúsculas/minúsculas y espacios entre una
    % lista priorizada de nombres posibles de columna en una tabla MATLAB.
    % Retorna el vector numérico limpio y una bandera indicando si se encontró.
    
    encontrada = false;
    nombre_real = '<No encontrada (Valor por defecto)>';
    nombres_tabla = tabla.Properties.VariableNames;
    
    % Normalizar nombres de la tabla (sin espacios ni guiones bajos para matching tolerante)
    norm_tabla = lower(regexprep(nombres_tabla, '[\s_]', ''));
    
    for i = 1:length(lista_alias)
        alias_actual = lista_alias{i};
        norm_alias = lower(regexprep(alias_actual, '[\s_]', ''));
        
        % 1. Búsqueda exacta
        idx = find(strcmp(nombres_tabla, alias_actual), 1);
        
        % 2. Búsqueda normalizada
        if isempty(idx)
            idx = find(strcmp(norm_tabla, norm_alias), 1);
        end
        
        % 3. Búsqueda por subcadena si no se encontró
        if isempty(idx)
            idx = find(contains(norm_tabla, norm_alias), 1);
        end
        
        if ~isempty(idx)
            col_raw = tabla.(nombres_tabla{idx(1)});
            nombre_real = nombres_tabla{idx(1)};
            encontrada = true;
            
            % Conversión robusta a vector numérico double
            if isnumeric(col_raw)
                columna_val = double(col_raw(:));
            elseif iscell(col_raw) || isstring(col_raw)
                columna_val = str2double(col_raw(:));
            elseif islogical(col_raw)
                columna_val = double(col_raw(:));
            else
                try
                    columna_val = double(col_raw);
                catch
                    columna_val = NaN(n_filas, 1);
                end
            end
            return;
        end
    end
    
    % Si no se encontró ningún alias en la tabla, asignar valor por defecto
    if isscalar(valor_defecto)
        columna_val = repmat(double(valor_defecto), n_filas, 1);
    else
        columna_val = double(valor_defecto(:));
        if length(columna_val) ~= n_filas
            columna_val = repmat(columna_val(1), n_filas, 1);
        end
    end
end

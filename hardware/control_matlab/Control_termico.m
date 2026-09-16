%% ========================================================================= %
%   OPTIMIZACIÓN DE COEFICIENTES PI - LÍNEA DE ELECTRODEPOSICIÓN (UdeG)     %
% ========================================================================= %
clear; clc; close all;

%% 1. PARÁMETROS GLOBALES Y CONSTANTES (BASE AGUA PURA)
T_amb = 25.0;         % Temperatura ambiente inicial (°C)
rho_agua = 1.0;       % Densidad del agua (kg/L)
cp_agua = 4184.3;     % Calor específico del agua (J/kgK)
h_efectivo = 65.0;    % Coeficiente de convección por burbujeo (W/m^2K)
f_red = 60;           % Frecuencia de la red eléctrica en Guadalajara (Hz)

%% 2. CONFIGURACIÓN GEOMÉTRICA Y TÉRMICA POR TINA
% Tina 1: Desengrase Alcalino (Punto medio de operación: 90°C)
tinas(1).nombre   = 'Desengrase Alcalino';
tinas(1).volumen  = 1.0;      % Volumen real (Litros)
tinas(1).A_s      = 0.0470;    % Área real de disipación activa (m^2)
tinas(1).P_max    = 450.0;     % Watts
tinas(1).retardo  = 6.0;       % Segundos de retraso (Resistencia encapsulada)
tinas(1).T_set    = 90.0;      % °C

% Tina 2: Decapado Ácido (Punto medio de operación: 90°C)
tinas(2).nombre   = 'Decapado Ácido';
tinas(2).volumen  = 1.0;      % Volumen real (Litros)
tinas(2).A_s      = 0.0470;    % Área real de disipación activa (m^2)
tinas(2).P_max    = 450.0;     % Watts
tinas(2).retardo  = 6.0;       % Segundos de retraso
tinas(2).T_set    = 90.0;      % °C

% Tina 3: Niquelado (Temperatura de operación: 30°C)
tinas(3).nombre   = 'Niquelado';
tinas(3).volumen  = 1.0;      % Volumen real (Litros)
tinas(3).A_s      = 0.0470;    % Área real de disipación activa (m^2)
tinas(3).P_max    = 450.0;     % Watts
tinas(3).retardo  = 6.0;       % Segundos de retraso
tinas(3).T_set    = 30.0;      % °C

% Tina 4: Celda Hull - Zincado Ácido (Volumen asimétrico de fábrica)
tinas(4).nombre   = 'Celda Hull (Zinc)';
tinas(4).volumen  = 0.267;    % Volumen exacto del prisma trapezoidal (Litros)
tinas(4).A_s      = 0.0210;    % Área de transferencia del acrílico disipando (m^2)
tinas(4).P_max    = 18.0;      % Watts (Resistencia integrada de fábrica)
tinas(4).retardo  = 3.0;       % Segundos de retraso (Contacto directo optimizado)
tinas(4).T_set    = 30.0;      % °C (Punto medio del DoE)

%% 3. BUCLE DE PROCESAMIENTO E INTERPOLACIÓN DE CONSTANTES PI
clc;
fprintf('// ==================================================================\n');
fprintf('//  SINTONIZACIÓN ANÍTICA PI - RESPUESTA CRÍTICA ANTISOBRETIRO\n');
fprintf('// ==================================================================\n\n');

for i = 1:length(tinas)
    % Parámetros termodinámicos puntuales de la planta actual
    m = tinas(i).volumen * rho_agua; 
    K_planta = 1 / (h_efectivo * tinas(i).A_s); 
    tau_planta = (m * cp_agua) / (h_efectivo * tinas(i).A_s); 
    
    % Modelo dinámico en lazo abierto con aproximación de Padé de orden 2 para el retardo
    s = tf('s');
    G_planta = (K_planta / (tau_planta * s + 1)) * pade(exp(-tinas(i).retardo * s), 2);
    
    % Criterio de sintonización restrictivo enfocado estrictamente en tracking libre de sobretiro
    wc = 0.015; 
    opciones = pidtuneOptions('DesignFocus', 'reference-tracking', 'PhaseMargin', 75);
    
    % Sintonizamos un controlador 'PI' (Fuerza de manera nativa Kd = 0.0)
    C_pi = pidtune(G_planta, 'PI', wc, opciones);
    
    % Extracción de constantes calculadas
    Kp_calc = C_pi.Kp;
    Ki_calc = C_pi.Ki;
    
    % Despliegue de resultados formateados de forma limpia en la consola de MATLAB
    fprintf('// Canal %d: %s (Set: %.1f °C)\n', i-1, tinas(i).nombre, tinas(i).T_set);
    fprintf('// Parámetros: Volumen = %.3f L | Área = %.4f m^2 | Retardo = %.1f s\n', tinas(i).volumen, tinas(i).A_s, tinas(i).retardo);
    fprintf('double Kp_%d = %.4f;\n', i-1, Kp_calc);
    fprintf('double Ki_%d = %.4f;\n', i-1, Ki_calc);
    fprintf('double Kd_%d = 0.0000; // Forzado por estabilidad eléctrica y atenuación de ruido\n\n', i-1);
end

%% 4. GENERACIÓN DE LOOK-UP TABLE ÚNICA (PROPIEDAD GEOMÉTRICA DE ONDA DE 60Hz)
T_medio = (1 / f_red) / 2;
T_us = round(T_medio * 1e6);
alpha_rad = linspace(pi, 0, 5000);
P_norm = 1 - (alpha_rad/pi) + sin(2 * alpha_rad)/(2 * pi);
lut_us = zeros(1, 101);

for p = 0:100
    [~, idx] = min(abs(P_norm * 100 - p));
    lut_us(p + 1) = round((alpha_rad(idx) / pi) * T_us);
end

fprintf('// ==================================================================\n');
fprintf('// LUT DE LINEALIZACIÓN DE DISPARO TRIAC A 60Hz (COMÚN PARA TODAS LAS TINAS)\n');
fprintf('// ==================================================================\n');
fprintf('const uint16_t lut_triac[101] = {\n    ');
for i = 1:101
    fprintf('%4d', lut_us(i));
    if i < 101, fprintf(', '); end
    if mod(i, 10) == 0 && i ~= 101, fprintf('\n    '); end
end
fprintf('\n};\n');
@echo off
chcp 65001 >nul
echo =======================================================
echo   Actualizando Showcase Web y Publicando a GitHub Pages
echo =======================================================
echo.
echo 1. Sincronizando showcase_web -> docs/ y paquete movil...
python herramientas\sincronizar_pages.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Fallo la sincronizacion.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo 2. Agregando archivos al control de versiones...
git add docs/ herramientas/sincronizar_pages.py .github/workflows/

echo.
echo 3. Creando commit de actualizacion web...
git commit -m "chore(pages): sincronizar actualizacion de showcase web"

echo.
echo 4. Subiendo cambios a GitHub (git push origin main)...
git push origin main
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] No se pudo hacer push a GitHub. Revisa tu conexion o permisos.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =======================================================
echo   EXITO: Cambios enviados a GitHub Pages
echo   La pagina estara actualizada en ~30-60 segundos en:
echo   https://chavacastro98.github.io/Proyecto/
echo =======================================================
echo.
pause

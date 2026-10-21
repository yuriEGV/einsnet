@echo off
chcp 65001 >nul
title EinsNet · Actualizador Oficial desde GitHub
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet · Actualización Forzada desde GitHub (yuriEGV/einsnet)
echo    Sede Lynch ⟷ Sede Levarte (12 Cámaras CCTV y Ambos Planos DWG)
echo ======================================================================
echo.

echo [*] Paso 1: Deteniendo procesos del servidor en segundo plano...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *netguard*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

echo [*] Paso 2: Descargando la última versión oficial desde GitHub...
where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    git fetch origin main
    git reset --hard origin/main
    echo.
    echo [OK] Código 100%% actualizado a la última versión (v6.0).
) else (
    echo [ERROR] Git no está instalado o no se encuentra en el PATH.
    echo Por favor asegúrate de tener Git instalado para actualizar automáticamente.
    pause
    exit /b 1
)

echo.
echo [*] Paso 3: Reiniciando el servidor EinsNet en puerto 8000...
python supervisor_einsnet.py --ensure

echo.
echo ======================================================================
echo    ¡SISTEMA ACTUALIZADO CON ÉXITO!
echo    - 12 Cámaras CCTV (4 Lynch + 8 Levarte)
echo    - Planos arquitectónicos interactivos de ambas sedes
echo    - Enlace de red e interconexión inter-sedes
echo ======================================================================
echo.
echo [*] Abriendo EinsNet en tu navegador...
start "" "http://localhost:8000"

timeout /t 4 /nobreak >nul
exit

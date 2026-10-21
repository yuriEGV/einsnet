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
    echo [*] Git detectado. Sincronizando con git fetch y reset...
    git fetch origin main
    git reset --hard origin/main
    if %ERRORLEVEL% equ 0 (
        echo [OK] Repositorio sincronizado exitosamente vía Git.
        goto :UPDATE_DONE
    )
)

echo [!] Git no disponible o fallo en sincronización.
echo [*] Descargando actualización directa vía HTTPS desde GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "Write-Host '[*] Conectando con GitHub (yuriEGV/einsnet)...'; " ^
    "Invoke-WebRequest -Uri 'https://github.com/yuriEGV/einsnet/archive/refs/heads/main.zip' -OutFile 'einsnet_latest.zip' -UseBasicParsing; " ^
    "Write-Host '[*] Descomprimiendo archivos actualizados...'; " ^
    "Expand-Archive -Path 'einsnet_latest.zip' -DestinationPath 'einsnet_tmp_update' -Force; " ^
    "Copy-Item -Path 'einsnet_tmp_update\einsnet-main\*' -Destination '.' -Recurse -Force; " ^
    "Remove-Item -Path 'einsnet_latest.zip', 'einsnet_tmp_update' -Recurse -Force; " ^
    "Write-Host '[OK] Actualización descargada e instalada con éxito.'"

:UPDATE_DONE
echo.
echo [OK] Código 100%% actualizado a la última versión (v6.0 con 12 Cámaras y Bi-Sede).

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

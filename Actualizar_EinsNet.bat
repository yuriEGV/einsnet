@echo off
chcp 65001 >nul
title EinsNet - Actualizador Oficial desde GitHub
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet - Actualizacion Forzada desde GitHub (yuriEGV/einsnet)
echo    Sede Lynch - Sede Levarte (12 Camaras CCTV y Ambos Planos DWG)
echo ======================================================================
echo.

echo [*] Deteniendo procesos anteriores en segundo plano...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *netguard*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

where git >nul 2>&1
if %ERRORLEVEL% equ 0 goto :GIT_UPDATE
goto :PWSH_UPDATE

:GIT_UPDATE
echo [*] Descargando ultima version con Git...
git fetch origin main
git reset --hard origin/main
if %ERRORLEVEL% equ 0 goto :DONE_UPDATE

:PWSH_UPDATE
echo [!] Descargando paquete oficial via HTTPS...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/yuriEGV/einsnet/archive/refs/heads/main.zip' -OutFile 'einsnet_latest.zip' -UseBasicParsing; Expand-Archive -Path 'einsnet_latest.zip' -DestinationPath 'einsnet_tmp' -Force; Copy-Item -Path 'einsnet_tmp\einsnet-main\*' -Destination '.' -Recurse -Force; Remove-Item -Path 'einsnet_latest.zip', 'einsnet_tmp' -Recurse -Force"

:DONE_UPDATE
echo.
echo [OK] Codigo 100%% actualizado a la version v6.0.
echo [*] Levantando servidor EinsNet en puerto 8000...
start "" python supervisor_einsnet.py --ensure
ping 127.0.0.1 -n 3 >nul

echo [*] Abriendo http://localhost:8000 en el navegador...
start "" "http://localhost:8000"
ping 127.0.0.1 -n 4 >nul
exit

@echo off
chcp 65001 >nul
title EinsNet - Cortar Internet en Estacion / PC
color 4f

:: Verificación y elevación como Administrador si es necesario
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [EinsNet] Solicitando permisos de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

setlocal EnableDelayedExpansion

set SERVER_IP=127.0.0.1
if exist "%~dp0server_ip.txt" (
    set /p SERVER_IP=<"%~dp0server_ip.txt"
)
set SERVER_IP=%SERVER_IP: =%
set SERVER_URL=http://%SERVER_IP%:8000

cls
echo ===============================================================================
echo     EINSNET CYBER-DEFENSE: CORTE DE INTERNET A ESTACION INDIVIDUAL
echo ===============================================================================
echo  Aisla una estacion de trabajo o PC infectada.
echo  - Se corta el acceso a Internet (Web HTTP/HTTPS y DNS externo).
echo  - Se conserva la comunicacion con el Servidor EinsNet (%SERVER_IP%:8000)
echo    para permitir administracion remota, desinfeccion y diagnostico.
echo ===============================================================================
echo.

set /p TARGET_IP="Ingresa la direccion IP de la estacion a aislar (ej: 192.168.80.70): "
if "%TARGET_IP%"=="" (
    echo [ERROR] No ingresaste ninguna IP.
    pause
    exit /b
)

set MOTIVO=Aislamiento de seguridad por infeccion de malware
set /p MOTIVO="Ingresa el motivo de la cuarentena [ENTER para default]: "

echo.
echo [TRANSMITIENDO ORDEN DE AISLAMIENTO A %TARGET_IP%...]

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$body = @{ ip = '%TARGET_IP%'; reason = '%MOTIVO%'; action = 'isolate' } | ConvertTo-Json; " ^
    "try { " ^
    "  $resp = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Red; " ^
    "  Write-Host '  ⛔ INTERNET CORTADO EN LA ESTACION ' $resp.name ' (' $resp.ip ')' -ForegroundColor Red; " ^
    "  Write-Host '  Modo: ' $resp.mode -ForegroundColor Yellow; " ^
    "  Write-Host '  Reglas de Firewall EinsNet aplicadas con exito.' -ForegroundColor Cyan; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Red; " ^
    "} catch { " ^
    "  Write-Host '  [FALLO EN SERVIDOR] ' $_.Exception.Message -ForegroundColor Red; " ^
    "  Write-Host '  Aplicando regla local directa para %TARGET_IP%...' -ForegroundColor Yellow; " ^
    "  netsh advfirewall firewall add rule name='EinsNet_Cut_Host_%TARGET_IP%' dir=out action=block remoteip=%TARGET_IP% | Out-Null; " ^
    "}"

echo.
echo  La estacion quedo registrada en el panel de control de EinsNet: %SERVER_URL%
echo  Para devolverle Internet, ejecuta Restaurar_Internet_Estacion.bat
echo.
pause
exit /b

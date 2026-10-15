@echo off
chcp 65001 >nul
title EinsNet - Restaurar Internet en Estacion / PC
color 2f

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
echo     EINSNET CYBER-DEFENSE: RESTAURAR INTERNET EN ESTACION INDIVIDUAL
echo ===============================================================================
echo  Levanta el aislamiento en la estacion, elimina las reglas de firewall
echo  y restaura la navegacion Web y conectividad completa.
echo  Servidor Activo: %SERVER_URL%
echo ===============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { " ^
    "  $status = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/status' -TimeoutSec 5; " ^
    "  $isolated = $status.isolated_hosts; " ^
    "  $keys = $isolated.psobject.properties.name; " ^
    "  if ($keys.Count -eq 0) { " ^
    "    Write-Host '  🟢 No hay estaciones individuales aisladas actualmente.' -ForegroundColor Green; " ^
    "  } else { " ^
    "    Write-Host '  ⛔ Estaciones en Cuarentena (Sin Internet):' -ForegroundColor Red; " ^
    "    foreach ($k in $keys) { " ^
    "      $item = $isolated.$k; " ^
    "      Write-Host '   - ' $k ' (' $item.name ') | Motivo: ' $item.reason -ForegroundColor Yellow; " ^
    "    } " ^
    "  } " ^
    "} catch { " ^
    "  Write-Host '  [AVISO] No se pudo conectar con %SERVER_URL%' -ForegroundColor Yellow; " ^
    "}"

echo.
set /p TARGET_IP="Ingresa la direccion IP de la estacion a restaurar: "
if "%TARGET_IP%"=="" (
    echo [ERROR] No ingresaste ninguna IP.
    pause
    exit /b
)

echo.
echo [TRANSMITIENDO ORDEN DE RESTAURACION A %TARGET_IP%...]

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$body = @{ ip = '%TARGET_IP%'; reason = 'Desinfeccion y trabajo completado'; action = 'restore' } | ConvertTo-Json; " ^
    "try { " ^
    "  $resp = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Green; " ^
    "  Write-Host '  🟢 INTERNET RESTAURADO EN LA ESTACION ' $resp.name ' (' $resp.ip ')' -ForegroundColor Green; " ^
    "  Write-Host '  Reglas de Firewall EinsNet eliminadas con exito.' -ForegroundColor Cyan; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Green; " ^
    "} catch { " ^
    "  Write-Host '  [FALLO EN SERVIDOR] ' $_.Exception.Message -ForegroundColor Red; " ^
    "} " ^
    "netsh advfirewall firewall delete rule name='EinsNet_Cut_Host_%TARGET_IP%' 2>$null | Out-Null"

echo.
pause
exit /b

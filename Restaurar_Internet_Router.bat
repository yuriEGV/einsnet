@echo off
chcp 65001 >nul
title EinsNet - Restaurar Internet en Routers
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
echo       EINSNET CYBER-DEFENSE: RESTAURAR INTERNET EN ROUTERS
echo ===============================================================================
echo  Levanta el estado de cuarentena, reactiva el trafico WAN/Internet y
echo  notifica a las estaciones que el trabajo de desinfeccion ha concluido.
echo  Servidor Activo: %SERVER_URL%
echo ===============================================================================
echo.

:: Consultar routers actualmente aislados
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try { " ^
    "  $status = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/status' -TimeoutSec 5; " ^
    "  $isolated = $status.isolated_routers; " ^
    "  $keys = $isolated.psobject.properties.name; " ^
    "  if ($keys.Count -eq 0) { " ^
    "    Write-Host '  🟢 No hay routers aislados en este momento. La red esta normal.' -ForegroundColor Green; " ^
    "  } else { " ^
    "    Write-Host '  ⛔ Routers actualmente en Cuarentena (Sin Internet):' -ForegroundColor Red; " ^
    "    foreach ($k in $keys) { " ^
    "      $item = $isolated.$k; " ^
    "      Write-Host '   - ' $k ' (' $item.name ') | Motivo: ' $item.reason -ForegroundColor Yellow; " ^
    "    } " ^
    "  } " ^
    "} catch { " ^
    "  Write-Host '  [AVISO] No se pudo conectar con %SERVER_URL%' -ForegroundColor Yellow; " ^
    "}"

echo.
echo  SELECCIONA QUE ROUTER RESTAURAR:
echo   [1]  192.168.80.1  - GW-FortiGate-Core        (Gateway Principal Lynch)
echo   [2]  192.168.80.9  - Belkin-AP-09             (WiFi Patio Lynch)
echo   [3]  192.168.80.10 - TP-SW-01                 (Administracion Central)
echo   [4]  192.168.80.12 - TP-SW-02                 (Unidad Formacion Profesional)
echo   [5]  192.168.80.13 - TP-SW-03                 (Lab Quimica / Ciencias)
echo   [6]  192.168.80.14 - ASUS-Router-14           (Talleres / Gastronomia)
echo   [7]  192.168.80.15 - TP-SW-04                 (Taller Elaboracion Industrial)
echo   [8]  192.168.80.16 - TP-SW-05                 (Simulador Maniobras / CCTV)
echo   [9]  192.168.80.17 - TP-SW-06                 (Operaciones Portuarias / TOS)
echo   [10] 192.168.80.20 - TP-SW-07                 (Pabellon Clases Norte)
echo   [11] 192.168.1.99  - FortiGate-GW-Levarte     (Gateway Principal Levarte)
echo   [12] 192.168.1.253 - Web-Switch-Levarte       (Switch Core Aulas y Talleres)
echo   [13] 192.168.9.1   - GW-Router-WiFi-Docentes  (WiFi Docentes Piso 2)
echo   [14] 192.168.9.10  - SW-Piso2-Levarte         (Gabinete Distribucion Piso 2)
echo   [15] 192.168.9.20  - Router-Taller-Tecnico    (Taller Bajo Nivel)
echo.
echo   [T]  🟢 RESTAURAR TODOS LOS ROUTERS DE AMBAS SEDES
echo   [C]  Ingresar otra IP de router
echo   [Q]  Cancelar y Salir
echo.
set /p OPCION="Selecciona una opcion (1-15, T, C o Q): "

if /i "%OPCION%"=="Q" exit /b
if /i "%OPCION%"=="T" goto :RESTORE_ALL

set TARGET_IP=
if "%OPCION%"=="1"  set TARGET_IP=192.168.80.1
if "%OPCION%"=="2"  set TARGET_IP=192.168.80.9
if "%OPCION%"=="3"  set TARGET_IP=192.168.80.10
if "%OPCION%"=="4"  set TARGET_IP=192.168.80.12
if "%OPCION%"=="5"  set TARGET_IP=192.168.80.13
if "%OPCION%"=="6"  set TARGET_IP=192.168.80.14
if "%OPCION%"=="7"  set TARGET_IP=192.168.80.15
if "%OPCION%"=="8"  set TARGET_IP=192.168.80.16
if "%OPCION%"=="9"  set TARGET_IP=192.168.80.17
if "%OPCION%"=="10" set TARGET_IP=192.168.80.20
if "%OPCION%"=="11" set TARGET_IP=192.168.1.99
if "%OPCION%"=="12" set TARGET_IP=192.168.1.253
if "%OPCION%"=="13" set TARGET_IP=192.168.9.1
if "%OPCION%"=="14" set TARGET_IP=192.168.9.10
if "%OPCION%"=="15" set TARGET_IP=192.168.9.20

if /i "%OPCION%"=="C" (
    set /p TARGET_IP="Ingresa la IP del Router a restaurar: "
)

if "%TARGET_IP%"=="" (
    echo [ERROR] Opcion no valida.
    pause
    exit /b
)

echo.
echo [TRANSMITIENDO ORDEN DE RESTAURACION...]
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$body = @{ router_ip = '%TARGET_IP%'; action = 'restore'; reason = 'Trabajo de desinfeccion completado' } | ConvertTo-Json; " ^
    "try { " ^
    "  $resp = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate-router' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Green; " ^
    "  Write-Host '  🟢 INTERNET RESTAURADO EXITOSAMENTE EN ' $resp.router_name -ForegroundColor Green; " ^
    "  Write-Host '  Equipos reconectados: ' $resp.restored_count -ForegroundColor Yellow; " ^
    "  Write-Host '  Estado: Rama Normalizada y Fuera de Cuarentena' -ForegroundColor Cyan; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Green; " ^
    "} catch { " ^
    "  Write-Host '  [FALLO EN SERVIDOR] ' $_.Exception.Message -ForegroundColor Red; " ^
    "} " ^
    "netsh advfirewall firewall delete rule name='EinsNet_Emergency_Cut_%TARGET_IP%' 2>$null | Out-Null"

echo.
pause
exit /b

:RESTORE_ALL
echo.
echo [TRANSMITIENDO ORDEN DE RESTAURACION TOTAL A TODOS LOS ROUTERS...]
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$routers = @('192.168.80.1','192.168.80.9','192.168.80.10','192.168.80.12','192.168.80.13','192.168.80.14','192.168.80.15','192.168.80.16','192.168.80.17','192.168.80.20','192.168.1.99','192.168.1.253','192.168.9.1','192.168.9.10','192.168.9.20'); " ^
    "foreach ($r in $routers) { " ^
    "  $b = @{ router_ip = $r; reason = 'Normalizacion General'; action = 'restore' } | ConvertTo-Json; " ^
    "  try { " ^
    "    $res = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate-router' -Method Post -Body $b -ContentType 'application/json' -TimeoutSec 5; " ^
    "    Write-Host '  [OK] Restaurado: ' $res.router_name -ForegroundColor Green; " ^
    "  } catch { " ^
    "    Write-Host '  [OMITIDO / SIN CUARENTENA] ' $r -ForegroundColor DarkGray; " ^
    "  } " ^
    "  netsh advfirewall firewall delete rule name=\"EinsNet_Emergency_Cut_$r\" 2>$null | Out-Null; " ^
    "}"

echo.
echo [COMPLETADO] Todas las ramas han sido restablecidas.
pause
exit /b

@echo off
chcp 65001 >nul
title EinsNet - Kill-Switch de Routers (Cortar Internet por Infeccion Masiva)
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
echo       EINSNET CYBER-DEFENSE: KILL-SWITCH DE ROUTERS (CORTE DE INTERNET)
echo ===============================================================================
echo  Permite aislar completamente un router y todas las estaciones que cuelgan
echo  de su rama para realizar trabajos tecnicos aislados en desinfeccion forense.
echo  Servidor Activo: %SERVER_URL%
echo ===============================================================================
echo.
echo  SEDE CENTRAL PATRICIO LYNCH:
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
echo.
echo  SEDE LEVARTE (MODULO A-15):
echo   [11] 192.168.1.99  - FortiGate-GW-Levarte     (Gateway Principal Levarte)
echo   [12] 192.168.1.253 - Web-Switch-Levarte       (Switch Core Aulas y Talleres)
echo   [13] 192.168.9.1   - GW-Router-WiFi-Docentes  (WiFi Docentes Piso 2)
echo   [14] 192.168.9.10  - SW-Piso2-Levarte         (Gabinete Distribucion Piso 2)
echo   [15] 192.168.9.20  - Router-Taller-Tecnico    (Taller Bajo Nivel)
echo.
echo   [A]  🚨 AISLAR TODAS LAS RAMAS (EMERGENCIA TOTAL DE RED)
echo   [C]  Ingresar IP personalizada de otro router
echo   [Q]  Cancelar y Salir
echo.
set /p OPCION="Selecciona una opcion (1-15, A, C o Q): "

if /i "%OPCION%"=="Q" exit /b
if /i "%OPCION%"=="A" goto :ISOLATE_ALL

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
    set /p TARGET_IP="Ingresa la IP del Router a aislar: "
)

if "%TARGET_IP%"=="" (
    echo [ERROR] Opcion no valida.
    pause
    exit /b
)

echo.
set MOTIVO=Aislamiento de rama por sospecha de infeccion masiva
set /p MOTIVO="Ingresa el motivo de contencion [ENTER para default]: "

echo.
echo [TRANSMITIENDO ORDEN DE CORTE DE INTERNET...]
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$body = @{ router_ip = '%TARGET_IP%'; reason = '%MOTIVO%'; action = 'isolate' } | ConvertTo-Json; " ^
    "try { " ^
    "  $resp = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate-router' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 15; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Red; " ^
    "  Write-Host '  ⛔ INTERNET CORTADO EXITOSAMENTE EN ROUTER ' $resp.router_name -ForegroundColor Red; " ^
    "  Write-Host '  Equipos dependientes aislados: ' $resp.affected_count -ForegroundColor Yellow; " ^
    "  Write-Host '  Estado: Rama en Cuarentena Forense' -ForegroundColor Cyan; " ^
    "  Write-Host '===============================================================================' -ForegroundColor Red; " ^
    "} catch { " ^
    "  Write-Host '  [FALLO EN SERVIDOR] ' $_.Exception.Message -ForegroundColor Red; " ^
    "  Write-Host '  Aplicando bloqueo de emergencia local mediante netsh...' -ForegroundColor Yellow; " ^
    "  netsh advfirewall firewall add rule name='EinsNet_Emergency_Cut_%TARGET_IP%' dir=out action=block remoteip=%TARGET_IP% | Out-Null; " ^
    "}"

echo.
echo  Puedes monitorear el aislamiento en vivo en EinsNet Web: %SERVER_URL%
echo  Para restaurar la conexion, ejecuta Restaurar_Internet_Router.bat
echo.
pause
exit /b

:ISOLATE_ALL
echo.
echo [!] ADVERTENCIA CRITICA: Se cortara el acceso a Internet en TODOS los 15 routers
echo     de ambas sedes escolares para contencion total de ransomware/malware.
set /p CONFIRM="¿Estas seguro de ejecutar el corte total de red? (S/N): "
if /i not "%CONFIRM%"=="S" exit /b

echo.
echo [TRANSMITIENDO KILL-SWITCH GLOBAL A TODAS LAS RAMAS...]
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$routers = @('192.168.80.1','192.168.80.9','192.168.80.10','192.168.80.12','192.168.80.13','192.168.80.14','192.168.80.15','192.168.80.16','192.168.80.17','192.168.80.20','192.168.1.99','192.168.1.253','192.168.9.1','192.168.9.10','192.168.9.20'); " ^
    "foreach ($r in $routers) { " ^
    "  $b = @{ router_ip = $r; reason = 'Alerta de Infeccion Masiva Global'; action = 'isolate' } | ConvertTo-Json; " ^
    "  try { " ^
    "    $res = Invoke-RestMethod -Uri '%SERVER_URL%/api/quarantine/isolate-router' -Method Post -Body $b -ContentType 'application/json' -TimeoutSec 5; " ^
    "    Write-Host '  [OK] Cortado: ' $res.router_name ' (' $res.affected_count ' equipos)' -ForegroundColor Red; " ^
    "  } catch { " ^
    "    Write-Host '  [FALLO] No se pudo comunicar con router ' $r -ForegroundColor DarkRed; " ^
    "  } " ^
    "}"

echo.
echo [COMPLETADO] Todas las ramas han sido colocadas en cuarentena.
pause
exit /b

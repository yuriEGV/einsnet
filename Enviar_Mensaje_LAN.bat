@echo off
chcp 65001 >nul
title EinsNet · Emisor de Mensajes y Alertas LAN (Puerto 8000)
cd /d "%~dp0"

set "SERVER_IP=192.168.80.22"
set "SERVER_PORT=8000"
if exist "%~dp0server_ip.txt" (
    set /p SERVER_IP=<"%~dp0server_ip.txt"
)

:MENU
cls
echo ======================================================================
echo    EinsNet · Centro de Despacho de Mensajes y Alertas LAN
echo    Servidor Activo: http://%SERVER_IP%:%SERVER_PORT%
echo ======================================================================
echo.
echo   [1] Enviar Mensaje a TODAS las Sedes y Equipos (Broadcast)
echo   [2] Enviar Mensaje a un Equipo Específico (por IP)
echo   [3] Enviar Alerta de EMERGENCIA (Con Alarma y Voz Sintética)
echo   [4] Ver Equipos y Agentes Conectados en Tiempo Real
echo   [5] Probar Conectividad con el Servidor
echo   [6] Salir
echo.
set /p Opcion="Selecciona una opción [1-6]: "

if "%Opcion%"=="1" goto BROADCAST
if "%Opcion%"=="2" goto UNICAST
if "%Opcion%"=="3" goto EMERGENCIA
if "%Opcion%"=="4" goto VER_AGENTES
if "%Opcion%"=="5" goto PROBAR_SERVER
if "%Opcion%"=="6" exit
goto MENU

:BROADCAST
cls
echo ======================================================================
echo   [1] Enviar Mensaje a TODAS las Sedes y Equipos (Broadcast)
echo ======================================================================
echo.
set /p Titulo="Título del Aviso (Ej: Reunión Docente): "
if "%Titulo%"=="" set "Titulo=Aviso del Administrador de Red"
set /p Mensaje="Escribe el Mensaje: "
if "%Mensaje%"=="" goto MENU

echo.
echo [*] Transmitiendo a la red por Canal HTTP Dual y UDP Broadcast (8888)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$body = @{ title = '%Titulo%'; message = '%Mensaje%'; target_ips = @('*'); preset = 'info' } | ConvertTo-Json; try { $res = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/broadcast-emergency' -Method Post -ContentType 'application/json' -Body $body; Write-Host '[OK] Mensaje transmitido con éxito!' -ForegroundColor Green } catch { Write-Host '[!] Error al conectar con el servidor: ' $_.Exception.Message -ForegroundColor Red }"
echo.
pause
goto MENU

:UNICAST
cls
echo ======================================================================
echo   [2] Enviar Mensaje a un Equipo Específico (por IP)
echo ======================================================================
echo.
echo Ejemplos de IPs habituales:
echo   - 192.168.80.70  (Puesto Gio)
echo   - 192.168.80.22  (maritimo Admin)
echo   - 192.168.1.111  (SubDirección)
echo   - 192.168.1.115  (Inspectoría General)
echo   - 192.168.1.125  (Coordinación Pedagógica)
echo   - 192.168.1.119  (Sala de Profesores)
echo.
set /p TargetIP="Ingresa la IP de destino: "
if "%TargetIP%"=="" goto MENU
set /p Titulo="Título del Aviso: "
if "%Titulo%"=="" set "Titulo=Aviso del Administrador"
set /p Mensaje="Escribe el Mensaje para %TargetIP%: "
if "%Mensaje%"=="" goto MENU

echo.
echo [*] Transmitiendo mensaje directo a %TargetIP%...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$body = @{ ip = '%TargetIP%'; title = '%Titulo%'; message = '%Mensaje%'; name = 'Admin (%COMPUTERNAME%)' } | ConvertTo-Json; try { $res = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/send-message' -Method Post -ContentType 'application/json' -Body $body; Write-Host '[OK] Mensaje entregado a %TargetIP%' -ForegroundColor Green } catch { Write-Host '[!] Fallo al entregar: ' $_.Exception.Message -ForegroundColor Red }"
echo.
pause
goto MENU

:EMERGENCIA
cls
echo ======================================================================
echo   [3] ALERTA DE EMERGENCIA GENERAL (Sirena + Voz Sintética)
echo ======================================================================
echo.
echo PRECAUCIÓN: Esta alerta sonará en voz alta en todas las salas conectadas.
set /p Mensaje="Motivo de la Emergencia (Ej: Evacuación Inmediata por Sismo / Fuego): "
if "%Mensaje%"=="" set "Mensaje=ALERTA DE SEGURIDAD ESCOLAR: Proceda a evacuar las instalaciones de inmediato."

echo.
echo [*] Activando protocolo de emergencia en ambas sedes...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$body = @{ title = '🚨 ALERTA DE EMERGENCIA ESCOLAR'; message = '%Mensaje%'; target_ips = @('*'); preset = 'emergency' } | ConvertTo-Json; try { $res = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/broadcast-emergency' -Method Post -ContentType 'application/json' -Body $body; Write-Host '[OK] Protocolo de Emergencia Activado en toda la red!' -ForegroundColor Green } catch { Write-Host '[!] Error al emitir emergencia: ' $_.Exception.Message -ForegroundColor Red }"
echo.
pause
goto MENU

:VER_AGENTES
cls
echo ======================================================================
echo   [4] Equipos y Agentes Conectados al Servidor EinsNet
echo ======================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $st = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/status'; Write-Host ('[*] Estado Servidor: ' + $st.status + ' | Equipos en Linea: ' + $st.online_devices_count + ' | Agentes: ' + $st.active_agents_count) -ForegroundColor Cyan; Write-Host ''; $ag = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/agents'; if ($ag.agents) { $ag.agents.PSObject.Properties | ForEach-Object { Write-Host (' - ' + $_.Value.ip + ' [' + $_.Value.hostname + '] - ' + $_.Value.last_seen) -ForegroundColor Green } } else { Write-Host '[!] No hay agentes registrados aun.' -ForegroundColor Yellow } } catch { Write-Host '[!] No se pudo conectar con http://%SERVER_IP%:%SERVER_PORT%' -ForegroundColor Red }"
echo.
pause
goto MENU

:PROBAR_SERVER
cls
echo ======================================================================
echo   [5] Probar Conectividad con el Servidor EinsNet
echo ======================================================================
echo.
echo [*] Haciendo Ping a %SERVER_IP%...
ping -n 3 %SERVER_IP%
echo.
echo [*] Verificando API HTTP en http://%SERVER_IP%:%SERVER_PORT%/api/status...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/status' -TimeoutSec 3; Write-Host '[OK] Servidor responde 200 OK. Backend: ' $r.backend -ForegroundColor Green } catch { Write-Host '[!] Servidor HTTP no responde: ' $_.Exception.Message -ForegroundColor Red }"
echo.
pause
goto MENU

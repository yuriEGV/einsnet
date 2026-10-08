@echo off
title EinsNet - Enviar Mensaje a Soporte TI (maritimo)
color 0b
chcp 65001 >nul

set SERVER_IP=
if exist "%~dp0server_ip.txt" set /p SERVER_IP=<"%~dp0server_ip.txt"
if "%SERVER_IP%"=="" if exist "C:\ProgramData\NetGuard\server_ip.txt" set /p SERVER_IP=<"C:\ProgramData\NetGuard\server_ip.txt"
if "%SERVER_IP%"=="" if exist "C:\ProgramData\EinsNet\server_ip.txt" set /p SERVER_IP=<"C:\ProgramData\EinsNet\server_ip.txt"
if "%SERVER_IP%"=="" (
    netstat -ano | findstr :8000 >nul
    if not errorlevel 1 (
        set SERVER_IP=127.0.0.1
    ) else (
        set SERVER_IP=192.168.1.130
    )
)
set SERVER_PORT=8000

echo ================================================================
echo           EinsNet · Intercomunicador y Mensajeria LAN
echo ================================================================
echo Conectado a Servidor Central: http://%SERVER_IP%:%SERVER_PORT%
echo Equipo remitente: %COMPUTERNAME%
echo ================================================================
echo.

:loop
set /p USER_MSG="Escribe tu mensaje para el Administrador (o 'salir'): "

if "%USER_MSG%"=="" goto loop
if /i "%USER_MSG%"=="salir" exit /b

echo.
echo [*] Enviando mensaje por la red...

powershell -NoProfile -Command ^
  "$body = @{ sender_ip = '%COMPUTERNAME%'; sender_name = 'Gio (%COMPUTERNAME%)'; message = '%USER_MSG%' } | ConvertTo-Json; " ^
  "try { " ^
  "  $r = Invoke-RestMethod -Uri 'http://%SERVER_IP%:%SERVER_PORT%/api/send-reply' -Method Post -ContentType 'application/json' -Body $body; " ^
  "  Write-Host '[OK] ¡Mensaje entregado de inmediato en la pantalla del Administrador!' -ForegroundColor Green; " ^
  "} catch { " ^
  "  Write-Host '[ERROR] No se pudo conectar con el servidor %SERVER_IP%:%SERVER_PORT%.' -ForegroundColor Red; " ^
  "}"

echo.
echo ----------------------------------------------------------------
goto loop

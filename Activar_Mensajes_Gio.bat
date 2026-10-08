@echo off
title EinsNet - Activación de Mensajes y Alertas de Red (Puesto Gio)
color 0b
chcp 65001 >nul
cd /d "%~dp0"

:: Verificar si se ejecuta como Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================================
    echo   EinsNet: Solicitando Permisos de Administrador...
    echo   Por favor haz clic en "SÍ" en la ventana de Windows.
    echo ========================================================
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && \"%~dpnx0\" run_elevated' -Verb RunAs"
    exit /b
)

echo ================================================================
echo      EinsNet · Configuración de Mensajes y Alertas LAN
echo                  Puesto Gio (192.168.80.70)
echo ================================================================
echo.
echo [*] 1. Habilitando servicio de mensajes RPC de Windows (AllowRemoteRPC)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f >nul 2>&1

echo [*] 2. Configurando política de red local (LocalAccountTokenFilterPolicy)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f >nul 2>&1

echo [*] 3. Abriendo puertos de red en Firewall de Windows (TCP 135, 445 y UDP 8888)...
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule group="escritorio remoto" new enable=Yes >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_MSG_RPC" dir=in action=allow protocol=TCP localport=135,445 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_UDP_Beacon" dir=in action=allow protocol=UDP localport=8888 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_HTTP_Client" dir=in action=allow protocol=TCP localport=8765 profile=any >nul 2>&1

set SERVER_IP=
if exist "%~dp0server_ip.txt" set /p SERVER_IP=<"%~dp0server_ip.txt"
if "%SERVER_IP%"=="" if exist "C:\ProgramData\EinsNet\server_ip.txt" set /p SERVER_IP=<"C:\ProgramData\EinsNet\server_ip.txt"
if "%SERVER_IP%"=="" set SERVER_IP=192.168.80.22

echo [*] 4. Instalando agente receptor en segundo plano...
if not exist "C:\ProgramData\EinsNet" mkdir "C:\ProgramData\EinsNet"
copy /y "%~dp0netguard_agent_windows.ps1" "C:\ProgramData\EinsNet\agente.ps1" >nul 2>&1
if exist "%~dp0server_ip.txt" copy /y "%~dp0server_ip.txt" "C:\ProgramData\EinsNet\server_ip.txt" >nul 2>&1
schtasks /create /tn "EinsNet_Agent" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\ProgramData\EinsNet\agente.ps1" /sc onlogon /rl highest /f >nul 2>&1

:: Iniciar agente de fondo ahora
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\ProgramData\EinsNet\agente.ps1"

echo [*] 5. Notificando a la consola central de maritimo...
powershell -NoProfile -Command ^
  "try { $body = @{ sender_ip = '%COMPUTERNAME%'; sender_name = 'Gio (%COMPUTERNAME%)'; message = '¡Receptor y alertas EinsNet activados con éxito en mi equipo!' } | ConvertTo-Json; Invoke-RestMethod -Uri 'http://%SERVER_IP%:8765/api/send-reply' -Method Post -ContentType 'application/json' -Body $body | Out-Null } catch {}"

echo.
echo ================================================================
echo   [OK] ¡TODO CONFIGURADO CON ÉXITO!
echo   1. Este equipo ya recibe mensajes emergentes y alertas en vivo.
echo   2. Puedes enviar mensajes al Administrador con "Enviar_Mensaje_LAN.bat".
echo   3. Abriendo el Intercomunicador Web oficial...
echo ================================================================
echo.

:: Abrir navegador en el intercomunicador
start "" "http://%SERVER_IP%:8765/alerta"

timeout /t 3 >nul
exit

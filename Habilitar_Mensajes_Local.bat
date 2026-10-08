@echo off
title Habilitar Mensajes Windows en esta Maquina
cd /d "%~dp0"

:: Solicitar elevacion si no es administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================================
    echo   NetGuard: Solicitando Permisos de Administrador...
    echo   Por favor haz clic en "SI" en la ventana de Windows
    echo ========================================================
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && \"%~dpnx0\" run_elevated' -Verb RunAs"
    exit /b
)

echo.
echo [*] 1. Aplicando AllowRemoteRPC (Permite recibir msg.exe)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f

echo.
echo [*] 2. Aplicando LocalAccountTokenFilterPolicy (Evita Error 5 Acceso Denegado en Red)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f

echo.
echo [*] 3. Abriendo puertos RPC y Escritorio Remoto en Firewall de Windows...
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule group="escritorio remoto" new enable=Yes >nul 2>&1
netsh advfirewall firewall add rule name="NetGuard_MSG_RPC" dir=in action=allow protocol=TCP localport=135,445 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="NetGuard_UDP_Beacon" dir=in action=allow protocol=UDP localport=8888 profile=any >nul 2>&1

echo.
echo [*] 4. Instalando Agente Receptor en segundo plano...
if not exist "C:\ProgramData\NetGuard" mkdir "C:\ProgramData\NetGuard"
copy /y "%~dp0netguard_agent_windows.ps1" "C:\ProgramData\NetGuard\netguard_agent.ps1" >nul 2>&1
if exist "%~dp0server_ip.txt" (
    copy /y "%~dp0server_ip.txt" "C:\ProgramData\NetGuard\server_ip.txt" >nul 2>&1
    if not exist "C:\ProgramData\EinsNet" mkdir "C:\ProgramData\EinsNet"
    copy /y "%~dp0server_ip.txt" "C:\ProgramData\EinsNet\server_ip.txt" >nul 2>&1
)
schtasks /create /tn "NetGuard_Agent" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\ProgramData\NetGuard\netguard_agent.ps1" /sc onlogon /rl highest /f >nul 2>&1
start /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\ProgramData\NetGuard\netguard_agent.ps1"

msg * /TIME:5 "NetGuard: Activacion exitosa. Este equipo ya puede recibir mensajes y alertas del Administrador." >nul 2>&1

echo.
echo ========================================================
echo   [OK] Claves de Registro, Firewall y Agente Activados!
echo   Este equipo ahora recibe mensajes y alertas en vivo.
echo ========================================================
echo.
pause
exit

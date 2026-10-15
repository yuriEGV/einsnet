@echo off
chcp 65001 >nul
title EinsNet · Habilitar Directivas de Mensajería y Firewall Windows
cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Solicitando permisos de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && \"%~dpnx0\" run_elevated' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo   EinsNet · Directivas de Red y Firewall Windows
echo ======================================================================
echo.

echo [*] 1. Permitiendo RPC Remoto (msg.exe / Terminal Server)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f >nul 2>&1

echo [*] 2. Permitiendo autenticación de cuentas locales sin bloqueo remoto...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f >nul 2>&1

echo [*] 3. Abriendo Firewall de Windows (TCP 8000, UDP 8888, RPC 135/445)...
netsh advfirewall firewall add rule name="EinsNet_HTTP_8000" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_UDP_8888" dir=in action=allow protocol=UDP localport=8888 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_RPC_MSG" dir=in action=allow protocol=TCP localport=135,445 profile=any >nul 2>&1
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule group="escritorio remoto" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule name="File and Printer Sharing (Echo Request - ICMPv4-In)" new enable=yes >nul 2>&1

echo.
echo ======================================================================
echo   [OK] Directivas aplicadas con éxito.
echo ======================================================================
echo.
pause
exit

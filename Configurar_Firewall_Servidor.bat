@echo off
chcp 65001 >nul
title EinsNet · Configurar Firewall en el Servidor (Puerto 8000)
cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Solicitando permisos de Administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && \"%~dpnx0\" run_elevated' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo   EinsNet · Apertura de Puertos del Servidor en Windows Firewall
echo ======================================================================
echo.
echo [*] Permitiendo Puerto 8000 TCP (Consola EinsNet, API y Descargas)...
netsh advfirewall firewall add rule name="EinsNet_Server_8000" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1

echo [*] Permitiendo Puerto 8888 UDP (Alertas Instantaneas LAN Broadcast)...
netsh advfirewall firewall add rule name="EinsNet_UDP_8888" dir=in action=allow protocol=UDP localport=8888 profile=any >nul 2>&1

echo [*] Permitiendo ICMP (Ping / Deteccion de Equipos en Vivo)...
netsh advfirewall firewall set rule name="File and Printer Sharing (Echo Request - ICMPv4-In)" new enable=yes >nul 2>&1

echo [*] Permitiendo RPC de Mensajeria Windows (Puertos 135 y 445)...
netsh advfirewall firewall add rule name="EinsNet_RPC_135_445" dir=in action=allow protocol=TCP localport=135,445 profile=any >nul 2>&1

echo.
echo ======================================================================
echo   [OK] Puertos configurados en Firewall de Windows.
echo   Los computadores de la red ya pueden conectarse a http://192.168.80.22:8000
echo ======================================================================
echo.
pause
exit

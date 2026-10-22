@echo off
chcp 65001 >nul
title EinsNet - Desbloquear Acceso a Red y Dispositivos
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet - Desbloqueo y Restauracion de Conectividad Total LAN
echo    Reloj Biometrico (192.168.1.201), Camaras CCTV y Red Local
echo ======================================================================
echo.

echo [*] Eliminando posibles reglas residuales de bloqueo en Windows Firewall...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { ($_.DisplayName -like '*EinsNet*' -or $_.DisplayName -like '*NetGuard*' -or $_.DisplayName -like '*Cut*' -or $_.DisplayName -like '*Aislar*' -or $_.DisplayName -like '*Quarantine*') -and $_.Action -eq 'Block' } | Remove-NetFirewallRule -ErrorAction SilentlyContinue"

echo [*] Asegurando politica de trafico saliente permitida (Allow Outbound)...
netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound >nul 2>&1

echo [*] Limpiando cache DNS y tablas de direcciones...
ipconfig /flushdns >nul 2>&1
arp -d * >nul 2>&1

echo.
echo [*] Probando conexion directa con Reloj Biometrico (192.168.1.201)...
ping 192.168.1.201 -n 2

echo.
echo [*] Probando conexion con DVR Camaras CCTV (192.168.1.126)...
ping 192.168.1.126 -n 2

echo.
echo ======================================================================
echo    [DIAGNOSTICO COMPLETADO]
echo    Si el navegador aun dice 'ERR_NETWORK_ACCESS_DENIED':
echo    1. Si tienes una VPN activa (ProtonVPN, FortiClient, etc.):
echo       -> Desconectala o activa 'Allow LAN Connections' / Split Tunnel.
echo    2. Si tienes Antivirus con Firewall (Kaspersky, ESET, Avast):
echo       -> Desactiva temporalmente el Firewall del Antivirus o
echo          autoriza la red 192.168.1.0/24 como 'Red Privada / Segura'.
echo ======================================================================
echo.
pause
exit

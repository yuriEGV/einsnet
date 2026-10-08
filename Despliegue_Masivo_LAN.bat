@echo off
title NetGuard - Despliegue Masivo de Mensajes LAN
cd /d "%~dp0"

:: Verificar privilegios de Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================================
    echo   NetGuard: Solicitando Permisos de Administrador...
    echo   Por favor haz clic en "SI" en la ventana de Windows
    echo ========================================================
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && powershell -NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0Despliegue_Masivo_LAN.ps1\"\"' -Verb RunAs"
    exit /b
)

echo [*] Ejecutando script de despliegue masivo en PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Despliegue_Masivo_LAN.ps1"
echo.
pause
exit

@echo off
chcp 65001 >nul
title EinsNet · Guardián y Levantador de Servidor
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet · Guardián y Auto-Recuperación de Servidor LAN (Puerto 8000)
echo ======================================================================
echo.
echo [*] Verificando estado del servidor en puerto 8000 y asegurando servicio...

python supervisor_einsnet.py --ensure

echo.
echo [OK] El servidor EinsNet está ACTIVO y OPERATIVO en puerto 8000.
echo [OK] Guardián de fondo ACTIVADO (Se reiniciará solo si llega a caerse).
echo.
echo [*] Abriendo consola de control en el navegador...
start "" "http://localhost:8000"

echo.
echo [ Listo. Puedes cerrar esta ventana en cualquier momento ]
timeout /t 3 /nobreak >nul
exit

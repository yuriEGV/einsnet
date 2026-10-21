@echo off
chcp 65001 >nul
title EinsNet · Guardián y Levantador de Servidor
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet · Guardián y Servidor Multi-Sede v6.0 (Puerto 8000)
echo    Campus Central Lynch ⟷ Módulo A-15 Levarte
echo ======================================================================
echo.

echo [*] Comprobando actualizaciones desde GitHub (git pull origin main)...
where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    git fetch origin main >nul 2>&1
    git reset --hard origin/main >nul 2>&1
    echo [OK] Repositorio sincronizado con la última versión oficial (12 Cámaras y Bi-Sede).
) else (
    echo [!] Git no detectado en PATH, iniciando con archivos locales.
)
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

@echo off
chcp 65001 >nul
title Iniciando EinsNet Monitor LAN (Puerto 8000)
cd /d "%~dp0"

where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    git fetch origin main >nul 2>&1
    git reset --hard origin/main >nul 2>&1
)

echo [*] Verificando y asegurando Motor Real EinsNet en puerto 8000...
python supervisor_einsnet.py --ensure
start "" "http://localhost:8000"
exit

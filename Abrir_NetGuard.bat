@echo off
title Iniciando EinsNet Monitor LAN
cd /d "%~dp0"
echo [*] Verificando Motor Real EinsNet...
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo [*] Iniciando servidor y conector de red en segundo plano (Puerto 8000)...
    start "" /b python netguard_server.py
    timeout /t 1 /nobreak >nul
)
start "" "http://localhost:8000"
exit

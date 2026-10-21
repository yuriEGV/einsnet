@echo off
chcp 65001 >nul
title EinsNet - Servidor Multi-Sede v6.0 (Puerto 8000)
cd /d "%~dp0"

echo ======================================================================
echo    EinsNet - Servidor Multi-Sede v6.0 (Puerto 8000)
echo    Campus Central Lynch - Modulo A-15 Levarte
echo ======================================================================
echo.

echo [*] Verificando Git...
where git >nul 2>&1
if %ERRORLEVEL% equ 0 goto :SYNC_GIT
goto :START_SERVER

:SYNC_GIT
echo [*] Sincronizando con repositorio oficial (git pull)...
git fetch origin main >nul 2>&1
git reset --hard origin/main >nul 2>&1
echo [OK] Repositorio al dia con GitHub.

:START_SERVER
echo [*] Levantando Servidor EinsNet en puerto 8000...
start "" python supervisor_einsnet.py --ensure
ping 127.0.0.1 -n 3 >nul

echo [*] Abriendo navegador en http://localhost:8000...
start "" "http://localhost:8000"

echo.
echo [OK] Servidor iniciado con exito en http://localhost:8000
echo.
ping 127.0.0.1 -n 3 >nul
exit

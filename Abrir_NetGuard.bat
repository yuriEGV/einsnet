@echo off
title Iniciando EinsNet Monitor LAN (Puerto 8000)
cd /d "%~dp0"
echo [*] Verificando y asegurando Motor Real EinsNet en puerto 8000...
python supervisor_einsnet.py --ensure
start "" "http://localhost:8000"
exit

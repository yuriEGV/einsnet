@echo off
title EinsNet - Nodo Receptor y Alertas LAN
color 0A
cd /d "%~dp0"
echo =================================================================
echo   EinsNet · Nodo Receptor Seguro y Enlace Escolar
echo =================================================================
echo [*] Iniciando nodo en primer plano...
python "%~dp0einsnet_node.py" %*
pause

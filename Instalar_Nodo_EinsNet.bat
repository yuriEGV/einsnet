@echo off
title EinsNet - Instalador Permanente de Nodo Receptor
color 0B
cd /d "%~dp0"
echo =================================================================
echo   EinsNet · Instalando Nodo Receptor Permanente
echo =================================================================
echo [*] Configurando persistencia y servicio de fondo...
python "%~dp0einsnet_node.py" --install
pause

@echo off
title EinsNet - Agente Receptor de Mensajes LAN
cd /d "%~dp0"
echo [*] Iniciando agente receptor de alertas de EinsNet en segundo plano...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0netguard_agent_windows.ps1"
pause

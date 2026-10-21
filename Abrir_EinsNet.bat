@echo off
chcp 65001 >nul
title EinsNet Monitor LAN (Puerto 8000)
cd /d "%~dp0"

start "" python supervisor_einsnet.py --ensure
start "" "http://localhost:8000"
exit

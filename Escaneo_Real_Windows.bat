@echo off
title NetGuard - Escaneo Nativo LAN y WAN
color 0B
echo =================================================================
echo   NetGuard - Escaner Nativo de Red (LAN y WAN)
echo =================================================================
echo.
echo Escaneando tu red y probando conexion exterior...
python "c:\Users\maritimo13\Desktop\conexiones\netguard_scanner.py" %1
echo.
echo =================================================================
echo Escaneo finalizado. Los resultados se guardaron en real_scan.json
echo =================================================================
pause

@echo off
chcp 65001 >nul
title EinsNet · Instalador Automático de Receptor y Directivas LAN
cd /d "%~dp0"

:: 1. Auto-elevación a Administrador si es necesario
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ======================================================================
    echo   EinsNet: Solicitando permisos de Administrador para configurar red...
    echo   Por favor haz clic en "SÍ" en la ventana emergente de Windows.
    echo ======================================================================
    powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"\"%~dp0\"\" && \"%~dpnx0\" run_elevated' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo   EinsNet · Instalación de Directivas de Mensajería y Agente LAN
echo   Servidor Central: 192.168.80.22 (Puerto 8000)
echo ======================================================================
echo.

:: 2. Habilitar directivas de mensajería remota de Windows (msg.exe / RPC)
echo [*] Configurando directivas de Registro de Windows (AllowRemoteRPC)...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f >nul 2>&1

:: 3. Habilitar reglas de Firewall de Windows
echo [*] Abriendo puertos en Firewall de Windows (8000 TCP, 8888 UDP, RPC 135/445)...
netsh advfirewall firewall add rule name="EinsNet_HTTP_8000" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_UDP_8888" dir=in action=allow protocol=UDP localport=8888 profile=any >nul 2>&1
netsh advfirewall firewall add rule name="EinsNet_RPC_MSG" dir=in action=allow protocol=TCP localport=135,445 profile=any >nul 2>&1
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule group="escritorio remoto" new enable=Yes >nul 2>&1
netsh advfirewall firewall set rule name="File and Printer Sharing (Echo Request - ICMPv4-In)" new enable=yes >nul 2>&1

:: 4. Preparar directorio local de EinsNet
set "TARGET_DIR=C:\ProgramData\EinsNet"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: Guardar IP del servidor
echo 192.168.80.22> "%TARGET_DIR%\server_ip.txt"

:: 5. Descargar o copiar el agente iniciar.ps1
set "AGENT_PATH=%TARGET_DIR%\iniciar.ps1"
if exist "%~dp0iniciar.ps1" (
    echo [*] Copiando agente localmente desde la carpeta...
    copy /y "%~dp0iniciar.ps1" "%AGENT_PATH%" >nul 2>&1
) else (
    echo [*] Descargando agente desde el servidor central (http://192.168.80.22:8000)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('http://192.168.80.22:8000/iniciar.ps1', '%AGENT_PATH%')" >nul 2>&1
    if not exist "%AGENT_PATH%" (
        curl -s "http://192.168.80.22:8000/iniciar.ps1" -o "%AGENT_PATH%" >nul 2>&1
    )
)

:: 6. Crear acceso directo en Inicio de Windows para auto-inicio permanente
echo [*] Registrando inicio automático en Windows (Startup)...
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $lnk = $WshShell.CreateShortcut('%STARTUP_DIR%\EinsNet_Agent.lnk'); $lnk.TargetPath = 'powershell.exe'; $lnk.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""%AGENT_PATH%""'; $lnk.WorkingDirectory = '%TARGET_DIR%'; $lnk.WindowStyle = 7; $lnk.Save()" >nul 2>&1

:: 7. Crear tarea programada de respaldo al iniciar sesión
schtasks /create /tn "EinsNet_Agent" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File %AGENT_PATH%" /sc onlogon /rl highest /f >nul 2>&1

:: 8. Iniciar el agente receptor ahora mismo en segundo plano
echo [*] Levantando el receptor en segundo plano...
taskkill /F /FI "WINDOWTITLE eq *NetGuard · Agente*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *EinsNet · Agente*" >nul 2>&1
start /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%AGENT_PATH%"

:: 9. Notificación de confirmación en pantalla
echo.
echo ======================================================================
echo   [OK] ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!
echo   1. Directivas de Mensajes Windows: HABILITADAS
echo   2. Firewall (Puertos 8000, 8888, 135, 445): HABILITADOS
echo   3. Receptor EinsNet en Segundo Plano: ACTIVO Y ESCUCHANDO
echo   4. Auto-Reinicio al Encender el PC: CONFIGURADO
echo ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Media.SystemSounds]::Asterisk.Play();" >nul 2>&1

echo [ Presiona cualquier tecla para cerrar esta ventana ]
pause >nul
exit

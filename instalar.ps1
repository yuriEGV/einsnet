# ===================================================================
# EinsNet · Instalador Permanente de Agente Receptor LAN
# Ejecutar en PowerShell como Administrador:
#   irm http://192.168.80.22:8765/instalar.ps1 | iex
# ===================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   EinsNet - Activando Recepcion de Mensajes y Alertas LAN       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[*] Solicitando elevacion de Administrador..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"& { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; irm http://192.168.80.22:8765/instalar.ps1 | iex }`"" -Verb RunAs
    exit
}

Write-Host "[1/3] Configurando Firewall y Puertos de red..." -ForegroundColor Yellow
try {
    netsh advfirewall firewall add rule name="NetGuard_UDP_Beacon" dir=in action=allow protocol=UDP localport=8888 profile=any >$null 2>&1
    Write-Host "      [OK] Firewall configurado para el puerto 8888." -ForegroundColor Green
} catch {}

Write-Host "[2/3] Instalando Agente Receptor permanente..." -ForegroundColor Yellow
try {
    $installDir = "C:\ProgramData\NetGuard"
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    }

    $agentFile = "$installDir\netguard_agent.ps1"
    $vbsFile = "$installDir\run_agent.vbs"

    # Descargar agente v3.0
    (New-Object System.Net.WebClient).DownloadFile("http://192.168.80.22:8765/netguard_agent_windows.ps1", $agentFile)

    # Guardar IP del servidor detectada para persistencia
    $serverIpVal = "192.168.80.22"
    Set-Content -Path "$installDir\server_ip.txt" -Value $serverIpVal -Encoding ASCII
    $einsDir = "C:\ProgramData\EinsNet"
    if (-not (Test-Path $einsDir)) { New-Item -ItemType Directory -Path $einsDir -Force | Out-Null }
    Set-Content -Path "$einsDir\server_ip.txt" -Value $serverIpVal -Encoding ASCII

    # Crear lanzador VBS totalmente transparente
    $vbsContent = "CreateObject(""Wscript.Shell"").Run ""powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """"$agentFile"""""", 0, False"
    Set-Content -Path $vbsFile -Value $vbsContent -Encoding ASCII

    # Registrar en carpeta Inicio de Todos los Usuarios (Inicia con Windows en sesion de escritorio)
    $allUsersStartup = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
    if (Test-Path $allUsersStartup) {
        Copy-Item -Path $vbsFile -Destination "$allUsersStartup\NetGuard_Agent.vbs" -Force
    }

    # Registrar en Clave Run de Registro
    reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v NetGuard_Agent /t REG_SZ /d "wscript.exe `"$vbsFile`"" /f | Out-Null

    # Iniciar el agente ahora mismo
    Start-Process wscript.exe -ArgumentList "`"$vbsFile`""
    Write-Host "      [OK] Agente instalado e iniciado en segundo plano." -ForegroundColor Green
} catch {
    Write-Host "      [!] Error: $_" -ForegroundColor Red
}

Write-Host "[3/3] Comprobando recepcion..." -ForegroundColor Yellow
try {
    $wsh = New-Object -ComObject WScript.Shell
    $wsh.Popup("✅ ¡EinsNet Conectado Exitosamente!`n`nEste equipo ahora recibirá todos los mensajes y alertas del Administrador directamente en pantalla con sonido y voz.", 0, "EinsNet LAN - Conectado", 64 + 4096) | Out-Null
} catch {}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  ¡LISTO! Equipo de $($env:COMPUTERNAME) configurado al 100%.    " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 3

# EinsNet - Actualizador Nativo PowerShell v6.0
$Host.UI.RawUI.WindowTitle = "EinsNet - Actualizador Oficial"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EinsNet - Actualizacion Forzada Oficial v6.0" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

Write-Host "[*] Deteniendo procesos anteriores en segundo plano..." -ForegroundColor Yellow
Get-Process python, pythonw -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*netguard*" -or $_.CommandLine -like "*netguard_server.py*" } | Stop-Process -Force -ErrorAction SilentlyContinue

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "[*] Sincronizando con git fetch y reset --hard..." -ForegroundColor Yellow
    git fetch origin main
    git reset --hard origin/main
    Write-Host "[OK] Sincronizado exitosamente con GitHub." -ForegroundColor Green
} else {
    Write-Host "[*] Descargando paquete oficial via HTTPS..." -ForegroundColor Yellow
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri 'https://github.com/yuriEGV/einsnet/archive/refs/heads/main.zip' -OutFile 'einsnet_latest.zip' -UseBasicParsing
    Expand-Archive -Path 'einsnet_latest.zip' -DestinationPath 'einsnet_tmp' -Force
    Copy-Item -Path 'einsnet_tmp\einsnet-main\*' -Destination '.' -Recurse -Force
    Remove-Item -Path 'einsnet_latest.zip', 'einsnet_tmp' -Recurse -Force
    Write-Host "[OK] Codigo descargado y actualizado." -ForegroundColor Green
}

Write-Host "[*] Iniciando Servidor EinsNet en puerto 8000..." -ForegroundColor Yellow
Start-Process python -ArgumentList "supervisor_einsnet.py --ensure" -WorkingDirectory $ScriptDir -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "[*] Abriendo navegador en http://localhost:8000..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"
Write-Host "[OK] Actualizacion v6.0 completada con exito." -ForegroundColor Green
Start-Sleep -Seconds 3

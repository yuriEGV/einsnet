# EinsNet - Lanzador Nativo PowerShell v6.0
$Host.UI.RawUI.WindowTitle = "EinsNet - Servidor Multi-Sede (Puerto 8000)"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EinsNet - Servidor Multi-Sede v6.0 (Puerto 8000)" -ForegroundColor Green
Write-Host "   Campus Central Lynch <-> Modulo A-15 Levarte" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "[*] Comprobando actualizaciones de Git..." -ForegroundColor Yellow
    git fetch origin main 2>$null
    git reset --hard origin/main 2>$null
    Write-Host "[OK] Codigo sincronizado con GitHub." -ForegroundColor Green
}

Write-Host "[*] Levantando Servidor EinsNet en puerto 8000..." -ForegroundColor Yellow
Start-Process python -ArgumentList "supervisor_einsnet.py --ensure" -WorkingDirectory $ScriptDir -WindowStyle Hidden
Start-Sleep -Seconds 2

Write-Host "[*] Abriendo navegador en http://localhost:8000..." -ForegroundColor Yellow
Start-Process "http://localhost:8000"
Write-Host "[OK] Servidor activo en http://localhost:8000" -ForegroundColor Green
Start-Sleep -Seconds 3

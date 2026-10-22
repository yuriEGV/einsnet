# EinsNet - Desbloqueo y Diagnóstico Nativo PowerShell
$Host.UI.RawUI.WindowTitle = "EinsNet - Desbloquear Acceso a Red y Dispositivos"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   EinsNet - Desbloqueo de Red LAN y Diagnostico de Dispositivos" -ForegroundColor Green
Write-Host "   Reloj Biometrico (192.168.1.201), Camaras CCTV y Nodos Locales" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[*] Eliminando cualquier regla de bloqueo en Windows Firewall..." -ForegroundColor Yellow
Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { 
    ($_.DisplayName -like '*EinsNet*' -or $_.DisplayName -like '*NetGuard*' -or $_.DisplayName -like '*Cut*' -or $_.DisplayName -like '*Aislar*' -or $_.DisplayName -like '*Quarantine*') -and $_.Action -eq 'Block' 
} | Remove-NetFirewallRule -ErrorAction SilentlyContinue

Write-Host "[*] Asegurando salida permitida en perfiles de Firewall..." -ForegroundColor Yellow
netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound 2>$null | Out-Null

Write-Host "[*] Limpiando cache DNS y ARP..." -ForegroundColor Yellow
ipconfig /flushdns 2>$null | Out-Null
arp -d * 2>$null | Out-Null

Write-Host ""
Write-Host "[*] Comprobando ping a Reloj Biometrico (192.168.1.201)..." -ForegroundColor Yellow
Test-Connection -ComputerName 192.168.1.201 -Count 2 -Quiet | ForEach-Object {
    if ($_) {
        Write-Host "  [OK] 192.168.1.201 RESPONDE CORRECTAMENTE AL PING." -ForegroundColor Green
    } else {
        Write-Host "  [!] 192.168.1.201 no respondio al ping en este momento." -ForegroundColor Red
    }
}

Write-Host "[*] Comprobando ping a DVR Camaras CCTV (192.168.1.126)..." -ForegroundColor Yellow
Test-Connection -ComputerName 192.168.1.126 -Count 2 -Quiet | ForEach-Object {
    if ($_) {
        Write-Host "  [OK] 192.168.1.126 RESPONDE CORRECTAMENTE AL PING." -ForegroundColor Green
    } else {
        Write-Host "  [!] 192.168.1.126 no respondio al ping en este momento." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Recomendaciones periciales si Brave/Chrome muestra ERR_NETWORK_ACCESS_DENIED:" -ForegroundColor Yellow
Write-Host "   1. Si tienes una VPN activa (como ProtonVPN, que asigna 10.2.0.2):" -ForegroundColor White
Write-Host "      -> Desconectala o marca 'Allow LAN Connections' en Ajustes de la VPN." -ForegroundColor White
Write-Host "   2. Si tienes un Antivirus (Kaspersky, ESET, Avast, Bitdefender):" -ForegroundColor White
Write-Host "      -> Asegurate de configurar tu red como 'Red Privada / Segura'." -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
pause

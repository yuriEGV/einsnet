<#
═══════════════════════════════════════════════════════════════════════════
 NetGuard · Despliegue Masivo de Mensajería Windows en Red LAN
 Aplica AllowRemoteRPC=1, LocalAccountTokenFilterPolicy=1 y reglas de
 Firewall a todos los equipos Windows de la subred de forma desatendida.
═══════════════════════════════════════════════════════════════════════════
#>

param(
    [switch]$Silent = $false,
    [switch]$Auto = $false,
    [System.Management.Automation.PSCredential]$Credential = $null
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   NetGuard · Despliegue Masivo de Recepción de Mensajes LAN     " -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Detección dinámica de IP y subred activa (funciona en Lynch, Levarte o cualquier red)
$LocalIP = "127.0.0.1"
try {
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
} catch {}

if (-not $LocalIP -or $LocalIP -eq "127.0.0.1") {
    try {
        $s = New-Object System.Net.Sockets.UdpClient
        $s.Connect("1.1.1.1", 80)
        $LocalIP = $s.Client.LocalEndPoint.Address.ToString()
        $s.Close()
    } catch {
        $LocalIP = "192.168.80.22"
    }
}

$parts = $LocalIP.Split('.')
if ($parts.Count -ge 3) {
    $SubnetPrefix = "$($parts[0]).$($parts[1]).$($parts[2])."
} else {
    $SubnetPrefix = "192.168.80."
}

# 1. Aplicar en la máquina local primero
Write-Host "[*] 1. Configurando máquina local ($LocalIP en subred ${SubnetPrefix}x)..." -ForegroundColor Yellow
try {
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f | Out-Null
    reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f | Out-Null
    netsh advfirewall firewall set rule group="remote desktop" new enable=Yes >$null 2>&1
    netsh advfirewall firewall set rule group="escritorio remoto" new enable=Yes >$null 2>&1
    netsh advfirewall firewall add rule name="NetGuard_MSG_RPC" dir=in action=allow protocol=TCP localport=135,445 profile=any >$null 2>&1
    Write-Host "  [OK] Máquina local configurada y lista para recibir/enviar." -ForegroundColor Green
} catch {
    Write-Host "  [!] Error al configurar localmente: $_" -ForegroundColor Red
}

# 2. Descubrir hosts activos en la red LAN mediante ARP y Ping
Write-Host ""
Write-Host "[*] 2. Escaneando equipos activos en la subred ${SubnetPrefix}x..." -ForegroundColor Yellow

$ActiveHosts = @()
$ArpOutput = arp -a
$escapedPrefix = [regex]::Escape($SubnetPrefix)
foreach ($line in $ArpOutput) {
    if ($line -match "$escapedPrefix(\d+)\s+([0-9a-fA-F-]+)") {
        $ip = $SubnetPrefix + $matches[1]
        $mac = $matches[2]
        if ($ip -ne $LocalIP -and $ip -ne "${SubnetPrefix}1" -and $ip -ne "${SubnetPrefix}255") {
            $ActiveHosts += [PSCustomObject]@{ IP = $ip; MAC = $mac }
        }
    }
}

Write-Host "  -> Detectados $($ActiveHosts.Count) equipos activos en la tabla de red." -ForegroundColor Cyan

# 3. Credenciales administrativas
$Cred = $Credential
if (-not $Silent -and -not $Auto -and -not $Cred) {
    Write-Host ""
    Write-Host "Para conectarse en segundo plano a las otras máquinas en un Grupo de Trabajo," -ForegroundColor White
    Write-Host "Windows puede requerir credenciales de Administrador si los puertos remotos están protegidos." -ForegroundColor Gray
    Write-Host "Presiona [ENTER] para intentar con credenciales actuales, o escribe 'C' para ingresar usuario/clave:" -ForegroundColor White
    $choice = Read-Host "Opción (Enter / C)"
    if ($choice -eq 'C' -or $choice -eq 'c') {
        $Cred = Get-Credential -UserName "Administrador" -Message "Ingresa credenciales de Administrador de los equipos de la red"
    }
}

# 4. Proceso de despliegue a cada host
Write-Host ""
Write-Host "[*] 3. Transmitiendo comandos de instalación a la red..." -ForegroundColor Yellow

$Results = @()

foreach ($h in $ActiveHosts) {
    $targetIP = $h.IP
    Write-Host "  -> Procesando $targetIP..." -NoNewline

    # Verificar conectividad y TTL para detectar Sistema Operativo
    $pingObj = Test-Connection -ComputerName $targetIP -Count 1 -ErrorAction SilentlyContinue
    if (-not $pingObj) {
        Write-Host " [OFFLINE / Sin respuesta ICMP]" -ForegroundColor DarkGray
        $Results += [PSCustomObject]@{ IP = $targetIP; SO = "Inactivo/Firewall"; Estado = "Sin Respuesta ICMP"; Metodo = "-" }
        continue
    }

    $ttl = $pingObj.ResponseTimeToLive
    $isLinux = ($ttl -and $ttl -le 64)

    if ($isLinux) {
        Write-Host " [LINUX / UNIX (TTL $ttl)]" -ForegroundColor DarkCyan
        $Results += [PSCustomObject]@{
            IP = $targetIP
            SO = "Linux / Unix (TTL $ttl)"
            Estado = "Receptor UDP Activo (Puerto 8888)"
            Metodo = "NetGuard Linux Agent / Web Alert"
        }
        continue
    }

    # Para equipos Windows (TTL > 64)
    $success = $false
    $methodUsed = ""

    # Intento 1: Registro Remoto .NET nativo
    try {
        $regKey = [Microsoft.Win32.RegistryKey]::OpenRemoteBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine, $targetIP)
        $subKey = $regKey.OpenSubKey("SYSTEM\CurrentControlSet\Control\Terminal Server", $true)
        if ($subKey) {
            $subKey.SetValue("AllowRemoteRPC", 1, [Microsoft.Win32.RegistryValueKind]::DWord)
            $subKey.Close()
            $regKey.Close()
            $success = $true
            $methodUsed = "Registro Remoto (.NET)"
        }
    } catch {}

    # Intento 2: PowerShell WinRM
    if (-not $success) {
        try {
            $scriptBlock = {
                reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f
                reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f
                netsh advfirewall firewall add rule name="NetGuard_MSG_RPC" dir=in action=allow protocol=TCP localport=135,445 profile=any
            }
            if ($Cred) {
                Invoke-Command -ComputerName $targetIP -Credential $Cred -ScriptBlock $scriptBlock -ErrorAction Stop | Out-Null
            } else {
                Invoke-Command -ComputerName $targetIP -ScriptBlock $scriptBlock -ErrorAction Stop | Out-Null
            }
            $success = $true
            $methodUsed = "PowerShell WinRM"
        } catch {}
    }

    # Intento 3: WMI Process Create
    if (-not $success) {
        try {
            $cmd = 'cmd.exe /c reg add "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v AllowRemoteRPC /t REG_DWORD /d 1 /f & reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f & netsh advfirewall firewall add rule name="NetGuard_MSG_RPC" dir=in action=allow protocol=TCP localport=135,445 profile=any'
            $wmi = [wmiclass]"\\$targetIP\root\cimv2:Win32_Process"
            $res = $wmi.Create($cmd)
            if ($res.ReturnValue -eq 0) {
                $success = $true
                $methodUsed = "WMI Remote Process"
            }
        } catch {}
    }

    if ($success) {
        Write-Host " [OK - $methodUsed]" -ForegroundColor Green
        $Results += [PSCustomObject]@{ IP = $targetIP; SO = "Windows (TTL $ttl)"; Estado = "Configurado Exitosamente"; Metodo = $methodUsed }
    } else {
        Write-Host " [REQUIERE SCRIPT WEB 1-LINEA]" -ForegroundColor Yellow
        $Results += [PSCustomObject]@{
            IP = $targetIP
            SO = "Windows (TTL $ttl)"
            Estado = "Firewall Bloquea RPC Remoto"
            Metodo = "Ejecutar irm http://$LocalIP:8765/instalar.ps1"
        }
    }
}

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                      RESUMEN DEL DESPLIEGUE                     " -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
$Results | Format-Table -AutoSize

Write-Host ""
Write-Host "[*] INSTALACIÓN RÁPIDA EN EQUIPOS CON FIREWALL RESTRICTIVO:" -ForegroundColor White
Write-Host "  1. En equipos Windows, abre PowerShell como Administrador y pega:" -ForegroundColor Gray
Write-Host "     irm http://${LocalIP}:8765/instalar.ps1 | iex" -ForegroundColor Green
Write-Host ""
Write-Host "  2. En equipos Linux / Raspberry / Servidores, ejecuta en terminal:" -ForegroundColor Gray
Write-Host "     curl -s http://${LocalIP}:8765/iniciar_agente_linux.sh | bash" -ForegroundColor Cyan
Write-Host ""

if (-not $Silent -and -not $Auto) {
    Read-Host "Presiona ENTER para salir..."
}

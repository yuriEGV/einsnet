# ===================================================================
# EinsNet · Agente Receptor de Mensajes y Alertas LAN (Windows)
# Ejecutar en CMD:
#   powershell -ep bypass -c "irm http://192.168.80.22:8000/iniciar.ps1|iex"
# Ejecutar en PowerShell:
#   irm http://192.168.80.22:8000/iniciar.ps1 | iex
# ===================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

Clear-Host
Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "     EinsNet · Agente Receptor de Mensajes LAN (Puerto 8000)    " -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$ServerPort = 8000
$UdpPort = 8888
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Detección inteligente del Servidor EinsNet (Servidor Central en 192.168.80.22:8000)
$ServerHost = "192.168.80.22"
if ($ScriptDir -and (Test-Path "$ScriptDir\server_ip.txt")) {
    $ServerHost = (Get-Content "$ScriptDir\server_ip.txt" -Raw).Trim()
} elseif (Test-Path "C:\ProgramData\EinsNet\server_ip.txt") {
    $ServerHost = (Get-Content "C:\ProgramData\EinsNet\server_ip.txt" -Raw).Trim()
} elseif (Test-Path "C:\ProgramData\NetGuard\server_ip.txt") {
    $ServerHost = (Get-Content "C:\ProgramData\NetGuard\server_ip.txt" -Raw).Trim()
} elseif ($env:EINSNET_SERVER) {
    $ServerHost = $env:EINSNET_SERVER
}

$LocalIPs = @("127.0.0.1")
try {
    $LocalIPs += [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) | ForEach-Object { $_.IPAddressToString }
} catch {}

Write-Host "[*] Equipo local: $env:COMPUTERNAME" -ForegroundColor Gray
Write-Host "[*] IPs detectadas: $($LocalIPs -join ', ')" -ForegroundColor Gray
Write-Host "[*] Conectando con consola central: http://${ServerHost}:${ServerPort}" -ForegroundColor Gray

# Cargar librerias graficas
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 1. Registrar Agente con Heartbeat
$script:isLocalQuarantineActive = $false
try {
    $wcHeartbeat = New-Object System.Net.WebClient
    $wcHeartbeat.Headers.Add("Content-Type", "application/json")
    $detectedIp = ($LocalIPs | Where-Object { $_ -notlike "127.*" -and $_ -notlike "169.254.*" } | Select-Object -First 1)
    if (-not $detectedIp) { $detectedIp = "127.0.0.1" }
    $hbPayload = @{
        ip = $detectedIp
        hostname = $env:COMPUTERNAME
        os = "Windows"
    } | ConvertTo-Json
    $hbRes = $wcHeartbeat.UploadString("http://${ServerHost}:${ServerPort}/api/agent-heartbeat", $hbPayload)
    if ($hbRes) {
        try {
            $hbStartJson = $hbRes | ConvertFrom-Json
            if ($hbStartJson.is_isolated -or $hbStartJson.quarantine_action -eq "ISOLATE") {
                $script:isLocalQuarantineActive = $true
                Write-Host "[!] ALERTA: Esta estación se encuentra en estado AISLADO (Internet Cortado)." -ForegroundColor Red
                netsh advfirewall firewall add rule name="EinsNet_Cut_Web" dir=out action=block protocol=TCP remoteport=80,443,8080,8443 | Out-Null
                netsh advfirewall firewall add rule name="EinsNet_Cut_DNS" dir=out action=block protocol=UDP remoteport=53 | Out-Null
                netsh advfirewall firewall add rule name="EinsNet_Allow_Server" dir=out action=allow remoteip=$ServerHost | Out-Null
            }
        } catch {}
    }
    Write-Host "[OK] Agente registrado exitosamente en la consola EinsNet." -ForegroundColor Green
} catch {
    Write-Host "[!] Conectando con servidor en http://${ServerHost}:${ServerPort}..." -ForegroundColor Yellow
}

# Sonido de confirmacion de conexion
try { [System.Console]::Beep(880, 150); [System.Console]::Beep(1100, 200) } catch {}

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  [OK] RECEPTOR ACTIVO · Escuchando mensajes en vivo...         " -ForegroundColor Green
Write-Host "  (Puedes minimizar esta ventana, seguira funcionando en fondo) " -ForegroundColor Gray
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$shownAlerts = @{}

function Show-NetGuardAlertWindow($title, $msg, $sender) {
    if (-not $title) { $title = "Aviso del Administrador de Red" }
    
    Write-Host ""
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Red
    Write-Host " [!] NUEVO MENSAJE RECIBIDO de $sender:" -ForegroundColor Yellow
    Write-Host "     $msg" -ForegroundColor White
    Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Red

    # 1. Sonido de alerta
    try { [System.Media.SystemSounds]::Exclamation.Play() } catch {}
    try { [System.Console]::Beep(750, 200); [System.Console]::Beep(1000, 300) } catch {}

    # 2. Voz sintetizada en segundo plano
    try {
        Start-Job -ScriptBlock {
            param($text)
            try {
                $voice = New-Object -ComObject SAPI.SpVoice
                $voice.Rate = 1
                $voice.Volume = 100
                $voice.Speak("Mensaje del Administrador: " + $text)
            } catch {}
        } -ArgumentList $msg | Out-Null
    } catch {}

    # 3. Ventana emergente al frente (TopMost = True)
    try {
        $form = New-Object System.Windows.Forms.Form
        $form.Text = $title
        $form.Size = New-Object System.Drawing.Size(580, 430)
        $form.StartPosition = "CenterScreen"
        $form.TopMost = $true
        $form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42) # Slate oscuro
        $form.ForeColor = [System.Drawing.Color]::White
        $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
        $form.MaximizeBox = $false
        $form.MinimizeBox = $false

        $lblHeader = New-Object System.Windows.Forms.Label
        $lblHeader.Text = "🚨 " + $title.ToUpper()
        $lblHeader.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
        $lblHeader.ForeColor = [System.Drawing.Color]::FromArgb(239, 68, 68)
        $lblHeader.Location = New-Object System.Drawing.Point(20, 20)
        $lblHeader.Size = New-Object System.Drawing.Size(520, 30)
        $form.Controls.Add($lblHeader)

        $lblSub = New-Object System.Windows.Forms.Label
        $lblSub.Text = "Emitido por el Administrador de Red ($sender) a las " + (Get-Date -Format "HH:mm:ss")
        $lblSub.Font = New-Object System.Drawing.Font("Segoe UI", 9)
        $lblSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
        $lblSub.Location = New-Object System.Drawing.Point(20, 50)
        $lblSub.Size = New-Object System.Drawing.Size(520, 20)
        $form.Controls.Add($lblSub)

        $txtBox = New-Object System.Windows.Forms.TextBox
        $txtBox.Multiline = $true
        $txtBox.ReadOnly = $true
        $txtBox.ScrollBars = "Vertical"
        $txtBox.Text = $msg
        $txtBox.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
        $txtBox.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
        $txtBox.ForeColor = [System.Drawing.Color]::White
        $txtBox.Location = New-Object System.Drawing.Point(20, 75)
        $txtBox.Size = New-Object System.Drawing.Size(520, 130)
        $txtBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
        $form.Controls.Add($txtBox)

        # Campo para que Gio responda al Administrador
        $lblReply = New-Object System.Windows.Forms.Label
        $lblReply.Text = "💬 Responder al Administrador (Soporte TI):"
        $lblReply.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
        $lblReply.ForeColor = [System.Drawing.Color]::FromArgb(56, 189, 248)
        $lblReply.Location = New-Object System.Drawing.Point(20, 218)
        $lblReply.Size = New-Object System.Drawing.Size(520, 20)
        $form.Controls.Add($lblReply)

        $txtReply = New-Object System.Windows.Forms.TextBox
        $txtReply.Font = New-Object System.Drawing.Font("Segoe UI", 10)
        $txtReply.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
        $txtReply.ForeColor = [System.Drawing.Color]::White
        $txtReply.Location = New-Object System.Drawing.Point(20, 242)
        $txtReply.Size = New-Object System.Drawing.Size(520, 30)
        $txtReply.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
        $form.Controls.Add($txtReply)

        $btnReply = New-Object System.Windows.Forms.Button
        $btnReply.Text = "✉️ ENVIAR RESPUESTA"
        $btnReply.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
        $btnReply.BackColor = [System.Drawing.Color]::FromArgb(16, 185, 129)
        $btnReply.ForeColor = [System.Drawing.Color]::White
        $btnReply.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
        $btnReply.Location = New-Object System.Drawing.Point(60, 295)
        $btnReply.Size = New-Object System.Drawing.Size(220, 44)
        $btnReply.Cursor = [System.Windows.Forms.Cursors]::Hand
        $btnReply.Add_Click({
            $replyMsg = $txtReply.Text.Trim()
            if ($replyMsg) {
                try {
                    $wcRep = New-Object System.Net.WebClient
                    $wcRep.Headers.Add("Content-Type", "application/json")
                    $repData = @{
                        sender_ip = ($LocalIPs | Where-Object { $_ -like "192.168.*" } | Select-Object -First 1)
                        sender_name = "Gio ($env:COMPUTERNAME)"
                        message = $replyMsg
                    } | ConvertTo-Json
                    $wcRep.UploadString("http://${ServerHost}:${ServerPort}/api/send-reply", "POST", $repData) | Out-Null
                    [System.Windows.Forms.MessageBox]::Show("Tu respuesta fue entregada con éxito al Administrador maritimo.", "EinsNet", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
                    $form.Close()
                } catch {
                    [System.Windows.Forms.MessageBox]::Show("Error al conectar con la consola EinsNet.", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
                }
            } else {
                [System.Windows.Forms.MessageBox]::Show("Por favor escribe un mensaje en la casilla.", "Aviso", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning) | Out-Null
            }
        })
        $form.Controls.Add($btnReply)

        $btnOk = New-Object System.Windows.Forms.Button
        $btnOk.Text = "CERRAR AVISO"
        $btnOk.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
        $btnOk.BackColor = [System.Drawing.Color]::FromArgb(239, 68, 68)
        $btnOk.ForeColor = [System.Drawing.Color]::White
        $btnOk.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
        $btnOk.Location = New-Object System.Drawing.Point(300, 295)
        $btnOk.Size = New-Object System.Drawing.Size(200, 44)
        $btnOk.Cursor = [System.Windows.Forms.Cursors]::Hand
        $btnOk.Add_Click({ $form.Close() })
        $form.Controls.Add($btnOk)
        $form.AcceptButton = $btnOk

        $form.Add_Shown({
            $form.Activate()
            $form.BringToFront()
        })

        $form.ShowDialog() | Out-Null
    } catch {
        # Fallback a MessageBox
        try {
            [System.Windows.Forms.MessageBox]::Show($msg, $title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Exclamation) | Out-Null
        } catch {
            (New-Object -ComObject WScript.Shell).Popup($msg, 0, $title, 64 + 4096) | Out-Null
        }
    }
}

# Configurar socket UDP puerto 8888
$udpClient = $null
$endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, $UdpPort)
try {
    $udpClient = New-Object System.Net.Sockets.UdpClient($UdpPort)
    $udpClient.Client.ReceiveTimeout = 400
} catch {}

$lastHttpCheck = [DateTime]::MinValue
$lastHeartbeat = [DateTime]::MinValue

while ($true) {
    # 1. Escuchar por Socket UDP
    if ($udpClient) {
        try {
            $bytes = $udpClient.Receive([ref]$endpoint)
            if ($bytes -and $bytes.Length -gt 0) {
                $jsonStr = [System.Text.Encoding]::UTF8.GetString($bytes)
                $data = $jsonStr | ConvertFrom-Json
                $targetIp = if ($data.target_ip) { $data.target_ip.ToString().Trim() } else { "*" }
                $msg = $data.message
                $sender = $data.sender_ip
                $title = $data.title
                $alertId = if ($data.id) { $data.id } else { "${sender}_${msg}_$($data.timestamp)" }

                $isForMe = ($targetIp -eq "*" -or $targetIp -eq "all" -or $targetIp -eq "255.255.255.255" -or $LocalIPs -contains $targetIp -or $targetIp -eq "" -or $targetIp -eq $env:COMPUTERNAME)

                if ($isForMe -and $msg -and (-not $shownAlerts.ContainsKey($alertId))) {
                    $shownAlerts[$alertId] = $true
                    Show-NetGuardAlertWindow $title $msg $sender
                }
            }
        } catch [System.Net.Sockets.SocketException] {} catch {}
    }

    # 2. Polling HTTP cada 1.2 segundos y Heartbeat
    $now = [DateTime]::Now
    if (($now - $lastHttpCheck).TotalSeconds -ge 1.2) {
        $lastHttpCheck = $now
        try {
            $wc = New-Object System.Net.WebClient
            $wc.Headers.Add("User-Agent", "NetGuard-Windows-Agent/3.0")
            $rawJson = $wc.DownloadString("http://${ServerHost}:${ServerPort}/api/alerts")
            $alerts = $rawJson | ConvertFrom-Json

            if ($alerts) {
                foreach ($prop in $alerts.PSObject.Properties) {
                    $item = $prop.Value
                    if ($item -and $item.message) {
                        $itemIp = if ($item.ip) { $item.ip.ToString().Trim() } else { "*" }
                        $targetList = if ($item.target_ips) { $item.target_ips } else { @($itemIp) }
                        
                        $isTarget = ($itemIp -eq "*" -or $itemIp -eq "all" -or $itemIp -eq "EMERGENCY" -or $itemIp -eq "LATEST" -or $LocalIPs -contains $itemIp -or $itemIp -eq $env:COMPUTERNAME)
                        if (-not $isTarget) {
                            foreach ($tip in $targetList) {
                                if ($LocalIPs -contains $tip -or $tip -eq "*" -or $tip -eq $env:COMPUTERNAME) {
                                    $isTarget = $true
                                    break
                                }
                            }
                        }

                        if ($isTarget) {
                            $alertId = if ($item.id) { $item.id } else { "$($item.timestamp)_$($item.message)" }
                            if (-not $shownAlerts.ContainsKey($alertId)) {
                                $shownAlerts[$alertId] = $true
                                $sender = if ($item.name) { $item.name } else { "Administrador" }
                                $title = if ($item.title) { $item.title } elseif ($item.is_emergency) { "🚨 ALERTA DE EMERGENCIA" } else { "💬 AVISO DEL ADMINISTRADOR" }
                                Show-NetGuardAlertWindow $title $item.message $sender
                            }
                        }
                    }
                }
            }
        } catch {}

        # Heartbeat cada 10 segundos y sincronización de estado de Cuarentena / Aislamiento
        if (($now - $lastHeartbeat).TotalSeconds -ge 10) {
            $lastHeartbeat = $now
            try {
                $wcHb = New-Object System.Net.WebClient
                $wcHb.Headers.Add("Content-Type", "application/json")
                $detectedIp = ($LocalIPs | Where-Object { $_ -notlike "127.*" -and $_ -notlike "169.254.*" } | Select-Object -First 1)
                if (-not $detectedIp) { $detectedIp = "127.0.0.1" }
                $hbData = @{
                    ip = $detectedIp
                    hostname = $env:COMPUTERNAME
                    os = "Windows"
                } | ConvertTo-Json
                $hbResp = $wcHb.UploadString("http://${ServerHost}:${ServerPort}/api/agent-heartbeat", $hbData)
                if ($hbResp) {
                    $hbJson = $hbResp | ConvertFrom-Json
                    if ($hbJson.is_isolated -or $hbJson.quarantine_action -eq "ISOLATE") {
                        if (-not $script:isLocalQuarantineActive) {
                            $script:isLocalQuarantineActive = $true
                            Write-Host "[!] AISLAMIENTO ACTIVADO: Cortando acceso externo a Internet..." -ForegroundColor Red
                            netsh advfirewall firewall add rule name="EinsNet_Cut_Web" dir=out action=block protocol=TCP remoteport=80,443,8080,8443 | Out-Null
                            netsh advfirewall firewall add rule name="EinsNet_Cut_DNS" dir=out action=block protocol=UDP remoteport=53 | Out-Null
                            netsh advfirewall firewall add rule name="EinsNet_Allow_Server" dir=out action=allow remoteip=$ServerHost | Out-Null
                            Show-NetGuardAlertWindow "⛔ INTERNET CORTADO (CUARENTENA)" "Esta estación ha sido aislada de Internet por el Administrador EinsNet debido a contención de infección masiva. La navegación externa está suspendida para permitir trabajos técnicos aislados." "Administrador TI"
                        }
                    } else {
                        if ($script:isLocalQuarantineActive) {
                            $script:isLocalQuarantineActive = $false
                            Write-Host "[+] AISLAMIENTO LEVANTADO: Restaurando acceso a Internet..." -ForegroundColor Green
                            netsh advfirewall firewall delete rule name="EinsNet_Cut_Web" | Out-Null
                            netsh advfirewall firewall delete rule name="EinsNet_Cut_DNS" | Out-Null
                            netsh advfirewall firewall delete rule name="EinsNet_Allow_Server" | Out-Null
                            Show-NetGuardAlertWindow "🟢 CONEXIÓN A INTERNET RESTAURADA" "El Administrador EinsNet ha levantado el aislamiento. Tu estación vuelve a tener acceso normal a la red e Internet." "Administrador TI"
                        }
                    }
                }
            } catch {}
        }
    }

    Start-Sleep -Milliseconds 150
}

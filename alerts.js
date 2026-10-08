/* ═══════════════════════════════════════════════════════════
   NetGuard · alerts.js — Sistema de Diagnóstico Inteligente
   Cada alerta incluye: problema detallado, impacto,
   causas raíz, pasos de solución con comandos copiables,
   prevención y análisis proactivo de mejoras de red.
   ═══════════════════════════════════════════════════════════ */

// Override ALERT_TPLS with rich diagnostic templates
window.ALERT_TPLS_RICH = [
  {
    type: 'Conexion a IP Maliciosa (C2)',
    icon: '🚨',
    level: 'critical',
    desc: d => `${d.ip} estableció conexión saliente a 185.234.218.4:4444, clasificada como servidor C2 activo.`,
    problem: d => `El host <strong>${d.ip} (${d.name})</strong> inició una conexión hacia <code>185.234.218.4:4444</code>, una IP catalogada en múltiples listas negras como servidor de Comando y Control (C2) de malware. El puerto 4444 es el canal por defecto de Metasploit y varios RATs. Esto indica que el host probablemente está comprometido y recibiendo órdenes de un atacante remoto.`,
    impact: 'CRÍTICO — Posible exfiltración de datos, instalación de backdoors, propagación lateral hacia otros hosts de la red.',
    causes: ['Malware descargado por el usuario (adjunto, descarga web maliciosa)', 'Explotación de vulnerabilidad RCE sin parche aplicado', 'Extensión maliciosa de navegador con acceso de red', 'Credenciales comprometidas usadas para instalar agente remoto'],
    solutions: [
      { step:1, action:'Aislar el host cortando su acceso a la red inmediatamente', cmd:'block {ip}', type:'critical' },
      { step:2, action:'Moverlo a VLAN 99 (Cuarentena) para análisis forense', cmd:'vlan {ip} 99', type:'critical' },
      { step:3, action:'Bloquear la IP C2 en el firewall Fortinet (192.168.80.1)', cmd:'config firewall address → edit block-c2 → set subnet 185.234.218.4/32', type:'warning' },
      { step:4, action:'Escanear puertos del host para detectar backdoors activos', cmd:'scan {ip} full', type:'warning' },
      { step:5, action:'Verificar procesos y conexiones activas en el host (Windows)', cmd:'netstat -ano | findstr :4444', type:'info' },
      { step:6, action:'Forzar cambio de contraseñas del usuario asociado al equipo', cmd:'net user [usuario] [nueva_pass] /domain', type:'info' },
      { step:7, action:'Ejecutar análisis antimalware desde live USB o modo seguro', cmd:'', type:'info' },
    ],
    prevention: ['Habilitar IPS en Fortinet con firmas actualizadas (Anti-botnet)', 'Implementar EDR en todos los endpoints (ej: Windows Defender ATP)', 'Bloquear salida a puertos 4444, 1337, 5900 desde el firewall', 'Aplicar política Zero-Trust con allowlisting de aplicaciones'],
    ref: 'MITRE ATT&CK: T1571 (Non-Standard Port) · T1041 (Exfil over C2) · T1095',
  },
  {
    type: 'Port Scan Detectado',
    icon: '🔍',
    level: 'high',
    desc: d => `${d.ip} está escaneando puertos de múltiples hosts en la subred.`,
    problem: d => `El host <strong>${d.ip} (${d.name})</strong> generó una ráfaga anómala de paquetes SYN hacia múltiples IPs de la subred 192.168.80.x. Este patrón es el paso de <em>reconocimiento</em> previo a un ataque lateral. El host puede estar ejecutando nmap, Masscan u otra herramienta de escaneo de forma automática, indicando posible compromiso.`,
    impact: 'ALTO — El atacante está mapeando la red buscando servicios vulnerables. Señal clara de fase de reconocimiento activo (pre-ataque).',
    causes: ['Host comprometido con agente de movimiento lateral', 'Usuario ejecutando herramienta de escaneo sin autorización', 'Malware de tipo worm propagándose por la red', 'Script de IT ejecutado sin coordinación'],
    solutions: [
      { step:1, action:'Verificar procesos activos en el host fuente ahora mismo', cmd:'tasklist /fi "status eq running" (Windows) o ps aux | grep nmap', type:'critical' },
      { step:2, action:'Trazar el tráfico del host para confirmar el patrón SYN flood', cmd:'trace {ip}', type:'warning' },
      { step:3, action:'Aplicar ACL temporal en el switch TP-Link para limitar el host', cmd:'ip access-list extended QUARANTINE → deny ip {ip} any', type:'warning' },
      { step:4, action:'Revisar logs del sistema por nuevos procesos instalados', cmd:'eventvwr → Security → Event ID 4688 (new process)', type:'info' },
      { step:5, action:'Si se confirma compromiso, aislar y mover a VLAN de cuarentena', cmd:'vlan {ip} 99', type:'critical' },
    ],
    prevention: ['Configurar detección de port scan en el IPS del Fortinet', 'Implementar microsegmentación: limitar comunicación intra-VLAN', 'Activar 802.1X en switches TP-Link para autenticación por puerto', 'Habilitar logs de conexión en todos los switches de la red'],
    ref: 'MITRE ATT&CK: T1046 Network Service Scanning',
  },
  {
    type: 'Telnet sin Cifrado Activo',
    icon: '⚠️',
    level: 'high',
    desc: d => `${d.ip} usa Telnet (puerto 23). Credenciales y comandos circulan en texto plano visible.`,
    problem: d => `Se detectó tráfico Telnet activo en <strong>${d.ip} (${d.name})</strong>. Telnet transmite usuario, contraseña y todos los datos <strong>completamente en texto plano</strong> sin ningún cifrado. Cualquier dispositivo en la misma VLAN puede capturar estas credenciales con Wireshark en menos de 30 segundos, realizando un ataque <em>Man-in-the-Middle pasivo</em>.`,
    impact: 'ALTO — Las credenciales de administración quedan expuestas a cualquier host de la red. Un ataque MitM pasivo puede robarlas sin dejar rastro.',
    causes: ['Switch/router con Telnet habilitado como método de administración remota', 'Equipo legacy que no soporta SSH (firmware antiguo)', 'Configuración por defecto de fábrica nunca actualizada en switches TP-Link', 'Administrador usando Telnet por comodidad o desconocimiento'],
    solutions: [
      { step:1, action:'Deshabilitar Telnet en TODOS los switches TP-Link de la red', cmd:'config → management → telnet → disable (consola switch)', type:'critical' },
      { step:2, action:'Habilitar SSH v2 como reemplazo seguro en cada switch', cmd:'ip ssh version 2\ncrypto key generate rsa modulus 2048', type:'critical' },
      { step:3, action:'Bloquear el puerto 23 en el firewall Fortinet', cmd:'config firewall policy → service Telnet → action deny', type:'warning' },
      { step:4, action:'Cambiar TODAS las contraseñas de administración de red', cmd:'', type:'warning' },
      { step:5, action:'Verificar qué credenciales circularon (revisar capturas si las hay)', cmd:'', type:'info' },
    ],
    prevention: ['Política de red: SOLO SSH v2, nunca Telnet ni HTTP sin TLS', 'Crear VLAN de gestión separada (ej: VLAN 10) solo accesible desde IPs autorizadas', 'Auditar configuración de todos los switches con herramienta de compliance', 'Usar password manager para credenciales de red con rotación periódica'],
    ref: 'RFC 4251 (SSH) · CVE-2011-4862 Telnet · NIST SP 800-115',
  },
  {
    type: 'SMB Expuesto — Riesgo Ransomware',
    icon: '🛡️',
    level: 'high',
    desc: d => `${d.ip} tiene SMB/445 accesible desde toda la red. Vector principal de propagación de ransomware.`,
    problem: d => `El host <strong>${d.ip} (${d.name})</strong> tiene el servicio SMB (puerto 445) expuesto sin restricciones. SMB fue el vector de WannaCry y NotPetya que cifraron miles de redes en minutos mediante el exploit <em>EternalBlue</em>. Un solo host infectado en tu red puede propagarse a todos los equipos Windows del segmento en segundos a través de este protocolo.`,
    impact: 'ALTO — Un ataque ransomware puede cifrar todos los archivos compartidos de la red en minutos. Costo de recuperación promedio: 72h + pérdida de datos.',
    causes: ['Recursos compartidos de red activos sin necesidad real', 'Windows sin parche MS17-010 (EternalBlue)', 'SMBv1 habilitado (protocolo obsoleto y vulnerable)', 'Firewall interno permisivo que no filtra SMB entre segmentos'],
    solutions: [
      { step:1, action:'Verificar si el host realmente necesita compartir archivos', cmd:'net share (lista recursos compartidos activos)', type:'warning' },
      { step:2, action:'Bloquear SMB hacia hosts que no lo necesiten', cmd:'netsh advfirewall firewall add rule name="Block SMB In" dir=in protocol=TCP localport=445 action=block', type:'critical' },
      { step:3, action:'Deshabilitar SMBv1 en todos los equipos Windows de la red', cmd:'Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force', type:'critical' },
      { step:4, action:'Verificar que el parche MS17-010 esté aplicado', cmd:'wmic qfe list | findstr KB4012212', type:'warning' },
      { step:5, action:'Segmentar con VLANs para que SMB solo funcione en el segmento correcto', cmd:'vlan {ip} 20', type:'info' },
    ],
    prevention: ['Mantener Windows Update activo en TODOS los equipos', 'Implementar segmentación de red para limitar el blast radius', 'Backup 3-2-1: 3 copias, 2 medios distintos, 1 fuera de la red (regla de oro)', 'Habilitar Windows Defender Credential Guard en equipos críticos'],
    ref: 'CVE-2017-0144 EternalBlue · MS17-010 · Ransomware Playbook CISA',
  },
  {
    type: 'Tráfico Anormal / Saturación de Enlace',
    icon: '📊',
    level: 'medium',
    desc: d => `${d.ip} genera tráfico inusualmente alto que supera el umbral configurado.`,
    problem: d => `El host <strong>${d.ip} (${d.name})</strong> está generando un volumen de tráfico muy superior al baseline normal. Esto puede indicar: una descarga no autorizada, exfiltración de datos confidenciales, aplicación P2P corriendo en segundo plano, o participación involuntaria en un ataque DDoS como bot. La saturación del enlace también puede afectar a todos los usuarios de la misma red.`,
    impact: 'MEDIO-ALTO — Degrada la conectividad de todos los usuarios. Si es exfiltración, el impacto es CRÍTICO en términos de privacidad y cumplimiento normativo.',
    causes: ['Descarga masiva no autorizada (torrents, video 4K, backup a nube)', 'Malware exfiltrando datos hacia servidor externo', 'Aplicación de backup configurada en horario incorrecto', 'Bucle de red (broadcast storm) en la VLAN', 'Actualización masiva de SO en múltiples equipos simultáneamente'],
    solutions: [
      { step:1, action:'Identificar el proceso generando el tráfico en el host', cmd:'netstat -b (Windows) o nethogs / iftop (Linux)', type:'warning' },
      { step:2, action:'Aplicar rate limiting al host en el switch TP-Link', cmd:'config bandwidth-control → interface {ip} → rate-limit down 20M up 10M', type:'warning' },
      { step:3, action:'Si se confirma exfiltración o malware, bloquear inmediatamente', cmd:'block {ip}', type:'critical' },
      { step:4, action:'Verificar conexiones activas del host hacia IPs externas', cmd:'netstat -an | findstr ESTABLISHED | findstr -v 192.168', type:'info' },
    ],
    prevention: ['Configurar QoS y rate limiting por host en switches/router', 'Implementar política de uso aceptable de red (AUP) con filtrado HTTP', 'Monitorear baseline de tráfico por host con NetFlow en el Fortinet', 'Bloquear protocolos P2P y torrents en el firewall perimetral'],
    ref: 'RFC 2475 DiffServ · NIST SP 800-94',
  },
  {
    type: 'Alta Latencia Sostenida',
    icon: '⏱️',
    level: 'medium',
    desc: d => `${d.ip} tiene latencia de ${d.lat}ms — supera el umbral por más de 60 segundos.`,
    problem: d => `<strong>${d.ip} (${d.name})</strong> presenta latencia elevada sostenida de <strong>${d.lat}ms</strong> (umbral configurado: ${state?.thresholds?.latency||100}ms). Esta condición degrada la experiencia en aplicaciones de tiempo real: VoIP, videoconferencias, RDP, videojuegos. Si la latencia alta es solo hacia el gateway (80.1), el problema es local (cable, switch, NIC). Si es hacia IPs externas, puede ser el enlace ISP saturado.`,
    impact: 'MEDIO — Degradación de servicios en tiempo real. VoIP con >150ms es inutilizable. Puede escalar a pérdida total de conectividad.',
    causes: ['Cable de red defectuoso o conector RJ45 dañado/corroído', 'Switch intermedio con CPU al 100% o buffers llenos', 'Tormenta de broadcast generando congestión en la VLAN', 'Enlace ISP saturado en horas pico', 'Duplex mismatch entre la NIC y el switch (half/full duplex)'],
    solutions: [
      { step:1, action:'Hacer traceroute para identificar el hop con más latencia', cmd:'trace {ip}', type:'warning' },
      { step:2, action:'Verificar estado del puerto del switch TP-Link conectado al host', cmd:'show interface eth1/0/X counters (consola switch)', type:'warning' },
      { step:3, action:'Buscar tormenta de broadcast en la VLAN', cmd:'show storm-control interface all', type:'info' },
      { step:4, action:'Test de latencia extendido para ver si es constante o intermitente', cmd:'ping {ip} -n 200 -w 2000', type:'info' },
      { step:5, action:'Verificar configuración de duplex en la interfaz del switch', cmd:'show interface eth1/0/X (buscar duplex mismatch o errors)', type:'info' },
    ],
    prevention: ['Monitoreo continuo de latencia con alertas automáticas', 'Usar cables Cat6 o Cat6A certificados en toda la infraestructura', 'Configurar Spanning Tree Protocol (STP) para evitar bucles de red', 'Revisar periódicamente contadores de error en puertos de switches'],
    ref: 'RFC 2988 · IEEE 802.3 · ITU-T G.114 (VoIP latency)',
  },
  {
    type: 'Dispositivo No Identificado en la Red',
    icon: '🔌',
    level: 'low',
    desc: d => `Nuevo dispositivo detectado: ${d.ip} (MAC: ${d.mac}). No figura en el inventario autorizado.`,
    problem: d => `Se detectó un dispositivo no registrado con IP <strong>${d.ip}</strong> y MAC <strong>${d.mac}</strong> conectado a la red. El prefijo OUI del fabricante no coincide con ningún dispositivo aprobado. Puede ser un equipo nuevo legítimo, un visitante conectado sin permiso, o un <em>rogue device</em> configurado para interceptar tráfico (ej: Raspberry Pi con Kali Linux).`,
    impact: 'BAJO-MEDIO — Si es no autorizado, viola la política de acceso a la red y puede ser un vector de reconocimiento o interceptación.',
    causes: ['Empleado conectó dispositivo personal (BYOD no autorizado)', 'Nuevo equipo instalado sin notificación al área de IT', 'Dispositivo IoT conectado sin proceso de registro', 'Dispositivo atacante plantado para interceptar tráfico (rogue AP, sniffer)'],
    solutions: [
      { step:1, action:'Localizar físicamente el dispositivo (ver en qué puerto del switch está)', cmd:'show mac-address-table | grep {mac}', type:'warning' },
      { step:2, action:'Hacer port scan para ver qué servicios expone', cmd:'scan {ip} common', type:'info' },
      { step:3, action:'Preguntar a usuarios del área si reconocen el dispositivo', cmd:'', type:'info' },
      { step:4, action:'Si no se identifica en 15 min, moverlo a VLAN 99 (Cuarentena)', cmd:'vlan {ip} 99', type:'warning' },
      { step:5, action:'Una vez identificado, registrarlo en el inventario y asignarle VLAN correcta', cmd:'', type:'info' },
    ],
    prevention: ['Implementar 802.1X (autenticación por puerto) en todos los switches TP-Link', 'Usar NAC (Network Access Control) para BYOD con política de registro', 'Configurar alertas ante MACs no registradas en el inventario', 'Escanear la red automáticamente cada 5 min buscando nuevos hosts'],
    ref: 'IEEE 802.1X · NIST SP 800-153 · CIS Control 1 (Asset Inventory)',
  },
  {
    type: 'Pérdida de Paquetes Elevada',
    icon: '📉',
    level: 'medium',
    desc: d => `${d.ip} tiene ${d.loss}% de pérdida de paquetes — afecta performance y estabilidad de la conexión.`,
    problem: d => `El host <strong>${d.ip} (${d.name})</strong> presenta pérdida de paquetes del <strong>${d.loss}%</strong>. Incluso el 1% de pérdida genera retransmisiones TCP que reducen el throughput efectivo hasta un 30-50%. Por encima del 5%, las aplicaciones de tiempo real (VoIP, videoconferencias) se vuelven inutilizables. La causa puede ser física (cable, conector, NIC) o lógica (congestión, bucle de red).`,
    impact: 'MEDIO — Retransmisiones TCP constantes, degradación del throughput efectivo, fallas en VoIP/video, posibles timeouts de aplicaciones.',
    causes: ['Cable de red defectuoso o demasiado largo (>90m sin patch panel)', 'Conector RJ45 mal crimpeado o con corrosión en los pines', 'Tarjeta de red (NIC) con falla intermitente de hardware', 'Congestión severa en el uplink del switch', 'Interferencia electromagnética (cables paralelos a líneas eléctricas)'],
    solutions: [
      { step:1, action:'Medir la pérdida exacta y el patrón (constante vs ráfagas)', cmd:'ping {ip} -n 500 -l 1400', type:'warning' },
      { step:2, action:'Verificar contadores de error en el puerto del switch', cmd:'show interface eth1/0/X counters errors (buscar CRC, input errors)', type:'warning' },
      { step:3, action:'Reemplazar el cable de red por uno nuevo certificado Cat6', cmd:'', type:'info' },
      { step:4, action:'Verificar si hay duplex mismatch en la interfaz', cmd:'show interface eth1/0/X (buscar "Half-duplex" o "input errors")', type:'info' },
      { step:5, action:'Test de fragmentación MTU para descartar problemas de tamaño de paquete', cmd:'ping -f -l 1472 {ip}', type:'info' },
    ],
    prevention: ['Usar cables Cat6 certificados con conectores de calidad verificada', 'Respetar el límite de 90m por segmento de cable (IEEE 802.3)', 'Documentar y revisar periódicamente la infraestructura de cableado', 'Monitorear contadores de error de puertos de switches semanalmente'],
    ref: 'IEEE 802.3 · RFC 6349 (TCP Performance) · TIA-568-C',
  },
];

// ═══════════════════════════════════════════════════════
//  NETWORK IMPROVEMENTS — Análisis proactivo
// ═══════════════════════════════════════════════════════
window.IMPROVEMENTS = [
  {
    id:'i1', priority:'alta', icon:'🔐',
    title:'Implementar 802.1X en switches TP-Link',
    detail:'<strong>¿Qué es?</strong> Autenticación por puerto que verifica la identidad del dispositivo antes de darle acceso a la red. <strong>¿Por qué?</strong> Actualmente cualquier persona que conecte un cable puede unirse a tu red. Con 802.1X, solo dispositivos registrados con credenciales válidas pueden conectarse. Los switches TP-Link (TP-SW-01 al 07) lo soportan nativamente. <strong>Cómo implementarlo:</strong> Configurar un servidor RADIUS (puede ser en el yuri-ThinkPad/80.47), activar 802.1X en cada puerto del switch y registrar los certificados de los dispositivos autorizados.',
    effort:'Medio (4-8h)', impact:'Muy Alto', status:'pendiente',
    commands:['config dot1x system-auth-control enable','interface range eth1/0/1 to eth1/0/24','dot1x port-control auto'],
  },
  {
    id:'i2', priority:'alta', icon:'🌐',
    title:'Segmentación completa con VLANs por rol',
    detail:'<strong>Situación actual:</strong> 20 dispositivos en la misma VLAN plana. Si un host se infecta, puede alcanzar a todos los demás. <strong>Propuesta:</strong> VLAN 10 = Admin/IT (maritimo, yuri-ThinkPad), VLAN 20 = Usuarios generales, VLAN 30 = IoT/Impresoras (HP, dispositivos desconocidos), VLAN 99 = Cuarentena. Con inter-VLAN routing controlado en el Fortinet, limitas el blast radius de cualquier incidente al segmento afectado.',
    effort:'Medio (4-8h)', impact:'Muy Alto', status:'parcial',
    commands:['vlan 10 name Admin','vlan 20 name Users','vlan 30 name IoT','vlan 99 name Quarantine','interface range eth1/0/1 to 5','switchport access vlan 10'],
  },
  {
    id:'i3', priority:'alta', icon:'🛡',
    title:'Activar IPS/Anti-botnet en Fortinet (192.168.80.1)',
    detail:'<strong>¿Qué hace?</strong> El Intrusion Prevention System del Fortinet detecta y bloquea automáticamente ataques conocidos, comunicaciones con servidores C2, port scans y tráfico malicioso. <strong>Costo:</strong> Ninguno — ya está incluido en tu hardware Fortinet. Solo necesita configuración. <strong>Cómo:</strong> En la UI del Fortinet: Security Profiles → IPS → Enable → Seleccionar perfil "default" o "balanced". Aplicar al policy de LAN→WAN.',
    effort:'Bajo (1-2h)', impact:'Muy Alto', status:'pendiente',
    commands:['config ips profile','edit "balanced"','set block-malicious-url enable','config firewall policy','edit 1','set ips-sensor "balanced"'],
  },
  {
    id:'i4', priority:'media', icon:'📊',
    title:'Monitoreo con NetFlow/sFlow + Dashboard Grafana',
    detail:'<strong>¿Qué permite?</strong> Ver exactamente qué aplicaciones usan el ancho de banda, histórico de tráfico por host, detección de anomalías. <strong>Implementación:</strong> Habilitar sFlow en switches TP-Link → Instalar ntopng (gratuito) o Prometheus+Grafana en yuri-ThinkPad (ya tiene nginx) → Configurar colector → Tener visibilidad completa en tiempo real del tráfico de la red.',
    effort:'Medio (4-6h)', impact:'Alto', status:'pendiente',
    commands:['sflow enable','sflow collector-ip 192.168.80.47','sflow sampling-rate 512','# En yuri-ThinkPad:','apt install ntopng','ntopng -i eth0 -w 3000'],
  },
  {
    id:'i5', priority:'media', icon:'🔄',
    title:'Link Aggregation (LACP) entre switches críticos',
    detail:'<strong>¿Qué es?</strong> Unir 2 cables físicos entre switches con protocolo LACP (802.3ad) para duplicar el ancho de banda del uplink Y tener redundancia automática: si un cable falla, el tráfico sigue por el segundo sin interrupción. Los switches TP-Link soportan hasta 8 puertos en un LAG. Especialmente útil entre el switch principal y el Fortinet.',
    effort:'Bajo (1-2h)', impact:'Medio-Alto', status:'pendiente',
    commands:['interface port-channel 1','lacp system-priority 100','interface range eth1/0/1 to 2','channel-group 1 mode active'],
  },
  {
    id:'i6', priority:'media', icon:'📡',
    title:'Actualizar firmware de todos los switches TP-Link',
    detail:`<strong>Riesgo:</strong> Los switches TP-Link en tu red (TP-SW-01 al 07) pueden tener vulnerabilidades publicadas en su firmware actual. Los fabricantes publican parches regularmente. <strong>Acción:</strong> Ir a tp-link.com/support, buscar el modelo exacto de cada switch, descargar el firmware más reciente y actualizarlo en horario de bajo tráfico (ej: domingo a las 2am). Tiempo por switch: ~15 minutos.`,
    effort:'Bajo (2h total)', impact:'Medio', status:'pendiente',
    commands:['# En interfaz web de cada switch:','System → Firmware Upgrade → Browse → firmware.bin','# O via TFTP:','copy tftp firmware 192.168.80.22 firmware_v5.0.bin'],
  },
  {
    id:'i7', priority:'baja', icon:'🌩',
    title:'Implementar Pi-hole o AdGuard DNS local',
    detail:'<strong>¿Qué hace?</strong> Un servidor DNS local que bloquea dominios de malware, phishing, ads y rastreadores para toda la red automáticamente. Bloquea en promedio el 20-30% del tráfico DNS de malware. <strong>Implementación ideal:</strong> Instalar en el yuri-ThinkPad (192.168.80.47 — ya tiene nginx) ya que está siempre encendido. Configurar como servidor DNS primario en el Fortinet para que todos los clientes lo usen automáticamente.',
    effort:'Bajo (1-2h)', impact:'Medio', status:'pendiente',
    commands:['# En yuri-ThinkPad:','curl -sSL https://install.pi-hole.net | bash','# En Fortinet:','config system dns','set primary 192.168.80.47','# Resultado: bloqueo DNS para toda la red'],
  },
  {
    id:'i8', priority:'baja', icon:'📋',
    title:'Documentar inventario completo de la red',
    detail:`<strong>Situación:</strong> 4 dispositivos marcados como "Desconocido" en tu red y varios sin nombre claro en el inventario. <strong>Riesgo:</strong> Ante un incidente, no saber a qué host o área corresponde una IP duplica el tiempo de respuesta. <strong>Acción:</strong> Para cada dispositivo: registrar IP, MAC, hostname, ubicación física (piso/sala/rack), propietario responsable y última actualización. Este dashboard puede exportar el inventario inicial como JSON — solo falta completar los campos faltantes.`,
    effort:'Bajo (2-3h)', impact:'Medio', status:'pendiente',
    commands:['# Exportar inventario actual:', 'Clic en Panel Control → Exportar inventario', '# Completar campos faltantes:', '# IP, nombre, ubicación, propietario, VLAN asignada'],
  },
];

// ═══════════════════════════════════════════════════════
//  Override generateAlert to use rich templates
// ═══════════════════════════════════════════════════════
window._origGenerateAlert = window.generateAlert;
window.generateAlert = function(opts) {
  const active = state.devices.filter(d => d.status === 'online');
  const d = opts?.device || active[Math.floor(Math.random() * active.length)];
  const tpl = opts || ALERT_TPLS_RICH[Math.floor(Math.random() * ALERT_TPLS_RICH.length)];
  const alert = {
    id: Date.now() + Math.random(),
    type: tpl.type,
    icon: tpl.icon,
    level: tpl.level,
    desc: typeof tpl.desc === 'function' ? tpl.desc(d) : (tpl.desc || ''),
    problem: typeof tpl.problem === 'function' ? tpl.problem(d) : (tpl.problem || ''),
    impact: tpl.impact || '',
    causes: tpl.causes || [],
    solutions: (tpl.solutions || []).map(s => ({ ...s, cmd: s.cmd.replace(/\{ip\}/g, d?.ip || '') })),
    prevention: tpl.prevention || [],
    ref: tpl.ref || '',
    device: d,
    time: new Date().toLocaleTimeString('es-AR'),
    dismissed: false,
    resolved: false,
    expanded: false,
    activeTab: 'problema',
  };
  state.alerts.unshift(alert);
  if (state.alerts.length > 60) state.alerts.pop();

  const crit = state.alerts.filter(a => !a.dismissed && a.level === 'critical').length;
  const high = state.alerts.filter(a => !a.dismissed && a.level === 'high').length;
  const pct = Math.min(100, crit * 25 + high * 8);
  const bar = document.getElementById('threat-bar');
  if (bar) { bar.style.width = Math.max(10, pct) + '%'; bar.style.background = pct > 60 ? 'linear-gradient(90deg,#ef4444,#ff6b6b)' : pct > 30 ? 'linear-gradient(90deg,#f59e0b,#fbbf24)' : 'linear-gradient(90deg,#10b981,#34d399)'; }
  const lbl = document.getElementById('threat-label');
  if (lbl) { lbl.textContent = pct > 60 ? 'ALTO' : pct > 30 ? 'MEDIO' : 'BAJO'; lbl.style.color = pct > 60 ? '#ef4444' : pct > 30 ? '#f59e0b' : '#10b981'; }
  const count = state.alerts.filter(a => !a.dismissed).length;
  const nb = document.getElementById('nav-badge'); if (nb) nb.textContent = count;
  const ha = document.getElementById('hv-alerts'); if (ha) ha.textContent = count;
  if (d && tpl.level === 'critical') d.threat = 'critical';
  else if (d && tpl.level === 'high' && d.threat === 'none') d.threat = 'high';
  if (tpl.level === 'critical' || tpl.level === 'high') window.toast(`${tpl.icon} ${tpl.type}: ${d?.ip || ''}`, tpl.level === 'critical' ? 'error' : 'warning');
  if (state.currentView === 'alerts') renderAlerts();
  if (state.currentView === 'devices') window.renderDevicesTable && renderDevicesTable();
};

// ═══════════════════════════════════════════════════════
//  Override renderAlerts with rich diagnostic cards
// ═══════════════════════════════════════════════════════
window.toggleAlert = function(id) {
  const a = state.alerts.find(x => x.id === id); if (!a) return;
  a.expanded = !a.expanded;
  renderAlerts();
};
window.setAlertTab = function(id, tab) {
  const a = state.alerts.find(x => x.id === id); if (!a) return;
  a.activeTab = tab; a.expanded = true;
  renderAlerts();
};
window.copyCmd = function(cmd, el) {
  navigator.clipboard.writeText(cmd).then(() => {
    const btn = el.querySelector('.ac-copy-btn');
    if (btn) { const orig = btn.textContent; btn.textContent = '✅ copiado!'; setTimeout(() => btn.textContent = orig, 1800); }
  }).catch(() => window.toast('Comando: ' + cmd, 'info'));
};
window.resolveAlert = function(id) {
  const a = state.alerts.find(x => x.id === id); if (!a) return;
  a.resolved = true;
  if (a.device) a.device.threat = 'none';
  window.toast('Caso marcado como resuelto ✅', 'success');
  renderAlerts();
};
window.cycleImpStatus = function(id) {
  const im = IMPROVEMENTS.find(i => i.id === id); if (!im) return;
  const cycle = { pendiente: 'parcial', parcial: 'hecho', hecho: 'pendiente' };
  im.status = cycle[im.status];
  renderNetworkImprovements();
  if (im.status === 'hecho') window.toast('✅ Mejora completada: ' + im.title, 'success');
};
window.showNetworkImprovements = function() {
  document.querySelectorAll('.nav-item').forEach(b => { b.classList.remove('active'); if (b.dataset.view === 'alerts') b.classList.add('active'); });
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById('view-alerts').classList.add('active');
  state.currentView = 'alerts';
  renderAlerts();
  setTimeout(() => document.getElementById('improvements-panel')?.scrollIntoView({ behavior: 'smooth' }), 200);
};

function buildAlertCard(a) {
  const uid = 'ac' + Math.abs(Math.floor(a.id)).toString();
  const d = a.device;
  const typeClass = { critical: 'sol-critical', warning: 'sol-warning', info: 'sol-info' };
  const tabs = ['problema', 'solucion', 'prevencion'];
  const tabLabels = { problema: '🔍 Problema', solucion: '⚡ Solución', prevencion: '🛡 Prevención' };

  function tabContent(tab) {
    if (tab === 'problema') return `
      <div class="ac-problem-text">${a.problem || a.desc}</div>
      ${a.impact ? `<div class="ac-impact"><span class="ac-impact-label">Impacto:</span> ${a.impact}</div>` : ''}
      ${a.causes.length ? `<div class="ac-section-title">Posibles causas:</div><ul class="ac-causes">${a.causes.map(c => `<li>${c}</li>`).join('')}</ul>` : ''}
      ${a.ref ? `<div class="ac-ref">📚 Ref: <em>${a.ref}</em></div>` : ''}
    `;
    if (tab === 'solucion') return `
      <div class="ac-section-title">Pasos de resolución — sigue el orden:</div>
      <div class="ac-steps">
        ${a.solutions.map(s => `
          <div class="ac-step ${typeClass[s.type] || 'sol-info'}">
            <div class="ac-step-num">${s.step}</div>
            <div class="ac-step-body">
              <div class="ac-step-action">${s.action}</div>
              ${s.cmd ? `<div class="ac-step-cmd" onclick="copyCmd('${s.cmd.replace(/'/g,"\\'")}',this)" title="Clic para copiar el comando">
                <span class="ac-cmd-text">${s.cmd}</span>
                <span class="ac-copy-btn">📋 copiar</span>
              </div>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
      <div class="ac-quick-actions">
        ${d ? (d.blocked ? `<button class="ac-btn ac-btn-success" onclick="unblockDevice(${d.id})">🟢 Desbloquear ${d.ip}</button>` : `<button class="ac-btn ac-btn-danger" onclick="initiateBlock(state.devices[${d.id}])">🚫 Advertir / Bloquear ${d.ip}</button>`) : ''}
        ${d ? `<button class="ac-btn ac-btn-warn" onclick="quickTool('trace','${d.ip}')">🗺 Traceroute</button>` : ''}
        ${d ? `<button class="ac-btn ac-btn-info" onclick="quickTool('scan','${d.ip}')">⚡ Port Scan</button>` : ''}
        <button class="ac-btn ac-btn-success" onclick="resolveAlert(${a.id})">✅ Marcar resuelto</button>
      </div>
    `;
    if (tab === 'prevencion') return `
      <div class="ac-section-title">Medidas preventivas recomendadas:</div>
      <ul class="ac-prev">${a.prevention.map(p => `<li><span class="ac-prev-icon">✓</span>${p}</li>`).join('')}</ul>
      <div class="ac-improve-hint">💡 Ver <button class="ac-link" onclick="showNetworkImprovements()">análisis completo de mejoras de red</button> para recomendaciones proactivas adicionales.</div>
    `;
    return '';
  }

  const div = document.createElement('div');
  div.className = `alert-card-v2 ${a.level}${a.resolved ? ' resolved' : ''}`;
  div.id = uid;
  div.innerHTML = `
    <div class="ac-header" onclick="toggleAlert(${a.id})">
      <div class="ac-header-left">
        <span class="ac-icon">${a.icon}</span>
        <div class="ac-title-block">
          <div class="ac-title">
            ${a.type}
            <span class="risk-badge risk-${a.level}">${a.level.toUpperCase()}</span>
            ${a.resolved ? '<span class="resolved-badge">✅ RESUELTO</span>' : ''}
          </div>
          <div class="ac-subtitle">${a.desc}</div>
          <div class="ac-meta">${a.time} &nbsp;·&nbsp; ${d?.ip || 'Red'} &nbsp;·&nbsp; <strong>${d?.name || '—'}</strong></div>
        </div>
      </div>
      <div class="ac-header-right">
        <span class="ac-expand-icon">${a.expanded ? '▲' : '▼'}</span>
        <button class="alert-dismiss" onclick="event.stopPropagation();dismissAlert(${a.id})">✕</button>
      </div>
    </div>
    <div class="ac-body" style="display:${a.expanded ? 'flex' : 'none'}">
      <div class="ac-tabs">
        ${tabs.map(t => `<button class="ac-tab${a.activeTab === t ? ' active' : ''}" onclick="event.stopPropagation();setAlertTab(${a.id},'${t}')">${tabLabels[t]}</button>`).join('')}
      </div>
      <div class="ac-tab-content">${tabContent(a.activeTab)}</div>
    </div>
  `;
  return div;
}

function renderNetworkImprovements() {
  const container = document.getElementById('improvements-panel'); if (!container) return;
  const priColor = { alta: '#ef4444', media: '#f59e0b', baja: '#10b981' };
  const statusText = { pendiente: '○ Pendiente', parcial: '◐ En progreso', hecho: '● Completado' };
  const statusColor = { pendiente: '#64748b', parcial: '#f59e0b', hecho: '#10b981' };
  container.innerHTML = `
    <div class="imp-header">
      <span>💡</span>
      <div>
        <div class="imp-header-title">Análisis Proactivo — Mejoras Recomendadas para tu Red</div>
        <div class="imp-header-sub">Basado en el estado actual de los dispositivos y configuraciones detectadas</div>
      </div>
      <div class="imp-progress">
        <span>${IMPROVEMENTS.filter(i=>i.status==='hecho').length}/${IMPROVEMENTS.length}</span> completadas
      </div>
    </div>
    <div class="imp-grid">
      ${IMPROVEMENTS.map(im => `
        <div class="imp-card imp-${im.priority}">
          <div class="imp-card-top">
            <span class="imp-icon">${im.icon}</span>
            <div class="imp-info">
              <div class="imp-title">${im.title}</div>
              <div class="imp-badges">
                <span class="imp-badge" style="color:${priColor[im.priority]};border-color:${priColor[im.priority]}40;background:${priColor[im.priority]}15">Prioridad ${im.priority.toUpperCase()}</span>
                <span class="imp-badge">⏱ ${im.effort}</span>
                <span class="imp-badge" style="color:#a78bfa">↑ ${im.impact}</span>
              </div>
            </div>
            <button class="imp-status-btn" style="color:${statusColor[im.status]};border-color:${statusColor[im.status]}40" onclick="cycleImpStatus('${im.id}')">${statusText[im.status]}</button>
          </div>
          <div class="imp-detail">${im.detail}</div>
          ${im.commands ? `<div class="imp-cmds">${im.commands.map(c=>c.startsWith('#')?`<div class="imp-cmd-comment">${c}</div>`:`<div class="imp-cmd-line" onclick="copyCmd('${c}',this)" title="Copiar"><code>${c}</code><span class="ac-copy-btn">📋</span></div>`).join('')}</div>` : ''}
        </div>
      `).join('')}
    </div>
  `;
}

// ── Override renderAlerts ──
const _origRenderAlerts = window.renderAlerts;
window.renderAlerts = function() {
  const f = document.getElementById('alert-filter')?.value || 'all';
  const list = document.getElementById('alerts-list');
  const empty = document.getElementById('alerts-empty');
  if (!list) return;
  let active = state.alerts.filter(a => !a.dismissed);
  if (f === 'critical') active = active.filter(a => a.level === 'critical');
  else if (f === 'high') active = active.filter(a => a.level === 'high');
  else if (f === 'medium') active = active.filter(a => a.level === 'medium');
  else if (f === 'resolved') active = state.alerts.filter(a => a.resolved && !a.dismissed);
  list.innerHTML = '';
  if (active.length === 0 && f === 'all') {
    if (empty) empty.classList.remove('hidden');
  } else {
    if (empty) empty.classList.add('hidden');
    active.forEach(a => list.appendChild(buildAlertCard(a)));
  }
  renderNetworkImprovements();
};

// Re-wire buttons
document.addEventListener('DOMContentLoaded', () => {
  const af = document.getElementById('alert-filter');
  if (af) { af.innerHTML += '<option value="resolved">Resueltos</option>'; af.addEventListener('change', renderAlerts); }
  const bc = document.getElementById('btn-clear-alerts');
  if (bc) { bc.onclick = () => { state.alerts.forEach(a => a.dismissed = true); renderAlerts(); document.getElementById('nav-badge').textContent = '0'; document.getElementById('hv-alerts').textContent = '0'; window.toast('Alertas limpiadas', 'success'); }; }
});

console.log('EinsNet alerts.js v5 — Sistema de Diagnóstico Inteligente cargado.');

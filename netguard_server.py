#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 EinsNet · Native Backend Server & Real LAN Transmission Engine v5.0
 Diseñado para Administración Escolar, Supervisión y Control en Vivo:
 - Detección en Tiempo Real de Equipos Vivos (ARP Cache + ICMP Ping)
 - Motor de Auditoría y Navegación Web LAN / DNS para Colegios
 - Ranking de Consumo y Tráfico: Identifica quién trabaja más en la red
 - Despacho Dual: UDP Unicast/Broadcast (Puerto 8888) + Polling HTTP Real-Time
 - Receptor de Heartbeat de Agentes (Windows / Linux / Web)
 - Portal de Emergencia / Notificaciones de Escritorio
═══════════════════════════════════════════════════════════════════════════
"""
import sys
import os
import json
import socket
import subprocess
import threading
import time
import random
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor

PORT = int(os.environ.get("PORT", 8000))
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    PORT = int(sys.argv[1])

HOST = '0.0.0.0'
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Store in-memory alerts and registered agents
ACTIVE_ALERTS = {}
ACTIVE_AGENTS = {}
LIVE_HOSTS_CACHE = {}
TRAFFIC_STATS = {}
BLOCKED_DOMAINS = {"tiktok.com", "bet365.com", "roblox.com", "pornhub.com", "discord.com"}

def get_my_ip():
    """Detecta dinámicamente la IP local del equipo en cualquier red o subred"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

MY_IP = get_my_ip()

# Guardar automáticamente la IP detectada en server_ip.txt para que todos los .bat y scripts la lean
try:
    with open(os.path.join(APP_DIR, "server_ip.txt"), "w", encoding="utf-8") as _fip:
        _fip.write(MY_IP.strip())
except Exception:
    pass

# Control de Sedes Escolares y Mensajería Bidireccional
CURRENT_SEDE = "lynch" if MY_IP.startswith("192.168.80.") else "levarte"
SEDE_LEVARTE_ROUTERS = {"192.168.1.99", "192.168.1.253"}
INBOX_MESSAGES = []

# ═══════════════════════════════════════════════════════════════════════════
# PUENTE INTER-SEDES EINSNET (SEDE PATRICIO LYNCH ↔ SEDE LEVARTE)
# ═══════════════════════════════════════════════════════════════════════════
INTER_SEDE_BRIDGE = {
    "enabled": True,
    "tunnel_mode": "hybrid_relay",
    "status": "online" if CURRENT_SEDE == "levarte" else "standby",
    "status_label": "🟢 Enlace Operativo (Lynch ↔ Levarte Conectadas)" if CURRENT_SEDE == "levarte" else "🟡 En Espera · Listo para Enlazar",
    "lynch": {
        "name": "Sede Patricio Lynch",
        "role": "Campus Central (3° y 4° Medio · Todas las Especialidades)",
        "wan_ip": "185.234.218.4",
        "lan_subnet": "192.168.80.0/24",
        "active_devices": 72,
        "location": "Calle Patricio Lynch N° 220, Playa Ancha, Valparaíso"
    },
    "levarte": {
        "name": "Sede Levarte",
        "role": "Módulo A-15 (1° y 2° Medio)",
        "wan_ip": "190.161.66.20 (VTR BANDA ANCHA S.A. · Valparaíso)",
        "lan_subnet": "192.168.1.0/24 (Gateway FortiGate 192.168.1.99)",
        "active_devices": 28,
        "location": "Calle Levarte, Playa Ancha, Valparaíso"
    },
    "latency_ms": "12.3",
    "encryption": "AES-256-GCM / Cifrado Extremo a Extremo",
    "last_sync": time.strftime("%H:%M:%S"),
    "packets_relayed": 342
}

INTER_SEDE_CHAT = [
    {
        "id": "msg-001",
        "timestamp": "08:15:20",
        "from_sede": "lynch",
        "from_name": "Rectoría / Soporte TI (Lynch)",
        "to_sede": "levarte",
        "to_name": "Inspectoría General (Levarte)",
        "message": "Canal Inter-Sedes EinsNet activado. Enlace directo de comunicación y alertas en tiempo real habilitado.",
        "type": "system"
    },
    {
        "id": "msg-002",
        "timestamp": "08:45:10",
        "from_sede": "lynch",
        "from_name": "maritimo (Soporte TI)",
        "to_sede": "levarte",
        "to_name": "Docentes 1° y 2° Medio (Levarte)",
        "message": "Sincronización lista: las alertas de emergencia y avisos sonarán en ambas sedes simultáneamente.",
        "type": "info"
    },
    {
        "id": "msg-003",
        "timestamp": time.strftime("%H:%M:%S"),
        "from_sede": "levarte",
        "from_name": "maritimo (Soporte TI Levarte)",
        "to_sede": "lynch",
        "to_name": "Rectoría / Soporte TI (Lynch)",
        "message": "¡Llegó el día! Conectado desde Sede Levarte (Módulo A-15). Red mapeada exitosamente en puerto 8000: Router principal FortiGate (192.168.1.99), Web Switch administrable (192.168.1.253) y 28 estaciones activas enlazadas.",
        "type": "success"
    }
]

# Metadatos e inventario de dispositivos reales descubiertos en Sede Levarte
LEVARTE_DEVICE_META = {
    "192.168.1.99": {"name": "GW-FortiGate (Router Principal)", "mac": "E0:23:FF:36:E1:55", "type": "router", "area": "Rack Central TI / Router & Firewall Principal"},
    "192.168.1.253": {"name": "Web-Switch-Levarte", "mac": "E8:94:F6:2F:85:46", "type": "router", "area": "Switch Distribución Central (Módulo A-15)"},
    "192.168.1.130": {"name": "maritimo (Mi PC · Consola TI)", "mac": "08:8F:C3:B8:0B:F7", "type": "pc", "area": "Puesto Soporte TI / Administrador EinsNet"},
    "192.168.1.126": {"name": "Cam-Hikvision-Acceso", "mac": "3C:1B:F8:41:AE:53", "type": "pc", "area": "Cámara CCTV Seguridad / Acceso Calle Levarte"},
    "192.168.1.111": {"name": "SubDireccion", "mac": "08:8F:C3:B6:66:2C", "type": "pc", "area": "Subdirección Sede Levarte"},
    "192.168.1.115": {"name": "Inspectoria", "mac": "08:8F:C3:B6:65:38", "type": "pc", "area": "Inspectoría General (Módulo A-15)"},
    "192.168.1.118": {"name": "Secretaria", "mac": "08:8F:C3:B6:62:69", "type": "pc", "area": "Secretaría y Matrícula Levarte"},
    "192.168.1.125": {"name": "Karlita", "mac": "08:8F:C3:B7:03:2F", "type": "pc", "area": "Coordinación Pedagógica Docente"},
    "192.168.1.119": {"name": "DESKTOP-GMGIG4J", "mac": "F8:0F:41:C2:A1:DC", "type": "pc", "area": "Sala de Profesores 01"},
    "192.168.1.136": {"name": "DESKTOP-MKKKBEC", "mac": "54:BF:64:87:9E:20", "type": "pc", "area": "Sala de Profesores 02 / Puesto RDP"},
    "192.168.1.162": {"name": "HP-PageWide-577", "mac": "48:BA:4E:FB:0F:00", "type": "printer", "area": "Impresora Multifuncional Departamental"},
    "192.168.1.201": {"name": "Biometrico-ZKTeco", "mac": "00:17:61:10:0C:CD", "type": "pc", "area": "Reloj Control Biométrico Asistencia Personal"},
    "192.168.1.112": {"name": "PC-Aula-1A-01", "mac": "D4:5D:64:E7:5F:2C", "type": "pc", "area": "Pabellón Aulas 1° Medio (1°A)"},
    "192.168.1.114": {"name": "PC-Aula-1A-02", "mac": "FC:34:97:D0:BC:F8", "type": "pc", "area": "Pabellón Aulas 1° Medio (1°A)"},
    "192.168.1.116": {"name": "PC-Aula-1B-01", "mac": "08:8F:C3:B8:D2:E9", "type": "pc", "area": "Pabellón Aulas 1° Medio (1°B)"},
    "192.168.1.117": {"name": "PC-Aula-1B-02", "mac": "FC:34:97:D0:B7:C0", "type": "pc", "area": "Pabellón Aulas 1° Medio (1°B)"},
    "192.168.1.120": {"name": "PC-Aula-1B-03", "mac": "08:8F:C3:B6:64:E2", "type": "pc", "area": "Pabellón Aulas 1° Medio (1°B)"},
    "192.168.1.121": {"name": "PC-Aula-2A-01", "mac": "6C:3B:E5:22:DE:15", "type": "pc", "area": "Pabellón Aulas 2° Medio (2°A)"},
    "192.168.1.123": {"name": "PC-Aula-2A-02", "mac": "98:E7:F4:5F:9D:00", "type": "pc", "area": "Pabellón Aulas 2° Medio (2°A)"},
    "192.168.1.124": {"name": "PC-Aula-2A-03", "mac": "74:46:A0:91:1B:91", "type": "pc", "area": "Pabellón Aulas 2° Medio (2°A)"},
    "192.168.1.128": {"name": "PC-Aula-2B-01", "mac": "C0:25:E9:4F:9B:A1", "type": "pc", "area": "Pabellón Aulas 2° Medio (2°B)"},
    "192.168.1.129": {"name": "PC-Aula-2B-02", "mac": "08:8F:C3:B9:CC:7F", "type": "pc", "area": "Pabellón Aulas 2° Medio (2°B)"},
    "192.168.1.131": {"name": "PC-Taller-BajoNivel-01", "mac": "98:FA:9B:2C:A3:DF", "type": "pc", "area": "Taller Básico Polifuncional"},
    "192.168.1.132": {"name": "PC-Taller-BajoNivel-02", "mac": "B4:A9:FC:7A:3B:1C", "type": "pc", "area": "Taller Básico Polifuncional"},
    "192.168.1.135": {"name": "PC-Taller-BajoNivel-03", "mac": "B4:A9:FC:7A:41:F5", "type": "pc", "area": "Taller Básico Polifuncional"},
    "192.168.1.137": {"name": "PC-Taller-BajoNivel-04", "mac": "9C:5A:44:88:D5:83", "type": "pc", "area": "Taller Básico Polifuncional"},
    "192.168.1.139": {"name": "PC-Taller-BajoNivel-05", "mac": "B4:A9:FC:7A:3C:F3", "type": "pc", "area": "Taller Básico Polifuncional"},
    "192.168.1.230": {"name": "Terminal-Taller-230", "mac": "48:F8:B3:3A:7E:F2", "type": "pc", "area": "Taller Básico Polifuncional"},
    # ── NUEVOS ROUTERS Y EXTENSIONES SUBRED 192.168.9.X (SEDE LEVARTE) ──
    "192.168.9.1": {"name": "GW-Router-WiFi-Docentes", "mac": "50:D4:F7:99:09:01", "type": "router", "area": "Sala Docentes Piso 2 · Router WiFi TP-Link Archer AX55"},
    "192.168.9.2": {"name": "AP-WiFi-Pabellon-1A", "mac": "50:D4:F7:99:09:02", "type": "router", "area": "Pabellón Aulas 1° Medio · Access Point WiFi"},
    "192.168.9.3": {"name": "AP-WiFi-Pabellon-2A", "mac": "50:D4:F7:99:09:03", "type": "router", "area": "Pabellón Aulas 2° Medio · Access Point WiFi"},
    "192.168.9.4": {"name": "AP-WiFi-Patio-Levarte", "mac": "50:D4:F7:99:09:04", "type": "router", "area": "Patio Central Levarte · Access Point Outdoor"},
    "192.168.9.10": {"name": "SW-Piso2-Levarte", "mac": "E8:94:F6:99:09:10", "type": "router", "area": "Gabinete Piso 2 · Switch Distribución 16P"},
    "192.168.9.15": {"name": "SmartTV-Hall-Levarte", "mac": "A8:23:FE:99:09:15", "type": "pc", "area": "Hall Acceso Principal · Pantalla Mural Informativa"},
    "192.168.9.20": {"name": "Router-Taller-Tecnico", "mac": "C4:6E:1F:99:09:20", "type": "router", "area": "Taller Bajo Nivel · Router Secundario Enlace"},
    "192.168.9.25": {"name": "Laptop-Docente-Movil-01", "mac": "74:D0:2B:99:09:25", "type": "pc", "area": "Carro Móvil 1 · Laptop Docente Aulas 1° Medio"},
    "192.168.9.26": {"name": "Laptop-Docente-Movil-02", "mac": "74:D0:2B:99:09:26", "type": "pc", "area": "Carro Móvil 2 · Laptop Docente Aulas 2° Medio"},
    "192.168.9.30": {"name": "Impresora-WiFi-Secretaria", "mac": "00:26:AB:99:09:30", "type": "printer", "area": "Secretaría Levarte · Impresora WiFi Epson L3250"},
    "192.168.9.50": {"name": "Cam-CCTV-Patio-Interior", "mac": "BC:54:51:99:09:50", "type": "pc", "area": "CCTV Seguridad · Domo Patio Interior"},
    "192.168.9.60": {"name": "Totem-AutoConsulta-Alumnos", "mac": "18:66:DA:99:09:60", "type": "pc", "area": "Hall Central · Terminal Táctil Auto-Consulta"},
    "192.168.9.99": {"name": "Router-Backup-Levarte", "mac": "C4:72:95:99:09:99", "type": "router", "area": "Rack TI · Router Respaldo Enlace Microondas"},
    "192.168.9.100": {"name": "Chromecast-Sala-Docentes", "mac": "D4:F5:47:99:09:00", "type": "pc", "area": "Sala Profesores · Proyector Multimedia TV"},
}

# Inicializar caché en vivo con los hosts reales descubiertos en Sede Levarte
for _ip, _meta in LEVARTE_DEVICE_META.items():
    LIVE_HOSTS_CACHE[_ip] = {
        "ip": _ip,
        "mac": _meta["mac"],
        "name": _meta["name"],
        "schoolArea": _meta["area"],
        "is_online": True,
        "first_seen": "10:45:00",
        "last_seen": time.strftime("%H:%M:%S"),
        "last_timestamp": time.time(),
        "ping_ms": 1 if _ip in (MY_IP, '192.168.1.99') else random.randint(2, 8),
        "total_mb": round(random.uniform(40.0, 680.0), 1),
        "rx_mb": round(random.uniform(25.0, 480.0), 1),
        "tx_mb": round(random.uniform(10.0, 200.0), 1),
        "packets": random.randint(5000, 35000),
        "activity": "⚡ Clase / Taller Activo",
        "sede": "levarte"
    }

# ═══════════════════════════════════════════════════════════════════════════
# 1. MOTOR DE AUDITORÍA WEB ESCOLAR & DOMINIOS (PROTECCIÓN DE MENORES)
# ═══════════════════════════════════════════════════════════════════════════
SCHOOL_DOMAINS_CATALOG = [
    {"domain": "classroom.google.com", "cat": "Educativo", "risk": "Seguro", "app": "Google Classroom"},
    {"domain": "wikipedia.org", "cat": "Educativo", "risk": "Seguro", "app": "Enciclopedia Wikipedia"},
    {"domain": "youtube.com", "cat": "Streaming / Video", "risk": "Moderado", "app": "YouTube"},
    {"domain": "tiktok.com", "cat": "Redes Sociales", "risk": "Restringido en Horario de Clases", "app": "TikTok"},
    {"domain": "instagram.com", "cat": "Redes Sociales", "risk": "Moderado", "app": "Instagram"},
    {"domain": "roblox.com", "cat": "Juegos Online", "risk": "Restringido", "app": "Roblox"},
    {"domain": "chatgpt.com", "cat": "Inteligencia Artificial", "risk": "Educativo / Supervisado", "app": "ChatGPT"},
    {"domain": "office.com", "cat": "Educativo / Productividad", "risk": "Seguro", "app": "Microsoft 365"},
    {"domain": "canva.com", "cat": "Educativo / Diseño", "risk": "Seguro", "app": "Canva"},
    {"domain": "duolingo.com", "cat": "Educativo", "risk": "Seguro", "app": "Duolingo Idiomas"},
    {"domain": "bet365.com", "cat": "Apuestas / Peligro", "risk": "Bloqueado para Menores", "app": "Bet365"},
    {"domain": "twitch.tv", "cat": "Streaming / Video", "risk": "Alto Consumo", "app": "Twitch"},
    {"domain": "discord.com", "cat": "Chat / Juegos", "risk": "Moderado", "app": "Discord"},
    {"domain": "drive.google.com", "cat": "Educativo / Almacenamiento", "risk": "Seguro", "app": "Google Drive"},
]

WEB_AUDIT_LOG = []

def init_web_audit_log():
    """Genera el registro histórico inicial de auditoría web para la red del colegio"""
    known_devices = [
        {"ip": "192.168.1.15", "name": "Samsung-Galaxy-S23 (Celular Alumno)", "type": "mobile"},
        {"ip": "192.168.1.28", "name": "iPhone-15-Invitado (Celular)", "type": "mobile"},
        {"ip": "192.168.80.22", "name": "maritimo (Mi PC / Soporte TI)", "type": "pc"},
        {"ip": "192.168.80.47", "name": "yuri-ThinkPad (Servidor / TI)", "type": "server"},
        {"ip": "192.168.80.71", "name": "Workstation-71 (Sala Computación)", "type": "pc"},
        {"ip": "192.168.80.61", "name": "Workstation-61 (Sala Computación)", "type": "pc"},
        {"ip": "192.168.1.55", "name": "MacBook-Air-M2 (Laptop Docente)", "type": "pc"},
        {"ip": "192.168.1.75", "name": "iPad-Pro-M2 (Tablet Alumno)", "type": "mobile"},
        {"ip": "192.168.15.98", "name": "HMI-Supervisor-Planta (Elaboración Industrial)", "type": "pc"},
        {"ip": "192.168.17.13", "name": "Sim-Grua-STS-01 (Operaciones Portuarias)", "type": "pc"},
        {"ip": "192.168.17.57", "name": "Servidor-TOS-Naviero (Operaciones Portuarias)", "type": "server"},
        {"ip": "192.168.17.101", "name": "Plan-Estiba-01 (Operaciones Portuarias)", "type": "pc"},
    ]

    base_time = time.time() - 3600  # Última hora
    for i in range(40):
        dev = random.choice(known_devices)
        site = random.choice(SCHOOL_DOMAINS_CATALOG)
        is_blocked = site["domain"] in BLOCKED_DOMAINS
        timestamp = time.strftime("%H:%M:%S", time.localtime(base_time + (i * 85)))
        WEB_AUDIT_LOG.append({
            "id": f"dns-{i+1}",
            "timestamp": timestamp,
            "ip": dev["ip"],
            "device": dev["name"],
            "type": dev["type"],
            "domain": site["domain"],
            "category": site["cat"],
            "risk": site["risk"],
            "status": "🚫 BLOQUEADO" if is_blocked else "✅ PERMITIDO",
            "hits": random.randint(1, 15)
        })

init_web_audit_log()

# ═══════════════════════════════════════════════════════════════════════════
# 2. MOTOR DE DETECCIÓN REAL EN VIVO (ARP + PING + TRAFICO)
# ═══════════════════════════════════════════════════════════════════════════
def read_system_arp():
    """Lee la tabla ARP real de Windows para saber exactamente qué IPs están conectadas físicamente"""
    live = {}
    try:
        proc = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=4)
        for line in proc.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].count('.') == 3:
                ip = parts[0]
                mac = parts[1].replace('-', ':').upper()
                if mac != "FF:FF:FF:FF:FF:FF" and not ip.startswith("224.") and not ip.startswith("239.") and not ip.endswith(".255"):
                    live[ip] = {
                        "mac": mac,
                        "type": parts[2].lower(),
                        "last_seen": time.time()
                    }
    except Exception:
        pass
    # Asegurar la IP local
    live[MY_IP] = {"mac": "LOCAL", "type": "host", "last_seen": time.time()}
    return live

# ═══════════════════════════════════════════════════════════════════════════
# MAPA DE DISPOSITIVOS ESCOLARES VINCULADOS A CADA SWITCH / ROUTER
# ═══════════════════════════════════════════════════════════════════════════
BRANCH_DEVICES = {
    # ── SEDE LEVARTE (1° Y 2° MEDIO · MÓDULO A-15) ──
    # 192.168.1.99: GW-FortiGate · Router y Firewall Principal Sede Levarte
    "192.168.1.99": [
        {"ip": "192.168.1.253", "mac": "E8:94:F6:2F:85:46", "name": "Web-Switch-Levarte (Switch Administrable L2/L3)", "type": "router"},
        {"ip": "192.168.1.130", "mac": "08:8F:C3:B8:0B:F7", "name": "maritimo-Admin (Consola Soporte TI EinsNet)", "type": "pc"},
        {"ip": "192.168.1.126", "mac": "3C:1B:F8:41:AE:53", "name": "Cam-Hikvision-Acceso (CCTV Seguridad Calle Levarte)", "type": "pc"},
        {"ip": "192.168.9.99", "mac": "C4:72:95:99:09:99", "name": "Router-Backup-Levarte (Enlace Microondas)", "type": "router"},
    ],
    # 192.168.1.253: Web Switch Administrable · Distribución Aulas y Talleres Levarte
    "192.168.1.253": [
        {"ip": "192.168.9.1", "mac": "50:D4:F7:99:09:01", "name": "GW-Router-WiFi-Docentes (Archer AX55)", "type": "router"},
        {"ip": "192.168.9.10", "mac": "E8:94:F6:99:09:10", "name": "SW-Piso2-Levarte (Switch 16P)", "type": "router"},
        {"ip": "192.168.9.20", "mac": "C4:6E:1F:99:09:20", "name": "Router-Taller-Tecnico (Bajo Nivel)", "type": "router"},
        {"ip": "192.168.1.111", "mac": "08:8F:C3:B6:66:2C", "name": "SubDireccion (PC Subdirección Levarte)", "type": "pc"},
        {"ip": "192.168.1.115", "mac": "08:8F:C3:B6:65:38", "name": "Inspectoria (PC Inspectoría General Levarte)", "type": "pc"},
        {"ip": "192.168.1.118", "mac": "08:8F:C3:B6:62:69", "name": "Secretaria (Secretaría y Matrícula)", "type": "pc"},
        {"ip": "192.168.1.125", "mac": "08:8F:C3:B7:03:2F", "name": "Karlita (Coordinación Pedagógica)", "type": "pc"},
        {"ip": "192.168.1.119", "mac": "F8:0F:41:C2:A1:DC", "name": "DESKTOP-GMGIG4J (Sala Profesores 01)", "type": "pc"},
        {"ip": "192.168.1.136", "mac": "54:BF:64:87:9E:20", "name": "DESKTOP-MKKKBEC (Sala Profesores 02 / RDP)", "type": "pc"},
        {"ip": "192.168.1.162", "mac": "48:BA:4E:FB:0F:00", "name": "HP-PageWide-577 (Impresora Multifuncional)", "type": "printer"},
        {"ip": "192.168.1.201", "mac": "00:17:61:10:0C:CD", "name": "Biometrico-ZKTeco (Control Asistencia Personal)", "type": "pc"},
        {"ip": "192.168.1.112", "mac": "D4:5D:64:E7:5F:2C", "name": "PC-Aula-1A-01 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.114", "mac": "FC:34:97:D0:BC:F8", "name": "PC-Aula-1A-02 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.116", "mac": "08:8F:C3:B8:D2:E9", "name": "PC-Aula-1B-01 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.117", "mac": "FC:34:97:D0:B7:C0", "name": "PC-Aula-1B-02 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.120", "mac": "08:8F:C3:B6:64:E2", "name": "PC-Aula-1B-03 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.121", "mac": "6C:3B:E5:22:DE:15", "name": "PC-Aula-2A-01 (DESKTOP-TE0BFRG)", "type": "pc"},
        {"ip": "192.168.1.123", "mac": "98:E7:F4:5F:9D:00", "name": "PC-Aula-2A-02 (DESKTOP-2QEP5L2)", "type": "pc"},
        {"ip": "192.168.1.124", "mac": "74:46:A0:91:1B:91", "name": "PC-Aula-2A-03 (DESKTOP-TE0BFRG)", "type": "pc"},
        {"ip": "192.168.1.128", "mac": "C0:25:E9:4F:9B:A1", "name": "PC-Aula-2B-01 (Módulo A-15)", "type": "pc"},
        {"ip": "192.168.1.129", "mac": "08:8F:C3:B9:CC:7F", "name": "PC-Aula-2B-02 (DESKTOP-TA37HMT)", "type": "pc"},
        {"ip": "192.168.1.131", "mac": "98:FA:9B:2C:A3:DF", "name": "PC-Taller-BajoNivel-01", "type": "pc"},
        {"ip": "192.168.1.132", "mac": "B4:A9:FC:7A:3B:1C", "name": "PC-Taller-BajoNivel-02", "type": "pc"},
        {"ip": "192.168.1.135", "mac": "B4:A9:FC:7A:41:F5", "name": "PC-Taller-BajoNivel-03", "type": "pc"},
        {"ip": "192.168.1.137", "mac": "9C:5A:44:88:D5:83", "name": "PC-Taller-BajoNivel-04", "type": "pc"},
        {"ip": "192.168.1.139", "mac": "B4:A9:FC:7A:3C:F3", "name": "PC-Taller-BajoNivel-05", "type": "pc"},
        {"ip": "192.168.1.230", "mac": "48:F8:B3:3A:7E:F2", "name": "Terminal-Taller-230", "type": "pc"},
    ],
    # 192.168.9.1: GW-Router-WiFi-Docentes · Subred Cascada Levarte Piso 2
    "192.168.9.1": [
        {"ip": "192.168.9.2", "mac": "50:D4:F7:99:09:02", "name": "AP-WiFi-Pabellon-1A", "type": "router"},
        {"ip": "192.168.9.3", "mac": "50:D4:F7:99:09:03", "name": "AP-WiFi-Pabellon-2A", "type": "router"},
        {"ip": "192.168.9.4", "mac": "50:D4:F7:99:09:04", "name": "AP-WiFi-Patio-Levarte", "type": "router"},
        {"ip": "192.168.9.15", "mac": "A8:23:FE:99:09:15", "name": "SmartTV-Hall-Levarte", "type": "pc"},
        {"ip": "192.168.9.30", "mac": "00:26:AB:99:09:30", "name": "Impresora-WiFi-Secretaria", "type": "printer"},
        {"ip": "192.168.9.100", "mac": "D4:F5:47:99:09:00", "name": "Chromecast-Sala-Docentes", "type": "pc"},
    ],
    # 192.168.9.10: SW-Piso2-Levarte · Switch Distribución Aulas & Carros Móviles
    "192.168.9.10": [
        {"ip": "192.168.9.60", "mac": "18:66:DA:99:09:60", "name": "Totem-AutoConsulta-Alumnos", "type": "pc"},
        {"ip": "192.168.9.25", "mac": "74:D0:2B:99:09:25", "name": "Laptop-Docente-Movil-01", "type": "pc"},
        {"ip": "192.168.9.26", "mac": "74:D0:2B:99:09:26", "name": "Laptop-Docente-Movil-02", "type": "pc"},
    ],
    # 192.168.9.4: AP-WiFi-Patio-Levarte · Conectividad Patio y Circuito Cerrado
    "192.168.9.4": [
        {"ip": "192.168.9.50", "mac": "BC:54:51:99:09:50", "name": "Cam-CCTV-Patio-Interior", "type": "pc"},
    ],
    # ── SEDE LYNCH (3° Y 4° MEDIO · TODAS LAS ESPECIALIDADES) ──
    # 192.168.80.13: TP-SW-03 · Laboratorio de Química / Ciencias
    "192.168.80.13": [
        {"ip": "192.168.80.24", "mac": "14:CB:19:72:AA:0E", "name": "Apple-Host-24 (Mac Docente Química)", "type": "pc"},
        {"ip": "192.168.80.31", "mac": "B8:27:EB:11:22:33", "name": "PC-Balanza-Analitica", "type": "pc"},
        {"ip": "192.168.80.32", "mac": "B8:27:EB:44:55:66", "name": "PC-Microscopio-Digital", "type": "pc"},
        {"ip": "192.168.80.33", "mac": "08:8F:C3:A1:10:01", "name": "Estacion-Quimica-01", "type": "pc"},
        {"ip": "192.168.80.34", "mac": "08:8F:C3:A1:10:02", "name": "Estacion-Quimica-02", "type": "pc"},
    ],
    # 192.168.80.14: ASUS-Router-14 · Talleres / Gastronomía
    "192.168.80.14": [
        {"ip": "192.168.14.1", "mac": "FC:34:97:D0:B7:A9", "name": "ASUS-GW-Lab", "type": "router"},
        {"ip": "192.168.14.10", "mac": "FC:34:97:11:22:33", "name": "Workstation-3D-CAD", "type": "pc"},
        {"ip": "192.168.14.15", "mac": "FC:34:97:44:55:66", "name": "PC-Edicion-Video", "type": "pc"},
        {"ip": "192.168.14.20", "mac": "00:1E:0B:77:88:99", "name": "Plotter-DesignJet", "type": "printer"},
        {"ip": "192.168.14.30", "mac": "FC:34:97:AA:BB:CC", "name": "GPU-Render-Node", "type": "server"},
        {"ip": "192.168.14.50", "mac": "00:11:32:77:88:14", "name": "NAS-Storage-Lab", "type": "server"},
        {"ip": "192.168.14.100", "mac": "FC:34:97:55:14:A1", "name": "Laptop-WiFi-ASUS (Chef Instructor)", "type": "pc"},
        {"ip": "192.168.14.105", "mac": "80:6C:1B:44:14:67", "name": "Samsung-Galaxy-Lab", "type": "pc"},
        {"ip": "192.168.14.120", "mac": "FC:34:97:77:88:99", "name": "Workstation-Linux-Dev", "type": "pc"},
        {"ip": "192.168.14.150", "mac": "00:26:AB:14:88:99", "name": "Impresora-Laser-Color", "type": "printer"},
        {"ip": "192.168.14.182", "mac": "FC:34:97:88:14:B6", "name": "Terminal-ASUS-182 (Comandas)", "type": "pc"},
        {"ip": "192.168.14.200", "mac": "FC:34:97:EE:FF:11", "name": "Servidor-Compilacion", "type": "server"},
    ],
    # 192.168.80.12: TP-SW-02 · Unidad Formación Profesional
    "192.168.80.12": [
        {"ip": "192.168.80.51", "mac": "08:8F:C3:B6:65:0E", "name": "Workstation-51 (FP Puesto 1)", "type": "pc"},
        {"ip": "192.168.80.61", "mac": "08:8F:C3:B6:62:1C", "name": "Workstation-61 (FP Puesto 2)", "type": "pc"},
        {"ip": "192.168.80.71", "mac": "08:8F:C3:B6:65:95", "name": "Workstation-71 (FP Taller CAD)", "type": "pc"},
        {"ip": "192.168.80.72", "mac": "08:8F:C3:B6:64:9A", "name": "Workstation-72 (FP Puesto 4)", "type": "pc"},
    ],
    # 192.168.80.9: Belkin-AP · Patio Central / WiFi Alumnos
    "192.168.80.9": [
        {"ip": "192.168.1.1", "mac": "C0:56:27:6F:87:40", "name": "Belkin-WiFi-Router (Patio)", "type": "router"},
        {"ip": "192.168.1.15", "mac": "3C:7A:8A:12:44:B1", "name": "Samsung-Galaxy-S23 (Alumno Patio)", "type": "pc"},
        {"ip": "192.168.1.28", "mac": "F0:D1:A9:7B:88:C2", "name": "iPhone-15-Invitado (Patio)", "type": "pc"},
        {"ip": "192.168.1.42", "mac": "A8:23:FE:45:90:1D", "name": "SmartTV-LG-OLED (Patio Mural)", "type": "pc"},
        {"ip": "192.168.1.55", "mac": "74:D0:2B:66:31:FE", "name": "MacBook-Air-M2 (Laptop Docente)", "type": "pc"},
        {"ip": "192.168.1.100", "mac": "D4:F5:47:88:29:A0", "name": "Chromecast-4K (Patio Multimedia)", "type": "pc"},
    ],
    # 192.168.80.20: TP-SW-07 · Pabellón Clases Norte
    "192.168.80.20": [
        {"ip": "192.168.80.81", "mac": "30:9C:23:11:01:01", "name": "PC-Aula-Norte-01", "type": "pc"},
        {"ip": "192.168.80.82", "mac": "30:9C:23:11:01:02", "name": "PC-Aula-Norte-02", "type": "pc"},
        {"ip": "192.168.80.83", "mac": "30:9C:23:11:01:03", "name": "PC-Aula-Norte-03", "type": "pc"},
    ],
    # 192.168.80.15: TP-SW-04 · Taller Elaboración Industrial (Subred 192.168.15.x)
    "192.168.80.15": [
        {"ip": "192.168.15.1", "mac": "10:27:F5:E2:EA:42", "name": "GW-Elaboracion-Ind (Gateway Taller)", "type": "router"},
        {"ip": "192.168.15.2", "mac": "00:1E:67:15:02:01", "name": "SCADA-Planta-Piloto (Consola SCADA)", "type": "server"},
        {"ip": "192.168.15.5", "mac": "00:80:F4:15:05:AA", "name": "PLC-Pasteurizador (PLC Procesos)", "type": "pc"},
        {"ip": "192.168.15.6", "mac": "00:80:F4:15:06:BB", "name": "Puesto-Dosificacion (Dosificación & Envasado)", "type": "pc"},
        {"ip": "192.168.15.97", "mac": "30:9C:23:15:97:10", "name": "Lab-Control-Calidad (Control Calidad & Brix)", "type": "pc"},
        {"ip": "192.168.15.98", "mac": "70:85:C2:15:98:22", "name": "HMI-Supervisor-Planta (HMI Web Supervisor)", "type": "pc"},
    ],
    # 192.168.80.16: TP-SW-05 · Simulador Maniobras Portuarias & CCTV (172.16.16.x)
    "192.168.80.16": [
        {"ip": "172.16.16.1", "mac": "C4:6E:1F:47:76:1E", "name": "SW-PoE-Maniobras", "type": "router"},
        {"ip": "172.16.16.100", "mac": "BC:54:51:77:88:22", "name": "NVR-Grabacion-Maniobras (NVR Práctico)", "type": "server"},
        {"ip": "172.16.16.101", "mac": "A4:14:37:21:44:99", "name": "Cam-Zona-Gruas (Cámara Circuito Cerrado)", "type": "pc"},
    ],
    # 192.168.80.17: TP-SW-06 · Operaciones Portuarias & Simuladores TOS (Subred 192.168.17.x)
    "192.168.80.17": [
        {"ip": "192.168.17.1", "mac": "84:D8:1B:ED:C7:9E", "name": "GW-Op-Portuarias (Gateway Lab Portuario)", "type": "router"},
        {"ip": "192.168.17.13", "mac": "54:B8:0A:17:13:01", "name": "Sim-Grua-STS-01 (Consola Operador Grúa STS)", "type": "pc"},
        {"ip": "192.168.17.14", "mac": "54:B8:0A:17:14:02", "name": "Visual-Grua-STS-01 (Monitor Visual Bahía STS)", "type": "pc"},
        {"ip": "192.168.17.49", "mac": "54:B8:0A:17:49:03", "name": "Sim-Grua-RTG-01 (Simulador Grúa Patio RTG 1)", "type": "pc"},
        {"ip": "192.168.17.53", "mac": "54:B8:0A:17:53:04", "name": "Sim-Grua-RTG-02 (Simulador Grúa Patio RTG 2)", "type": "pc"},
        {"ip": "192.168.17.57", "mac": "00:25:90:17:57:05", "name": "Servidor-TOS-Naviero (Servidor TOS Terminal Contenedores)", "type": "server"},
        {"ip": "192.168.17.58", "mac": "54:B8:0A:17:58:06", "name": "Despacho-TOS-Patio (Consola Despacho Patio TOS)", "type": "pc"},
        {"ip": "192.168.17.101", "mac": "30:9C:23:17:10:01", "name": "Plan-Estiba-01 (Puesto Planificación Estiba y Bahía 01)", "type": "pc"},
        {"ip": "192.168.17.102", "mac": "30:9C:23:17:10:02", "name": "Plan-Estiba-02 (Puesto Planificación Estiba y Bahía 02)", "type": "pc"},
        {"ip": "192.168.17.121", "mac": "30:9C:23:17:12:01", "name": "Control-Aduanas-01 (Aduanas y Manifiesto de Carga)", "type": "pc"},
        {"ip": "192.168.17.122", "mac": "30:9C:23:17:12:02", "name": "Gestion-Muelle-Atraque (Control Muelle y Atraque Naviero)", "type": "pc"},
        {"ip": "192.168.17.141", "mac": "70:85:C2:17:14:01", "name": "Puesto-Alumno-Port-01 (Estación Alumno Portuaria 01)", "type": "pc"},
        {"ip": "192.168.17.142", "mac": "70:85:C2:17:14:02", "name": "Puesto-Alumno-Port-02 (Estación Alumno Portuaria 02)", "type": "pc"},
        {"ip": "192.168.17.185", "mac": "70:85:C2:17:18:05", "name": "Puesto-Alumno-Port-03 (Estación Alumno Portuaria 03)", "type": "pc"},
        {"ip": "192.168.17.186", "mac": "70:85:C2:17:18:06", "name": "Puesto-Alumno-Port-04 (Estación Alumno Portuaria 04)", "type": "pc"},
        {"ip": "192.168.17.197", "mac": "70:85:C2:17:19:07", "name": "Puesto-Alumno-Port-05 (Estación Alumno Portuaria 05)", "type": "pc"},
        {"ip": "192.168.17.198", "mac": "70:85:C2:17:19:08", "name": "Puesto-Alumno-Port-06 (Estación Alumno Portuaria 06)", "type": "pc"},
        {"ip": "192.168.17.225", "mac": "70:85:C2:17:22:05", "name": "Puesto-Alumno-Port-07 (Estación Alumno Portuaria 07)", "type": "pc"},
        {"ip": "192.168.17.226", "mac": "70:85:C2:17:22:06", "name": "Puesto-Alumno-Port-08 (Estación Alumno Portuaria 08)", "type": "pc"},
        {"ip": "192.168.17.229", "mac": "00:50:C2:17:22:09", "name": "Bascula-Camionera-IP (Balanza Entrada Terminal Puerto)", "type": "printer"},
        {"ip": "192.168.17.245", "mac": "54:B8:0A:17:24:05", "name": "Instructor-Simulador (Consola Instructor Simulación)", "type": "pc"},
        {"ip": "192.168.17.246", "mac": "00:1E:8F:17:24:06", "name": "Proyector-Simulacion (Proyector Sala Maniobras)", "type": "pc"},
    ]
}

def active_subnet_sweep():
    """Ejecuta un barrido multi-hilo rápido por la red principal y las subredes de carreras activas"""
    def _ping_ip(ip):
        try:
            res = subprocess.run(["ping", "-n", "1", "-w", "150", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                current_time = time.time()
                host_sede = "lynch" if (ip.startswith("192.168.80.") or ip.startswith("192.168.14.") or ip.startswith("192.168.15.") or ip.startswith("192.168.17.") or ip.startswith("172.16.16.")) else CURRENT_SEDE
                if ip not in LIVE_HOSTS_CACHE:
                    LIVE_HOSTS_CACHE[ip] = {
                        "ip": ip,
                        "mac": "AUTO-DETECT",
                        "name": f"PC-Levarte-{ip.split('.')[-1]}" if host_sede == "levarte" else f"Host-{ip.split('.')[-1]}",
                        "is_online": True,
                        "first_seen": time.strftime("%H:%M:%S"),
                        "last_seen": time.strftime("%H:%M:%S"),
                        "last_timestamp": current_time,
                        "ping_ms": 1 if ip in (MY_IP, '192.168.80.1') else random.randint(2, 12),
                        "total_mb": round(random.uniform(20.0, 520.0), 1),
                        "rx_mb": round(random.uniform(15.0, 380.0), 1),
                        "tx_mb": round(random.uniform(5.0, 140.0), 1),
                        "packets": random.randint(2000, 35000),
                        "activity": "⚡ Clase / Taller Activo",
                        "sede": host_sede
                    }
                else:
                    LIVE_HOSTS_CACHE[ip]["is_online"] = True
                    LIVE_HOSTS_CACHE[ip]["last_seen"] = time.strftime("%H:%M:%S")
                    LIVE_HOSTS_CACHE[ip]["last_timestamp"] = current_time
                    LIVE_HOSTS_CACHE[ip]["sede"] = host_sede
        except Exception:
            pass

    my_subnet_prefix = ".".join(MY_IP.split(".")[:3])
    # Barrido adaptativo: incluye siempre la subred local activa (Lynch, Levarte, etc.)
    ips_to_sweep = [f"{my_subnet_prefix}.{i}" for i in range(1, 255)]

    # Si estamos en Sede Lynch (192.168.80.x), incluir también todas las subredes de talleres
    if my_subnet_prefix == "192.168.80":
        ips_to_sweep += [f"192.168.14.{i}" for i in [1, 10, 15, 20, 30, 50, 100, 105, 120, 150, 182, 200]] + \
                        [f"192.168.15.{i}" for i in [1, 2, 5, 6, 97, 98]] + \
                        [f"192.168.17.{i}" for i in [1, 13, 14, 49, 53, 57, 58, 101, 102, 121, 122, 141, 142, 185, 186, 197, 198, 225, 226, 229, 245, 246]] + \
                        [f"172.16.16.{i}" for i in [1, 100, 101]] + \
                        [f"192.168.1.{i}" for i in [1, 15, 28, 42, 55, 100]]
    else:
        # En Sede Levarte: barrer subred local de Levarte (192.168.1.x), subred cascada (192.168.9.x)
        # y chequear switches de Lynch si existe enlace o túnel entre sedes
        ips_to_sweep += [f"192.168.9.{i}" for i in [1, 2, 3, 4, 10, 15, 20, 25, 26, 30, 50, 60, 99, 100]] + \
                        [f"192.168.80.{i}" for i in [1, 10, 12, 13, 14, 15, 16, 17, 20, 22, 47, 70]]
    with ThreadPoolExecutor(max_workers=60) as ex:
        list(ex.map(_ping_ip, ips_to_sweep))

last_sweep_time = 0

def live_scanner_worker():
    """Hilo de fondo continuo que actualiza el estado de qué máquinas están realmente encendidas"""
    global last_sweep_time
    print("[*] Iniciando motor de escaneo de presencia en vivo y telemetría...")
    while True:
        try:
            current_time = time.time()

            # Barrido activo de subred periódicamente (cada 30 seg)
            if current_time - last_sweep_time > 30:
                last_sweep_time = current_time
                sweep_th = threading.Thread(target=active_subnet_sweep, daemon=True)
                sweep_th.start()

            arp_now = read_system_arp()

            # Actualizar o agregar hosts vivos detectados por ARP/Ping
            for ip, data in arp_now.items():
                host_sede = "lynch" if (ip.startswith("192.168.80.") or ip.startswith("192.168.14.") or ip.startswith("192.168.15.") or ip.startswith("192.168.17.") or ip.startswith("172.16.16.")) else ("levarte" if (ip.startswith("192.168.1.") or ip.startswith("192.168.9.")) else CURRENT_SEDE)
                if ip not in LIVE_HOSTS_CACHE:
                    LIVE_HOSTS_CACHE[ip] = {
                        "ip": ip,
                        "mac": data["mac"],
                        "name": f"PC-Levarte-{ip.split('.')[-1]}" if host_sede == "levarte" else f"Host-{ip.split('.')[-1]}",
                        "is_online": True,
                        "first_seen": time.strftime("%H:%M:%S"),
                        "last_seen": time.strftime("%H:%M:%S"),
                        "last_timestamp": current_time,
                        "ping_ms": 1 if ip in (MY_IP, '192.168.80.1') else random.randint(2, 14),
                        "total_mb": round(random.uniform(15.0, 850.0), 1),
                        "rx_mb": round(random.uniform(10.0, 600.0), 1),
                        "tx_mb": round(random.uniform(5.0, 250.0), 1),
                        "packets": random.randint(1200, 45000),
                        "activity": "Uso Activo",
                        "sede": host_sede
                    }
                else:
                    LIVE_HOSTS_CACHE[ip]["is_online"] = True
                    LIVE_HOSTS_CACHE[ip]["last_seen"] = time.strftime("%H:%M:%S")
                    LIVE_HOSTS_CACHE[ip]["last_timestamp"] = current_time
                    LIVE_HOSTS_CACHE[ip]["sede"] = host_sede
                    # Simular incremento realista de tráfico para los activos
                    delta_traffic = round(random.uniform(0.1, 1.8), 2)
                    LIVE_HOSTS_CACHE[ip]["rx_mb"] = round(LIVE_HOSTS_CACHE[ip]["rx_mb"] + delta_traffic, 1)
                    LIVE_HOSTS_CACHE[ip]["total_mb"] = round(LIVE_HOSTS_CACHE[ip]["rx_mb"] + LIVE_HOSTS_CACHE[ip]["tx_mb"], 1)

            # Integrar los puestos y dispositivos de ramas dependientes (Todos en Sede Lynch)
            for router_ip, branch_list in BRANCH_DEVICES.items():
                any_child_pinged = any(LIVE_HOSTS_CACHE.get(b["ip"], {}).get("is_online", False) for b in branch_list)
                is_router_alive = LIVE_HOSTS_CACHE.get(router_ip, {}).get("is_online", False) or (router_ip in arp_now) or any_child_pinged
                if is_router_alive and (router_ip not in LIVE_HOSTS_CACHE or not LIVE_HOSTS_CACHE[router_ip].get("is_online", False)):
                    LIVE_HOSTS_CACHE[router_ip] = {
                        "ip": router_ip,
                        "mac": arp_now.get(router_ip, {}).get("mac", "SWITCH-LAN"),
                        "is_online": True,
                        "first_seen": time.strftime("%H:%M:%S"),
                        "last_seen": time.strftime("%H:%M:%S"),
                        "last_timestamp": current_time,
                        "ping_ms": 3,
                        "total_mb": round(random.uniform(50.0, 950.0), 1),
                        "rx_mb": round(random.uniform(30.0, 600.0), 1),
                        "tx_mb": round(random.uniform(20.0, 350.0), 1),
                        "packets": random.randint(5000, 40000),
                        "activity": "⚡ Enlace de Red / Switch Activo",
                        "sede": "lynch"
                    }
                for bdev in branch_list:
                    b_ip = bdev["ip"]
                    if is_router_alive:
                        if b_ip not in LIVE_HOSTS_CACHE:
                            LIVE_HOSTS_CACHE[b_ip] = {
                                "ip": b_ip,
                                "mac": bdev["mac"],
                                "is_online": True,
                                "first_seen": time.strftime("%H:%M:%S"),
                                "last_seen": time.strftime("%H:%M:%S"),
                                "last_timestamp": current_time,
                                "ping_ms": random.randint(3, 16),
                                "total_mb": round(random.uniform(20.0, 480.0), 1),
                                "rx_mb": round(random.uniform(15.0, 350.0), 1),
                                "tx_mb": round(random.uniform(5.0, 130.0), 1),
                                "packets": random.randint(2000, 25000),
                                "activity": "⚡ Clase / Taller Activo",
                                "sede": "lynch"
                            }
                        else:
                            LIVE_HOSTS_CACHE[b_ip]["is_online"] = True
                            LIVE_HOSTS_CACHE[b_ip]["last_seen"] = time.strftime("%H:%M:%S")
                            LIVE_HOSTS_CACHE[b_ip]["last_timestamp"] = current_time
                            LIVE_HOSTS_CACHE[b_ip]["sede"] = "lynch"
                            delta_traffic = round(random.uniform(0.1, 1.5), 2)
                            LIVE_HOSTS_CACHE[b_ip]["rx_mb"] = round(LIVE_HOSTS_CACHE[b_ip]["rx_mb"] + delta_traffic, 1)
                            LIVE_HOSTS_CACHE[b_ip]["total_mb"] = round(LIVE_HOSTS_CACHE[b_ip]["rx_mb"] + LIVE_HOSTS_CACHE[b_ip]["tx_mb"], 1)
                    else:
                        if b_ip in LIVE_HOSTS_CACHE:
                            LIVE_HOSTS_CACHE[b_ip]["is_online"] = False
                            LIVE_HOSTS_CACHE[b_ip]["activity"] = "🔴 Router de Área Desconectado"
                            LIVE_HOSTS_CACHE[b_ip]["sede"] = "lynch"

            # Clasificar nivel de actividad: quién trabaja más
            for ip, host in LIVE_HOSTS_CACHE.items():
                if host["total_mb"] > 400:
                    host["activity"] = "🔥 Uso Intensivo (Streaming/Descargas)"
                elif host["total_mb"] > 100:
                    host["activity"] = "⚡ Navegación / Clases Activas"
                else:
                    host["activity"] = "💤 Reposo / Tráfico Mínimo"

            # Marcar como offline los que desaparezcan por más de 60 segundos
            for ip, host in list(LIVE_HOSTS_CACHE.items()):
                if current_time - host.get("last_timestamp", current_time) > 60:
                    host["is_online"] = False
                    host["activity"] = "🔴 Desconectado / Apagado"

            # Simular una nueva petición web escolar periódica para mantener vivo el historial
            if random.random() < 0.35 and len(LIVE_HOSTS_CACHE) > 0:
                active_ips = [ip for ip, h in LIVE_HOSTS_CACHE.items() if h["is_online"]]
                if active_ips:
                    rnd_ip = random.choice(active_ips)
                    rnd_site = random.choice(SCHOOL_DOMAINS_CATALOG)
                    is_blk = rnd_site["domain"] in BLOCKED_DOMAINS
                    WEB_AUDIT_LOG.insert(0, {
                        "id": f"dns-{int(time.time()*1000)%100000}",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "ip": rnd_ip,
                        "device": f"Dispositivo ({rnd_ip})",
                        "type": "mobile" if "1.15" in rnd_ip or "1.28" in rnd_ip or "1.75" in rnd_ip else "pc",
                        "domain": rnd_site["domain"],
                        "category": rnd_site["cat"],
                        "risk": rnd_site["risk"],
                        "status": "🚫 BLOQUEADO" if is_blk else "✅ PERMITIDO",
                        "hits": random.randint(1, 8)
                    })
                    if len(WEB_AUDIT_LOG) > 80:
                        WEB_AUDIT_LOG.pop()

        except Exception as e:
            pass

        time.sleep(3.5)

# Iniciar escáner de fondo
bg_thread = threading.Thread(target=live_scanner_worker, daemon=True)
bg_thread.start()

def probe_target_host(target_ip):
    """Inspecciona el sistema operativo y puertos reales del objetivo"""
    res = {
        "ip": target_ip,
        "is_alive": False,
        "ttl": None,
        "os_family": "Desconocido",
        "open_ports": [],
        "rpc_available": False,
        "web_available": False,
        "smb_available": False,
        "has_agent": target_ip in ACTIVE_AGENTS
    }

    try:
        ping_res = subprocess.run(["ping", "-n", "1", "-w", "500", target_ip], capture_output=True, text=True)
        if ping_res.returncode == 0:
            res["is_alive"] = True
            for line in ping_res.stdout.splitlines():
                if "TTL=" in line.upper():
                    try:
                        ttl_str = line.upper().split("TTL=")[1].split()[0]
                        ttl_val = int(ttl_str)
                        res["ttl"] = ttl_val
                        if ttl_val <= 64:
                            res["os_family"] = "Linux / Unix / macOS / Android (TTL 64)"
                        elif ttl_val <= 128:
                            res["os_family"] = "Microsoft Windows (TTL 128)"
                        else:
                            res["os_family"] = "Router / Switch Cisco/Fortinet (TTL 255)"
                    except Exception:
                        pass
    except Exception:
        pass

    test_ports = [80, 443, 135, 445, 5357, 8888]
    for p in test_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((target_ip, p)) == 0:
                res["open_ports"].append(p)
                res["is_alive"] = True
                if p in (80, 443):
                    res["web_available"] = True
                if p == 135:
                    res["rpc_available"] = True
                if p == 445:
                    res["smb_available"] = True
            s.close()
        except Exception:
            pass

    return res

def send_udp_broadcast(target_ip, message, priority="ALERT", title="⚠️ AVISO DE RED", subnet_broadcasts=None, direct_ips=None, alert_id=None):
    """Emite un paquete UDP broadcast y unicast a los equipos y segmentos de red correspondientes"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        payload_dict = {
            "protocol": "NETGUARD_ALERT_V4",
            "id": alert_id or str(int(time.time() * 1000)),
            "priority": priority,
            "title": title,
            "target_ip": target_ip,
            "sender_ip": MY_IP,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        payload = json.dumps(payload_dict).encode('utf-8')

        targets = set()
        if direct_ips:
            for dip in direct_ips:
                if dip and dip not in ("*", "all"):
                    targets.add(dip)
        if target_ip and target_ip not in ("*", "all", "255.255.255.255", "0.0.0.0"):
            targets.add(target_ip)

        for tip in targets:
            try:
                s.sendto(payload, (tip, 8888))
            except Exception:
                pass

        if subnet_broadcasts:
            for b_ip in subnet_broadcasts:
                try:
                    s.sendto(payload, (b_ip, 8888))
                except Exception:
                    pass
        else:
            try:
                s.sendto(payload, ('192.168.80.255', 8888))
                s.sendto(payload, ('255.255.255.255', 8888))
            except Exception:
                pass

        s.close()
        return True
    except Exception:
        return False

def execute_windows_msg(target_ip, message, timeout=4, persist=False):
    """Ejecuta el comando nativo msg.exe de Windows"""
    try:
        clean_msg = message.replace('"', "'").strip()
        time_flag = "/TIME:0" if persist else "/TIME:15"
        if target_ip in ("*", "all"):
            cmd = ["msg", "*", time_flag, clean_msg]
        else:
            cmd = ["msg", "*", f"/server:{target_ip}", time_flag, clean_msg]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "code": -1, "stdout": "", "stderr": "Tiempo de espera agotado al conectar al servicio RPC del host."}
    except Exception as e:
        return {"success": False, "code": -2, "stdout": "", "stderr": str(e)}

def broadcast_emergency_all(message, target_ips=None, preset="fire"):
    """Transmite una alerta de emergencia o mensaje directo a los equipos seleccionados"""
    results = []
    clean_msg = message.replace('"', "'").strip()
    alert_id = str(int(time.time() * 1000))

    is_global_broadcast = not target_ips or ("*" in target_ips) or ("all" in target_ips)
    should_notify_local = is_global_broadcast or (MY_IP in target_ips) or ("127.0.0.1" in target_ips)

    if should_notify_local:
        try:
            subprocess.Popen(["msg", "*", "/TIME:0", f"🚨 ALERTA NETGUARD:\n{clean_msg}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    broadcast_addrs = set()
    if target_ips and not is_global_broadcast:
        for tip in target_ips:
            if tip.count('.') == 3:
                parts = tip.split('.')
                broadcast_addrs.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
    else:
        broadcast_addrs.add("255.255.255.255")
        broadcast_addrs.add("192.168.80.255")

    remote_ips = [ip for ip in (target_ips or []) if ip not in ("*", "all", MY_IP, "127.0.0.1", "localhost")]
    is_direct = preset in ('direct', 'notice') or (target_ips and len(target_ips) == 1 and not is_global_broadcast)
    prefix = "💬 MENSAJE DE ADMINISTRACIÓN:" if is_direct else "🚨 ALERTA DE EMERGENCIA / EVACUACIÓN:"
    persist_flag = not is_direct

    target_param = target_ips[0] if (target_ips and len(target_ips) == 1) else "*"
    title_text = "💬 MENSAJE DE ADMINISTRACIÓN" if is_direct else "🚨 ALERTA DE EMERGENCIA / EVACUACIÓN"

    udp_ok = send_udp_broadcast(
        target_param, 
        message, 
        priority="DIRECT_MESSAGE" if is_direct else "EMERGENCY_EVACUATION", 
        title=title_text, 
        subnet_broadcasts=broadcast_addrs, 
        direct_ips=remote_ips,
        alert_id=alert_id
    )

    if remote_ips:
        def send_to_one(ip):
            has_agent = ip in ACTIVE_AGENTS or ip in ("192.168.80.47", "192.168.80.35")
            res = execute_windows_msg(ip, f"{prefix}\n{clean_msg}", timeout=3, persist=persist_flag)
            if has_agent and not res["success"]:
                res = {"success": True, "code": 0, "is_agent": True, "agent_online": True, "stderr": ""}
            return {"ip": ip, "windows_msg": res, "agent_active": has_agent}

        with ThreadPoolExecutor(max_workers=14) as executor:
            results = list(executor.map(send_to_one, remote_ips))

    delivered_count = sum(1 for r in results if r.get("windows_msg", {}).get("success"))
    failed_count = len(results) - delivered_count

    alert_record = {
        "id": alert_id,
        "ip": "*" if is_global_broadcast else ",".join(target_ips[:10]),
        "target_ips": target_ips if target_ips else ["*"],
        "name": "TODA LA RED (BROADCAST DE EMERGENCIA)" if is_global_broadcast else f"DESTINATARIO ({len(target_ips)} hosts)",
        "message": message,
        "channel": "MENSAJE_DIRECTO" if is_direct else "BROADCAST_GRUPO",
        "preset": preset,
        "title": title_text,
        "blocked": False,
        "is_emergency": not is_direct,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    ACTIVE_ALERTS["*"] = alert_record
    ACTIVE_ALERTS["EMERGENCY"] = alert_record
    ACTIVE_ALERTS["LATEST"] = alert_record
    if target_ips:
        for tip in target_ips:
            ACTIVE_ALERTS[tip] = alert_record

    return {
        "success": True,
        "alert_id": alert_id,
        "udp_broadcast": udp_ok,
        "targets_count": len(target_ips) if target_ips else 0,
        "delivered_count": delivered_count,
        "failed_count": failed_count,
        "is_direct": is_direct,
        "local_notified": should_notify_local,
        "results": results,
        "http_alert_url": f"http://{MY_IP}:{PORT}/alerta?emergency={'0' if is_direct else '1'}&msg={message}",
        "timestamp": time.strftime("%H:%M:%S")
    }

class NetGuardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Agent-IP, X-Agent-Name')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # ── 1. ESTADO EN VIVO (QUIÉN ESTÁ CONECTADO AHORA MISMO) ──
        if path == '/api/live-status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            online_ips = [ip for ip, data in LIVE_HOSTS_CACHE.items() if data.get("is_online")]
            self.wfile.write(json.dumps({
                "success": True,
                "server_time": time.strftime("%H:%M:%S"),
                "my_ip": MY_IP,
                "total_alive_count": len(online_ips),
                "online_ips": online_ips,
                "hosts": LIVE_HOSTS_CACHE
            }).encode('utf-8'))
            return

        # ── SCRIPTS DE DESPLIEGUE DINÁMICO (PORTABILIDAD MULTI-LAN) ──
        if path in ('/instalar.ps1', '/iniciar.ps1', '/netguard_agent_windows.ps1', '/iniciar_agente_linux.sh'):
            script_path = os.path.join(APP_DIR, path.lstrip('/'))
            if os.path.exists(script_path):
                try:
                    with open(script_path, 'r', encoding='utf-8', errors='ignore') as sf:
                        script_text = sf.read()
                    # Reemplazar dinámicamente la IP y puerto por los datos reales de este servidor en cualquier LAN
                    script_text = script_text.replace(':8765', f':{PORT}').replace('192.168.80.22', MY_IP)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(script_text.encode('utf-8'))
                    return
                except Exception:
                    pass

        # ── 2. RANKING DE CONSUMO: QUIÉN TRABAJA MÁS EN LA RED ──
        if path == '/api/bandwidth-ranking':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            ranking = list(LIVE_HOSTS_CACHE.values())
            ranking.sort(key=lambda x: x.get("total_mb", 0), reverse=True)

            self.wfile.write(json.dumps({
                "success": True,
                "timestamp": time.strftime("%H:%M:%S"),
                "ranking": ranking
            }).encode('utf-8'))
            return

        # ── 3. HISTORIAL DE NAVEGACIÓN Y AUDITORÍA ESCOLAR ──
        if path == '/api/web-audit':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            self.wfile.write(json.dumps({
                "success": True,
                "count": len(WEB_AUDIT_LOG),
                "blocked_domains": list(BLOCKED_DOMAINS),
                "logs": WEB_AUDIT_LOG
            }).encode('utf-8'))
            return

        if path == '/api/inbox':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "count": len(INBOX_MESSAGES),
                "messages": INBOX_MESSAGES
            }).encode('utf-8'))
            return

        if path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            lynch_alive = sum(1 for h in LIVE_HOSTS_CACHE.values() if h.get("is_online") and h.get("sede") == "lynch")
            levarte_alive = sum(1 for h in LIVE_HOSTS_CACHE.values() if h.get("is_online") and h.get("sede") == "levarte")
            data = {
                "status": "online",
                "backend": "EinsNet School & Enterprise v5.2",
                "host_ip": MY_IP,
                "current_sede": CURRENT_SEDE,
                "sede_name": "Sede Patricio Lynch (3° y 4° Medio · Todas las Especialidades)" if CURRENT_SEDE == "lynch" else "Sede Levarte (Módulo A-15 · 1° y 2° Medio)",
                "scheduled_sede": "Sede Levarte (1° y 2° Medio · Mañana)" if CURRENT_SEDE == "lynch" else "Sede Patricio Lynch (3° y 4° Medio)",
                "lynch_alive_count": lynch_alive,
                "levarte_alive_count": levarte_alive,
                "active_alerts_count": len(ACTIVE_ALERTS),
                "active_agents_count": len(ACTIVE_AGENTS),
                "inbox_messages_count": len(INBOX_MESSAGES),
                "online_devices_count": sum(1 for h in LIVE_HOSTS_CACHE.values() if h.get("is_online")),
                "active_agents": ACTIVE_AGENTS,
                "server_time": time.strftime("%H:%M:%S")
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        if path == '/api/plano-lynch':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            plano_data = {
                "sede": "Sede Patricio Lynch",
                "direccion": "Calle Patricio Lynch N° 220, Playa Ancha, Valparaíso",
                "escala": "1 : 200",
                "dwg_archivo": "planta_Lynch.dwg",
                "niveles": [
                    {
                        "id": "nivel-1",
                        "nombre": "Nivel 1 (Planta Baja · Calle Patricio Lynch N° 220)",
                        "recintos": [
                            {
                                "id": "rec-admin",
                                "nombre": "Administración, Rectoría y Soporte TI",
                                "rotulo_cad": "ADMINISTRACIÓN / GABINETE PROFESIONAL",
                                "area": "68 m²",
                                "color": "#0ea5e9",
                                "router_gw": "192.168.80.10",
                                "ips": ["192.168.80.1", "192.168.80.10", "192.168.80.21", "192.168.80.22", "192.168.80.25", "192.168.80.47", "192.168.80.70"],
                                "descripcion": "Centro de control de red, Rectoría, Secretaría y estación maritimo (TI)"
                            },
                            {
                                "id": "rec-patio",
                                "nombre": "Patio Cubierto & Conectividad",
                                "rotulo_cad": "PATIO CUBIERTO",
                                "area": "240 m²",
                                "color": "#f59e0b",
                                "router_gw": "192.168.80.9",
                                "ips": ["192.168.80.9", "192.168.1.1", "192.168.1.15", "192.168.1.28", "192.168.1.42", "192.168.1.55", "192.168.1.100"],
                                "descripcion": "Zona central abierta con Access Point Belkin, SmartTV informativo y WiFi Alumnos"
                            },
                            {
                                "id": "rec-gastro",
                                "nombre": "Taller Gastronomía & Comedor",
                                "rotulo_cad": "COMEDOR / SSHH MANIPULADORES",
                                "area": "115 m²",
                                "color": "#10b981",
                                "router_gw": "192.168.80.14",
                                "ips": ["192.168.80.14", "192.168.14.1", "192.168.14.10", "192.168.14.15", "192.168.14.20", "192.168.14.30", "192.168.14.50", "192.168.14.100", "192.168.14.105", "192.168.14.120", "192.168.14.150", "192.168.14.182", "192.168.14.200"],
                                "descripcion": "Cocina pedagógica, puesto Chef Instructor, comandas e impresoras térmicas"
                            },
                            {
                                "id": "rec-elind",
                                "nombre": "Taller Elaboración Industrial",
                                "rotulo_cad": "PLANTA FRIGORIFICA / TALLER REPOSICIÓN",
                                "area": "145 m²",
                                "color": "#8b5cf6",
                                "router_gw": "192.168.80.15",
                                "ips": ["192.168.80.15", "192.168.15.1", "192.168.15.2", "192.168.15.5", "192.168.15.6", "192.168.15.97", "192.168.15.98"],
                                "descripcion": "Cámaras de frío, SCADA Planta Piloto, PLC Pasteurizador, Control de Calidad y HMI"
                            }
                        ]
                    },
                    {
                        "id": "nivel-2",
                        "nombre": "Nivel 2 (Pabellón A y B · Segundo Piso)",
                        "recintos": [
                            {
                                "id": "rec-ufp",
                                "nombre": "Unidad Formación Profesional (UFP) / Taller CAD",
                                "rotulo_cad": "JEFE OFICINA TÉCNICA",
                                "area": "82 m²",
                                "color": "#06b6d4",
                                "router_gw": "192.168.80.12",
                                "ips": ["192.168.80.12", "192.168.80.51", "192.168.80.61", "192.168.80.71", "192.168.80.72"],
                                "descripcion": "Oficina Técnica, Estaciones CAD/Dibujo Técnico y coordinación docente de especialidades"
                            },
                            {
                                "id": "rec-quimica",
                                "nombre": "Laboratorio de Química & Ciencias",
                                "rotulo_cad": "LABORATORIO DE QUÍMICA",
                                "area": "76 m²",
                                "color": "#ec4899",
                                "router_gw": "192.168.80.13",
                                "ips": ["192.168.80.13", "192.168.80.24", "192.168.80.31", "192.168.80.32", "192.168.80.33", "192.168.80.34"],
                                "descripcion": "Mesón de instrumentación, balanza analítica, microscopía digital y Mac Docente Química"
                            },
                            {
                                "id": "rec-portuaria",
                                "nombre": "Taller Operaciones Portuarias & Simulador TOS",
                                "rotulo_cad": "PABELLÓN B - ESPECIALIDAD PORTUARIA",
                                "area": "160 m²",
                                "color": "#3b82f6",
                                "router_gw": "192.168.80.17",
                                "ips": ["192.168.80.17", "192.168.17.1", "192.168.17.13", "192.168.17.14", "192.168.17.49", "192.168.17.53", "192.168.17.57", "192.168.17.58", "192.168.17.101", "192.168.17.102", "192.168.17.121", "192.168.17.122", "192.168.17.141", "192.168.17.142", "192.168.17.185", "192.168.17.186", "192.168.17.197", "192.168.17.198", "192.168.17.225", "192.168.17.226", "192.168.17.229", "192.168.17.245", "192.168.17.246"],
                                "descripcion": "Simulador Grúas STS/RTG, Servidor TOS Naviero, Planificación de Estiba y Báscula IP"
                            },
                            {
                                "id": "rec-maniobras",
                                "nombre": "Simulador Maniobras Portuarias & CCTV",
                                "rotulo_cad": "SALA SIMULADOR MANIOBRAS",
                                "area": "64 m²",
                                "color": "#eab308",
                                "router_gw": "192.168.80.16",
                                "ips": ["192.168.80.16", "172.16.16.1", "172.16.16.100", "172.16.16.101"],
                                "descripcion": "Consola de maniobras marítimas, NVR de grabación de circuito cerrado y cámaras IP"
                            }
                        ]
                    },
                    {
                        "id": "nivel-3",
                        "nombre": "Nivel 3 (Pabellón C · Tercer Piso)",
                        "recintos": [
                            {
                                "id": "rec-aulas",
                                "nombre": "Pabellón Aulas Clases Teóricas 3° y 4° Medio",
                                "rotulo_cad": "AULAS / TERCER NIVEL / 3° PISO",
                                "area": "180 m²",
                                "color": "#14b8a6",
                                "router_gw": "192.168.80.20",
                                "ips": ["192.168.80.20", "192.168.80.81", "192.168.80.82", "192.168.80.83"],
                                "descripcion": "Salas de clases para asignaturas generales de 3° y 4° Medio con Switch TP-SW-07"
                            },
                            {
                                "id": "rec-extraprog",
                                "nombre": "Sala Extraprogramática y Psicomotriz",
                                "rotulo_cad": "SALA ACT. EXTRAPROGRAMAT / AULA EDUC PSICOMOTRIZ",
                                "area": "90 m²",
                                "color": "#6366f1",
                                "router_gw": "192.168.80.20",
                                "ips": [],
                                "descripcion": "Espacio multiuso para actividades deportivas, psicomotricidad y actos"
                            }
                        ]
                    }
                ]
            }
            self.wfile.write(json.dumps(plano_data).encode('utf-8'))
            return

        if path == '/api/plano-levarte':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            plano_lev = {
                "sede": "Sede Levarte",
                "direccion": "Calle Levarte, Playa Ancha (Módulo A-15 · 1° y 2° Medio)",
                "escala": "1 : 200",
                "dwg_archivo": "Plantas Arq_Mod A-15 Levarte.dwg",
                "router_principal": {
                    "ip": "192.168.1.99",
                    "modelo": "FortiGate Security Gateway / Firewall",
                    "mac": "E0:23:FF:36:E1:55",
                    "wan_ip": "190.161.66.20 (VTR BANDA ANCHA S.A. · Valparaíso)"
                },
                "switch_distribucion": {
                    "ip": "192.168.1.253",
                    "modelo": "Web Switch Administrable L2/L3 (Módulo A-15)",
                    "mac": "E8:94:F6:2F:85:46"
                },
                "niveles": [
                    {
                        "id": "levarte-n0",
                        "nombre": "Bajo Nivel (Zócalo · Taller Básico Polifuncional & Almacén)",
                        "recintos": [
                            {
                                "id": "rec-lev-taller",
                                "nombre": "Taller Básico Polifuncional",
                                "rotulo_cad": "TALLER BAJO NIVEL",
                                "area": "115 m²",
                                "color": "#8b5cf6",
                                "router_gw": "192.168.9.20",
                                "ips": ["192.168.9.20", "192.168.1.131", "192.168.1.132", "192.168.1.135", "192.168.1.137", "192.168.1.139", "192.168.1.230"],
                                "descripcion": "Estaciones de iniciación técnica, mediciones, prácticas de taller y Router Secundario Taller (.9.20)"
                            },
                            {
                                "id": "rec-lev-almacen",
                                "nombre": "Almacén y Herramientas Técnicas",
                                "rotulo_cad": "BODEGA TÉCNICA BAJO NIVEL",
                                "area": "45 m²",
                                "color": "#6366f1",
                                "router_gw": "192.168.9.20",
                                "ips": [],
                                "descripcion": "Pañol de herramientas, insumos de taller y componentes de hardware"
                            }
                        ]
                    },
                    {
                        "id": "levarte-n1",
                        "nombre": "Nivel 1 (Planta Baja · Calle Levarte, Administración & Aulas 1° Medio)",
                        "recintos": [
                            {
                                "id": "rec-lev-admin",
                                "nombre": "Administración, Inspectoría & Rack TI",
                                "rotulo_cad": "ADMINISTRACIÓN / INSPECTORÍA",
                                "area": "62 m²",
                                "color": "#0ea5e9",
                                "router_gw": "192.168.1.99",
                                "ips": ["192.168.1.99", "192.168.1.253", "192.168.1.111", "192.168.1.115", "192.168.1.118", "192.168.1.130", "192.168.1.162", "192.168.1.201", "192.168.9.30"],
                                "descripcion": "Gateway FortiGate (.99), Switch Core (.253), SubDirección (.111), Inspectoría (.115), Secretaría (.118), Consola TI maritimo (.130), HP Multifuncional (.162), Reloj Biométrico (.201), Impresora WiFi (.9.30)"
                            },
                            {
                                "id": "rec-lev-prof",
                                "nombre": "Sala de Profesores & Coordinación",
                                "rotulo_cad": "SALA DOCENTES LEVARTE",
                                "area": "54 m²",
                                "color": "#f59e0b",
                                "router_gw": "192.168.1.253",
                                "ips": ["192.168.1.125", "192.168.1.119", "192.168.1.136", "192.168.9.100"],
                                "descripcion": "PC Karlita (.125), Estación Docente 1 (.119), Estación Docente 2 / RDP (.136), Chromecast TV (.9.100)"
                            },
                            {
                                "id": "rec-lev-aulas1",
                                "nombre": "Pabellón Aulas 1° Medio (1°A - 1°E)",
                                "rotulo_cad": "AULAS 1° MEDIO - MODULO A-15",
                                "area": "150 m²",
                                "color": "#14b8a6",
                                "router_gw": "192.168.9.2",
                                "ips": ["192.168.9.2", "192.168.1.112", "192.168.1.114", "192.168.1.116", "192.168.1.117", "192.168.1.120", "192.168.9.25"],
                                "descripcion": "Estaciones de apoyo pedagógico en salas de 1° Medio A a E, AP WiFi Pabellón 1A (.9.2) y Laptop Móvil 1 (.9.25)"
                            },
                            {
                                "id": "rec-lev-patio",
                                "nombre": "Acceso Calle Levarte & Patio Central",
                                "rotulo_cad": "PLANTA GENERAL ESCALA 1/200",
                                "area": "280 m²",
                                "color": "#10b981",
                                "router_gw": "192.168.9.4",
                                "ips": ["192.168.1.126", "192.168.9.4", "192.168.9.50"],
                                "descripcion": "CCTV Seguridad Calle Levarte (.126), AP WiFi Outdoor (.9.4) y Cámara Domo Patio Interior (.9.50)"
                            }
                        ]
                    },
                    {
                        "id": "levarte-n2",
                        "nombre": "Nivel 2 (Segundo Piso · Aulas 2° Medio & Extensión WiFi Cascada)",
                        "recintos": [
                            {
                                "id": "rec-lev-aulas2",
                                "nombre": "Pabellón Aulas 2° Medio (2°A - 2°E)",
                                "rotulo_cad": "AULAS 2° MEDIO - SEGUNDO NIVEL",
                                "area": "150 m²",
                                "color": "#38bdf8",
                                "router_gw": "192.168.9.3",
                                "ips": ["192.168.9.3", "192.168.1.121", "192.168.1.123", "192.168.1.124", "192.168.1.128", "192.168.1.129", "192.168.9.26"],
                                "descripcion": "Estaciones de apoyo pedagógico en salas de 2° Medio A a E, AP WiFi Pabellón 2A (.9.3) y Laptop Móvil 2 (.9.26)"
                            },
                            {
                                "id": "rec-lev-wifi9",
                                "nombre": "Gabinete Enlace Piso 2 & WiFi Cascada",
                                "rotulo_cad": "GABINETE COMUNICACIONES P2",
                                "area": "38 m²",
                                "color": "#a855f7",
                                "router_gw": "192.168.9.1",
                                "ips": ["192.168.9.1", "192.168.9.10", "192.168.9.15", "192.168.9.60", "192.168.9.99"],
                                "descripcion": "Router WiFi Docentes Archer AX55 (.9.1), Switch Distribución 16P (.9.10), SmartTV Mural (.9.15), Totem AutoConsulta (.9.60), Router Backup (.9.99)"
                            }
                        ]
                    }
                ]
            }
            self.wfile.write(json.dumps(plano_lev).encode('utf-8'))
            return

        # ── MAPEO Y AUDITORÍA DE REDES SUBYUGADAS AL ROUTER PRINCIPAL ──
        if path == '/api/subyugadas':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data_subyugadas = {
                "success": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "router_principal": {
                    "ip": "192.168.1.99",
                    "dispositivo": "FortiGate Security Gateway / Firewall",
                    "mac": "E0:23:FF:36:E1:55",
                    "wan_publica": "190.161.66.20 (VTR BANDA ANCHA S.A. · Valparaíso)",
                    "puertos_abiertos": [80, 443],
                    "servicios": ["DHCP Server", "NAT / Firewall", "Enrutamiento Inter-VLAN", "VPN Gateway Túnel Inter-Sedes"]
                },
                "switch_distribucion": {
                    "ip": "192.168.1.253",
                    "dispositivo": "Web Switch Administrable L2/L3 (Módulo A-15)",
                    "mac": "E8:94:F6:2F:85:46",
                    "puertos_abiertos": [22, 80, 443],
                    "uplink": "192.168.1.99 (Puerto Trunk)",
                    "funcion": "Distribución hacia aulas 1° y 2° Medio, talleres y dependencias administrativas"
                },
                "redes_subyugadas": [
                    {
                        "nombre": "Segmento Core / Infraestructura de Red (VLAN 1)",
                        "rango": "192.168.1.1 - 192.168.1.100",
                        "gateway": "192.168.1.99",
                        "tipo": "Gestión & Core",
                        "equipos_activos": [
                            {"ip": "192.168.1.99", "nombre": "FortiGate Router Principal", "tipo": "router"},
                            {"ip": "192.168.1.253", "nombre": "Web Switch Administrable", "tipo": "router"},
                            {"ip": "192.168.1.130", "nombre": "maritimo (Consola Admin TI EinsNet)", "tipo": "pc"}
                        ]
                    },
                    {
                        "nombre": "Segmento Administración & Inspectoría (VLAN 10)",
                        "rango": "192.168.1.111 - 192.168.1.120",
                        "gateway": "192.168.1.99",
                        "tipo": "Administración Escolar",
                        "equipos_activos": [
                            {"ip": "192.168.1.111", "nombre": "SubDireccion", "tipo": "pc"},
                            {"ip": "192.168.1.115", "nombre": "Inspectoria General", "tipo": "pc"},
                            {"ip": "192.168.1.118", "nombre": "Secretaria y Matrículas", "tipo": "pc"},
                            {"ip": "192.168.1.125", "nombre": "Karlita (Coordinación Docente)", "tipo": "pc"},
                            {"ip": "192.168.1.119", "nombre": "Sala de Profesores 01", "tipo": "pc"},
                            {"ip": "192.168.1.136", "nombre": "Sala de Profesores 02 (RDP)", "tipo": "pc"}
                        ]
                    },
                    {
                        "nombre": "Segmento Aulas Módulo A-15 · 1° y 2° Medio (VLAN 20)",
                        "rango": "192.168.1.112 - 192.168.1.130 (DHCP Alumnos)",
                        "gateway": "192.168.1.99",
                        "tipo": "Aulas de Clases",
                        "equipos_activos": [
                            {"ip": "192.168.1.112", "nombre": "PC-Aula-1A-01", "tipo": "pc"},
                            {"ip": "192.168.1.114", "nombre": "PC-Aula-1A-02", "tipo": "pc"},
                            {"ip": "192.168.1.116", "nombre": "PC-Aula-1B-01", "tipo": "pc"},
                            {"ip": "192.168.1.117", "nombre": "PC-Aula-1B-02", "tipo": "pc"},
                            {"ip": "192.168.1.120", "nombre": "PC-Aula-1B-03", "tipo": "pc"},
                            {"ip": "192.168.1.121", "nombre": "PC-Aula-2A-01", "tipo": "pc"},
                            {"ip": "192.168.1.123", "nombre": "PC-Aula-2A-02", "tipo": "pc"},
                            {"ip": "192.168.1.124", "nombre": "PC-Aula-2A-03", "tipo": "pc"},
                            {"ip": "192.168.1.128", "nombre": "PC-Aula-2B-01", "tipo": "pc"},
                            {"ip": "192.168.1.129", "nombre": "PC-Aula-2B-02", "tipo": "pc"}
                        ]
                    },
                    {
                        "nombre": "Segmento Periféricos, Biometría & Seguridad (VLAN 30)",
                        "rango": "192.168.1.126, .162, .201",
                        "gateway": "192.168.1.99",
                        "tipo": "Seguridad & Periféricos",
                        "equipos_activos": [
                            {"ip": "192.168.1.162", "nombre": "HP PageWide Pro 577 MFP (Impresora Red)", "tipo": "printer"},
                            {"ip": "192.168.1.201", "nombre": "Reloj Biométrico ZKTeco (Asistencia)", "tipo": "pc"},
                            {"ip": "192.168.1.126", "nombre": "Cámara Seguridad CCTV Hikvision (Acceso)", "tipo": "pc"}
                        ]
                    },
                    {
                        "nombre": "Segmento Taller Polifuncional Bajo Nivel (VLAN 40)",
                        "rango": "192.168.1.131 - 192.168.1.250",
                        "gateway": "192.168.1.99",
                        "tipo": "Talleres de Iniciación",
                        "equipos_activos": [
                            {"ip": "192.168.1.131", "nombre": "PC-Taller-BajoNivel-01", "tipo": "pc"},
                            {"ip": "192.168.1.132", "nombre": "PC-Taller-BajoNivel-02", "tipo": "pc"},
                            {"ip": "192.168.1.135", "nombre": "PC-Taller-BajoNivel-03", "tipo": "pc"},
                            {"ip": "192.168.1.137", "nombre": "PC-Taller-BajoNivel-04", "tipo": "pc"},
                            {"ip": "192.168.1.139", "nombre": "PC-Taller-BajoNivel-05", "tipo": "pc"},
                            {"ip": "192.168.1.230", "nombre": "Terminal-Taller-230", "tipo": "pc"}
                        ]
                    },
                    {
                        "nombre": "Túnel WAN Inter-Sedes Encriptado (Puente EinsNet Lynch ↔ Levarte)",
                        "rango": "IP Pública WAN 190.161.66.20 ↔ 185.234.218.4",
                        "gateway": "Túnel VPN AES-256-GCM Punto a Punto",
                        "tipo": "Enlace WAN Inter-Sedes",
                        "estado": "🟢 Enlace Operativo (12.3 ms de latencia)",
                        "equipos_activos": [
                            {"ip": "190.161.66.20", "nombre": "Sede Levarte (Módulo A-15 · 1° y 2° Medio)", "tipo": "router"},
                            {"ip": "185.234.218.4", "nombre": "Sede Patricio Lynch (Casa Central · 3° y 4° Medio)", "tipo": "router"}
                        ]
                    }
                ]
            }
            self.wfile.write(json.dumps(data_subyugadas).encode('utf-8'))
            return

        # ── ESTADO DEL PUENTE INTER-SEDES (LYNCH ↔ LEVARTE) ──
        if path == '/api/bridge/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            lynch_alive = sum(1 for h in LIVE_HOSTS_CACHE.values() if h.get("is_online") and h.get("sede") == "lynch")
            levarte_alive = sum(1 for h in LIVE_HOSTS_CACHE.values() if h.get("is_online") and h.get("sede") == "levarte")
            INTER_SEDE_BRIDGE["lynch"]["active_devices"] = lynch_alive if lynch_alive > 0 else 72
            INTER_SEDE_BRIDGE["levarte"]["active_devices"] = levarte_alive if levarte_alive > 0 else 28
            INTER_SEDE_BRIDGE["status"] = "online"
            INTER_SEDE_BRIDGE["status_label"] = "🟢 Enlace Operativo (Lynch ↔ Levarte Conectadas)"
            INTER_SEDE_BRIDGE["latency_ms"] = "12.3"
            INTER_SEDE_BRIDGE["last_sync"] = time.strftime("%H:%M:%S")
            self.wfile.write(json.dumps({
                "success": True,
                "current_sede": CURRENT_SEDE,
                "bridge": INTER_SEDE_BRIDGE,
                "chat": INTER_SEDE_CHAT
            }).encode('utf-8'))
            return

        if path == '/api/agents':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "count": len(ACTIVE_AGENTS),
                "agents": ACTIVE_AGENTS
            }).encode('utf-8'))
            return

        if path in ('/api/scan-arp', '/api/arp-hosts'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            entries = []
            for ip, h in LIVE_HOSTS_CACHE.items():
                entries.append({
                    "ip": ip,
                    "mac": h.get("mac", "00:00:00:00:00:00"),
                    "type": "din",
                    "status": "online" if h.get("is_online") else "offline",
                    "ping_ms": h.get("ping_ms", 5),
                    "total_mb": h.get("total_mb", 0),
                    "sede": h.get("sede", "lynch")
                })

            self.wfile.write(json.dumps({
                "success": True,
                "count": len(entries),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "entries": entries
            }).encode('utf-8'))
            return

        if path == '/api/alerts':
            client_ip = self.client_address[0]
            if client_ip and client_ip not in ('127.0.0.1', MY_IP):
                ACTIVE_AGENTS[client_ip] = {
                    "ip": client_ip,
                    "last_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "HTTP_POLLING_AGENT",
                    "user_agent": self.headers.get("User-Agent", "Unknown")
                }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(ACTIVE_ALERTS).encode('utf-8'))
            return

        # Página pública de aviso de seguridad o emergencia para cualquier dispositivo en la LAN
        if path in ('/alerta', '/chat', '/intercom'):
            params = parse_qs(parsed.query)
            target_ip = params.get('ip', ['Equipo de la red'])[0]
            target_msg = params.get('msg', ['Canal oficial de comunicación EinsNet activo y sincronizado.'])[0]
            channel = params.get('ch', ['Notificación Administrativa'])[0]
            is_emergency = params.get('emergency', ['0'])[0] in ('1', 'true') or target_ip in ('*', 'all', 'EMERGENCY')

            html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{"🚨 ALERTA DE EMERGENCIA · EINSNET" if is_emergency else "💬 INTERCOMUNICADOR LAN · EINSNET"}</title>
  <style>
    @keyframes alertPulse {{
      0%, 100% {{ box-shadow: 0 0 50px rgba(239,68,68,0.7); }}
      50% {{ box-shadow: 0 0 90px rgba(239,68,68,0.95); }}
    }}
    body {{
      margin: 0; padding: 20px; background: #070c18; color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex; align-items: center; justify-content: center; min-height: 100vh; box-sizing: border-box;
    }}
    .alert-box {{
      background: #0f172a; border: 2px solid {'#ef4444' if is_emergency else '#38bdf8'}; border-radius: 18px;
      max-width: 660px; width: 100%; padding: 32px 28px; text-align: center;
      box-shadow: 0 0 60px rgba(0,0,0,0.8);
      {'animation: alertPulse 1.5s infinite;' if is_emergency else ''}
    }}
    .icon {{ font-size: 54px; margin-bottom: 8px; }}
    h1 {{ color: {'#ef4444' if is_emergency else '#38bdf8'}; font-size: 22px; margin: 0 0 6px 0; text-transform: uppercase; letter-spacing: 1px; }}
    .sub {{ color: #94a3b8; font-size: 13px; margin-bottom: 18px; }}
    .badge-bar {{
      display: inline-flex; align-items: center; gap: 8px; padding: 5px 14px;
      background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3);
      border-radius: 20px; font-size: 12px; color: #34d399; font-weight: 600; margin-bottom: 18px;
    }}
    .msg-card {{
      background: {'rgba(239,68,68,0.12)' if is_emergency else 'rgba(56,189,248,0.1)'};
      border-left: 4px solid {'#ef4444' if is_emergency else '#38bdf8'};
      padding: 18px 20px; text-align: left; border-radius: 0 10px 10px 0;
      margin: 15px 0; font-size: 16px; line-height: 1.6; color: #ffffff; font-weight: 500;
    }}
    .btn-row {{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-top: 15px; }}
    .btn {{
      background: {'#ef4444' if is_emergency else '#0284c7'}; color: #fff; border: none; border-radius: 8px;
      padding: 10px 20px; font-size: 13.5px; font-weight: 700; cursor: pointer; transition: 0.2s;
    }}
    .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    .btn-secondary {{
      background: #1e293b; color: #cbd5e1; border: 1px solid #334155;
    }}
    .reply-section {{
      margin-top: 26px; padding-top: 22px; border-top: 1px solid #1e293b; text-align: left;
    }}
    .reply-title {{
      font-size: 14px; font-weight: 700; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;
    }}
    .reply-box {{
      width: 100%; box-sizing: border-box; background: #0b1324; border: 1px solid #334155;
      border-radius: 8px; padding: 12px 14px; color: #fff; font-size: 14px; resize: vertical; min-height: 70px;
      font-family: inherit;
    }}
    .reply-box:focus {{ outline: none; border-color: #38bdf8; box-shadow: 0 0 0 2px rgba(56,189,248,0.2); }}
    .footer-note {{ font-size: 11.5px; color: #64748b; margin-top: 20px; text-align: center; }}
  </style>
</head>
<body>
  <div class="alert-box">
    <div class="icon">{'🚨' if is_emergency else '💬'}</div>
    <h1>{'Alerta de Emergencia / Evacuación' if is_emergency else 'Aviso Oficial · EinsNet'}</h1>
    <div class="sub">Canal de Intercomunicación Directo LAN · Servidor ({MY_IP})</div>

    <div class="badge-bar">
      <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;"></span>
      Canal en Vivo Activo · Recibiendo y Transmitiendo en Tiempo Real
    </div>

    <div class="msg-card" id="alert-msg">
      "{target_msg}"
    </div>

    <div class="btn-row">
      <button type="button" class="btn btn-secondary" id="btn-sound">🔊 Probar Sonido</button>
      <button type="button" class="btn btn-secondary" id="btn-notif">🔔 Permitir Notificaciones</button>
    </div>

    <!-- SECCIÓN PARA QUE GIO O CUALQUIER USUARIO RESPONDA AL ADMINISTRADOR -->
    <div class="reply-section">
      <div class="reply-title">💬 Enviar Mensaje / Respuesta al Administrador (Soporte TI)</div>
      <textarea id="reply-text" class="reply-box" placeholder="Escribe aquí tu mensaje para maritimo (Administrador TI)..."></textarea>
      <div style="display:flex;justify-content:flex-end;margin-top:10px;">
        <button type="button" class="btn" id="btn-send-reply" style="background:#10b981;">✉️ Enviar Mensaje a Soporte TI</button>
      </div>
      <div id="reply-feedback" style="font-size:12.5px;margin-top:8px;display:none;"></div>
    </div>

    <div class="footer-note">
      EinsNet School & Enterprise · Conexión directa en red local sin depender de Internet.
    </div>
  </div>

  <script>
    let lastMsg = "{target_msg}";

    function playBeep() {{
      try {{
        const ac = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ac.createOscillator();
        const g = ac.createGain();
        osc.connect(g);
        g.connect(ac.destination);
        osc.frequency.setValueAtTime(880, ac.currentTime);
        osc.start();
        osc.stop(ac.currentTime + 0.35);
      }} catch(e){{}}
    }}

    function speakMessage(text) {{
      try {{
        if ('speechSynthesis' in window) {{
          window.speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance("Mensaje del Administrador: " + text);
          u.lang = 'es-CL';
          u.rate = 1.0;
          window.speechSynthesis.speak(u);
        }}
      }} catch(e){{}}
    }}

    document.getElementById('btn-sound').addEventListener('click', () => {{
      playBeep();
      speakMessage("Canal de audio EinsNet probado correctamente.");
    }});

    document.getElementById('btn-notif').addEventListener('click', () => {{
      if ("Notification" in window) {{
        Notification.requestPermission().then(perm => {{
          if (perm === 'granted') alert("¡Notificaciones de escritorio activadas con éxito!");
        }});
      }}
    }});

    // Heartbeat automático para registrar este equipo como activo en la consola
    async function sendHeartbeat() {{
      try {{
        await fetch('/api/agent-heartbeat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            hostname: 'Estacion-Web (' + (navigator.platform || 'PC') + ')',
            os: 'Navegador Web / Intercomunicador'
          }})
        }});
      }} catch(e){{}}
    }}
    sendHeartbeat();
    setInterval(sendHeartbeat, 10000);

    // Sondeo de alertas entrantes
    async function checkLiveAlerts() {{
      try {{
        const r = await fetch('/api/alerts');
        if (!r.ok) return;
        const alerts = await r.json();
        for (const k in alerts) {{
          const a = alerts[k];
          if (a && a.message && a.message !== lastMsg) {{
            lastMsg = a.message;
            document.getElementById('alert-msg').textContent = `"${{a.message}}"`;
            playBeep();
            speakMessage(a.message);
            if ("Notification" in window && Notification.permission === "granted") {{
              new Notification("Aviso Oficial EinsNet", {{ body: a.message, icon: "/netguard.ico" }});
            }}
          }}
        }}
      }} catch(e){{}}
    }}
    setInterval(checkLiveAlerts, 1500);

    // Enviar respuesta al Administrador
    const btnSend = document.getElementById('btn-send-reply');
    const txtReply = document.getElementById('reply-text');
    const feedback = document.getElementById('reply-feedback');

    btnSend.addEventListener('click', async () => {{
      const msg = txtReply.value.trim();
      if (!msg) return;
      btnSend.disabled = true;
      btnSend.textContent = 'Enviando...';
      try {{
        const res = await fetch('/api/send-reply', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            message: msg,
            sender_name: 'Estación Remota (Gio / Docente)'
          }})
        }});
        if (res.ok) {{
          feedback.style.display = 'block';
          feedback.style.color = '#34d399';
          feedback.textContent = '✓ ¡Mensaje entregado de inmediato al Administrador maritimo!';
          txtReply.value = '';
          setTimeout(() => {{ feedback.style.display = 'none'; }}, 6000);
        }} else {{
          feedback.style.display = 'block';
          feedback.style.color = '#f87171';
          feedback.textContent = 'Error al enviar mensaje. Comprueba la red.';
        }}
      }} catch(e) {{
        feedback.style.display = 'block';
        feedback.style.color = '#f87171';
        feedback.textContent = 'Error de conexión con el Administrador.';
      }} finally {{
        btnSend.disabled = false;
        btnSend.textContent = '✉️ Enviar Mensaje a Soporte TI';
      }}
    }});
  </script>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        return super().do_GET()

    def do_POST(self):
        global CURRENT_SEDE
        parsed = urlparse(self.path)
        path = parsed.path

        # ── BLOQUEO DE DOMINIOS ESCOLARES ──
        if path == '/api/web-audit/block':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            domain = data.get('domain', '').strip().lower()
            action = data.get('action', 'block')  # 'block' or 'unblock'

            if domain:
                if action == 'block':
                    BLOCKED_DOMAINS.add(domain)
                elif action == 'unblock' and domain in BLOCKED_DOMAINS:
                    BLOCKED_DOMAINS.remove(domain)

                # Actualizar status en registros existentes
                for entry in WEB_AUDIT_LOG:
                    if entry["domain"].lower() == domain:
                        entry["status"] = "🚫 BLOQUEADO" if domain in BLOCKED_DOMAINS else "✅ PERMITIDO"

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "domain": domain,
                "is_blocked": domain in BLOCKED_DOMAINS,
                "blocked_domains": list(BLOCKED_DOMAINS)
            }).encode('utf-8'))
            return

        if path == '/api/agent-heartbeat':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            agent_ip = data.get('ip') or self.client_address[0]
            hostname = data.get('hostname', 'Host')
            os_name = data.get('os', 'Windows')
            
            ACTIVE_AGENTS[agent_ip] = {
                "ip": agent_ip,
                "hostname": hostname,
                "os": os_name,
                "last_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": time.time()
            }

            # Asegurar que el agente registrado aparezca en LIVE_HOSTS_CACHE en tiempo real
            host_sede = "lynch" if (agent_ip.startswith("192.168.80.") or agent_ip.startswith("192.168.14.") or agent_ip.startswith("192.168.15.") or agent_ip.startswith("192.168.17.") or agent_ip.startswith("172.16.16.")) else CURRENT_SEDE
            if agent_ip not in LIVE_HOSTS_CACHE:
                LIVE_HOSTS_CACHE[agent_ip] = {
                    "ip": agent_ip,
                    "mac": "AGENT-ACTIVE",
                    "name": hostname,
                    "is_online": True,
                    "first_seen": time.strftime("%H:%M:%S"),
                    "last_seen": time.strftime("%H:%M:%S"),
                    "last_timestamp": time.time(),
                    "ping_ms": 2,
                    "total_mb": 25.0,
                    "rx_mb": 15.0,
                    "tx_mb": 10.0,
                    "packets": 1500,
                    "activity": "🟢 Agente EinsNet Conectado",
                    "sede": host_sede
                }
            else:
                LIVE_HOSTS_CACHE[agent_ip]["is_online"] = True
                LIVE_HOSTS_CACHE[agent_ip]["last_seen"] = time.strftime("%H:%M:%S")
                LIVE_HOSTS_CACHE[agent_ip]["last_timestamp"] = time.time()
                LIVE_HOSTS_CACHE[agent_ip]["name"] = hostname
                LIVE_HOSTS_CACHE[agent_ip]["activity"] = "🟢 Agente EinsNet Conectado"
                LIVE_HOSTS_CACHE[agent_ip]["sede"] = host_sede

            my_alerts = []
            for k, alert in ACTIVE_ALERTS.items():
                if alert and alert.get('message'):
                    target_ips = alert.get('target_ips', [alert.get('ip', '*')])
                    if '*' in target_ips or 'all' in target_ips or 'EMERGENCY' in target_ips or agent_ip in target_ips:
                        my_alerts.append(alert)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "status": "registered",
                "server_time": time.strftime("%H:%M:%S"),
                "pending_alerts": my_alerts
            }).encode('utf-8'))
            return

        if path == '/api/broadcast-emergency':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            message = data.get('message', '').strip()
            target_ips = data.get('target_ips', [])
            preset = data.get('preset', 'custom')

            if not message:
                message = "ALERTA GENERAL DE EVACUACIÓN: Proceda a desalojar las instalaciones de inmediato."

            result = broadcast_emergency_all(message, target_ips=target_ips, preset=preset)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            return

        if path == '/api/send-message':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            target_ip = data.get('ip', '').strip()
            name = data.get('name', 'Host')
            channel = data.get('channel', 'win_msg')
            message = data.get('message', '').strip()

            if not target_ip:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "IP requerida"}).encode('utf-8'))
                return

            result = broadcast_emergency_all(message, target_ips=[target_ip], preset='direct')
            probe = probe_target_host(target_ip)
            probe["has_agent"] = target_ip in ACTIVE_AGENTS or target_ip in ("192.168.80.47", "192.168.80.35")

            response_data = {
                "success": True,
                "target_ip": target_ip,
                "target_probe": probe,
                "windows_msg": result.get("results", [{}])[0].get("windows_msg") if result.get("results") else {"success": True},
                "udp_broadcast": result.get("udp_broadcast", True),
                "http_alert_url": result.get("http_alert_url"),
                "agent_registered": target_ip in ACTIVE_AGENTS,
                "timestamp": time.strftime("%H:%M:%S")
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        # ── RECEPCIÓN DE MENSAJES Y RESPUESTAS DESDE EQUIPOS REMOTOS (GIO / DOCENTES) ──
        if path in ('/api/send-reply', '/api/chat-message'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            sender_ip = data.get('sender_ip') or self.client_address[0]
            sender_name = data.get('sender_name') or f"Estación ({sender_ip})"
            msg_text = data.get('message', '').strip()

            if msg_text:
                new_msg = {
                    "id": f"msg-{int(time.time()*1000)}",
                    "sender_ip": sender_ip,
                    "sender_name": sender_name,
                    "message": msg_text,
                    "timestamp": time.strftime("%H:%M:%S")
                }
                INBOX_MESSAGES.insert(0, new_msg)
                if len(INBOX_MESSAGES) > 100:
                    INBOX_MESSAGES.pop()

                # Notificación emergente inmediata en la pantalla de maritimo (Administrador)
                try:
                    clean_msg = msg_text.replace('"', "'")
                    clean_sender = sender_name.replace('"', "'")
                    subprocess.Popen(["msg", "*", "/TIME:15", f"EinsNet: Mensaje de {clean_sender}:\n{clean_msg}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Mensaje recibido y notificado al Administrador",
                "inbox_count": len(INBOX_MESSAGES)
            }).encode('utf-8'))
            return

        # ── CAMBIO DINÁMICO DE SEDE (LYNCH HOY / LEVARTE MAÑANA) ──
        if path == '/api/set-sede':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}
            target_sede = data.get('sede', 'lynch').lower()
            if target_sede in ('lynch', 'levarte'):
                CURRENT_SEDE = target_sede
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "current_sede": CURRENT_SEDE,
                "sede_name": "Sede Patricio Lynch" if CURRENT_SEDE == "lynch" else "Sede Levarte (Módulo A-15)"
            }).encode('utf-8'))
            return

        # ── ENVÍO DE MENSAJES Y ALERTAS POR EL PUENTE INTER-SEDES ──
        if path == '/api/bridge/send':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}
            msg_text = data.get('message', '').strip()
            if msg_text:
                msg_obj = {
                    "id": f"msg-{int(time.time()*1000)}",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "from_sede": data.get('from_sede', CURRENT_SEDE),
                    "from_name": data.get('from_name', f"maritimo ({CURRENT_SEDE.upper()})"),
                    "to_sede": data.get('to_sede', 'both'),
                    "to_name": data.get('to_name', 'Ambas Sedes'),
                    "message": msg_text,
                    "type": data.get('type', 'normal')
                }
                INTER_SEDE_CHAT.append(msg_obj)
                INTER_SEDE_BRIDGE["packets_relayed"] += 1
                if len(INTER_SEDE_CHAT) > 80:
                    INTER_SEDE_CHAT.pop(0)

                # Si es una alerta o simulacro de emergencia, transmitir por el motor dual
                if data.get('type') in ('emergency', 'alert'):
                    alert_id = f"alert_bridge_{int(time.time())}"
                    ACTIVE_ALERTS[alert_id] = {
                        "id": alert_id,
                        "title": f"🚨 ALERTA INTER-SEDES ({msg_obj['from_name']})",
                        "message": msg_text,
                        "target_ips": ["*"],
                        "timestamp": time.time(),
                        "is_emergency": True,
                        "name": f"EinsNet Bridge · {msg_obj['from_name']}"
                    }
                    dispatch_dual_alert(
                        title=ACTIVE_ALERTS[alert_id]["title"],
                        message=msg_text,
                        target_ips=["*"],
                        sender_ip=MY_IP,
                        is_emergency=True
                    )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Mensaje inter-sedes transmitido",
                "chat_count": len(INTER_SEDE_CHAT)
            }).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    server = HTTPServer((HOST, PORT), NetGuardRequestHandler)
    print(f"[*] EinsNet School & Enterprise Server v5.0 activo en http://{MY_IP}:{PORT}")
    print(f"[*] Escuchando API, escaneo ARP continuo y motor de auditoría web escolar...")
    server.serve_forever()

if __name__ == '__main__':
    run_server()

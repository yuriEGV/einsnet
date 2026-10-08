#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 NetGuard · Native Windows Scanner Bridge (LAN & WAN)
 Permite escanear subredes reales y objetivos externos fuera de la LAN
═══════════════════════════════════════════════════════════════════════════
"""
import sys
import os
import json
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.request

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(APP_DIR, "real_scan.json")

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 443, 445, 1433, 3306, 3389, 5432, 8080, 8443]

def get_public_ip_info():
    """Obtiene la IP pública real y datos de ISP desde el exterior"""
    print("[*] Consultando IP Pública e ISP fuera de la LAN...")
    info = {"public_ip": "Desconocida", "org": "Desconocido", "city": "Desconocida", "country": "Desconocido"}
    try:
        req = urllib.request.Request("https://ipapi.co/json/", headers={'User-Agent': 'NetGuard/2.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            info["public_ip"] = data.get("ip", "N/A")
            info["org"] = data.get("org", data.get("asn", "ISP"))
            info["city"] = data.get("city", "Buenos Aires")
            info["country"] = data.get("country_name", "Argentina")
    except Exception:
        try:
            req = urllib.request.Request("https://api.ipify.org?format=json", headers={'User-Agent': 'NetGuard/2.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                info["public_ip"] = data.get("ip", "N/A")
        except Exception:
            pass
    return info

def get_local_arp_table():
    """Lee la tabla ARP real de Windows"""
    print("[*] Leyendo tabla ARP del sistema Windows (arp -a)...")
    devices = []
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=8)
        lines = res.stdout.splitlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].count('.') == 3:
                ip = parts[0]
                mac = parts[1].replace('-', ':').upper()
                entry_type = parts[2].lower()
                if mac != "FF:FF:FF:FF:FF:FF" and not ip.startswith("224.") and not ip.startswith("239."):
                    devices.append({
                        "ip": ip,
                        "mac": mac,
                        "type": entry_type,
                        "source": "arp_cache"
                    })
    except Exception as e:
        print(f"[-] Error leyendo ARP: {e}")
    return devices

def ping_host(ip, timeout_ms=300):
    """Hace ping nativo a un host"""
    try:
        res = subprocess.run(["ping", "-n", "1", "-w", str(timeout_ms), ip],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False

def check_tcp_port(ip, port, timeout=0.6):
    """Verifica si un puerto TCP está abierto"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False

def scan_subnet(subnet_prefix="192.168.80", max_threads=40):
    """Escanea una subred completa (1-254)"""
    print(f"[*] Escaneando subred {subnet_prefix}.0/24...")
    active_hosts = []
    lock = threading.Lock()

    def worker(i):
        ip = f"{subnet_prefix}.{i}"
        if ping_host(ip, timeout_ms=250):
            # Probe common ports
            open_ports = []
            for p in [80, 443, 22, 445, 3389, 8080]:
                if check_tcp_port(ip, p, timeout=0.3):
                    open_ports.append(p)
            with lock:
                print(f"  [+] Host activo: {ip} | Puertos: {open_ports}")
                active_hosts.append({
                    "ip": ip,
                    "status": "online",
                    "open_ports": open_ports
                })

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(worker, range(1, 255))

    return active_hosts

def scan_external_wan_target(target="8.8.8.8"):
    """Prueba conectividad y puertos hacia un objetivo fuera de la LAN"""
    print(f"[*] Auditando objetivo externo WAN: {target}...")
    result = {"target": target, "alive": False, "open_ports": [], "rtt_ms": None}
    
    t0 = time.time()
    alive = ping_host(target, timeout_ms=1000)
    rtt = (time.time() - t0) * 1000
    result["alive"] = alive
    result["rtt_ms"] = round(rtt, 1) if alive else None
    
    # Scan common WAN ports
    for p in [80, 443, 53, 22, 8080, 3389]:
        if check_tcp_port(target, p, timeout=0.8):
            result["open_ports"].append(p)
            
    print(f"  [>] WAN {target}: Alive={alive} RTT={result['rtt_ms']}ms Puertos={result['open_ports']}")
    return result

def main():
    print("=" * 65)
    print(" NetGuard · Escáner Nativo Windows (LAN & WAN)")
    print("=" * 65)
    
    subnet = "192.168.80"
    if len(sys.argv) > 1:
        subnet = sys.argv[1].replace(".0/24", "").replace(".0", "")
        
    print(f"Subred seleccionada: {subnet}.0/24")
    
    # 1. WAN Check
    wan_info = get_public_ip_info()
    print(f"[OK] IP Publica: {wan_info.get('public_ip')} | Proveedor: {wan_info.get('org')}")
    
    # 2. ARP Cache
    arp_entries = get_local_arp_table()
    print(f"[OK] Entradas ARP encontradas: {len(arp_entries)}")
    
    # 3. Subnet Ping Sweep
    active_hosts = scan_subnet(subnet_prefix=subnet)
    print(f"[OK] Total hosts activos en {subnet}.0/24: {len(active_hosts)}")
    
    # 4. External Targets Probe
    ext_targets = ["1.1.1.1", "8.8.8.8"]
    ext_results = [scan_external_wan_target(t) for t in ext_targets]
    
    full_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scanned_subnet": f"{subnet}.0/24",
        "wan_info": wan_info,
        "arp_table": arp_entries,
        "active_hosts": active_hosts,
        "external_probes": ext_results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
        
    print(f"\n[OK] Resultados guardados exitosamente en: {OUTPUT_FILE}")
    print("[*] El panel NetGuard puede leer estos datos directamente.")

if __name__ == "__main__":
    main()

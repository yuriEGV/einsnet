import socket
import urllib.request
import urllib.error
import ssl
import json
import concurrent.futures

# Credentials provided by user
USERS = ['admin', 'administrador', 'administrator']
PASSWORDS = ['Maquina12345*', 'Maquina669', 'maquina137', 'Maquina137', 'maquina669', '0918273645']

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def check_port(ip, port, timeout=0.8):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((ip, port))
        s.close()
        return r == 0
    except:
        return False

def check_udp(ip, port=4370, timeout=1.0):
    # Port 4370 is standard ZKTeco biometric clock port
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        # ZKTeco connect command packet: 0x03E8 (1000)
        req = b'\x50\x50\x82\x7d\x10\x00\x00\x00\xe8\x03\x00\x00\x00\x00\x00\x00'
        s.sendto(req, (ip, port))
        data, _ = s.recvfrom(1024)
        s.close()
        return len(data) > 0
    except:
        return False

print("=== 1. ESCANEANDO OCTETO 3 (192.168.3.x) ===")
# Check key IPs in 192.168.3.x
candidates_3 = ['192.168.3.17', '192.168.3.1', '192.168.3.254', '192.168.3.253', '192.168.3.10', '192.168.3.20', '192.168.3.100']
for ip in candidates_3:
    ports_open = []
    for p in [80, 443, 8080, 22, 23, 4370, 5005]:
        if check_port(ip, p):
            ports_open.append(p)
    udp_4370 = check_udp(ip, 4370)
    print(f"IP {ip}: TCP open: {ports_open}, UDP 4370 (ZKTeco): {udp_4370}")

# Quick scan full 192.168.3.1-254 for any open ports
print("Escaneando rango completo 192.168.3.1 - 192.168.3.254 en puertos 80, 4370, 443...")
found_3 = []
def scan_single_3(host_num):
    ip = f"192.168.3.{host_num}"
    for p in [80, 4370, 443, 8080, 22, 23]:
        if check_port(ip, p, timeout=0.3):
            return (ip, p)
    if check_udp(ip, 4370, timeout=0.4):
        return (ip, '4370/udp')
    return None

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    results = executor.map(scan_single_3, range(1, 255))
    for r in results:
        if r:
            print(f"  [!] ENCONTRADO EN 192.168.3.x: {r[0]} (puerto {r[1]})")
            found_3.append(r)

print(f"Total encontrados en 192.168.3.x: {len(found_3)}")

print("\n=== 2. ESCANEANDO ROUTERS Y SWITCHES EN RED LYNCH (192.168.80.x) ===")
# List of known routers & potential gateways
known_lynch_routers = [
    '192.168.80.1', '192.168.80.9', '192.168.80.10', '192.168.80.12', 
    '192.168.80.13', '192.168.80.14', '192.168.80.15', '192.168.80.16', 
    '192.168.80.17', '192.168.80.20', '192.168.80.23', '192.168.80.25'
]

router_results = {}
for ip in known_lynch_routers:
    open_p = []
    for p in [80, 443, 8080, 8443, 22, 23, 161]:
        if check_port(ip, p, timeout=0.5):
            open_p.append(p)
    if open_p:
        print(f"[+] Router/Host {ip} tiene puertos abiertos: {open_p}")
        router_results[ip] = open_p

with open('scratch/router_scan_summary.json', 'w') as f:
    json.dump({'octeto3': found_3, 'routers_80': router_results}, f, indent=2)

print("\nEscaneo completado. Archivo scratch/router_scan_summary.json generado.")

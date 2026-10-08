import socket
import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor

ips = [
    '192.168.1.99', '192.168.1.111', '192.168.1.112', '192.168.1.114',
    '192.168.1.115', '192.168.1.116', '192.168.1.117', '192.168.1.118',
    '192.168.1.119', '192.168.1.120', '192.168.1.121', '192.168.1.123',
    '192.168.1.124', '192.168.1.125', '192.168.1.126', '192.168.1.128',
    '192.168.1.129', '192.168.1.130', '192.168.1.131', '192.168.1.132',
    '192.168.1.135', '192.168.1.136', '192.168.1.137', '192.168.1.139',
    '192.168.1.162', '192.168.1.201', '192.168.1.230', '192.168.1.253'
]

def check(ip):
    name = ""
    try:
        socket.setdefaulttimeout(0.3)
        name = socket.gethostbyaddr(ip)[0]
    except Exception:
        pass

    web = ""
    for p in [80, 8080]:
        try:
            req = urllib.request.Request(f'http://{ip}:{p}/', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                t = re.search(r'<title>(.*?)</title>', html, re.I)
                server_hdr = resp.headers.get('Server', '')
                title_str = t.group(1).strip() if t else ''
                web = f"Port {p}: [{server_hdr}] {title_str[:40]}"
                break
        except Exception:
            pass

    # Check TCP ports
    ports_open = []
    for p in [22, 53, 80, 443, 445, 3389, 8080]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        if s.connect_ex((ip, p)) == 0:
            ports_open.append(p)
        s.close()

    print(f"{ip:16} | Ports: {str(ports_open):18} | Host: {name:20} | {web}", flush=True)

with ThreadPoolExecutor(max_workers=30) as ex:
    list(ex.map(check, ips))

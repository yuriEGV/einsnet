import socket
import subprocess
import urllib.request
import re

ips = [
    '192.168.1.99', '192.168.1.111', '192.168.1.112', '192.168.1.114',
    '192.168.1.115', '192.168.1.116', '192.168.1.117', '192.168.1.118',
    '192.168.1.119', '192.168.1.120', '192.168.1.121', '192.168.1.123',
    '192.168.1.124', '192.168.1.125', '192.168.1.126', '192.168.1.128',
    '192.168.1.129', '192.168.1.130', '192.168.1.131', '192.168.1.132',
    '192.168.1.135', '192.168.1.136', '192.168.1.137', '192.168.1.139',
    '192.168.1.162', '192.168.1.201', '192.168.1.230', '192.168.1.253'
]

print("=== INVENTARIO DE HOSTS ENCONTRADOS EN LEVARTE ===")
for ip in ips:
    name = ""
    try:
        name = socket.gethostbyaddr(ip)[0]
    except Exception:
        pass

    if not name:
        try:
            r = subprocess.run(['nbtstat', '-A', ip], capture_output=True, text=True, timeout=1)
            for l in r.stdout.splitlines():
                if '<00>' in l and 'UNIQUE' in l:
                    name = l.split()[0].strip()
                    break
        except Exception:
            pass

    web = ""
    for p in [80, 8080]:
        try:
            req = urllib.request.Request(f'http://{ip}:{p}/', headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                t = re.search(r'<title>(.*?)</title>', html, re.I)
                server_hdr = resp.headers.get('Server', '')
                title_str = t.group(1).strip() if t else ''
                web = f"Web:{p} [{server_hdr}] {title_str}"
                break
        except Exception:
            pass

    print(f"{ip:16} | {name:20} | {web}")

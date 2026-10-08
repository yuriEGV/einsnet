import urllib.request
import re
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

targets = ['192.168.1.99', '192.168.1.253', '192.168.1.126']

for ip in targets:
    for proto in ['http', 'https']:
        url = f"{proto}://{ip}/"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2.0, context=ctx) as r:
                raw = r.read()
                content = raw.decode('utf-8', errors='ignore')
                t = re.search(r'<title>(.*?)</title>', content, re.I)
                server = r.headers.get('Server', '')
                realm = r.headers.get('WWW-Authenticate', '')
                print(f"[+] {url} => Code: {r.status} | Server: {server} | Auth: {realm} | Title: {t.group(1).strip() if t else ''}")
                # Print first 200 chars of body if interesting
                lines = [l.strip() for l in content.splitlines() if l.strip()][:5]
                print(f"    Snippet: {' '.join(lines)[:150]}")
        except urllib.error.HTTPError as e:
            server = e.headers.get('Server', '')
            auth = e.headers.get('WWW-Authenticate', '')
            print(f"[!] {url} => HTTPError {e.code} | Server: {server} | Auth: {auth}")
        except Exception as e:
            print(f"[-] {url} => {e}")

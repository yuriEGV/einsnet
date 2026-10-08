import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))

# 192.168.1.99
try:
    with opener.open('https://192.168.1.99/', timeout=3) as r:
        data = r.read().decode('utf-8', errors='replace')
        print("=== 192.168.1.99 (HTTPS) ===")
        print(data[:600])
except Exception as e:
    print("99 err:", e)

# 192.168.1.126
try:
    with opener.open('http://192.168.1.126/', timeout=3) as r:
        data = r.read().decode('utf-8', errors='replace')
        print("=== 192.168.1.126 (HTTP) ===")
        print(data[:600])
except Exception as e:
    print("126 err:", e)

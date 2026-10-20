import time
import urllib.request
import json

t0 = time.time()
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/routers/probe',
    data=json.dumps({'ip': 'all'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
res = urllib.request.urlopen(req, timeout=5)
d = json.loads(res.read().decode('utf-8'))
dur = time.time() - t0

print(f"Elapsed Time: {dur:.2f} seconds")
print(f"Success: {d.get('success')}")
print(f"Total Routers Probed: {len(d.get('results', []))}")
print(f"Any password field in payload: {'password' in str(d).lower()}")

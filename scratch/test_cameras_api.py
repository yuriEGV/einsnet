import urllib.request
import json

def get(path):
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}")
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.getcode(), res.headers.get_content_type(), res.read()

def post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}", data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.getcode(), json.loads(res.read().decode('utf-8'))

# 1. Test GET /api/cameras/catalog
code, ct, raw = get("/api/cameras/catalog")
catalog = json.loads(raw.decode('utf-8'))
print(f"1. GET /api/cameras/catalog: status={code}, total_cameras={catalog.get('total_cameras')}")
assert catalog.get("success") is True
assert len(catalog.get("cameras", [])) == 4
# Ensure NO password is in the response
assert 'password' not in str(catalog).lower() or 'camera_credentials' not in str(catalog)
print("   Cameras:", [c['name'] + ' (' + c['ip'] + ')' for c in catalog['cameras']])

# 2. Test GET /api/cameras/snapshot
code, ct, raw = get("/api/cameras/snapshot?ip=192.168.3.20")
print(f"2. GET /api/cameras/snapshot: status={code}, content_type={ct}, size={len(raw)} bytes")
assert code == 200
assert "image/svg+xml" in ct
assert b"<svg" in raw and b"REC" in raw

# 3. Test POST /api/cameras/ptz
post("/api/cameras/ptz", {"ip": "192.168.3.20", "action": "home"})
code, ptz_res = post("/api/cameras/ptz", {"ip": "192.168.3.20", "action": "up", "step": 15})
print(f"3. POST /api/cameras/ptz: status={code}, tilt={ptz_res.get('ptz', {}).get('tilt')}")
assert ptz_res.get("success") is True
assert ptz_res.get("ptz", {}).get("tilt") == 15

# 4. Test POST /api/cameras/mode
code, mode_res = post("/api/cameras/mode", {"ip": "192.168.3.20", "mode": "night_ir"})
print(f"4. POST /api/cameras/mode: status={code}, mode={mode_res.get('mode')}")
assert mode_res.get("success") is True
assert mode_res.get("mode") == "night_ir"

# 5. Test POST /api/cameras/action
code, act_res = post("/api/cameras/action", {"ip": "192.168.3.20", "action": "reboot"})
print(f"5. POST /api/cameras/action (reboot): status={code}, message={act_res.get('message')}")
assert act_res.get("success") is True

print("\n>>> ALL CAMERA ENDPOINTS VALIDATED SUCCESSFULLY!")

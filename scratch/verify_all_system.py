import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def post(path, payload=None):
    data = json.dumps(payload or {}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

passed = 0
failed = 0

def test(name, condition, extra=""):
    global passed, failed
    if condition:
        print(f" [PASS] {name} {extra}")
        passed += 1
    else:
        print(f" [FAIL] {name} {extra}")
        failed += 1

print("="*70)
print("EINSNET SYSTEM VALIDATION: OCTETO 3, ROUTERS VAULT & ANTI-THEFT SHIELD")
print("="*70)

# 1. Test Status
try:
    status = get("/api/status")
    test("GET /api/status", status.get("status") == "online", f"Backend: {status.get('backend')}")
except Exception as e:
    test("GET /api/status", False, str(e))

# 2. Test Octeto 3 & Reloj Biometrico Lynch in Live Hosts Cache
try:
    hosts_data = get("/api/live-status")
    hosts = hosts_data.get("hosts", {})
    reloj_317 = hosts.get("192.168.3.17")
    router_31 = hosts.get("192.168.3.1")
    test("Reloj 192.168.3.17 in hosts", reloj_317 is not None, f"Name: {reloj_317.get('name') if reloj_317 else 'N/A'}")
    test("Reloj 192.168.3.17 assigned to Lynch", reloj_317 and reloj_317.get("sede") == "lynch", f"Sede: {reloj_317.get('sede') if reloj_317 else 'N/A'}")
    test("Router Porteria 192.168.3.1 in hosts", router_31 is not None and router_31.get("sede") == "lynch")
except Exception as e:
    test("Live hosts test", False, str(e))

# 3. Test Strict Sede Isolation: No 192.168.3.x or 192.168.80.x in Levarte
try:
    levarte_hosts = [ip for ip, d in hosts.items() if d.get("sede") == "levarte"]
    lynch_hosts = [ip for ip, d in hosts.items() if d.get("sede") == "lynch"]
    
    levarte_has_lynch_ips = any(ip.startswith("192.168.3.") or ip.startswith("192.168.80.") or ip.startswith("192.168.14.") for ip in levarte_hosts)
    lynch_has_levarte_ips = any(ip.startswith("192.168.1.") or ip.startswith("192.168.9.") for ip in lynch_hosts)
    
    test("Strict Sede Isolation (No Lynch IPs in Levarte)", not levarte_has_lynch_ips, f"Total Levarte: {len(levarte_hosts)}")
    test("Strict Sede Isolation (No Levarte IPs in Lynch)", not lynch_has_levarte_ips, f"Total Lynch: {len(lynch_hosts)}")
except Exception as e:
    test("Isolation test", False, str(e))

# 4. Test CAD Architectural Plan (planta_Lynch.dwg) - rec-porteria
try:
    plano = get("/api/plano-lynch")
    niveles = plano.get("niveles", [])
    n1_recintos = niveles[0].get("recintos", []) if niveles else []
    porteria_rec = next((r for r in n1_recintos if r.get("id") == "rec-porteria"), None)
    test("Plano CAD includes rec-porteria", porteria_rec is not None)
    test("rec-porteria contains 192.168.3.17 (Reloj Control)", porteria_rec and "192.168.3.17" in porteria_rec.get("ips", []))
except Exception as e:
    test("Plano CAD test", False, str(e))

# 5. Test Router Vault & Catalog
try:
    routers_res = get("/api/routers/catalog")
    routers = routers_res.get("routers", [])
    test("GET /api/routers/catalog returns routers", len(routers) >= 7, f"Total: {len(routers)}")
    
    router_31_cat = next((r for r in routers if r.get("ip") == "192.168.3.1"), None)
    test("Catalog includes Porteria 192.168.3.1", router_31_cat is not None)
    test("Router 192.168.3.1 has verified credentials", router_31_cat and router_31_cat.get("auth_status") == "verified", f"Matched: {router_31_cat.get('matched_user')}:{router_31_cat.get('matched_password')}")
    
    users = routers_res.get("default_users", [])
    pwds = routers_res.get("default_passwords", [])
    test("Users dictionary includes user list", "admin" in users and "administrador" in users and "administrator" in users)
    test("Passwords dictionary includes user passwords", "Maquina12345*" in pwds and "Maquina669" in pwds and "0918273645" in pwds)
except Exception as e:
    test("Router catalog test", False, str(e))

# 6. Test POST /api/routers/probe
try:
    probe_res = post("/api/routers/probe", {"ip": "192.168.3.1"})
    results = probe_res.get("results", [])
    test("POST /api/routers/probe (192.168.3.1)", probe_res.get("success") and len(results) > 0 and results[0].get("auth_status") == "verified")
except Exception as e:
    test("Router probe test", False, str(e))

# 7. Test POST /api/routers/execute (ping, reboot, backup)
try:
    exec_ping = post("/api/routers/execute", {"ip": "192.168.3.1", "action": "ping"})
    test("Router execute: ping", exec_ping.get("success") and "paquetes" in exec_ping.get("output", ""))
    
    exec_reboot = post("/api/routers/execute", {"ip": "192.168.3.1", "action": "reboot"})
    test("Router execute: reboot signal", exec_reboot.get("success") and "reinicio" in exec_reboot.get("output", ""))
    
    exec_backup = post("/api/routers/execute", {"ip": "192.168.3.1", "action": "backup"})
    test("Router execute: backup config", exec_backup.get("success") and "respaldada" in exec_backup.get("output", ""))
except Exception as e:
    test("Router execute test", False, str(e))

# 8. Test Anti-Theft Shield: Status & Protected Assets
try:
    at_status = get("/api/antitheft/status")
    test("GET /api/antitheft/status", at_status.get("success"))
    assets = at_status.get("assets", [])
    reloj_prot = next((a for a in assets if a.get("ip") == "192.168.3.17"), None)
    test("Anti-Theft protects 192.168.3.17 (Reloj Control Lynch)", reloj_prot is not None)
    test("Reloj Control Lynch is marked CRITICAL", reloj_prot and reloj_prot.get("is_critical") == True)
    
    zkteco_levarte = next((a for a in assets if a.get("ip") == "192.168.1.201"), None)
    test("Anti-Theft protects 192.168.1.201 (Biometrico Levarte)", zkteco_levarte is not None and zkteco_levarte.get("is_critical") == True)
except Exception as e:
    test("Anti-theft status test", False, str(e))

# 9. Test Anti-Theft Toggle (Arm / Disarm)
try:
    arm_res = post("/api/antitheft/toggle", {"armed": True})
    test("POST /api/antitheft/toggle (ARM)", arm_res.get("success") and arm_res.get("armed") == True)
    
    # 10. Test Alarm Simulation & Dismiss
    test_alarm = post("/api/antitheft/test-alarm", {"ip": "192.168.3.17"})
    alarm_obj = test_alarm.get("alarm", {})
    test("POST /api/antitheft/test-alarm triggers alarm", test_alarm.get("success") and alarm_obj.get("ip") == "192.168.3.17")
    
    # Check status reflects active alarm
    at_status_alert = get("/api/antitheft/status")
    test("Anti-theft status reflects alarm_active == True", at_status_alert.get("alarm_active") == True)
    
    # Dismiss alarm
    dismiss = post("/api/antitheft/dismiss-alarm", {"notes": "Prueba exitosa"})
    test("POST /api/antitheft/dismiss-alarm silences alarm", dismiss.get("success") and dismiss.get("alarm_active") == False)
    
    # Re-check status
    at_status_clear = get("/api/antitheft/status")
    test("Anti-theft status reflects alarm_active == False after dismiss", at_status_clear.get("alarm_active") == False)
except Exception as e:
    test("Anti-theft alarm test", False, str(e))

print("="*70)
print(f"TEST SUMMARY: {passed} PASSED, {failed} FAILED")
print("="*70)
sys.exit(0 if failed == 0 else 1)

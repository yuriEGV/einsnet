#!/usr/bin/env python3
"""
EinsNet - Guardián y Supervisor Automático del Servidor v1.3
Supervisa netguard_server.py 24/7. Si el servidor se cae, falla o es cerrado,
lo levanta inmediatamente en segundo plano.
"""
import sys
import os
import time
import socket
import subprocess
import urllib.request
import urllib.error

# Forzar codificación segura UTF-8 en consola de Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR, "supervisor.log")
LOCK_PORT = 8769  # Puerto local exclusivo para asegurar instancia única del supervisor

def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    try:
        print(line)
    except Exception:
        pass
    try:
        # Rotar log si supera 1MB
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1024 * 1024:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-500:]
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_python_executables():
    """Obtiene pythonw.exe (silencioso) y python.exe"""
    cur_py = sys.executable
    py_dir = os.path.dirname(cur_py)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = cur_py
    python = os.path.join(py_dir, "python.exe")
    if not os.path.exists(python):
        python = cur_py
    return python, pythonw

def is_server_healthy():
    """Verifica si el servidor responde en el puerto 8000"""
    for port in [8000]:
        url = f"http://127.0.0.1:{port}/api/status"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EinsNet-Supervisor/1.3"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False

def kill_stuck_server():
    """Si el servidor no responde por HTTP pero el puerto sigue tomado, libera el puerto 8000"""
    if os.name != 'nt':
        return
    try:
        cmd = 'powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid > 0 and pid != os.getpid():
                    log(f"[*] Liberando proceso en conflicto en puerto EinsNet 8000 (PID {pid})...")
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"[!] Error al verificar procesos colgados: {e}")

def start_server_process():
    """Inicia netguard_server.py en un proceso totalmente desacoplado y protegido"""
    python_exe, pythonw = get_python_executables()
    server_script = os.path.join(APP_DIR, "netguard_server.py")
    
    # Si no responde pero hay puertos colgados, limpiarlos
    if not is_server_healthy():
        kill_stuck_server()

    # Usar python.exe con CREATE_NO_WINDOW (0x08000000) para ejecución headless robusta en Windows
    launcher_exe = python_exe
    creationflags = 0
    if os.name == 'nt':
        creationflags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

    log(f"[*] Levantando servidor EinsNet...")
    try:
        proc = subprocess.Popen(
            [launcher_exe, server_script],
            cwd=APP_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=(os.name != 'nt')
        )
        log(f"[OK] Proceso servidor lanzado con PID: {proc.pid}")
        
        # Esperar hasta 8 segundos para confirmar arranque
        for i in range(16):
            time.sleep(0.5)
            if is_server_healthy():
                log("[OK] Servidor EinsNet respondiendo exitosamente en http://localhost:8000")
                return True
        log("[!] Servidor lanzado, verificando respuesta en el siguiente ciclo...")
        return is_server_healthy()
    except Exception as e:
        log(f"[ERROR] Error al iniciar servidor: {e}")
        return False

def start_supervisor_daemon():
    """Lanza una instancia de este supervisor en segundo plano si no está corriendo"""
    python_exe, _ = get_python_executables()
    launcher_exe = python_exe
    this_script = os.path.abspath(__file__)
    
    creationflags = 0
    if os.name == 'nt':
        creationflags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

    try:
        proc = subprocess.Popen(
            [launcher_exe, this_script, "--daemon"],
            cwd=APP_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=(os.name != 'nt')
        )
        log(f"[OK] Guardián de fondo activado con PID: {proc.pid}")
        return True
    except Exception as e:
        log(f"[ERROR] No se pudo lanzar daemon supervisor: {e}")
        return False

def acquire_lock():
    """Asegura que solo haya UN supervisor corriendo"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', LOCK_PORT))
        s.listen(1)
        return s
    except socket.error:
        return None

def run_daemon():
    """Bucle continuo de supervisión y auto-recuperación 24/7"""
    lock_sock = acquire_lock()
    if not lock_sock:
        log("[*] Ya existe un supervisor EinsNet activo en segundo plano.")
        return

    log("==================================================================")
    log("  EinsNet Guardián Activo - Monitoreo y Auto-Reinicio Continuo   ")
    log("==================================================================")

    if not is_server_healthy():
        log("[!] Servidor caído al iniciar supervisor. Levantando...")
        start_server_process()
    else:
        log("[OK] Servidor activo y saludable al inicio.")

    consecutive_failures = 0

    while True:
        try:
            time.sleep(5)
            if is_server_healthy():
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                log(f"[ALERTA] Servidor EinsNet no responde (Fallo {consecutive_failures}).")
                
                # Al primer fallo verificado, levantar inmediatamente
                log("[!] El servidor se ha caído o cerrado. Levantándolo de inmediato...")
                start_server_process()
                time.sleep(3)
        except Exception as e:
            log(f"[ERROR] Excepción en bucle de supervisión: {e}")
            time.sleep(5)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--ensure":
        # Asegurar servidor
        server_ok = is_server_healthy()
        if not server_ok:
            log("[*] Invocado --ensure: Servidor abajo. Levantando...")
            start_server_process()
        else:
            log("[*] Invocado --ensure: Servidor ya se encuentra activo.")

        # Asegurar guardián supervisor en segundo plano
        test_sock = acquire_lock()
        if test_sock:
            test_sock.close()
            time.sleep(0.3)
            log("[*] Iniciando Guardián supervisor en segundo plano...")
            start_supervisor_daemon()
        else:
            log("[*] Guardián supervisor en segundo plano ya estaba activo.")

        sys.exit(0)

    # Modo daemon permanente
    run_daemon()

if __name__ == '__main__':
    main()

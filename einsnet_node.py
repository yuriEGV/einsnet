#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 EinsNet · Nodo Receptor Seguro & Enlace Multi-Sede v5.0 (Python Nativo)
 Sede Patricio Lynch (Campus Central) ↔ Sede Levarte (Módulo A-15)
 
 - Cero dependencias de terceros: 100% Python estándar (Windows y Linux)
 - Canal Dual Fail-Safe: Baliza UDP (Puerto 8888) + Polling HTTP Sede
 - Alerta gráfica nativa con síntesis de voz en español y sonido
 - Casilla interactiva de respuesta instantánea hacia el Administrador
 - Modo Satélite / Relay (--satellite) para enlazar sedes completas
 - Instalador permanente automático (--install) para inicio con Windows
═══════════════════════════════════════════════════════════════════════════
"""
import sys
import os
import json
import socket
import time
import threading
import subprocess
import platform
import urllib.request
import urllib.parse

# ── CONFIGURACIÓN BASE ──
UDP_PORT = 8888
HTTP_PORTS = [8765, 8000]
APP_NAME = "EinsNet"
NODE_VERSION = "5.0"

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def get_local_ips():
    """Detecta todas las IPs locales asociadas a este equipo"""
    ips = ["127.0.0.1"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 80))
        main_ip = s.getsockname()[0]
        s.close()
        if main_ip not in ips:
            ips.insert(0, main_ip)
    except Exception:
        pass
    try:
        host_name = socket.gethostname()
        for info in socket.getaddrinfo(host_name, None):
            ip = info[4][0]
            if ':' not in ip and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips

LOCAL_IPS = get_local_ips()
PRIMARY_IP = LOCAL_IPS[0] if LOCAL_IPS else "127.0.0.1"
COMPUTER_NAME = socket.gethostname()

# Detección automática de la sede
if PRIMARY_IP.startswith("192.168.80."):
    CURRENT_SEDE = "lynch"
elif PRIMARY_IP.startswith("192.168.1.") or PRIMARY_IP.startswith("192.168.9."):
    CURRENT_SEDE = "levarte"
else:
    CURRENT_SEDE = "lynch"

def resolve_server_address(custom_host=None):
    """Determina la IP y puerto del servidor EinsNet más adecuado"""
    if custom_host:
        host = custom_host
        port = 8765 if CURRENT_SEDE == "lynch" else 8000
        if ":" in custom_host:
            parts = custom_host.split(":")
            host = parts[0]
            port = int(parts[1])
        return host, port

    # Revisar variable de entorno
    if os.environ.get("EINSNET_SERVER"):
        env_val = os.environ.get("EINSNET_SERVER")
        if ":" in env_val:
            h, p = env_val.split(":")
            return h, int(p)
        return env_val, 8765

    # Revisar archivos de configuración locales
    for pth in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_ip.txt"),
        "C:\\ProgramData\\EinsNet\\server_ip.txt",
        "C:\\ProgramData\\NetGuard\\server_ip.txt"
    ]:
        if os.path.exists(pth):
            try:
                with open(pth, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val:
                        return val, (8765 if CURRENT_SEDE == "lynch" else 8000)
            except Exception:
                pass

    # Prueba de servidor local en este mismo PC
    for p in HTTP_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex(('127.0.0.1', p)) == 0:
                s.close()
                return '127.0.0.1', p
            s.close()
        except Exception:
            pass

    # Valores por defecto según sede
    if CURRENT_SEDE == "levarte":
        return "192.168.1.131", 8000
    return "192.168.80.22", 8765

# ── SÍNTESIS DE VOZ Y SONIDO NATIVO ──
def play_alert_sound():
    """Emite un sonido de alerta nativo sin librerías externas"""
    try:
        if sys.platform == 'win32':
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        else:
            sys.stdout.write('\a')
            sys.stdout.flush()
    except Exception:
        pass

def speak_message(text):
    """Pronuncia el mensaje en voz alta en español nativo de Windows"""
    if sys.platform != 'win32':
        return
    try:
        clean = text.replace('"', ' ').replace("'", " ")[:140]
        cmd = f'(New-Object -ComObject SAPI.SpVoice).Speak("{clean}")'
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

# ── VENTANA GRÁFICA DE ALERTA Y RESPUESTA ──
SHOWN_ALERTS = {}

def show_graphical_alert(title, message, sender_ip="Consola Central", server_host="127.0.0.1", server_port=8765):
    """Muestra una ventana emergente gráfica profesional con casilla de respuesta interactiva"""
    play_alert_sound()
    speak_message(f"Atención. {title}. {message}")

    try:
        import tkinter as tk
        from tkinter import messagebox

        def on_send_reply(root, txt_entry, lbl_status):
            reply_text = txt_entry.get("1.0", tk.END).strip()
            if not reply_text:
                return
            try:
                payload = json.dumps({
                    "sender_ip": PRIMARY_IP,
                    "sender_name": f"{COMPUTER_NAME} ({CURRENT_SEDE.upper()})",
                    "message": reply_text
                }).encode('utf-8')
                req = urllib.request.Request(
                    f"http://{server_host}:{server_port}/api/send-reply",
                    data=payload,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        lbl_status.config(text="✓ ¡Respuesta entregada con éxito a Soporte TI!", fg="#34d399")
                        txt_entry.delete("1.0", tk.END)
                        root.after(3000, root.destroy)
            except Exception as ex:
                lbl_status.config(text=f"Error al enviar respuesta: {ex}", fg="#f87171")

        def run_gui():
            root = tk.Tk()
            root.title(f"EinsNet · {title}")
            root.geometry("540x400")
            root.configure(bg="#0f172a")
            root.attributes('-topmost', True)
            root.resizable(False, False)

            # Header Banner
            header_frame = tk.Frame(root, bg="#1e293b", padx=16, pady=12)
            header_frame.pack(fill=tk.X)

            icon_lbl = tk.Label(header_frame, text="🚨", font=("Segoe UI Emoji", 24), bg="#1e293b", fg="#00f5ff")
            icon_lbl.pack(side=tk.LEFT, padx=(0, 10))

            title_lbl = tk.Label(
                header_frame,
                text=title.upper(),
                font=("Segoe UI", 13, "bold"),
                bg="#1e293b",
                fg="#f87171" if "EMERGENCIA" in title.upper() or "ALERTA" in title.upper() else "#38bdf8"
            )
            title_lbl.pack(anchor=tk.W)

            sub_lbl = tk.Label(
                header_frame,
                text=f"Emitido desde: {sender_ip} · Sede: {CURRENT_SEDE.capitalize()}",
                font=("Segoe UI", 9),
                bg="#1e293b",
                fg="#94a3b8"
            )
            sub_lbl.pack(anchor=tk.W)

            # Mensaje Body
            body_frame = tk.Frame(root, bg="#0f172a", padx=18, pady=14)
            body_frame.pack(fill=tk.BOTH, expand=True)

            msg_box = tk.Text(body_frame, font=("Segoe UI", 11), bg="#1e293b", fg="#f1f5f9", wrap=tk.WORD, height=4, relief=tk.FLAT, padx=10, pady=10)
            msg_box.insert(tk.END, message)
            msg_box.configure(state=tk.DISABLED)
            msg_box.pack(fill=tk.X, pady=(0, 10))

            # Casilla de respuesta al Administrador
            reply_lbl = tk.Label(body_frame, text="💬 Responder directamente a Soporte TI / Administrador:", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#a7f3d0")
            reply_lbl.pack(anchor=tk.W, pady=(2, 4))

            reply_entry = tk.Text(body_frame, font=("Segoe UI", 10), bg="#1e293b", fg="#ffffff", height=2, relief=tk.FLAT, padx=8, pady=6)
            reply_entry.pack(fill=tk.X, pady=(0, 6))

            status_lbl = tk.Label(body_frame, text="", font=("Segoe UI", 9), bg="#0f172a")
            status_lbl.pack(anchor=tk.W)

            # Botones
            btn_frame = tk.Frame(root, bg="#0f172a", padx=18, pady=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            btn_send = tk.Button(
                btn_frame,
                text="✉️ Enviar Respuesta",
                font=("Segoe UI", 10, "bold"),
                bg="#10b981",
                fg="#ffffff",
                activebackground="#059669",
                relief=tk.FLAT,
                padx=14,
                pady=6,
                cursor="hand2",
                command=lambda: on_send_reply(root, reply_entry, status_lbl)
            )
            btn_send.pack(side=tk.LEFT)

            btn_close = tk.Button(
                btn_frame,
                text="Entendido / Cerrar",
                font=("Segoe UI", 10),
                bg="#334155",
                fg="#ffffff",
                activebackground="#475569",
                relief=tk.FLAT,
                padx=14,
                pady=6,
                cursor="hand2",
                command=root.destroy
            )
            btn_close.pack(side=tk.RIGHT)

            root.mainloop()

        th = threading.Thread(target=run_gui, daemon=True)
        th.start()
        return

    except Exception:
        pass

    # Fallback si Tkinter no estuviese disponible
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, f"EinsNet: {title}", 0x30 | 0x1000)
        except Exception:
            pass
    else:
        try:
            subprocess.run(["notify-send", title, message, "-u", "critical"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# ── HILOS DE ESCUCHA Y SINCRONIZACIÓN ──
class EinsNetNode:
    def __init__(self, server_host=None, is_satellite=False):
        self.server_host, self.server_port = resolve_server_address(server_host)
        self.is_satellite = is_satellite
        self.running = True
        self.seen_alerts = set()
        print("═" * 68)
        print(f" EinsNet · Nodo Receptor y Enlace Escolar v{NODE_VERSION}")
        print("═" * 68)
        print(f"[*] Equipo Local: {COMPUTER_NAME} | IP Principal: {PRIMARY_IP}")
        print(f"[*] Sede Asignada: {'Sede Patricio Lynch' if CURRENT_SEDE == 'lynch' else 'Sede Levarte'}")
        print(f"[*] Servidor Maestro Enlazado: http://{self.server_host}:{self.server_port}")
        print(f"[*] Rol de este Nodo: {'🟢 SERVIDOR SATÉLITE / RELAY' if self.is_satellite else '📱 AGENTE RECEPTOR LAN'}")
        print("═" * 68)

    def heartbeat_worker(self):
        """Reporta periódicamente la presencia activa de este equipo a la consola maestra"""
        while self.running:
            try:
                payload = json.dumps({
                    "ip": PRIMARY_IP,
                    "hostname": COMPUTER_NAME,
                    "os": f"{platform.system()} {platform.release()} (Nodo Python v{NODE_VERSION})",
                    "sede": CURRENT_SEDE,
                    "is_satellite": self.is_satellite,
                    "timestamp": time.time()
                }).encode('utf-8')
                req = urllib.request.Request(
                    f"http://{self.server_host}:{self.server_port}/api/agent-heartbeat",
                    data=payload,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    pass
            except Exception:
                pass
            time.sleep(6)

    def udp_listener_worker(self):
        """Escucha instantánea por socket UDP puerto 8888"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', UDP_PORT))
            print(f"[OK] Canal UDP activo escuchando balizas en el puerto {UDP_PORT}...")
        except Exception as e:
            print(f"[!] No se pudo enlazar socket UDP 8888 ({e}). Usando fail-safe HTTP.")
            return

        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                if not data:
                    continue
                payload = json.loads(data.decode('utf-8', errors='replace'))
                target_ip = payload.get("target_ip", "*").strip()
                message = payload.get("message", "").strip()
                title = payload.get("title", "AVISO OFICIAL DE ADMINISTRACIÓN")
                sender = payload.get("sender_ip", addr[0])
                alert_id = payload.get("id") or f"{sender}_{message}_{payload.get('timestamp')}"

                # Comprobar si la alerta es para este equipo o para toda la red
                is_for_me = (
                    target_ip in ("*", "all", "255.255.255.255", "") or
                    target_ip in LOCAL_IPS or
                    target_ip.lower() == COMPUTER_NAME.lower() or
                    (self.is_satellite and CURRENT_SEDE == "levarte")
                )

                if is_for_me and message and alert_id not in self.seen_alerts:
                    self.seen_alerts.add(alert_id)
                    print(f"\n[🚨 ALERTA RECIBIDA VÍA UDP] {title}: {message}")
                    show_graphical_alert(title, message, sender, self.server_host, self.server_port)

                    # Si es satélite, retransmitir localmente en Levarte
                    if self.is_satellite:
                        self.relay_local_broadcast(payload)
            except Exception:
                pass

    def http_polling_worker(self):
        """Consulta cada 1.5 seg al servidor por si UDP fue bloqueado o para alertas inter-sedes"""
        print("[OK] Canal HTTP Fail-Safe activo consultando servidor maestro...")
        while self.running:
            try:
                req = urllib.request.Request(
                    f"http://{self.server_host}:{self.server_port}/api/alerts",
                    headers={'User-Agent': 'EinsNet-Python-Node/5.0'}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        alerts = json.loads(resp.read().decode('utf-8'))
                        for k, item in alerts.items():
                            if not item or not isinstance(item, dict):
                                continue
                            msg = item.get("message", "").strip()
                            alert_id = item.get("id") or f"{item.get('ip')}_{msg}"
                            target_ips = item.get("target_ips", [])
                            item_ip = item.get("ip", "*").strip()

                            is_for_me = (
                                item_ip in ("*", "EMERGENCY", "LATEST") or
                                any(ip in LOCAL_IPS for ip in target_ips) or
                                COMPUTER_NAME in target_ips or
                                PRIMARY_IP == item_ip
                            )

                            if is_for_me and msg and alert_id not in self.seen_alerts:
                                self.seen_alerts.add(alert_id)
                                title = item.get("title", "MENSAJE DE ADMINISTRACIÓN")
                                sender = item.get("sender_ip", self.server_host)
                                print(f"\n[🚨 ALERTA RECIBIDA VÍA HTTP] {title}: {msg}")
                                show_graphical_alert(title, msg, sender, self.server_host, self.server_port)

                                if self.is_satellite:
                                    self.relay_local_broadcast(item)
            except Exception:
                pass
            time.sleep(1.5)

    def relay_local_broadcast(self, alert_data):
        """Retransmite una alerta de Lynch localmente por broadcast en la subred de Levarte"""
        try:
            bcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            raw = json.dumps(alert_data).encode('utf-8')
            # Enviar a la subred de Levarte
            for b_ip in ["192.168.1.255", "192.168.9.255", "255.255.255.255"]:
                try:
                    bcast_sock.sendto(raw, (b_ip, UDP_PORT))
                except Exception:
                    pass
            bcast_sock.close()
        except Exception:
            pass

    def start(self):
        """Inicia todos los hilos del nodo EinsNet"""
        t_heartbeat = threading.Thread(target=self.heartbeat_worker, daemon=True)
        t_udp = threading.Thread(target=self.udp_listener_worker, daemon=True)
        t_http = threading.Thread(target=self.http_polling_worker, daemon=True)

        t_heartbeat.start()
        t_udp.start()
        t_http.start()

        print("\n[LISTO] Nodo EinsNet en ejecución permanente.")
        print("[*] Presiona Ctrl+C para salir.\n")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Deteniendo nodo EinsNet...")
            self.running = False

# ── INSTALADOR PERMANENTE PARA WINDOWS ──
def install_node_permanently():
    """Instala el nodo de forma permanente y silenciosa para que inicie con Windows"""
    if sys.platform != 'win32':
        print("[!] La autoinstalación permanente con esta rutina está optimizada para Windows.")
        return

    print("═════════════════════════════════════════════════════════════")
    print("   Instalando EinsNet Node Permanente en este Equipo...      ")
    print("═════════════════════════════════════════════════════════════")

    install_dir = r"C:\ProgramData\EinsNet"
    if not os.path.exists(install_dir):
        os.makedirs(install_dir, exist_ok=True)

    target_script = os.path.join(install_dir, "einsnet_node.py")
    current_script = os.path.abspath(__file__)

    # Copiar script
    with open(current_script, "r", encoding="utf-8") as sf:
        code = sf.read()
    with open(target_script, "w", encoding="utf-8") as df:
        df.write(code)

    # Crear lanzador VBS totalmente transparente y silencioso
    vbs_path = os.path.join(install_dir, "run_einsnet_node.vbs")
    py_exe = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(py_exe):
        py_exe = sys.executable

    vbs_content = f'CreateObject("Wscript.Shell").Run "{py_exe} ""{target_script}""", 0, False\n'
    with open(vbs_path, "w", encoding="ascii") as vf:
        vf.write(vbs_content)

    # Configurar Firewall de Windows para UDP 8888
    try:
        subprocess.run(
            ['netsh', 'advfirewall', 'firewall', 'add', 'rule', 'name=EinsNet_Node_UDP',
             'dir=in', 'action=allow', 'protocol=UDP', 'localport=8888', 'profile=any'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(" [OK] Regla de Firewall configurada para Puerto UDP 8888.")
    except Exception:
        pass

    # Copiar a carpeta Inicio (Startup) de Todos los Usuarios
    startup_dir = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"),
                               r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(startup_dir):
        startup_vbs = os.path.join(startup_dir, "EinsNet_Node.vbs")
        with open(startup_vbs, "w", encoding="ascii") as svf:
            svf.write(vbs_content)
        print(" [OK] Registrado en Inicio automático de Windows.")

    # Iniciar ahora mismo
    subprocess.Popen(["wscript.exe", vbs_path])
    print(" [OK] Nodo EinsNet instalado e iniciado con éxito en segundo plano.")
    print("═════════════════════════════════════════════════════════════")
    print("¡Listo! Este equipo ahora recibirá todas las alertas y mensajes.")
    time.sleep(3)

def main():
    if "--install" in sys.argv:
        install_node_permanently()
        return

    is_sat = "--satellite" in sys.argv or "--relay" in sys.argv
    server_arg = None
    for i, a in enumerate(sys.argv):
        if a == "--server" and i + 1 < len(sys.argv):
            server_arg = sys.argv[i + 1]

    node = EinsNetNode(server_host=server_arg, is_satellite=is_sat)
    node.start()

if __name__ == '__main__':
    main()

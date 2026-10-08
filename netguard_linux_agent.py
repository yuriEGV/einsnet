#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
 NetGuard · Agente Receptor de Alertas de Red para Linux (ThinkPad / PC)
 Compatible con Ubuntu, Debian, Fedora, Arch, Linux Mint, etc.
 Recibe las advertencias enviadas desde NetGuard y las muestra como:
 1. Notificación nativa de escritorio (notify-send)
 2. Ventana emergente gráfica (zenity / kdialog)
 3. Aviso por terminal (wall)
═══════════════════════════════════════════════════════════════════════════
"""
import sys
import os
import json
import socket
import subprocess

PORT = 8888

def show_linux_notification(title, message):
    # 1. Notificación visual de escritorio (burbuja de notificación)
    try:
        subprocess.run([
            "notify-send", 
            title, 
            message, 
            "-u", "critical", 
            "-i", "dialog-warning", 
            "-t", "15000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 2. Ventana emergente emergente gráfica (Zenity)
    try:
        subprocess.Popen([
            "zenity", 
            "--warning", 
            f"--title={title}", 
            f"--text={message}", 
            "--width=420"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 3. Aviso de consola a todas las terminales abiertas (wall)
    try:
        p = subprocess.Popen(["wall"], stdin=subprocess.PIPE, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.communicate(input=f"\n[ALERTA DE SEGURIDAD NETGUARD LAN]\n{title}\nMensaje: {message}\n")
    except Exception:
        pass

def get_local_ips():
    ips = ["127.0.0.1"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('192.168.80.1', 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        for ip in out.stdout.split():
            if ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips

def main():
    print("═════════════════════════════════════════════════════════════")
    print("   NetGuard · Agente Receptor de Alertas LAN para Linux     ")
    print("═════════════════════════════════════════════════════════════")
    my_ips = get_local_ips()
    print(f"[*] IPs locales detectadas en este Linux: {my_ips}")
    print(f"[*] Escuchando balizas de alerta en UDP puerto {PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))

    print("[OK] Agente activo. Listo para recibir advertencias del Administrador.")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            payload = json.loads(data.decode('utf-8', errors='replace'))
            target_ip = payload.get("target_ip", "").strip()
            msg = payload.get("message", "").strip()
            sender = payload.get("sender_ip", "Administrador NetGuard")

            title = payload.get("title", f"⚠️ AVISO DE RED · Administrador ({sender})")

            # Verificar si el mensaje va dirigido a este equipo o broadcast general / emergencia
            is_for_me = (target_ip in my_ips) or (target_ip in ("255.255.255.255", "0.0.0.0", "all", "*", ""))
            
            if is_for_me:
                print(f"\n[!] ALERTA RECIBIDA desde {sender} para {target_ip}:")
                print(f"    \"{msg}\"")
                show_linux_notification(title, msg)
            else:
                # Mensaje para otra máquina de la LAN
                print(f"[*] Notificación en red para otro host: {target_ip}")
        except Exception as e:
            pass

if __name__ == '__main__':
    main()

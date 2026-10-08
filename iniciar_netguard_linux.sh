#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  NetGuard · Iniciar Servidor y Dashboard en Linux
# ═══════════════════════════════════════════════════════════

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[*] Iniciando servidor NetGuard en Linux..."
python3 netguard_server.py &

sleep 1
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8765"
elif command -v google-chrome &> /dev/null; then
    google-chrome "http://localhost:8765" &
elif command -v firefox &> /dev/null; then
    firefox "http://localhost:8765" &
fi

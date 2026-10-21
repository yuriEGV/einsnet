#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  EinsNet · Iniciar Servidor y Dashboard en Linux (Puerto 8000)
# ═══════════════════════════════════════════════════════════

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "[*] Comprobando actualizaciones desde GitHub..."
if command -v git &> /dev/null; then
    git fetch origin main > /dev/null 2>&1
    git reset --hard origin/main > /dev/null 2>&1
fi

echo "[*] Deteniendo instancias previas..."
pkill -f "python.*netguard_server.py" > /dev/null 2>&1

echo "[*] Iniciando servidor EinsNet v6.0 en Linux (Puerto 8000)..."
python3 netguard_server.py &

sleep 2
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000"
elif command -v google-chrome &> /dev/null; then
    google-chrome "http://localhost:8000" &
elif command -v firefox &> /dev/null; then
    firefox "http://localhost:8000" &
fi

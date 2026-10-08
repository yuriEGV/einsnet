#!/bin/bash
# ===========================================================
#  NetGuard - Iniciar Agente Receptor en Linux (ThinkPad / PC)
#  Ejecucion rapida desde terminal Linux:
#    curl -s http://192.168.80.22:8765/iniciar_agente_linux.sh | bash
# ===========================================================

if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    DIR="/tmp/netguard"
    mkdir -p "$DIR"
fi

cd "$DIR"

echo "=========================================================="
echo "  Iniciando Agente Receptor NetGuard para Linux"
echo "=========================================================="

# Instalar libnotify si no existe (para notificaciones graficas)
if ! command -v notify-send &> /dev/null; then
    echo "[*] Instalando herramientas de notificacion..."
    sudo apt-get update -y && sudo apt-get install -y libnotify-bin zenity 2>/dev/null || true
fi

# Descargar agente receptor si no existe en la carpeta
if [ ! -f "$DIR/netguard_linux_agent.py" ]; then
    echo "[*] Descargando agente receptor desde consola NetGuard..."
    curl -s "http://192.168.80.22:8765/netguard_linux_agent.py" -o "$DIR/netguard_linux_agent.py" 2>/dev/null || wget -q "http://192.168.80.22:8765/netguard_linux_agent.py" -O "$DIR/netguard_linux_agent.py"
fi

# Iniciar agente receptor en Python 3
python3 "$DIR/netguard_linux_agent.py"

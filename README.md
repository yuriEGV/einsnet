# EinsNet · Control Total de Red LAN & Auditoría Multi-Sede

Plataforma de gestión, monitoreo en tiempo real, auditoría de seguridad y mapeo arquitectónico por pisos para redes educativas y corporativas (Sede Patricio Lynch & Sede Levarte).

---

## 🚀 Características Principales

- **🌐 Topología Interactiva de Red (Tiempo Real & Dual Bisede)**:
  - Visualización interactiva con nodos arrastrables, zoom, pan y auto-layout por cuadrantes.
  - Modos de visualización: **Solo Sede Levarte**, **Solo Sede Lynch** o **Ambos Mapas (Dual)** con enlace y túnel WAN activo inter-sedes.
  - Indicadores y conteo dinámico de nodos en vivo y latencia ICMP.
  
- **📐 Plano Arquitectónico y Despliegue Físico por Piso (Escala 1:200)**:
  - Basado en los planos oficiales CAD DWG:
    - `Plantas Arq_Mod A-15 Levarte.dwg` (Módulo A-15 · 1° y 2° Medio): Bajo Nivel (Zócalo / Taller), Nivel 1 (Calle Levarte, Administración, Docentes) y Nivel 2 (Aulas 2° Medio y WiFi Cascada).
    - `planta_Lynch.dwg` (Sede Patricio Lynch · 3° y 4° Medio): Nivel 1, Nivel 2 y Nivel 3 (Simuladores Portuarios TOS, Grúas STS/RTG, Gastronomía, Elaboración Industrial, Química).
  - Filtros dinámicos por recinto, sala o especialidad.
  - Inspección física de equipos, estado LAN, IP, MAC y pruebas de ping directas.

- **📡 Escáner Multi-Red & Descubrimiento de Extensiones**:
  - Detección y auditoría de subredes subordinadas en cascada detrás de routers y switches (`192.168.1.0/24`, `192.168.9.0/24`, `192.168.14.0/24`, `192.168.15.0/24`, `192.168.17.0/24`, `172.16.16.0/24`, etc.).
  - Integración automática de nuevos dispositivos a la topología y base de datos local.

- **💬 Comunicación y Alertas LAN**:
  - Envío de mensajes y notificaciones de evacuación/emergencia directas a puestos de trabajo y salas completas.
  - Agente receptor multiplataforma para Windows (`netguard_agent_windows.ps1`) y Linux (`netguard_linux_agent.py`).

- **🛡️ Auditoría WAN & SOC**:
  - Detección de puertos inseguros (Telnet, FTP sin cifrar).
  - Listas de bloqueo DNS y control de acceso MAC.

---

## 🛠️ Tecnologías

- **Backend**: Python 3 (HTTP REST API, Socket Ping ICMP, ARP / Subnet Scanner, Servidor Asíncrono).
- **Frontend**: HTML5 Semántico, CSS3 Moderno (Glassmorphism, Neon Dark Theme, Flexbox/Grid), JavaScript Vanilla ES6+ Canvas 2D.
- **Agentes**: PowerShell 5.1/7+ para estaciones Windows, Python / Bash para terminales Linux.

---

## 💻 Puesta en Marcha

### Requisitos
- Python 3.8+ instalado en el sistema.

### Iniciar EinsNet (Servidor Local)
```powershell
# En PowerShell
python netguard_server.py 8000
```
O ejecutando el acceso directo:
```cmd
Abrir_EinsNet.bat
```
La aplicación web estará disponible inmediatamente en `http://localhost:8000`.

---

## 📂 Estructura del Proyecto

```
conexiones/
├── index.html                 # Interfaz visual principal (SPA)
├── app.js                     # Motor de topología Canvas, navegación y planos
├── style.css                  # Sistema de diseño, temas y componentes
├── netguard_server.py         # Servidor API REST y motor de escaneo de red
├── scanner_pro.js             # Módulo de auditoría y escaneo de extensiones
├── alerts.js                  # Centro de alertas y notificaciones SOC
├── soc.js                     # Panel de seguridad y amenazas
├── netguard_agent_windows.ps1 # Agente receptor para clientes Windows
├── netguard_linux_agent.py    # Agente receptor para clientes Linux
├── Plantas Arq_Mod A-15 Levarte.dwg # Plano CAD oficial Sede Levarte
├── planta_Lynch.dwg           # Plano CAD oficial Sede Patricio Lynch
└── Abrir_EinsNet.bat          # Acceso directo para ejecución rápida
```

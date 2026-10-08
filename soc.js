/* ═══════════════════════════════════════════════════════════
   NetGuard Pro · soc.js — Centro de Operaciones de Seguridad
   Módulos: Risk Score, Timeline, Heatmap, Health Scores,
   Risky Services, Geolocation Intel, Vulnerability Scanner
   ═══════════════════════════════════════════════════════════ */
'use strict';

// ── SOC STATE ──────────────────────────────────────────────
const SOC = {
  events: [],
  anomalies: 0,
  lastUpdate: Date.now(),
  feedInterval: null,
  timelineInterval: null,
  vulnScanned: false,
  geoCache: [],
};

// ── THREAT EVENT TEMPLATES ─────────────────────────────────
const EVENT_TEMPLATES = [
  { sev:'crit', icon:'🚨', title:'Conexión C2 detectada',            desc: ip => `${ip} intentó conectar a 185.234.218.4:4444 (Metasploit C2)` },
  { sev:'crit', icon:'💀', title:'Escaneo de puertos agresivo',       desc: ip => `${ip} envió ráfaga SYN a 254 hosts en 2 segundos` },
  { sev:'high', icon:'🔓', title:'Intento de fuerza bruta',          desc: ip => `${ip} intentó acceso SSH/RDP: 47 fallos en 30s` },
  { sev:'high', icon:'⚠️', title:'Telnet sin cifrado activo',         desc: ip => `${ip} transmite credenciales en texto plano (puerto 23)` },
  { sev:'high', icon:'🦠', title:'SMB v1 expuesto',                   desc: ip => `${ip} responde a EternalBlue probe (MS17-010)` },
  { sev:'med',  icon:'📡', title:'ARP Spoofing detectado',            desc: ip => `Tabla ARP anómala: ${ip} duplica MACs en la subred` },
  { sev:'med',  icon:'🌐', title:'DNS sobre puerto no estándar',      desc: ip => `${ip} consultas DNS en puerto 5353 inusualmente frecuentes` },
  { sev:'med',  icon:'📊', title:'Consumo anómalo de ancho de banda', desc: ip => `${ip} superó 10x su baseline histórico (posible exfiltración)` },
  { sev:'low',  icon:'🔍', title:'Nuevo dispositivo detectado',       desc: ip => `Dispositivo desconocido conectado a la red desde ${ip}` },
  { sev:'low',  icon:'⏱️', title:'Latencia elevada sostenida',        desc: ip => `${ip} supera 150ms por más de 5 minutos` },
];

// ── VULNERABILITY DATABASE ─────────────────────────────────
const VULN_DB = [
  {
    sev:'critical', cve:'CVE-2017-0144', type:'RCE · EternalBlue',
    desc:'SMBv1 expuesto. Vector principal de WannaCry/NotPetya. Permite ejecución remota sin autenticación.',
    hosts:['192.168.80.22','192.168.80.70','192.168.80.51'], cvss:9.8,
    remediation:'Deshabilitar SMBv1 y aplicar KB4012212', status:'open', ref:'MS17-010',
  },
  {
    sev:'critical', cve:'CVE-2019-0708', type:'RCE · BlueKeep',
    desc:'RDP vulnerable pre-auth. Explotable remotamente sin credenciales en Windows 7/2008.',
    hosts:['192.168.80.47'], cvss:9.8,
    remediation:'Parche KB4499175 o deshabilitar RDP expuesto', status:'open', ref:'BlueKeep',
  },
  {
    sev:'high', cve:'CVE-2021-34527', type:'PE · PrintNightmare',
    desc:'Servicio Print Spooler permite elevación de privilegios SYSTEM sin ser admin.',
    hosts:['192.168.80.22','192.168.80.47'], cvss:8.8,
    remediation:'Detener Print Spooler si no se necesita + KB5004945', status:'review', ref:'PrintNightmare',
  },
  {
    sev:'high', cve:'CVE-2020-1472', type:'Auth Bypass · Zerologon',
    desc:'Netlogon permite autenticación con contraseña vacía, comprometiendo el dominio completo.',
    hosts:['192.168.80.47'], cvss:10.0,
    remediation:'Parche agosto 2020 (KB4566782) urgente', status:'open', ref:'Zerologon',
  },
  {
    sev:'medium', cve:'CVE-2020-0601', type:'Crypto · CurveBall',
    desc:'Validación de firmas criptográficas ECC defectuosa en Windows CryptoAPI.',
    hosts:['192.168.80.22','192.168.80.70','192.168.80.14'], cvss:8.1,
    remediation:'KB4528760 en todos los hosts Windows 10', status:'fixed', ref:'NSA reported',
  },
  {
    sev:'medium', cve:'CVE-2022-30190', type:'RCE · Follina MSDT',
    desc:'Ejecución de código a través de documentos Office maliciosos sin abrir macros.',
    hosts:['192.168.80.22'], cvss:7.8,
    remediation:'Deshabilitar MSDT URL handler + parche junio 2022', status:'open', ref:'Follina',
  },
  {
    sev:'low', cve:'CVE-2021-1675', type:'LPE · PrintNightmare v1',
    desc:'Primera variante, elevación de privilegios local mediante cola de impresión.',
    hosts:['192.168.80.21','192.168.80.22'], cvss:6.7,
    remediation:'KB5003637 para Windows Server', status:'fixed', ref:'Print Spooler',
  },
  {
    sev:'low', cve:'BEST-001', type:'Config · Telnet activo',
    desc:'Administración de switches vía Telnet envía credenciales en texto plano.',
    hosts:['192.168.80.10','192.168.80.12','192.168.80.13'], cvss:5.4,
    remediation:'Migrar a SSH v2 en todos los switches TP-Link', status:'open', ref:'RFC 4253',
  },
];

// ── GEO IP INTELLIGENCE ─────────────────────────────────────
const GEO_DB = [
  { ip:'185.234.218.4',  flag:'🇷🇺', country:'Rusia',    isp:'AS64428 Hosting-Media',  threat:'C2 Server',     risk:'crit' },
  { ip:'45.129.33.211',  flag:'🇨🇳', country:'China',    isp:'AS134764 CHINANET',       threat:'Port Scanner',  risk:'high' },
  { ip:'91.214.124.143', flag:'🇺🇦', country:'Ucrania',  isp:'AS44050 Perfect Quality', threat:'Brute Force',   risk:'high' },
  { ip:'198.51.100.12',  flag:'🇩🇪', country:'Alemania', isp:'AS24940 Hetzner Online',  threat:'TOR Exit Node', risk:'med'  },
  { ip:'142.250.80.14',  flag:'🇺🇸', country:'EE.UU.',   isp:'AS15169 Google LLC',      threat:'DNS / CDN',     risk:'ok'   },
  { ip:'17.57.144.61',   flag:'🇺🇸', country:'EE.UU.',   isp:'AS714 Apple Inc.',        threat:'Push / Updates',risk:'ok'   },
  { ip:'52.96.47.186',   flag:'🇮🇪', country:'Irlanda',  isp:'AS8075 Microsoft Corp.',  threat:'Cloud / O365',  risk:'ok'   },
];

// ── RISKY SERVICES ─────────────────────────────────────────
const RISKY_SERVICES = [
  { icon:'🔓', title:'RDP :3389 Expuesto',     desc:'192.168.80.47 — Acceso remoto sin MFA ni restricción de IP de origen', level:'critical' },
  { icon:'📡', title:'Telnet :23 Activo',       desc:'TP-SW-01, TP-SW-02 — Credenciales en texto plano en la red',           level:'critical' },
  { icon:'🌐', title:'SMBv1 :445 Abierto',      desc:'3 hosts — Protocolo obsoleto vulnerable a EternalBlue/WannaCry',       level:'critical' },
  { icon:'⚠️', title:'HTTP Admin :80',          desc:'192.168.80.9 (Belkin) — Panel de admin sin HTTPS',                     level:'high'     },
  { icon:'🔧', title:'SNMP v1 :161',            desc:'Routers TP-Link — Community string por defecto "public"',              level:'high'     },
  { icon:'💾', title:'FTP :21 sin cifrar',      desc:'Transferencia de archivos en texto plano detectada',                   level:'medium'   },
];

// ── HEALTH SCORE CALCULATOR ────────────────────────────────
function calcHealthScore(device) {
  if (device.status === 'offline') return 0;
  let score = 100;
  if (device.lat > 100)      score -= 30;
  else if (device.lat > 50)  score -= 15;
  else if (device.lat > 20)  score -= 5;
  if (device.jitter > 5)     score -= 15;
  else if (device.jitter > 2) score -= 7;
  if (device.loss > 5)       score -= 25;
  else if (device.loss > 0)  score -= 10;
  if (device.threat === 'critical') score -= 40;
  else if (device.threat === 'high')   score -= 25;
  else if (device.threat === 'medium') score -= 10;
  if (device.cpu > 90)   score -= 15;
  else if (device.cpu > 70) score -= 7;
  if (device.ram > 90)   score -= 10;
  else if (device.ram > 80) score -= 4;
  if (device.blocked)    score -= 30;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function healthColor(score) {
  if (score >= 85) return '#10b981';
  if (score >= 65) return '#f59e0b';
  if (score >= 40) return '#f97316';
  return '#ef4444';
}

// ── SOC TIMELINE CHART ─────────────────────────────────────
function renderSOCTimeline() {
  const canvas = document.getElementById('soc-timeline');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = (canvas.parentElement.clientWidth || 800) - 32;
  const H = 90;
  canvas.width = W; canvas.height = H;
  const N = 120;
  const critData = Array.from({length:N}, (_,i) => Math.max(0, Math.round(Math.sin(i/12)*1.5 + Math.random()*2)));
  const highData = Array.from({length:N}, (_,i) => Math.max(0, Math.round(Math.cos(i/8)*2 + Math.random()*3)));
  const medData  = Array.from({length:N}, (_,i) => Math.max(0, Math.round(3 + Math.random()*4)));
  const lowData  = Array.from({length:N}, (_,i) => Math.max(0, Math.round(5 + Math.random()*6)));
  ctx.clearRect(0,0,W,H);
  function drawLine(data, color, alpha) {
    const max = Math.max(...lowData, ...medData, ...highData, ...critData, 1);
    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = alpha; ctx.lineWidth = 1.5;
    data.forEach((v, i) => {
      const x = (i / (N-1)) * W;
      const y = H - 8 - (v / max) * (H - 16);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
    ctx.fillStyle = color; ctx.globalAlpha = alpha * 0.12; ctx.fill(); ctx.globalAlpha = 1;
  }
  drawLine(lowData, '#00f5ff', 0.7);
  drawLine(medData, '#f59e0b', 0.75);
  drawLine(highData,'#f97316', 0.8);
  drawLine(critData,'#ef4444', 0.9);
  ctx.fillStyle = 'rgba(148,163,184,0.5)'; ctx.font = '9px Inter,sans-serif';
  ctx.fillText('-2h', 2, H-1); ctx.fillText('-1h', W/2-10, H-1); ctx.fillText('Ahora', W-32, H-1);
  ctx.strokeStyle = 'rgba(0,245,255,0.6)'; ctx.lineWidth = 1; ctx.setLineDash([3,3]);
  ctx.beginPath(); ctx.moveTo(W-1, 0); ctx.lineTo(W-1, H-12); ctx.stroke(); ctx.setLineDash([]);
}

// ── HEATMAP RENDER ─────────────────────────────────────────
function renderHeatmap() {
  const el = document.getElementById('soc-heatmap');
  if (!el || typeof state === 'undefined') return;
  el.innerHTML = '';
  const devices = state.devices.filter(d => d.status === 'online').slice(0, 20);
  devices.forEach(d => {
    const score = 100 - calcHealthScore(d);
    const hue = Math.round((1 - score/100) * 130);
    const bg = `hsl(${hue}, 75%, ${15 + score * 0.15}%)`;
    const cell = document.createElement('div');
    cell.className = 'hm-cell';
    cell.style.background = bg;
    cell.style.boxShadow = score > 50 ? `0 0 10px hsla(${Math.round((1-score/100)*20)},90%,50%,0.35)` : 'none';
    cell.innerHTML = `<div class="hm-cell-score">${score}</div><div class="hm-cell-ip">${d.ip.split('.').slice(-1)[0]}</div><div class="hm-cell-name">${d.name}</div>`;
    cell.title = `${d.name} (${d.ip}) — Riesgo: ${score}/100`;
    cell.onclick = () => typeof toast !== 'undefined' && toast(`${d.name}: Riesgo ${score}/100 · CPU ${d.cpu}% · RAM ${d.ram}% · Lat ${d.lat}ms`, score > 60 ? 'error' : score > 30 ? 'warning' : 'success');
    el.appendChild(cell);
  });
}

// ── HEALTH SCORES RENDER ───────────────────────────────────
function renderHealthScores() {
  const el = document.getElementById('soc-health-scores');
  if (!el || typeof state === 'undefined') return;
  el.innerHTML = '';
  const sorted = [...state.devices].filter(d => d.ip !== '192.168.80.1').sort((a,b) => calcHealthScore(a) - calcHealthScore(b));
  sorted.forEach(d => {
    const score = calcHealthScore(d);
    const color = healthColor(score);
    const card = document.createElement('div');
    card.className = 'health-card';
    card.innerHTML = `
      <div class="health-ip">${d.ip}</div>
      <div class="health-score-val" style="color:${color}">${score}</div>
      <div class="health-score-bar"><div class="health-score-bar-fill" style="width:${score}%;background:${color}"></div></div>
      <div class="health-name">${d.name}</div>
      <div class="health-meta">
        <span class="health-chip">CPU ${d.cpu}%</span>
        <span class="health-chip">RAM ${d.ram}%</span>
        <span class="health-chip">${d.lat}ms</span>
      </div>
    `;
    el.appendChild(card);
  });
}

// ── ACTIVITY FEED ─────────────────────────────────────────
function addFeedEvent(event) {
  const feed = document.getElementById('soc-activity-feed');
  if (!feed || typeof state === 'undefined') return;
  const devices = state.devices.filter(d => d.status === 'online');
  const randDev = devices[Math.floor(Math.random() * devices.length)];
  if (!randDev) return;
  const tpl = event || EVENT_TEMPLATES[Math.floor(Math.random() * EVENT_TEMPLATES.length)];
  const sevMap = { crit:'crit', high:'high', med:'med', low:'low' };
  const now = new Date().toLocaleTimeString('es-AR', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
  const item = document.createElement('div');
  item.className = `feed-item ${sevMap[tpl.sev] || 'low'}`;
  item.innerHTML = `<div class="feed-icon">${tpl.icon}</div><div class="feed-body"><div class="feed-title">${tpl.title}</div><div class="feed-desc">${tpl.desc(randDev.ip)}</div></div><div class="feed-time">${now}</div>`;
  feed.insertBefore(item, feed.firstChild);
  while (feed.children.length > 12) feed.removeChild(feed.lastChild);
  if (tpl.sev === 'crit' || tpl.sev === 'high') {
    SOC.anomalies++;
    const el = document.getElementById('kpi-anomalies-val');
    if (el) el.textContent = SOC.anomalies;
  }
}

// ── RISKY SERVICES ─────────────────────────────────────────
function renderRiskyServices() {
  const el = document.getElementById('soc-risky-ports');
  if (!el) return;
  el.innerHTML = '';
  RISKY_SERVICES.forEach(s => {
    const item = document.createElement('div');
    item.className = 'risk-item';
    item.innerHTML = `<div class="risk-icon">${s.icon}</div><div class="risk-body"><div class="risk-title">${s.title}</div><div class="risk-desc">${s.desc}</div></div><div class="risk-badge ${s.level}">${s.level === 'critical' ? 'CRÍTICO' : s.level === 'high' ? 'ALTO' : 'MEDIO'}</div>`;
    el.appendChild(item);
  });
}

// ── GEO INTEL ─────────────────────────────────────────────
function renderGeoIntel() {
  const el = document.getElementById('soc-geo-list');
  if (!el) return;
  el.innerHTML = '';
  GEO_DB.forEach(g => {
    const item = document.createElement('div');
    item.className = 'geo-item';
    const rc = g.risk === 'crit' ? 'threat-red' : (g.risk === 'high' || g.risk === 'med') ? 'threat-orange' : 'threat-green';
    const rl = g.risk === 'crit' ? '🔴 CRÍTICO' : g.risk === 'high' ? '🟠 ALTO' : g.risk === 'med' ? '🟡 MEDIO' : '🟢 OK';
    item.innerHTML = `<div class="geo-flag">${g.flag}</div><div class="geo-body"><div class="geo-ip">${g.ip}</div><div class="geo-info">${g.country} · ${g.isp} · ${g.threat}</div></div><div class="geo-threat ${rc}">${rl}</div>`;
    el.appendChild(item);
  });
}

// ── KPI UPDATER ───────────────────────────────────────────
function updateSOCKPIs() {
  if (typeof state === 'undefined') return;
  const online  = state.devices.filter(d => d.status === 'online');
  const healthy = online.filter(d => calcHealthScore(d) >= 70);
  const blocked = state.devices.filter(d => d.blocked || d.vlan == 99);
  const setEl = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
  setEl('kpi-hosts-ok-val', healthy.length);
  if (online.length) {
    const pct = Math.round(healthy.length / online.length * 100);
    const pctEl = document.getElementById('kpi-hosts-pct');
    if (pctEl) { pctEl.textContent = `${pct}% de la red`; pctEl.style.color = pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444'; }
  }
  setEl('kpi-blocked-val', blocked.length);
  const evts = Math.floor(Math.random() * 8) + 2;
  setEl('kpi-events-val', evts);
  const evtTrend = document.getElementById('kpi-events-trend');
  if (evtTrend) { evtTrend.textContent = evts > 7 ? '▲ ALTO' : evts > 4 ? '▲ Elevado' : '▲ Normal'; evtTrend.style.color = evts > 7 ? '#ef4444' : evts > 4 ? '#f59e0b' : '#10b981'; }
  const numCrit = state.devices.filter(d => d.threat === 'critical').length;
  const numHigh = state.devices.filter(d => d.threat === 'high').length;
  const baseRisk = Math.min(100, numCrit * 20 + numHigh * 10 + blocked.length * 5 + 25);
  setEl('threat-score-val', baseRisk);
  const arc = document.getElementById('threat-arc');
  if (arc) { const offset = 201 - (baseRisk / 100) * 201; arc.setAttribute('stroke-dashoffset', offset); arc.setAttribute('stroke', baseRisk > 70 ? 'url(#arcGrad)' : baseRisk > 40 ? '#f59e0b' : '#10b981'); }
  const sub = document.querySelector('#kpi-threat-score .soc-kpi-sub');
  if (sub) { sub.textContent = baseRisk >= 70 ? 'CRÍTICO' : baseRisk >= 40 ? 'MEDIO' : 'BAJO'; sub.style.color = baseRisk >= 70 ? '#ef4444' : baseRisk >= 40 ? '#f59e0b' : '#10b981'; }
}

// ── SOC INIT ──────────────────────────────────────────────
function initSOC() {
  renderSOCTimeline();
  renderHeatmap();
  renderHealthScores();
  renderRiskyServices();
  renderGeoIntel();
  updateSOCKPIs();
  for (let i = 0; i < 5; i++) setTimeout(() => addFeedEvent(), i * 300);
  clearInterval(SOC.feedInterval);
  SOC.feedInterval = setInterval(() => {
    if (typeof state !== 'undefined' && state.currentView === 'soc') addFeedEvent();
  }, 10000);
  clearInterval(SOC.timelineInterval);
  SOC.timelineInterval = setInterval(() => {
    if (typeof state !== 'undefined' && state.currentView === 'soc') { updateSOCKPIs(); renderHeatmap(); }
  }, 5000);
}

// ── VULNERABILITY SCANNER ─────────────────────────────────
function renderVulnTable() {
  const tbody = document.getElementById('vuln-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  VULN_DB.forEach(v => {
    const tr = document.createElement('tr');
    const sc = v.status === 'fixed' ? 'vstatus-fixed' : v.status === 'review' ? 'vstatus-review' : 'vstatus-open';
    const sl = v.status === 'fixed' ? '✅ Solucionado' : v.status === 'review' ? '🔄 En revisión' : '🔴 Abierta';
    tr.innerHTML = `
      <td class="vuln-col-sev"><span class="vsev-badge vsev-${v.sev}">${{critical:'🔴 CRÍTICA',high:'🟠 ALTA',medium:'🟡 MEDIA',low:'🔵 BAJA'}[v.sev]}</span></td>
      <td class="vuln-col-cve"><span class="vcve-code">${v.cve}</span><span class="vcve-type">${v.type}</span></td>
      <td class="vuln-col-desc">${v.desc}</td>
      <td class="vuln-col-hosts"><div class="vsev-hosts-container">${v.hosts.map(h=>`<span class="vsev-host-chip"><span class="vsev-host-icon">🖥️</span>${h}</span>`).join('')}</div></td>
      <td class="vuln-col-cvss"><span class="vcvss-val" style="color:${v.cvss>=9?'#ef4444':v.cvss>=7?'#f97316':'#f59e0b'}">${v.cvss.toFixed(1)}</span></td>
      <td class="vuln-col-remed">${v.remediation}</td>
      <td class="vuln-col-status"><span class="vsev-status ${sc}">${sl}</span></td>`;
    tbody.appendChild(tr);
  });
  const counts = {};
  VULN_DB.forEach(v => counts[v.sev] = (counts[v.sev]||0)+1);
  const setEl = (id,val) => { const e=document.getElementById(id); if(e) e.textContent=val; };
  setEl('vsev-critical', counts.critical||0); setEl('vsev-high', counts.high||0);
  setEl('vsev-medium', counts.medium||0); setEl('vsev-low', counts.low||0);
  const totalCVSS = VULN_DB.filter(v=>v.status!=='fixed').reduce((s,v)=>s+v.cvss,0);
  const exposure = Math.round(totalCVSS / (VULN_DB.length*10) * 100);
  const bar = document.getElementById('vuln-exposure-bar');
  const scoreEl = document.getElementById('vuln-exposure-score');
  if (bar) setTimeout(()=>{ bar.style.width = exposure+'%'; }, 200);
  if (scoreEl) scoreEl.textContent = `Índice ${exposure}/100 — ${exposure>=70?'🔴 Red con exposición CRÍTICA':exposure>=40?'🟠 Exposición SIGNIFICATIVA':'🟢 Exposición controlada'}`;
}

function runVulnScan() {
  const btn = document.getElementById('btn-vuln-scan');
  if (!btn) return;
  btn.disabled = true; btn.textContent = '⏳ Analizando 192.168.80.x...';
  typeof toast !== 'undefined' && toast('🔍 Iniciando análisis de vulnerabilidades...', 'info');
  let progress = 0;
  const iv = setInterval(() => {
    progress += Math.floor(Math.random()*15)+5;
    btn.textContent = `⏳ Analizando... ${Math.min(progress,98)}%`;
    if (progress >= 100) {
      clearInterval(iv);
      btn.textContent = '🔍 Ejecutar Análisis Completo'; btn.disabled = false;
      renderVulnTable();
      typeof toast !== 'undefined' && toast(`✅ Análisis completado: ${VULN_DB.length} vulnerabilidades encontradas`, 'warning');
    }
  }, 350);
}

function exportVulnReport() {
  const lines = ['EINSNET PRO — REPORTE DE VULNERABILIDADES','='.repeat(50),`Fecha: ${new Date().toLocaleString('es-AR')}`,`Red: 192.168.80.x`,'','CVE/TIPO | SEVERIDAD | CVSS | HOSTS | ESTADO','-'.repeat(50),...VULN_DB.map(v=>`${v.cve} | ${v.sev.toUpperCase()} | ${v.cvss} | ${v.hosts.join(',')} | ${v.status}`)];
  const blob = new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download=`EinsNet_Vulns_${Date.now()}.txt`; a.click();
  typeof toast !== 'undefined' && toast('📋 Reporte exportado', 'success');
}

// ── INIT ON DOM READY ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const socRefresh = document.getElementById('btn-soc-refresh');
  if (socRefresh) socRefresh.addEventListener('click', () => { renderSOCTimeline(); renderHeatmap(); renderHealthScores(); updateSOCKPIs(); addFeedEvent(); typeof toast !== 'undefined' && toast('SOC actualizado', 'success'); });
  const vulnScan = document.getElementById('btn-vuln-scan');
  if (vulnScan) vulnScan.addEventListener('click', runVulnScan);
  const vulnExport = document.getElementById('btn-vuln-export');
  if (vulnExport) vulnExport.addEventListener('click', exportVulnReport);
  renderVulnTable();

  // Hook nav buttons for SOC and Vulns
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const v = btn.dataset.view;
      if (v === 'soc')   setTimeout(() => initSOC(), 50);
      if (v === 'vulns') setTimeout(() => renderVulnTable(), 50);
    });
  });
});

window.SOC_MODULE = { initSOC, renderVulnTable, runVulnScan, calcHealthScore, healthColor };

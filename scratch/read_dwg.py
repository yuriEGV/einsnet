import re, sys

def scan_dwg(fname):
    print("=" * 60)
    print("SCANNING:", fname)
    print("=" * 60)
    with open(fname, "rb") as f:
        content = f.read()
    
    # In DWG AC1021, text entities like MTEXT and TEXT store room labels
    matches = re.findall(b"[A-Za-z\xc0-\xff0-9\.\-\_\/\,\: ]{4,}", content)
    unique = []
    seen = set()
    for m in matches:
        try:
            txt = m.decode("latin1").strip()
        except Exception:
            continue
        if len(txt) < 4:
            continue
        if txt in seen:
            continue
        seen.add(txt)
        # Look for architectural labels
        txt_low = txt.lower()
        if any(term in txt_low for term in [
            "sala", "taller", "lab", "oficina", "piso", "patio", "bodega",
            "admin", "ban", "docente", "alumn", "profesor", "lynch", "levarte",
            "modulo", "mod", "aula", "quim", "gastro", "port", "calle", "acc"
        ]):
            unique.append(txt)
            
    for item in sorted(unique):
        print("  ->", repr(item))

scan_dwg("planta_Lynch.dwg")
scan_dwg("Plantas Arq_Mod A-15 Levarte.dwg")

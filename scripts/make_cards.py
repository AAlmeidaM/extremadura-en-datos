# scripts/make_cards.py
# Genera tarjetas PNG (cards) con último valor y variación % del periodo anterior.
# PRIORIDAD: solo "Industria y Empresa"; si no encuentra, usa TODOS los JSON de docs/data.

import json
import math
import os
import re
import unicodedata
from pathlib import Path
from datetime import datetime

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

EXCEL_PATH = "Datos Extremadura Mensual.xlsx"
DOCS_DATA  = Path("docs/data")
CARDS_DIR  = Path("docs/cards")
CARDS_DIR.mkdir(parents=True, exist_ok=True)

def _load_font(size=32):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

FONT_T = _load_font(42)   # título
FONT_V = _load_font(68)   # valor
FONT_S = _load_font(28)   # secundarios

def normalize_period(p):
    if isinstance(p, (pd.Timestamp, datetime)):
        return p.strftime("%Y-%m")
    s = str(p).strip()
    m = re.match(r"^(\d{4})\s*[Mm]\s*(\d{1,2})$", s)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{1,2})[/-](\d{4})$", s)
    if m: return f"{int(m.group(2)):04d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})[/-](\d{1,2})$", s)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m: return f"{m.group(1)}-{m.group(2)}"
    try:
        dt = pd.to_datetime(s, errors="raise", dayfirst=True)
        return dt.strftime("%Y-%m")
    except Exception:
        return s

def to_float(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "na", "none"}:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def pct_change(a, b):
    if b is None or b == 0 or a is None:
        return None
    return (a - b) / b * 100.0

def read_json(table_id):
    """
    Lee docs/data/<id>.json en cualquiera de estos formatos:
    - Lista de registros con period/value o Periodo/Valor o Fecha/Valor
    - Objeto con clave 'Data' (dict)
    - Lista con UN objeto que contiene 'Data' (list[dict])  <-- tu caso
    Convierte Fecha epoch(ms) a 'YYYY-MM', limpia y ordena.
    """
    f = DOCS_DATA / f"{table_id}.json"
    if not f.exists():
        return None

    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] JSON inválido en {f.name}: {e}")
        return None

    # Caso A: lista con dicts "planos"
    if isinstance(data, list) and data and isinstance(data[0], dict) and not data[0].get("Data"):
        out = []
        for d in data:
            per = d.get("period") or d.get("Periodo") or d.get("Fecha")
            val = d.get("value")  or d.get("Valor")
            # epoch(ms) -> YYYY-MM
            if isinstance(per, (int, float)) and per > 10_000_000:
                per = datetime.utcfromtimestamp(float(per)/1000.0).strftime("%Y-%m")
            else:
                per = normalize_period(per)
            val = to_float(val)
            if per and val is not None:
                out.append({"period": per, "value": val})
        out.sort(key=lambda x: x["period"])
        return out

    # Caso B: dict con 'Data'
    if isinstance(data, dict) and "Data" in data and isinstance(data["Data"], list):
        seq = data["Data"]
    # Caso C: lista con un dict que tiene 'Data'  <-- tu ejemplo
    elif isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict) and "Data" in data[0]:
        seq = data[0]["Data"]
    else:
        print(f"[WARN] Estructura no reconocida en {f.name}.")
        return None

    # Normalizar secuencia 'Data'
    out = []
    for it in seq:
        per = it.get("Fecha") or it.get("Periodo") or it.get("period")
        val = it.get("Valor")  or it.get("value")
        if isinstance(per, (int, float)) and per > 10_000_000:
            per = datetime.utcfromtimestamp(float(per)/1000.0).strftime("%Y-%m")
        else:
            per = normalize_period(per)
        val = to_float(val)
        if per and val is not None:
            out.append({"period": per, "value": val})
    out.sort(key=lambda x: x["period"])
    return out


def draw_card(title, last_period, last_value, delta_pct, outfile):
    W, H = 1000, 560
    img = Image.new("RGB", (W, H), (247, 249, 252))
    d = ImageDraw.Draw(img)
    margin = 24
    d.rounded_rectangle([margin, margin, W - margin, H - margin],
                        radius=24, fill="white", outline=(225,230,236), width=2)
    d.text((margin + 32, margin + 24), title[:70], font=FONT_T, fill=(30,41,59))

    val_text = f"{last_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    d.text((margin + 32, margin + 120), val_text, font=FONT_V, fill=(9,105,218))

    d.text((margin + 32, margin + 210), f"Periodo: {last_period}", font=FONT_S, fill=(71,85,105))

    if delta_pct is not None:
        color = (16,185,129) if delta_pct >= 0 else (239,68,68)
        signo = "▲" if delta_pct >= 0 else "▼"
        delta_text = f"{signo} {delta_pct:.2f}% vs periodo anterior"
    else:
        color = (148,163,184)
        delta_text = "s/d (sin dato anterior)"
    d.text((margin + 32, margin + 270), delta_text, font=FONT_S, fill=color)

    d.text((margin + 32, H - margin - 36),
           "Extremadura en Datos · Industria y Empresa",
           font=FONT_S, fill=(100,116,139))
    img.save(outfile, "PNG")

def normalize_text(s):
    s = str(s or "")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.lower().strip()

def ids_from_excel(excel_path):
    if not Path(excel_path).exists():
        print(f"[WARN] Excel no encontrado: {excel_path}. Se usará fallback por JSON.")
        return []
    df = pd.read_excel(excel_path, header=2)
    def extrae_id(u):
        if not isinstance(u, str): return ""
        m = re.search(r"t=(\d+)", u)
        return m.group(1) if m else ""
    df["table_id"] = df["URL"].apply(extrae_id)
    df = df[df["table_id"].astype(bool)]

    # Filtrado robusto por categoría ("industria" en cualquier parte)
    cat = df["Categoría"].apply(normalize_text)
    mask = cat.str.contains(r"\bindustria\b|\bempresa\b", regex=True)
    df_ie = df.loc[mask, ["table_id", "Métricas"]].drop_duplicates()
    ids = [(str(r["table_id"]), str(r["Métricas"])) for _, r in df_ie.iterrows()]
    print(f"[INFO] IDs Industria y Empresa encontrados en Excel: {len(ids)}")
    if len(ids) < 1:
        print("[WARN] Excel sin coincidencias. Se usará fallback: todos los JSON presentes en docs/data/")
    return ids

def fallback_ids_from_json():
    ids = []
    for f in sorted(DOCS_DATA.glob("*.json")):
        ids.append((f.stem, f"Tabla {f.stem}"))
    print(f"[INFO] Fallback por JSON: {len(ids)} ids")
    return ids

def main():
    ids = ids_from_excel(EXCEL_PATH)
    if not ids:
        ids = fallback_ids_from_json()

    generadas = 0
    for tid, title in ids:
        data = read_json_records(tid)
        if not data:
            print(f"[WARN] No hay datos en docs/data/{tid}.json. Se omite.")
            continue
        last = data[-1]
        prev = data[-2] if len(data) >= 2 else None
        last_val = to_float(last.get("value"))
        prev_val = to_float(prev.get("value")) if prev else None
        if last_val is None:
            print(f"[WARN] Último valor no numérico para {tid}. Se omite.")
            continue
        delta = pct_change(last_val, prev_val)

        outfile = CARDS_DIR / f"{tid}.png"
        draw_card(title or f"Tabla {tid}", last.get("period"), last_val, delta, outfile)
        print(f"[OK] Generada tarjeta {outfile.name}")
        generadas += 1

    # Generar index con las tarjetas (si hay)
    index_path = Path("docs/index.html")
    if generadas:
        items = []
        for f in sorted(CARDS_DIR.glob("*.png")):
            items.append(f'<div class="card"><img src="./cards/{f.name}" alt="{f.stem}"><div class="t">{f.stem}</div></div>')
        html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Extremadura en Datos · Industria y Empresa</title>
<style>
body{{font-family:system-ui,Arial;margin:24px;background:#f7f9fc;color:#111}}
h1{{margin:0 0 8px 0}} p{{margin:4px 0 16px 0;color:#475569}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:16px;box-shadow:0 1px 3px rgba(0,0,0,.04);overflow:hidden}}
.card img{{width:100%;display:block}}
.t{{padding:10px 12px;color:#475569}}
</style>
</head>
<body>
<h1>Industria y Empresa</h1>
<p>Último valor y variación % vs periodo anterior (tarjetas generadas automáticamente).</p>
<div class="grid">
{''.join(items)}
</div>
</body></html>"""
        index_path.write_text(html, encoding="utf-8")
        print(f"[OK] Index generado con {generadas} tarjetas.")
    else:
        print("[WARN] No se generaron tarjetas.")

if __name__ == "__main__":
    main()

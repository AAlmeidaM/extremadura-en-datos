# scripts/make_cards.py
# Genera tarjetas PNG (cards) por indicador SOLO de la categoría "Industria y Empresa"
# usando los JSON ya generados en docs/data/<id>.json y los metadatos del Excel.

import json
import math
import os
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# === Configuración básica ===
EXCEL_PATH = "Datos Extremadura Mensual.xlsx"  # mismo que usa el workflow
DOCS_DATA = Path("docs/data")
OUT_DIR   = Path("docs/cards")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Fuentes: usaremos las fuentes por defecto del sistema del runner
# Si no encuentra TTF, PIL usa una básica. Puedes cambiar por fuentes propias si quieres.
def _load_font(size=32):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

FONT_T = _load_font(42)   # título
FONT_V = _load_font(68)   # valor
FONT_S = _load_font(28)   # secundarios

# === Utilidades ===
def normalize_period(p):
    """Devuelve 'YYYY-MM' a partir de formatos varios."""
    if isinstance(p, (pd.Timestamp, datetime)):
        return p.strftime("%Y-%m")
    s = str(p).strip()
    m = re.match(r"^(\d{4})\s*[Mm]\s*(\d{1,2})$", s)           # 2024M01
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{1,2})[/-](\d{4})$", s)                 # 01/2024
    if m: return f"{int(m.group(2)):04d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})[/-](\d{1,2})$", s)                 # 2024/01
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)              # 2024-01-31
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
    # quita miles y cambia coma a punto
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def pct_change(a, b):
    """(a - b) / b * 100 en %, con control de cero."""
    if b is None or b == 0 or a is None:
        return None
    return (a - b) / b * 100.0

def read_json_records(table_id):
    f = DOCS_DATA / f"{table_id}.json"
    if not f.exists():
        return None
    with open(f, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Normalizamos un poco por si acaso
    for d in data:
        d["period"] = normalize_period(d.get("period"))
        d["value"]  = to_float(d.get("value"))
    # quitamos nulos
    data = [d for d in data if d.get("value") is not None and d.get("period")]
    # orden por periodo
    data.sort(key=lambda x: x["period"])
    return data

# === Generador de tarjeta ===
def draw_card(title, last_period, last_value, delta_pct, outfile):
    W, H = 1000, 560
    card = Image.new("RGB", (W, H), (247, 249, 252))  # fondo suave
    draw = ImageDraw.Draw(card)

    # tarjeta con borde
    margin = 24
    draw.rounded_rectangle([margin, margin, W - margin, H - margin], radius=24, fill="white", outline=(225, 230, 236), width=2)

    # título
    draw.text((margin + 32, margin + 24), title, font=FONT_T, fill=(30, 41, 59))

    # valor principal
    val_text = f"{last_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # formateo con coma decimal
    draw.text((margin + 32, margin + 120), val_text, font=FONT_V, fill=(9, 105, 218))

    # periodo
    draw.text((margin + 32, margin + 210), f"Periodo: {last_period}", font=FONT_S, fill=(71, 85, 105))

    # delta
    if delta_pct is not None:
        color = (16, 185, 129) if delta_pct >= 0 else (239, 68, 68)  # verde/rojo
        signo = "▲" if delta_pct >= 0 else "▼"
        delta_text = f"{signo} {delta_pct:.2f}% vs periodo anterior"
    else:
        color = (148, 163, 184)
        delta_text = "s/d (sin dato anterior)"
    draw.text((margin + 32, margin + 270), delta_text, font=FONT_S, fill=color)

    # pie
    draw.text((margin + 32, H - margin - 36), "Extremadura en Datos · Industria y Empresa", font=FONT_S, fill=(100, 116, 139))

    card.save(outfile, "PNG")

def main():
    # 1) Leer Excel y quedarnos con INDUSTRIA Y EMPRESA
    df = pd.read_excel(EXCEL_PATH, header=2)
    def extract_id(u: str) -> str:
        if not isinstance(u, str): return ""
        m = re.search(r"t=(\d+)", u)
        return m.group(1) if m else ""
    df["table_id"] = df["URL"].apply(extract_id)

    # Filtrar categoría (ajusta el texto exacto si en tu Excel está con otras mayúsculas/acentos)
    mask = df["Categoría"].astype(str).str.strip().str.lower().eq("industria y empresa")
    df_ie = df.loc[mask & df["table_id"].astype(bool), ["table_id", "Métricas"]].drop_duplicates()

    generated = 0
    for _, row in df_ie.iterrows():
        tid = str(row["table_id"])
        title = str(row["Métricas"]).strip() or f"Tabla {tid}"
        data = read_json_records(tid)
        if not data or len(data) == 0:
            continue
        last = data[-1]
        prev = data[-2] if len(data) >= 2 else None
        last_val = to_float(last.get("value"))
        prev_val = to_float(prev.get("value")) if prev else None
        delta = pct_change(last_val, prev_val)

        out = OUT_DIR / f"{tid}.png"
        draw_card(title, last.get("period"), last_val, delta, out)
        generated += 1

    # índice simple con las tarjetas
    index_path = Path("docs/index.html")
    items = []
    for img in sorted(OUT_DIR.glob("*.png")):
        items.append(f'<div class="card"><img src="./cards/{img.name}" alt="{img.stem}"><div class="t">{img.stem}</div></div>')
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
{''.join(items) if items else '<p>No se generaron tarjetas (¿faltan JSON en docs/data o no hay tablas de esa categoría?).</p>'}
</div>
</body></html>"""
    index_path.write_text(html, encoding="utf-8")
    print(f"[OK] Generadas {generated} tarjetas en {OUT_DIR}")
    if generated == 0:
        print("[WARN] No se generaron tarjetas. Revise que existan docs/data/<id>.json y que la categoría en el Excel sea exactamente 'Industria y Empresa'.")

if __name__ == "__main__":
    main()

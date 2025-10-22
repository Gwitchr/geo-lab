#!/usr/bin/env python3
"""Synthetic property-listing generator for geo-lab.

Generates ~100,000 realistic-looking Mexican property listings, split across
3-4 raw CSV files under ``data/raw/`` as if pulled from different listing
sites, each with its own flavor of real-world messiness for
``pipeline/clean.py`` to fix (currency-formatted prices, a latin-1-encoded
export, broken/missing fields, stray whitespace).

Determinism: everything is driven by a single ``random.Random(SEED)``
instance in a fixed call order, and no wall-clock time or filesystem
iteration order is ever used for anything that affects output. Re-running
this script produces byte-identical CSVs (see ``pipeline/tests`` for a
regression test, and the "rerun byte-identical" section of
``HANDOFF-pipeline.md`` for the verification transcript).

Run: ``python3 data/gen/gen_listings.py`` (from anywhere -- paths are
resolved relative to this file, not the current working directory).
"""
from __future__ import annotations

import csv
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gazetteer import CDMX_COLONIAS, GDL_MUNICIPIOS, MTY_MUNICIPIOS  # noqa: E402

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
GEN_DIR = Path(__file__).resolve().parent
DATA_DIR = GEN_DIR.parent
GEO_DIR = DATA_DIR / "geo"
RAW_DIR = DATA_DIR / "raw"
AGEBS_PATH = GEO_DIR / "agebs_cdmx.geojson"
MARGINACION_PATH = GEO_DIR / "marginacion_cdmx.csv"

# --------------------------------------------------------------------------
# Determinism knobs
# --------------------------------------------------------------------------
SEED = 20260101
GOOD_TOTAL = 100_000          # semantically valid listings (brief target: ~100k)
DUP_FRACTION = 0.025          # 2.5% near-duplicate re-listings, within the 2-3% brief
BROKEN_EXTRA = 750            # extra intentionally-malformed rows for clean.py to drop
ANCHOR_DATE = date(2024, 1, 1)
DATE_WINDOW_DAYS = 920

DUP_COUNT = round(GOOD_TOTAL * DUP_FRACTION)
PRIMARY_COUNT = GOOD_TOTAL - DUP_COUNT

TYPES = ["casa", "departamento", "terreno", "local"]
TYPE_WEIGHTS = [0.38, 0.42, 0.12, 0.08]
TYPE_PRICE_MULT = {"casa": 1.00, "departamento": 1.08, "terreno": 0.50, "local": 0.85}
TYPE_M2_PARAMS = {
    # (log-mean target m2, sigma, min, max)
    "casa": (140.0, 0.35, 45, 600),
    "departamento": (78.0, 0.32, 28, 280),
    "terreno": (220.0, 0.55, 60, 4000),
    "local": (65.0, 0.50, 18, 500),
}
BEDROOM_CHOICES = {
    "casa": ([1, 2, 3, 4, 5], [0.03, 0.12, 0.45, 0.30, 0.10]),
    "departamento": ([0, 1, 2, 3, 4], [0.05, 0.20, 0.45, 0.25, 0.05]),
}

SOURCES = ["vivanuncios", "inmuebles24", "metroscubicos", "lamudi"]
SOURCE_WEIGHTS = [0.30, 0.26, 0.24, 0.20]

CITY_SHARES = [("cdmx", 0.50), ("gdl", 0.27), ("mty", 0.23)]

# Rough base price per m2 (MXN) for Guadalajara/Monterrey municipios. These
# are approximate assumptions (not a cited dataset), used only to give the
# synthetic price distribution a realistic per-municipio spread; see
# gazetteer.py / docs/data-notes.md.
GDL_PRICE_BASE = {
    "Guadalajara": 22000, "Zapopan": 26000, "San Pedro Tlaquepaque": 14000,
    "Tonalá": 11000, "Tlajomulco de Zúñiga": 13000,
}
MTY_PRICE_BASE = {
    "Monterrey": 24000, "Guadalupe": 13000, "San Nicolás de los Garza": 14000,
    "Apodaca": 12000, "San Pedro Garza García": 48000, "Santa Catarina": 15000,
    "General Escobedo": 11000,
}

# --------------------------------------------------------------------------
# Text generation building blocks (Spanish, deliberately noisy)
# --------------------------------------------------------------------------
OPENERS = [
    "Excelente {type} en {colonia}, {municipio}.",
    "Se vende {type} en {colonia}.",
    "Hermoso {type} ubicado en {colonia}, {municipio}.",
    "Oportunidad unica: {type} en {colonia}.",
    "Vendo {type} en muy buena ubicacion, {colonia}.",
    "{type_cap} en venta, colonia {colonia}, {municipio}.",
]
FEATURE_TEMPLATES_WITH_ROOMS = [
    "Cuenta con {m2} m2 de construccion y {bedrooms} recamaras.",
    "{m2} m2, {bedrooms} recamaras, muy iluminado.",
    "Superficie de {m2} m2 con {bedrooms} recamaras amplias.",
]
FEATURE_TEMPLATES_NO_ROOMS = [
    "Cuenta con {m2} m2 de superficie.",
    "Terreno/local de {m2} m2, listo para escriturar.",
    "{m2} m2 en total, buena ubicacion.",
]
AMENITIES = [
    "cocina integral", "closets en todas las recamaras", "dos banos completos",
    "estacionamiento techado", "vigilancia 24 horas", "alberca", "roof garden",
    "area de lavado", "jardin privado", "bodega", "elevador", "gimnasio",
    "salon de fiestas", "cisterna y tinaco", "cerca del metro",
    "cerca de escuelas", "zona comercial cercana", "amplia sala", "terraza",
    "cuarto de servicio", "cochera para dos autos", "excelente vista",
]
CLOSERS = [
    "Acepto credito infonavit.", "Trato directo con propietario.",
    "Excelente plusvalia en la zona.", "A unos pasos del transporte publico.",
    "Ideal para inversion.", "Contactame para mas informacion.",
    "Solo interesados, favor de llamar.", "Precio de contado o credito bancario.",
    "No intermediarios.", "Papeles en regla, escrituras al dia.",
]
URGENCY_PHRASES = ["URGE VENDER", "URGE VENTA", "SE VENDE RAPIDO", "PRECIO NEGOCIABLE POR URGENCIA"]

SYNONYM_SWAPS = [
    ("Excelente", "Bonito"), ("Hermoso", "Precioso"), ("venta", "remate"),
    ("Cuenta con", "Tiene"), ("iluminado", "ventilado"), ("amplia", "espaciosa"),
    ("Ideal", "Perfecto"), ("buena", "excelente"), ("Vendo", "Se vende"),
]


def _typo(word: str, rng: random.Random) -> str:
    if len(word) < 4:
        return word
    kind = rng.randrange(3)
    i = rng.randrange(1, len(word) - 1)
    if kind == 0:
        return word[:i] + word[i + 1:]  # drop a letter
    if kind == 1:
        return word[:i] + word[i] + word[i:]  # double a letter
    swapped = list(word)
    swapped[i], swapped[i - 1] = swapped[i - 1], swapped[i]
    return "".join(swapped)


def make_description(type_, colonia, municipio, m2, bedrooms, rng: random.Random) -> str:
    opener = rng.choice(OPENERS).format(
        type=type_, type_cap=type_.capitalize(), colonia=colonia, municipio=municipio
    )
    if type_ in ("casa", "departamento") and bedrooms:
        feature = rng.choice(FEATURE_TEMPLATES_WITH_ROOMS).format(m2=m2, bedrooms=bedrooms)
    else:
        feature = rng.choice(FEATURE_TEMPLATES_NO_ROOMS).format(m2=m2)
    n_amenities = rng.randint(1, 4)
    amenities = ", ".join(rng.sample(AMENITIES, n_amenities))
    amenities_sentence = f"Incluye {amenities}."
    closer = rng.choice(CLOSERS)

    parts = [opener, feature, amenities_sentence, closer]

    if rng.random() < 0.18:
        parts.insert(rng.randrange(len(parts) + 1), rng.choice(URGENCY_PHRASES) + "!")

    if rng.random() < 0.15:
        idx = rng.randrange(len(parts))
        parts[idx] = parts[idx].upper()

    if rng.random() < 0.30:
        idx = rng.randrange(len(parts))
        words = parts[idx].split(" ")
        if words:
            j = rng.randrange(len(words))
            words[j] = _typo(words[j], rng)
            parts[idx] = " ".join(words)

    # occasionally vary length: drop the closer, or add a second amenity sentence
    if rng.random() < 0.20 and len(parts) > 2:
        parts.pop(-1)
    elif rng.random() < 0.15:
        extra = ", ".join(rng.sample(AMENITIES, rng.randint(1, 2)))
        parts.append(f"Tambien cuenta con {extra}.")

    return " ".join(p for p in parts if p)


def reword_description(original: str, rng: random.Random) -> str:
    """Produce a near-duplicate description: same facts, different wording."""
    text = original
    for old, new in rng.sample(SYNONYM_SWAPS, min(2, len(SYNONYM_SWAPS))):
        if rng.random() < 0.6:
            text = text.replace(old, new, 1)
    if rng.random() < 0.5:
        text = text + " " + rng.choice(CLOSERS)
    if rng.random() < 0.3:
        words = text.split(" ")
        if len(words) > 3:
            j = rng.randrange(len(words))
            words[j] = _typo(words[j], rng)
            text = " ".join(words)
    if rng.random() < 0.2:
        text = rng.choice(URGENCY_PHRASES) + "! " + text
    return text


def make_title(type_, colonia, m2, bedrooms, rng: random.Random) -> str:
    if bedrooms:
        title = f"{type_.capitalize()} en {colonia}, {bedrooms} rec, {m2} m2"
    else:
        title = f"{type_.capitalize()} en {colonia}, {m2} m2"
    if rng.random() < 0.10:
        title = rng.choice(URGENCY_PHRASES) + " - " + title
    if rng.random() < 0.08:
        title = title.upper()
    return title


# --------------------------------------------------------------------------
# Geometry helpers (self-contained; gen_listings.py does not depend on the
# fastgeo chokepoint, which belongs to pipeline/)
# --------------------------------------------------------------------------
def point_in_ring(x: float, y: float, ring) -> bool:
    inside = False
    n = len(ring)
    x1, y1 = ring[-1]
    for i in range(n):
        x2, y2 = ring[i]
        if (y1 > y) != (y2 > y):
            x_at_y = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_at_y:
                inside = not inside
        x1, y1 = x2, y2
    return inside


def ring_bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def sample_point_in_polygon(ring, bbox, rng: random.Random, max_attempts: int = 30):
    minx, miny, maxx, maxy = bbox
    for _ in range(max_attempts):
        x = rng.uniform(minx, maxx)
        y = rng.uniform(miny, maxy)
        if point_in_ring(x, y, ring):
            return (y, x)  # (lat, lng)
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    return (cy, cx)


# --------------------------------------------------------------------------
# Context builders (CDMX polygons + real municipio names + marginacion-based
# price weighting; GDL/MTY curated gazetteer)
# --------------------------------------------------------------------------
def build_cdmx_context():
    with open(AGEBS_PATH, encoding="utf-8") as f:
        gj = json.load(f)

    polys_by_mun: dict[str, list[dict]] = {}
    for feat in gj["features"]:
        mun = feat["properties"]["NOM_MUN"]
        ring = feat["geometry"]["coordinates"][0]  # [(lng, lat), ...]; no holes in this dataset
        polys_by_mun.setdefault(mun, []).append({"ring": ring, "bbox": ring_bbox(ring)})

    norm_sum: dict[str, float] = {}
    norm_n: dict[str, int] = {}
    pop_sum: dict[str, int] = {}
    with open(MARGINACION_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mun = row["municipio"]
            norm_sum[mun] = norm_sum.get(mun, 0.0) + float(row["index_normalized"])
            norm_n[mun] = norm_n.get(mun, 0) + 1
            pop_sum[mun] = pop_sum.get(mun, 0) + int(row["population"])

    avg_norm = {m: norm_sum[m] / norm_n[m] for m in norm_sum}
    lo, hi = min(avg_norm.values()), max(avg_norm.values())
    spread = hi - lo or 1.0

    municipios = []
    for mun, polys in sorted(polys_by_mun.items()):
        colonias = CDMX_COLONIAS.get(mun)
        if not colonias:
            continue
        rank = (avg_norm.get(mun, lo) - lo) / spread  # 0 = most marginalized, 1 = least
        price_base = 9000 + (rank ** 1.5) * 46000
        municipios.append({
            "name": mun,
            "colonias": colonias,
            "polygons": polys,
            "weight": float(pop_sum.get(mun, 1)),
            "price_base": price_base,
            "bbox": None,
        })
    return {"estado": "Ciudad de México", "municipios": municipios}


def build_gdl_context():
    municipios = []
    for name, info in GDL_MUNICIPIOS.items():
        municipios.append({
            "name": name,
            "colonias": info["colonias"],
            "polygons": None,
            "weight": info["weight"],
            "price_base": GDL_PRICE_BASE[name],
            "bbox": info["bbox"],  # (min_lat, min_lng, max_lat, max_lng)
        })
    return {"estado": "Jalisco", "municipios": municipios}


def build_mty_context():
    municipios = []
    for name, info in MTY_MUNICIPIOS.items():
        municipios.append({
            "name": name,
            "colonias": info["colonias"],
            "polygons": None,
            "weight": info["weight"],
            "price_base": MTY_PRICE_BASE[name],
            "bbox": info["bbox"],
        })
    return {"estado": "Nuevo León", "municipios": municipios}


# --------------------------------------------------------------------------
# Row generation
# --------------------------------------------------------------------------
def pick_municipio(city_ctx, rng: random.Random):
    munis = city_ctx["municipios"]
    weights = [m["weight"] for m in munis]
    return rng.choices(munis, weights=weights, k=1)[0]


def pick_coords(muni, rng: random.Random):
    if muni["polygons"]:
        poly = rng.choice(muni["polygons"])
        return sample_point_in_polygon(poly["ring"], poly["bbox"], rng)
    min_lat, min_lng, max_lat, max_lng = muni["bbox"]
    return (rng.uniform(min_lat, max_lat), rng.uniform(min_lng, max_lng))


def make_primary_row(row_id: str, city_ctx, rng: random.Random) -> dict:
    muni = pick_municipio(city_ctx, rng)
    colonia = rng.choice(muni["colonias"])
    lat, lng = pick_coords(muni, rng)

    type_ = rng.choices(TYPES, weights=TYPE_WEIGHTS, k=1)[0]
    log_mean_m2, sigma, m2_min, m2_max = TYPE_M2_PARAMS[type_]
    import math
    m2 = rng.lognormvariate(math.log(log_mean_m2), sigma)
    m2 = int(round(min(max(m2, m2_min), m2_max)))

    if type_ in BEDROOM_CHOICES:
        choices, weights = BEDROOM_CHOICES[type_]
        bedrooms = rng.choices(choices, weights=weights, k=1)[0]
    else:
        bedrooms = 0

    price_raw = m2 * muni["price_base"] * TYPE_PRICE_MULT[type_] * rng.lognormvariate(0, 0.20)
    price_mxn = int(round(price_raw / 500.0)) * 500
    price_mxn = min(max(price_mxn, 120_000), 80_000_000)

    offset = rng.randint(0, DATE_WINDOW_DAYS)
    listed_date = (ANCHOR_DATE + timedelta(days=offset)).isoformat()

    description = make_description(type_, colonia, muni["name"], m2, bedrooms, rng)
    title = make_title(type_, colonia, m2, bedrooms, rng)
    source = rng.choices(SOURCES, weights=SOURCE_WEIGHTS, k=1)[0]

    return {
        "id": row_id, "title": title, "description": description,
        "price_mxn": price_mxn, "m2": m2, "bedrooms": bedrooms, "type": type_,
        "colonia": colonia, "municipio": muni["name"], "estado": city_ctx["estado"],
        "lat": round(lat, 6), "lng": round(lng, 6), "listed_date": listed_date,
        "source": source,
    }


def make_duplicate_row(row_id: str, original: dict, rng: random.Random) -> dict:
    lat = round(original["lat"] + rng.uniform(-0.0006, 0.0006), 6)
    lng = round(original["lng"] + rng.uniform(-0.0006, 0.0006), 6)
    m2 = original["m2"] + rng.randint(-2, 2)
    price_mxn = int(round(original["price_mxn"] * rng.uniform(0.92, 1.08) / 500.0)) * 500
    orig_date = date.fromisoformat(original["listed_date"])
    new_date = orig_date + timedelta(days=rng.randint(3, 180))
    max_date = ANCHOR_DATE + timedelta(days=DATE_WINDOW_DAYS)
    if new_date > max_date:
        new_date = max_date
    description = reword_description(original["description"], rng)
    title = make_title(original["type"], original["colonia"], m2, original["bedrooms"], rng)
    source = rng.choices(SOURCES, weights=SOURCE_WEIGHTS, k=1)[0]

    return {
        "id": row_id, "title": title, "description": description,
        "price_mxn": price_mxn, "m2": m2, "bedrooms": original["bedrooms"],
        "type": original["type"], "colonia": original["colonia"],
        "municipio": original["municipio"], "estado": original["estado"],
        "lat": lat, "lng": lng, "listed_date": new_date.isoformat(),
        "source": source,
    }


def make_broken_row(row_id: str, rng: random.Random, good_pool: list[dict]) -> dict:
    """A deliberately malformed row for clean.py to catch and drop."""
    base = dict(rng.choice(good_pool))
    base["id"] = row_id
    kind = rng.randrange(5)
    if kind == 0:
        base["price_mxn"] = "N/D"
    elif kind == 1:
        base["m2"] = -1
    elif kind == 2:
        base["type"] = "oficina"  # not in the casa|departamento|terreno|local enum
    elif kind == 3:
        base["colonia"] = ""
    else:
        base["price_mxn"] = ""
    return base


# --------------------------------------------------------------------------
# Raw-CSV "messiness" per source, applied only to the on-disk representation
# --------------------------------------------------------------------------
FIELDNAMES = [
    "id", "title", "description", "price_mxn", "m2", "bedrooms", "type",
    "colonia", "municipio", "estado", "lat", "lng", "listed_date", "source",
]


def format_for_source(row: dict, rng: random.Random) -> dict:
    out = dict(row)
    source = row["source"]
    if source == "inmuebles24":
        if isinstance(out["price_mxn"], int):
            out["price_mxn"] = f"${out['price_mxn']:,}"
        out["title"] = "  " + out["title"] + "  "
        out["colonia"] = out["colonia"] + "  "
    elif source == "metroscubicos":
        caser = rng.choice([str.upper, str.lower, str.title])
        out["type"] = caser(out["type"])
    return out


def write_source_csv(path: Path, rows: list[dict], source: str, rng: random.Random):
    with open(path, "w", newline="", encoding="latin-1" if source == "metroscubicos" else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(format_for_source(row, rng))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def generate(
    out_dir: Path = RAW_DIR,
    primary_count: int = PRIMARY_COUNT,
    dup_count: int = DUP_COUNT,
    broken_extra: int = BROKEN_EXTRA,
    verbose: bool = True,
) -> dict:
    """Generate the full raw-CSV set. Parameterized (out_dir + counts) so
    pipeline/tests/test_gen_listings.py can exercise this at a small scale
    without regenerating the full ~100k-row dataset; the CLI entry point
    below always uses the real ~100k-row defaults."""
    rng = random.Random(SEED)

    cdmx_ctx = build_cdmx_context()
    gdl_ctx = build_gdl_context()
    mty_ctx = build_mty_context()
    city_ctxs = {"cdmx": cdmx_ctx, "gdl": gdl_ctx, "mty": mty_ctx}
    city_names = [c[0] for c in CITY_SHARES]
    city_weights = [c[1] for c in CITY_SHARES]

    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"LST{counter:07d}"

    primaries: list[dict] = []
    for _ in range(primary_count):
        city = rng.choices(city_names, weights=city_weights, k=1)[0]
        row = make_primary_row(next_id(), city_ctxs[city], rng)
        primaries.append(row)

    duplicates: list[dict] = []
    for _ in range(dup_count):
        original = rng.choice(primaries)
        duplicates.append(make_duplicate_row(next_id(), original, rng))

    broken: list[dict] = []
    good_pool_sample = primaries[: min(2000, len(primaries))]
    for _ in range(broken_extra):
        broken.append(make_broken_row(next_id(), rng, good_pool_sample))

    by_source: dict[str, list[dict]] = {s: [] for s in SOURCES}
    for row in primaries:
        by_source[row["source"]].append(row)
    for row in duplicates:
        by_source[row["source"]].append(row)
    # broken rows: spread mostly into lamudi (weakest-QA source), some elsewhere
    for i, row in enumerate(broken):
        target = "lamudi" if i % 4 != 0 else rng.choices(SOURCES, weights=SOURCE_WEIGHTS, k=1)[0]
        row["source"] = target
        by_source[target].append(row)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_written = 0
    written_paths = {}
    for source in SOURCES:
        rows = by_source[source]
        out_path = out_dir / f"listings_{source}.csv"
        write_source_csv(out_path, rows, source, rng)
        written_paths[source] = out_path
        total_written += len(rows)
        if verbose:
            print(f"wrote {out_path}: {len(rows)} rows")

    if verbose:
        print(f"total physical rows: {total_written} "
              f"(primaries={len(primaries)} duplicates={len(duplicates)} broken={len(broken)})")

    return {
        "paths": written_paths,
        "total": total_written,
        "primaries": len(primaries),
        "duplicates": len(duplicates),
        "broken": len(broken),
    }


if __name__ == "__main__":
    generate()

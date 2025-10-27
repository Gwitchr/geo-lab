#!/usr/bin/env python3
"""Normalize prices, drop broken rows, fix encodings.

Reads the raw source CSVs (``data/raw/listings_*.csv``, produced by
``data/gen/gen_listings.py``) and turns each row into a well-typed dict or
drops it with a reason. Each raw source has its own flavor of real-world
messiness this module is responsible for:

- ``inmuebles24``: ``price_mxn`` written as ``"$1,234,567"``; stray padding
  whitespace on text fields.
- ``metroscubicos``: the whole CSV file is latin-1 encoded instead of utf-8;
  ``type`` values arrive in random casing.
- ``lamudi``: a small fraction of rows are genuinely broken (missing price,
  non-positive m2, an out-of-enum ``type``, empty ``colonia``) and must be
  dropped, not silently coerced.

``clean_row`` is the single-row unit this all reduces to; ``clean_all`` walks
every ``data/raw/listings_*.csv`` file and aggregates the results plus a
per-reason drop count, which ``pipeline/ingest.py`` reports and this module's
own ``__main__`` prints as a standalone diagnostic (``python pipeline/clean.py``).
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
RAW_DIR = ROOT / "data" / "raw"

VALID_TYPES = {"casa", "departamento", "terreno", "local"}
# Generous bounding box covering all of Mexico's territory, used only as a
# sanity check that lat/lng survived the round trip -- not a tight fit.
LAT_RANGE = (14.0, 33.0)
LNG_RANGE = (-118.5, -86.0)

FIELDNAMES = [
    "id", "title", "description", "price_mxn", "m2", "bedrooms", "type",
    "colonia", "municipio", "estado", "lat", "lng", "listed_date", "source",
]


def parse_price(raw) -> int | None:
    """Parse a price field that may be a plain int or a "$1,234,567" string."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("$", "").replace(",", "").strip()
    try:
        value = int(round(float(text)))
    except ValueError:
        return None
    return value if value > 0 else None


def parse_int_field(raw, allow_blank_zero: bool = False) -> int | None:
    text = str(raw).strip() if raw is not None else ""
    if not text:
        return 0 if allow_blank_zero else None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def clean_row(raw: dict) -> tuple[dict | None, str | None]:
    """Validate + normalize one raw CSV row.

    Returns ``(cleaned_row, None)`` on success or ``(None, reason)`` when the
    row should be dropped.
    """
    row_id = (raw.get("id") or "").strip()
    if not row_id:
        return None, "missing_id"

    price = parse_price(raw.get("price_mxn"))
    if price is None:
        return None, "bad_price"

    m2 = parse_int_field(raw.get("m2"))
    if m2 is None or m2 <= 0:
        return None, "bad_m2"

    bedrooms = parse_int_field(raw.get("bedrooms"), allow_blank_zero=True)
    if bedrooms is None or bedrooms < 0:
        return None, "bad_bedrooms"

    type_ = (raw.get("type") or "").strip().lower()
    if type_ not in VALID_TYPES:
        return None, "bad_type"

    colonia = (raw.get("colonia") or "").strip()
    municipio = (raw.get("municipio") or "").strip()
    estado = (raw.get("estado") or "").strip()
    if not colonia or not municipio or not estado:
        return None, "missing_location"

    try:
        lat = float(raw.get("lat"))
        lng = float(raw.get("lng"))
    except (TypeError, ValueError):
        return None, "bad_coords"
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1]) or not (LNG_RANGE[0] <= lng <= LNG_RANGE[1]):
        return None, "bad_coords"

    listed_date = (raw.get("listed_date") or "").strip()
    try:
        date.fromisoformat(listed_date)
    except ValueError:
        return None, "bad_date"

    title = (raw.get("title") or "").strip()
    description = (raw.get("description") or "").strip()
    source = (raw.get("source") or "").strip()

    return {
        "id": row_id,
        "title": title,
        "description": description,
        "price_mxn": price,
        "m2": m2,
        "bedrooms": bedrooms,
        "type": type_,
        "colonia": colonia,
        "municipio": municipio,
        "estado": estado,
        "lat": lat,
        "lng": lng,
        "listed_date": listed_date,
        "source": source,
    }, None


def read_raw_csv(path: Path) -> list[dict]:
    """Read one raw CSV, trying utf-8 first and falling back to latin-1."""
    raw_bytes = path.read_bytes()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")
    return list(csv.DictReader(text.splitlines()))


def clean_all(raw_dir: Path = RAW_DIR) -> tuple[list[dict], dict]:
    """Read + clean every ``listings_*.csv`` in ``raw_dir``.

    Returns ``(rows, stats)`` where ``stats`` has ``read``, ``kept``,
    ``dropped``, and a ``reasons`` dict of drop-reason -> count.
    """
    rows: list[dict] = []
    stats = {"read": 0, "kept": 0, "dropped": 0, "reasons": {}}
    seen_ids: set[str] = set()

    for path in sorted(Path(raw_dir).glob("listings_*.csv")):
        for raw in read_raw_csv(path):
            stats["read"] += 1
            cleaned, reason = clean_row(raw)
            if cleaned is None:
                stats["dropped"] += 1
                stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1
                continue
            if cleaned["id"] in seen_ids:
                stats["dropped"] += 1
                stats["reasons"]["duplicate_id"] = stats["reasons"].get("duplicate_id", 0) + 1
                continue
            seen_ids.add(cleaned["id"])
            stats["kept"] += 1
            rows.append(cleaned)

    return rows, stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    args = parser.parse_args()
    _, run_stats = clean_all(args.raw_dir)
    print(f"read {run_stats['read']} rows")
    print(f"kept {run_stats['kept']} rows")
    print(f"dropped {run_stats['dropped']} rows: {run_stats['reasons']}")

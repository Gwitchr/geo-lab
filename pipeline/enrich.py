#!/usr/bin/env python3
"""Assign CDMX listings to their containing AGEB polygon (see native/).

For every listing with ``estado = 'Ciudad de México'``, finds the AGEB
(``data/geo/agebs_cdmx.geojson``) whose polygon contains its (lat, lng) and
attaches that AGEB's CONAPO marginación grade/index
(``data/geo/marginacion_cdmx.csv``). Writes ``ageb_id``,
``marginacion_grade``, ``marginacion_index`` on the ``listings`` row.

This is exactly the "100k listings x 2.4k polygons" case BRIEF.md calls out
as the reason fastgeo has a C++ path: a naive brute-force point-in-polygon
test against all ~2,431 AGEB polygons for every CDMX listing is minutes of
work in pure Python. Two cheap pre-filters, applied before ever calling
fastgeo.point_in_polygon, make the pure-python fallback practical too:

1. only test polygons belonging to the listing's own ``municipio``
   (already recorded on the row) -- narrows ~2,431 candidates to ~150 on
   average;
2. a plain-Python bounding-box containment check per remaining candidate,
   which eliminates all but a handful of polygons before paying for the
   real (and, on the fallback, much more expensive) point-in-polygon test.

Both fastgeo backends (compiled extension or pure-python fallback, selected
via pipeline/geo_backend.py) go through the same filtered candidate list, so
this is a straightforward point_in_polygon consumer, not a re-implementation
of anything fastgeo owns.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
from geo_backend import fastgeo  # noqa: E402

ROOT = PIPELINE_DIR.parent
DB_PATH = ROOT / "data" / "db.sqlite"
AGEBS_PATH = ROOT / "data" / "geo" / "agebs_cdmx.geojson"
MARGINACION_PATH = ROOT / "data" / "geo" / "marginacion_cdmx.csv"
CDMX_ESTADO = "Ciudad de México"
ASSIGNMENT_TARGET = 0.95


def load_agebs(path: Path = AGEBS_PATH) -> dict[str, list[dict]]:
    """Returns {municipio: [{"id": cvegeo, "ring": [(lat,lng),...], "bbox": (...)}]}."""
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)

    by_mun: dict[str, list[dict]] = {}
    for feat in gj["features"]:
        cvegeo = feat["properties"]["CVEGEO"]
        mun = feat["properties"]["NOM_MUN"]
        ring_lnglat = feat["geometry"]["coordinates"][0]
        ring = [(lat, lng) for lng, lat in ring_lnglat]  # fastgeo wants (lat, lng)
        lats = [p[0] for p in ring]
        lngs = [p[1] for p in ring]
        entry = {
            "id": cvegeo,
            "ring": ring,
            "bbox": (min(lats), min(lngs), max(lats), max(lngs)),
        }
        by_mun.setdefault(mun, []).append(entry)
    return by_mun


def load_marginacion(path: Path = MARGINACION_PATH) -> dict[str, dict]:
    info: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            info[row["ageb_id"]] = {
                "grade": row["grade"],
                "index_value": float(row["index_value"]),
            }
    return info


def assign_ageb(lat: float, lng: float, polygons: list[dict]) -> str | None:
    for poly in polygons:
        min_lat, min_lng, max_lat, max_lng = poly["bbox"]
        if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
            continue
        if fastgeo.point_in_polygon(lat, lng, poly["ring"]):
            return poly["id"]
    return None


def _ensure_columns(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("PRAGMA table_info(listings)")}
    for name, sqltype in (
        ("ageb_id", "TEXT"),
        ("marginacion_grade", "TEXT"),
        ("marginacion_index", "REAL"),
    ):
        if name not in cols:
            con.execute(f"ALTER TABLE listings ADD COLUMN {name} {sqltype}")


def run(db_path: Path = DB_PATH, verbose: bool = True) -> dict:
    by_mun = load_agebs()
    marginacion = load_marginacion()

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    _ensure_columns(con)
    rows = con.execute(
        "SELECT id, lat, lng, municipio FROM listings WHERE estado = ?",
        (CDMX_ESTADO,),
    ).fetchall()

    updates = []
    assigned = 0
    for row in rows:
        polys = by_mun.get(row["municipio"], [])
        ageb_id = assign_ageb(row["lat"], row["lng"], polys)
        marg = marginacion.get(ageb_id) if ageb_id else None
        updates.append((
            ageb_id,
            marg["grade"] if marg else None,
            marg["index_value"] if marg else None,
            row["id"],
        ))
        if ageb_id is not None:
            assigned += 1

    con.executemany(
        "UPDATE listings SET ageb_id = ?, marginacion_grade = ?, marginacion_index = ? WHERE id = ?",
        updates,
    )
    con.commit()
    con.close()

    total = len(rows)
    rate = assigned / total if total else 0.0
    if verbose:
        print(f"CDMX listings: {total}")
        print(f"assigned to an AGEB: {assigned} ({rate:.2%})")
        if rate < ASSIGNMENT_TARGET:
            print(
                f"WARNING: assignment rate {rate:.2%} is below the "
                f"{ASSIGNMENT_TARGET:.0%} acceptance target",
                file=sys.stderr,
            )
    return {"total": total, "assigned": assigned, "rate": rate}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run(args.db)

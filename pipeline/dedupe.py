#!/usr/bin/env python3
"""Near-duplicate re-listing detection (simhash, see native/).

Flags listings that are the same property re-listed with slightly different
wording (see ``data/gen/gen_listings.py``'s ~2.5% near-duplicate injection).
Text similarity alone is not a safe signal here: many descriptions share the
same small template pool (see the generator), so unrelated listings can
collide on simhash by chance. Each candidate pair therefore also has to agree
on municipio, type, m2 (within a small tolerance), and geographic proximity
(haversine, via fastgeo) before it is flagged.

Within a matched cluster the earliest-``listed_date`` row is canonical
(``dup_of = None``); later ones point to it. Nothing is deleted -- this is a
label, not a filter -- so downstream consumers (stats.py, export_web.py)
decide whether to exclude ``dup_of IS NOT NULL`` rows.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
from geo_backend import fastgeo  # noqa: E402

ROOT = PIPELINE_DIR.parent
DB_PATH = ROOT / "data" / "db.sqlite"

# TODO: these are a first guess, not calibrated against anything yet.
HAMMING_THRESHOLD = 12
DISTANCE_THRESHOLD_M = 120.0
M2_TOLERANCE = 2


def _is_match(a: dict, b: dict) -> bool:
    if a["type"] != b["type"] or a["municipio"] != b["municipio"]:
        return False
    if abs(a["m2"] - b["m2"]) > M2_TOLERANCE:
        return False
    if fastgeo.hamming(a["_simhash"], b["_simhash"]) > HAMMING_THRESHOLD:
        return False
    dist = fastgeo.haversine_matrix([(a["lat"], a["lng"])], [(b["lat"], b["lng"])])[0][0]
    return dist <= DISTANCE_THRESHOLD_M


def find_duplicates(rows: list[dict]) -> dict[str, str | None]:
    """rows: dicts with id, description, lat, lng, m2, type, listed_date, municipio.

    Returns ``{id: dup_of_id_or_None}``.

    Buckets by municipio first (matches require the same municipio anyway)
    then compares every pair within a bucket. Fine at small scale; will need
    a tighter spatial bucket if this ever gets slow on the full ~100k run.
    """
    ordered = sorted(rows, key=lambda r: (r["listed_date"], r["id"]))
    for row in ordered:
        row["_simhash"] = fastgeo.simhash64(row["description"] or "")

    buckets: dict[str, list[dict]] = {}
    dup_of: dict[str, str | None] = {}

    for row in ordered:
        bucket = buckets.setdefault(row["municipio"], [])
        canonical_id = None
        for other in bucket:
            if _is_match(row, other):
                canonical_id = other["_canonical_id"]
                break
        row["_canonical_id"] = canonical_id if canonical_id else row["id"]
        dup_of[row["id"]] = canonical_id
        bucket.append(row)

    return dup_of


def run(db_path: Path = DB_PATH, verbose: bool = True) -> dict[str, str | None]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = [
        dict(r)
        for r in con.execute(
            "SELECT id, description, lat, lng, m2, type, listed_date, municipio FROM listings"
        ).fetchall()
    ]
    dup_map = find_duplicates(rows)
    con.executemany(
        "UPDATE listings SET dup_of = ? WHERE id = ?",
        [(v, k) for k, v in dup_map.items()],
    )
    con.commit()
    con.close()

    n_dupes = sum(1 for v in dup_map.values() if v is not None)
    if verbose:
        total = len(dup_map)
        rate = n_dupes / total if total else 0.0
        print(f"listings scanned: {total}")
        print(f"marked as near-duplicate: {n_dupes} ({rate:.2%})")
    return dup_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    run(args.db)

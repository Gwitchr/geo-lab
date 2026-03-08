#!/usr/bin/env python3
"""Near-duplicate re-listing detection (simhash, see native/).

Flags listings that are the same property re-listed with slightly different
wording (see ``data/gen/gen_listings.py``'s ~2.5% near-duplicate injection).
Text similarity alone is not a safe signal here: many descriptions share the
same small template pool (see the generator), so unrelated listings can
collide on simhash by chance. Each candidate pair therefore also has to agree
on municipio, type, m2 (within a small tolerance), and geographic proximity
(haversine, via fastgeo) before it is flagged.

Rows are bucketed into a coarse lat/lng grid first (``GRID_SIZE_DEG``, about
1.1 km per cell -- far coarser than the near-duplicate coordinate jitter the
generator injects) so this stays close to O(n) instead of comparing every
pair, and only the fastgeo chokepoint (pipeline/geo_backend.py) is used for
the actual simhash/hamming/haversine math.

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

# Calibrated against data/gen/gen_listings.py's own near-duplicate generator
# at full ~100k-row scale (see HANDOFF-pipeline.md for the precision/recall
# sweep): the generator's coordinate jitter for a re-listing is at most
# ~0.0006 deg per axis (~94 m worst case diagonal), so DISTANCE_THRESHOLD_M
# has headroom without inviting unrelated-but-nearby listings; hamming <=12
# and m2 tolerance 2 together land at ~96% precision / ~96% recall against
# the known-duplicate set (2492 flagged vs. 2500 true, 94 false positives).
# Looser settings (e.g. hamming<=16, dist<=250) climb recall to ~99% but
# collapse precision to <80% at this scale -- many unrelated listings share
# template phrasing, see module docstring.
HAMMING_THRESHOLD = 12
DISTANCE_THRESHOLD_M = 120.0
M2_TOLERANCE = 2
GRID_SIZE_DEG = 0.01  # ~1.1 km per cell


def _grid_key(lat: float, lng: float) -> tuple[int, int]:
    return (int(lat // GRID_SIZE_DEG), int(lng // GRID_SIZE_DEG))


def _neighbor_keys(key: tuple[int, int]):
    gx, gy = key
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            yield (gx + dx, gy + dy)


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
    """
    ordered = sorted(rows, key=lambda r: (r["listed_date"], r["id"]))
    for row in ordered:
        row["_simhash"] = fastgeo.simhash64(row["description"] or "")

    grid: dict[tuple[int, int], list[dict]] = {}
    dup_of: dict[str, str | None] = {}

    for row in ordered:
        key = _grid_key(row["lat"], row["lng"])
        canonical_id = None
        for nkey in _neighbor_keys(key):
            for other in grid.get(nkey, ()):
                if _is_match(row, other):
                    canonical_id = other["_canonical_id"]
                    break
            if canonical_id:
                break
        row["_canonical_id"] = canonical_id if canonical_id else row["id"]
        dup_of[row["id"]] = canonical_id
        grid.setdefault(key, []).append(row)

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

#!/usr/bin/env python3
"""raw CSVs (data/raw/listings_*.csv) -> data/db.sqlite, table `listings`.

Owns the DB contract every other consumer relies on: a single sqlite file at
``data/db.sqlite`` with one table, ``listings``, in the exact column layout
``cli/`` and ``web/`` were built against (see ``cli/src/__tests__/fixtures/fixtureDb.ts``
and ``cli/src/parser/eval.ts``'s ``FIELD_COLUMNS``). One run of this script:

1. cleans every raw row via ``clean.clean_all`` (drops broken rows, fixes
   price formats/encodings -- see clean.py's docstring),
2. flags near-duplicate re-listings via ``dedupe.find_duplicates`` (label
   only, nothing is dropped),
3. (re)creates ``data/db.sqlite`` from scratch and bulk-inserts the result.

``ageb_id`` / ``marginacion_grade`` / ``marginacion_index`` columns are
created here (NULL) and populated later by ``pipeline/enrich.py`` -- kept in
the base schema instead of an ``ALTER TABLE`` there so the full contract is
visible in one place.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
import clean  # noqa: E402
import dedupe  # noqa: E402

ROOT = PIPELINE_DIR.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "db.sqlite"

SCHEMA = """
CREATE TABLE listings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price_mxn INTEGER NOT NULL,
    m2 INTEGER NOT NULL,
    bedrooms INTEGER NOT NULL,
    type TEXT NOT NULL,
    colonia TEXT NOT NULL,
    municipio TEXT NOT NULL,
    estado TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    listed_date TEXT NOT NULL,
    source TEXT,
    dup_of TEXT,
    ageb_id TEXT,
    marginacion_grade TEXT,
    marginacion_index REAL
);
"""

INDEXES = [
    "CREATE INDEX idx_listings_municipio ON listings(municipio)",
    "CREATE INDEX idx_listings_colonia ON listings(colonia)",
    "CREATE INDEX idx_listings_type ON listings(type)",
    "CREATE INDEX idx_listings_price ON listings(price_mxn)",
    "CREATE INDEX idx_listings_dup_of ON listings(dup_of)",
]

INSERT_SQL = """
INSERT INTO listings
    (id, title, description, price_mxn, m2, bedrooms, type, colonia,
     municipio, estado, lat, lng, listed_date, source, dup_of)
VALUES
    (:id, :title, :description, :price_mxn, :m2, :bedrooms, :type, :colonia,
     :municipio, :estado, :lat, :lng, :listed_date, :source, :dup_of)
"""


def build(raw_dir: Path = RAW_DIR, db_path: Path = DB_PATH, verbose: bool = True) -> dict:
    t0 = time.time()
    rows, clean_stats = clean.clean_all(raw_dir)
    if verbose:
        print(
            f"read {clean_stats['read']} raw rows, kept {clean_stats['kept']}, "
            f"dropped {clean_stats['dropped']} {clean_stats['reasons']}"
        )

    dup_map = dedupe.find_duplicates(rows)
    n_dupes = sum(1 for v in dup_map.values() if v is not None)
    if verbose:
        print(f"flagged {n_dupes} near-duplicate rows")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA)
        con.executemany(
            INSERT_SQL,
            [{**row, "dup_of": dup_map.get(row["id"])} for row in rows],
        )
        for stmt in INDEXES:
            con.execute(stmt)
        con.commit()
    finally:
        con.close()

    elapsed = time.time() - t0
    if verbose:
        print(f"wrote {len(rows)} rows to {db_path} in {elapsed:.1f}s")

    return {
        "rows": len(rows),
        "read": clean_stats["read"],
        "dropped": clean_stats["dropped"],
        "drop_reasons": clean_stats["reasons"],
        "duplicates": n_dupes,
        "seconds": elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    build(args.raw_dir, args.db)

#!/usr/bin/env python3
"""data/db.sqlite -> web/public/listings.json.

JSON array of objects with fields
``id,title,price_mxn,m2,bedrooms,type,colonia,municipio,estado,lat,lng,listed_date``
(per BRIEF.md's pinned interface), capped at 5000 rows, newest-listed first.
Rows flagged as near-duplicates (``dup_of IS NOT NULL``) are excluded so the
web explorer doesn't show the same property twice.

This script is provided for whoever runs the pipeline end to end; per this
agent's task scope it is NOT executed against the real
``web/public/listings.json`` (that file is owned by the web/ agent's area --
see HANDOFF-pipeline.md for how this was verified against a throwaway path
instead).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
DB_PATH = ROOT / "data" / "db.sqlite"
OUT_PATH = ROOT / "web" / "public" / "listings.json"
MAX_ROWS = 5000

FIELDS = [
    "id", "title", "price_mxn", "m2", "bedrooms", "type", "colonia",
    "municipio", "estado", "lat", "lng", "listed_date",
]


def export(db_path: Path = DB_PATH, out_path: Path = OUT_PATH, max_rows: int = MAX_ROWS) -> int:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        f"SELECT {', '.join(FIELDS)} FROM listings "
        "WHERE dup_of IS NULL ORDER BY listed_date DESC LIMIT ?",
        (max_rows,),
    ).fetchall()
    con.close()

    data = [dict(r) for r in rows]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return len(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    parser.add_argument("--max-rows", type=int, default=MAX_ROWS)
    args = parser.parse_args()
    n = export(args.db, args.out, args.max_rows)
    print(f"wrote {n} listings to {args.out}")

#!/usr/bin/env python3
"""data/db.sqlite -> pipeline/stats.json for web/.

Schema (per BRIEF.md's pinned interface)::

    {
      "generated_at": "<ISO 8601 UTC timestamp>",
      "total_listings": <int>,
      "by_colonia": [{"colonia", "municipio", "count", "median_price_per_m2"}, ...],
      "histogram": [{"bucket_max_mxn", "count"}, ...]
    }

Rows flagged as near-duplicates (``dup_of IS NOT NULL``) are excluded from
every aggregate so a re-listed property isn't counted twice. The last
histogram bucket has ``bucket_max_mxn: null``, meaning "everything above the
previous bucket" (an explicit null reads better than a made-up sentinel price).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent
DB_PATH = ROOT / "data" / "db.sqlite"
OUT_PATH = PIPELINE_DIR / "stats.json"

HISTOGRAM_BUCKETS_MXN = [
    500_000, 1_000_000, 1_500_000, 2_000_000, 3_000_000, 4_000_000,
    5_000_000, 7_500_000, 10_000_000, 15_000_000, None,
]


def compute(db_path: Path = DB_PATH) -> dict:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    total = con.execute("SELECT COUNT(*) FROM listings WHERE dup_of IS NULL").fetchone()[0]

    groups = con.execute(
        """
        SELECT colonia, municipio, COUNT(*) AS n
        FROM listings WHERE dup_of IS NULL
        GROUP BY colonia, municipio
        """
    ).fetchall()

    by_colonia = []
    for group in groups:
        price_rows = con.execute(
            "SELECT price_mxn, m2 FROM listings "
            "WHERE dup_of IS NULL AND colonia = ? AND municipio = ? AND m2 > 0",
            (group["colonia"], group["municipio"]),
        ).fetchall()
        ppm2 = [r["price_mxn"] / r["m2"] for r in price_rows]
        if not ppm2:
            continue
        by_colonia.append({
            "colonia": group["colonia"],
            "municipio": group["municipio"],
            "count": group["n"],
            "median_price_per_m2": round(statistics.median(ppm2), 2),
        })
    by_colonia.sort(key=lambda r: (-r["count"], r["colonia"]))

    prices = [r[0] for r in con.execute("SELECT price_mxn FROM listings WHERE dup_of IS NULL")]
    histogram = []
    prev = 0
    for bucket_max in HISTOGRAM_BUCKETS_MXN:
        if bucket_max is None:
            count = sum(1 for p in prices if p > prev)
        else:
            count = sum(1 for p in prices if prev < p <= bucket_max)
            prev = bucket_max
        histogram.append({"bucket_max_mxn": bucket_max, "count": count})

    con.close()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_listings": total,
        "by_colonia": by_colonia,
        "histogram": histogram,
    }


def run(db_path: Path = DB_PATH, out_path: Path = OUT_PATH, verbose: bool = True) -> dict:
    data = compute(db_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if verbose:
        print(
            f"wrote {out_path} ({data['total_listings']} listings, "
            f"{len(data['by_colonia'])} colonias)"
        )
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()
    run(args.db, args.out)

"""Make pipeline/*.py importable regardless of the directory pytest was
invoked from (repo root, pipeline/, or pipeline/tests/)."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

ROOT_DIR = PIPELINE_DIR.parent

# Mirrors ingest.SCHEMA (pipeline/ingest.py). Duplicated here, not imported,
# so tests that only care about the DB shape (stats.py, export_web.py) don't
# have to pull in ingest -> dedupe -> geo_backend -> fastgeo, which may not
# be buildable in every environment this suite runs in.
LISTINGS_SCHEMA = """
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

_INSERT_SQL = """
INSERT INTO listings
    (id, title, description, price_mxn, m2, bedrooms, type, colonia,
     municipio, estado, lat, lng, listed_date, source, dup_of, ageb_id,
     marginacion_grade, marginacion_index)
VALUES
    (:id, :title, :description, :price_mxn, :m2, :bedrooms, :type, :colonia,
     :municipio, :estado, :lat, :lng, :listed_date, :source, :dup_of, :ageb_id,
     :marginacion_grade, :marginacion_index)
"""

_ROW_DEFAULTS = {
    "title": "", "description": "", "bedrooms": 0, "source": None,
    "dup_of": None, "ageb_id": None, "marginacion_grade": None,
    "marginacion_index": None,
}


def build_test_db(db_path: Path, rows: list[dict]) -> None:
    """Build a throwaway sqlite db with the same `listings` schema ingest.py
    creates, pre-populated with `rows` (dicts; missing optional keys default
    per _ROW_DEFAULTS)."""
    con = sqlite3.connect(db_path)
    con.executescript(LISTINGS_SCHEMA)
    full_rows = []
    for row in rows:
        full = dict(_ROW_DEFAULTS)
        full.update(row)
        full_rows.append(full)
    con.executemany(_INSERT_SQL, full_rows)
    con.commit()
    con.close()

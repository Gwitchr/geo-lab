from __future__ import annotations

import csv
import sqlite3

import pytest

pytest.importorskip("native.fallback.fastgeo_py", reason="pipeline/native/ not present yet")

import ingest  # noqa: E402

FIELDNAMES = [
    "id", "title", "description", "price_mxn", "m2", "bedrooms", "type",
    "colonia", "municipio", "estado", "lat", "lng", "listed_date", "source",
]

ORIGINAL_DESC = (
    "Excelente casa en Roma Norte, Cuauhtemoc. Cuenta con 140 m2 de construccion "
    "y 3 recamaras. Incluye jardin privado, alberca. Acepto credito infonavit."
)
REWORDED_DESC = (
    "Excelente casa en Roma Norte, Cuauhtemoc! Cuenta con 140 m2 de construccion "
    "y 3 recamaras. Incluye jardin privado, alberca. Acepto credito infonavit. URGE VENTA!"
)


def _row(**overrides):
    row = {
        "id": "LST0000001",
        "title": "Casa en Roma Norte",
        "description": ORIGINAL_DESC,
        "price_mxn": "3500000",
        "m2": "140",
        "bedrooms": "3",
        "type": "casa",
        "colonia": "Roma Norte",
        "municipio": "Cuauhtémoc",
        "estado": "Ciudad de México",
        "lat": "19.4179",
        "lng": "-99.1626",
        "listed_date": "2024-01-01",
        "source": "vivanuncios",
    }
    row.update(overrides)
    return row


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_build_creates_db_with_expected_schema_and_rows(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "db.sqlite"

    good = _row(id="LST0000001")
    near_dup = _row(
        id="LST0000002",
        description=REWORDED_DESC,
        lat="19.41795",
        lng="-99.16255",
        listed_date="2024-02-01",
    )
    broken = _row(id="LST0000003", price_mxn="N/D")

    _write_csv(raw_dir / "listings_vivanuncios.csv", [good, near_dup, broken])

    result = ingest.build(raw_dir, db_path, verbose=False)

    assert result["read"] == 3
    assert result["dropped"] == 1
    assert result["rows"] == 2
    assert result["duplicates"] == 1
    assert db_path.exists()

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cols = {r[1] for r in con.execute("PRAGMA table_info(listings)")}
    for expected in (
        "id", "title", "description", "price_mxn", "m2", "bedrooms", "type",
        "colonia", "municipio", "estado", "lat", "lng", "listed_date",
        "source", "dup_of", "ageb_id", "marginacion_grade", "marginacion_index",
    ):
        assert expected in cols

    rows = con.execute("SELECT id, dup_of FROM listings ORDER BY id").fetchall()
    assert len(rows) == 2
    by_id = {r["id"]: r["dup_of"] for r in rows}
    assert by_id["LST0000001"] is None
    assert by_id["LST0000002"] == "LST0000001"

    pk_check = con.execute("PRAGMA table_info(listings)").fetchall()
    id_col = next(c for c in pk_check if c[1] == "id")
    assert id_col[5] == 1  # pk flag
    con.close()


def test_build_overwrites_existing_db(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "db.sqlite"

    _write_csv(raw_dir / "listings_vivanuncios.csv", [_row(id="LST0000001")])
    ingest.build(raw_dir, db_path, verbose=False)

    _write_csv(raw_dir / "listings_vivanuncios.csv", [_row(id="LST0000009")])
    result = ingest.build(raw_dir, db_path, verbose=False)

    con = sqlite3.connect(db_path)
    ids = [r[0] for r in con.execute("SELECT id FROM listings")]
    con.close()
    assert ids == ["LST0000009"]
    assert result["rows"] == 1

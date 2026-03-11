from __future__ import annotations

import json

import export_web
from conftest import build_test_db


def _row(id_, listed_date, price_mxn=2_000_000, m2=100, dup_of=None):
    return {
        "id": id_, "title": f"Listing {id_}", "colonia": "Roma Norte",
        "municipio": "Cuauhtémoc", "estado": "Ciudad de México",
        "price_mxn": price_mxn, "m2": m2, "bedrooms": 2, "type": "departamento",
        "lat": 19.4, "lng": -99.1, "listed_date": listed_date, "dup_of": dup_of,
    }


def test_export_writes_expected_fields(tmp_path):
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "listings.json"
    build_test_db(db_path, [_row("A", "2024-01-01")])

    n = export_web.export(db_path, out_path)

    assert n == 1
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert set(data[0].keys()) == set(export_web.FIELDS)
    assert data[0]["id"] == "A"


def test_export_excludes_duplicates(tmp_path):
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "listings.json"
    build_test_db(db_path, [
        _row("A", "2024-01-01"),
        _row("B", "2024-01-02", dup_of="A"),
    ])

    n = export_web.export(db_path, out_path)
    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert n == 1
    assert data[0]["id"] == "A"


def test_export_orders_newest_first(tmp_path):
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "listings.json"
    build_test_db(db_path, [
        _row("OLD", "2023-01-01"),
        _row("NEW", "2024-06-01"),
    ])

    export_web.export(db_path, out_path)
    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert [row["id"] for row in data] == ["NEW", "OLD"]


def test_export_respects_max_rows_cap(tmp_path):
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "listings.json"
    rows = [_row(f"L{i:03d}", f"2024-01-{(i % 28) + 1:02d}") for i in range(20)]
    build_test_db(db_path, rows)

    n = export_web.export(db_path, out_path, max_rows=5)
    data = json.loads(out_path.read_text(encoding="utf-8"))

    assert n == 5
    assert len(data) == 5

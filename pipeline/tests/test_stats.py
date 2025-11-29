from __future__ import annotations

import json

import stats
from conftest import build_test_db


def _row(id_, colonia, municipio, price_mxn, m2, dup_of=None):
    return {
        "id": id_, "colonia": colonia, "municipio": municipio,
        "price_mxn": price_mxn, "m2": m2, "type": "casa",
        "estado": "Ciudad de México", "lat": 19.4, "lng": -99.1,
        "listed_date": "2024-01-01", "dup_of": dup_of,
    }


def test_compute_basic_shape_and_totals(tmp_path):
    db_path = tmp_path / "db.sqlite"
    build_test_db(db_path, [
        _row("A", "Roma Norte", "Cuauhtémoc", 2_000_000, 100),
        _row("B", "Roma Norte", "Cuauhtémoc", 3_000_000, 150),
        _row("C", "Del Valle", "Benito Juárez", 4_000_000, 100),
    ])

    data = stats.compute(db_path)

    assert data["total_listings"] == 3
    assert "generated_at" in data
    assert isinstance(data["by_colonia"], list)
    assert isinstance(data["histogram"], list)

    roma = next(r for r in data["by_colonia"] if r["colonia"] == "Roma Norte")
    assert roma["municipio"] == "Cuauhtémoc"
    assert roma["count"] == 2
    # median of [2_000_000/100, 3_000_000/150] = median of [20000, 20000] = 20000
    assert roma["median_price_per_m2"] == 20000.0


def test_compute_excludes_duplicates(tmp_path):
    db_path = tmp_path / "db.sqlite"
    build_test_db(db_path, [
        _row("A", "Roma Norte", "Cuauhtémoc", 2_000_000, 100),
        _row("B", "Roma Norte", "Cuauhtémoc", 2_100_000, 100, dup_of="A"),
    ])

    data = stats.compute(db_path)
    assert data["total_listings"] == 1
    roma = next(r for r in data["by_colonia"] if r["colonia"] == "Roma Norte")
    assert roma["count"] == 1


def test_compute_histogram_buckets_and_overflow(tmp_path):
    db_path = tmp_path / "db.sqlite"
    build_test_db(db_path, [
        _row("A", "X", "Y", 400_000, 100),      # <= 500k bucket
        _row("B", "X", "Y", 900_000, 100),      # <= 1M bucket
        _row("C", "X", "Y", 50_000_000, 100),   # overflow (null) bucket
    ])

    data = stats.compute(db_path)
    histogram = data["histogram"]
    assert histogram[0] == {"bucket_max_mxn": 500_000, "count": 1}
    assert histogram[1] == {"bucket_max_mxn": 1_000_000, "count": 1}
    assert histogram[-1]["bucket_max_mxn"] is None
    assert histogram[-1]["count"] == 1
    assert sum(h["count"] for h in histogram) == 3


def test_compute_empty_db(tmp_path):
    db_path = tmp_path / "db.sqlite"
    build_test_db(db_path, [])
    data = stats.compute(db_path)
    assert data["total_listings"] == 0
    assert data["by_colonia"] == []
    assert sum(h["count"] for h in data["histogram"]) == 0


def test_run_writes_json_file(tmp_path):
    db_path = tmp_path / "db.sqlite"
    out_path = tmp_path / "stats.json"
    build_test_db(db_path, [_row("A", "Roma Norte", "Cuauhtémoc", 2_000_000, 100)])

    stats.run(db_path, out_path, verbose=False)

    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["total_listings"] == 1

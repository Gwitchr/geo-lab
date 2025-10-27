from __future__ import annotations

import csv
from pathlib import Path

import clean

GOOD_ROW = {
    "id": "LST0000001",
    "title": "Casa en Roma Norte, 3 rec, 140 m2",
    "description": "Excelente casa en Roma Norte, Cuauhtemoc. URGE VENDER.",
    "price_mxn": "3500000",
    "m2": "140",
    "bedrooms": "3",
    "type": "casa",
    "colonia": "Roma Norte",
    "municipio": "Cuauhtémoc",
    "estado": "Ciudad de México",
    "lat": "19.4179",
    "lng": "-99.1626",
    "listed_date": "2024-05-01",
    "source": "vivanuncios",
}


def _row(**overrides):
    row = dict(GOOD_ROW)
    row.update(overrides)
    return row


# --------------------------------------------------------------------------
# parse_price
# --------------------------------------------------------------------------


def test_parse_price_plain_int_string():
    assert clean.parse_price("1500000") == 1500000


def test_parse_price_currency_formatted():
    assert clean.parse_price("$1,250,000") == 1250000


def test_parse_price_float_string_rounds():
    assert clean.parse_price("999999.6") == 1000000


def test_parse_price_invalid_returns_none():
    for bad in ("N/D", "", None, "  ", "abc"):
        assert clean.parse_price(bad) is None


def test_parse_price_non_positive_returns_none():
    assert clean.parse_price("0") is None
    assert clean.parse_price("-500") is None


# --------------------------------------------------------------------------
# clean_row
# --------------------------------------------------------------------------


def test_clean_row_valid_passes_through_with_correct_types():
    cleaned, reason = clean.clean_row(GOOD_ROW)
    assert reason is None
    assert cleaned["id"] == "LST0000001"
    assert cleaned["price_mxn"] == 3500000
    assert isinstance(cleaned["price_mxn"], int)
    assert cleaned["m2"] == 140
    assert isinstance(cleaned["m2"], int)
    assert cleaned["bedrooms"] == 3
    assert cleaned["type"] == "casa"
    assert cleaned["lat"] == 19.4179
    assert isinstance(cleaned["lat"], float)


def test_clean_row_normalizes_type_casing():
    cleaned, reason = clean.clean_row(_row(type="CASA"))
    assert reason is None
    assert cleaned["type"] == "casa"


def test_clean_row_strips_currency_formatted_price():
    cleaned, reason = clean.clean_row(_row(price_mxn="$3,500,000"))
    assert reason is None
    assert cleaned["price_mxn"] == 3500000


def test_clean_row_strips_whitespace_padding():
    cleaned, reason = clean.clean_row(_row(title="  Casa en Roma  ", colonia="Roma Norte  "))
    assert reason is None
    assert cleaned["title"] == "Casa en Roma"
    assert cleaned["colonia"] == "Roma Norte"


def test_clean_row_missing_id_dropped():
    cleaned, reason = clean.clean_row(_row(id=""))
    assert cleaned is None
    assert reason == "missing_id"


def test_clean_row_bad_price_dropped():
    cleaned, reason = clean.clean_row(_row(price_mxn="N/D"))
    assert cleaned is None
    assert reason == "bad_price"


def test_clean_row_negative_m2_dropped():
    cleaned, reason = clean.clean_row(_row(m2="-1"))
    assert cleaned is None
    assert reason == "bad_m2"


def test_clean_row_zero_m2_dropped():
    cleaned, reason = clean.clean_row(_row(m2="0"))
    assert cleaned is None
    assert reason == "bad_m2"


def test_clean_row_invalid_type_dropped():
    cleaned, reason = clean.clean_row(_row(type="oficina"))
    assert cleaned is None
    assert reason == "bad_type"


def test_clean_row_missing_colonia_dropped():
    cleaned, reason = clean.clean_row(_row(colonia=""))
    assert cleaned is None
    assert reason == "missing_location"


def test_clean_row_bad_coords_dropped():
    cleaned, reason = clean.clean_row(_row(lat="200", lng="-99.0"))
    assert cleaned is None
    assert reason == "bad_coords"


def test_clean_row_bad_date_dropped():
    cleaned, reason = clean.clean_row(_row(listed_date="05/01/2024"))
    assert cleaned is None
    assert reason == "bad_date"


def test_clean_row_blank_bedrooms_defaults_to_zero():
    cleaned, reason = clean.clean_row(_row(bedrooms=""))
    assert reason is None
    assert cleaned["bedrooms"] == 0


# --------------------------------------------------------------------------
# read_raw_csv / clean_all (encoding fallback + aggregation)
# --------------------------------------------------------------------------

FIELDNAMES = clean.FIELDNAMES


def _write_csv(path: Path, rows: list[dict], encoding: str) -> None:
    with open(path, "w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_read_raw_csv_handles_latin1_encoding(tmp_path):
    path = tmp_path / "listings_metroscubicos.csv"
    row = _row(description="Departamento con jardín, cerca del metro, año de construcción 2020")
    _write_csv(path, [row], encoding="latin-1")

    rows = clean.read_raw_csv(path)
    assert len(rows) == 1
    assert "jardín" in rows[0]["description"]


def test_clean_all_aggregates_across_sources_and_counts_drops(tmp_path):
    good = _row(id="LST0000001")
    broken = _row(id="LST0000002", price_mxn="N/D")
    dup_id = _row(id="LST0000001", title="duplicate id row")

    _write_csv(tmp_path / "listings_vivanuncios.csv", [good, broken], encoding="utf-8")
    _write_csv(tmp_path / "listings_lamudi.csv", [dup_id], encoding="utf-8")

    rows, stats = clean.clean_all(tmp_path)

    assert stats["read"] == 3
    assert stats["kept"] == 1
    assert stats["dropped"] == 2
    assert stats["reasons"]["bad_price"] == 1
    assert stats["reasons"]["duplicate_id"] == 1
    assert len(rows) == 1
    assert rows[0]["id"] == "LST0000001"


def test_clean_all_ignores_non_matching_files(tmp_path):
    (tmp_path / "readme.txt").write_text("not a csv", encoding="utf-8")
    rows, stats = clean.clean_all(tmp_path)
    assert rows == []
    assert stats["read"] == 0

from __future__ import annotations

import pytest

# native/ (the fastgeo fallback dedupe.py imports through pipeline/geo_backend.py)
# is owned/built by a different agent and may not exist yet in some checkouts;
# skip cleanly instead of erroring the whole suite, same pattern as
# pipeline/tests/test_parity.py.
pytest.importorskip("native.fallback.fastgeo_py", reason="pipeline/native/ not present yet")

import dedupe  # noqa: E402


def _row(id_, description, lat, lng, m2=100, type_="casa", municipio="Cuauhtémoc", listed_date="2024-01-01"):
    return {
        "id": id_,
        "description": description,
        "lat": lat,
        "lng": lng,
        "m2": m2,
        "type": type_,
        "listed_date": listed_date,
        "municipio": municipio,
    }


ORIGINAL_DESC = (
    "Excelente casa en Roma Norte, Cuauhtemoc. Cuenta con 140 m2 de construccion "
    "y 3 recamaras. Incluye jardin privado, alberca. Acepto credito infonavit."
)
REWORDED_DESC = (
    "Excelente casa en Roma Norte, Cuauhtemoc! Cuenta con 140 m2 de construccion "
    "y 3 recamaras. Incluye jardin privado, alberca. Acepto credito infonavit. URGE VENTA!"
)
UNRELATED_DESC = "Terreno plano en Milpa Alta, ideal para inversion, escrituras al corriente."


def test_near_duplicate_pair_is_flagged():
    rows = [
        _row("A", ORIGINAL_DESC, 19.4179, -99.1626, listed_date="2024-01-01"),
        _row("B", REWORDED_DESC, 19.41795, -99.16255, listed_date="2024-02-01"),
    ]
    dup_map = dedupe.find_duplicates(rows)
    assert dup_map["A"] is None  # canonical: earliest listed_date
    assert dup_map["B"] == "A"


def test_unrelated_listing_with_similar_text_not_flagged_when_far_away():
    rows = [
        _row("A", ORIGINAL_DESC, 19.4179, -99.1626, listed_date="2024-01-01"),
        # Same text template, same municipio/type/m2, but ~5km away: not the same property.
        _row("C", REWORDED_DESC, 19.46, -99.16, listed_date="2024-02-01"),
    ]
    dup_map = dedupe.find_duplicates(rows)
    assert dup_map["A"] is None
    assert dup_map["C"] is None


def test_unrelated_listing_different_type_not_flagged_even_if_close():
    rows = [
        _row("A", ORIGINAL_DESC, 19.4179, -99.1626, type_="casa", listed_date="2024-01-01"),
        _row("D", REWORDED_DESC, 19.41795, -99.16255, type_="departamento", listed_date="2024-02-01"),
    ]
    dup_map = dedupe.find_duplicates(rows)
    assert dup_map["A"] is None
    assert dup_map["D"] is None


def test_completely_different_text_not_flagged_even_if_close():
    rows = [
        _row("A", ORIGINAL_DESC, 19.4179, -99.1626, listed_date="2024-01-01"),
        _row("E", UNRELATED_DESC, 19.41795, -99.16255, listed_date="2024-02-01"),
    ]
    dup_map = dedupe.find_duplicates(rows)
    assert dup_map["A"] is None
    assert dup_map["E"] is None


def test_duplicate_chain_points_to_earliest_canonical():
    rows = [
        _row("A", ORIGINAL_DESC, 19.4179, -99.1626, listed_date="2024-01-01"),
        _row("B", REWORDED_DESC, 19.41795, -99.16255, listed_date="2024-02-01"),
        _row("C", REWORDED_DESC, 19.41792, -99.16258, listed_date="2024-03-01"),
    ]
    dup_map = dedupe.find_duplicates(rows)
    assert dup_map["A"] is None
    assert dup_map["B"] == "A"
    assert dup_map["C"] == "A"


def test_empty_rows_returns_empty_map():
    assert dedupe.find_duplicates([]) == {}

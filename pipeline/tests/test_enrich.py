from __future__ import annotations

import pytest

pytest.importorskip("native.fallback.fastgeo_py", reason="pipeline/native/ not present yet")

import enrich  # noqa: E402
from conftest import ROOT_DIR  # noqa: E402

# A simple 1x1-degree square, as (lat, lng) -- matches fastgeo's ring convention.
SQUARE = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
SQUARE_BBOX = (0.0, 0.0, 1.0, 1.0)


def test_assign_ageb_point_inside_polygon():
    polys = [{"id": "AGEB-1", "ring": SQUARE, "bbox": SQUARE_BBOX}]
    assert enrich.assign_ageb(0.5, 0.5, polys) == "AGEB-1"


def test_assign_ageb_point_outside_all_polygons_returns_none():
    polys = [{"id": "AGEB-1", "ring": SQUARE, "bbox": SQUARE_BBOX}]
    assert enrich.assign_ageb(5.0, 5.0, polys) is None


def test_assign_ageb_picks_correct_polygon_among_several():
    other_square = [(2.0, 2.0), (2.0, 3.0), (3.0, 3.0), (3.0, 2.0)]
    polys = [
        {"id": "AGEB-1", "ring": SQUARE, "bbox": SQUARE_BBOX},
        {"id": "AGEB-2", "ring": other_square, "bbox": (2.0, 2.0, 3.0, 3.0)},
    ]
    assert enrich.assign_ageb(0.2, 0.8, polys) == "AGEB-1"
    assert enrich.assign_ageb(2.5, 2.5, polys) == "AGEB-2"


def test_assign_ageb_empty_polygon_list_returns_none():
    assert enrich.assign_ageb(0.5, 0.5, []) is None


def test_assign_ageb_vertex_is_boundary_inclusive():
    # fastgeo's point_in_polygon treats a ring's own vertices as inside
    # (boundary-inclusive), see pipeline/native/fallback/fastgeo_py.py and
    # pipeline/tests/test_parity.py.
    polys = [{"id": "AGEB-1", "ring": SQUARE, "bbox": SQUARE_BBOX}]
    for lat, lng in SQUARE:
        assert enrich.assign_ageb(lat, lng, polys) == "AGEB-1"


# --------------------------------------------------------------------------
# Integration-style checks against the real, committed open data (small
# enough -- a few MB -- to load in a test without network access).
# --------------------------------------------------------------------------

AGEBS_PATH = ROOT_DIR / "data" / "geo" / "agebs_cdmx.geojson"
MARGINACION_PATH = ROOT_DIR / "data" / "geo" / "marginacion_cdmx.csv"


@pytest.mark.skipif(not AGEBS_PATH.exists(), reason="data/geo/agebs_cdmx.geojson not present")
def test_load_agebs_real_data_shape():
    by_mun = enrich.load_agebs(AGEBS_PATH)
    assert len(by_mun) == 16  # CDMX's 16 alcaldías
    total_polys = sum(len(v) for v in by_mun.values())
    assert total_polys > 2000


@pytest.mark.skipif(not AGEBS_PATH.exists(), reason="data/geo/agebs_cdmx.geojson not present")
def test_assign_ageb_real_vertex_resolves_to_its_own_ageb():
    by_mun = enrich.load_agebs(AGEBS_PATH)
    mun, polys = next(iter(by_mun.items()))
    target = polys[0]
    lat, lng = target["ring"][0]
    assert enrich.assign_ageb(lat, lng, polys) == target["id"]


@pytest.mark.skipif(not MARGINACION_PATH.exists(), reason="data/geo/marginacion_cdmx.csv not present")
def test_load_marginacion_real_data_shape():
    info = enrich.load_marginacion(MARGINACION_PATH)
    assert len(info) > 2000
    sample = next(iter(info.values()))
    assert "grade" in sample and "index_value" in sample
    assert isinstance(sample["index_value"], float)

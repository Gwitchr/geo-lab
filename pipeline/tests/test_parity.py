"""Property-style parity tests: the compiled fastgeo C++ extension must
agree with the pure-Python reference implementation
(pipeline/native/fallback/fastgeo_py.py) on every API call.

Fixed-seed random polygons/points/strings are generated once per session and
reused across the tests below. Booleans and integers (point_in_polygon,
batch_assign, simhash64, hamming) must match exactly; haversine_matrix
distances (floats, computed via libm sin/cos/atan2 that may round
differently between the two call paths) are compared with a tight
relative tolerance.

Skip behavior (see the module-level guard below):
- FASTGEO_FORCE_FALLBACK=1: there is nothing to compare (both sides would be
  the same fallback module), so the whole suite is skipped cleanly.
- compiled `fastgeo` extension not built/importable: skipped cleanly, same
  as the pipeline-test CI job does.
"""

from __future__ import annotations

import math
import os
import random
import sys
from pathlib import Path

import pytest

# Make `native.fallback.fastgeo_py` importable regardless of the directory
# pytest was invoked from (repo root or pipeline/).
_PIPELINE_DIR = Path(__file__).resolve().parent.parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    pytest.skip(
        "FASTGEO_FORCE_FALLBACK=1: no compiled module to compare against the "
        "fallback, parity suite skipped",
        allow_module_level=True,
    )

native = pytest.importorskip(
    "fastgeo", reason="compiled fastgeo extension not built; parity suite skipped"
)

from native.fallback import fastgeo_py as ref  # noqa: E402

SEED = 20260710
RNG = random.Random(SEED)

HAVERSINE_REL_TOL = 1e-9
HAVERSINE_ABS_TOL = 1e-6  # meters, for near-zero distances


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------


def _random_simple_ring(rng: random.Random, min_vertices: int = 3, max_vertices: int = 12) -> list[tuple[float, float]]:
    """Random simple (non-self-intersecting) polygon ring as (lat, lng) tuples.

    Built by sampling random angles/radii around a center and sorting by
    angle -- a star-shaped-by-construction polygon is always simple.
    """
    n = rng.randint(min_vertices, max_vertices)
    center_lat = rng.uniform(-60.0, 60.0)
    center_lng = rng.uniform(-170.0, 170.0)
    scale = rng.uniform(0.001, 5.0)

    angles = sorted(rng.uniform(0.0, 2.0 * math.pi) for _ in range(n))
    ring = []
    for angle in angles:
        radius = scale * rng.uniform(0.2, 1.0)
        lat = center_lat + radius * math.sin(angle)
        lng = center_lng + radius * math.cos(angle)
        ring.append((lat, lng))
    return ring


def _random_point_near(rng: random.Random, ring: list[tuple[float, float]]) -> tuple[float, float]:
    """Random point in the bounding box of ring, padded a bit to cover outside cases."""
    lats = [p[0] for p in ring]
    lngs = [p[1] for p in ring]
    pad_lat = (max(lats) - min(lats)) * 0.5 + 0.01
    pad_lng = (max(lngs) - min(lngs)) * 0.5 + 0.01
    return (
        rng.uniform(min(lats) - pad_lat, max(lats) + pad_lat),
        rng.uniform(min(lngs) - pad_lng, max(lngs) + pad_lng),
    )


def _boundary_points(ring: list[tuple[float, float]], rng: random.Random) -> list[tuple[float, float]]:
    """Vertices and near-edge points -- boundary and near-boundary cases.

    Vertices are algebraically guaranteed to satisfy the exact on-segment
    check in both implementations (the cross product reduces to `0 * k`
    regardless of rounding), so both must classify them as inside. Midpoints
    and arbitrary linear-interpolation points are *not* guaranteed to land
    exactly on the segment once floating-point rounding of the interpolation
    itself is involved -- they are included to stress-test that the two
    implementations still round identically and agree with each other, not
    to assert a fixed inside/outside answer.
    """
    pts: list[tuple[float, float]] = list(ring)
    n = len(ring)
    for i in range(n):
        a = ring[i]
        b = ring[(i + 1) % n]
        pts.append(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
        t = rng.uniform(0.0, 1.0)
        pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return pts


_WORDS = [
    "casa", "departamento", "terreno", "local", "venta", "renta", "URGE", "VENDER",
    "excelente", "ubicacion", "ubicación", "cuauhtemoc", "Cuauhtémoc", "roma", "condesa",
    "Polanco", "recamaras", "recámaras", "baños", "banos", "jardin", "jardín", "alberca",
    "seguridad", "24hrs", "$1,250,000", "m2", "credito", "crédito", "INFONAVIT", "oportunidad",
]
_PUNCT = [" ", " ", " ", ", ", "! ", ". ", " - ", "  ", "\n", "\t", "¡", "()", "'", '"']


def _random_listing_text(rng: random.Random) -> str:
    if rng.random() < 0.05:
        return ""
    n = rng.randint(1, 25)
    parts = []
    for _ in range(n):
        word = rng.choice(_WORDS)
        if rng.random() < 0.15:
            word = word.upper()
        parts.append(word)
        parts.append(rng.choice(_PUNCT))
    return "".join(parts)


# Fixed-seed corpora built once, shared by the tests below.
RANDOM_RINGS = [_random_simple_ring(RNG) for _ in range(20)]
DEGENERATE_RINGS: list[list[tuple[float, float]]] = [
    [],
    [(0.0, 0.0)],
    [(0.0, 0.0), (1.0, 1.0)],
    [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)],  # all-identical (zero area)
    [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)],  # collinear (zero area)
    [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)],  # explicit closing vertex
]
RANDOM_TEXTS = [_random_listing_text(RNG) for _ in range(60)]


# --------------------------------------------------------------------------
# point_in_polygon
# --------------------------------------------------------------------------


def test_point_in_polygon_random_points_agree():
    for ring in RANDOM_RINGS:
        for _ in range(15):
            lat, lng = _random_point_near(RNG, ring)
            assert native.point_in_polygon(lat, lng, ring) == ref.point_in_polygon(lat, lng, ring), (
                lat,
                lng,
                ring,
            )


def test_point_in_polygon_boundary_points_agree():
    for ring in RANDOM_RINGS:
        for lat, lng in _boundary_points(ring, RNG):
            native_result = native.point_in_polygon(lat, lng, ring)
            ref_result = ref.point_in_polygon(lat, lng, ring)
            assert native_result == ref_result, (lat, lng, ring)


def test_point_in_polygon_vertices_are_always_inside():
    # A vertex is trivially on its own incident edges: the cross product
    # reduces to `0 * k`, which is exactly 0.0 regardless of rounding. Both
    # implementations must classify every ring vertex as inside.
    for ring in RANDOM_RINGS:
        for lat, lng in ring:
            assert native.point_in_polygon(lat, lng, ring) is True
            assert ref.point_in_polygon(lat, lng, ring) is True


def test_point_in_polygon_degenerate_rings_agree():
    query_points = [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (-3.0, 42.0), (0.0, 1.0)]
    for ring in DEGENERATE_RINGS:
        for lat, lng in query_points:
            assert native.point_in_polygon(lat, lng, ring) == ref.point_in_polygon(lat, lng, ring), (
                lat,
                lng,
                ring,
            )


# --------------------------------------------------------------------------
# batch_assign
# --------------------------------------------------------------------------


def test_batch_assign_random_agrees():
    polygons = {f"poly-{i}": ring for i, ring in enumerate(RANDOM_RINGS)}
    points = []
    for ring in RANDOM_RINGS:
        for _ in range(5):
            points.append(_random_point_near(RNG, ring))

    native_result = native.batch_assign(points, polygons)
    ref_result = ref.batch_assign(points, polygons)
    assert native_result == ref_result


def test_batch_assign_boundary_and_empty_agrees():
    polygons = {f"poly-{i}": ring for i, ring in enumerate(RANDOM_RINGS[:5])}
    points = _boundary_points(RANDOM_RINGS[0], RNG) + [(1000.0, 1000.0)]

    assert native.batch_assign(points, polygons) == ref.batch_assign(points, polygons)
    assert native.batch_assign([], polygons) == ref.batch_assign([], polygons) == []
    assert native.batch_assign(points, {}) == ref.batch_assign(points, {}) == [None] * len(points)


# --------------------------------------------------------------------------
# haversine_matrix
# --------------------------------------------------------------------------


def _assert_matrices_close(a: list[list[float]], b: list[list[float]]) -> None:
    assert len(a) == len(b)
    for row_a, row_b in zip(a, b):
        assert len(row_a) == len(row_b)
        for va, vb in zip(row_a, row_b):
            assert math.isclose(va, vb, rel_tol=HAVERSINE_REL_TOL, abs_tol=HAVERSINE_ABS_TOL), (va, vb)


def test_haversine_matrix_random_agrees():
    points_a = [(RNG.uniform(-85.0, 85.0), RNG.uniform(-180.0, 180.0)) for _ in range(30)]
    points_b = [(RNG.uniform(-85.0, 85.0), RNG.uniform(-180.0, 180.0)) for _ in range(25)]

    native_matrix = native.haversine_matrix(points_a, points_b)
    ref_matrix = ref.haversine_matrix(points_a, points_b)
    _assert_matrices_close(native_matrix, ref_matrix)


def test_haversine_matrix_identical_points_agree_near_zero():
    points = [(19.4326, -99.1332), (0.0, 0.0), (-33.45, -70.6667)]
    native_matrix = native.haversine_matrix(points, points)
    ref_matrix = ref.haversine_matrix(points, points)
    _assert_matrices_close(native_matrix, ref_matrix)
    for i, row in enumerate(native_matrix):
        assert row[i] == pytest.approx(0.0, abs=1e-6)


def test_haversine_matrix_empty_inputs_agree():
    assert native.haversine_matrix([], []) == ref.haversine_matrix([], []) == []
    assert native.haversine_matrix([(0.0, 0.0)], []) == ref.haversine_matrix([(0.0, 0.0)], []) == [[]]


# --------------------------------------------------------------------------
# simhash64 / hamming
# --------------------------------------------------------------------------


def test_simhash64_random_texts_agree():
    for text in RANDOM_TEXTS:
        assert native.simhash64(text) == ref.simhash64(text), text


def test_simhash64_empty_and_whitespace_only_is_zero():
    for text in ["", "   ", "!!! ... ---", "\n\t"]:
        assert native.simhash64(text) == 0
        assert ref.simhash64(text) == 0


def test_simhash64_near_duplicate_texts_are_close():
    original = "URGE VENDER casa en Cuauhtémoc, excelente ubicación, 3 recamaras"
    near_dup = "urge vender casa en cuauhtemoc, excelente ubicacion, 3 recamaras!!"
    unrelated = _random_listing_text(random.Random(999))

    h_orig_native, h_orig_ref = native.simhash64(original), ref.simhash64(original)
    h_dup_native, h_dup_ref = native.simhash64(near_dup), ref.simhash64(near_dup)
    h_unrel_native, h_unrel_ref = native.simhash64(unrelated), ref.simhash64(unrelated)

    assert h_orig_native == h_orig_ref
    assert h_dup_native == h_dup_ref
    assert h_unrel_native == h_unrel_ref

    dist_dup_native = native.hamming(h_orig_native, h_dup_native)
    dist_dup_ref = ref.hamming(h_orig_ref, h_dup_ref)
    assert dist_dup_native == dist_dup_ref

    dist_unrel_native = native.hamming(h_orig_native, h_unrel_native)
    dist_unrel_ref = ref.hamming(h_orig_ref, h_unrel_ref)
    assert dist_unrel_native == dist_unrel_ref


def test_hamming_random_pairs_agree():
    hashes = [native.simhash64(t) for t in RANDOM_TEXTS]
    ref_hashes = [ref.simhash64(t) for t in RANDOM_TEXTS]
    assert hashes == ref_hashes

    for _ in range(50):
        i, j = RNG.randrange(len(hashes)), RNG.randrange(len(hashes))
        assert native.hamming(hashes[i], hashes[j]) == ref.hamming(ref_hashes[i], ref_hashes[j])

    assert native.hamming(0, 0) == ref.hamming(0, 0) == 0
    max64 = (1 << 64) - 1
    assert native.hamming(0, max64) == ref.hamming(0, max64) == 64
    assert native.hamming(max64, max64) == ref.hamming(max64, max64) == 0

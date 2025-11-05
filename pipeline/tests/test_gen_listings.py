"""Tests for data/gen/gen_listings.py, run from pipeline/tests/ (this
project's only pytest suite -- data/gen has no tests/ of its own per
BRIEF.md's tree). Uses small counts (not the real ~100k) so this stays fast;
byte-reproducibility itself is re-verified at small scale here as a
regression guard, and was verified at full scale manually (see
HANDOFF-pipeline.md).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from conftest import ROOT_DIR

GEN_DIR = ROOT_DIR / "data" / "gen"
if str(GEN_DIR) not in sys.path:
    sys.path.insert(0, str(GEN_DIR))

import gen_listings  # noqa: E402


def _hash_dir(path: Path) -> dict[str, str]:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(path.glob("*.csv"))
    }


def test_generate_is_byte_reproducible(tmp_path):
    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"

    gen_listings.generate(out_dir=out_a, primary_count=200, dup_count=5, broken_extra=3, verbose=False)
    gen_listings.generate(out_dir=out_b, primary_count=200, dup_count=5, broken_extra=3, verbose=False)

    hashes_a = _hash_dir(out_a)
    hashes_b = _hash_dir(out_b)
    assert hashes_a == hashes_b
    assert len(hashes_a) == len(gen_listings.SOURCES)


def test_generate_row_count_matches_request(tmp_path):
    out_dir = tmp_path / "run"
    result = gen_listings.generate(
        out_dir=out_dir, primary_count=100, dup_count=4, broken_extra=6, verbose=False
    )
    assert result["primaries"] == 100
    assert result["duplicates"] == 4
    assert result["broken"] == 6
    assert result["total"] == 110

    total_rows = 0
    for path in out_dir.glob("*.csv"):
        encoding = "latin-1" if "metroscubicos" in path.name else "utf-8"
        with open(path, encoding=encoding) as f:
            total_rows += sum(1 for _ in f) - 1  # minus header
    assert total_rows == 110


def test_generate_writes_all_four_sources(tmp_path):
    out_dir = tmp_path / "run"
    result = gen_listings.generate(out_dir=out_dir, primary_count=50, dup_count=2, broken_extra=1, verbose=False)
    assert set(result["paths"].keys()) == set(gen_listings.SOURCES)
    for path in result["paths"].values():
        assert path.exists()


def test_point_in_ring_and_sampling():
    square = [(-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)]
    assert gen_listings.point_in_ring(0.0, 0.0, square) is True
    assert gen_listings.point_in_ring(5.0, 5.0, square) is False

    import random
    rng = random.Random(1)
    bbox = gen_listings.ring_bbox(square)
    for _ in range(20):
        lat, lng = gen_listings.sample_point_in_polygon(square, bbox, rng)
        assert -1.0 <= lng <= 1.0
        assert -1.0 <= lat <= 1.0


def test_sample_point_in_polygon_falls_back_to_centroid_for_zero_attempts():
    # max_attempts=0 skips the rejection-sampling loop entirely, forcing the
    # centroid fallback deterministically -- must not raise, and must return
    # (lat, lng) computed from the ring's own (lng, lat) vertices.
    triangle = [(0.0, 0.0), (0.0, 6.0), (3.0, 0.0)]  # (lng, lat) points, per gen_listings' ring convention
    bbox = gen_listings.ring_bbox(triangle)
    import random
    lat, lng = gen_listings.sample_point_in_polygon(triangle, bbox, random.Random(1), max_attempts=0)
    assert lng == sum(p[0] for p in triangle) / 3  # mean lng = (0+0+3)/3
    assert lat == sum(p[1] for p in triangle) / 3  # mean lat = (0+6+0)/3

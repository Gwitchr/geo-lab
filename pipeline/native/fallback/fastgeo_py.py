"""Pure-Python reference implementation of the fastgeo API.

This module is the spec: the C++17 extension (``pipeline/native/fastgeo`` +
``pipeline/native/bindings.cpp``, built as the ``fastgeo`` pybind11 module) must
match every result this module produces, bit-for-bit for booleans/ints and
within floating-point tolerance for distances. See ``pipeline/tests/test_parity.py``.

Consumers should not import this module directly; go through the chokepoint:

    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo

Public API:
    point_in_polygon(lat, lng, ring) -> bool
    batch_assign(points, polygons) -> list[str | None]
    haversine_matrix(points_a, points_b) -> list[list[float]]
    simhash64(text) -> int
    hamming(a, b) -> int
"""

from __future__ import annotations

import math

# Mean Earth radius in meters. Must match the constant used by the C++
# implementation (fastgeo/geo.cpp) so haversine_matrix agrees within
# floating-point tolerance.
_EARTH_RADIUS_M = 6371000.0

# FNV-1a 64-bit constants. Must match fastgeo/simhash.cpp exactly.
_FNV_OFFSET_BASIS = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3
_MASK64 = 0xFFFFFFFFFFFFFFFF

Point = tuple[float, float]
Ring = list[tuple[float, float]]


def _on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    """True if (px, py) lies exactly on the closed segment [(ax, ay), (bx, by)].

    Uses an exact (epsilon-free) collinearity check via cross product, then a
    bounding-box containment check. Arithmetic order matters for bit-for-bit
    parity with the C++ implementation -- keep it identical on both sides.
    """
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if cross != 0.0:
        return False
    min_x, max_x = (ax, bx) if ax <= bx else (bx, ax)
    min_y, max_y = (ay, by) if ay <= by else (by, ay)
    return min_x <= px <= max_x and min_y <= py <= max_y


def point_in_polygon(lat: float, lng: float, ring: Ring) -> bool:
    """Ray-casting point-in-polygon test.

    ``ring`` is a list of (lat, lng) vertices describing a simple polygon
    (implicitly closed: the last vertex connects back to the first). Points
    exactly on an edge or vertex count as inside (boundary-inclusive).
    Rings with fewer than 3 vertices have no area and always return False.
    """
    n = len(ring)
    if n < 3:
        return False

    x, y = lng, lat
    inside = False
    for i in range(n):
        ax, ay = ring[i][1], ring[i][0]
        bx, by = ring[(i + 1) % n][1], ring[(i + 1) % n][0]

        if _on_segment(x, y, ax, ay, bx, by):
            return True

        if (ay > y) != (by > y):
            x_intersect = ax + (y - ay) * (bx - ax) / (by - ay)
            if x < x_intersect:
                inside = not inside

    return inside


def batch_assign(points: list[Point], polygons: dict[str, Ring]) -> list[str | None]:
    """Assign each point to the first polygon (in dict insertion order) containing it.

    Returns a list parallel to ``points``; entries are the polygon id (dict
    key) or None if the point falls inside no polygon.
    """
    items = list(polygons.items())
    result: list[str | None] = []
    for lat, lng in points:
        assigned: str | None = None
        for pid, ring in items:
            if point_in_polygon(lat, lng, ring):
                assigned = pid
                break
        result.append(assigned)
    return result


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return _EARTH_RADIUS_M * c


def haversine_matrix(points_a: list[Point], points_b: list[Point]) -> list[list[float]]:
    """Pairwise great-circle distances (meters) between two point sets."""
    return [
        [_haversine_m(lat_a, lng_a, lat_b, lng_b) for lat_b, lng_b in points_b]
        for lat_a, lng_a in points_a
    ]


def _is_word_byte(b: int) -> bool:
    return b >= 0x80 or (48 <= b <= 57) or (65 <= b <= 90) or (97 <= b <= 122)


def _tokenize(text: str) -> list[bytes]:
    """Split UTF-8 bytes of ``text`` into lowercase word tokens.

    ASCII letters/digits and any byte >= 0x80 (i.e. any byte of a multi-byte
    UTF-8 sequence, which covers accented Spanish characters) are word bytes;
    everything else is a separator. Only ASCII uppercase is folded to
    lowercase. This byte-level definition is chosen so the C++ side (which
    receives the pybind11-converted UTF-8 std::string) can replicate it
    exactly without a Unicode-aware library.
    """
    data = text.encode("utf-8")
    tokens: list[bytes] = []
    current = bytearray()
    for b in data:
        if _is_word_byte(b):
            if 65 <= b <= 90:
                b += 32
            current.append(b)
        elif current:
            tokens.append(bytes(current))
            current = bytearray()
    if current:
        tokens.append(bytes(current))
    return tokens


def _fnv1a64(token: bytes) -> int:
    h = _FNV_OFFSET_BASIS
    for byte in token:
        h ^= byte
        h = (h * _FNV_PRIME) & _MASK64
    return h


def simhash64(text: str) -> int:
    """64-bit simhash fingerprint of ``text``.

    Empty text (or text with no word tokens) hashes to 0. Each token is
    hashed with FNV-1a 64-bit; per-bit weights are accumulated (+1 for a set
    bit, -1 for a clear bit) across tokens, then the result bit is set where
    the weight is positive.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0

    weights = [0] * 64
    for token in tokens:
        h = _fnv1a64(token)
        for bit in range(64):
            if (h >> bit) & 1:
                weights[bit] += 1
            else:
                weights[bit] -= 1

    result = 0
    for bit in range(64):
        if weights[bit] > 0:
            result |= 1 << bit
    return result


def hamming(a: int, b: int) -> int:
    """Hamming distance between two values, treated as 64-bit unsigned."""
    return bin((a ^ b) & _MASK64).count("1")

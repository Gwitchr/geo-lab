---
aliases: [fastgeo]
tags: [architecture]
---

# fastgeo

A C++17 pybind11 extension module (`pipeline/native/`) for the spatial and text hot loops, with a
**pure-Python reference implementation that is the normative spec**
(`pipeline/native/fallback/fastgeo_py.py`). The compiled module is optional: pipeline code resolves
one or the other through `pipeline/geo_backend.py` and behaves identically either way.

## Why it exists

The pure-Python spatial join is genuinely the bottleneck at real scale (100k listings × ~2,400 AGEB
polygons). The first full `enrich.py` run against naive Python `batch_assign` took long enough that
it looked hung. Measured on macOS arm64, AppleClang, `-O3 -ffp-contract=off`, Python 3.13.1,
single-threaded, fixed-seed fixture (seed `20260710`), both sides producing the identical
6,673/100,000 matches:

| workload | compiled | pure-Python fallback | speedup |
|---|---|---|---|
| `batch_assign`, 100,000 points × 2,000 polygons | **2.19 s** | **247.32 s** (4 min 7 s) | **~113x** |
| `dedupe.py`, full 100,000-row run | **5.3 s** | **22.5 s** | **~4.3x** |
| `enrich.py`, full 50,314-CDMX-row run | 0.9 s | 1.5 s | ~1.7x |

The ~113x number is apples-to-apples brute force (no spatial index on either side) but it is *not*
the production story. `enrich.py` pre-filters candidates by municipio + bbox before it ever calls
`point_in_polygon` ([[pipeline]]), which engineers most of that gap away. **`dedupe.py`'s ~4.3x is
the honest "why fastgeo matters" number** — simhashing every description has no equivalent cheap
pre-filter.

## The API — 5 functions

Identical in both implementations. Signatures are a [[contracts]]-level commitment; changing one
means changing `fastgeo/geo.hpp`, `fastgeo/simhash.hpp`, `bindings.cpp`, `fallback/fastgeo_py.py`,
and `pipeline/tests/test_parity.py` together.

```python
point_in_polygon(lat: float, lng: float, ring: list[tuple[float, float]]) -> bool
batch_assign(points: list[Point], polygons: dict[str, Ring]) -> list[str | None]
haversine_matrix(points_a: list[Point], points_b: list[Point]) -> list[list[float]]  # meters
simhash64(text: str) -> int
hamming(a: int, b: int) -> int
```

- **`point_in_polygon`** — ray casting. `ring` is `(lat, lng)` pairs, implicitly closed. Rings with
  fewer than 3 vertices return `False`. Boundary points count as **inside**.
- **`batch_assign`** — first polygon *in dict insertion order* containing the point wins, else
  `None`. The pybind11 binding walks the `py::dict` directly into an ordered vector
  (`bindings.cpp:32`) precisely to preserve CPython insertion-order semantics. Brute-force
  O(points × polygons) by design — there is deliberately **no spatial index** on either side.
- **`haversine_matrix`** — meters, mean Earth radius `6371000.0` (constant duplicated in
  `geo.cpp:11` and `fastgeo_py.py:30`; they must match).
- **`simhash64`** — FNV-1a 64-bit per token, ±1 per-bit weight accumulation, bit set where the
  weight is **strictly positive**. Empty text (or text with no word tokens) hashes to `0`.
- **`hamming`** — popcount of `(a ^ b) & 0xFFFFFFFFFFFFFFFF`.

Consumers: `dedupe.py` uses `simhash64` / `hamming` / `haversine_matrix`; `enrich.py` uses
`point_in_polygon`. Nothing in the repo currently calls `batch_assign` in production — it exists as
the API surface and is what the headline benchmark measures.

## The fallback is the spec

`fallback/fastgeo_py.py` is not a degraded mode; it is the reference. Any disagreement is treated as
a **`fastgeo` bug, never a reference bug**. `pipeline/tests/test_parity.py` (fixed seed `20260710`,
13 tests) enforces this: random simple polygons, boundary points (every vertex, every edge midpoint,
a random interpolation point per edge), degenerate rings (empty / single / two-vertex /
all-identical / collinear / self-closing), `batch_assign` edge cases, `haversine_matrix` on random
and identical points, and `simhash64`/`hamming` on Spanish-listing-style text.

The suite `pytest.importorskip`s the compiled module, so CI's `pipeline-test` job (which never
builds C++) skips it cleanly; under `FASTGEO_FORCE_FALLBACK=1` it also skips, because both sides
would be the fallback and there is nothing to compare. Verified counts: 13 passed compiled, 1
skipped forced-fallback.

## Exact, epsilon-free boundary semantics

Boundary handling is **exact**, not fuzzy. `_on_segment` / `on_segment` does an exact
cross-product-equals-zero collinearity test plus a bounding-box containment test:

```python
cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
if cross != 0.0:
    return False
```

An epsilon tolerance was rejected deliberately: it would just relocate the cross-language
disagreement to the epsilon boundary rather than remove it. A consequence worth knowing: a ring's own
vertices are algebraically always inside, in both implementations.

**Arithmetic order is load-bearing.** `fastgeo_py.py:41` and `geo.cpp:17` mirror each other
operation-for-operation, as do the ray/edge intersection formulas
(`x_intersect = ax + (y - ay) * (bx - ax) / (by - ay)`). Do not "simplify" or reassociate either
side in isolation.

### The `-ffp-contract=off` bug — never add `-ffast-math`

`-O3` on Apple Clang (arm64, native FMA hardware) fuses multiply-add/subtract chains — exactly the
boundary cross-product and the ray-intersection formula — into a single FMA instruction with **one**
rounding step, which disagrees in the last bit with Python's strictly-separate IEEE754 operations.
The failures were real, sparse, and only ever on polygon-boundary points, which made them slow to
localize.

The fix is in `pipeline/native/CMakeLists.txt:29`:

```cmake
target_compile_options(fastgeo PRIVATE
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-O3 -Wall -Wextra -ffp-contract=off>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /W4>
)
```

**`-ffp-contract=off` is load-bearing. Do not remove it. Do not add `-ffast-math` or any
fast-math-adjacent flag** — and if you touch these flags at all, re-run `test_parity.py` against a
freshly built extension. MSVC needs no equivalent flag (it does not contract by default), though
that path is untested for lack of a Windows toolchain.

## Other design decisions

- **simhash tokenizer is byte-level**: any byte `>= 0x80` (i.e. any byte of a multi-byte UTF-8
  sequence) is a word byte, so accented Spanish text stays a single token without pulling a Unicode
  library into C++. Only ASCII `A-Z` is folded to lowercase — accented uppercase is *not* folded.
  Linguistically imperfect, but it only has to match the Python side, and it does
  (`fastgeo_py.py:121` ↔ `simhash.cpp:29`).
- **No wrapper Python package**: `CMakeLists.txt`'s `install(TARGETS fastgeo LIBRARY DESTINATION .)`
  plus `wheel.packages = []` put the `.so` at the wheel root, so `import fastgeo` resolves straight
  to the extension module.
- **Self-intersecting rings are unvalidated** — both implementations assume simple rings; behavior on
  a self-intersecting ring is whatever even/odd ray-casting happens to produce. Fine for AGEB
  polygons.

## Building it

```sh
python3 -m venv .venv-native && source .venv-native/bin/activate
pip install pybind11 cmake ninja scikit-build-core pytest numpy
pip install ./pipeline/native          # CMake >= 3.24 via scikit-build-core
cd pipeline && python3 -m pytest tests/test_parity.py -v
```

---

## See also

- ↑ [[ARCHITECTURE]] · [[RUNTIME]]
- [[overview]] · [[pipeline]] · [[contracts]] · [[query-engine]] · [[web-app]]
- Reference: [[dev-notes]] (benchmarks, the FMA bug write-up) · [[TESTING]]
- ↩ [[overview]]

---
aliases: [C++ / Native]
tags: [convention]
---

# C++ / Native

`pipeline/native/` — the `fastgeo` extension module. **C++17**, **pybind11**,
built by **scikit-build-core** via **CMake >= 3.24**, installed with
`pip install ./pipeline/native`. Optional at runtime: the pipeline falls back to
pure Python when it isn't installed (see [[python-style]], [[fastgeo]]).

## Build settings

`CMakeLists.txt`, in full-force form:

- `CMAKE_CXX_STANDARD 17`, `CXX_STANDARD_REQUIRED ON`, `CXX_EXTENSIONS OFF`.
- Build type defaults to `Release` (also pinned in `pyproject.toml` under
  `[tool.scikit-build.cmake.define]`).
- Flags: `-O3 -Wall -Wextra **-ffp-contract=off**` on non-MSVC; `/O2 /W4` on
  MSVC.
- `pybind11_add_module(fastgeo bindings.cpp fastgeo/geo.cpp fastgeo/simhash.cpp)`,
  installed straight into the wheel root (`wheel.packages = []`) so
  `import fastgeo` resolves to the extension directly — no wrapper package.

## `-ffp-contract=off` is load-bearing

Do not remove it. Do not add `-ffast-math`, `-Ofast`, or any other
fast-math-adjacent flag.

`-O3` on FMA-capable hardware (Apple Silicon arm64, AppleClang) fuses the
multiply-add/subtract chains in the boundary cross-product and the ray/edge
intersection formula into a single FMA instruction with one rounding step. That
disagrees in the last bit with Python's strictly-separate IEEE754 ops, and it
**breaks boundary-point parity** — sparse, boundary-only failures that cost an
evening to localize (the full story is in [[dev-notes]]). MSVC doesn't contract
by default, hence no equivalent flag there.

Related invariant: **boundary semantics are exact and epsilon-free** —
cross-product `== 0.0` plus a bbox test. An epsilon tolerance would just move
the cross-language disagreement to the epsilon boundary instead of removing it.

## The Python reference is the spec

`pipeline/native/fallback/fastgeo_py.py` is **normative**. Its own docstring
says so: *"This module is the spec."* Any disagreement between the compiled
module and the reference is a **`fastgeo` bug, never a reference bug.** Fix the
C++.

If you genuinely need to change the semantics, change the reference *first*,
deliberately, and then make C++ match — never the other way around.

## Every API change lands in three places

The API is small and fixed ([[contracts]]):

```
point_in_polygon(lat, lng, ring) -> bool
batch_assign(points, polygons: dict[str, ring]) -> list[str | None]
haversine_matrix(points_a, points_b) -> list[list[float]]   # meters
simhash64(text) -> int
hamming(a, b) -> int
```

Touching it means editing **all three** in the same commit:

1. `pipeline/native/fastgeo/geo.cpp` / `simhash.cpp` (+ the matching `.hpp`)
2. `pipeline/native/bindings.cpp` (the pybind11 surface)
3. `pipeline/native/fallback/fastgeo_py.py` (the reference)

…and then the parity suite must stay green. A change in two of the three is a
broken change.

## Parity suite

```sh
python3 -m venv .venv-native && source .venv-native/bin/activate
pip install pybind11 cmake ninja scikit-build-core pytest numpy
pip install ./pipeline/native
cd pipeline && python3 -m pytest tests/test_parity.py -v    # 13 passed
```

`pipeline/tests/test_parity.py` (fixed seed `20260710`) compares compiled vs.
reference over random simple polygons, **every vertex, every edge midpoint and a
random point per edge**, degenerate rings (empty / single / two-vertex /
all-identical / collinear / self-closing), `batch_assign` edge cases,
`haversine_matrix`, and `simhash64`/`hamming` on Spanish listing text. It
`importorskip`s when the extension isn't built, and skips under
`FASTGEO_FORCE_FALLBACK=1` (nothing to compare). CI runs it in the
`native-build` job.

## Implementation notes to preserve

- **`simhash64`** — FNV-1a 64-bit over a byte-level tokenizer; bytes `>= 0x80`
  count as word bytes so accented Spanish stays a single token without pulling
  in a Unicode library. It only needs to match the Python side, and it does.
- **`batch_assign` polygon order** follows Python dict insertion order — the
  binding walks the `py::dict` directly. Don't reorder or sort.
- **No spatial index** in either implementation; `batch_assign` is brute-force
  O(points × polygons) by design. `enrich.py` pre-filters instead.
- **Self-intersecting rings are unvalidated** — simple rings are assumed.

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- [[typescript-style]] · [[python-style]] · [[styling-system]] · [[git-and-pr]]
- ↩ [[Home]]

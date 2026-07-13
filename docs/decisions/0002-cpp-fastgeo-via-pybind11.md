---
aliases: [0002 C++ fastgeo via pybind11]
tags: [adr]
---

# 0002, Write the spatial hot loops in C++ behind pybind11

## Status

accepted

## Context

`enrich.py` has to assign every listing to its containing INEGI AGEB polygon:
100k listings against ~2,400 CDMX polygons, brute-force point-in-polygon. The
first pure-Python `batch_assign` run took long enough that it looked hung before
it turned out to just be working, slowly. Measured properly on a fixed-seed
fixture (seed `20260710`, 100,000 points × 2,000 polygons, both implementations
confirmed to match the same 6,673/100,000 assignments):

| implementation | elapsed |
|---|---|
| compiled `fastgeo` | 2.19 s |
| pure-Python fallback | 247.32 s (4 min 7 s) |

**~113x.** Apples-to-apples — same brute-force O(points × polygons) search, no
spatial index on either side. But requiring a C++ toolchain to clone and run the
repo is a real cost: a visitor should be able to `npm ci && npm run dev` and get
a working app.

## Decision

Write `fastgeo` as a C++17 pybind11 extension (`pipeline/native/`), and keep a
pure-Python implementation of the **identical API** at
`pipeline/native/fallback/fastgeo_py.py`. `pipeline/geo_backend.py` is the single
chokepoint resolving which one the pipeline gets: compiled if importable,
fallback otherwise, with `FASTGEO_FORCE_FALLBACK=1` to force the Python path.

The fallback is the **spec**, not a degraded copy. Any disagreement is a
`fastgeo` bug, never a reference bug.

## Consequences

Easier: the pipeline runs with no C++ toolchain at all — CI's `pipeline-test`
job never builds the extension and still passes (51 passed, 1 skipped). The
real-workload wins are smaller than the raw benchmark but real: `dedupe.py`
over 100,000 rows goes 22.5s → 5.3s (~4.3x), while `enrich.py`'s full
50,314-row CDMX run is 1.5s → 0.9s only because it pre-filters candidates by
municipio and bbox before ever calling in.

Harder, and permanently so:

- **A parity suite is now mandatory.** `pipeline/tests/test_parity.py` (13
  tests) compares the two implementations on random polygons, every vertex and
  edge midpoint, degenerate rings, and simhash over Spanish text. It is the
  only thing keeping the two from drifting.
- **Every API change lands in three places** — the C++ source, the pybind11
  binding, and the Python fallback — or parity breaks.
- Boundary semantics have to be bit-exact across two languages, which is its
  own problem (see [[0003-fp-contract-off-for-parity|0003]]).

---

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
- [[fastgeo]] · [[pipeline]] · [[contracts]] · [[TESTING]] · [[dev-notes]]
- ↩ [[Home]]

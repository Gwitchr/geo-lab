---
aliases: [Diagnose a parity failure]
tags: [workflow]
---

# Diagnose a fastgeo parity failure

`pipeline/tests/test_parity.py` asserts that the compiled C++ `fastgeo` agrees
with the pure-Python reference on every API call. When it goes red, work this
list in order — the causes are ranked by how often they are actually the
problem.

**Rule zero: `pipeline/native/fallback/fastgeo_py.py` is the spec.** A parity
failure is a `fastgeo` bug, never a reference bug. Do not "fix" it by changing the
fallback, loosening an assertion, or adding an epsilon — boundary semantics are
deliberately exact and epsilon-free (cross-product `== 0.0` plus a bbox test), and
an epsilon just moves the disagreement to the epsilon boundary.

## 1. Reproduce

```sh
cd pipeline
python3 -m pytest tests/test_parity.py -v          # expected: 13 passed
python3 -m pytest tests/test_parity.py -x --tb=long -k point_in_polygon
```

The suite is seeded (`SEED = 20260710` in `tests/test_parity.py`), so the
corpora — 20 random simple rings, the degenerate rings, 60 listing-style texts —
and therefore the failing ring/point are identical on every run. The assertion
carries the repro with it: `assert native_result == ref_result, (lat, lng, ring)`.
Copy that tuple out of the traceback.

## 2. Suspect FP contraction first

This is the real historical bug and it will be the first thing to check
forever. `-O3` on Clang/GCC targeting FMA hardware (arm64 / Apple Silicon)
fuses multiply-add chains — the boundary cross-product and the ray/edge
intersection formula — into a single FMA instruction with **one** rounding
step, where Python performs strictly separate IEEE754 operations. The results
differ in the last bit, which is invisible everywhere except exactly on a
polygon boundary. Symptom: sparse, boundary-only failures in
`test_point_in_polygon_boundary_points_agree` that look random.

The fix is already in `pipeline/native/CMakeLists.txt`:

```cmake
target_compile_options(fastgeo PRIVATE
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-O3 -Wall -Wextra -ffp-contract=off>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /W4>
)
```

Check, in this order: (1) is `-ffp-contract=off` still there, and did someone add
`-ffast-math` / `-Ofast` / `-march=native` that re-enables contraction? (2) are
you running a genuinely **rebuilt** module, not a stale `.so`? (3) is this a new
compiler/platform — MSVC does not contract by default and needs no flag, anything
non-MSVC must carry it.

```sh
pip uninstall -y fastgeo && pip install --no-cache-dir ./pipeline/native
cd pipeline && python3 -m pytest tests/test_parity.py -q
```

## 3. Check boundary points and degenerate rings

If the flag is intact, isolate the geometry. Vertices are the hard invariant:
a ring's own vertex is algebraically on its edges (the cross product reduces to
`0 * k`), so both implementations **must** call it inside —
`test_point_in_polygon_vertices_are_always_inside` asserts exactly that, with no
tolerance.

```sh
cd pipeline
python3 - <<'PY'
import fastgeo
from native.fallback import fastgeo_py as ref

ring = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]   # or paste the failing ring
pts = list(ring)                                          # vertices
pts += [((a[0]+b[0])/2.0, (a[1]+b[1])/2.0)                # edge midpoints
        for a, b in zip(ring, ring[1:] + ring[:1])]
for lat, lng in pts:
    n, r = fastgeo.point_in_polygon(lat, lng, ring), ref.point_in_polygon(lat, lng, ring)
    if n != r:
        print("DISAGREE", lat.hex(), lng.hex(), n, r)
PY
```

`float.hex()` is the point — a last-bit difference is unreadable in decimal.

Then the degenerate cases (`DEGENERATE_RINGS`): empty ring, single vertex, two
vertices, all-identical vertices, collinear vertices, explicit closing vertex.
Contract: fewer than 3 vertices has no area and returns `False`; rings are
implicitly closed, so a duplicated final vertex must not change the answer. A C++
loop that reads `ring[i+1]` without wrapping breaks here and nowhere else.

## 4. Check `batch_assign` polygon iteration order

`batch_assign` returns the **first** polygon containing the point, where "first"
means **Python dict insertion order**. The fallback does
`items = list(polygons.items())` and breaks on the first hit; `bindings.cpp`
deliberately copies the `py::dict` into an order-preserving
`std::vector<std::pair<std::string, Ring>>` for exactly this reason. Any
`std::unordered_map` / `std::map` / sort introduced into that path silently
changes which polygon wins for a point inside two overlapping rings — and nothing
else. Symptom: `test_batch_assign_random_agrees` fails while every
`point_in_polygon` test passes. AGEB polygons rarely overlap, so this never shows
up in `enrich.py` output; the suite is the only thing that catches it.

## 5. Interpret the failure type correctly

- `point_in_polygon` / `batch_assign` / `simhash64` / `hamming` — booleans and
  integers, compared for **exact** equality. Any mismatch is a real bug.
- `haversine_matrix` — floats, compared with `rel_tol=1e-9`, `abs_tol=1e-6` m,
  since libm's `sin`/`cos`/`atan2` may round differently between the two call
  paths. Exceeding that tolerance is still a bug, but it is not the FMA story.
- `simhash64` — FNV-1a 64-bit, byte-level tokenizer, bytes `>= 0x80` counted as
  word bytes so accented Spanish stays one token. A C++ side that treats UTF-8
  continuation bytes as separators diverges on exactly the accented texts.

## 6. Verify the fix

```sh
cd pipeline
python3 -m pytest tests/test_parity.py -v                     # 13 passed
python3 -m pytest -q                                          # 64 passed
FASTGEO_FORCE_FALLBACK=1 python3 -m pytest -q                 # 51 passed, 1 skipped
```

The last one skips the parity module on purpose (nothing to compare against).
Then re-run the real workload both ways and confirm the enrichment is identical:

```sh
python3 pipeline/enrich.py                            # CDMX listings: 50314 / assigned: 50297 (99.97%)
FASTGEO_FORCE_FALLBACK=1 python3 pipeline/enrich.py   # same two lines
```

Build details and the `FASTGEO_FORCE_FALLBACK` chokepoint: [[build-fastgeo]].
The original evening lost to FP contraction is written up in [[dev-notes]].

---

## See also

- ↑ [[ENGINEERING]] · [[TESTING]]
- [[fastgeo]] · [[contracts]] · [[dev-notes]] · [[pipeline]]
- [[build-fastgeo]] · [[regenerate-data]] · [[add-a-filter-field]] · [[add-a-region]]
- ↩ [[Home]]

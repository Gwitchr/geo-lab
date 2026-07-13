---
aliases: [Build fastgeo]
tags: [workflow]
---

# Build fastgeo (the optional C++ module)

`fastgeo` is a C++17/pybind11 extension for the spatial hot loops
(point-in-polygon AGEB assignment, simhash near-duplicate detection). It is
**optional**. Everything in this repo — the full pipeline, the whole pytest
suite, CI's `pipeline-test` job — works without a C++ toolchain, because
`pipeline/geo_backend.py` falls back to a pure-Python implementation.

Build it when you want the speed (`dedupe.py`: 5.3s compiled vs. 22.5s fallback
on the full 100k-row run; raw `batch_assign` benchmark: ~113x) or when you are
changing `pipeline/native/` and need the parity suite to actually run.

## The fallback is automatic

`pipeline/geo_backend.py` is the single import chokepoint every consumer goes
through:

```python
if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    from native.fallback import fastgeo_py as fastgeo
else:
    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo
```

No compiled module, no error — you get `pipeline/native/fallback/fastgeo_py.py`,
which is the **reference implementation and the spec**. Same five functions
either way: `point_in_polygon`, `batch_assign`, `haversine_matrix`, `simhash64`,
`hamming`.

## 1. Build and install

From the repo root, in its own venv (keep it separate from `.venv-pipeline` so
you can test both backends):

```sh
python3 -m venv .venv-native && source .venv-native/bin/activate
pip install pybind11 cmake ninja scikit-build-core pytest numpy
pip install ./pipeline/native
```

That last line runs the CMake build (`pipeline/native/CMakeLists.txt`, CMake
≥ 3.24, Python ≥ 3.11) via scikit-build-core and installs the wheel. Expected
output, roughly:

```
*** Configuring CMake...
-- The CXX compiler identification is AppleClang 21.0.0.21000101
-- Found pybind11: .../pybind11/include (found version "3.0.4")
*** Building project with Ninja...
[4/4] Linking CXX shared module fastgeo.cpython-313-darwin.so
*** Created fastgeo-0.1.0-cp313-cp313-macosx_26_0_arm64.whl
Successfully installed fastgeo-0.1.0
```

The module installs at the wheel root, so `import fastgeo` finds it as a
top-level extension — no wrapper package.

## 2. Run the parity suite

```sh
cd pipeline && python3 -m pytest tests/test_parity.py -v
```

Expected: **13 passed**. This is the whole point of the build — every call must
agree with the pure-Python reference: random polygons, boundary points (every
vertex, every edge midpoint, a random interpolation point per edge), degenerate
rings, `batch_assign` edge cases, `haversine_matrix`, `simhash64`/`hamming` on
Spanish listing text. Fixed seed `20260710`.

If it fails, go to [[diagnose-parity-failure]] — a parity failure is a `fastgeo`
bug, never a reference bug.

Full suite with the module present:

```sh
cd pipeline && python3 -m pytest -q     # 64 passed
```

## 3. Verify both backends agree

`FASTGEO_FORCE_FALLBACK=1` forces the pure-Python path even when the compiled
module is installed. That is how you check the fallback still does the same
thing:

```sh
cd pipeline && FASTGEO_FORCE_FALLBACK=1 python3 -m pytest -q
```

Expected: **51 passed, 1 skipped**. The skip is `test_parity.py` itself, by
design — with the fallback forced there is nothing to compare against (both
sides would be the same module), so it skips at module level with
`allow_module_level=True`.

The real end-to-end check is running the pipeline both ways and diffing the
result:

```sh
python3 pipeline/enrich.py                              # compiled
python3 pipeline/stats.py --out /tmp/stats-compiled.json

FASTGEO_FORCE_FALLBACK=1 python3 pipeline/enrich.py     # pure Python
python3 pipeline/stats.py --out /tmp/stats-fallback.json

diff /tmp/stats-compiled.json /tmp/stats-fallback.json  # only generated_at should differ
```

Both must produce the same `ageb_id` / `marginacion_grade` / `marginacion_index`
on all 100,000 rows, and the same `CDMX listings: 50314 / assigned to an AGEB:
50297 (99.97%)` line. (`stats.json` carries a `generated_at` timestamp, so that
one line always differs.)

## Notes

- **`-ffp-contract=off` in `CMakeLists.txt` is load-bearing.** Do not remove it,
  do not add `-ffast-math`. It is what keeps boundary-point parity on FMA
  hardware — see [[diagnose-parity-failure]].
- CI's `pipeline-test` job never builds the extension (`test_parity.py` skips
  itself cleanly via `pytest.importorskip`); the separate `native-build` job does
  the `pip install ./pipeline/native` + parity run above.
- `data/gen/gen_listings.py` deliberately does **not** import `fastgeo` or
  `geo_backend` — it has its own ray-casting helpers, so the generator never
  depends on the thing it generates fixtures for.

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- [[fastgeo]] · [[contracts]] · [[pipeline]] · [[dev-notes]]
- [[diagnose-parity-failure]] · [[regenerate-data]] · [[add-a-filter-field]] · [[add-a-region]]
- ↩ [[Home]]

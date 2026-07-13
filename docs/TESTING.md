---
aliases: [Testing, TESTING]
tags: [moc]
---

# Testing

Three runners, one philosophy: test the behavior at the boundary, and for anything with two
implementations, test that they **agree**. The parity suite is the load-bearing one — it is
the only reason a C++ rewrite of the spatial hot path is safe to depend on.

---

## Runners and counts

| Suite | Runner | Where | Count |
|---|---|---|---|
| Web | vitest + jsdom | `web/src/__tests__/` | 25 |
| CLI | vitest | `cli/src/__tests__/` | 89 |
| Pipeline | pytest | `pipeline/tests/` | 64 (51 + 13 parity) |
| Parity | pytest | `pipeline/tests/test_parity.py` | 13 |

CLI breakdown: `lexer` 14 · `parser` 18 · `eval` 12 · `golden` 13 · `commands` 19 · `cli` 13.

Without a compiled `fastgeo`, the pipeline suite reports **51 passed, 1 skipped** — the
parity module `pytest.importorskip`s itself. That skip is by design: with no compiled
extension there are not two implementations to compare.

## Co-location

Tests live beside the code they cover — `cli/src/__tests__/`, `web/src/__tests__/`,
`pipeline/tests/`. `cli/` type-checks its tests separately (`tsconfig.test.json`, run in CI
as its own `tsc --noEmit`) because `tsconfig.json` excludes them from the build.

## Behavior over implementation

- **The CLI's `golden.test.ts`** pins whole `expr → SQL + params` outputs. If a refactor
  changes the generated SQL text, that's a deliberate decision, not a passing test.
- **Fixtures, not the real database.** `cli/src/__tests__/fixtures/fixtureDb.ts` builds an
  in-memory sqlite with the same schema. Keep it in sync when a column is added
  ([[add-a-filter-field]]).
- **The web tests exercise `data.ts` and `charts.ts` directly** (filtering, sorting,
  bucketing) — pure functions over listing arrays, no DOM theatrics. They pass explicit URLs
  to `loadListings()`, so the `import.meta.env.BASE_URL` default is not what they cover.
- **The pipeline tests run the real scripts** against generated fixtures. `clean.py`'s drop
  reasons and `dedupe.py`'s thresholds are asserted against the generator's own ground truth,
  which is what makes the "750 dropped, zero false drops" claim checkable rather than
  anecdotal.

## Mocking

Essentially none, and that's deliberate: there is no network, no server, no auth provider,
no clock dependency worth faking. `jsdom` supplies a DOM for the web suite; sqlite runs in
memory for the CLI suite. If you find yourself reaching for a mock, ask whether the seam is
in the wrong place first.

## The parity suite

`pipeline/tests/test_parity.py`, fixed seed `20260710`. It asserts the compiled `fastgeo`
and the pure-Python `fallback/fastgeo_py.py` agree **exactly** — no epsilon — across:

- random simple polygons;
- **boundary points**: every vertex, every edge midpoint, a random interpolation per edge;
- degenerate rings: empty, single-vertex, two-vertex, all-identical, collinear, self-closing;
- `batch_assign` edge cases (polygon iteration order must follow Python dict insertion order);
- `haversine_matrix` on random and identical points;
- `simhash64` / `hamming` over Spanish listing-style text.

**The fallback is the spec.** A parity failure is a `fastgeo` bug, never a reference bug.
The historical failure was floating-point contraction, not logic — see
[[0003-fp-contract-off-for-parity]] and the debugging recipe in [[diagnose-parity-failure]].

Run it both ways:

```sh
cd pipeline
python3 -m pytest tests/test_parity.py -v          # compiled vs. Python
FASTGEO_FORCE_FALLBACK=1 python3 -m pytest -q      # whole suite on the pure-Python path
```

## Coverage

No coverage threshold is enforced, and no coverage tool is wired up. The bar is behavioral:
**the four CI jobs green, the parity suite green both ways, and the README quickstart working
verbatim from a fresh clone.** See [[data-integrity]] for the numeric invariants a change
must not move.

---

## See also

- ↑ [[ENGINEERING]] · [[RUNTIME]]
- [[diagnose-parity-failure]] · [[build-fastgeo]] · [[add-a-filter-field]]
- [[fastgeo]] · [[query-engine]] · [[pipeline]] · [[contracts]]
- [[data-integrity]] · [[dev-notes]]
- ↩ [[Home]]

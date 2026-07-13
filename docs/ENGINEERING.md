---
aliases: [Engineering, ENGINEERING]
tags: [moc, convention]
---

# Engineering

Three toolchains, one standing bias: **don't add a dependency for something this small.**
No UI framework, no chart library, no parser library, no ORM, no CSS framework. The
dependency list is `leaflet`, `better-sqlite3`, `pybind11` — and that's the whole of it.

---

## Daily commands

```sh
# web
cd web && npm ci && npm run dev     # test: npm test · lint: npm run lint · build: npm run build

# cli
cd cli && npm ci && npm test        # dev run: npm run dev -- query "…" --db ../data/db.sqlite

# pipeline
python3 -m venv .venv-pipeline && source .venv-pipeline/bin/activate
pip install pytest && cd pipeline && python3 -m pytest -q

# native (optional — the pipeline falls back to pure Python without it)
pip install ./pipeline/native && cd pipeline && python3 -m pytest tests/test_parity.py
```

## Language rules

| Area | Rule | Detail |
|---|---|---|
| TypeScript | Pinned to `^6.0.3` in **both** packages | [[typescript-style]] |
| Python | stdlib + `sqlite3` only; pytest is the only dev dep | [[python-style]] |
| C++ | C++17, `-O3` **and `-ffp-contract=off`** (load-bearing) | [[cpp-native]] |
| CSS | Custom properties in `:root`, no framework, no preprocessor | [[styling-system]] |

Lint exists only in `web/` (`eslint`, flat config). `cli/` has no lint script — a deliberate
choice, `test` and `build` cover it. Both TS packages are `strict`; `cli/` additionally sets
`noUncheckedIndexedAccess`.

## Git and PR

Single-author personal repo, work lands on `main`. Commit subjects are lowercase
`area: summary` (`web:`, `ci:`, `readme:`, `notes:`). Full rules: [[git-and-pr]].

**Committed build artifacts.** `data/db.sqlite` and `web/public/listings.json` are checked in
on purpose ([[0004-commit-built-artifacts]]) — when the pipeline changes, regenerate **and
re-commit** them, or a fresh clone silently serves stale data.

## CI

Four jobs, all must be green (`.github/workflows/ci.yml`): `web-test`, `cli-test`,
`pipeline-test`, `native-build`. `pipeline-test` never builds the C++ extension — the parity
suite `importorskip`s itself cleanly, which is exactly what makes the fallback path a
first-class citizen rather than an afterthought. See [[RUNTIME]] and [[TESTING]].

Pages deploys from `main` via `.github/workflows/pages.yml`.

## The non-negotiables

These are the things that quietly break if you're not paying attention:

1. **`gen_listings.py` output stays byte-identical** for the committed seed.
2. **The parity suite passes both ways** — compiled, and under `FASTGEO_FORCE_FALLBACK=1`.
3. **Never add `-ffast-math`** or remove `-ffp-contract=off` ([[0003-fp-contract-off-for-parity]]).
4. **The pure-Python fallback is the spec.** A parity failure is a `fastgeo` bug, never a
   reference bug.
5. **All fastgeo access goes through `pipeline/geo_backend.py`.** Never `import fastgeo`
   directly in pipeline code.
6. **SQL values are always bound `?` parameters**, never interpolated ([[security]]).
7. **The README quickstart works verbatim from a fresh clone.** It's been simulated; keep it
   true.
8. **No secrets, no machine-local absolute paths** in committed files.
9. **Never label synthetic data as INEGI/CONAPO-sourced** ([[data-notes]]).

## Workflows

[[regenerate-data]] · [[add-a-filter-field]] · [[add-a-region]] · [[build-fastgeo]] ·
[[diagnose-parity-failure]]

## Running log

[[dev-notes]] is the author's running log — decisions, benchmarks, calibration tables, and
the mistakes worth not repeating. It's the richest source in the repo for *why* something is
the way it is. Read it before arguing with a design choice.

---

## See also

- ↑ [[RUNTIME]] · [[ARCHITECTURE]]
- [[typescript-style]] · [[python-style]] · [[cpp-native]] · [[styling-system]] · [[git-and-pr]]
- [[TESTING]] · [[DESIGN]] · [[performance]] · [[security]]
- [[Decisions Index]] · [[immediate]] · [[backlog]] · [[dev-notes]]
- ↩ [[Home]]

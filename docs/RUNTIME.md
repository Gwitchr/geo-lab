---
aliases: [Runtime, RUNTIME]
tags: [moc]
---

# Runtime

Four independently-runnable pieces, three toolchains, no server. Everything runs locally;
the only deployed artifact is a static page on GitHub Pages.

---

## Stack

| Piece | Language / runtime | Key deps | Tests |
|---|---|---|---|
| `web/` | TypeScript 6.x, Vite 8 | `leaflet` (only runtime dep) | vitest + jsdom (25 tests) |
| `cli/` | TypeScript 6.x, Node ≥ 20 | `better-sqlite3` (only runtime dep) | vitest (89 tests) |
| `pipeline/` | Python ≥ 3.11 | **stdlib + sqlite3 only** | pytest (64 tests, 51 without fastgeo) |
| `pipeline/native/` | C++17, pybind11, CMake ≥ 3.24 | scikit-build-core | pytest parity suite (13 tests) |

TypeScript is pinned to `^6.0.3` in **both** `web/` and `cli/` — `typescript-eslint`'s peer
range excludes TS 7. Don't bump one without the other ([[typescript-style]]).

## Services

None. No database server (sqlite file), no API server, no auth provider, no queue, no cache.
See [[AUTH]].

## Environment variables

Exactly one, and it's a debug switch:

| Var | Values | Effect |
|---|---|---|
| `FASTGEO_FORCE_FALLBACK` | `1` | Forces `pipeline/geo_backend.py` to import the pure-Python reference instead of the compiled extension. Used to verify both backends agree. |

There is no `.env` file in this repo and there are no secrets. Never read `.env` /
`.env.local` with agent tools.

## Local setup

`data/db.sqlite` (~45.65 MB, 100,000 rows) and `web/public/listings.json` (5,000 rows) are
**committed build artifacts** ([[0004-commit-built-artifacts]]), so both the web app and the
CLI work straight off a clone with **no Python setup at all**.

```sh
# Web explorer
cd web && npm ci && npm run dev        # http://localhost:5173

# CLI
cd cli && npm ci && npm run build
node dist/index.js query "price<2500000 and colonia:roma" --db ../data/db.sqlite
```

Rebuilding the data is optional and only needed when touching the pipeline — see
[[regenerate-data]]. Building the C++ module is also optional; the pipeline falls back to
pure Python automatically — see [[build-fastgeo]].

## Commands

| Where | Command | What |
|---|---|---|
| `web/` | `npm run dev` | Vite dev server, port 5173 |
| `web/` | `npm run build` | `tsc --noEmit` + `vite build` → `web/dist/` |
| `web/` | `npm test` / `npm run lint` | vitest / eslint |
| `cli/` | `npm run dev -- query "…" --db ../data/db.sqlite` | run TS directly via `tsx` |
| `cli/` | `npm run build` | `tsc` → `cli/dist/`, entry `dist/index.js` |
| `cli/` | `npm test` | vitest (no lint script by choice) |
| repo root | `python3 pipeline/<script>.py` | ingest / enrich / stats / export_web |
| `pipeline/` | `python3 -m pytest -q` | full suite; parity tests skip cleanly with no fastgeo |

`geoq`'s `--db` resolves against `process.cwd()` — run from the repo root or pass `--db`
explicitly. There is no repo-root auto-detection ([[immediate]]).

## Deploy target

**GitHub Pages**, project page at `/geo-lab/`. `.github/workflows/pages.yml` builds `web/`
on every push to `main` and deploys via `actions/deploy-pages`. Because the site is served
from a subpath, `web/vite.config.ts` sets `base: "/geo-lab/"` for production builds only
(dev stays at `/`), and asset URLs in code must go through `import.meta.env.BASE_URL` — see
[[contracts]].

Nothing else deploys. The CLI and pipeline are local-only.

## CI

`.github/workflows/ci.yml`, four jobs on push to `main` and every PR:

| Job | Runs |
|---|---|
| `web-test` | `npm ci` → lint → test → build |
| `cli-test` | `npm ci` → `tsc --noEmit` (src + tests) → test → build |
| `pipeline-test` | `pip install pytest` → `pytest -q` (never builds fastgeo; parity tests `importorskip` cleanly) |
| `native-build` | builds the fastgeo wheel → runs the parity suite against the compiled module |

No Actions run has actually been watched yet — every job's steps were verified locally on
macOS arm64 instead of `ubuntu-latest` ([[immediate]]).

---

## See also

- ↑ [[PRODUCT]]
- [[ARCHITECTURE]] · [[ENGINEERING]] · [[TESTING]] · [[AUTH]]
- [[overview]] · [[contracts]] · [[fastgeo]]
- [[regenerate-data]] · [[build-fastgeo]] · [[performance]] · [[security]]
- ↩ [[Home]]

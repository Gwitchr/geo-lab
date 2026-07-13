# AGENTS.md

Entry point for any AI agent (Claude, Cursor, Aider, Copilot, …) working in this repo.

## Read this first

`docs/` is an Obsidian vault. Eight flat top-level domain docs, read in order:

| # | Domain | File | What it covers |
|---|--------|------|----------------|
| 1 | Product | [docs/PRODUCT.md](docs/PRODUCT.md) | What geo-lab is, audiences, the three surfaces, domain glossary, roadmap |
| 2 | Runtime | [docs/RUNTIME.md](docs/RUNTIME.md) | Stack, commands, the one env var, local setup, Pages deploy, CI |
| 3 | Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Code layout, dataflow, state and ownership boundaries |
| 4 | Data | [docs/DATA.md](docs/DATA.md) | SQLite, the `listings` schema, pipeline layers, real-vs-synthetic provenance |
| 5 | Auth | [docs/AUTH.md](docs/AUTH.md) | **There is none** — and the trust boundaries that exist anyway |
| 6 | Engineering | [docs/ENGINEERING.md](docs/ENGINEERING.md) | Language rules, CI, the non-negotiables |
| 7 | Testing | [docs/TESTING.md](docs/TESTING.md) | Three runners, and why the fastgeo parity suite is load-bearing |
| 8 | Design | [docs/DESIGN.md](docs/DESIGN.md) | Tokens, type scale, components (spec-compliant `design.md`) |

Deeper folder docs hang off each: `docs/architecture/`, `docs/conventions/`,
`docs/workflows/`, `docs/quality/`, `docs/decisions/`, `docs/upgrades/`.
Index: [docs/README.md](docs/README.md) · Obsidian MOC: [docs/Home.md](docs/Home.md).

**`docs/dev-notes.md` is the richest "why" source in the repo** — the author's running log of
decisions, benchmarks, calibration tables, and the mistakes worth not repeating. Read it
before arguing with a design choice.

## Open as an Obsidian vault

`docs/` is a real vault. Obsidian → **Open folder as vault** → pick `docs/`. `.obsidian/` is
committed (graph colour groups by tag, backlinks, bookmarks).

## Stack at a glance

Four pieces, three toolchains, no server. A **Python 3.11+ pipeline** (stdlib + sqlite3 only)
builds `data/db.sqlite` from synthetic listings; a **TypeScript CLI** (`geoq`, better-sqlite3)
queries it through a hand-written filter language; a **Vite + TypeScript web explorer** (no UI
framework, no chart library) reads a 5,000-row JSON export and renders a table, hand-rolled
SVG charts, and a Leaflet map; and **`fastgeo`**, a C++17/pybind11 module, carries the spatial
hot loops with a pure-Python fallback of identical API.

Standing bias: **don't add a dependency for something this small.** The entire dependency list
is `leaflet`, `better-sqlite3`, `pybind11`.

## The non-negotiables

1. **`data/gen/gen_listings.py` output stays byte-identical** for the committed seed.
2. **The fastgeo parity suite passes both ways** — compiled, and under `FASTGEO_FORCE_FALLBACK=1`.
3. **`pipeline/native/fallback/fastgeo_py.py` is the spec.** A parity failure is a `fastgeo`
   bug, never a reference bug.
4. **Never remove `-ffp-contract=off` from `pipeline/native/CMakeLists.txt`, never add
   `-ffast-math`.** FMA contraction on arm64 breaks boundary-point parity. This cost an
   evening once — see [docs/decisions/0003-fp-contract-off-for-parity.md](docs/decisions/0003-fp-contract-off-for-parity.md).
5. **All fastgeo access goes through `pipeline/geo_backend.py`.** Never `import fastgeo`
   directly in pipeline code.
6. **SQL values are always bound `?` parameters, never interpolated.** Identifiers come from
   allowlists. See [docs/quality/security.md](docs/quality/security.md).
7. **The README quickstart works verbatim from a fresh clone.** It has been simulated. Keep it
   true.
8. **`data/db.sqlite` and `web/public/listings.json` are committed build artifacts** — when the
   pipeline changes, regenerate *and re-commit* them, or a fresh clone serves stale data.
9. **Never label synthetic data as INEGI/CONAPO-sourced.** `data/raw/` and `data/db.sqlite` are
   generated; only `data/geo/` is real open data. See [docs/data-notes.md](docs/data-notes.md).
10. **No secrets, no machine-local absolute paths** in committed files. There is no `.env` and
    none is expected — don't read `.env` / `.env.local` with agent tools.

## Where things live

```
web/       Vite + TypeScript explorer   (src/main.ts · data.ts · charts.ts · map.ts)
cli/       geoq                          (src/cli.ts · commands/ · parser/{lexer,parser,eval}.ts)
pipeline/  Python data pipeline          (ingest · clean · dedupe · enrich · stats · export_web)
           geo_backend.py                the fastgeo import chokepoint
pipeline/native/  fastgeo C++17          (fastgeo/*.cpp · bindings.cpp · fallback/fastgeo_py.py)
data/      gen/ (generator) · raw/ (CSVs) · geo/ (real open data) · db.sqlite (artifact)
docs/      this vault
```

## Local commands

```bash
cd web && npm ci && npm run dev          # http://localhost:5173 · test · lint · build
cd cli && npm ci && npm test             # npm run dev -- query "…" --db ../data/db.sqlite
cd pipeline && python3 -m pytest -q      # stdlib only; pip install pytest
pip install ./pipeline/native            # optional C++ build — everything works without it
```

CI runs four jobs on every push and PR: `web-test`, `cli-test`, `pipeline-test`,
`native-build`. All four must be green.

## Skills

Inventory: [`skills-lock.json`](skills-lock.json). Sources under `.agents/skills/<name>/SKILL.md`.

The vault does **not** maintain a separate skills index — domain docs name the skill they
distill inline. Open the relevant `.agents/skills/<name>/SKILL.md` directly when working in
that area.

## See also

- [CLAUDE.md](CLAUDE.md)
- [docs/README.md](docs/README.md) · [docs/Home.md](docs/Home.md)
- [docs/upgrades/immediate.md](docs/upgrades/immediate.md) — what's worth doing next

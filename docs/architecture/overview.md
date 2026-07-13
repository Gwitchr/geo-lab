---
aliases: [Architecture Overview]
tags: [architecture]
---

# Architecture Overview

geo-lab is four separately-owned pieces joined by **file artifacts**, not by APIs or a service
boundary. Nothing calls anything over a network; everything hands off through `data/db.sqlite`,
`web/public/listings.json`, and `pipeline/stats.json`. That is the whole integration story, and
it is why each piece can be built, tested, and run alone.

## The four pieces

| Piece | Lives in | Language / stack | Owns |
|---|---|---|---|
| Data pipeline | `pipeline/`, `data/gen/` | Python 3.11+, **stdlib + sqlite3 only** (pytest to test) | Generating, cleaning, deduping, enriching, and exporting listings |
| `geoq` CLI | `cli/` | TypeScript, `better-sqlite3`, vitest | Querying `data/db.sqlite` through a hand-written filter language |
| Web explorer | `web/` | Vite + TypeScript, Leaflet, **no UI framework, no chart library** | Table / charts / map over the exported JSON slice |
| `fastgeo` | `pipeline/native/` | C++17 + pybind11 (CMake ≥ 3.24, scikit-build-core) | The spatial/text hot loops the pipeline needs |

`fastgeo` is **optional**. `pipeline/geo_backend.py` falls back to the pure-Python reference
(`pipeline/native/fallback/fastgeo_py.py`) when the compiled extension isn't installed, so the
entire pipeline runs with no C++ toolchain present. See [[fastgeo]].

## End-to-end dataflow

```mermaid
graph LR
  gen["data/gen/gen_listings.py<br/>seed 20260101"] --> raw["data/raw/listings_*.csv<br/>4 files, ~100,750 rows"]
  geo["data/geo/agebs_cdmx.geojson<br/>+ marginacion_cdmx.csv"] --> gen
  raw --> ingest["pipeline/ingest.py<br/>clean.py + dedupe.py"]
  ingest --> db[("data/db.sqlite<br/>table listings, 100,000 rows")]
  geo --> enrich["pipeline/enrich.py"]
  db --> enrich
  enrich --> db
  db --> stats["pipeline/stats.py"]
  db --> exportweb["pipeline/export_web.py"]
  db --> geoq["cli/ geoq<br/>query · stats · export"]
  stats --> statsjson["pipeline/stats.json"]
  exportweb --> listingsjson["web/public/listings.json<br/>capped at 5,000"]
  listingsjson --> web["web/ explorer<br/>table · charts · map"]
  fastgeo["fastgeo (C++17)<br/>or pure-Python fallback"] -. via pipeline/geo_backend.py .-> ingest
  fastgeo -. via pipeline/geo_backend.py .-> enrich
```

Concretely, the full rebuild (from `README.md`'s optional section):

```sh
python3 data/gen/gen_listings.py    # -> data/raw/listings_*.csv
python3 pipeline/ingest.py          # -> data/db.sqlite (clean + dedupe inside)
python3 pipeline/enrich.py          # AGEB + marginación for CDMX rows, in place
python3 pipeline/stats.py           # -> pipeline/stats.json
python3 pipeline/export_web.py      # -> web/public/listings.json (5000 cap)
```

Real numbers from that run (`docs/dev-notes.md`): 100,750 raw rows read, 100,000 kept, 750 dropped
(`bad_type` 162, `bad_price` 281, `missing_location` 152, `bad_m2` 155), 2,492 rows flagged as
near-duplicates, 50,314 CDMX rows of which 50,297 (99.97%) got an AGEB, 97,508 non-duplicate
listings across 374 colonias in `stats.json`.

## Ownership boundaries

- **`data/db.sqlite` is the pipeline's output and everyone else's input.** `ingest.py:38` is the
  single place the `listings` schema is declared. `cli/` and `web/` only read; neither ever writes
  to the DB. `geoq` opens it `readonly: true` (`cli/src/db.ts:26`).
- **`pipeline/native/` is owned separately from `pipeline/*.py`.** Pipeline code never imports
  `fastgeo` directly — it goes through `pipeline/geo_backend.py`, the one chokepoint
  (`dedupe.py:33`, `enrich.py:40`). The fallback is the *spec*; the C++ module must match it.
- **`data/gen/gen_listings.py` deliberately does not import `fastgeo`/`geo_backend`** — it has its
  own ray-casting and rejection-sampling helpers, so the generator never depends on the thing it
  generates fixtures to exercise.
- **`web/` and `cli/` do not share code.** They deliberately implement *different* filter languages:
  `geoq`'s is a full lexer/parser/SQL compiler ([[query-engine]]), the browser's is a smaller
  AND-only substring matcher ([[web-app]]). No shared package; duplication is intentional.
- **`dup_of` is a label, not a filter.** All 100,000 cleaned rows stay in `listings`. `stats.py` and
  `export_web.py` exclude `dup_of IS NOT NULL`; `geoq` does **not** — its results and counts still
  include the 2,492 flagged near-duplicates. That asymmetry is deliberate and documented in
  `docs/dev-notes.md`.

## Committed build artifacts

`data/db.sqlite` (~45.65 MB after a VACUUM, 100,000 rows) and `web/public/listings.json` (5,000
rows) are **committed on purpose** so a fresh clone can run the web app and the CLI with zero
Python setup. `.gitignore` deliberately does not ignore them. Regenerating them is optional and
byte-reproducible from `gen_listings.py`'s fixed seed (`SEED = 20260101`).

## Where to go next

- [[pipeline]] — what each script does, the `listings` schema, drop reasons, dedupe calibration.
- [[fastgeo]] — why C++ exists here, the 5-function API, the FMA parity bug.
- [[query-engine]] — `geoq`'s lexer → parser → AST → SQL compiler.
- [[web-app]] — the framework-free explorer and its caps.
- [[contracts]] — the five cross-boundary contracts to change deliberately on all sides.

---

## See also

- ↑ [[ARCHITECTURE]] · [[PRODUCT]] · [[RUNTIME]]
- [[pipeline]] · [[fastgeo]] · [[query-engine]] · [[web-app]] · [[contracts]]
- Reference: [[dev-notes]] · [[data-notes]] · [[filter-language]]
- ↩ [[Home]]

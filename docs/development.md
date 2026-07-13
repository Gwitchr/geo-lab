# Development guide

A personal "geo lab": collect and explore property listings, grow into open-data
geographic analysis (census areas, marginación index, business directory), and
answer questions like "¿dónde en la CDMX funcionaría un concierto mediano?" or how
marginalization maps onto price per m². Mexico is the first region, kept
region-friendly rather than hardcoded. This is the deeper companion to the
repo's [`README.md`](../README.md): layout, component behavior, internal contracts, and the
invariants to keep when changing things.

## Layout

```
geo-lab/
  README.md                  visitor-facing intro, quickstart, roadmap
  LICENSE                    MIT
  web/                       Vite + TypeScript explorer (no UI framework)
    src/main.ts              table + filter box + Tabla/Gráficas/Mapa tabs
    src/data.ts              loads web/public/listings.json, client-side filtering
    src/charts.ts            price histogram, median price/m2 by colonia (plain SVG)
    src/map.ts               Leaflet map, capped/sampled markers
  cli/                       geoq query tool (TypeScript, better-sqlite3)
    src/index.ts             subcommands: query, stats, export; --db path option
    src/parser/lexer.ts      hand-written tokenizer for the filter language
    src/parser/parser.ts     recursive descent -> AST
    src/parser/eval.ts       AST -> SQL WHERE clause with bound parameters
  pipeline/                  Python 3.11+, stdlib + sqlite3 only (pytest to test)
    ingest.py clean.py dedupe.py stats.py enrich.py export_web.py
    geo_backend.py           the fastgeo import chokepoint (see Contracts)
    tests/                   pytest suite incl. test_parity.py for fastgeo
  pipeline/native/           fastgeo C++17 module
    fastgeo/geo.cpp          point_in_polygon, batch_assign, haversine_matrix
    fastgeo/simhash.cpp      simhash64 + hamming
    bindings.cpp             pybind11 module `fastgeo`; CMake >= 3.24, pip-buildable
    fallback/fastgeo_py.py   pure-python reference — this is the spec
  data/
    gen/gen_listings.py      synthetic-data generator, fixed seed, byte-reproducible
    raw/listings_*.csv       generated source CSVs (~100k rows, deliberate messiness)
    db.sqlite                built artifact, committed on purpose (quickstart works
                             without Python)
    geo/agebs_cdmx.geojson   real INEGI urban AGEB polygons, CDMX subset
    geo/marginacion_cdmx.csv real CONAPO marginación rows for those AGEBs
  .github/workflows/ci.yml   jobs: web-test, cli-test, pipeline-test, native-build
  .github/workflows/pages.yml  deploys web/ to GitHub Pages on main
  docs/
    filter-language.md       the query grammar, examples, error behavior
    data-notes.md            dataset sources, URLs, retrieval dates, licenses
    dev-notes.md             running dev log: decisions, benchmarks, verifications
```

## Components

### Data and pipeline

`gen_listings.py` produces ~100k listings across several raw CSVs with intentional
real-world messiness (currency-formatted prices, latin-1 files, broken rows, 2-3%
near-duplicate re-listings) so `clean.py` and `dedupe.py` have a real job. Fixed RNG
seed; regenerating must stay byte-identical. `ingest.py` builds `data/db.sqlite`;
`enrich.py` assigns listings to AGEB polygons (99.97% of CDMX rows at last
verification; keep it ≥95%); `stats.py` and `export_web.py` feed the web app.

Listings schema (table `listings`): `id TEXT pk, title TEXT, description TEXT,
price_mxn INTEGER, m2 INTEGER, bedrooms INTEGER, type TEXT
(casa|departamento|terreno|local), colonia TEXT, municipio TEXT, estado TEXT,
lat REAL, lng REAL, listed_date TEXT, source TEXT`.

### The filter language (geoq)

Hand-written lexer/parser/eval — no parser library. Grammar reference:
`docs/filter-language.md`. `and` binds tighter than `or`; parentheses override;
`:` is case-insensitive contains; values are numbers, quoted strings, or bare words
(bare words split at whitespace — quote multi-word values). SQL is generated with
bound `?` parameters only, never interpolated. Example:

```sh
geoq query "price<2500000 and colonia:roma or type=terreno"
```

### fastgeo

The pure-python spatial join was far too slow at 100k listings × 2.4k polygons
(~113x measured difference on `batch_assign`), hence the C++ path. The API is
identical in both implementations; `fallback/fastgeo_py.py` is the reference and
the parity suite (`pipeline/tests/test_parity.py`) keeps them in agreement,
including polygon-boundary points. `-ffp-contract=off` in `CMakeLists.txt` is
load-bearing: without it, FMA contraction on arm64 breaks boundary-point parity
(see dev-notes). Do not remove it or add `-ffast-math`.

## Internal contracts

These are relied on across component boundaries; change them only deliberately and
update all sides:

1. **fastgeo import chokepoint** — pipeline code gets fastgeo exclusively via
   `pipeline/geo_backend.py`, which implements:
   `import fastgeo` → on ImportError → `from native.fallback import fastgeo_py as
   fastgeo`, plus the `FASTGEO_FORCE_FALLBACK=1` env override to force the
   pure-python path.
2. **fastgeo API** — `point_in_polygon(lat, lng, ring) -> bool`,
   `batch_assign(points, polygons: dict[str, ring]) -> list[str|None]`,
   `haversine_matrix(points_a, points_b) -> list[list[float]]` (meters),
   `simhash64(text) -> int`, `hamming(a, b) -> int`.
3. **web data shape** — `web/public/listings.json`: JSON array of listing objects
   (schema fields above), capped at 5,000 rows, produced by
   `pipeline/export_web.py`. Asset paths in web code go through
   `import.meta.env.BASE_URL` (Pages serves from `/geo-lab/`).
4. **stats shape** — `pipeline/stats.json`: `{generated_at, total_listings,
   by_colonia:[{colonia,municipio,count,median_price_per_m2}],
   histogram:[{bucket_max_mxn,count}]}`.
5. **db path** — CLI defaults to `data/db.sqlite` resolved from the CWD; pass
   `--db` explicitly when running from elsewhere.

## Working on the code

Real commands (also in the README quickstart, which is kept literally true):

```sh
# web
cd web && npm ci && npm run dev        # test: npm test ; lint: npm run lint
# cli
cd cli && npm ci && npm test           # dev run: npm run dev -- query "..." --db ../data/db.sqlite
# pipeline
python3 -m venv .venv-pipeline && source .venv-pipeline/bin/activate
pip install pytest && pytest pipeline/tests/
# native (optional; pipeline falls back to pure python without it)
pip install ./pipeline/native && pytest pipeline/tests/test_parity.py
```

TypeScript is pinned to 6.x in both `web/` and `cli/` (typescript-eslint's peer
range; see dev-notes before bumping).

## Invariants to keep

- `gen_listings.py` output stays byte-identical for the committed seed.
- The parity suite passes both with the compiled module and with
  `FASTGEO_FORCE_FALLBACK=1`.
- The README quickstart works exactly as written from a fresh clone.
- CI (all four jobs) green on main.
- No secrets, no machine-local absolute paths in committed files.

## Data sources

Synthetic listings (generated, clearly documented as such). Real open data:
INEGI Marco Geoestadístico AGEB polygons and CONAPO Índice de Marginación Urbana —
exact URLs, retrieval dates, and licenses in `docs/data-notes.md`. Never label
generated data as INEGI/CONAPO.

## Roadmap

Layer 1 (done): listings ingest, sqlite, geoq, web explorer. Layer 2 (in
progress): geo enrichment — AGEB assignment done; marginación choropleth, AGEB
detail panel, DENUE business layer, second region (Guadalajara) pending. Layer 3
(exploring): marginación vs price/m² analysis, colonia scoring for event siting,
price alerts, GeoJSON export (open PR).

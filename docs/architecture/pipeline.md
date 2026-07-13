---
aliases: [Pipeline]
tags: [architecture]
---

# Pipeline

Python 3.11+, **stdlib + `sqlite3` only** — `pytest` is the single dev dependency. Every script is
runnable standalone (`python3 pipeline/<script>.py --db ...`) and importable as a module; the tests
in `pipeline/tests/` drive the module functions, not the CLIs.

## Scripts, in run order

| Script | Input | Output | Notes |
|---|---|---|---|
| `data/gen/gen_listings.py` | `data/geo/*` | `data/raw/listings_*.csv` | Synthetic generator, `SEED = 20260101`, byte-reproducible |
| `pipeline/clean.py` | `data/raw/*.csv` | in-memory rows + drop stats | Called by `ingest.py`; standalone `__main__` is a diagnostic |
| `pipeline/dedupe.py` | cleaned rows | `{id: dup_of \| None}` | Called by `ingest.py`; also has a `run(db)` that UPDATEs in place |
| `pipeline/ingest.py` | `data/raw/*.csv` | `data/db.sqlite` | Orchestrator: drops + recreates the DB from scratch |
| `pipeline/enrich.py` | `db.sqlite` + `data/geo/*` | `db.sqlite` (in place) | Fills `ageb_id` / `marginacion_grade` / `marginacion_index` |
| `pipeline/stats.py` | `db.sqlite` | `pipeline/stats.json` | Excludes `dup_of IS NOT NULL` |
| `pipeline/export_web.py` | `db.sqlite` | `web/public/listings.json` | Capped at 5,000, newest first, excludes `dup_of IS NOT NULL` |
| `pipeline/geo_backend.py` | — | `fastgeo` | The import chokepoint; see [[fastgeo]] and [[contracts]] |

### `gen_listings.py`

`GOOD_TOTAL = 100_000` valid listings, of which `DUP_FRACTION = 0.025` (2,500) are injected
near-duplicate re-listings, plus `BROKEN_EXTRA = 750` intentionally-malformed rows. Split across
four source files that each carry a distinct flavor of real-world mess: `listings_inmuebles24.csv`
(prices as `"$1,234,567"`, padded whitespace), `listings_metroscubicos.csv` (**latin-1 encoded**,
random `type` casing), `listings_lamudi.csv` (the broken rows), `listings_vivanuncios.csv`.
Near-duplicates jitter coordinates by `rng.uniform(-0.0006, 0.0006)` degrees per axis
(`gen_listings.py:384`) — ~94 m worst-case diagonal, which is exactly what `dedupe.py`'s distance
threshold is calibrated against.

### `clean.py`

`clean_row()` returns `(row, None)` or `(None, reason)`. Reading is utf-8-sig first, **latin-1 on
`UnicodeDecodeError`** (`clean.py:138`) — one raw source really is latin-1 and it broke the first
version. Drop reasons, in the order they're checked (`clean.py:70`):

| reason | condition |
|---|---|
| `missing_id` | empty/blank `id` |
| `bad_price` | `parse_price` fails, or price ≤ 0 (accepts `"$1,234,567"`) |
| `bad_m2` | not an int, or ≤ 0 |
| `bad_bedrooms` | not an int, or < 0 (blank is allowed and becomes 0) |
| `bad_type` | not in `{casa, departamento, terreno, local}` after `.strip().lower()` |
| `missing_location` | any of `colonia` / `municipio` / `estado` blank |
| `bad_coords` | unparseable, or outside `LAT_RANGE (14.0, 33.0)` / `LNG_RANGE (-118.5, -86.0)` |
| `bad_date` | `date.fromisoformat(listed_date)` raises |
| `duplicate_id` | `id` already seen (applied in `clean_all`, not `clean_row`) |

Observed on the real run: **750 dropped** — `{'bad_type': 162, 'bad_price': 281,
'missing_location': 152, 'bad_m2': 155}` — exactly matching the 750 rows the generator injects.
Zero false drops, zero broken rows through.

## The `listings` table

Declared once, in `pipeline/ingest.py:38`. **This is the schema contract** — `cli/src/parser/eval.ts`'s
`FIELD_COLUMNS`, `cli/src/types.ts`'s `ALL_COLUMNS`, and `cli/src/__tests__/fixtures/fixtureDb.ts`
must be kept in sync with it.

```sql
CREATE TABLE listings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price_mxn INTEGER NOT NULL,
    m2 INTEGER NOT NULL,
    bedrooms INTEGER NOT NULL,
    type TEXT NOT NULL,          -- casa | departamento | terreno | local
    colonia TEXT NOT NULL,
    municipio TEXT NOT NULL,
    estado TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    listed_date TEXT NOT NULL,   -- ISO YYYY-MM-DD
    source TEXT,
    dup_of TEXT,                 -- set by dedupe.py; NULL = canonical
    ageb_id TEXT,                -- set by enrich.py (CDMX rows only)
    marginacion_grade TEXT,      -- set by enrich.py: Muy bajo..Muy alto
    marginacion_index REAL       -- set by enrich.py: CONAPO IM_2020
);
```

The three enrichment columns are created **NULL in the base schema**, not via `ALTER TABLE` in
`enrich.py`, so the full contract is visible in one place. (`enrich.py:93`'s `_ensure_columns` is a
defensive `ALTER TABLE` for older DBs; it's a no-op against a fresh `ingest.py` build.)
Indexes: `municipio`, `colonia`, `type`, `price_mxn`, `dup_of` (`ingest.py:61`).

## `dedupe.py` — near-duplicate detection

Text similarity alone is unsafe: the generator draws descriptions from a small template pool, so
unrelated listings collide on simhash by chance. A pair is flagged only if it agrees on **all** of
(`dedupe.py:65`):

1. same `type` and same `municipio`,
2. `abs(a.m2 - b.m2) <= M2_TOLERANCE` (2),
3. `fastgeo.hamming(simhash64(a.description), simhash64(b.description)) <= HAMMING_THRESHOLD` (12),
4. `fastgeo.haversine_matrix(...)[0][0] <= DISTANCE_THRESHOLD_M` (120.0 m).

Rows are bucketed into a `GRID_SIZE_DEG = 0.01` (~1.1 km) lat/lng grid and only compared against the
3×3 neighborhood, keeping this near-linear. Full pairwise was tried first and was hopeless past a
few thousand rows. Rows are processed in `(listed_date, id)` order, so the **earliest-listed row in
a cluster is canonical** (`dup_of = None`) and later ones point at it. Nothing is ever deleted.

### Calibrated thresholds

Measured at full ~100k scale against the generator's own true duplicate→original mapping
(`docs/dev-notes.md`):

| hamming≤ | dist≤ | m2 tol≤ | flagged | true positives | false positives | precision | recall |
|---|---|---|---|---|---|---|---|
| 16 | 250m | 5 | 5,805 | 2,375 | 3,430 | 40.9% | 95.0% |
| **12** | **120m** | **2** | **2,492** | **2,398** | **94** | **96.2%** | **95.9%** |

The first row is what the uncalibrated thresholds actually produced — nearly 60% false positives.
The shipped row lands almost exactly on the true 2,500-duplicate count. **Do not loosen these
without re-running the sweep**; the reasoning is duplicated in `dedupe.py:38`'s comment block.

## `enrich.py` — AGEB + marginación assignment

For every row with `estado = 'Ciudad de México'`, find the AGEB polygon from
`data/geo/agebs_cdmx.geojson` (2,431 polygons across 16 alcaldías) containing its `(lat, lng)`, then
attach that AGEB's CONAPO grade/index from `data/geo/marginacion_cdmx.csv`.

The naive version is the "100k listings × 2.4k polygons" case that motivated [[fastgeo]]. **Two
cheap pre-filters run before `fastgeo.point_in_polygon` is ever called** (`enrich.py:83`):

1. **Own-municipio only** — `by_mun[row["municipio"]]` narrows ~2,431 candidates to ~150.
2. **Plain-Python bbox check** per remaining candidate — eliminates all but a handful before paying
   for the real point-in-polygon test.

This is why the pure-Python fallback is still practical here (`enrich.py` full run: 0.9s compiled vs
1.5s fallback) even though the raw `batch_assign` benchmark shows ~113x. It also means `enrich.py`
calls `point_in_polygon` per candidate rather than `batch_assign` — an intentional trade.

**Assignment rate: 50,297 / 50,314 CDMX rows = 99.97%.** `ASSIGNMENT_TARGET = 0.95`
(`enrich.py:47`) — below that, `run()` prints a WARNING to stderr. **Keep it ≥ 95%.** The 17 misses
are all near-duplicate rows whose ±0.0006° jitter pushed them into a genuine inter-polygon gap
(several in Xochimilco's chinampa/wetland gaps) or just across a boundary into a neighboring
alcaldía, which isn't searched because only the row's own recorded `municipio` is. `assign_ageb`
correctly returns `None` there. Not a bug. (Separately: the geojson has ~50 AGEBs with no CONAPO
row, so a matched `ageb_id` can still yield NULL grade/index.)

## `stats.py` / `export_web.py`

Both exclude `dup_of IS NOT NULL` from every aggregate/row set. `stats.py` writes the shape pinned
in [[contracts]]; its histogram's last bucket uses `bucket_max_mxn: null` for "everything above the
previous bucket". `export_web.py` writes 12 of the 18 columns, `ORDER BY listed_date DESC LIMIT
5000`. Neither is idempotent-sensitive — both fully rewrite their output file.

---

## See also

- ↑ [[ARCHITECTURE]] · [[DATA]]
- [[overview]] · [[fastgeo]] · [[contracts]] · [[query-engine]] · [[web-app]]
- Reference: [[data-notes]] (real sources, licenses) · [[dev-notes]] (run transcripts, calibration)
- ↩ [[overview]]

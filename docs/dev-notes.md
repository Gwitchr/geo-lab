# Dev notes

Running notes to myself as I build this out — decisions, numbers, and the
occasional dumb mistake, so I don't re-litigate the same question in six
months. `BRIEF.md` is the original spec I wrote for myself before starting;
these are the notes from actually building it.

## Pipeline (`data/`, `pipeline/`)

### How to run

```sh
python3 -m venv .venv-pipeline && source .venv-pipeline/bin/activate
pip install pytest                  # only dev dependency; pipeline/*.py is stdlib-only

python3 data/gen/gen_listings.py    # -> data/raw/listings_*.csv (~100k rows, fixed seed)
python3 pipeline/ingest.py          # -> data/db.sqlite, table `listings`
python3 pipeline/stats.py           # -> pipeline/stats.json

cd pipeline && python3 -m pytest -q
```

### First real end-to-end run

```
$ python3 pipeline/ingest.py
read 100750 raw rows, kept 100000, dropped 750 {'bad_type': 162, 'bad_price': 281, 'missing_location': 152, 'bad_m2': 155}
flagged 2492 near-duplicate rows
wrote 100000 rows to .../data/db.sqlite

$ python3 pipeline/stats.py
wrote .../pipeline/stats.json (97508 listings, 374 colonias)
```

Exactly 750 rows dropped by `clean.py`, matching the 750 intentionally-broken
rows the generator injects — zero false drops, zero broken rows slipped
through. Satisfying when the numbers line up like that.

### Scripts

- **`clean.py`** — parses/validates every raw row (price incl. `"$1,234,567"`
  format, m2/bedrooms, type enum, non-empty colonia/municipio/estado, lat/lng
  bounding box, ISO date), drops broken rows with a reason, reads utf-8 first
  then falls back to latin-1 (one of the raw sources exports latin-1 and it
  choked the first version of this).
- **`ingest.py`** — orchestrates `clean.clean_all()` + `dedupe.find_duplicates()`,
  (re)creates `data/db.sqlite`. Table `listings`: `id, title, description,
  price_mxn, m2, bedrooms, type, colonia, municipio, estado, lat, lng,
  listed_date, source, dup_of, ageb_id, marginacion_grade,
  marginacion_index` — the last three columns are reserved for the geo
  enrichment layer, not populated yet. Keep this list in sync with
  `cli/src/__tests__/fixtures/fixtureDb.ts` and `cli/src/parser/eval.ts`'s
  `FIELD_COLUMNS` if I ever add a column.
- **`stats.py`** — writes `pipeline/stats.json` (`generated_at,
  total_listings, by_colonia[...], histogram[...]`), excluding
  `dup_of IS NOT NULL` from every aggregate. Histogram's last bucket uses
  `bucket_max_mxn: null` for "everything above the previous bucket".

`dedupe.py`'s near-duplicate detection uses `simhash64`/`hamming`/
`haversine_matrix`, refined with municipio/type/m2-tolerance agreement so
template-phrase collisions between unrelated listings aren't flagged.
Currently a simple per-municipio nested-loop pass — fine for now, will need
a real spatial bucket if it gets slow at full scale. Non-destructive: sets
`dup_of` (earliest-`listed_date` row in a cluster is canonical), never
deletes rows.

### Decisions and assumptions

- **`dup_of` is a label, not a filter.** All 100,000 cleaned rows stay in
  `listings`; `stats.py` excludes `dup_of IS NOT NULL`, but I expect the CLI
  (once it exists) to read the raw table unfiltered by default.
- **`gen_listings.py` does not import `fastgeo`/`geo_backend`.** It has its
  own small ray-casting + rejection-sampling helpers, deliberately
  independent of `pipeline/native/` — didn't want the generator to depend on
  the thing it's generating fixtures to test. It does read
  `data/geo/agebs_cdmx.geojson` and `data/geo/marginacion_cdmx.csv` directly
  for realistic coordinate sampling and CDMX price baselines (see
  `docs/data-notes.md` for where those came from).
- **Price-per-m2 baselines for Guadalajara/Monterrey are hand-set
  approximations**, not backed by an open dataset — CDMX's is, via the CONAPO
  marginación index. Same for the two metros' population-share weights.

## CLI (`cli/`, `geoq`)

`geoq` — subcommands `query`, `stats`, `export` — with a hand-written
lexer/parser/eval for the filter language (grammar in
`docs/filter-language.md`). Didn't want a parser dependency for something
this small.

```sh
cd cli
npm ci
npm test         # vitest — 89 tests
npm run build    # tsc -> cli/dist/
node dist/index.js query "price<2500000 and colonia:roma" --db ../data/db.sqlite
```

`--db` resolves against `process.cwd()` (no repo-root auto-detection) — run
`geoq` from the repo root, or pass `--db` explicitly. Might add
auto-detection later, not bothering yet.

### Decisions

- Field names and `and`/`or` are case-insensitive; string values are not.
- `:` (contains) is rejected on numeric fields (`price`, `m2`, `bedrooms`) as
  a semantic `EvalError`.
- `listed` needs its value **quoted** — an unquoted `2024-01-01` tokenizes as
  three separate number/word tokens and fails fast with a clear error. Spent
  a bit too long on this before just requiring the quote.
- SQL params are always positional `?`, bound via `better-sqlite3`; user text
  never touches the SQL string. `:` search terms are escaped for
  `%`/`_`/`\` so literal wildcards can't sneak through.
- `query` defaults to `LIMIT 20`, `stats --by` defaults to the top 15 groups —
  both overridable via `--limit`.
- `export` writes to stdout when `--out` is omitted (useful for piping).
- No `lint` script in `cli/package.json` — didn't feel worth the setup for
  `cli/` yet (only `test`/`build` matter day to day).

## Web (`web/`)

Vite + TypeScript listings explorer: table + filter, charts (hand-rolled SVG,
no chart library). No UI framework — didn't want the overhead for a page
this small.

```sh
cd web
npm ci
npm run dev      # http://localhost:5173
npm test         # vitest — 25 tests
npm run build    # tsc --noEmit + vite build -> web/dist/
npm run lint     # eslint .
```

### Decisions

- **Filter language is intentionally simpler than `geoq`'s**: whitespace-
  separated tokens, AND-only, no OR/parentheses/quoted multi-word values. A
  bare word substring-matches across title/colonia/municipio/estado/type
  (accent-insensitive); `field<op>value` supports the same operator set as
  the CLI on a smaller field list. Didn't want to reimplement the full CLI
  grammar in the browser for what's mostly quick table filtering.
- **Charts respond to the live filter**, not just the table — filtering also
  narrows the histogram and colonia ranking. This one felt obviously right
  once I had the table filter working.
- `web/public/listings.json` is placeholder fixture data (200 rows) for now;
  will wire it to the real pipeline export once `export_web.py` exists.

## Native (`pipeline/native/`, fastgeo)

### Why it exists

Hit the wall on this early: the pure-Python spatial join was way too slow at
real scale (100k listings × ~2,400 polygons). First full `enrich.py` run
against the naive Python `batch_assign` took long enough that I assumed
something was hung before I checked and realized it was just working,
slowly. That's what pushed me into writing `fastgeo` — a C++17 module via
pybind11, API identical to a pure-Python reference implementation
(`pipeline/native/fallback/fastgeo_py.py`, which stays the spec — parity is
non-negotiable, I treat any parity failure as a `fastgeo` bug, never a
reference bug):

- `point_in_polygon(lat, lng, ring) -> bool` (ray casting)
- `batch_assign(points, polygons) -> list[str|None]`
- `haversine_matrix(points_a, points_b) -> list[list[float]]` (meters)
- `simhash64(text) -> int`, `hamming(a, b) -> int`

### Design decisions

- **Boundary semantics are exact, epsilon-free** (cross-product == 0.0 plus a
  bbox test), not fuzzy — an epsilon tolerance would just move the
  cross-language disagreement to the epsilon boundary instead of removing it.
  A ring's own vertices are algebraically always inside in both
  implementations.
- **FNV-1a 64-bit + byte-level tokenizer for `simhash64`**: bytes `>= 0x80`
  (any byte of a multi-byte UTF-8 sequence) are treated as word bytes so
  accented Spanish text stays intact as single tokens without a Unicode
  library in C++. Not linguistically perfect (accented uppercase isn't
  folded); only needs to match the Python side, which it does.
- **`batch_assign` polygon order** follows Python dict insertion order for
  parity — the pybind11 binding walks the `py::dict` directly.

### The bug that actually mattered: FP contraction breaks parity

Lost an evening to this one. `-O3` on Apple Clang (arm64, native FMA
hardware) by default fuses multiply-add/subtract chains (the boundary
cross-product, the ray/edge intersection formula) into a single FMA
instruction, rounding differently in the last bit than Python's
strictly-separate IEEE754 ops. Produced real parity failures right on
polygon-boundary points — took a while to even localize because the failures
were sparse and only ever on boundary cases. Fixed with `-ffp-contract=off`
in `CMakeLists.txt` (MSVC needs no equivalent flag — it doesn't contract by
default). Noting this so I don't "clean up" the flag later:
**don't add `-ffast-math` or similar without re-running the parity suite.**

### Build instructions

```sh
python3 -m venv .venv-native && source .venv-native/bin/activate
pip install pybind11 cmake ninja scikit-build-core pytest numpy
pip install ./pipeline/native      # builds via CMake, installs fastgeo.*.so
```

### Tests: `pipeline/tests/test_parity.py`

Fixed seed `20260710`. Covers random simple polygons, boundary points (every
vertex, every edge midpoint, a random interpolation point per edge),
degenerate rings (empty/single/two-vertex/all-identical/collinear/
self-closing), `batch_assign` edge cases, `haversine_matrix` on random and
identical points, and `simhash64`/`hamming` on Spanish-listing-style text.

`FASTGEO_FORCE_FALLBACK=1` skips the whole module (nothing to compare —
both sides would be the fallback); compiled `fastgeo` not importable also
skips cleanly via `pytest.importorskip`, which is what CI's `pipeline-test`
job relies on (it never builds the extension).

### Benchmark: `batch_assign`, ~100k points vs 2,000 polygons

Fixed-seed fixture (seed `20260710`), both runs assigning the identical
pickled fixture, confirmed to match the same 6,673/100,000 points:

| implementation | elapsed | matched |
|---|---|---|
| compiled `fastgeo` | 2.19 s | 6,673 / 100,000 |
| pure-Python fallback | 247.32 s (4 min 7 s) | 6,673 / 100,000 |

**~113x speedup** (247.32 / 2.19), apples-to-apples — both implementations do
the same brute-force O(points × polygons) search, no spatial index either
side. Machine: macOS arm64 (Apple Silicon), AppleClang, `-O3
-ffp-contract=off`, Python 3.13.1, single-threaded.

The more honest "why fastgeo actually matters in production" numbers are the
real workload ones, not the raw benchmark above:

- **`enrich.py`, full 50,314-CDMX-row run**: compiled 0.9s, fallback
  (`FASTGEO_FORCE_FALLBACK=1`) 1.5s — both produced byte-identical
  `ageb_id`/`marginacion_grade`/`marginacion_index` on all 100,000 rows. The
  fallback is fast here specifically because `enrich.py` pre-filters
  candidates before ever calling `fastgeo.point_in_polygon` — it avoids the
  naive brute-force the raw benchmark above measures.
- **`dedupe.py`, full 100,000-row run**: compiled 5.3s, fallback 22.5s — a
  genuine **~4.3x** speedup, since the simhash-over-every-description
  workload has no equivalent cheap pre-filter. This is closer to the real
  "why fastgeo exists" story for the README, since `enrich.py`'s
  naive-brute-force framing doesn't manifest once it's been engineered
  around.


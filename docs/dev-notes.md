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
python3 pipeline/enrich.py          # fills ageb_id / marginacion_* for CDMX rows
python3 pipeline/stats.py           # -> pipeline/stats.json
python3 pipeline/export_web.py      # -> web/public/listings.json (capped at 5000)

cd pipeline && python3 -m pytest -q
```

### First real end-to-end run

```
$ python3 pipeline/ingest.py
read 100750 raw rows, kept 100000, dropped 750 {'bad_type': 162, 'bad_price': 281, 'missing_location': 152, 'bad_m2': 155}
flagged 2492 near-duplicate rows
wrote 100000 rows to .../data/db.sqlite

$ python3 pipeline/enrich.py
CDMX listings: 50314
assigned to an AGEB: 50297 (99.97%)

$ python3 pipeline/stats.py
wrote .../pipeline/stats.json (97508 listings, 374 colonias)
```

99.97% comfortably clears the ≥95% target I set myself in the brief. Dug into
the 17 CDMX rows that miss: all near-duplicate rows whose coordinates were
jittered ±0.0006° (~90 m) off their original — enough, right at an AGEB edge,
to land in a real gap between polygons (several in Xochimilco, which has real
chinampa/wetland gaps) or just past a boundary into a neighboring alcaldía
that isn't searched (`enrich.py` only searches the listing's own recorded
municipio). Not a bug — `assign_ageb` correctly returns `None` for a point
genuinely outside every candidate polygon. Left it as-is.

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
  marginacion_index` — keep this list in sync with
  `cli/src/__tests__/fixtures/fixtureDb.ts` and `cli/src/parser/eval.ts`'s
  `FIELD_COLUMNS` if I ever add a column.
- **`enrich.py`** — assigns every CDMX listing to its containing AGEB polygon
  + marginación grade/index. Pre-filters candidates two ways before ever
  calling `fastgeo.point_in_polygon` (own municipio only, ~2,431 → ~150
  candidates; then a plain-Python bbox check) — this is what keeps the
  pure-Python fallback fast enough for a full run (numbers below).
- **`stats.py`** — writes `pipeline/stats.json` (`generated_at,
  total_listings, by_colonia[...], histogram[...]`), excluding
  `dup_of IS NOT NULL` from every aggregate. Histogram's last bucket uses
  `bucket_max_mxn: null` for "everything above the previous bucket".
- **`export_web.py`** — writes the JSON array `web/public/listings.json`
  needs: `id, title, price_mxn, m2, bedrooms, type, colonia, municipio,
  estado, lat, lng, listed_date`, capped at 5000, newest-listed first,
  `dup_of IS NOT NULL` excluded.
- **`geo_backend.py`** — the fastgeo chokepoint, see "FASTGEO_FORCE_FALLBACK"
  below.

### Dedupe threshold calibration

Didn't want to eyeball `dedupe.py`'s thresholds, so I measured
precision/recall against ground truth (the generator's own true
duplicate→original mapping) at full ~100k scale:

| hamming≤ | dist≤ | m2 tol≤ | flagged | true positives | false positives | precision | recall |
|---|---|---|---|---|---|---|---|
| 16 | 250m | 5 | 5,805 | 2,375 | 3,430 | 40.9% | 95.0% |
| **12** | **120m** | **2** | **2,492** | **2,398** | **94** | **96.2%** | **95.9%** |

First row is what my initial (uncalibrated) thresholds actually produced —
nearly 60% false positives, way too loose. `hamming≤12, dist≤120m, m2 tol≤2`
lands almost exactly on the true 2,500-duplicate count, so that's what
shipped. Full reasoning is in `pipeline/dedupe.py`'s docstrings so future-me
doesn't have to re-derive it.

`dedupe.py`'s near-duplicate detection uses `simhash64`/`hamming`/
`haversine_matrix`, refined with municipio/type/m2-tolerance agreement so
template-phrase collisions between unrelated listings aren't flagged. Rows
are bucketed into a ~1.1 km lat/lng grid so this is close to linear instead
of all-pairs — full pairwise was the first thing I tried and it was
predictably terrible past a few thousand rows. Non-destructive: sets
`dup_of` (earliest-`listed_date` row in a cluster is canonical), never
deletes rows.

### Decisions and assumptions

- **CDMX AGEB polygons carry no colonia names** (INEGI's AGEB grid is codes
  only). `agebs_cdmx.geojson`'s `NOM_MUN` (real alcaldía name, joined in from
  the CONAPO table) covers **municipio**; **colonia** names come from a
  second real source, the CDMX portal's "Colonias del IECM 2019" CSV (1,812
  real names, sampled to 252) — see `docs/data-notes.md`.
- **`dup_of` is a label, not a filter.** All 100,000 cleaned rows stay in
  `listings`; `stats.py` and `export_web.py` exclude `dup_of IS NOT NULL`,
  but `geoq query` reads the raw table unfiltered, so it currently includes
  the 2,492 flagged near-duplicates in results/counts. Leaving this as-is for
  now — making dedup table-wide rather than per-consumer is a `cli/`-side
  call I haven't needed to make yet.
- **`gen_listings.py` does not import `fastgeo`/`geo_backend`.** It has its
  own small ray-casting + rejection-sampling helpers, deliberately
  independent of `pipeline/native/` — didn't want the generator to depend on
  the thing it's generating fixtures to test.
- **Price-per-m2 baselines for Guadalajara/Monterrey are hand-set
  approximations**, not backed by an open dataset — CDMX's is, via the CONAPO
  marginación index (see `docs/data-notes.md`). Same for the two metros'
  population-share weights. Good enough for now, would revisit if I ever
  pull in real GDL/MTY data.
- **Colonia counts are lumpy for Guadalajara/Monterrey vs. CDMX** in
  `stats.json`'s `by_colonia` — a direct consequence of CDMX having 252 real
  curated colonias vs. ~4-17 per municipio for the other two metros. Known
  shape, not a bug, don't "fix" this later without remembering why.

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
no chart library), Leaflet map. No UI framework — didn't want the overhead
for a page this small.

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
- **No marker-clustering plugin.** `sampleForMap()` caps rendered markers at
  400 via deterministic equal-stride sampling instead — didn't want a second
  dependency for a "basic" map.
- **Charts respond to the live filter**, not just the table — filtering also
  narrows the histogram and colonia ranking. This one felt obviously right
  once I had the table filter working.
- `web/public/listings.json` was placeholder fixture data (200 rows) while I
  got the UI working; wired it to the real pipeline export once the pipeline
  side was solid (see "Wiring it together" below).

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

## Wiring it together

Notes from the pass where I actually connected the four pieces end to end
instead of testing them in isolation.

### Pipeline -> web

Ran `pipeline/export_web.py` for real: `web/public/listings.json` now holds
5,000 real rows (the pinned cap) exported from `data/db.sqlite`, replacing
the 200-row placeholder. Re-verified `web`'s `npm test` (25/25), `npm run
build`, and `npm run dev` against the real file (`curl`'d `/`,
`/listings.json` — 5000 rows — and `/src/main.ts`, no console/transform
errors).

### TypeScript version alignment

Had `cli/package.json` pinned to `typescript@^7.0.2` and `web/package.json`
to `^6.0.3` — had downgraded web because `typescript-eslint`'s peer range
excludes TS 7. Aligned `cli/` down to `^6.0.3` too so I'm not running two
compiler versions across the repo for no reason. No code changes needed;
`cli/`'s source doesn't use anything TS 7-only. Verified clean afterward:
`npm test` (89/89), `npx tsc -p tsconfig.json --noEmit`, `npx tsc -p
tsconfig.test.json --noEmit`, `npm run build`. Both packages are on
`^6.0.3` now.

### FASTGEO_FORCE_FALLBACK chokepoint

Had a note to myself that the two-line chokepoint doesn't itself react to
`FASTGEO_FORCE_FALLBACK=1` and that consumers would need the fuller if/else
form. Checked `pipeline/geo_backend.py` and it already implements exactly
that fuller form:

```python
if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    from native.fallback import fastgeo_py as fastgeo
else:
    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo
```

— so nothing to fix, just confirmed by reading the module. Past-me had
already handled it.

### `data/db.sqlite` VACUUM

Ran `sqlite3 data/db.sqlite "VACUUM;"`. Size before: 52,944,896 bytes
(~50.49 MB). Size after: **47,869,952 bytes (~45.65 MB)**. Row counts
unaffected (100,000 rows in `listings`, unchanged). Puts it back under
GitHub's 50 MB warning threshold, so no git-lfs needed.

### GitHub Pages base-path bug

While wiring up `pages.yml`, realized I hadn't set a Pages `base` anywhere.
Set `web/vite.config.ts`'s `base` to `/geo-lab/` for production builds (dev
stays at `/`). That exposed a real bug: `web/src/data.ts`'s `loadListings()`
defaulted to fetching the hardcoded absolute path `/listings.json`, which
would 404 once the app is served from a `/geo-lab/` subpath. Fixed by
defaulting to `` `${import.meta.env.BASE_URL}listings.json` `` instead,
which resolves correctly in both dev (`/listings.json`) and the Pages build
(`/geo-lab/listings.json` — confirmed by grepping the built bundle). Re-ran
`npm test` (still 25/25, tests pass explicit URLs so the default change
doesn't affect them) and `npm run build` after the fix. Glad I caught this
before actually turning Pages on.

### Root hygiene

Added `LICENSE` (MIT) and `.gitignore` (`node_modules/`, `dist/`, `build/`,
`__pycache__/`, `.pytest_cache/`, `.venv*/`, `*.egg-info/`,
`*.sqlite-journal`, `.DS_Store`) — `data/db.sqlite` is deliberately not
ignored, it's committed on purpose so the web app and CLI work straight off
a clone.

### CI workflows

Added `.github/workflows/ci.yml` (`web-test`, `cli-test`, `pipeline-test`,
`native-build`) and `.github/workflows/pages.yml` (build `web/` on push to
`main`, deploy via `actions/deploy-pages`). I ran every job's steps locally
before pushing anything, on macOS arm64, since I wanted to know they'd pass
before finding out from a red check — see "Final verification sweep" below
for the exact commands and output, including a from-scratch `native-build`
simulation in a brand-new venv.

## Known limitations I'm sitting on for now

- **No spatial index** (grid/R-tree) in either `fastgeo` implementation —
  `batch_assign` is brute-force O(points × polygons) by design (that's the
  whole reason the C++ path exists in the first place). `enrich.py` works
  around it with municipio + bbox pre-filtering; a generic spatial index
  would be the natural next step if I ever need it without that kind of
  pre-filter.
- **`-ffp-contract=off` only verified on the non-MSVC compile path** — I
  don't have a Windows/MSVC toolchain handy to confirm MSVC's default
  non-contracting behavior holds parity end-to-end there. Only matters if I
  ever add a Windows runner to CI.
- **Self-intersecting rings are unvalidated** — `point_in_polygon`/
  `batch_assign` assume simple rings; behavior on a self-intersecting ring is
  whatever even/odd ray-casting happens to produce. Not a real-world concern
  for AGEB polygons but noting it.
- **Guadalajara/Monterrey price baselines and colonia gazetteers are
  hand-curated assumptions**, not backed by an open dataset the way CDMX's
  marginación-index-driven baseline is.
- **`geoq` queries the raw `listings` table unfiltered** — near-duplicate
  rows (`dup_of IS NOT NULL`) are included in its results/counts, unlike
  `stats.py`/`export_web.py` which exclude them. Deliberate scope boundary
  for now, might revisit.
- **No marker clustering** in the web map (capped, evenly-sampled 400
  markers instead) — fine at the current 5,000-row export size; worth
  revisiting if the export cap or map interaction model changes.
- **No repo-root auto-detection for `geoq`'s `--db`** — resolves against
  `process.cwd()`; run from the repo root or pass `--db` explicitly.
- **`cli/` has no lint script** — haven't bothered setting one up, `test`/
  `build` cover what I need day to day.

## Final verification sweep

Ran this end to end right before publishing, in this exact tree state (post
VACUUM, post TS alignment, post CI/README/gitignore additions), because I
wanted every claim in the README to actually be true and not just "true when
I last checked." All output below is real, copy-pasted, not paraphrased.

### Test suites

```
$ cd web && npm test
 Test Files  2 passed (2)
      Tests  25 passed (25)

$ cd cli && npm test
 ✓ src/__tests__/lexer.test.ts (14 tests)
 ✓ src/__tests__/golden.test.ts (13 tests)
 ✓ src/__tests__/eval.test.ts (12 tests)
 ✓ src/__tests__/parser.test.ts (18 tests)
 ✓ src/__tests__/commands.test.ts (19 tests)
 ✓ src/__tests__/cli.test.ts (13 tests)
 Test Files  6 passed (6)
      Tests  89 passed (89)

$ cd pipeline && python3 -m pytest -q          # fastgeo compiled + installed
................................................................         [100%]
64 passed in 0.58s

$ cd pipeline && FASTGEO_FORCE_FALLBACK=1 python3 -m pytest -q
...................................................                      [100%]
51 passed, 1 skipped in 0.45s

$ cd pipeline && python3 -m pytest tests/test_parity.py -q   # compiled vs. Python
.............                                                            [100%]
13 passed in 0.03s

$ cd pipeline && FASTGEO_FORCE_FALLBACK=1 python3 -m pytest tests/test_parity.py -q
1 skipped in 0.00s
```

Expected counts (web 25, cli 89, pipeline 64, parity 13) all matched exactly.

### Builds

```
$ cd web && npm run build
vite v8.1.4 building client environment for production...
dist/index.html                   0.43 kB │ gzip:  0.29 kB
dist/assets/index-DKEFTJBW.css   17.85 kB │ gzip:  7.20 kB
dist/assets/index-CmCgb15Y.js   160.37 kB │ gzip: 47.93 kB
✓ built in 79ms

$ cd cli && npm run build
> tsc -p tsconfig.json
(clean exit, dist/ produced: args.js, cli.js, commands/, db.js, format.js,
index.js, parser/, types.js, plus .map files)
```

### My own acceptance checks from the brief

```
$ node cli/dist/index.js query "price<2500000 and colonia:roma" --db data/db.sqlite
(20 rows returned — real Roma/Roma Norte listings across CDMX and Monterrey,
since "Roma" is a real colonia name in both gazetteers; e.g.:)
LST0098973  Departamento en Roma, 2 rec, 61 m2  ...  1265000  61  2  departamento  Roma  Monterrey  Nuevo León  ...
LST0063462  Casa en Roma, 3 rec, 74 m2          ...  1876500  74  3  casa          Roma  Monterrey  Nuevo León  ...

$ python3 pipeline/enrich.py
CDMX listings: 50314
assigned to an AGEB: 50297 (99.97%)          # clears the >=95% target I set

$ python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/a.txt
$ python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/b.txt
$ diff /tmp/a.txt /tmp/b.txt && echo BYTE IDENTICAL
BYTE IDENTICAL
```

Parity suite green both ways is shown above (13 passed compiled, 1 skipped
under `FASTGEO_FORCE_FALLBACK=1` — nothing to compare against by design).

### `native-build`, simulated from a genuinely clean venv

```
$ python3 -m venv /tmp/venv-ci-native && source /tmp/venv-ci-native/bin/activate
$ pip install pybind11 cmake ninja scikit-build-core pytest numpy
$ pip install ./pipeline/native
*** Configuring CMake...
-- The CXX compiler identification is AppleClang 21.0.0.21000101
-- Found pybind11: .../pybind11/include (found version "3.0.4")
*** Building project with Ninja...
[4/4] Linking CXX shared module fastgeo.cpython-313-darwin.so
*** Created fastgeo-0.1.0-cp313-cp313-macosx_26_0_arm64.whl
Successfully installed fastgeo-0.1.0

$ cd pipeline && python3 -m pytest tests/test_parity.py -v
13 passed in 0.39s
```

This is the exact sequence the CI `native-build` job runs; confirmed working
end to end outside any previously-built venv before I trusted it to CI.

### `pipeline-test`'s "skip gracefully" behavior, simulated

```
$ python3 -m venv /tmp/venv-ci-pipeline-test && source /tmp/venv-ci-pipeline-test/bin/activate
$ pip install pytest      # no fastgeo, no native build at all
$ cd pipeline && python3 -m pytest -v
... (test_clean, test_dedupe, test_enrich, test_export_web, test_gen_listings,
     test_ingest, test_stats all pass — dedupe/enrich/ingest fall through to
     the pure-Python fallback automatically, no compiled extension needed)
51 passed, 1 skipped in 0.50s
```

Confirms `test_parity.py` skips cleanly via `pytest.importorskip` when
`fastgeo` was never built — the `pipeline-test` CI job needs no special
handling beyond `pip install pytest`.

### Web dev server, real data

```
$ cd web && npm run dev &
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/          # 200
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/listings.json  # 200
$ curl -s http://localhost:5173/listings.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
5000
```

### `data/db.sqlite` size

VACUUM'd from 52,944,896 bytes (~50.49 MB) to **47,869,952 bytes (~45.65
MB)**, row counts unchanged (100,000 rows).

### Fresh-clone quickstart, actually simulated

Copied the tree (excluding `node_modules/`, `.venv*/`, `dist/`,
`__pycache__/`, `.git/`) to a scratch directory and followed my own README's
Quickstart literally: `cd web && npm ci && npm test && npm run build`,
`cd cli && npm ci && npm test && npm run build`, then `node dist/index.js
query ... --db ../data/db.sqlite` and `npm run dev` against the copy's
already-committed `data/db.sqlite`/`web/public/listings.json`. All steps
passed with the same counts as above (web 25/25, cli 89/89, `geoq` returned
real rows, dev server served 5000 real listings). Also ran the optional
"Regenerating the data from scratch" section end to end in the same copy
(fresh `.venv-pipeline`) — reproduced the identical `ingest.py`/`enrich.py`/
`stats.py` numbers shown above (100000 kept, 750 dropped with the same
per-reason breakdown, 2492 duplicates, 99.97% AGEB assignment, 97508 stats
listings, 374 colonias) and `python3 -m pytest -q` gave `51 passed, 1
skipped` (no fastgeo built in that copy). Worth doing — would've been easy
to have some silent dependency on my own machine state otherwise.

### Not verified yet

- Haven't watched an actual GitHub Actions run — every job's steps above were
  run locally instead, on macOS arm64 rather than the `ubuntu-latest` CI will
  actually use. The native build's compiler (AppleClang vs. GCC/Clang on
  Linux) and the MSVC `-ffp-contract` question noted under "Known
  limitations" are the two places Linux CI could still surprise me.
- Haven't seen an actual Pages deploy either — the `/geo-lab/` base path fix
  above was verified by inspecting the built bundle's asset URLs, not by a
  real deploy. Will know for sure once CI runs on push.

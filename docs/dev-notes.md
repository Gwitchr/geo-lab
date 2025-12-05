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

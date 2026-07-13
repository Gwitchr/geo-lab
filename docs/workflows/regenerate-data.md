---
aliases: [Regenerate the data]
tags: [workflow]
---

# Regenerate the data from scratch

Re-runs the whole pipeline: synthetic listings -> sqlite -> AGEB enrichment ->
stats -> web export. You only need this if you changed the generator, the
gazetteer, or a pipeline script. A fresh clone already works without it —
`data/db.sqlite`, `data/raw/listings_*.csv`, `pipeline/stats.json`, and
`web/public/listings.json` are committed artifacts.

Run every command from the repo root.

## 1. Set up the pipeline venv

`pipeline/*.py` and `data/gen/*.py` are stdlib-only; `pytest` is the single dev
dependency.

```sh
python3 -m venv .venv-pipeline && source .venv-pipeline/bin/activate
pip install pytest
```

## 2. Generate the raw CSVs

```sh
python3 data/gen/gen_listings.py
```

Fixed seed (`SEED = 20260101` in `data/gen/gen_listings.py`). Writes four
source CSVs with deliberate real-world messiness (currency-formatted prices,
one latin-1 file, 750 broken rows, 2,500 near-duplicate re-listings).

## 3. Ingest, enrich, stats, export

```sh
python3 pipeline/ingest.py          # -> data/db.sqlite, table `listings`
python3 pipeline/enrich.py          # ageb_id / marginacion_* for CDMX rows
python3 pipeline/stats.py           # -> pipeline/stats.json
python3 pipeline/export_web.py      # -> web/public/listings.json (capped at 5000)
```

## What you should see

```
$ python3 data/gen/gen_listings.py
wrote .../data/raw/listings_vivanuncios.csv: 29920 rows
wrote .../data/raw/listings_inmuebles24.csv: 26202 rows
wrote .../data/raw/listings_metroscubicos.csv: 24000 rows
wrote .../data/raw/listings_lamudi.csv: 20628 rows
total physical rows: 100750 (primaries=97500 duplicates=2500 broken=750)

$ python3 pipeline/ingest.py
read 100750 raw rows, kept 100000, dropped 750 {'bad_type': 162, 'bad_price': 281, 'missing_location': 152, 'bad_m2': 155}
flagged 2492 near-duplicate rows
wrote 100000 rows to .../data/db.sqlite in <elapsed>s

$ python3 pipeline/enrich.py
CDMX listings: 50314
assigned to an AGEB: 50297 (99.97%)

$ python3 pipeline/stats.py
wrote .../pipeline/stats.json (97508 listings, 374 colonias)

$ python3 pipeline/export_web.py
wrote 5000 listings to .../web/public/listings.json
```

Every one of those numbers is deterministic. If any of them moves, something
changed — the 750 dropped rows match exactly the 750 broken rows the generator
injects (zero false drops), and the AGEB assignment rate must stay ≥95%
(`ASSIGNMENT_TARGET` in `pipeline/enrich.py`, which prints a WARNING below it).
The 17 unassigned CDMX rows are jittered duplicate coordinates landing in real
polygon gaps — see [[data-notes]] and [[dev-notes]].

## 4. Run the tests

```sh
cd pipeline && python3 -m pytest -q
```

`51 passed, 1 skipped` without a compiled `fastgeo` (the skip is
`tests/test_parity.py`, which needs the C++ module — see [[build-fastgeo]]),
or `64 passed` with it installed.

## 5. Verify byte-reproducibility

The generator must stay byte-identical for the committed seed. Run it twice and
compare:

```sh
python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/a.txt
python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/b.txt
diff /tmp/a.txt /tmp/b.txt && echo BYTE IDENTICAL
```

(On macOS without coreutils, `shasum -a 256` instead of `sha256sum`.) A diff
here means someone introduced nondeterminism — an unseeded `random`, a dict
iteration order, a timestamp — and it must be fixed, not re-committed.

## 6. VACUUM and re-commit the artifacts

`ingest.py` recreates the db from scratch, which leaves it bloated. VACUUM it
before committing:

```sh
sqlite3 data/db.sqlite "VACUUM;"
ls -l data/db.sqlite
```

Last run: 52,944,896 bytes (~50.49 MB) before, **47,869,952 bytes (~45.65 MB)**
after, row counts unchanged. This is what keeps `data/db.sqlite` under GitHub's
50 MB warning threshold, so no git-lfs is needed. Skipping the VACUUM will push
it over.

Then re-commit the artifacts the quickstart depends on:

```sh
git add data/raw/listings_*.csv data/db.sqlite pipeline/stats.json web/public/listings.json
```

`data/db.sqlite` and `web/public/listings.json` are committed **on purpose**
(the web app and `geoq` work straight off a clone with no Python). A pipeline
change that isn't re-exported leaves the repo self-inconsistent.

---

## See also

- ↑ [[ENGINEERING]] · [[DATA]]
- [[pipeline]] · [[data-notes]] · [[dev-notes]] · [[overview]]
- [[add-a-region]] · [[add-a-filter-field]] · [[build-fastgeo]] · [[diagnose-parity-failure]]
- ↩ [[Home]]

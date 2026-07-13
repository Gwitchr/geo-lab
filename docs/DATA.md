---
aliases: [Data, DATA]
tags: [moc]
---

# Data

One sqlite file, one table, no ORM, no migration tool, no query cache. The pipeline writes
it; everything else reads it. Provenance is the part that actually needs care: some of this
data is real cited open data and some of it is synthetic, and the two must never be
confused.

---

## Store

**SQLite** (`data/db.sqlite`), accessed via Python's stdlib `sqlite3` in the pipeline and
`better-sqlite3` in the CLI. Committed as a build artifact — ~45.65 MB post-VACUUM,
100,000 rows ([[0004-commit-built-artifacts]]).

- **No ORM.** Hand-written SQL on both sides.
- **No migrations.** `ingest.py` drops and recreates the table; the schema lives in one
  `CREATE TABLE` statement.
- **No validation library.** `clean.py` validates every raw row by hand and drops broken
  ones with a recorded reason.
- **No query cache.** The CLI opens the file per invocation; the web app loads a static JSON
  array once.

## Schema — table `listings`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | e.g. `LST0098973` |
| `title` | TEXT | |
| `description` | TEXT | fed to `simhash64` for near-duplicate detection |
| `price_mxn` | INTEGER | filter field `price` |
| `m2` | INTEGER | filter field `m2` |
| `bedrooms` | INTEGER | filter field `bedrooms` |
| `type` | TEXT | `casa` \| `departamento` \| `terreno` \| `local` |
| `colonia` | TEXT | |
| `municipio` | TEXT | |
| `estado` | TEXT | |
| `lat`, `lng` | REAL | |
| `listed_date` | TEXT | ISO `YYYY-MM-DD`; filter field `listed` |
| `source` | TEXT | which synthetic listing site the row came from |
| `dup_of` | TEXT | near-duplicate label, not a delete ([[0005-dup-of-is-a-label]]) |
| `ageb_id` | TEXT | filled by `enrich.py`, CDMX rows only |
| `marginacion_grade` | TEXT | CONAPO grade, Muy bajo…Muy alto |
| `marginacion_index` | REAL | CONAPO raw index |

**Adding a column touches four places at once:** `pipeline/ingest.py`'s `CREATE TABLE`,
`cli/src/parser/eval.ts`'s `FIELD_COLUMNS`, `cli/src/types.ts`'s `ListingRow` / `ALL_COLUMNS`,
and `cli/src/__tests__/fixtures/fixtureDb.ts`. Recipe: [[add-a-filter-field]].

## Layers

| Layer | File | Job |
|---|---|---|
| Generate | `data/gen/gen_listings.py` | ~100k synthetic rows, fixed seed, **byte-reproducible** |
| Clean | `pipeline/clean.py` | Parse/validate every raw row; utf-8 then latin-1 fallback; drop with a reason |
| Dedupe | `pipeline/dedupe.py` | simhash64 + haversine, grid-bucketed; sets `dup_of` |
| Ingest | `pipeline/ingest.py` | Orchestrates clean + dedupe, (re)creates the db |
| Enrich | `pipeline/enrich.py` | AGEB polygon + marginación grade for CDMX rows |
| Aggregate | `pipeline/stats.py` | → `pipeline/stats.json` |
| Export | `pipeline/export_web.py` | → `web/public/listings.json`, capped at 5,000 |

Deep spec: [[pipeline]]. Re-run recipe: [[regenerate-data]].

## The numbers that must keep holding

| Invariant | Current |
|---|---|
| Rows dropped by `clean.py` = the rows the generator intentionally broke | 750 / 750, zero false drops |
| Near-duplicates flagged at the calibrated thresholds | 2,492 (precision 96.2%, recall 95.9%) |
| CDMX listings assigned to an AGEB | 50,297 / 50,314 = **99.97%** (target ≥ 95%) |
| Generator output for the committed seed | byte-identical across runs |

Full list and how to check them: [[data-integrity]].

## Provenance — real vs synthetic

This is the rule that matters most:

> **Everything under `data/raw/` and `data/db.sqlite` is synthetic.** Realistic in
> distribution, built on real place names and a real price gradient, but no row corresponds
> to an actual property. **Never label it as INEGI/CONAPO-sourced.**

| Asset | Real? | Source |
|---|---|---|
| `data/geo/agebs_cdmx.geojson` | ✅ real | INEGI Marco Geoestadístico via the CDMX open-data portal, CC-BY-4.0-ESP. 2,431 urban AGEB polygons. |
| `data/geo/marginacion_cdmx.csv` | ✅ real | CONAPO *Índice de Marginación Urbana 2020*, filtered to CDMX (2,381 rows). |
| CDMX colonia names (`gazetteer.py`) | ✅ real | IECM 2019 colonias dataset, 1,812 names sampled to 252. |
| GDL / MTY colonia lists | ⚠️ curated | Hand-picked well-known neighborhoods. Plausible, **not** official. |
| GDL / MTY price baselines | ⚠️ assumed | Hand-set from general knowledge of relative affluence. Unlike CDMX's, which is marginación-index-driven. |
| `data/raw/listings_*.csv`, `data/db.sqlite` | ❌ synthetic | `data/gen/gen_listings.py` |

Exact URLs, retrieval dates, licenses, and the processing applied to each download:
[[data-notes]].

Two facts that surprise people: **AGEB polygons carry no colonia names** (INEGI's grid is
codes only — colonias are a separate, non-nesting layer), and CONAPO's `index_normalized` is
**higher = less marginalized**.

---

## See also

- ↑ [[ARCHITECTURE]] · [[PRODUCT]]
- [[pipeline]] · [[contracts]] · [[data-notes]] · [[filter-language]]
- [[regenerate-data]] · [[add-a-filter-field]] · [[add-a-region]]
- [[data-integrity]] · [[TESTING]]
- ↩ [[Home]]

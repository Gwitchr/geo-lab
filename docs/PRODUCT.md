---
aliases: [Product, PRODUCT]
tags: [moc]
---

# Product

geo-lab is a personal geographic-analysis lab. It starts practical — collect, clean, and
explore property listings — and grows into open-data geographic analysis (census areas,
marginación index, business directory) so that questions like *"¿dónde en la CDMX
funcionaría un concierto mediano?"* or *"how does marginalization map onto price per m²?"*
can be answered against real socioeconomic geography rather than raw lat/lng.

Mexico is the first region. Nothing is Mexico-hardcoded; adding a metro is a gazetteer +
data-source exercise, not a rewrite. See [[add-a-region]].

---

## Audiences

| Audience | What they do | Surface |
|---|---|---|
| **The author** (primary) | Explores listings, runs ad-hoc geo questions, extends the lab | `geoq` CLI, the pipeline scripts |
| **A visitor** | Lands on the deployed page, filters/sorts/maps listings without installing anything | Web explorer (GitHub Pages) |
| **An AI agent** | Changes the code without breaking the invariants | This vault, entry at [`AGENTS.md`](../AGENTS.md) |

There are no accounts, no roles, and no multi-tenancy — see [[AUTH]].

## Surfaces

### Web explorer (`web/`)

Static Vite + TypeScript page, no UI framework. Three tabs over the exported listings
slice: **Tabla** (sortable table, capped at 300 rendered rows), **Gráficas** (price
histogram + median price/m² by colonia, hand-rolled SVG), **Mapa** (Leaflet, capped at 400
equal-stride-sampled markers). One filter box drives all three. Deployed to GitHub Pages
from `/geo-lab/`. Details: [[web-app]].

### `geoq` CLI (`cli/`)

Three subcommands over `data/db.sqlite`:

| Command | Purpose |
|---|---|
| `geoq query [expr]` | Rows matching a filter expression (default `LIMIT 20`, `--json`, `--columns`) |
| `geoq stats [expr]` | Aggregates, optionally grouped (`--by colonia\|municipio\|type\|…`, default top 15) |
| `geoq export [expr]` | JSON or CSV to a file or stdout (`--out`, `--format`) |

All three take the same filter expression: `price<2500000 and colonia:roma or type=terreno`.
Grammar reference: [[filter-language]]. Implementation: [[query-engine]].

### Data pipeline (`pipeline/`)

Not user-facing. Six stdlib-only Python scripts, run from the repo root, each printing a
one-line summary: `ingest.py` → `enrich.py` → `stats.py` → `export_web.py`. See [[pipeline]]
and [[regenerate-data]].

## Domain glossary

| Term | Meaning |
|---|---|
| **AGEB** | *Área Geoestadística Básica* — INEGI's urban census unit. 2,431 polygons cover CDMX's 16 alcaldías. Carries geostatistical codes only, **no colonia names**. |
| **Marginación** | CONAPO's *Índice de Marginación Urbana* (2020), scored per AGEB. Five grades, Muy bajo → Muy alto. `index_normalized` is 0–1 where **higher = less marginalized**. |
| **Colonia** | Neighborhood. A separate, non-nesting administrative layer from AGEBs. CDMX names come from the IECM 2019 colonias dataset. |
| **Municipio / alcaldía** | Municipality. CDMX's 16 are alcaldías; the term `municipio` is used uniformly in the schema. |
| **Listing** | One property row: price, m², bedrooms, type (`casa\|departamento\|terreno\|local`), location, listed date, source. |
| **`dup_of`** | Near-duplicate label, not a delete. See [[0005-dup-of-is-a-label]]. |
| **fastgeo** | The C++17 spatial module. See [[fastgeo]]. |

## Roadmap

1. **Listings explorer — done.** Collect, clean, dedupe, browse. `geoq` + the web app.
2. **Geo enrichment — done for CDMX.** Every CDMX listing is assigned to its INEGI AGEB
   polygon and CONAPO marginación grade (99.97% assignment rate). Pending: marginación
   choropleth, AGEB detail panel, DENUE business layer, a second region with real polygons.
3. **Socio-cultural analysis — exploring.** The open-ended layer: price-vs-marginación
   correlation, colonia scoring for event-venue siting, business-directory overlays. No
   fixed scope; this is where the "lab" lives.

Full item list: [[backlog]]. What's worth doing next: [[immediate]].

## Revenue model

None. Personal project, MIT licensed.

## Open questions

- Should dedup be table-wide or stay per-consumer? Today `geoq` counts near-duplicates and
  `stats.py`/`export_web.py` don't ([[0005-dup-of-is-a-label]]).
- Guadalajara/Monterrey price baselines and colonia gazetteers are **hand-curated
  assumptions**, not open data, unlike CDMX's marginación-driven baseline ([[data-notes]]).
- What does "where would a mid-size concert work" actually reduce to — a scoring function
  over which inputs? Undecided.

---

## See also

- [[RUNTIME]] · [[ARCHITECTURE]] · [[DESIGN]]
- [[web-app]] · [[query-engine]] · [[pipeline]] · [[filter-language]] · [[data-notes]]
- [[immediate]] · [[backlog]]
- ↩ [[Home]]

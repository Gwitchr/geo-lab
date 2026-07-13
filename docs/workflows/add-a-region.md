---
aliases: [Add a region]
tags: [workflow]
---

# Add a region (a new metro)

geo-lab is region-friendly, not Mexico-hardcoded: nothing in `cli/` or `web/`
knows about CDMX. `estado`, `municipio`, and `colonia` are plain columns, and the
region layer lives entirely in `data/gen/gazetteer.py` + `data/gen/gen_listings.py`.
Today there are three metros — CDMX, Guadalajara (Jalisco), Monterrey (Nuevo
León) — and only **CDMX** has real polygon + marginación data behind it. Before
writing code, decide what is **cited open data** and what is a **curated
assumption**: you must state that split in [[data-notes]].

| piece | CDMX | GDL / MTY (the curated pattern) |
|---|---|---|
| municipio names | read from `agebs_cdmx.geojson`'s `NOM_MUN` (INEGI, cited) | hand-listed in `gazetteer.py` |
| colonia names | "Colonias del IECM 2019" CSV, CDMX open-data portal (cited) | hand-curated well-known real neighborhoods — plausible, not official |
| coordinates | rejection-sampled inside real AGEB polygons | uniform inside an OSM Nominatim bbox (real lookup, approximate extent) |
| price/m² baseline | derived from CONAPO marginación `index_normalized` (cited) | hand-set numbers from general knowledge — an assumption |
| AGEB + marginación enrichment | yes | none — rows stay NULL |

Either pattern is acceptable. Mislabelling one as the other is not.

## 1. Gazetteer entry — `data/gen/gazetteer.py`

Add a `<REGION>_MUNICIPIOS` dict alongside `GDL_MUNICIPIOS` / `MTY_MUNICIPIOS`:

```python
PUE_MUNICIPIOS = {
    "Puebla": {
        "bbox": (18.9, -98.35, 19.15, -98.05),   # (min_lat, min_lng, max_lat, max_lng)
        "weight": 1.54,                          # approximate population share
        "colonias": ["Centro Histórico", "La Paz", "Angelópolis", ...],
    },
    ...
}
```

- **bbox** must come from a real place lookup (the existing two used OpenStreetMap
  Nominatim, `https://nominatim.openstreetmap.org/search`, `city=`/`state=`/
  `country=Mexico`). Record the retrieval date; do not invent coordinates.
- **weight** only biases which municipio a listing lands in; approximate is fine.
- **colonias** are real names or nothing. Note in the module docstring whether
  they came from an open dataset or your own curation.

## 2. Price baselines and city share — `data/gen/gen_listings.py`

```python
PUE_PRICE_BASE = {"Puebla": 17000, "San Andrés Cholula": 26000, ...}   # MXN per m2

CITY_SHARES = [("cdmx", 0.50), ("gdl", 0.27), ("mty", 0.23)]           # must still sum to 1.0
```

Then add a context builder mirroring `build_gdl_context()`:

```python
def build_pue_context():
    municipios = []
    for name, info in PUE_MUNICIPIOS.items():
        municipios.append({
            "name": name,
            "colonias": info["colonias"],
            "polygons": None,          # no AGEB layer -> pick_coords() uses bbox
            "weight": info["weight"],
            "price_base": PUE_PRICE_BASE[name],
            "bbox": info["bbox"],
        })
    return {"estado": "Puebla", "municipios": municipios}
```

and register it in `generate()`'s `city_ctxs = {"cdmx": ..., "gdl": ..., "mty": ...}`.
Rebalance `CITY_SHARES` — adding a metro takes rows away from the others, so
every downstream count changes.

`pick_coords()` branches on `muni["polygons"]`: polygons present -> rejection-sample
inside a real ring; `None` -> uniform inside the bbox. That is the entire
"does this region have real geometry?" switch.

## 3. Optional: AGEB polygons + marginación — `data/geo/`

Only if you can actually source them. CDMX's are
`data/geo/agebs_cdmx.geojson` (INEGI Marco Geoestadístico urban AGEBs, via the
CDMX open-data portal) and `data/geo/marginacion_cdmx.csv` (CONAPO Índice de
Marginación Urbana 2020, filtered to those AGEBs). To do the same for a new
region you need both, keyed by `CVEGEO`, with `NOM_MUN` present on each feature.

Then follow `build_cdmx_context()`: load the geojson, group rings by `NOM_MUN`,
average the marginación `index_normalized` per municipio, and derive
`price_base` from it instead of hand-setting it.

**`pipeline/enrich.py` only enriches CDMX.** It is pinned to
`CDMX_ESTADO = "Ciudad de México"` and a single `AGEBS_PATH` /
`MARGINACION_PATH`, and it selects
`... FROM listings WHERE estado = ?`. Rows from any other estado get
`ageb_id` / `marginacion_grade` / `marginacion_index` left NULL — which is
correct and expected today. Adding polygons for a second region means
generalizing `enrich.py` to a per-estado map of (geojson, marginación csv), and
its printed assignment rate becomes per-region. Don't half-do this: a region
with polygons but no `enrich.py` wiring produces silently unenriched rows.

## 4. Regenerate and re-baseline

```sh
source .venv-pipeline/bin/activate
python3 data/gen/gen_listings.py
python3 pipeline/ingest.py && python3 pipeline/enrich.py
python3 pipeline/stats.py && python3 pipeline/export_web.py
cd pipeline && python3 -m pytest -q
```

Full recipe, including the venv setup, the byte-reproducibility check, the
VACUUM, and which artifacts must be re-committed: [[regenerate-data]]. Expect
**all** of its
"what you should see" numbers to move (rows kept/dropped, duplicates, CDMX
count, AGEB rate, stats listings/colonias) — re-baseline them there and in
[[dev-notes]] rather than pretending they didn't change.

`pipeline/tests/test_gen_listings.py` asserts byte-reproducibility and row
counts, not city membership, so it should stay green without edits.

## 5. Document the sources — mandatory

Add a section to [[data-notes]] covering, for the new region: dataset page and
direct download URL (or an explicit "hand-curated, not from a dataset"),
retrieval date, license, and any processing applied. Say plainly which parts are
cited and which are assumptions — the existing GDL/MTY entries are the template
("Treat these as plausible, not verified/official"). Never label generated or
curated data as INEGI/CONAPO.

Also expect colonia counts in `stats.json`'s `by_colonia` to be lumpy compared to
CDMX (252 curated colonias vs. a handful per municipio elsewhere). That is a
known shape, not a bug.

---

## See also

- ↑ [[ENGINEERING]] · [[DATA]]
- [[pipeline]] · [[data-notes]] · [[dev-notes]] · [[overview]]
- [[regenerate-data]] · [[add-a-filter-field]] · [[build-fastgeo]] · [[diagnose-parity-failure]]
- ↩ [[Home]]

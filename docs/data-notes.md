---
aliases: [Data Notes, Provenance]
tags: [architecture]
---

# Data notes

Sources, retrieval dates, and licenses for everything under `data/`, plus how
the synthetic listings dataset was built. Retrieval commands are given so
each download is reproducible; no one-off fetch script is kept in the repo
(nothing under `data/` depends on it running again -- the fetched files are
already committed as build artifacts).

## Open data (real)

### `data/geo/agebs_cdmx.geojson` -- INEGI Marco Geoestadístico, urban AGEBs, CDMX

- **Source**: Portal de Datos Abiertos de la Ciudad de México, dataset
  "AGEB Urbanas (Áreas geoestadísticas básicas urbanas)", GeoJSON resource.
  The dataset republishes INEGI's Marco Geoestadístico (2020 vintage) urban
  AGEB boundaries for CDMX.
- **Dataset page**: https://datos.cdmx.gob.mx/dataset/ageb-urbanas-areas-geoestadisticas-basicas-urbanas
- **Direct download URL used**:
  `https://datos.cdmx.gob.mx/dataset/d2ccf6ae-fdf4-407c-a15f-e7dfac2d509d/resource/7b0b7a89-d92e-46ec-9286-018e849f8123/download/lmites-de-ageb-urbanas-en-la-ciudad-de-mxico.json`
- **Retrieved**: 2026-07-10
- **License**: CDMX open-data portal, CC-BY-4.0-ESP (per the portal's standard
  dataset license).
- **Processing applied** (not a re-fetch, just local cleanup of the
  downloaded file): coordinates rounded to 6 decimal places (~11 cm
  precision, discarding ~14 significant digits of floating-point noise the
  source export carried); JSON re-serialized without indentation. Original
  download was 7.48 MB; the committed file is ~4.1 MB (well under the 25 MB
  brief limit). Feature `properties` were trimmed to `CVEGEO`, `CVE_ENT`,
  `CVE_MUN`, `CVE_LOC`, `CVE_AGEB` (as published) plus two added fields,
  `NOM_ENT` (constant `"Ciudad de México"`) and `NOM_MUN` (the alcaldía name
  for `CVE_MUN`), joined in from the CONAPO marginación table below (same
  INEGI-sourced catalog, see next section) so consumers don't have to
  maintain their own CVE_MUN -> name lookup. 2,431 polygons, covering CDMX's
  16 alcaldías (`NOM_MUN` values).
- **No colonia (neighborhood) names**: this AGEB layer's properties are
  geostatistical codes only -- INEGI's AGEB grid does not carry colonia-level
  names (colonias are a different, non-nesting administrative layer). See
  "Colonia names" below for how `data/gen/gen_listings.py` gets real colonia
  names despite this.

### `data/geo/marginacion_cdmx.csv` -- CONAPO Índice de Marginación Urbana 2020, CDMX AGEBs

- **Source**: CONAPO (Consejo Nacional de Población), "Índices de marginación
  2020" publication, AGEB-level database (`IMU_2020.xls`, "AGEB urbana 2020"
  sheet).
- **Publication page**: https://www.gob.mx/conapo/documentos/indices-de-marginacion-2020-284372
- **Direct download URL used**: `https://conapo.segob.gob.mx/work/models/CONAPO/Datos_Abiertos/Marginacion/IMU_2020.zip`
  (unzips to `IMU_2020.xls`, sheet `IMU_2020`, 50,791 national AGEB rows).
- **Retrieved**: 2026-07-10
- **License**: CONAPO / gob.mx open data (public sector information,
  attribution requested per CONAPO's standard terms).
- **Processing applied**: filtered to `ENT == '09'` (Ciudad de México, 2,381
  rows) and further to the 2,381 AGEBs that also have a polygon in
  `agebs_cdmx.geojson` (all of them matched by `CVEGEO`/`CVE_AGEB` -- the
  geojson has 50 additional AGEBs with no marginación row, most likely AGEBs
  with population too small/zero to score; they simply get no
  `ageb_id` match downstream, which is why `enrich.py`'s assignment rate is
  ~99.97% rather than 100%, still comfortably over BRIEF.md's 95% target).
  Columns kept: `ageb_id` (=`CVE_AGEB`, joins to the geojson's `CVEGEO`),
  `municipio` (=`NOM_MUN`), `population` (=`POB_TOTAL`, rounded to int),
  `grade` (=`GM_2020`, CONAPO's five-level marginación grade,
  Muy bajo..Muy alto), `index_value` (=`IM_2020`, the raw marginación index),
  `index_normalized` (=`IMN_2020`, CONAPO's 0-1 normalized index; **higher =
  less marginalized** -- verified against known-wealthy alcaldías scoring
  highest, e.g. Benito Juárez avg 0.972, Miguel Hidalgo avg 0.969, vs.
  known-poorer Milpa Alta avg 0.932, Xochimilco avg 0.941).
  `data/gen/gen_listings.py` uses `index_normalized` (averaged per municipio)
  to bias its synthetic price-per-m2 baseline, so CDMX's price/marginación
  gradient in the generated dataset roughly tracks the real one -- see
  "Synthetic listings" below.

## Synthetic listings (`data/gen/gen_listings.py`, `data/raw/listings_*.csv`)

Everything in `data/raw/` and `data/db.sqlite` is **synthetic** -- generated
data, not scraped or sourced from any real listing site. It is realistic in
distribution and uses real place names, but no row corresponds to an actual
property. See `HANDOFF-pipeline.md` for the full generator design and
verification transcript.

### Colonia / municipio names

- **CDMX**: `data/gen/gazetteer.py`'s `CDMX_COLONIAS` is a curated sample
  (~16 per alcaldía, 252 total) of **real** colonia names, sourced from the
  CDMX open-data portal, dataset "Colonias del IECM 2019" (Instituto
  Electoral de la Ciudad de México), CSV resource.
  - Dataset page: https://datos.cdmx.gob.mx/dataset/04a1900a-0c2f-41ed-94dc-3d2d5bad4065
  - Direct download URL used: `https://datos.cdmx.gob.mx/dataset/04a1900a-0c2f-41ed-94dc-3d2d5bad4065/resource/03368e1e-f05e-4bea-ac17-58fc650f6fee/download/coloniascdmx.csv`
  - Retrieved: 2026-07-10 (1,812 unique colonia names across CDMX's 16
    alcaldías before sampling down to 252).
  - The source export is uppercase ASCII with no diacritics at all (e.g.
    `"CUAUHTEMOC"`, not `"Cuauhtémoc"`) and some classification suffixes
    (`(PBLO)`, `(U HAB)`, etc.). `gazetteer.py`'s build step (not kept as a
    script, see `HANDOFF-pipeline.md`) title-cased names, stripped those
    suffixes, and restored accents via a ~60-word dictionary of common
    Spanish place-name tokens (México, Cuauhtémoc, Juárez, Álvaro Obregón,
    ...). This is a best-effort cleanup, not a verified transliteration --
    some less-common names may still be missing an accent. The well-known
    "Colonia Cuauhtémoc" (alcaldía Cuauhtémoc) was force-included since it
    is a common example neighborhood.
  - Municipio (alcaldía) names are **not** duplicated in `gazetteer.py`;
    `gen_listings.py` reads them straight from `agebs_cdmx.geojson`'s
    `NOM_MUN` property (see above) so there is one source of truth for
    CDMX's 16 alcaldía names.
- **Guadalajara metro** (`GDL_MUNICIPIOS` in `gazetteer.py`): Guadalajara,
  Zapopan, San Pedro Tlaquepaque, Tonalá, Tlajomulco de Zúñiga. Colonia names
  are a **hand-curated list of well-known real neighborhoods** (Americana,
  Chapultepec Country Club, Providencia, Puerta de Hierro, Andares-area
  Zapopan colonias, etc.) -- not from a cited open dataset (INEGI's AGEB
  layer has no colonia names anywhere, and geo-lab does not yet source AGEB
  polygons for Guadalajara), per BRIEF.md's explicit fallback instruction
  ("if not reachable, embed a curated gazetteer"). Treat these as plausible,
  not verified/official.
- **Monterrey metro** (`MTY_MUNICIPIOS` in `gazetteer.py`): Monterrey, San
  Pedro Garza García, San Nicolás de los Garza, Guadalupe, Apodaca, Santa
  Catarina, General Escobedo. Same curated-list caveat as Guadalajara.
- Municipio bounding boxes for both metros (used to sample coordinates,
  since there is no AGEB polygon layer for them) come from a real place
  lookup, OpenStreetMap Nominatim (`https://nominatim.openstreetmap.org/search`,
  `city=`/`state=`/`country=Mexico`, retrieved 2026-07-10) -- real
  centroids, not fabricated, though Nominatim's fallback bounding box for a
  `place=city`/`place=town` node is a padded box around the centroid, not an
  administrative boundary, so it is only an approximation of each
  municipio's actual extent.
- Per-municipio synthetic price-per-m2 baselines for Guadalajara/Monterrey
  (`GDL_PRICE_BASE`, `MTY_PRICE_BASE` in `data/gen/gen_listings.py`) are
  **rough assumptions** from general knowledge of relative affluence in
  those metros (e.g. San Pedro Garza García highest, matching its real-world
  reputation as one of Latin America's wealthiest municipios) -- not backed
  by a cited dataset, unlike CDMX's marginación-index-driven baseline.

## Never labelled as real when it isn't

No file under `data/` is a placeholder standing in for a failed download --
both open-data fetches (AGEBs, marginación) succeeded and are the real INEGI/
CONAPO-sourced files described above. If a future re-run of the fetch needs
to fall back to a placeholder, it must not carry the `agebs_cdmx.geojson` /
`marginacion_cdmx.csv` filenames without a clear placeholder label, per
BRIEF.md.

---

## See also

- ↑ [[DATA]] · [[PRODUCT]]
- [[pipeline]] · [[data-integrity]] · [[add-a-region]] · [[regenerate-data]]
- ↩ [[Home]]

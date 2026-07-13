---
aliases: [Backlog]
tags: [upgrade]
---

# Backlog

The longer-horizon items, grouped by the three layers `README.md`'s Roadmap builds
in order. Layer 1 (listings explorer) is **done** — ingest, sqlite, `geoq`, web
explorer — so it has no entries. Everything below is drawn from what the repo
records: the two Roadmap sections (`README.md`, `docs/development.md`) and
[[dev-notes]]' "Known limitations I'm sitting on for now". Nothing here is
scheduled — this is the "when it earns its place" list. For what's worth doing
*next*, see [[immediate]].

## Layer 2 — Geo enrichment (done for CDMX)

AGEB assignment itself is done and verified: 50,297 of 50,314 CDMX listings
(99.97%) land in an INEGI AGEB polygon with a CONAPO marginación grade attached.
What remains is *surfacing and widening* that enrichment.

**Marginación choropleth.** Shade the map by grade instead of dropping
undifferentiated pins on it. The data is already joined onto every CDMX row
(`marginacion_grade`, `marginacion_index`) and the 2,431 polygons are already
committed (`data/geo/agebs_cdmx.geojson`). The most direct payoff from Layer 2's
work — right now the enrichment exists in the DB and is invisible in the UI. Note
`index_normalized` runs **higher = less marginalized** ([[data-notes]]), the
opposite of the intuitive reading and the first thing a color ramp gets backwards.
Lives in `web/src/map.ts`; needs AGEB geometry exported to the browser, which
`pipeline/export_web.py` doesn't do today (listings only). See [[DESIGN]].

**AGEB detail panel.** Click an AGEB, get its grade, index, population, the
listings inside it, median price/m². The per-row fields already exist; the panel
is a `web/src/main.ts` concern. Aggregates want precomputing pipeline-side rather
than deriving in the browser from a 5,000-row export slice.

**DENUE business-directory layer.** INEGI's national business directory as an
overlay — the "business directory" half of the project's stated premise. A new
real open-data source, so it lands under `data/geo/` with a full [[data-notes]]
entry (source URL, retrieval date, license) the way the AGEB and CONAPO files
have. This is the input Layer 3's venue-siting question actually needs.

**A second region with real AGEB polygons (Guadalajara).** Today GDL and MTY exist
only as **curated gazetteers** — real municipio names, real Nominatim centroids,
hand-picked colonia lists — with no polygon layer at all, which is why
`enrich.py` only ever touches CDMX rows. Sourcing INEGI AGEBs + CONAPO
marginación for Jalisco would make GDL first-class and prove the "region-friendly
rather than hardcoded" claim the README makes. Touches `data/geo/`,
`pipeline/enrich.py`, `data/gen/gazetteer.py`.

## Layer 3 — Socio-cultural analysis (exploring)

The open-ended layer. The README is explicit that there is **no fixed scope yet** —
"this is where the 'lab' part of geo-lab lives" — so these are directions, not
commitments. All of them want Layer 2 surfaced first.

**Marginación vs. price/m² correlation across the metro.** The headline question
from the README's own framing. Every ingredient is already in `data/db.sqlite` —
an analysis, not a feature. Be honest about what it can show: the listings are
**synthetic**, and `gen_listings.py` *derives* CDMX's price-per-m² baseline from
the real CONAPO `index_normalized`. A correlation found here partly measures the
generator. Real for CDMX's *shape*, circular as evidence. Say so wherever it's
published.

**Colonia scoring for event-venue siting.** "¿Dónde en la CDMX funcionaría un
concierto mediano?" — the question the project was started to answer. A composite
score per colonia over marginación, density, price, and (once it exists) DENUE
business mix. Wants DENUE first; without it the score is missing its most
interesting input.

**Price alerts.** Watch a filter, notify on new matches. Interesting mostly
because it's the first item that needs listings to *change over time* — the
current dataset is a fixed-seed snapshot, so this implies a real ingest cadence,
a bigger change than the feature itself.

**GeoJSON export.** `geoq export --format geojson` (or a pipeline-side
equivalent), so query results drop straight into QGIS / kepler.gl / anything that
speaks GeoJSON. Every listing already carries `lat`/`lng`. `docs/development.md`
records this as an open PR. Lands in `cli/src/commands/` alongside the existing
`export`, with a line in [[filter-language]].

## Engineering

Not roadmap features — the known limitations, each a deliberate trade with a
recorded reason.

**A real spatial index (grid / R-tree) in fastgeo.** `batch_assign` is brute-force
**O(points × polygons)** in *both* implementations, by design — the C++ path
exists precisely to make brute force fast enough (~113x: 2.19s vs. 247.32s on
100k points × 2k polygons). `enrich.py` then engineers around the brute force
anyway, pre-filtering candidates twice before it ever calls in (own municipio
only, ~2,431 → ~150 polygons; then a plain-Python bbox check) — which is exactly
why the pure-Python fallback stays viable in production (0.9s vs. 1.5s on a full
`enrich.py` run, nothing like the 113x the raw benchmark shows). A generic index
is the natural next step **only if a caller ever needs `batch_assign` without that
kind of pre-filter**. Nothing does today. Where: `pipeline/native/fastgeo/geo.cpp`
*and* `pipeline/native/fallback/fastgeo_py.py` — both, since the fallback is the
spec and parity is non-negotiable. See [[performance]] and [[fastgeo]].

**Marker clustering in the web map.** No clustering plugin: `sampleForMap()` caps
rendered markers at **400** via deterministic equal-stride sampling instead, a
deliberate call to avoid a second map dependency. Fine at the current 5,000-row
export; worth revisiting if the export cap or the map's interaction model changes.
Where: `web/src/map.ts` (`MAX_MARKERS`, `sampleForMap()`).

**Real open-data price baselines for Guadalajara / Monterrey.** `GDL_PRICE_BASE`
and `MTY_PRICE_BASE` in `data/gen/gen_listings.py` are **hand-set assumptions**
from general knowledge of relative affluence (San Pedro Garza García highest, and
so on) — plausible, not sourced. CDMX's is not: it's driven by the real CONAPO
marginación index. Same gap for the two metros' population-share weights and
colonia gazetteers. Downstream this shows up as lumpy `by_colonia` counts in
`stats.json` (252 curated CDMX colonias vs. ~4–17 per municipio elsewhere) — a
**known shape, not a bug**; don't "fix" it without remembering why.

**`-ffp-contract=off` unverified on MSVC.** The flag is load-bearing: without it,
FMA contraction on arm64 breaks boundary-point parity (an evening lost to that
one — see [[dev-notes]]). MSVC is believed not to contract by default and so to
need no equivalent flag, but that has **never been confirmed end-to-end** — no
Windows toolchain to hand. Only matters if a Windows runner is ever added to CI.
Where: `pipeline/native/CMakeLists.txt`. **Do not add `-ffast-math` or similar
without re-running the parity suite.**

**Self-intersecting rings unvalidated in `point_in_polygon`.** `point_in_polygon`
and `batch_assign` assume **simple rings**. Behavior on a self-intersecting ring
is whatever even/odd ray-casting happens to produce — undefined, not wrong. Not a
real-world concern for INEGI AGEB polygons, which is why it sits here and not in
[[immediate]], but it is an unguarded precondition and worth recording as one.
Where: `pipeline/native/fastgeo/geo.cpp` and
`pipeline/native/fallback/fastgeo_py.py`.

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]] · [[PRODUCT]]
- [[immediate]] (the peer)
- Reference: [[dev-notes]] · [[data-notes]] · [[performance]] · [[fastgeo]] · [[web-app]]
- ↩ [[Home]]

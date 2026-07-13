---
aliases: [Performance]
tags: [quality]
---

# Performance

Every number below was measured on this repo and is copied from [[dev-notes]].
Nothing here is estimated. If you change a hot path, re-measure — do not
update these figures by inference.

## The one that justifies the C++ path

`batch_assign`, fixed-seed fixture (seed `20260710`), **100,000 points ×
2,000 polygons**, both implementations assigning the identical pickled
fixture and matching the same 6,673/100,000 points:

| implementation | elapsed |
|---|---|
| compiled [[fastgeo]] | **2.19 s** |
| pure-Python fallback (`native/fallback/fastgeo_py.py`) | **247.32 s** (4 min 7 s) |

**~113x** (247.32 / 2.19). Apples-to-apples: both sides do the same
brute-force O(points × polygons) scan, no spatial index either way. Machine:
macOS arm64 (Apple Silicon), AppleClang, `-O3 -ffp-contract=off`, Python
3.13.1, single-threaded. `-ffp-contract=off` is load-bearing for parity, not
performance — see [[fastgeo]] before touching compiler flags.

## The numbers that describe the real pipeline

The raw benchmark is the *worst case*, not the shipped case. What the
[[pipeline]] actually costs on a full run:

| stage | compiled | `FASTGEO_FORCE_FALLBACK=1` | ratio |
|---|---|---|---|
| `dedupe.py`, full 100,000-row run | **5.3 s** | **22.5 s** | ~4.3x |
| `enrich.py`, full run (50,314 CDMX rows) | **0.9 s** | **1.5 s** | ~1.7x |

`enrich.py`'s fallback stays fast **only** because it never hands `fastgeo`
the brute-force problem. Before any `point_in_polygon` call it pre-filters
candidates twice: to the listing's own `municipio` (~2,431 polygons → ~150),
then a plain-Python bbox containment test per remaining candidate. That
engineering is what collapses the 113x gap to 1.7x here. Remove either
pre-filter and `enrich.py` inherits the raw benchmark's shape.

`dedupe.py` has no equivalent cheap pre-filter for its
simhash-every-description workload, so its ~4.3x is the honest "why fastgeo
exists in production" number.

## Structural choices behind the numbers

- **`dedupe.py` buckets rows into a ~1.1 km lat/lng grid** (`GRID_SIZE_DEG =
  0.01`) and only compares within a cell and its 8 neighbours — close to
  linear instead of all-pairs. Full pairwise was tried first and was
  unusable past a few thousand rows.
- **`enrich.py`'s municipio + bbox pre-filter** (above) is the reason the
  pure-Python fallback is a usable path at all, not just a correctness
  reference.

## Known gap: no spatial index

Neither `fastgeo` implementation has a grid or R-tree. `batch_assign` is
brute-force O(points × polygons) **by design** — that brute force is exactly
what the C++ path exists to make fast. `enrich.py` works around the missing
index with its own pre-filtering. A generic spatial index is the natural next
step only if a consumer ever needs `batch_assign` *without* that kind of
pre-filter. This is a deliberate open gap, not an oversight.

## Web budget

From the real production build (`vite build`, see [[web-app]]):

| artifact | size | gzip |
|---|---|---|
| `dist/assets/index-*.js` | **160.37 kB** | 47.93 kB |
| `dist/assets/index-*.css` | **17.85 kB** | 7.20 kB |
| `dist/index.html` | 0.43 kB | 0.29 kB |

The app has no UI framework and no chart library (hand-rolled SVG); the bulk
of the JS is Leaflet. Three caps keep the page responsive, and all three are
load-bearing:

- **`listings.json` capped at 5,000 rows** — pinned in `export_web.py`
  (`MAX_ROWS = 5000`), newest-listed first, `dup_of IS NOT NULL` excluded.
  This is a [[contracts]] shape, not a tuning knob.
- **Table capped at 300 rows** rendered (`TABLE_ROW_CAP` in `main.ts`); the
  status line says so when it truncates. Filtering still runs over all 5,000.
- **Map capped at 400 markers** (`MAX_MARKERS` in `map.ts`), chosen by
  deterministic equal-stride sampling in `sampleForMap()` rather than
  head-truncation, so markers stay spread across the filtered set. No
  marker-clustering plugin — a second dependency was not worth it at 5,000
  rows. Revisit if the export cap grows.

The filter box is debounced at 150 ms; charts and the map render lazily only
when their tab is active (Leaflet and the SVG width calc both need a
laid-out container).

---

## See also

- ↑ [[RUNTIME]] · [[ENGINEERING]]
- [[accessibility]] · [[security]] · [[data-integrity]]
- [[fastgeo]] · [[pipeline]] · [[web-app]] · [[dev-notes]]
- ↩ [[Home]]

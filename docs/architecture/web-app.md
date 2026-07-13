---
aliases: [Web App]
tags: [architecture]
---

# Web App

Vite + TypeScript listings explorer: a table with a filter box, two charts, and a map, over the
5,000-row JSON slice the pipeline exports. **No UI framework and no chart library** — the page is
small enough that neither earns its weight. Only runtime dependency: `leaflet` (`^1.9.4`).

## Files

| File | Role |
|---|---|
| `web/src/main.ts` | Everything DOM: `innerHTML` app shell, tab switching, table render, sort, debounced filter, `bootstrap()` |
| `web/src/data.ts` | `loadListings()`, the browser filter language (`filterListings`), `sortListings` |
| `web/src/charts.ts` | `computePriceHistogram`, `computeMedianPricePerM2ByColonia`, and hand-rolled SVG renderers |
| `web/src/map.ts` | Leaflet map, `sampleForMap()`, `initMap()`, `destroyMap()` |
| `web/src/style.css` | All styling |

State is one module-level object in `main.ts:24` — `{ all, query, sortField, sortDir, activeTab }` —
and a single `render()` recomputes everything from it. There is no reactivity layer; every mutation
calls `render()` by hand.

## Rendering caps (all three are deliberate)

- **`TABLE_ROW_CAP = 300`** (`main.ts:6`) — the table renders `filtered.slice(0, 300)`. The status
  line tells the user when it's truncating: `"N de M propiedades (mostrando los primeros 300 en la
  tabla)"`. Filtering still runs over the full set; only the DOM is capped.
- **`MAX_MARKERS = 400`** (`map.ts:7`) — `sampleForMap()` caps rendered markers via **deterministic
  equal-stride sampling**, not head-truncation:

  ```ts
  const stride = listings.length / max;
  for (let i = 0; i < max; i++) sampled.push(listings[Math.floor(i * stride)]);
  ```

  So markers stay spread across the whole result set instead of clumping in whatever the current sort
  put first. This exists **instead of a marker-clustering plugin** — a second dependency wasn't worth
  it at a 5,000-row export. If the export cap or interaction model changes, revisit.
- **Charts are top-N capped**: the histogram is 10 equal-width bins across the filtered min/max;
  the colonia chart is `topN = 20` by median price/m².

## Lazy tab rendering

`renderCharts()` and `renderMap()` both early-return unless their tab is active
(`main.ts:172`, `main.ts:180`). This is not an optimization — it's a correctness requirement:
**Leaflet and the SVG width calculation both need a laid-out (visible) container.** Rendering into a
`display:none` panel produces a zero-size map and garbage chart geometry. `switchTab()` therefore
sets `state.activeTab`, toggles the panel classes, and *then* calls `render()`. `initMap()` also
fires `setTimeout(() => map?.invalidateSize(), 0)` (`map.ts:88`) to make Leaflet recompute size once
its container is actually visible.

`initMap()` is re-entrant: it reuses the module-level `map`/`markerLayer` and calls
`markerLayer.clearLayers()` rather than constructing a new map per filter change.

## Charts, hand-rolled

`charts.ts` builds SVG through `document.createElementNS(SVG_NS, tag)` (`svgEl`, `charts.ts:91`).
Both charts use a fixed `viewBox` (`640 × 260` for the histogram; `640 × (rows*22 + margins)` for the
colonia chart) with `width: 100%`, so they scale without measuring the container. Each bar carries an
SVG `<title>` for a native hover tooltip. Compute and render are separate exported functions
(`computePriceHistogram` / `renderPriceHistogram`), which is what makes them unit-testable without a
DOM measurement pass.

**Charts respond to the live filter**, not just the table — `render()` passes the same `filtered`
array to the table, the histogram, and the colonia ranking.

## The browser filter language — deliberately simpler than `geoq`'s

`filterListings()` (`data.ts:143`) is *not* a port of [[query-engine]]. Reimplementing the full CLI
grammar in the browser wasn't worth it for what is mostly quick table filtering. The differences are
intentional:

| | `geoq` ([[filter-language]]) | browser (`data.ts`) |
|---|---|---|
| combining | `and` / `or` + parentheses, `and` binds tighter | **whitespace-separated tokens, AND-only** — no `or`, no parens |
| quoting | quoted strings, escapes | none — no multi-word values |
| bare word | not a thing (field required) | substring-matches across `title`, `colonia`, `municipio`, `estado`, `type` |
| case/accents | `:` is case-insensitive; `=` case-sensitive | **accent-insensitive and case-insensitive everywhere** via NFD normalize |
| fields | `price m2 bedrooms type colonia municipio listed` | `price m2 bedrooms` + `title colonia municipio estado type` (**no `listed`**) |
| execution | compiled to SQL `WHERE` with bound `?` params | in-memory `Array.filter` |

`normalize()` (`data.ts:35`) is the accent-insensitivity — `.normalize("NFD")`, strip the combining
range `̀-ͯ`, `.toLowerCase().trim()` — so typing `cuauhtemoc` matches `Cuauhtémoc`. It is
applied to both haystack and needle. Operators are matched **longest-first**
(`COMPARATORS = ["<=", ">=", "<", ">", ":", "="]`, `data.ts:64`) and a `field<op>value` token only
counts as such if `field` is a known field — otherwise the whole token falls back to a bare-word
search. `:` on a numeric field is a string-contains on the number's digits here (`data.ts:107`),
which is *not* what `geoq` does (there it's an `EvalError`). Don't "align" these without deciding
that's actually what you want.

Filter input is debounced 150 ms (`main.ts:216`).

## Data loading and the `/geo-lab/` base path

```ts
export async function loadListings(
  url = `${import.meta.env.BASE_URL}listings.json`,
): Promise<Listing[]>
```

`web/vite.config.ts` sets `base: command === "build" ? "/geo-lab/" : "/"` — GitHub Pages serves this
as a **project page** (`<user>.github.io/geo-lab/`), not at domain root. Any asset path in web code
must therefore go through `import.meta.env.BASE_URL`. The original code fetched the hardcoded
absolute `/listings.json`, which resolved fine in dev and would have **404'd on Pages**; the
`BASE_URL` default resolves to `/listings.json` in dev and `/geo-lab/listings.json` in the build.
This is a standing rule, not a one-off fix: see [[contracts]].

`loadListings` throws on a non-ok response or a non-array body. `bootstrap()` catches and writes the
message into the status line rather than leaving a blank page.

## Escaping

`escapeHtml()` (`main.ts:159`) round-trips through `div.textContent` → `div.innerHTML` before the
table's template-literal `innerHTML` write. Map popups build their DOM nodes with `textContent` and
serialize via `outerHTML` (`map.ts:31`). Any new field rendered into `innerHTML` must go through one
of these.

## Commands and tests

```sh
cd web
npm ci
npm run dev      # http://localhost:5173
npm test         # vitest — 25 tests (charts.test.ts, data.test.ts)
npm run build    # tsc --noEmit + vite build -> web/dist/
npm run lint     # eslint .
```

Tests pass explicit URLs to `loadListings`, so they're unaffected by the `BASE_URL` default.
TypeScript is pinned to `^6.0.3` here and in `cli/` (typescript-eslint's peer range excludes TS 7).

---

## See also

- ↑ [[ARCHITECTURE]] · [[DESIGN]]
- [[overview]] · [[query-engine]] · [[contracts]] · [[pipeline]] · [[fastgeo]]
- Reference: [[filter-language]] (the *other*, richer language) · [[dev-notes]]
- ↩ [[overview]]

---
aliases: [Accessibility]
tags: [quality]
---

# Accessibility

State of the [[web-app]] as it actually exists in `web/index.html`,
`web/src/main.ts`, `web/src/charts.ts`, `web/src/map.ts`, and
`web/src/style.css` — verified by reading them, not by intent. There is no
axe/Lighthouse run in CI, so treat this page as the source of truth and
re-verify against the code when you change the DOM.

## What exists today

- **`lang="es"`** on `<html>` (`web/index.html`). All UI copy is Spanish, so
  screen readers get the right voice.
- **Tab bar is marked up as tabs**: `role="tablist"` on the `<nav>`,
  `role="tab"` on each of the three buttons, and `aria-selected` kept in sync
  in `switchTab()` (`btn.setAttribute("aria-selected", String(isActive))`).
  They are real `<button>` elements, so Tab/Enter/Space work.
- **`role="status"`** on the `#status` line, so the live "N de M propiedades"
  count is announced after filtering without stealing focus.
- **`aria-label="Filtrar propiedades"`** on the `#filter-box` search input
  (it has no visible `<label>`, only a placeholder — the `aria-label` is what
  gives it an accessible name).
- **Visible focus ring** on that input: `#filter-box:focus { outline: 2px
  solid var(--accent-light); outline-offset: 1px; }` — the default outline is
  never suppressed anywhere in `style.css`.
- **Sortable `<th>`** are given `tabIndex = 0` and `role="button"` in
  `renderTableHead()`, so they are reachable by keyboard and announced as
  operable.
- **`font-variant-numeric: tabular-nums`** on `tbody td.num`, so price / m2 /
  bedrooms columns align digit-for-digit and don't shimmer while filtering.
- **Charts do have an accessible name**: both SVGs are built with
  `role="img"` + `aria-label` ("Histograma de precios", "Precio mediano por
  m2, por colonia"), and each bar carries an SVG `<title>` with its value.
  Empty datasets render the text "Sin datos para graficar." rather than an
  empty box.

## Gaps — real, open, not done

These are stated as gaps on purpose. Do not describe them as handled.

1. **Sortable `<th>` are focusable but not operable by keyboard.**
   `renderTableHead()` registers `th.addEventListener("click", ...)` and
   nothing else. There is no `keydown` handler, so Enter/Space on a focused
   `<th>` does nothing — `role="button"` promises an interaction the code
   does not implement. This is the highest-value fix on the page.
2. **No `aria-sort`.** Sort state is conveyed only visually, via the
   `.sorted-asc` / `.sorted-desc` classes and their `▲`/`▼` `::after`
   content. A screen-reader user cannot tell which column is sorted or in
   which direction.
3. **Tab bar has no roving focus.** The buttons are wired for `click` only;
   ArrowLeft/ArrowRight do not move between tabs, and there is no
   `tabindex="-1"`/`tabindex="0"` roving pattern. The panels also carry no
   `role="tabpanel"` / `aria-controls` / `aria-labelledby` wiring, so the
   `role="tablist"` markup is structurally incomplete.
4. **Charts have a name but no data alternative.** The `aria-label` says what
   the chart *is*; nothing exposes what it *says*. The per-bar `<title>`
   elements are pointer-hover tooltips — the `<rect>`s are not focusable, so
   keyboard and screen-reader users never reach them. A visually-hidden table
   (or the same numbers in text) is the missing piece.
5. **Leaflet markers are not keyboard reachable.** `map.ts` uses
   `L.circleMarker`, which renders as an SVG path with no tab stop and no
   accessible name, so the popups (`bindPopup`) are mouse-only. The map is
   effectively a pointer-only surface today.

## Contrast

Measured against the tokens in `web/src/style.css` (see [[DESIGN]]):

| pair | ratio | verdict |
|---|---|---|
| `--text` `#1f2320` on `--bg` `#f7f7f5` | ~14.8:1 | passes AA and AAA, comfortably |
| `--text-muted` `#6b7069` on `--bg` `#f7f7f5` | **4.72:1** | passes AA for normal text — with almost no headroom |
| `--accent` `#2563eb` on `--bg` `#f7f7f5` | ~4.8:1 | passes AA for normal text (active tab label) |

**Do not lighten `--text-muted` any further.** At 4.72:1 it clears the 4.5:1
AA threshold by 0.22 — any nudge toward the background fails. It is used for
the status line (0.85rem), the subtitle, inactive tab labels, chart axis and
row labels, and the empty-table message, i.e. for a lot of small text. If you
want more visual hierarchy, take it from weight or size, not from contrast.

---

## See also

- ↑ [[DESIGN]] · [[ENGINEERING]]
- [[performance]] · [[security]] · [[data-integrity]]
- [[web-app]] · [[overview]]
- ↩ [[Home]]

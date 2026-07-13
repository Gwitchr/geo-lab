---
aliases: [Styling System]
tags: [convention]
---

# Styling System

One stylesheet: **`web/src/style.css`**. Plain CSS custom properties, no
framework, no preprocessor, no CSS-in-JS, no webfont. The token contract lives
in [[DESIGN]]; this page is the rules for working inside it.

## The tokens

Everything visual comes from seven custom properties declared once, in `:root`:

```css
:root {
  --bg: #f7f7f5;          /* page background */
  --panel-bg: #ffffff;    /* cards, table surface, map surface */
  --border: #e2e2df;      /* hairlines, table rules, input borders */
  --text: #1f2320;        /* body copy */
  --text-muted: #6b7069;  /* subtitles, axis/row/value labels, status line */
  --accent: #2563eb;      /* active tab, sort caret, bar hover */
  --accent-light: #3b82f6;/* bar fill, focus ring */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               Helvetica, Arial, sans-serif;
  color-scheme: light;
}
```

The font is the **system stack** — no webfont is loaded, and none should be.
`color-scheme: light` — the app is light-mode only; there is no dark theme and
no `prefers-color-scheme` branch to keep in sync.

## Rules

**Never hardcode a hex outside `:root`.** If you find yourself typing `#` in a
rule body, you either want an existing token or you're adding one *to `:root`*
and to [[DESIGN]]. (The single existing exception, `tbody tr:hover`'s `#fafaf8`,
is a wart, not a precedent — don't add more.)

**Charts are hand-written SVG and take their colors from CSS, not from inline
fills.** `web/src/charts.ts` builds elements with a `class` attribute and the
stylesheet paints them:

```ts
// charts.ts — set the class, never a fill
svgEl("rect", { x, y, width, height, class: "bar" });
svgEl("text", { x, y, class: "axis-label" });
```

```css
/* style.css — the only place a chart color is decided */
.chart-block svg .bar        { fill: var(--accent-light); }
.chart-block svg .bar:hover  { fill: var(--accent); }
.chart-block svg .axis-label,
.chart-block svg .row-label,
.chart-block svg .value-label { font-size: 10px; fill: var(--text-muted); }
.chart-block svg .axis-title  { font-size: 11px; fill: var(--text-muted); }
```

The existing class vocabulary: `.bar`, `.axis-label`, `.axis-title`,
`.row-label`, `.value-label` inside `.chart-block`. Extend that vocabulary
rather than reaching for `fill="…"` — an inline fill is invisible to the token
system and can't be re-themed.

**No chart library, no CSS framework.** Both charts (price histogram, median
price/m² by colonia) are ~a few dozen lines of SVG each; that's the whole reason
there's no dependency. Same standing bias as [[typescript-style]].

## Layout and structure conventions

- Structural classes are semantic and flat: `.topbar`, `.tabs`, `.tab-btn`,
  `.panel`, `.table-wrap`, `.chart-block`, `.map`, `.status`, `.popup-title`,
  `.popup-meta`. IDs only for the two singletons: `#app`, `#filter-box`.
- Panel visibility is a class toggle (`.panel` / `.panel.active`), same for
  `.tab-btn.active` and the sort carets (`thead th.sorted-asc` / `.sorted-desc`,
  rendered via `::after` content). State lives in a class, not in inline
  `style=`.
- Spacing is in `rem`; radii are 6px (input) / 8px (surfaces); borders are
  `1px solid var(--border)`.
- Focus is visible: `#filter-box:focus` draws a `2px` `--accent-light` outline.
  Don't remove outlines.
- Numeric table cells get `.num` (right-aligned, `font-variant-numeric:
  tabular-nums`).

## Leaflet

Leaflet ships its own CSS; it's the one external stylesheet. Style the app
*around* the map (`.map` sets the surface, height, border, radius) and the popup
contents (`.popup-title`, `.popup-meta`) — don't fork or override Leaflet's
internals.

---

## See also

- ↑ [[ENGINEERING]] · [[DESIGN]]
- [[typescript-style]] · [[python-style]] · [[cpp-native]] · [[git-and-pr]]
- ↩ [[Home]]

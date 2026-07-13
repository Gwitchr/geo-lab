---
# DESIGN.md spec (google-labs-code/design.md, version: alpha)
# Tokens are normative. Prose explains how to apply them.
#
# Derived from web/src/style.css (the :root custom properties are the design
# source of truth). Values were read out of that file, not invented; anywhere a
# token had to be newly codified, the prose below says so explicitly.

# Obsidian metadata (preserved alongside the spec; ignored by the linter)
aliases: [Design, Design System, DESIGN]
tags: [moc, quality]

version: alpha
name: geo-lab
description: >
  A quiet, document-like data explorer. Warm off-white paper, white panels, hairline
  borders, and a single blue accent that only appears where something is interactive or
  selected. Depth comes from 1px borders, never shadows. Type is the OS system stack at
  small sizes with tabular numerals, because the interface is mostly a dense table of
  prices and areas. Light theme only.

colors:
  # Brand / action — from --accent and --accent-light
  primary: "#2563eb"                 # --accent · active tab, sort arrow, bar hover. 5.17:1 on white ✓ WCAG AA
  on-primary: "#ffffff"              # readable foreground on a primary fill
  primary-accent: "#3b82f6"          # --accent-light · resting chart-bar fill, focus ring
  on-primary-accent: "#ffffff"

  # Surfaces — from --bg and --panel-bg
  surface: "#f7f7f5"                 # --bg · body, the warm off-white "paper"
  surface-container-low: "#ffffff"   # --panel-bg · table, chart blocks, map, sticky table head
  surface-container-high: "#fafaf8"  # table row hover (currently a raw hex in style.css — see Do's and Don'ts)

  # Foregrounds — from --text and --text-muted
  on-surface: "#1f2320"              # --text · primary text. 14.6:1 on surface
  on-surface-variant: "#6b7069"      # --text-muted · secondary text, chart labels. 4.72:1 on surface ✓ AA (no headroom — do not lighten)

  # Lines — from --border
  outline: "#e2e2df"                 # --border · panel borders, table rules, tab underline

typography:
  # Newly codified. style.css sizes in rem against a 16px root; converted to px here.
  # One family: the OS system stack. No webfont is loaded and none should be.
  headline-md:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.2
  title-md:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 16px
    fontWeight: 700
    lineHeight: 1.3
  body-lg:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
  body-md:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label-lg:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
  label-md:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 15px
    fontWeight: 600
    lineHeight: 1.4
  caption:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.4
  numeric-tabular:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: '"tnum" 1'
  chart-label:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 10px
    fontWeight: 400
    lineHeight: 1.2
  chart-axis-title:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 1.2

rounded:
  md: 6px      # the filter input
  lg: 8px      # table wrapper, chart blocks, map

spacing:
  xxs: 4px     # 0.25rem · tab gap
  xs: 8px      # 0.5rem
  sm: 12px     # 0.75rem
  md: 16px     # 1rem
  lg: 20px     # 1.25rem
  xl: 24px     # 1.5rem
  xxl: 48px    # 3rem · app bottom padding
  shell-max-width: 1100px
  map-height: 560px

components:
  app-shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-lg}"
    maxWidth: "{spacing.shell-max-width}"
    padding: 24px 20px 48px

  page-title:
    textColor: "{colors.on-surface}"
    typography: "{typography.headline-md}"

  page-subtitle:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.body-lg}"

  input-search:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    borderWidth: 1px
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 8px 12px

  input-search-focus:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    outlineColor: "{colors.primary-accent}"
    outlineWidth: 2px
    rounded: "{rounded.md}"

  tab:
    backgroundColor: transparent
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.body-md}"
    padding: 8px 16px
    borderBottomColor: transparent
    borderBottomWidth: 2px

  tab-hover:
    backgroundColor: transparent
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    padding: 8px 16px

  tab-active:
    backgroundColor: transparent
    textColor: "{colors.primary}"
    typography: "{typography.label-md}"
    borderBottomColor: "{colors.primary}"
    borderBottomWidth: 2px
    padding: 8px 16px

  card:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline}"
    borderWidth: 1px
    rounded: "{rounded.lg}"
    padding: 16px 20px

  card-title:
    textColor: "{colors.on-surface}"
    typography: "{typography.title-md}"

  table-header-cell:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-sm}"
    borderBottomColor: "{colors.outline}"
    borderBottomWidth: 1px
    padding: 9px 11px

  table-header-cell-sorted:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.primary}"
    typography: "{typography.body-sm}"
    borderBottomColor: "{colors.outline}"
    borderBottomWidth: 1px

  table-cell:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-sm}"
    borderBottomColor: "{colors.outline}"
    borderBottomWidth: 1px
    padding: 8px 11px

  table-cell-numeric:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    typography: "{typography.numeric-tabular}"
    textAlign: right
    padding: 8px 11px

  table-row-hover:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-sm}"

  empty-state:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.body-sm}"
    textAlign: center
    padding: 24px

  status-line:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.caption}"

  divider:
    backgroundColor: "{colors.outline}"
    height: 1px

  chart-bar:
    backgroundColor: "{colors.primary-accent}"
    textColor: "{colors.on-primary-accent}"

  chart-bar-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"

  chart-label:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.chart-label}"

  chart-axis-title:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.chart-axis-title}"

  map-canvas:
    backgroundColor: "{colors.surface-container-low}"
    borderColor: "{colors.outline}"
    borderWidth: 1px
    rounded: "{rounded.lg}"
    height: "{spacing.map-height}"

  map-popup-title:
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"

  map-popup-meta:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.caption}"

  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.md}"
    padding: 8px 16px
---

# Design

The web explorer is a reading surface, not an app chrome. It should feel like a printed
data sheet: warm off-white paper, white panels, hairline rules, and one blue that appears
**only** where something is interactive or selected. Everything else is greyscale.

The source of truth is `web/src/style.css` — the `:root` custom properties. Every token in
the frontmatter above was read out of that file. Typography is the one exception and is
marked as newly codified below.

---

## Overview

**Brand personality.** Restrained, documentary, Spanish-language. The interface is mostly a
dense table of prices and square metres; the design's job is to stay out of its way.

**Theme.** Light only. `color-scheme: light` is declared explicitly — there is no dark
theme and adding one means adding a second value for every surface/foreground token.

**No framework.** No Tailwind, no CSS-in-JS, no preprocessor, no component library, no chart
library. Plain CSS with custom properties, hand-written SVG for charts, Leaflet for the map.
This is a deliberate standing choice ([[styling-system]]); a PR that introduces a UI
framework needs to argue for it.

## Colors

Two greys, one blue, one line colour. That's the whole palette.

| Role | Token | CSS variable | Where it shows up |
|---|---|---|---|
| Action / selected | `primary` `#2563eb` | `--accent` | Active tab text + underline, sort arrows, chart-bar hover |
| Accent fill | `primary-accent` `#3b82f6` | `--accent-light` | Resting chart-bar fill, filter-box focus ring |
| Paper | `surface` `#f7f7f5` | `--bg` | Body |
| Panel | `surface-container-low` `#ffffff` | `--panel-bg` | Table, chart blocks, map, sticky header |
| Row hover | `surface-container-high` `#fafaf8` | *(none — raw hex)* | `tbody tr:hover` |
| Text | `on-surface` `#1f2320` | `--text` | Everything primary |
| Muted text | `on-surface-variant` `#6b7069` | `--text-muted` | Subtitle, status, chart labels, popup meta |
| Line | `outline` `#e2e2df` | `--border` | Borders, table rules, tab underline |

**Contrast, checked:**

| Pair | Ratio | Verdict |
|---|---|---|
| `on-surface` on `surface` | 14.6:1 | ✓ AAA |
| `on-surface-variant` on `surface` | **4.72:1** | ✓ AA for normal text — **no headroom**. Do not lighten `--text-muted`. |
| `on-primary` (white) on `primary` | **5.17:1** | ✓ AA. This is why `primary`, not `primary-accent`, is the fill for anything with text on it. |
| `on-primary` on `primary-accent` | 3.68:1 | ✗ fails AA for normal text. `primary-accent` is a **fill-only** token — chart bars and focus rings, never a background behind text. |

That last row is the one rule to remember: **`--accent-light` is decoration, `--accent` is
action.** The chart bars invert the usual hover direction for this reason — they rest on the
lighter blue and *darken* to `primary` on hover.

There are no `error` / `success` / `warning` / `info` tokens, because the app has no
semantic feedback states — the only failure surface is a status line that renders an error
message in plain muted text. If a real alert component ever lands, it gets tokens then,
derived from a real design pass, not guessed at now.

## Typography

**Newly codified.** `style.css` sizes everything in `rem` against a 16px root and never
names a scale. The `typography.*` levels above convert those real sizes to px and give them
names; they describe what the app already renders, they don't change it.

One family: the OS system stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
Helvetica, Arial, sans-serif`). **No webfont is loaded and none should be** — the page is a
static Pages deploy and a font request is the largest thing that could be added to it.

| Level | Real usage |
|---|---|
| `headline-md` 22/700 | `h1` in the topbar |
| `title-md` 16/700 | `h2` on each chart block |
| `body-lg` 16/400 | The subtitle beside the title |
| `body-md` 15/400 | Filter input, tab labels |
| `label-md` 15/600 | The **active** tab (weight is the only change) |
| `body-sm` 14/400 | Table cells and headers |
| `numeric-tabular` 14/400 + `tnum` | Numeric table cells — prices and areas must align in a column |
| `caption` 14/400 | Status line, map popup meta |
| `label-lg` 16/600 | Map popup title |
| `chart-label` 10/400 · `chart-axis-title` 11/400 | SVG text inside charts |

`numeric-tabular` is not optional decoration. The table is a price comparison surface; the
digits have to line up.

## Layout

- **App shell**: `max-width: 1100px`, centred, `24px 20px 48px` padding. It does not go
  full-bleed.
- **Topbar**: flex, `wrap`, baseline-aligned, `space-between` — the title and the filter box
  sit on one line on desktop and stack on narrow screens. The filter box is
  `flex: 1 1 280px; max-width: 420px`.
- **Tabs**: a flex row above a 1px `outline` rule; the active tab's 2px `primary` underline
  overlaps it.
- **Panels**: exactly one visible at a time (`.panel` / `.panel.active`, plain
  `display: none` / `block`). Charts and the map only render when their tab becomes active —
  Leaflet and the SVG width calculation both need a laid-out container ([[web-app]]).
- **Spacing** rides a 4px base: 4 / 8 / 12 / 16 / 20 / 24 / 48.

## Elevation & Depth

**There is none, and that's the design.** Not one `box-shadow` exists in the stylesheet.
Depth is expressed with a 1px `outline` border and the value step from `surface` (warm
off-white paper) to `surface-container-low` (white panel). The sticky table header works the
same way — it stays legible over scrolling rows because it is opaque white with a bottom
rule, not because it floats.

If you need to signal elevation, reach for the border and the surface step. Do not
introduce a shadow scale.

## Shapes

Two radii, both from the stylesheet: `md` 6px for the filter input, `lg` 8px for every
panel-sized container (table wrapper, chart blocks, map). Nothing is a pill; nothing is a
circle. Borders are always exactly 1px `outline`, except the 2px `primary` tab underline and
the 2px `primary-accent` focus outline.

## Components

The frontmatter defines every primitive the app actually renders. Two notes:

**`button-primary` is codified intent, not current code.** The app has no filled button today
— its only controls are the tab buttons (plain, underline-active) and the search input. The
token is defined so that the first filled action button in this project has an obvious,
accessible answer (`primary` + white text, 5.17:1) instead of someone reaching for
`--accent-light` and shipping 3.68:1 text.

**`surface-container-high` (`#fafaf8`) is drift.** It is currently a raw hex inline at
`tbody tr:hover` in `web/src/style.css` — the one colour in the app that is not a custom
property. The token above encodes where it should live. Promote it into `:root` next time
that file is touched.

### Iconography

There is no icon set and no icon dependency. The two "icons" in the app are text glyphs in
CSS `content`: `▲` / `▼` on the sorted table header. Keep it that way unless a real need
appears; a webfont or SVG sprite would be the heaviest thing on the page.

### Charts

Hand-written SVG, no chart library ([[web-app]]). Bars are styled by **class**, not by inline
`fill` — `.bar` picks up `primary-accent`, `.bar:hover` picks up `primary`. This is what
keeps the charts inside the token system. Labels use `chart-label` / `chart-axis-title` at
`on-surface-variant`.

### Animation

None. No transitions, no keyframes, no motion tokens. The only state changes are instant
(tab switch, sort, filter). The filter input is debounced 150ms in `main.ts`, which is
input handling, not animation.

## Do's and Don'ts

**Do**

- Read colours from the `:root` custom properties. Add a new one there if you need it.
- Use `primary` for anything that carries text on top of it; use `primary-accent` for fills
  and focus rings only.
- Use `numeric-tabular` (`font-variant-numeric: tabular-nums`) for every column of numbers.
- Express depth with the 1px border + surface step.
- Style SVG chart elements with classes so they inherit the tokens.
- Keep `--text-muted` exactly where it is — it is at 4.72:1, one shade from failing AA.

**Don't**

- **Don't hardcode a hex outside `:root`.** There is exactly one today (`#fafaf8`) and it's
  flagged above as drift, not as precedent.
- **Don't put text on `primary-accent`** — 3.68:1, fails AA.
- **Don't add a `box-shadow`.** The design has no elevation layer.
- **Don't add a webfont.** The system stack is the choice, not a placeholder.
- **Don't add a UI framework, a CSS framework, or a chart library** to a page this size —
  see [[styling-system]] and [[ENGINEERING]].
- **Don't invent semantic colours** (`error`, `success`, …) ad hoc. There is no alert
  component yet; when there is, derive the tokens deliberately.
- **Don't introduce ad-hoc type sizes.** If a size isn't in the scale above, either it maps
  to an existing level or the scale needs an argued addition.

## Implementation mapping

| Token group | Source of truth | Consumers |
|---|---|---|
| `colors.*` | `web/src/style.css` `:root` (`--bg`, `--panel-bg`, `--border`, `--text`, `--text-muted`, `--accent`, `--accent-light`) | Body, panels, tabs, table, chart bars, focus rings, map popups |
| `typography.*` | `web/src/style.css` (rem sizes; **no named scale exists in code** — this file codifies one) | `h1`/`h2`, tabs, table cells, SVG chart text, popups |
| `rounded.*` | `web/src/style.css` (`6px` input, `8px` panels) | Filter input, table wrapper, chart blocks, map |
| `spacing.*` | `web/src/style.css` (rem values on a 4px base) | Shell padding, tab gaps, cell padding, chart block padding |
| Component roles | `web/src/main.ts` (markup), `web/src/charts.ts` (SVG), `web/src/map.ts` (Leaflet popups) | The three tabs: Tabla, Gráficas, Mapa |

There is no token generator and no export pipeline — `style.css` **is** the artifact. The
convergence loop is therefore short:

1. Change `web/src/style.css`'s `:root`.
2. Update the `colors` / `rounded` / `spacing` blocks in this file from the same values.
3. `npx @google/design.md lint docs/DESIGN.md`
4. `cd web && npm run lint && npm test && npm run build`

---

## See also

- ↑ [[PRODUCT]] · [[ARCHITECTURE]]
- [[styling-system]] · [[web-app]] · [[accessibility]]
- [[ENGINEERING]] · [[RUNTIME]]
- ↩ [[Home]]

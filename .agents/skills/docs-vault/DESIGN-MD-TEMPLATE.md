# DESIGN.md template (general-purpose)

Reference for [SKILL.md](SKILL.md) Step 6.

This file explains how to derive a spec-compliant `docs/DESIGN.md` from an existing project's design sources. The DESIGN.md spec is [google-labs-code/design.md](https://github.com/google-labs-code/design.md); read its `docs/spec.md` for the normative format definition.

---

## Goal

Produce a `docs/DESIGN.md` that:

1. **Lints clean**, `npx @google/design.md lint docs/DESIGN.md` reports `0 errors, 0 warnings`.
2. **Maps back to the implementation**, token names, values, and component roles correspond to files already in the repo or to explicitly documented brand sources.
3. **Coexists with Obsidian**, frontmatter carries both spec keys and Obsidian metadata (`aliases`, `tags`).
4. **Documents intent, not just current code**, if implementation code reaches for raw values but the brand tokens intend semantic values, tokens encode the intended state and prose calls out the drift.

## Step-by-step derivation

### Step 1, Find the design source of truth

Do not assume a framework, styling library, or file name. Inspect the repository for the source that most directly defines visual language:

```bash
rg --files -g '*token*' -g '*theme*' -g '*style*' -g '*brand*' -g '*design*'
```

Common sources:

- Design token files: `tokens.json`, `design-tokens.*`, `theme.json`, Style Dictionary inputs, Theo inputs, or generated token packages.
- Theme configs: app theme modules, component-library theme files, native/mobile style definitions, package-level theme exports.
- Stylesheets: global styles, variables, preprocessors, resets, typography files, and platform style resources.
- Component primitives: buttons, inputs, cards, alerts, badges, navigation, dialogs, toasts, layout shells.
- Product/brand docs: brand palette, type rules, logo docs, accessibility guidance, Figma exports, or design-system docs.

If several sources conflict, prefer the most intentional source in this order:

1. Committed design token or theme source.
2. Shared component-library primitives.
3. Global stylesheet or platform style resources.
4. Repeated raw values observed in product screens.
5. External brand docs supplied by the user.

Record conflicts in prose instead of silently choosing values.

### Step 2, Read dominant interface primitives

Read the primitives that users or developers reuse most often. Names vary by stack, so search by role instead of framework:

```bash
rg -n "button|input|card|badge|toast|alert|dialog|modal|nav|shell|layout" src app packages lib components ui
```

For each variant, capture:

- Background, foreground, border, focus, and hover/pressed/active state.
- Disabled, loading, destructive, selected, and error states.
- Padding, gap, radius, border width, elevation/shadow/depth.
- Font family, size, weight, line height, letter spacing.
- Motion duration/easing when components animate.

This tells you what the design system currently produces versus what the token source intends.

### Step 3, Read global surface rules

Find app-wide defaults and platform-level resources:

```bash
rg -n "font|background|surface|color|radius|spacing|shadow|elevation|motion|duration|easing" .
```

Look for:

- Font-loading method and fallback stacks.
- Body, root, app shell, or window background and text defaults.
- Light/dark theme switches, high-contrast modes, and density modes.
- Custom properties, constants, enums, or theme accessors used by primitives.
- Design assets that affect tokens, such as icons, illustrations, or logo color constraints.

### Step 4, Decide the semantic palette

Map raw values to semantic token names. The DESIGN.md spec recommends:

| Spec name | Common role |
|-----------|-------------|
| `primary` | Primary action color, selected states |
| `on-primary` | Text/icon on primary fill |
| `primary-container` | Soft brand surface, chips, badges, hover |
| `on-primary-container` | Text on soft surface |
| `secondary` | Secondary action or supporting accent |
| `tertiary` | Editorial, marketing, or tertiary accent |
| `surface` | App body/window background |
| `surface-container-low/medium/high` | Elevation ladder for cards, panels, menus, modals |
| `on-surface` | Primary text on surface |
| `on-surface-variant` | Secondary text |
| `on-surface-muted` | Placeholders, metadata |
| `outline` | Borders, dividers, rings |
| `error` / `success` / `warning` / `info` | Semantic feedback |

**WCAG check before committing:** any foreground/background pair used for normal text must hit >= 4.5:1 contrast. If a brand color is too light or too dark for a role, introduce a role split:

- `primary` = accessible action color.
- `primary-container` = softer brand surface.
- `on-primary` and `on-primary-container` = readable foregrounds for each context.

This preserves brand intent without making inaccessible tokens normative.

### Step 5, Define the typography scale

If the project already codifies typography, use those names and values. If the project relies on repeated raw values, codify the scale this file commits to and mark it as "newly codified" in prose.

Recommended levels (matches the spec's non-normative naming):

```yaml
typography:
  display-lg:   { fontFamily: <display>, fontSize: 48px, fontWeight: 700, lineHeight: 1.1, letterSpacing: -0.02em }
  display-md:   { fontFamily: <display>, fontSize: 36px, fontWeight: 700, lineHeight: 1.15 }
  headline-lg:  { fontFamily: <display>, fontSize: 28px, fontWeight: 600, lineHeight: 1.2 }
  headline-md:  { fontFamily: <display>, fontSize: 22px, fontWeight: 600, lineHeight: 1.3 }
  title-lg:     { fontFamily: <display>, fontSize: 18px, fontWeight: 600, lineHeight: 1.4 }
  title-md:     { fontFamily: <display>, fontSize: 16px, fontWeight: 600, lineHeight: 1.4 }
  body-lg:      { fontFamily: <body>,    fontSize: 16px, fontWeight: 400, lineHeight: 1.5 }
  body-md:      { fontFamily: <body>,    fontSize: 14px, fontWeight: 400, lineHeight: 1.5 }
  body-sm:      { fontFamily: <body>,    fontSize: 13px, fontWeight: 400, lineHeight: 1.5 }
  label-lg:     { fontFamily: <body>,    fontSize: 14px, fontWeight: 500, lineHeight: 1 }
  label-md:     { fontFamily: <body>,    fontSize: 13px, fontWeight: 500, lineHeight: 1 }
  label-sm:     { fontFamily: <body>,    fontSize: 12px, fontWeight: 500, lineHeight: 1 }
  caption:      { fontFamily: <body>,    fontSize: 11px, fontWeight: 400, lineHeight: 1.4, letterSpacing: 0.02em }
  numeric-tabular: { fontFamily: <body>, fontSize: 14px, fontWeight: 500, lineHeight: 1, fontFeature: '"tnum" 1' }
```

If the project ships dynamic numbers such as counters, prices, or timers, include `numeric-tabular` with `fontFeature: '"tnum" 1'`.

### Step 6, Spacing, radius, elevation, and motion

Document the named anchors the project actually uses. Start from existing token names when present; otherwise name repeated values by role:

```yaml
rounded:
  none: 0px
  sm: 4px      # tag, badge
  md: 6px      # input
  lg: 8px      # button, card, dialog
  xl: 12px     # large card
  full: 9999px # pill, avatar

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  input-padding: 10px
  button-medium-x: 20px
  button-medium-y: 10px
  modal-padding: 16px
  card-gap: 16px
```

If the spec or linter version in use supports elevation or motion tokens, include them only when the project has clear source values. Otherwise document those choices in body prose under "Elevation & Depth" and "Components".

### Step 7, Components

Define every visual primitive that varies by tokens. **Reference tokens, never inline hex.** Use `{colors.primary}`, `{rounded.lg}`, `{typography.label-md}`, and equivalent token references.

Minimum component coverage when these roles exist:

- `button-primary` + `-hover` + `-disabled`
- `button-secondary`
- `button-outlined`
- `button-plain` or link-style action
- `button-danger`
- `input-text`
- `card`
- `badge`
- `toast`
- `app-shell`
- `divider`
- `alert-success` / `alert-warning` / `alert-info` / `alert-error`
- Navigation item, tab, menu item, dialog, or sheet when those are core primitives

Every defined color token must be referenced by at least one component, otherwise the linter warns "orphaned-tokens".

### Step 8, Sections in canonical order

```text
1. Overview                          (also: "Brand & Style")
2. Colors
3. Typography
4. Layout                            (also: "Layout & Spacing")
5. Elevation & Depth                 (also: "Elevation")
6. Shapes
7. Components                        (sub-sections OK: Iconography, Animations, etc.)
8. Do's and Don'ts
```

Sections can be omitted, but those present must appear in this order. Do not reorder; the linter checks.

### Step 9, Implementation mapping

Add a final section bridging DESIGN.md tokens back to the project's actual implementation. Name the real source files, package names, generation commands, or consuming APIs:

```markdown
## Implementation mapping

How tokens flow into the implementation:

| Token group | Source of truth | Consumers |
|-------------|-----------------|-----------|
| `colors.*` | `<design-source>` | Buttons, alerts, surfaces, focus states |
| `typography.*` | `<font/theme source>` | Headings, body copy, labels, numeric counters |
| `rounded.*` | `<theme/style source>` | Inputs, cards, dialogs, badges |
| `spacing.*` | `<theme/style source>` | Layout gaps, padding, density rules |
| Component roles | `<component primitive files>` | Product screens, examples, stories |

Convergence loop:

1. Update the source token/theme files.
2. Regenerate any platform-specific theme artifacts if the project has a generator.
3. Update `docs/DESIGN.md` from the same source values.
4. Run `npx @google/design.md lint docs/DESIGN.md`.
```

If the project supports exporting DESIGN.md into a platform theme, document that command here. Do not require an export path when the project has no exporter.

### Step 10, Lint

```bash
npx @google/design.md lint docs/DESIGN.md
```

Fix every error and every warning except `info`-level. Common fixes:

| Finding | Fix |
|---------|-----|
| `contrast-ratio` warning | Split the brand color into accessible action and container roles. Re-test. |
| `orphaned-tokens` warning | Add a component that references the token, or delete the token if it is truly unused. |
| `missing-primary` warning | Define `colors.primary`. |
| `missing-typography` warning | Define at least one `typography.*` entry. |
| `broken-ref` error | A `{path.to.token}` reference does not resolve. Check the path. |
| `section-order` warning | Reorder sections to match the canonical order. |

Re-lint until clean.

## Frontmatter template

```yaml
---
# DESIGN.md spec (google-labs-code/design.md, version: alpha)
# Tokens are normative. Prose explains how to apply them.

# Obsidian metadata (preserved alongside the spec; ignored by the linter)
aliases: [Design, Design System, DESIGN]
tags: [moc, quality]

version: alpha
name: <Project Brand Name>
description: >
  One-paragraph summary of the brand personality, color emphasis, type pairing,
  and theme decision (light / dark / both).

colors:
  primary: "#XXXXXX"            # action color, must pass WCAG AA against on-primary
  on-primary: "#FFFFFF"
  primary-hover: "#XXXXXX"
  primary-container: "#XXXXXX"  # soft brand surface
  on-primary-container: "#XXXXXX"
  # ... + secondary, tertiary, surface ladder, on-surface family,
  # outline, error/success/warning/info

typography:
  display-lg: { ... }
  # ... 9-14 levels total

rounded:
  none: 0px
  sm: 4px
  md: 6px
  lg: 8px
  xl: 12px
  full: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  # + repeated role anchors from the implementation

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.lg}"
    padding: 10px 20px
  # + every other primitive variant
---
```

## Body section template

Each section is short prose followed by token-derivation notes where useful. Do not restate the token values; they are already in the YAML. Explain why the tokens exist, when to use them, and where implementation drift remains.

For an exemplar that lints clean, see the spec's reference samples at [google-labs-code/design.md](https://github.com/google-labs-code/design.md).

# Vault structure reference

Per-file scaffolds for every artifact [SKILL.md](SKILL.md) produces. Copy-paste targets, not normative content.

---

## Vault config (`docs/.obsidian/`)

### `app.json`

```json
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "alwaysUpdateLinks": true,
  "showInlineTitle": true,
  "showFrontmatter": false,
  "promptDelete": true,
  "attachmentFolderPath": "_attachments"
}
```

### `core-plugins.json`

```json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "canvas": true,
  "outgoing-link": true,
  "tag-pane": true,
  "properties": true,
  "page-preview": true,
  "templates": false,
  "note-composer": true,
  "command-palette": true,
  "editor-status": true,
  "bookmarks": true,
  "outline": true,
  "word-count": true,
  "file-recovery": true
}
```

### `community-plugins.json`

```json
[]
```

### `appearance.json`

```json
{
  "baseFontSize": 16,
  "showViewHeader": true
}
```

### `graph.json`

Color groups by tag. Adjust hex/`rgb` values to taste; the structure is what matters.

```json
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    { "query": "tag:#architecture", "color": { "a": 1, "rgb": 14773924 } },
    { "query": "tag:#convention",   "color": { "a": 1, "rgb":  5431518 } },
    { "query": "tag:#workflow",     "color": { "a": 1, "rgb":  3636920 } },
    { "query": "tag:#quality",      "color": { "a": 1, "rgb": 14701138 } },
    { "query": "tag:#adr",          "color": { "a": 1, "rgb": 11823538 } },
    { "query": "tag:#upgrade",      "color": { "a": 1, "rgb": 13312586 } },
    { "query": "tag:#moc",          "color": { "a": 1, "rgb": 16777215 } }
  ],
  "collapse-display": false,
  "showArrow": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1.2,
  "lineSizeMultiplier": 1,
  "collapse-forces": false,
  "centerStrength": 0.5,
  "repelStrength": 12,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": false
}
```

### `bookmarks.json`

Pin Home + 3-4 most-touched entry points.

```json
{
  "items": [
    { "type": "file", "path": "Home.md",                 "title": "Home" },
    { "type": "file", "path": "PRODUCT.md",              "title": "PRODUCT" },
    { "type": "file", "path": "ARCHITECTURE.md",         "title": "ARCHITECTURE" },
    { "type": "file", "path": "DESIGN.md",               "title": "DESIGN" },
    { "type": "file", "path": "upgrades/immediate.md",   "title": "Immediate Upgrades" }
  ]
}
```

---

## `docs/Home.md` (Obsidian MOC)

```markdown
---
aliases: [Vault Home, Index]
tags: [moc]
---

# Home

Obsidian vault for <project>. Open `docs/` as the vault root, `.obsidian/` lives here.

GitHub-facing entry: [README](README.md).
External entry from repo root: [`AGENTS.md`](../AGENTS.md), [`CLAUDE.md`](../CLAUDE.md).

## MOC, start here

### Top-level (flat domain docs)

**Read order:** [[PRODUCT]] → [[RUNTIME]] → [[ARCHITECTURE]] → [[DATA]] → [[AUTH]] → [[ENGINEERING]] → [[TESTING]] → [[DESIGN]]

| File | What it covers |
|------|----------------|
| [[PRODUCT]] | What <project> is, audiences, surfaces, glossary |
| [[RUNTIME]] | Stack, services, env, setup, commands |
| [[ARCHITECTURE]] | Code layout, data flow, state boundary |
| [[DATA]] | DB + validation + cache layer |
| [[AUTH]] | Auth, sessions, role gates |
| [[ENGINEERING]] | Lint, format, language config, hooks, PR flow |
| [[TESTING]] | Test runner, strategy, coverage |
| [[DESIGN]] | Color, type, spacing, components, brand |

### Architecture
- [[overview]] · [[data-layer]] · [[components]] · [[state-*]] · [[auth-session]] · ...

### Conventions
- [[language-style]] · [[styling-system]] · [[naming]] · ...

### Workflows
- [[new-domain]] · [[new-component]] · [[diagnose-bug]] · ...

### Quality
- [[performance]] · [[accessibility]] · [[security]] · [[reliability]] · [[operability]]
- [[design-polish]] · [[audit-checklist]]

### Decisions
- [[Decisions Index]]

### Upgrades
- [[immediate]] · [[backlog]]

## Skills

Skill inventory lives in [`skills-lock.json`](../skills-lock.json) at repo root. Domain docs name the skill they distill inline; open `.agents/skills/<name>/SKILL.md` directly when working in that area.

## Tags drive graph color groups

`#architecture` · `#convention` · `#workflow` · `#quality` · `#adr` · `#upgrade` · `#moc`
```

---

## `docs/README.md` (GitHub folder index)

```markdown
---
aliases: [Vault Home, Home, Index]
tags: [moc]
---

# <project> docs vault

Obsidian-style vault. Open `docs/` as the vault root.

In Obsidian → start at [[Home]]. On GitHub → keep reading.

External entry points: [`AGENTS.md`](../AGENTS.md), [`CLAUDE.md`](../CLAUDE.md).

## Read order (top-level domain docs)

PRODUCT → RUNTIME → ARCHITECTURE → DATA → AUTH → ENGINEERING → TESTING → DESIGN

\`\`\`mermaid
graph TD
  README["README"] --> PRODUCT["PRODUCT"]
  README --> RUNTIME["RUNTIME"]
  README --> ARCHITECTURE["ARCHITECTURE"]
  README --> DATA["DATA"]
  README --> AUTH["AUTH"]
  README --> ENGINEERING["ENGINEERING"]
  README --> TESTING["TESTING"]
  README --> DESIGN["DESIGN"]

  PRODUCT --> ARCHITECTURE
  RUNTIME --> AUTH
  RUNTIME --> DATA
  ARCHITECTURE --> DATA
  ARCHITECTURE --> AUTH
  DATA --> AUTH
  ENGINEERING --> RUNTIME
  ENGINEERING --> TESTING
  DESIGN --> ARCHITECTURE
\`\`\`

Each top-level doc is a short summary that links into the deeper folder content (`architecture/*`, `conventions/*`, `workflows/*`, `quality/*`).

## Folders

\`\`\`
docs/
├── .obsidian/        Obsidian config (graph colors, plugins, bookmarks)
├── Home.md           Vault MOC, open this first in Obsidian
├── README.md         This file, GitHub folder index
│
├── PRODUCT.md        ┐
├── RUNTIME.md        │
├── ARCHITECTURE.md   │  Flat top-level domain summaries
├── DATA.md           │  (each links into the deeper folder docs below)
├── AUTH.md           │
├── ENGINEERING.md    │
├── TESTING.md        │
├── DESIGN.md         ┘
│
├── architecture/     how parts fit (deeper specs)
├── conventions/      rules per layer
├── workflows/        step recipes
├── quality/          perf, accessibility, reliability, security, design polish
├── decisions/        ADRs (lazy)
└── upgrades/         gap analysis vs skill defaults
\`\`\`

Skill inventory lives in [`../skills-lock.json`](../skills-lock.json).
```

---

## Top-level domain doc template

Every top-level (PRODUCT/RUNTIME/ARCHITECTURE/DATA/AUTH/ENGINEERING/TESTING) follows this shape:

```markdown
---
aliases: [<DisplayName>, <ALL_CAPS>]
tags: [moc, <domain-tag>]
---

# <Title>

<One-paragraph summary of what this domain covers in this project.>

---

## <Section 1>
<concrete content>

## <Section 2>
<concrete content>

## ...

---

## See also

- ↑ <up-links to other top-level docs that overlap, if any>
- <wikilinks to deeper folder docs>
- <peer top-level wikilinks>
- ↩ [[Home]]
```

`DESIGN.md` is the exception, see [DESIGN-MD-TEMPLATE.md](DESIGN-MD-TEMPLATE.md).

---

## Folder doc template (architecture / conventions / workflows / quality)

```markdown
---
aliases: [<DisplayName>]
tags: [<folder-tag>]
---

# <Title>

<concrete content>

---

## See also

- ↑ [[<TOP-LEVEL>]] · [[<OPTIONAL_SECOND_TOP>]]
- <peer wikilinks within the same folder>
- ↩ <[[overview]] for architecture/, [[Home]] otherwise>
```

The `↑` line is non-negotiable, it makes the graph bidirectional. See SKILL.md §5.

---

## ADR template (`docs/decisions/<NNNN>-<short-title>.md`)

ADRs are lazy. Only when the decision is hard to reverse, surprising, AND the result of a real trade-off.

```markdown
---
aliases: [<NNNN> <short title>]
tags: [adr]
---

# <NNNN>, <short imperative title>

## Status
proposed | accepted | superseded by <NNNN>

## Context
What's the situation? What forces are at play?

## Decision
The choice we're making and why.

## Consequences
What gets easier, what gets harder, what we now have to maintain.

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
```

---

## Repo-root entry files

### `CLAUDE.md`

```markdown
# CLAUDE.md

Single pointer. Everything else is downstream.

## Read this

→ **[AGENTS.md](AGENTS.md)**, entry point for AI agents working in this repo.

→ **Top-level domain docs** (read in order):
[PRODUCT](docs/PRODUCT.md) → [RUNTIME](docs/RUNTIME.md) → [ARCHITECTURE](docs/ARCHITECTURE.md) → [DATA](docs/DATA.md) → [AUTH](docs/AUTH.md) → [ENGINEERING](docs/ENGINEERING.md) → [TESTING](docs/TESTING.md) → [DESIGN](docs/DESIGN.md).

→ **[docs/README.md](docs/README.md)**, Obsidian vault. Open `docs/` as a vault in Obsidian, `.obsidian/` config is committed (graph color groups by tag, bookmarks, plugin defaults). MOC entry: [docs/Home.md](docs/Home.md).

## Don't

- Don't read `.env` / `.env.local` with agent tools, live secrets. Read `.env.example` instead.
- <other project-specific don'ts>

## Do

- Use installed skills (see `.agents/skills/` and the inventory in [`skills-lock.json`](skills-lock.json)).
- <other project-specific dos>
```

### `AGENTS.md`

Mirror your project's specifics. The shape:

```markdown
# AGENTS.md

Entry point for any AI agent (Claude, Cursor, Aider, Copilot, ...) working in this repo.

## Read this first (top-level domain docs)

Read order: PRODUCT → RUNTIME → ARCHITECTURE → DATA → AUTH → ENGINEERING → TESTING → DESIGN.

| Domain | File | What it covers |
|--------|------|----------------|
| ... | ... | ... |

## Open as Obsidian vault

`docs/` is a real Obsidian vault. From the Obsidian app: **Open folder as vault** → pick `docs/`.

## Stack at a glance

<one-paragraph summary>

## The non-negotiables

- <repo-specific hard rules>

## Where things live

\`\`\`
src/
├── ...
\`\`\`

## Skills

Inventory: [`skills-lock.json`](skills-lock.json) at repo root. Sources installed under `.agents/skills/<name>/SKILL.md`.

The vault does **not** maintain a separate skills index, domain docs name the skill they distill inline. Open the relevant `.agents/skills/<name>/SKILL.md` directly when working in that area.

## Local commands

\`\`\`bash
<commands>
\`\`\`

## See also

- [CLAUDE.md](CLAUDE.md)
- [docs/README.md](docs/README.md)
- [docs/Home.md](docs/Home.md)
- [docs/DESIGN.md](docs/DESIGN.md)
```

---

## Up-link mapping (which folder doc → which top-level)

Use this when wiring `↑ See also` lines:

| Folder doc | Up-links |
|------------|---------|
| `architecture/overview` | `[[ARCHITECTURE]]` |
| `architecture/data-*` | `[[DATA]]` · `[[ARCHITECTURE]]` |
| `architecture/auth-*` | `[[AUTH]]` · `[[ARCHITECTURE]]` |
| `architecture/components` | `[[ARCHITECTURE]]` · `[[DESIGN]]` |
| `architecture/state-*` | `[[ARCHITECTURE]]` |
| `architecture/i18n-*` | `[[DATA]]` · `[[ARCHITECTURE]]` |
| `architecture/infrastructure` | `[[RUNTIME]]` · `[[ARCHITECTURE]]` |
| `conventions/language-style` | `[[ENGINEERING]]` · `[[ARCHITECTURE]]` |
| `conventions/styling-system` | `[[DESIGN]]` |
| `conventions/naming` · `variants` | `[[DESIGN]]` · `[[ENGINEERING]]` |
| `conventions/api-resources` · `background-jobs` · `fetchers` · `query-*` · `schemas-*` · `hooks-*` | `[[DATA]]` |
| `conventions/forms` | `[[DATA]]` · `[[DESIGN]]` |
| `conventions/icons` | `[[DESIGN]]` |
| `conventions/images` | `[[DESIGN]]` · `[[RUNTIME]]` (image host allowlist) |
| `conventions/tests` | `[[TESTING]]` · `[[ENGINEERING]]` |
| `conventions/git-and-pr` | `[[ENGINEERING]]` |
| `workflows/new-domain` | `[[DATA]]` · `[[ENGINEERING]]` |
| `workflows/new-component` | `[[DESIGN]]` · `[[ARCHITECTURE]]` · `[[ENGINEERING]]` |
| `workflows/new-surface` | `[[ARCHITECTURE]]` · `[[ENGINEERING]]` |
| `workflows/diagnose-*` · `tdd` | `[[TESTING]]` · `[[ENGINEERING]]` |
| `workflows/triage-*` · `write-prd` · `grill` | `[[PRODUCT]]` · `[[ENGINEERING]]` |
| `workflows/write-skill` · `ultrareview` | `[[ENGINEERING]]` |
| `quality/performance-budget` | `[[RUNTIME]]` · `[[DESIGN]]` |
| `quality/performance` | `[[RUNTIME]]` · `[[ENGINEERING]]` |
| `quality/accessibility` | `[[DESIGN]]` · `[[ENGINEERING]]` |
| `quality/discoverability` | `[[PRODUCT]]` · `[[RUNTIME]]` |
| `quality/security` | `[[RUNTIME]]` · `[[AUTH]]` · `[[ENGINEERING]]` |
| `quality/audit-checklist` | `[[ENGINEERING]]` · `[[RUNTIME]]` |
| `quality/design-polish` | `[[DESIGN]]` |
| `decisions/<*>` | `[[Decisions Index]]` · `[[ENGINEERING]]` · `[[ARCHITECTURE]]` |
| `upgrades/immediate` · `backlog` | Multi (the doc names the relevant tiers) |

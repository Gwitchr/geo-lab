---
name: docs-vault
description: Build a complete agent-readable Obsidian vault for any software codebase, eight flat top-level domain docs (PRODUCT/RUNTIME/ARCHITECTURE/DATA/AUTH/ENGINEERING/TESTING/DESIGN), folder-level deep specs, bidirectional wikilinks for graph navigation, and a `DESIGN.md` that conforms to the google-labs-code/design.md spec with tokens derived from the project's existing design sources. Use when asked to "set up project docs", "write project documentation", "create an Obsidian vault from this repo", "document this codebase for agents", "add a DESIGN.md", or "make the design system machine-readable".
---

# docs-vault

Build a `docs/` Obsidian vault that's both an Obsidian vault (graph view, backlinks, color-coded tags) and a flat GitHub-readable index. Pair it with a `DESIGN.md` that follows the [google-labs-code/design.md](https://github.com/google-labs-code/design.md) spec so the design system becomes machine-readable.

TRIGGER when: bootstrapping documentation for an application, service, library, platform, or multi-package repository; introducing a flat top-level domain-doc pattern over an existing tangle of docs; or making the design system machine-readable for agents.

> **Stack assumed.** None. Inspect the repository first and adapt the docs to the language, framework, package manager, runtime, UI layer, infrastructure, and test stack actually present.

> **Notation.** `<project>`, `docs/`, `<design-source>`, `<NNNN>` are placeholders. Resolve to the project's actual project name, root, design token/theme source, and ADR numbering scheme. Frontmatter examples (`aliases`, `tags`) follow Obsidian conventions, adjust to whatever tag taxonomy your team prefers.

> **Precedence.** Project rules (CLAUDE.md / AGENTS.md / contributing guide) win. This skill produces those files for projects that don't have them; if they already exist, extend rather than replace.

> **Scope.** Skill is about *how* to write the docs and *which* docs. The content of any given doc is the project's own; this skill provides the structure, the read order, the link conventions, and the DESIGN.md template.

---

## Outputs

When this skill finishes, the repo has:

```
CLAUDE.md                       single pointer (3 lines, points at AGENTS.md)
AGENTS.md                       primary entry for any AI agent
docs/
├── .obsidian/                  vault config (committed)
│   ├── app.json
│   ├── core-plugins.json
│   ├── community-plugins.json
│   ├── graph.json              color groups by tag
│   ├── appearance.json
│   └── bookmarks.json
├── Home.md                     Obsidian MOC (alias: Vault Home)
├── README.md                   GitHub folder index (mermaid map)
│
├── PRODUCT.md                  ┐
├── RUNTIME.md                  │
├── ARCHITECTURE.md             │  Flat top-level domain docs.
├── DATA.md                     │  Each is a short summary (~50-150 lines)
├── AUTH.md                     │  that links into the deeper folder content.
├── ENGINEERING.md              │
├── TESTING.md                  │
├── DESIGN.md                   ┘  ← spec-compliant (google-labs-code/design.md)
│
├── architecture/               deeper specs per domain
├── conventions/                rules per layer (language, styling, data access, ...)
├── workflows/                  step recipes (new-domain, diagnose-bug, ...)
├── quality/                    perf, accessibility, reliability, security, design polish
├── decisions/                  ADRs (lazy)
└── upgrades/                   gap analysis vs skill defaults
```

## Workflow

### 1. Sweep the codebase (read, don't write yet)

Before writing a single doc, read enough to map the project:

- **Surfaces**, list screens, routes, CLIs, APIs, jobs, packages, or user-facing entry points; identify public vs restricted surfaces.
- **Stack**, manifest files, language/runtime config, dependency manager files, workspace config, database schemas, infrastructure manifests, and design token/theme sources if present.
- **Entry points**, app/server/CLI/library entry files, provider/bootstrap files, global styles, config loaders, and deployment adapters.
- **Interface primitives**, components, views, screens, templates, API resources, command handlers, or other primary user/developer-facing building blocks.
- **Data layer**, persistence, validation, caching, service clients, query modules, schema files, and equivalent abstractions.
- **CI / tooling**, workflow files, hooks, lint/format/test/build configs, release automation.
- **Existing docs**, `README.md`, anything in `docs/`. **Don't overwrite.** If they exist, extend.

Use Glob + Grep + Read in parallel. Don't open every file, open enough to fill out PRODUCT/RUNTIME/ARCHITECTURE.

### 2. Create vault config

Drop `.obsidian/` into `docs/` so opening the folder in Obsidian works immediately. Templates: see [VAULT-STRUCTURE.md](VAULT-STRUCTURE.md) §Vault config.

Required: `app.json` (sets `useMarkdownLinks: false` so wikilinks are the default), `core-plugins.json` (graph/backlinks/tag-pane on), `graph.json` (color groups by tag).

### 3. Write the eight top-level domain docs (flat)

Order, and what each must cover:

| File | Covers | Lines target |
|------|--------|--------------|
| `PRODUCT.md` | Audiences (roles), surfaces (screens/routes/APIs/commands), domain glossary, revenue model, open questions | 60-120 |
| `RUNTIME.md` | Stack, services, env vars, local setup, available commands, deploy target | 80-150 |
| `ARCHITECTURE.md` | Code layout tree, canonical data flow, state boundaries, ownership boundaries | 50-100 |
| `DATA.md` | DB choice, ORM, validation lib, query cache, layers, naming conventions | 70-150 |
| `AUTH.md` | Auth/session system, credential shape, role gating, access patterns | 40-80 |
| `ENGINEERING.md` | Daily commands, lint/format rules, language config, hooks, Git/PR style, CI | 60-110 |
| `TESTING.md` | Test runner, co-location, behavior-over-impl, mocking guidance, coverage | 50-90 |
| `DESIGN.md` | Spec-compliant. See [DESIGN-MD-TEMPLATE.md](DESIGN-MD-TEMPLATE.md). | 200-400 |

**Frontmatter on every file:**

```yaml
---
aliases: [Display Name, Alternative Name]
tags: [moc, architecture]   # see tag list below
---
```

Each top-level file is a **summary that links into deeper folder content**. Don't duplicate, link. The `architecture/data-layer.md` deep doc may be 200 lines; `DATA.md` is 100 lines and points at it.

**Read order goes in `Home.md` and `AGENTS.md`:** PRODUCT → RUNTIME → ARCHITECTURE → DATA → AUTH → ENGINEERING → TESTING → DESIGN.

### 4. Write folder docs (deeper specs)

Folders + tag mapping:

| Folder | Tag | Up-link target(s) |
|--------|-----|-------------------|
| `architecture/` | `#architecture` | `[[ARCHITECTURE]]` (+ `[[DATA]]`, `[[AUTH]]`, `[[RUNTIME]]` per topic) |
| `conventions/` | `#convention` | `[[ENGINEERING]]`, `[[DESIGN]]`, `[[DATA]]`, `[[TESTING]]` per topic |
| `workflows/` | `#workflow` | `[[ENGINEERING]]` + the topic top-level (`[[DATA]]`, `[[DESIGN]]`, `[[TESTING]]`) |
| `quality/` | `#quality` | `[[DESIGN]]`, `[[RUNTIME]]`, `[[ENGINEERING]]` per topic |
| `decisions/` | `#adr` | `[[ENGINEERING]]` · `[[ARCHITECTURE]]` |
| `upgrades/` | `#upgrade` | Multi (the doc lists the relevant tiers) |

Per-file scaffolds (overview, conventions, workflows, quality, decisions, upgrades): see [VAULT-STRUCTURE.md](VAULT-STRUCTURE.md).

### 5. Wire bidirectional links

For Obsidian's graph + backlinks panel to work well:

- **Wikilinks `[[file]]`** for in-vault navigation. Obsidian resolves by basename; aliases let you target by display name.
- **External markdown links** for files outside the vault (`../AGENTS.md`, `../package.json`).
- **Every folder doc has a `↑ up-link`** in its **See also** section pointing to its parent top-level file:

```markdown
## See also

- ↑ [[DATA]] · [[ENGINEERING]]
- (peer wikilinks)
- ↩ [[overview]]   (or [[Home]])
```

- **Every top-level domain doc has a See also** linking to its deep docs and to peer top-levels.

### 6. Write the spec-compliant `DESIGN.md`

Follow [DESIGN-MD-TEMPLATE.md](DESIGN-MD-TEMPLATE.md). Hard requirements:

1. **YAML frontmatter** with the canonical token schema (`colors`, `typography`, `rounded`, `spacing`, `components`).
2. **Token values derived from existing project sources** (design token files, theme configs, CSS variables, component styles, native/mobile style definitions, Figma exports, brand docs), not invented. The template explains the derivation step-by-step.
3. **Sections in canonical order:** Overview → Colors → Typography → Layout → Elevation & Depth → Shapes → Components → Do's and Don'ts.
4. **`primary` must pass WCAG AA contrast against `on-primary`** (4.5:1). If the brand color is too light/dark, introduce a `primary` / `primary-container` split (Material-style).
5. **Component definitions reference tokens** via `{colors.primary}`, `{rounded.lg}`, `{typography.label-md}`. No hex values inside the `components:` block except for `transparent` and `rgba(...)`.
6. **Lint clean**, `npx @google/design.md lint docs/DESIGN.md` reports `0 errors, 0 warnings`.
7. **Obsidian frontmatter (`aliases`, `tags`)** lives alongside spec keys, the YAML parser accepts unknown keys.

### 7. Refresh entry files

After the vault exists, update / create:

- **`CLAUDE.md`** at repo root, 3-line pointer to `AGENTS.md` and `docs/README.md`.
- **`AGENTS.md`** at repo root, entry for any agent. Read-order table + non-negotiables + skill discipline (point at `skills-lock.json` if applicable; do NOT maintain a separate skills index in the vault, it creates SKILL graph noise).
- **`docs/README.md`**, GitHub-facing folder index with a mermaid graph and the folder map.
- **`docs/Home.md`**, Obsidian MOC (alias `Vault Home`). Top section lists all 8 top-level docs with a one-line description each.
- **`docs/.obsidian/bookmarks.json`**, pin Home + 3-4 most-touched files (PRODUCT, ARCHITECTURE, DESIGN, "Immediate upgrades" if you wrote one).

## Tag set (drives Obsidian graph color groups)

```
#moc          , index / map-of-content files (Home, README, top-level domain docs)
#architecture , architecture/* + ARCHITECTURE.md
#convention   , conventions/* + ENGINEERING.md
#workflow     , workflows/*
#quality      , quality/* + DESIGN.md (also #moc)
#adr          , decisions/*
#upgrade      , upgrades/*
```

`graph.json` (provided in [VAULT-STRUCTURE.md](VAULT-STRUCTURE.md)) maps each tag to a color group.

## Hard rules

- **Never** put SKILL.md backlinks (`🌐 Live skill: [name](.../SKILL.md)`) in vault docs, every link to a `SKILL.md` becomes a "SKILL" node in the graph view, clustering visual noise. Reference skills as plain code-fenced text (`` `zod-prisma-tanstack` ``) and point readers at `skills-lock.json` once at the top level.
- **Never** maintain a parallel skills index inside the vault. `skills-lock.json` is the inventory. The relevant skill name is mentioned inline in the doc that distills it.
- **Never** invent token values for `DESIGN.md`, derive from the project's existing design sources and call out drift in prose.
- **Never** skip the `↑ up-link` in folder docs, the graph becomes one-directional and the backlinks panel becomes the only path back up.
- **Never** use broad transitions, ad-hoc type sizes, or hardcoded brand values outside the project's token/theme source; flag those in the DESIGN.md "Do's and Don'ts" so agents reading the file produce code that matches.
- **Never** read `.env` / `.env.local` while writing docs. Read `.env.example` and ask the user for live values.

## Anti-patterns

- ❌ A single 1000-line `docs/INDEX.md` with everything inline. Split into the 8 top-level domain files; each links into its folder.
- ❌ Top-level docs that duplicate folder content. Top-level summarizes; folder doc is the deep spec.
- ❌ Folder docs that don't link up to their top-level parent (graph becomes one-directional).
- ❌ DESIGN.md that defines tokens but no components, every color token should be referenced by at least one component (the linter flags orphans).
- ❌ DESIGN.md `primary` with white text but contrast < 4.5:1, split into `primary` (action) and `primary-container` (soft surface) so the brand color survives both contexts.
- ❌ Wikilinks pointing to ambiguous basenames (e.g. multiple `README.md` files). Use frontmatter aliases (`Vault Home`, `Skills Index`) and reference by alias.
- ❌ Markdown links to `.agents/skills/<name>/SKILL.md` from inside the vault. Plain code-fenced reference only.
- ❌ Inventing typography levels not present in the project. If the project hasn't codified a typography scale, define one in DESIGN.md based on the dominant atoms and call it out as "newly codified" in prose.

## Checklist (before declaring done)

- [ ] `docs/.obsidian/` committed with at least `app.json`, `core-plugins.json`, `graph.json`, `bookmarks.json`
- [ ] `docs/Home.md` exists with `aliases: [Vault Home]` and lists all 8 top-level docs
- [ ] `docs/README.md` exists with a mermaid graph + folder map (GitHub-renderable)
- [ ] All 8 top-level docs exist with frontmatter (`aliases`, `tags`)
- [ ] Every folder doc has a `↑ up-link` in its **See also** section
- [ ] No `🌐 Live skill: [...](.../SKILL.md)` links anywhere in the vault
- [ ] `npx @google/design.md lint docs/DESIGN.md` → `0 errors, 0 warnings`
- [ ] `CLAUDE.md` and `AGENTS.md` exist at repo root and point at the vault
- [ ] Read order is documented in **both** `Home.md` and `AGENTS.md`
- [ ] Tags applied consistently per the tag set table

## Reference files

- [VAULT-STRUCTURE.md](VAULT-STRUCTURE.md), full file inventory + per-file scaffolds (`.obsidian/*.json`, top-level templates, folder doc templates)
- [DESIGN-MD-TEMPLATE.md](DESIGN-MD-TEMPLATE.md), general-purpose DESIGN.md template + step-by-step token derivation from the project's existing design sources

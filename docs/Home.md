---
aliases: [Vault Home, Index]
tags: [moc]
---

# Home

Obsidian vault for **geo-lab**. Open `docs/` as the vault root — `.obsidian/` lives here
(graph colour groups by tag, backlinks, bookmarks, plugin defaults, all committed).

GitHub-facing entry: [README](README.md).
From the repo root: [`AGENTS.md`](../AGENTS.md) · [`CLAUDE.md`](../CLAUDE.md) ·
[project README](../README.md).

---

## Start here

**Read order:** [[PRODUCT]] → [[RUNTIME]] → [[ARCHITECTURE]] → [[DATA]] → [[AUTH]] →
[[ENGINEERING]] → [[TESTING]] → [[DESIGN]]

| File | What it covers |
|------|----------------|
| [[PRODUCT]] | What geo-lab is, audiences, the three surfaces, domain glossary, roadmap |
| [[RUNTIME]] | Stack, commands, the one env var, local setup, GitHub Pages deploy, CI |
| [[ARCHITECTURE]] | Code layout, the dataflow, state and ownership boundaries |
| [[DATA]] | SQLite, the `listings` schema, the pipeline layers, real-vs-synthetic provenance |
| [[AUTH]] | **There is none** — and the trust boundaries that exist anyway |
| [[ENGINEERING]] | Daily commands, language rules, CI, the non-negotiables |
| [[TESTING]] | Three runners, and why the fastgeo parity suite is load-bearing |
| [[DESIGN]] | Tokens, type scale, components — spec-compliant, derived from `style.css` |

## Architecture

[[overview]] · [[pipeline]] · [[fastgeo]] · [[query-engine]] · [[web-app]] · [[contracts]]

## Conventions

[[typescript-style]] · [[python-style]] · [[cpp-native]] · [[styling-system]] · [[git-and-pr]]

## Workflows

[[regenerate-data]] · [[add-a-filter-field]] · [[add-a-region]] · [[build-fastgeo]] ·
[[diagnose-parity-failure]]

## Quality

[[performance]] · [[accessibility]] · [[security]] · [[data-integrity]]

## Decisions

[[Decisions Index]] — [[0001-hand-written-filter-parser]] ·
[[0002-cpp-fastgeo-via-pybind11]] · [[0003-fp-contract-off-for-parity]] ·
[[0004-commit-built-artifacts]] · [[0005-dup-of-is-a-label]]

## Upgrades

[[immediate]] · [[backlog]]

## Long-form references

These predate the vault and remain the canonical deep sources. They are wired into the graph:

| File | What it is |
|---|---|
| [[filter-language]] | The full `geoq` query grammar — fields, operators, values, errors |
| [[data-notes]] | Dataset provenance: source URLs, retrieval dates, licenses, processing applied |
| [[dev-notes]] | The author's running log — decisions, benchmarks, calibration tables, mistakes worth not repeating. **The richest "why" source in the repo.** |

---

## Skills

The skill inventory lives in [`skills-lock.json`](../skills-lock.json) at the repo root.
Domain docs name the skill they distill inline; open `.agents/skills/<name>/SKILL.md`
directly when working in that area. This vault deliberately keeps **no** parallel skills
index.

## Tags → graph colour groups

`#moc` · `#architecture` · `#convention` · `#workflow` · `#quality` · `#adr` · `#upgrade`

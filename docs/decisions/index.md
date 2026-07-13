---
aliases: [Decisions Index]
tags: [adr, moc]
---

# Decisions Index

Architecture decision records for geo-lab. Each one captures a choice that was
genuinely contested — where the alternative was reasonable, the reasoning is
not obvious from the code, and undoing it later would cost real work.

The long-form reasoning, benchmarks, and verification transcripts these are
distilled from live in [[dev-notes]]; dataset provenance lives in
[[data-notes]].

## The ADRs

| # | Title | Status |
|---|---|---|
| [[0001-hand-written-filter-parser\|0001]] | Hand-write the filter language's lexer, parser, and eval | accepted |
| [[0002-cpp-fastgeo-via-pybind11\|0002]] | Write the spatial hot loops in C++ behind pybind11 | accepted |
| [[0003-fp-contract-off-for-parity\|0003]] | Compile fastgeo with `-ffp-contract=off` | accepted |
| [[0004-commit-built-artifacts\|0004]] | Commit `data/db.sqlite` and `web/public/listings.json` | accepted |
| [[0005-dup-of-is-a-label\|0005]] | Treat `dup_of` as a label, not a filter | accepted |

## The bar for a new ADR

Write one **only** when all three hold:

1. **Hard to reverse.** Undoing it means touching several components, migrating
   data, or re-verifying a build — not editing one function.
2. **Surprising.** A competent reader of the code would ask "why on earth is
   this here?" A flag like `-ffp-contract=off` qualifies; a naming convention
   does not.
3. **The result of a real trade-off.** Something was genuinely given up. If
   there was no losing option, there is no decision to record — it is just how
   the thing works, and it belongs in [[ARCHITECTURE]] or the component doc.

Everything else — running notes, benchmarks, calibration tables, mistakes,
"known limitations I'm sitting on" — goes in [[dev-notes]], not here. An ADR
that fails the bar is noise in the index and makes the ones that pass it
easier to ignore.

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- Components the ADRs cover: [[query-engine]] · [[fastgeo]] · [[pipeline]] ·
  [[web-app]] · [[contracts]]
- Background: [[dev-notes]] · [[data-notes]] · [[filter-language]]
- ↩ [[Home]]

---
aliases: [0005 dup_of is a label]
tags: [adr]
---

# 0005, Treat `dup_of` as a label, not a filter

## Status

accepted

## Context

The synthetic listings deliberately contain near-duplicate re-listings, and
`pipeline/dedupe.py` finds them: simhash over the description, refined by
distance, municipio, type, and m2 agreement. Calibrated against the generator's
own ground-truth mapping at full scale, the shipped thresholds
(`hamming≤12, dist≤120m, m2 tol≤2`) flag **2,492** rows at 96.2% precision /
95.9% recall.

The question is what "found a duplicate" should *do*. Deleting the row is the
tempting answer, and it is irreversible: a false positive (94 of them, at these
thresholds) silently destroys a real listing, and re-tuning the thresholds later
means rebuilding the database from raw.

## Decision

Dedupe is **non-destructive**. It sets a column, it never deletes:

- `dup_of` marks the row that is the near-duplicate, pointing at its canonical
  row.
- The **canonical row is the earliest `listed_date`** in the cluster — the
  original listing, not the re-list.
- All **100,000** cleaned rows stay in `listings`. Nothing is removed.

Filtering is then each consumer's call, not the table's.

## Consequences

Easier: the flag is reversible. Re-calibrating thresholds is a re-run of
`dedupe.py`, not a rebuild from raw. A false positive hides a row from some
views; it does not destroy it. The ground-truth precision/recall measurement is
possible at all because both sides of every flagged pair survive.

Harder — and this is the **known asymmetry**, deliberate and revisitable:

- `pipeline/stats.py` and `pipeline/export_web.py` both exclude
  `dup_of IS NOT NULL` from every aggregate and from the web export.
- `geoq query` reads the raw `listings` table **unfiltered**. So it currently
  includes the 2,492 flagged near-duplicates in its results and its counts,
  unlike the other two consumers.

Same database, two different answers to "how many listings are there," depending
on which tool you asked. That is a scope boundary, not an oversight — making
dedupe table-wide rather than per-consumer is a `cli/`-side call that has not
needed making yet. Anyone comparing a `geoq` count against `stats.json` should
know why they differ.

---

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
- [[pipeline]] · [[query-engine]] · [[DATA]] · [[contracts]] · [[dev-notes]]
- ↩ [[Home]]

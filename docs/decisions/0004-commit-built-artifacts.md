---
aliases: [0004 Commit built artifacts]
tags: [adr]
---

# 0004, Commit `data/db.sqlite` and `web/public/listings.json`

## Status

accepted

## Context

Both files are build outputs. `data/db.sqlite` comes from `pipeline/ingest.py` +
`enrich.py` (100,000 rows in `listings`); `web/public/listings.json` comes from
`pipeline/export_web.py` (5,000 rows, newest-listed first). Build outputs
normally do not belong in git — `.gitignore` already excludes `dist/`, `build/`,
`__pycache__/`, `.venv*/`.

But regenerating them means a Python venv and four scripts run in order. Making
a visitor do that before they can see anything is a lot of friction for a repo
whose whole point is that you can look at it.

Weighing against: repo size, and the risk of the committed artifact silently
drifting from the pipeline that produces it. `db.sqlite` was **52,944,896
bytes** as first built — over GitHub's 50 MB warning threshold, which would have
pushed the question toward git-lfs.

## Decision

Commit both, on purpose. `.gitignore` carries an explicit note so nobody
"fixes" it:

```
# sqlite runtime artifacts (data/db.sqlite itself is committed by design)
*.sqlite-journal
```

`sqlite3 data/db.sqlite "VACUUM;"` brought it from 52,944,896 → **47,869,952
bytes (~45.65 MB)**, row counts unchanged at 100,000. That is back under the
warning threshold, so no git-lfs.

A fresh clone therefore runs the web app and the CLI with **no Python setup at
all** — verified by copying the tree to a scratch directory and following the
README quickstart literally.

## Consequences

Easier: the README quickstart is true from a cold clone. The web dev server
serves 5,000 real listings immediately; `geoq` queries a real 100k-row database.
CI's `web-test` and `cli-test` jobs need no pipeline run.

Harder — this is the maintenance debt:

- **Both files must be regenerated and re-committed whenever the pipeline
  changes.** A schema change in `ingest.py`, a new column, a different dedupe
  threshold — the committed artifacts are now stale until someone re-runs
  `ingest.py` → `enrich.py` → `stats.py` → `export_web.py` and commits the
  result.
- **VACUUM is part of that ritual**, not an optimization. Skip it and the db
  drifts back over 50 MB.
- Every regeneration is a large binary diff in git history. Acceptable at this
  cadence; would not be if the pipeline changed weekly.

---

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
- [[pipeline]] · [[web-app]] · [[DATA]] · [[contracts]] · [[data-notes]] · [[dev-notes]]
- ↩ [[Home]]

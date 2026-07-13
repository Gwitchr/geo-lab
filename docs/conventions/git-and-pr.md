---
aliases: [Git & PRs]
tags: [convention]
---

# Git & PRs

Single-author personal repo. Work lands on **`main`**. No review gate, no
CODEOWNERS, no changelog — the discipline lives in the commit messages, the four
CI jobs, and [[dev-notes]].

## Commit style

Lowercase `area: summary`, imperative-ish, one line, no trailing period. The
areas are the repo's own components, not Conventional Commits types. Straight
from `git log`:

```
web: fix asset paths for GitHub Pages' /geo-lab/ base path
cli: align typescript version with web (7.x breaks typescript-eslint's peer range there)
ci: deploy web/ to GitHub Pages
native: parity suite (compiled vs python reference)
pipeline: enrich.py assigns listings to their AGEB + marginación grade
docs: filter language grammar
notes: fastgeo + the FP contraction bug
readme: rewrite for a visitor
```

Areas in use: `web:`, `cli:`, `pipeline:`, `native:`, `ci:`, `docs:`, `notes:`,
`readme:`, and occasionally a narrower one for a single module (`eval:`,
`dedupe:`). A bare summary with no prefix is fine when the change genuinely
isn't scoped to one area (`add MIT license`, `wire the real pipeline export into
the web app`, `run enrich.py for real, VACUUM the db`).

Say **why** in the subject when the why is the point — `cli: align typescript
version with web (7.x breaks typescript-eslint's peer range there)` is the model
here. Longer reasoning, benchmark numbers, and calibration tables go in
`docs/dev-notes.md`, and the `notes:` prefix is for commits that do exactly
that.

Accented Spanish (`marginación`, `colonia`) in messages is fine and expected.

## Before you commit

CI (`.github/workflows/ci.yml`) must be green. **Four jobs**, all
`ubuntu-latest`, on push to `main` and on every PR:

| job | what it runs |
|---|---|
| `web-test` | `npm ci` → `npm run lint` → `npm test` → `npm run build` in `web/` |
| `cli-test` | `npm ci` → `tsc -p tsconfig.json --noEmit` → `tsc -p tsconfig.test.json --noEmit` → `npm test` → `npm run build` in `cli/` |
| `pipeline-test` | `pip install pytest` → `python3 -m pytest -q` in `pipeline/` (no fastgeo build; parity skips via `importorskip`) |
| `native-build` | `pip install ./pipeline/native` → `pytest tests/test_parity.py -v` |

Run the affected job's steps locally first — that's the established habit here
(every job was run locally before it was ever pushed; see [[dev-notes]]'s final
verification sweep). A separate `pages.yml` deploys `web/` to GitHub Pages on
push to `main`.

## Never commit

- **Secrets.** There are none in this repo and none are needed — no API keys, no
  tokens, no `.env`.
- **Machine-local absolute paths.** No `/Users/<me>/…` in tracked files; paths
  resolve from the repo root or from `process.cwd()` / `Path(__file__)`.
- `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.pytest_cache/`,
  `.venv*/`, `*.egg-info/`, `*.sqlite-journal`, `.DS_Store` — all in
  `.gitignore`.

## Committed build artifacts (on purpose)

Two generated files are tracked deliberately, so the web app and `geoq` work
straight off a clone with no Python setup:

- **`data/db.sqlite`** — ~100k rows, ~45.65 MB after `VACUUM` (kept under
  GitHub's 50 MB warning threshold; VACUUM before committing a rebuild, no
  git-lfs).
- **`web/public/listings.json`** — the 5,000-row export produced by
  `pipeline/export_web.py`.

They are explicitly *not* gitignored. The consequence: **when the pipeline
changes, regenerate and re-commit them in the same change**, or the repo ships a
db that no longer matches the code that built it.

```sh
python3 data/gen/gen_listings.py     # only if the generator changed
python3 pipeline/ingest.py
python3 pipeline/enrich.py
python3 pipeline/stats.py
python3 pipeline/export_web.py
sqlite3 data/db.sqlite "VACUUM;"
git add data/db.sqlite web/public/listings.json pipeline/stats.json
```

Generator output must stay byte-reproducible from its fixed seed
([[python-style]]); if a change moves those numbers, record the new baseline in
[[dev-notes]] rather than silently landing a different dataset.

## Keeping the docs honest

The README quickstart is kept **literally true** — if you change a command, a
path, or a count, change the README (and `docs/development.md`) in the same
commit. Same for the invariants list: parity green both ways, CI green,
AGEB assignment ≥95%, no secrets, no local paths.

---

## See also

- ↑ [[ENGINEERING]]
- [[typescript-style]] · [[python-style]] · [[cpp-native]] · [[styling-system]]
- ↩ [[Home]]

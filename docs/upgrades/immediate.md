---
aliases: [Immediate Upgrades]
tags: [upgrade]
---

# Immediate Upgrades

The gap list worth doing next. Every entry is something the repo already records
as a known limitation, an unverified claim, or a deliberate "not yet". Sources:
`README.md`'s Roadmap, `docs/dev-notes.md` ("Known limitations I'm sitting on for
now", "Not verified yet"), `docs/development.md`. Effort: **S** = an afternoon,
**M** = a focused day or two, **L** = a real chunk of work with design decisions
in it.

## 1. Keyboard operability of the sortable table headers

- **What** — the sortable `<th>`s announce themselves as interactive but can't be
  operated from the keyboard. `renderTableHead()` sets `th.tabIndex = 0` and
  `role="button"`, then attaches only a `click` listener — no `keydown` handler
  for Enter/Space, and no `aria-sort` on the sorted column. The current sort is
  conveyed purely through the `sorted-asc` / `sorted-desc` CSS classes.
- **Why it matters** — a focusable `role="button"` that does nothing on Enter is
  worse than a plain `<th>`: it puts a stop in the tab order that leads nowhere.
  And a screen-reader user gets no signal about which column is sorted or in
  which direction, because the only signal is visual.
- **Where** — `web/src/main.ts` (`renderTableHead()`, `onSortClick()`);
  `web/src/style.css` for the `.sorted-*` rules.
- **Effort** — **S**. A `keydown` handler plus `aria-sort` on the active column,
  and a vitest case covering both. See [[accessibility]].

## 2. Never-observed CI (and never-observed Pages deploy)

- **What** — four CI jobs and a Pages workflow are authored and committed, but no
  GitHub Actions run has ever been watched. Dev-notes' "Not verified yet" is
  explicit: every job's steps were rehearsed **locally on macOS arm64**, not on
  the `ubuntu-latest` runner CI actually uses. No Pages deploy has been seen
  either — the `/geo-lab/` base-path fix was verified by *grepping the built
  bundle's asset URLs*, not by loading a deployed page.
- **Why it matters** — two named places Linux could still surprise us. First,
  `native-build`: the compile has only ever been proven against **AppleClang** on
  arm64, and the `-ffp-contract=off` flag that keeps boundary-point parity green
  is compiler-specific behavior — GCC/Clang on x86-64 is a genuinely different FP
  code path, and a parity failure there is a real correctness bug, not a flake.
  Second, Pages: a base-path bug that only manifests when served from `/geo-lab/`
  is exactly what bundle inspection can miss. `docs/development.md` lists "CI (all
  four jobs) green on main" as an invariant — today it is an *aspiration*.
- **Where** — `.github/workflows/ci.yml`, `.github/workflows/pages.yml`,
  `web/vite.config.ts` (`base`), `web/src/data.ts` (`loadListings()`'s
  `import.meta.env.BASE_URL` default).
- **Effort** — **S** to trigger and watch (push, enable Pages, read the logs);
  **M** if Linux or the deploy does surprise us. Highest value here purely because
  it converts several unverified claims into verified ones for near-zero cost.

## 3. `geoq` counts near-duplicates; the pipeline doesn't

- **What** — `dup_of` is a label, not a filter. All 100,000 cleaned rows stay in
  `listings`. `stats.py` and `export_web.py` exclude `dup_of IS NOT NULL`;
  `geoq query` reads the raw table **unfiltered**, so the 2,492 flagged
  near-duplicates land in its results and its counts.
- **Why it matters** — the same question asked two ways gives two different
  answers, and neither surface says so. Dev-notes calls it a deliberate scope
  boundary, but the decision is the deliverable: should dedup be **table-wide** (a
  view, or a default `WHERE dup_of IS NULL` in the query compiler) or stay
  **per-consumer**? Either is defensible; the silent drift between them isn't.
- **Where** — `pipeline/dedupe.py` (sets it), `pipeline/stats.py` +
  `pipeline/export_web.py` (exclude it), `cli/src/parser/eval.ts` (builds the
  `WHERE` clause), `cli/src/commands/` (where a flag would land). See
  [[data-integrity]] and [[contracts]].
- **Effort** — **M**. The code change is small; the call is the work, and it
  touches a documented cross-boundary contract.

## 4. No repo-root auto-detection for `geoq --db`

- **What** — `--db` resolves against `process.cwd()` (`path.resolve(process.cwd(),
  dbPath)` in `cli/src/db.ts`), with no walk up the tree for a repo root. Run
  `geoq` from anywhere but the root without an explicit `--db` and it fails.
- **Why it matters** — small, but it's the first thing a new user trips over, and
  the README's quickstart has to route around it (`--db ../data/db.sqlite`). The
  error message is already good, which is the only reason this isn't higher.
- **Where** — `cli/src/db.ts` (`openDb()`, `DEFAULT_DB_PATH`).
- **Effort** — **S**. Walk parent dirs for a marker (`.git/`, or
  `data/db.sqlite` itself) before falling back to today's behavior.

## 5. No lint script in `cli/`

- **What** — `web/package.json` has `lint` (`eslint .`) and CI runs it;
  `cli/package.json` has only `dev`, `build`, `start`, `test`, `test:watch`.
- **Why it matters** — the two TypeScript packages are held to different standards
  for no reason but inertia. `cli/` is the larger and more intricate of the two —
  a hand-written lexer, parser, and SQL compiler — so it's the *less* obvious one
  to leave unlinted.
- **Where** — `cli/package.json`, a new `cli/eslint.config.js` mirroring
  `web/eslint.config.js`, and `.github/workflows/ci.yml`'s `cli-test` job (add the
  `npm run lint` step `web-test` already has). TypeScript is pinned to `^6.0.3` in
  both packages precisely because of `typescript-eslint`'s peer range — read
  [[dev-notes]] before bumping anything.
- **Effort** — **S**.

## Done / verified — don't re-do these

Recorded green in dev-notes' "Final verification sweep":

- **Four CI jobs authored** — `web-test`, `cli-test`, `pipeline-test`,
  `native-build`, plus `pages.yml`. Every job's steps were executed locally before
  the push, including a `native-build` simulation from a genuinely clean venv.
  (Authored and *locally rehearsed* — gap #2 is what's still missing.)
- **Byte-reproducible generator** — `gen_listings.py` run twice, `sha256sum
  data/raw/*.csv` diffed: BYTE IDENTICAL.
- **Parity suite green both ways** — `test_parity.py`: 13 passed compiled, 1
  skipped under `FASTGEO_FORCE_FALLBACK=1` (by design — nothing to compare a
  fallback against). Full suites: web 25/25, cli 89/89, pipeline 64 compiled /
  51 + 1 skipped fallback.
- **Fresh-clone quickstart simulated** — tree copied without `node_modules/`,
  `.venv*/`, `dist/`, `.git/`; README Quickstart followed literally, including the
  optional regenerate-from-scratch section. Same counts throughout (100,000 kept,
  750 dropped, 2,492 duplicates, 99.97% AGEB assignment, 5,000 rows served).

Longer-horizon items — roadmap layers, the spatial index, marker clustering, real
GDL/MTY price baselines — are in [[backlog]].

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]] · [[PRODUCT]] · [[DESIGN]]
- [[backlog]] (the peer)
- Reference: [[dev-notes]] · [[accessibility]] · [[TESTING]] · [[web-app]] · [[query-engine]]
- ↩ [[Home]]

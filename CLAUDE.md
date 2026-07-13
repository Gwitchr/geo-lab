# CLAUDE.md

Single pointer. Everything else is downstream.

## Read this

→ **[AGENTS.md](AGENTS.md)** — entry point for AI agents working in this repo.

→ **Top-level domain docs** (read in order):
[PRODUCT](docs/PRODUCT.md) → [RUNTIME](docs/RUNTIME.md) → [ARCHITECTURE](docs/ARCHITECTURE.md) →
[DATA](docs/DATA.md) → [AUTH](docs/AUTH.md) → [ENGINEERING](docs/ENGINEERING.md) →
[TESTING](docs/TESTING.md) → [DESIGN](docs/DESIGN.md).

→ **[docs/README.md](docs/README.md)** — the Obsidian vault. Open `docs/` as a vault in
Obsidian; `.obsidian/` is committed (graph colour groups by tag, backlinks, bookmarks).
MOC entry: [docs/Home.md](docs/Home.md).

→ **[docs/dev-notes.md](docs/dev-notes.md)** — the author's running log. The richest "why" source
in the repo. Read it before arguing with a design choice.

## Don't

- Don't remove `-ffp-contract=off` from `pipeline/native/CMakeLists.txt` or add `-ffast-math` —
  it breaks fastgeo boundary-point parity on arm64.
- Don't `import fastgeo` directly in pipeline code — go through `pipeline/geo_backend.py`.
- Don't interpolate a user value into SQL. Bound `?` parameters only.
- Don't label synthetic data (`data/raw/`, `data/db.sqlite`) as INEGI/CONAPO-sourced.
- Don't read `.env` / `.env.local` with agent tools — though there are none in this repo, and
  no secrets.
- Don't add a dependency for something small. No UI framework, no chart library, no parser
  library, no ORM.

## Do

- Keep the four CI jobs green (`web-test`, `cli-test`, `pipeline-test`, `native-build`).
- Regenerate **and re-commit** `data/db.sqlite` + `web/public/listings.json` when the pipeline
  changes — they're committed artifacts.
- Run the fastgeo parity suite both ways (compiled, and `FASTGEO_FORCE_FALLBACK=1`).
- Use installed skills — see `.agents/skills/` and the inventory in
  [`skills-lock.json`](skills-lock.json).

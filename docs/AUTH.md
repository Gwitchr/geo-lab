---
aliases: [Auth, AUTH, Trust Boundaries]
tags: [moc]
---

# Auth

**geo-lab has no authentication and no authorization.** There are no accounts, no sessions,
no roles, no tokens, no secrets, and no `.env` file. This page exists to say that
explicitly, and to name the trust boundaries that *do* exist so nobody mistakes "no auth"
for "no security surface."

---

## Why there is nothing to authenticate

| Piece | Deployment | Access model |
|---|---|---|
| `web/` | Static files on GitHub Pages | Fully public, read-only. No server, no API, no session. |
| `cli/` | Runs on the author's machine | Whoever has a shell already has the sqlite file. |
| `pipeline/` | Runs on the author's machine | Same. |
| `data/db.sqlite` | Committed to a public repo | Synthetic listings + public open data. Nothing personal, nothing to protect. |

Adding a role gate would be gating public data from itself. If a real backend ever appears
(a hosted API over the listings, a per-user saved-search feature), that's the moment this
page stops being a stub — and the moment [[security]]'s assumptions need rewriting.

## The trust boundaries that do exist

Even with no auth, three places take untrusted input:

### 1. Filter expressions → SQL (`cli/`)

`geoq`'s filter language compiles to a SQL `WHERE` fragment. **Values never reach the SQL
string.** They ride along as bound `?` parameters via `better-sqlite3`, and `:` (contains)
terms have `%`, `_`, and `\` escaped so a literal wildcard can't be smuggled in. A malformed
or adversarial expression produces a `LexError` / `ParseError` / `EvalError` with a character
position, exit code 1 — never a query.

This is structural, not incidental. Keep it that way: **never string-interpolate a user value
into SQL.** See [[query-engine]] and [[filter-language]].

### 2. Listing text → DOM (`web/`)

Every user-visible string goes through `escapeHtml()` in `web/src/main.ts` before it is
assigned into `innerHTML`. The listings JSON is generated data today, but the escaping is
what makes that safe to assume. Don't bypass it.

### 3. Database handle (`cli/`)

`cli/src/db.ts` opens sqlite with `readonly: true, fileMustExist: true`. `geoq` structurally
cannot write to, create, or corrupt the database — the pipeline is the only writer
([[ARCHITECTURE]]).

## Deploy permissions

`.github/workflows/pages.yml` requests exactly `contents: read`, `pages: write`,
`id-token: write`. Nothing else in CI has write access to the repo.

## Rules

- **No secrets in this repo, ever.** There is no `.env` and none is expected. Never read
  `.env` / `.env.local` with agent tools.
- **No machine-local absolute paths** in committed files.
- If auth ever becomes real, it gets an ADR before it gets code.

---

## See also

- ↑ [[RUNTIME]] · [[ARCHITECTURE]]
- [[security]] · [[query-engine]] · [[web-app]] · [[contracts]]
- [[DATA]] · [[ENGINEERING]]
- ↩ [[Home]]

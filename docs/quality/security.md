---
aliases: [Security]
tags: [quality]
---

# Security

geo-lab has an unusually small attack surface: a **static site** (no server,
no backend, no API) plus a **local CLI** reading a **local SQLite file**.
There is no login, no session, no user data, no network write path. See
[[AUTH]] for why there is no authentication surface at all — that is a
property of the architecture, not an omission to fix.

The trust boundaries that *do* exist are listed below. Each one is currently
closed; the point of this page is to keep them closed.

## 1. SQL injection is structurally prevented — keep it that way

`geoq`'s filter language is user input that ends up in SQL. It cannot inject,
because `cli/src/parser/eval.ts` compiles the AST into a WHERE fragment that
contains **only positional `?` placeholders**, with the values carried
separately in `params` and bound by `better-sqlite3`:

```ts
return { sql: `${column} ${compareOpSql(node.op)} ?`, params: [num] };
```

No user-supplied value is ever concatenated into SQL text. Reinforcing that:

- **Identifiers come from allowlists, never from input.** Column names are
  resolved through `FIELD_COLUMNS` (`eval.ts`) and `resolveColumns()`
  (`cli/src/types.ts`), both of which reject anything not in a fixed list.
  `stats --by` validates against `isField()` before the column name is
  interpolated.
- **`LIMIT` is a coerced number**, not raw text — `optionNumber()` in
  `cli/src/args.ts` runs `Number(raw)` and throws on `NaN`, so a string can
  never reach the `LIMIT ${limit}` slot.
- **`:` (contains) escapes LIKE metacharacters.** `escapeLike()` escapes
  `\`, `%`, and `_` and the query uses `LIKE ? ESCAPE '\'`, so a user
  searching for a literal `%` gets a literal `%` and cannot turn a term into
  a wildcard.

**Invariant:** any new operator or field must go through `compileFilter()`
and produce bound params. Never build a WHERE clause with template
interpolation of a value, however "safe" it looks. See [[query-engine]] and
[[filter-language]].

## 2. The database is opened read-only

`cli/src/db.ts` opens with `{ fileMustExist: true, readonly: true }`. `geoq`
cannot write, migrate, or create `data/db.sqlite` — a malformed query is at
worst an error, never a mutation. Only the [[pipeline]] writes the db. Keep
the `readonly` flag; if a future subcommand needs to write, it should open a
second, explicitly-writable handle rather than relaxing this one.

## 3. The web app escapes everything before `innerHTML`

`web/src/main.ts` builds table rows with a template literal assigned to
`tr.innerHTML`, and every string field goes through `escapeHtml()` first
(title, type, colonia, municipio, listed_date); the numeric fields are
formatted through `Intl.NumberFormat`. `escapeHtml()` is the
set-`textContent`-then-read-`innerHTML` trick, which is correct for text
nodes.

`map.ts`'s `popupHtml()` reaches the same guarantee differently: it builds
real DOM nodes, sets `textContent`, and serializes with `outerHTML`. Charts
set `textContent` on SVG `<text>`/`<title>` nodes. All three paths are safe.

**Invariant:** never interpolate a listing field into `innerHTML` without
`escapeHtml()`. The data is synthetic today, but the pipeline's whole premise
is that it will one day ingest text it did not author.

## 4. No secrets, no `.env`

There are no secrets in this repo, and **there are no `.env` files at all** —
`find` for `.env*` returns nothing. Nothing in `web/`, `cli/`, or `pipeline/`
reads an API key, token, or credential; the only network calls are Leaflet
fetching OpenStreetMap tiles and the app fetching its own `listings.json`.

**Rule for agents and tooling: never read `.env` / `.env.local` with agent
tools.** If such a file ever appears here, it is out of scope by default and
must not be opened, echoed, or committed. `.gitignore` covers build output
and venvs; `data/db.sqlite` is committed *on purpose* (it is synthetic, see
below), and that is the only deliberate exception.

## 5. Committed data carries no personal information

Everything in `data/raw/` and `data/db.sqlite` is **synthetic** listings from
`data/gen/gen_listings.py`. The only real data is public open data: INEGI AGEB
polygons and CONAPO marginación rows. No row corresponds to a real property,
a real person, or a real seller — there is nothing personal to leak. See
[[DATA]] and [[data-notes]]. (The related integrity rule — never *label*
synthetic data as INEGI/CONAPO-sourced — lives in [[data-integrity]].)

## 6. CI permissions

`.github/workflows/pages.yml` declares exactly:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

`contents: read` (checkout), `pages: write` + `id-token: write` (what
`actions/deploy-pages` needs for its OIDC-based deploy). No `contents: write`,
no `packages:`, no PAT anywhere — the deploy uses the ephemeral GitHub-issued
token. `ci.yml` declares no `permissions` block and so inherits the repo
default; it only runs tests and builds and needs nothing beyond read.
Tightening it to `contents: read` explicitly would be a cheap improvement.

---

## See also

- ↑ [[AUTH]] · [[RUNTIME]] · [[ENGINEERING]]
- [[performance]] · [[accessibility]] · [[data-integrity]]
- [[query-engine]] · [[filter-language]] · [[web-app]] · [[data-notes]]
- ↩ [[Home]]

---
aliases: [TypeScript Style]
tags: [convention]
---

# TypeScript Style

Two TypeScript packages: `cli/` (the `geoq` query tool, Node + better-sqlite3)
and `web/` (the Vite explorer). They share a compiler version and almost
nothing else — different module systems, different tsconfigs, different lint
posture. Know which one you're in.

## The version pin (read this before `npm update`)

TypeScript is pinned to **`^6.0.3` in both `web/package.json` and
`cli/package.json`**. This is not cosmetic:

- `typescript-eslint` (web's only lint dependency) has a peer range that
  **excludes TS 7**. Bumping web to 7.x breaks `npm run lint`, which is a CI
  step in the `web-test` job.
- `cli/` was on `^7.0.2` and was deliberately aligned **down** to `^6.0.3`
  (commit `b51a00c`) so the repo isn't running two compilers for no reason.

Rule: **never bump one package's TypeScript without the other.** If you bump,
bump both, re-run `npm run lint` in `web/`, and check both `tsc` projects in
`cli/`. The history is in [[dev-notes]].

## `cli/` — Node, NodeNext, strict+

`cli/tsconfig.json`: `target: ES2022`, `module`/`moduleResolution: NodeNext`,
`strict: true`, **`noUncheckedIndexedAccess: true`**, `rootDir: src`,
`outDir: dist`, sourcemaps on, declarations off. `"type": "module"`.

NodeNext means **relative imports carry a `.js` extension**, even though the
source is `.ts`:

```ts
// cli/src/cli.ts
import { openDb, DEFAULT_DB_PATH } from "./db.js";
import { tokenize, type Token } from "./parser/lexer.js";
import fs from "node:fs";           // node builtins use the node: prefix
```

`noUncheckedIndexedAccess` means `arr[i]` is `T | undefined`. Don't reach for
`!`; narrow it. Two tsconfigs, and CI type-checks **both**:

- `tsconfig.json` — `src` only, excludes `src/__tests__`; this is what
  `npm run build` emits from.
- `tsconfig.test.json` — extends it with `noEmit`, `rootDir: "."`, and pulls
  in tests + `vitest.config.ts`.

```sh
cd cli
npx tsc -p tsconfig.json --noEmit
npx tsc -p tsconfig.test.json --noEmit   # both are CI steps
```

## `web/` — bundler resolution, noEmit

`web/tsconfig.json`: `strict: true`, plus **`noUnusedLocals`,
`noUnusedParameters`, `noFallthroughCasesInSwitch`**;
`moduleResolution: "bundler"` with `allowImportingTsExtensions` and
`isolatedModules`; `noEmit: true` — **vite does the building**, `tsc` is only a
type gate (`npm run build` = `tsc --noEmit && vite build`). Asset URLs go
through `import.meta.env.BASE_URL`, never a hardcoded `/…` path (Pages serves
from `/geo-lab/`; see [[web-app]]).

## Lint

**ESLint exists only in `web/`** (`npm run lint` → `eslint .`, flat config in
`web/eslint.config.js`: `typescript-eslint` recommended + `projectService`,
unused args ignored when `^_`-prefixed). It is a CI step.

**`cli/` has no lint script on purpose** — `test` and `build` (plus the two
`tsc` passes) cover it. Don't "fix" this by adding one; the deliberate
omission is recorded in [[dev-notes]].

## Dependencies: the standing bias

> Don't add a dependency for something this small.

That bias is why, concretely:

- **No UI framework.** `web/src/main.ts` builds the table/tabs/panels with
  plain DOM calls.
- **No chart library.** `web/src/charts.ts` emits hand-written SVG.
- **No parser library.** `cli/src/parser/` is a hand-written
  lexer → recursive-descent parser → SQL eval (see [[filter-language]]).
- **No marker-clustering plugin** in `web/src/map.ts` — markers are capped and
  evenly sampled instead.

Current runtime deps, in full: `better-sqlite3` (cli), `leaflet` (web). Adding
a third is a decision, not a reflex — justify it in [[dev-notes]].

## SQL from TypeScript

`cli/src/parser/eval.ts` compiles the AST to a WHERE clause with **positional
`?` parameters only**. User text is never interpolated into SQL; `:` search
terms are escaped for `%`, `_`, and `\`. This is a hard rule, not a style
preference — see [[query-engine]].

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- [[python-style]] · [[cpp-native]] · [[styling-system]] · [[git-and-pr]]
- ↩ [[Home]]

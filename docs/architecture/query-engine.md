---
aliases: [Query Engine]
tags: [architecture]
---

# Query Engine

`geoq`'s filter language, compiled to SQL. Four stages, all hand-written, no parser library — the
language is small enough that a dependency wasn't worth it.

```
source string
  -> tokenize()   cli/src/parser/lexer.ts    -> Token[]
  -> parse()      cli/src/parser/parser.ts   -> ExprNode (AST, cli/src/parser/ast.ts)
  -> compile()    cli/src/parser/eval.ts     -> { sql: string, params: unknown[] }
  -> db.prepare(sql).all(...params)          via better-sqlite3, readonly
```

**The full grammar reference — fields, operators, values, quoting rules, error examples — lives in
[[filter-language]]. This page is the implementation shape, not the language spec.** Don't restate
the grammar here; if the two ever disagree, `docs/filter-language.md` plus the code win.

## Lexer — `cli/src/parser/lexer.ts`

A single `while (i < len)` character scan producing a flat `Token[]` terminated by exactly one `EOF`
token. Token types: `NUMBER | STRING | WORD | AND | OR | LPAREN | RPAREN | OP | EOF`. Every token
carries a 0-based `position` (character offset) — that offset is what every error message reports.

Ordering inside the scan matters:

1. whitespace skipped;
2. `(` / `)`;
3. quoted strings (`"` or `'`), with `\"`, `\'`, `\\` as the only legal escapes — any other
   backslash sequence is a `LexError`; unterminated is a `LexError` at the *opening* quote;
4. numbers — optional leading `-` (only when a digit follows), digits, optional `.` + digits;
   `numericValue` is attached here;
5. operators — **two-char (`<=`, `>=`) tried before one-char** (`<`, `>`, `=`, `:`);
6. identifiers — `IDENT_START = /[\p{L}_]/u`, `IDENT_PART = /[\p{L}\p{N}_]/u`, so accented bare words
   like `cuauhtémoc` need no quotes. `and`/`or` (any casing) are lexed as keyword tokens `AND`/`OR`,
   not `WORD`;
7. anything else → `LexError`.

The number rule is why `listed>2024-01-01` fails: `2024`, `-01`, `-01` lex as three tokens. Dates
must be quoted.

## Parser — `cli/src/parser/parser.ts`

Recursive descent, one class with `pos`/`peek()`/`advance()`/`expect()`. Precedence is expressed
directly in the call chain — **`and` binds tighter than `or`**:

```
parseExpr()  := parseOr()
parseOr()    := parseAnd() ("or"  parseAnd())*      // loop, left-associative
parseAnd()   := parseClause() ("and" parseClause())*  // loop, left-associative
parseClause():= "(" parseExpr() ")" | parseComparison()
```

So `price<2500000 and colonia:roma or type=terreno` parses as
`(price<2500000 and colonia:roma) or type=terreno`. Parentheses override; `parseClause` recurses
back into `parseExpr` for a group.

`parseComparison` expects `WORD` (field) → `OP` → value. Field names are lowercased and checked
against `FIELDS` (`ast.ts:17`), so field names are case-insensitive; unknown fields raise a
`ParseError` listing the valid set. A value token may be `NUMBER`, `STRING` (`quoted: true`) or
`WORD` (`quoted: false`); an `AND`/`OR` token in value position gets a specific hint — *"'and' is a
reserved keyword here; quote it to use as a value"*.

`parse()` calls `parser.finish()`, which `expect`s `EOF` — trailing garbage is rejected rather than
silently ignored.

The AST (`cli/src/parser/ast.ts`) is two node kinds:

```ts
type ExprNode = ComparisonNode | LogicalNode;
// ComparisonNode: { kind, field, op, value: NumberValue | StringValue, position }
// LogicalNode:    { kind, op: "and" | "or", left, right, position }
```

Grouping is carried by tree shape only — there is no paren node.

## SQL compiler — `cli/src/parser/eval.ts`

`compile(ast) -> { sql, params }`. **User text never touches the SQL string.** Values always ride
along as positional `?` parameters bound through `better-sqlite3`, so no filter input — however
adversarial — can inject SQL.

- `FIELD_COLUMNS` (`eval.ts:6`) is the field-name → column map: `price → price_mxn`, `m2 → m2`,
  `bedrooms → bedrooms`, `type`/`colonia`/`municipio` → same name, `listed → listed_date`. **This map
  must stay in sync with `pipeline/ingest.py`'s schema.**
- `NUMERIC_FIELDS = {price, m2, bedrooms}`. A non-numeric value for one of these is an `EvalError`.
- `:` on a numeric field is a semantic error, not a coercion:
  `Operator ':' (contains) is not valid for numeric field 'price'; use <, <=, >, >=, or =`.
- `:` on a string field compiles to `LOWER(col) LIKE ? ESCAPE '\'` with the pattern
  `%<lowercased, escaped value>%`. `escapeLike` (`eval.ts:26`) escapes `\`, `%`, `_` **in that
  order**, so literal wildcards in user input can't act as wildcards.
- `<, <=, >, >=, =` compile to `col <op> ?`. `=` on strings is exact and **case-sensitive** (only
  `:` is case-insensitive).
- Parenthesization is minimal by construction: `evalFragment` emits a node's SQL unwrapped, and
  `evalChild` adds parens only around a *logical* child (`eval.ts:103`). Same-operator chains render
  flat; real grouping is preserved.

The three commands all call `compileFilter(filter)` and splice the fragment in as
` WHERE ${compiled.sql}` (`commands/query.ts:29`, `commands/stats.ts:60`, `commands/export.ts:53`).
An omitted or all-whitespace filter means "no filter" — no `WHERE` clause at all.

Note: `LIMIT` and `GROUP BY <column>` are interpolated as text, but only from already-validated
values (a `Number` from `--limit`, and a column name looked up through `FIELD_COLUMNS`) — never from
raw user strings.

## Errors — `cli/src/parser/errors.ts`

One base class, three subclasses, each carrying `position`:

| class | stage | raised for |
|---|---|---|
| `LexError` | tokenize | bad character, unterminated string, invalid escape |
| `ParseError` | parse | unknown field, missing operator/value, unbalanced `)`, trailing tokens |
| `EvalError` | compile | `:` on a numeric field; non-numeric value for a numeric field |

All three extend `FilterError`. `cli/src/cli.ts:59`'s `formatError` catches `FilterError` specially
and prints `Error: <message> (position <n>)`; `runCli` returns exit code **1**. The subclass split
exists so tests can assert *which stage* rejected an expression, not just that it failed.

## Commands and the DB

`geoq query | stats | export` (`cli/src/cli.ts:90`). `query` defaults to `LIMIT 20`
(`DEFAULT_QUERY_LIMIT`, `0` = no limit); `stats --by` defaults to the top 15 groups
(`DEFAULT_GROUP_LIMIT`); `export` writes to stdout unless `--out` is given, inferring json/csv from
the extension. All three `ORDER BY listed_date DESC`.

`openDb` (`cli/src/db.ts:15`) opens the file `readonly: true, fileMustExist: true` and resolves
`--db` against **`process.cwd()`** — there is no repo-root auto-detection. Run `geoq` from the repo
root or pass `--db` explicitly; see [[contracts]].

**`geoq` reads `listings` unfiltered** — unlike `stats.py`/`export_web.py`, it does *not* exclude
`dup_of IS NOT NULL`, so the 2,492 flagged near-duplicates appear in its results and counts. This is
a known, deliberate scope boundary.

Tests: `cli/src/__tests__/` — lexer (14), parser (18), eval (12), golden (13), commands (19), cli
(13) = **89 tests**. The golden suite pins expression → SQL + params pairs; changing the compiler's
output shape will (correctly) break it.

---

## See also

- ↑ [[ARCHITECTURE]]
- [[overview]] · [[pipeline]] · [[fastgeo]] · [[web-app]] · [[contracts]]
- Grammar reference: [[filter-language]] · Decisions: [[dev-notes]] · [[TESTING]]
- ↩ [[overview]]

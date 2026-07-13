---
aliases: [Add a filter field]
tags: [workflow]
---

# Add a field to geoq's filter language

A filter field (`price`, `m2`, `bedrooms`, `type`, `colonia`, `municipio`,
`listed`) touches the db schema, the parser, the CLI surface, the fixtures, and
the docs. Work through them in this order — the compiler catches most of the CLI
side, but not the schema or the docs. Grammar reference: [[filter-language]].
Worked example: adding `estado` (a text field, column `estado`, already in the
table).

## 1. The column must exist in `listings`

If the column is new, add it to `SCHEMA` (and `INSERT_SQL`, and an index if you
will filter on it a lot) in `pipeline/ingest.py`, and make sure something
populates it: `pipeline/clean.py` for a raw-CSV-derived field,
`pipeline/enrich.py` for a derived/joined one (that is where `ageb_id`,
`marginacion_grade`, `marginacion_index` get filled). Then rebuild the db —
see [[regenerate-data]].

If the column already exists (like `estado`), skip to step 2.

## 2. `cli/src/parser/ast.ts` — the field enum

```ts
export const FIELDS = [
  "price", "m2", "bedrooms", "type", "colonia", "municipio", "listed",
] as const;
```

Add the name here first. `parser.ts` validates against `isField()` and prints
`Unknown field '<x>', expected one of: ${FIELDS.join(", ")}` — until the name is
in this list, the lexer/parser will refuse it. Everything downstream is typed
off `Field`, so TypeScript now tells you what else is missing.

## 3. `cli/src/parser/eval.ts` — `FIELD_COLUMNS` (and `NUMERIC_FIELDS`)

```ts
export const FIELD_COLUMNS: Record<Field, string> = {
  price: "price_mxn",
  ...
  listed: "listed_date",
};
```

`Record<Field, string>` is exhaustive, so this fails to compile until you map
the new field to its real column name. If the field is numeric, also add it to
`NUMERIC_FIELDS` in the same file.

**The numeric-vs-text rule.** `NUMERIC_FIELDS` decides the semantics:

- numeric field: the value must parse as a number (bare digits, or a quoted
  string of digits/`.`/`-`); a non-numeric value is an `EvalError`
  (`Field 'price' expects a numeric value for '<'`).
- numeric field + `:` (contains): **always** an `EvalError` —
  `Operator ':' (contains) is not valid for numeric field 'price'; use <, <=, >, >=, or =`.
  This is a semantic error raised while compiling to SQL, not a parse error.
- text field: `=` is exact and case-sensitive; `:` compiles to
  `LOWER(col) LIKE ? ESCAPE '\'` with `%`/`_`/`\` escaped in the value.

Getting this wrong is the classic bug: a numeric field left out of
`NUMERIC_FIELDS` silently accepts `price:2500000` and compiles a `LIKE` against
an INTEGER column.

## 4. `cli/src/types.ts` — `ListingRow` and `ALL_COLUMNS`

Add the **column** (not the filter-language name) to the `ListingRow` interface
and to `ALL_COLUMNS`, in schema order. `ALL_COLUMNS` drives `--columns`
validation, the default `SELECT` list, and CSV export headers.

## 5. `cli/src/cli.ts` — the USAGE text

Two lines mention the field list verbatim and neither is type-checked:

```
  --by <field>      Group stats by a filter-language field (price|m2|bedrooms|type|colonia|municipio|listed)
...
  field   := price | m2 | bedrooms | type | colonia | municipio | listed
```

Update both. (`geoq stats --by <field>` accepts any filter-language field via
`isField()`, so the new field works there for free — the help text is the only
thing that goes stale.)

## 6. `cli/src/__tests__/fixtures/fixtureDb.ts`

The fixture db is an independent hand-written mirror of the real schema. If the
column is new, add it to the `CREATE TABLE listings` block **and** the
`INSERT INTO listings` statement, and give all eight `FIXTURE_ROWS` a value.
`ListingRow` typing will point you at the rows.

## 7. `docs/filter-language.md`

Add a row to the **Fields** table (`field | column | kind`) and, if the field is
text, add it to the `:` operator's "valid fields" cell in the **Operators**
table. Add an example row to the Examples table if it earns one. This doc is the
grammar's contract; a field that only exists in code is invisible.

## 8. Tests

```sh
cd cli
npm test
```

Four suites care:

- `src/__tests__/lexer.test.ts` — the name tokenizes as a field (case-insensitive).
- `src/__tests__/parser.test.ts` — it parses into a comparison node; an unknown
  neighbor still errors.
- `src/__tests__/eval.test.ts` — the numeric/text behavior above, especially the
  `:`-on-numeric `EvalError`.
- `src/__tests__/golden.test.ts` — pinned `expr -> exact SQL + params` cases. Add
  one; this suite is what catches an accidental change to SQL shape or
  precedence.

Then the full CLI gate (what CI's `cli-test` job runs), and a real-data check:

```sh
npx tsc -p tsconfig.json --noEmit
npx tsc -p tsconfig.test.json --noEmit
npm test          # 89 tests before your additions
npm run build
node dist/index.js query "estado:jalisco and price<2500000" --db ../data/db.sqlite
```

The web explorer has its own, deliberately simpler filter (`web/src/data.ts`,
AND-only, no parentheses) — it does **not** share this grammar, so adding a
field here does not add it there. See [[web-app]].

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- [[query-engine]] · [[filter-language]] · [[contracts]] · [[dev-notes]]
- [[regenerate-data]] · [[add-a-region]] · [[build-fastgeo]] · [[diagnose-parity-failure]]
- ↩ [[Home]]

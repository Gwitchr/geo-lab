---
aliases: [Filter Language, geoq grammar]
tags: [architecture]
---

# geoq filter language

`geoq query`, `geoq stats`, and `geoq export` all take an optional filter
expression as their first positional argument. It compiles to a SQL `WHERE`
fragment with bound parameters (never string-interpolated values) and runs
against the `listings` table.

```
geoq query "price<2500000 and colonia:roma or type=terreno"
```

The lexer, parser, and SQL compiler are hand-written (no parser library) in
`cli/src/parser/lexer.ts`, `cli/src/parser/parser.ts`, and
`cli/src/parser/eval.ts`.

## Grammar

```
expr    := clause (("and" | "or") clause)*
clause  := field op value | "(" expr ")"
field   := price | m2 | bedrooms | type | colonia | municipio | listed
op      := "<" | "<=" | ">" | ">=" | "=" | ":"
value   := number | quoted string | bare word
```

Precedence, spelled out as the actual parse:

```
expr    := orExpr
orExpr  := andExpr ("or" andExpr)*
andExpr := clause ("and" clause)*
clause  := field op value | "(" expr ")"
```

`and` binds tighter than `or`. Parentheses override precedence. Chains of the
same operator (`a and b and c`, `a or b or c`) are left-associative, though
`and`/`or` are logically associative so evaluation order does not change the
result.

- `price<2500000 and colonia:roma or type=terreno` parses as
  `(price<2500000 and colonia:roma) or type=terreno`.
- `price<2500000 and (colonia:roma or type=terreno)` uses parentheses to force
  the other grouping, and can select a different set of rows.

Field names and the `and` / `or` keywords are matched case-insensitively
(`PRICE`, `Price`, `price` are equivalent; so are `AND`/`and`/`And`).

## Fields

| field       | column        | kind    |
|-------------|---------------|---------|
| `price`     | `price_mxn`   | number  |
| `m2`        | `m2`          | number  |
| `bedrooms`  | `bedrooms`    | number  |
| `type`      | `type`        | string (`casa`, `departamento`, `terreno`, `local`) |
| `colonia`   | `colonia`     | string  |
| `municipio` | `municipio`   | string  |
| `listed`    | `listed_date` | string (ISO date, `YYYY-MM-DD`) |

## Operators

| op   | meaning                          | valid fields                    |
|------|-----------------------------------|----------------------------------|
| `<`  | less than                         | any                               |
| `<=` | less than or equal                | any                               |
| `>`  | greater than                       | any                               |
| `>=` | greater than or equal              | any                               |
| `=`  | equals (case-sensitive for strings)| any                               |
| `:`  | contains, case-insensitive         | `type`, `colonia`, `municipio`, `listed` (not numeric fields) |

`price`, `m2`, and `bedrooms` are numeric: their value must parse as a number
(bare digits, or a quoted string containing only digits/`.`/`-`). Using `:`
(contains) on a numeric field is a compile-time error, e.g.:

```
$ geoq query "price:2500000"
Error: Operator ':' (contains) is not valid for numeric field 'price'; use <, <=, >, >=, or = (position 0)
```

`type`, `colonia`, `municipio`, and `listed` are compared as text. `=` is an
exact, case-sensitive match; `:` is a case-insensitive substring match
(SQL `LIKE '%value%'`, with `%`, `_`, and `\` in the value escaped so they are
matched literally, not as wildcards).

## Values

- **number**: optional leading `-`, digits, optional `.` and fractional
  digits. Example: `price<2500000`, `lat>-99.5`.
- **quoted string**: `"..."` or `'...'`. Supports `\"`, `\'`, and `\\` as
  escapes; any other backslash sequence is a lexer error. Use quotes whenever
  a value contains whitespace, punctuation, or would otherwise be ambiguous.
  Example: `colonia:"Santa Fe"`.
- **bare word**: an unquoted run of Unicode letters/digits/underscore,
  starting with a letter or underscore. No spaces or hyphens. Accented
  letters are valid bare-word characters, so `colonia:cuauhtémoc` does not
  need quotes. Example: `type=terreno`.

### `listed` (dates) must be quoted

A bare date like `2024-01-15` does **not** lex as a single bare word (bare
words must start with a letter, and the `-` separators would otherwise be
read as unary minus on the following number group). Write date values as a
quoted string:

```
geoq query 'listed>="2024-01-01" and listed<"2024-06-01"'
```

An unquoted attempt fails fast with a parse error rather than silently doing
the wrong thing:

```
$ geoq query "listed>2024-01-01"
Error: Unexpected number '-01' after expression, expected 'and', 'or', ')', or end of input (position 11)
```

### Reserved words

`and` and `or` (any casing) are keywords, not values. A bare-word value that
is literally `and` or `or` must be quoted:

```
$ geoq query "colonia:and"
Error: Expected a value (number, quoted string, or word) after 'colonia:', got 'and' ('and' is a reserved keyword here; quote it to use as a value) (position 8)

$ geoq query 'colonia:"and"'
```

## Examples

| expression | meaning |
|---|---|
| `price<2500000` | price under 2.5M MXN |
| `m2>=80 and bedrooms>=3` | at least 80 m² and 3+ bedrooms |
| `type=departamento` | exact type match |
| `colonia:roma` | colonia name contains "roma" (case-insensitive) |
| `colonia:cuauhtémoc` | accented bare word, no quotes needed |
| `colonia:"Santa Fe"` | quoted value with a space |
| `price<2500000 and colonia:roma or type=terreno` | `and` before `or`: `(price<2500000 and colonia:roma) or type=terreno` |
| `price<2500000 and (colonia:roma or type=terreno)` | parentheses force the other grouping |
| `listed>="2024-01-01" and listed<"2024-06-01"` | listed in the first half of 2024 |

## Errors

Every stage raises a distinct error type carrying the source character
position (`LexError`, `ParseError` from `cli/src/parser/errors.ts` for
tokenizing/grammar problems; `EvalError` for field/value type mismatches
caught while compiling to SQL, e.g. `price` given a non-numeric value). The
CLI catches all three and prints `Error: <message> (position <n>)` with exit
code 1; nothing is ever string-interpolated into the SQL text itself, so
malformed or adversarial filter input cannot inject SQL — values always ride
along as bound `?` parameters.

---

## See also

- ↑ [[ARCHITECTURE]] · [[PRODUCT]]
- [[query-engine]] — how the lexer/parser/eval are actually built
- [[add-a-filter-field]] · [[security]] · [[TESTING]]
- ↩ [[Home]]

---
aliases: [0001 Hand-written filter parser]
tags: [adr]
---

# 0001, Hand-write the filter language's lexer, parser, and eval

## Status

accepted

## Context

`geoq` needs a filter language — `price<2500000 and colonia:roma or type=terreno`
— over seven fields (`price`, `m2`, `bedrooms`, `type`, `colonia`, `municipio`,
`listed`), six operators (`< <= > >= = :`), `and`/`or` with `and` binding
tighter, and parentheses to override. That is a small grammar: three
precedence levels, no statements, no declarations, no recursion beyond
parenthesized groups.

The obvious alternative is a parser generator or combinator library (nearley,
chevrotain, peggy). For a grammar this size that buys a `.grammar` file and a
build step, and it hands control of the error messages to the library.

Error messages are the whole point. This is a CLI a person types into and gets
wrong constantly — quoting a date, misspelling a field, using `:` on a number.
Every failure has to say what went wrong and where.

## Decision

Hand-write the three stages, no parser dependency:
`cli/src/parser/lexer.ts` (source → tokens), `cli/src/parser/parser.ts`
(recursive descent → AST), `cli/src/parser/eval.ts` (AST → SQL `WHERE` fragment
with bound `?` params).

Each stage raises its own error subclass — `LexError`, `ParseError`, `EvalError`,
all extending `FilterError` in `cli/src/parser/errors.ts`, all carrying a
`position` (0-based character offset into the source expression). So the stage
that failed and the exact character it failed at are both recoverable by the
caller and by the tests.

## Consequences

Easier: error text is ours to write, and it is specific — an unknown field
lists the valid ones, `and` in value position says it is a reserved keyword and
suggests quoting it, `:` on `price` is a semantic `EvalError` naming the
operators that would work. Zero parser dependencies in `cli/`. The AST is a
plain tagged union, so `eval.ts` compiles it straight to parameterized SQL with
nothing interpolated into the string.

Harder: the grammar is maintained by hand. There is no generator to re-derive
precedence from — adding an operator means touching the lexer, the parser, the
AST types, and `eval.ts`'s `FIELD_COLUMNS`. The three stages are covered by 44
of `cli/`'s 89 tests (lexer 14, parser 18, eval 12) precisely because nothing
else is checking the grammar for us.

---

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
- [[query-engine]] · [[filter-language]] · [[TESTING]] · [[dev-notes]]
- ↩ [[Home]]

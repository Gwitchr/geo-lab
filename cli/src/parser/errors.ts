/**
 * Error hierarchy for the filter language. Each stage of the pipeline
 * (lexer -> parser -> eval) throws its own subclass so callers/tests can
 * tell where a bad expression failed, but all of them carry a
 * human-readable `message` suitable for printing straight to the CLI user.
 */

export class FilterError extends Error {
  /** Character offset into the source expression where the problem starts. */
  readonly position: number;

  constructor(message: string, position: number) {
    super(message);
    this.name = new.target.name;
    this.position = position;
  }
}

/** Raised while turning raw source text into tokens. */
export class LexError extends FilterError {}

/** Raised while turning tokens into an AST (syntax errors). */
export class ParseError extends FilterError {}

/** Raised while turning an AST into SQL (semantic errors, e.g. type mismatches). */
export class EvalError extends FilterError {}

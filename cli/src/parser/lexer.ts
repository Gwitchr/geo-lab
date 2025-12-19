import { LexError } from "./errors.js";

export type TokenType =
  | "NUMBER"
  | "STRING"
  | "WORD"
  | "AND"
  | "OR"
  | "LPAREN"
  | "RPAREN"
  | "OP"
  | "EOF";

export interface Token {
  readonly type: TokenType;
  /**
   * NUMBER: the parsed numeric value (as text, see `numericValue`).
   * STRING: the unescaped string contents.
   * WORD/AND/OR: the raw source text (original casing preserved).
   * OP: one of "<" "<=" ">" ">=" "=" ":".
   * LPAREN/RPAREN/EOF: empty string.
   */
  readonly value: string;
  /** Parsed numeric value, only set when type === "NUMBER". */
  readonly numericValue?: number;
  /** True when a STRING token was written with quotes in the source (always true for STRING). */
  readonly quoted?: boolean;
  /** Character offset (0-based) where this token starts in the source. */
  readonly position: number;
}

const IDENT_START = /[\p{L}_]/u;
const IDENT_PART = /[\p{L}\p{N}_]/u;
const DIGIT = /[0-9]/;

function isOperatorChar(ch: string): boolean {
  return ch === "<" || ch === ">" || ch === "=" || ch === ":";
}

/**
 * Turn a filter expression into a flat list of tokens, terminated by a
 * single EOF token. Throws LexError on unexpected characters or
 * unterminated string literals.
 */
export function tokenize(source: string): Token[] {
  const tokens: Token[] = [];
  const len = source.length;
  let i = 0;

  while (i < len) {
    const ch = source[i] as string;

    // Whitespace
    if (ch === " " || ch === "\t" || ch === "\n" || ch === "\r") {
      i++;
      continue;
    }

    // Parentheses
    if (ch === "(") {
      tokens.push({ type: "LPAREN", value: "(", position: i });
      i++;
      continue;
    }
    if (ch === ")") {
      tokens.push({ type: "RPAREN", value: ")", position: i });
      i++;
      continue;
    }

    // Quoted strings
    if (ch === '"' || ch === "'") {
      const start = i;
      const quote = ch;
      i++;
      let value = "";
      let closed = false;
      while (i < len) {
        const c = source[i] as string;
        if (c === quote) {
          closed = true;
          i++;
          break;
        }
        if (c === "\\") {
          const next = source[i + 1];
          if (next === quote || next === "\\") {
            value += next;
            i += 2;
            continue;
          }
          throw new LexError(
            `Invalid escape sequence '\\${next ?? ""}' in string literal starting at position ${start}`,
            i,
          );
        }
        value += c;
        i++;
      }
      if (!closed) {
        throw new LexError(
          `Unterminated string literal starting at position ${start}`,
          start,
        );
      }
      tokens.push({ type: "STRING", value, quoted: true, position: start });
      continue;
    }

    // Numbers: optional leading '-', digits, optional fractional part.
    if (DIGIT.test(ch) || (ch === "-" && DIGIT.test(source[i + 1] ?? ""))) {
      const start = i;
      if (ch === "-") i++;
      while (i < len && DIGIT.test(source[i] as string)) i++;
      if (source[i] === "." && DIGIT.test(source[i + 1] ?? "")) {
        i++;
        while (i < len && DIGIT.test(source[i] as string)) i++;
      }
      const raw = source.slice(start, i);
      tokens.push({
        type: "NUMBER",
        value: raw,
        numericValue: Number(raw),
        position: start,
      });
      continue;
    }

    // Operators: try two-char operators before one-char ones.
    if (isOperatorChar(ch)) {
      const start = i;
      const two = source.slice(i, i + 2);
      if (two === "<=" || two === ">=") {
        tokens.push({ type: "OP", value: two, position: start });
        i += 2;
        continue;
      }
      if (ch === "<" || ch === ">" || ch === "=" || ch === ":") {
        tokens.push({ type: "OP", value: ch, position: start });
        i += 1;
        continue;
      }
    }

    // Identifiers / keywords (field names, and/or, bare-word values).
    if (IDENT_START.test(ch)) {
      const start = i;
      i++;
      while (i < len && IDENT_PART.test(source[i] as string)) i++;
      const raw = source.slice(start, i);
      const lower = raw.toLowerCase();
      if (lower === "and") {
        tokens.push({ type: "AND", value: raw, position: start });
      } else if (lower === "or") {
        tokens.push({ type: "OR", value: raw, position: start });
      } else {
        tokens.push({ type: "WORD", value: raw, position: start });
      }
      continue;
    }

    throw new LexError(`Unexpected character '${ch}' at position ${i}`, i);
  }

  tokens.push({ type: "EOF", value: "", position: len });
  return tokens;
}

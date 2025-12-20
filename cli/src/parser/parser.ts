import { ParseError } from "./errors.js";
import { tokenize, type Token, type TokenType } from "./lexer.js";
import {
  FIELDS,
  isField,
  type CompareOp,
  type ExprNode,
  type Value,
} from "./ast.js";

function describeToken(t: Token): string {
  switch (t.type) {
    case "EOF":
      return "end of input";
    case "LPAREN":
      return "'('";
    case "RPAREN":
      return "')'";
    case "NUMBER":
      return `number '${t.value}'`;
    case "STRING":
      return `string "${t.value}"`;
    case "AND":
    case "OR":
    case "WORD":
    case "OP":
      return `'${t.value}'`;
  }
}

class Parser {
  private readonly tokens: readonly Token[];
  private pos = 0;

  constructor(tokens: readonly Token[]) {
    this.tokens = tokens;
  }

  private peek(): Token {
    return this.tokens[this.pos] as Token;
  }

  private advance(): Token {
    const t = this.peek();
    if (this.pos < this.tokens.length - 1) this.pos++;
    return t;
  }

  private expect(type: TokenType, message: (found: Token) => string): Token {
    const t = this.peek();
    if (t.type !== type) throw new ParseError(message(t), t.position);
    return this.advance();
  }

  /** expr := orExpr */
  parseExpr(): ExprNode {
    return this.parseOr();
  }

  /** orExpr := andExpr ("or" andExpr)* */
  private parseOr(): ExprNode {
    let left = this.parseAnd();
    while (this.peek().type === "OR") {
      const opTok = this.advance();
      const right = this.parseAnd();
      left = { kind: "logical", op: "or", left, right, position: opTok.position };
    }
    return left;
  }

  /** andExpr := clause ("and" clause)* */
  private parseAnd(): ExprNode {
    let left = this.parseClause();
    while (this.peek().type === "AND") {
      const opTok = this.advance();
      const right = this.parseClause();
      left = { kind: "logical", op: "and", left, right, position: opTok.position };
    }
    return left;
  }

  /** clause := field op value | "(" expr ")" */
  private parseClause(): ExprNode {
    if (this.peek().type === "LPAREN") {
      this.advance();
      const inner = this.parseExpr();
      this.expect(
        "RPAREN",
        (found) =>
          `Expected ')' to close the group, got ${describeToken(found)}`,
      );
      return inner;
    }
    return this.parseComparison();
  }

  private parseComparison(): ExprNode {
    const fieldTok = this.expect(
      "WORD",
      (found) =>
        `Expected a field name (${FIELDS.join(", ")}), got ${describeToken(found)}`,
    );
    const fieldName = fieldTok.value.toLowerCase();
    if (!isField(fieldName)) {
      throw new ParseError(
        `Unknown field '${fieldTok.value}', expected one of: ${FIELDS.join(", ")}`,
        fieldTok.position,
      );
    }

    const opTok = this.expect(
      "OP",
      (found) =>
        `Expected an operator (< <= > >= = :) after field '${fieldTok.value}', got ${describeToken(found)}`,
    );

    const valueTok = this.peek();
    let value: Value;
    if (valueTok.type === "NUMBER") {
      this.advance();
      value = { kind: "number", value: valueTok.numericValue as number, raw: valueTok.value };
    } else if (valueTok.type === "STRING") {
      this.advance();
      value = { kind: "string", value: valueTok.value, quoted: true };
    } else if (valueTok.type === "WORD") {
      this.advance();
      value = { kind: "string", value: valueTok.value, quoted: false };
    } else {
      const hint =
        valueTok.type === "AND" || valueTok.type === "OR"
          ? ` ('${valueTok.value}' is a reserved keyword here; quote it to use as a value)`
          : "";
      throw new ParseError(
        `Expected a value (number, quoted string, or word) after '${fieldTok.value}${opTok.value}', got ${describeToken(valueTok)}${hint}`,
        valueTok.position,
      );
    }

    return {
      kind: "comparison",
      field: fieldName,
      op: opTok.value as CompareOp,
      value,
      position: fieldTok.position,
    };
  }

  /** Ensure nothing but EOF remains after a full expression was parsed. */
  finish(): void {
    this.expect(
      "EOF",
      (found) =>
        `Unexpected ${describeToken(found)} after expression, expected 'and', 'or', ')', or end of input`,
    );
  }
}

/**
 * Parse a filter expression into an AST. Throws LexError for tokenizer
 * problems and ParseError for grammar/semantic-of-syntax problems.
 */
export function parse(source: string): ExprNode {
  const tokens = tokenize(source);
  const parser = new Parser(tokens);
  const ast = parser.parseExpr();
  parser.finish();
  return ast;
}

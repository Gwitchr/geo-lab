import { describe, expect, it } from "vitest";
import { parse } from "../parser/parser.js";
import { ParseError, LexError } from "../parser/errors.js";
import type { ComparisonNode, LogicalNode } from "../parser/ast.js";

function comparison(node: ReturnType<typeof parse>): ComparisonNode {
  expect(node.kind).toBe("comparison");
  return node as ComparisonNode;
}

function logical(node: ReturnType<typeof parse>): LogicalNode {
  expect(node.kind).toBe("logical");
  return node as LogicalNode;
}

describe("parse", () => {
  it("parses a single comparison", () => {
    const ast = comparison(parse("price<2500000"));
    expect(ast.field).toBe("price");
    expect(ast.op).toBe("<");
    expect(ast.value).toEqual({ kind: "number", value: 2500000, raw: "2500000" });
  });

  it("parses a bare-word value", () => {
    const ast = comparison(parse("type=terreno"));
    expect(ast.value).toEqual({ kind: "string", value: "terreno", quoted: false });
  });

  it("parses a quoted-string value", () => {
    const ast = comparison(parse('colonia="Santa Fe"'));
    expect(ast.value).toEqual({ kind: "string", value: "Santa Fe", quoted: true });
  });

  it("'and' binds tighter than 'or': a and b or c => (a and b) or c", () => {
    const ast = logical(parse("price<1 and m2>2 or bedrooms=3"));
    expect(ast.op).toBe("or");
    const left = logical(ast.left);
    expect(left.op).toBe("and");
    expect(comparison(left.left).field).toBe("price");
    expect(comparison(left.right).field).toBe("m2");
    expect(comparison(ast.right).field).toBe("bedrooms");
  });

  it("'and' binds tighter than 'or': a or b and c => a or (b and c)", () => {
    const ast = logical(parse("price<1 or m2>2 and bedrooms=3"));
    expect(ast.op).toBe("or");
    expect(comparison(ast.left).field).toBe("price");
    const right = logical(ast.right);
    expect(right.op).toBe("and");
    expect(comparison(right.left).field).toBe("m2");
    expect(comparison(right.right).field).toBe("bedrooms");
  });

  it("parentheses override precedence: (a or b) and c", () => {
    const ast = logical(parse("(price<1 or m2>2) and bedrooms=3"));
    expect(ast.op).toBe("and");
    const left = logical(ast.left);
    expect(left.op).toBe("or");
    expect(comparison(ast.right).field).toBe("bedrooms");
  });

  it("handles nested parentheses", () => {
    const ast = logical(parse("((price<1))  and  (m2>2 or bedrooms=3)"));
    expect(ast.op).toBe("and");
    expect(comparison(ast.left).field).toBe("price");
    const right = logical(ast.right);
    expect(right.op).toBe("or");
  });

  it("chains of the same operator are left-associative", () => {
    const ast = logical(parse("price<1 and price<2 and price<3"));
    expect(ast.op).toBe("and");
    const left = logical(ast.left);
    expect(left.op).toBe("and");
    expect(comparison(left.left).value).toEqual({ kind: "number", value: 1, raw: "1" });
    expect(comparison(left.right).value).toEqual({ kind: "number", value: 2, raw: "2" });
    expect(comparison(ast.right).value).toEqual({ kind: "number", value: 3, raw: "3" });
  });

  it("matches field and keyword names case-insensitively", () => {
    const ast = logical(parse("PRICE<1 AND Type=casa"));
    expect(comparison(ast.left).field).toBe("price");
    expect(comparison(ast.right).field).toBe("type");
  });

  it("throws ParseError for an unknown field", () => {
    expect(() => parse("surface<10")).toThrow(ParseError);
    expect(() => parse("surface<10")).toThrow(/Unknown field 'surface'/);
  });

  it("throws ParseError when a field is not followed by an operator", () => {
    expect(() => parse("price 5")).toThrow(ParseError);
    expect(() => parse("price 5")).toThrow(/Expected an operator/);
  });

  it("throws ParseError when a comparison has no value", () => {
    expect(() => parse("price<")).toThrow(ParseError);
    expect(() => parse("price<")).toThrow(/Expected a value/);
  });

  it("throws ParseError on an unclosed parenthesis", () => {
    expect(() => parse("(price<1")).toThrow(ParseError);
    expect(() => parse("(price<1")).toThrow(/Expected '\)'/);
  });

  it("throws ParseError on an unopened parenthesis", () => {
    expect(() => parse("price<1)")).toThrow(ParseError);
  });

  it("throws ParseError on trailing garbage after a full expression", () => {
    expect(() => parse("price<1 price<2")).toThrow(ParseError);
    expect(() => parse("price<1 price<2")).toThrow(/Unexpected/);
  });

  it("throws ParseError on an empty expression", () => {
    expect(() => parse("")).toThrow(ParseError);
    expect(() => parse("   ")).toThrow(ParseError);
  });

  it("throws ParseError when a value is a bare 'and'/'or' keyword", () => {
    expect(() => parse("colonia:and")).toThrow(ParseError);
    expect(() => parse("colonia:and")).toThrow(/reserved keyword/);
  });

  it("still throws LexError (not ParseError) for tokenizer-level problems", () => {
    expect(() => parse('colonia:"unterminated')).toThrow(LexError);
  });
});

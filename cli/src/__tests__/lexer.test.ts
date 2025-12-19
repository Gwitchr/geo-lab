import { describe, expect, it } from "vitest";
import { tokenize } from "../parser/lexer.js";
import { LexError } from "../parser/errors.js";

describe("tokenize", () => {
  it("tokenizes a simple comparison", () => {
    const tokens = tokenize("price<2500000");
    expect(tokens.map((t) => [t.type, t.value])).toEqual([
      ["WORD", "price"],
      ["OP", "<"],
      ["NUMBER", "2500000"],
      ["EOF", ""],
    ]);
  });

  it("prefers two-character operators over one-character prefixes", () => {
    expect(tokenize("m2<=80").map((t) => t.type)).toEqual(["WORD", "OP", "NUMBER", "EOF"]);
    expect(tokenize("m2<=80")[1]).toMatchObject({ type: "OP", value: "<=" });
    expect(tokenize("bedrooms>=2")[1]).toMatchObject({ type: "OP", value: ">=" });
  });

  it("tokenizes all six operators", () => {
    for (const op of ["<", "<=", ">", ">=", "=", ":"]) {
      const tokens = tokenize(`price${op}1`);
      expect(tokens[1]).toMatchObject({ type: "OP", value: op });
    }
  });

  it("recognizes and/or case-insensitively as keywords", () => {
    expect(tokenize("a and b").map((t) => t.type)).toEqual(["WORD", "AND", "WORD", "EOF"]);
    expect(tokenize("a AND b")[1]).toMatchObject({ type: "AND" });
    expect(tokenize("a Or b")[1]).toMatchObject({ type: "OR" });
    expect(tokenize("a OR b")[1]).toMatchObject({ type: "OR" });
  });

  it("tokenizes parentheses", () => {
    expect(tokenize("(a)").map((t) => t.type)).toEqual(["LPAREN", "WORD", "RPAREN", "EOF"]);
  });

  it("tokenizes bare words including accented unicode letters", () => {
    const tokens = tokenize("colonia:cuauhtémoc");
    expect(tokens[2]).toMatchObject({ type: "WORD", value: "cuauhtémoc" });
  });

  it("tokenizes double-quoted strings and unescapes \\\" and \\\\", () => {
    const tokens = tokenize('colonia:"Santa Fe \\"Centro\\" \\\\ok"');
    expect(tokens[2]).toMatchObject({
      type: "STRING",
      value: 'Santa Fe "Centro" \\ok',
      quoted: true,
    });
  });

  it("tokenizes single-quoted strings", () => {
    const tokens = tokenize("colonia:'Santa Fe'");
    expect(tokens[2]).toMatchObject({ type: "STRING", value: "Santa Fe" });
  });

  it("tokenizes negative and decimal numbers", () => {
    expect(tokenize("lat<-99.5")[2]).toMatchObject({ type: "NUMBER", value: "-99.5", numericValue: -99.5 });
    expect(tokenize("price=2500000.50")[2]).toMatchObject({
      type: "NUMBER",
      value: "2500000.50",
      numericValue: 2500000.5,
    });
  });

  it("records the character position of each token", () => {
    const tokens = tokenize("price < 5");
    expect(tokens[0]).toMatchObject({ position: 0 });
    expect(tokens[1]).toMatchObject({ position: 6 });
    expect(tokens[2]).toMatchObject({ position: 8 });
  });

  it("throws LexError on an unterminated string", () => {
    expect(() => tokenize('colonia:"roma')).toThrow(LexError);
    expect(() => tokenize('colonia:"roma')).toThrow(/[Uu]nterminated string/);
  });

  it("throws LexError on an unexpected character", () => {
    expect(() => tokenize("price!2")).toThrow(LexError);
    expect(() => tokenize("price!2")).toThrow(/Unexpected character '!' at position 5/);
  });

  it("throws LexError on an invalid escape sequence", () => {
    expect(() => tokenize('colonia:"roma\\n"')).toThrow(LexError);
  });

  it("skips whitespace between tokens", () => {
    const tokens = tokenize("  price   <   5  ");
    expect(tokens.map((t) => t.type)).toEqual(["WORD", "OP", "NUMBER", "EOF"]);
  });
});

import { describe, expect, it } from "vitest";
import { compileFilter } from "../parser/eval.js";
import { EvalError, ParseError } from "../parser/errors.js";

describe("compileFilter", () => {
  it("compiles a numeric comparison to a bound parameter", () => {
    const { sql, params } = compileFilter("price<2500000");
    expect(sql).toBe("price_mxn < ?");
    expect(params).toEqual([2500000]);
  });

  it("compiles ':' to a case-insensitive LIKE with escaped wildcards", () => {
    const { sql, params } = compileFilter("colonia:roma");
    expect(sql).toBe("LOWER(colonia) LIKE ? ESCAPE '\\'");
    expect(params).toEqual(["%roma%"]);
  });

  it("lowercases the search term for ':' so matching is case-insensitive", () => {
    const { params } = compileFilter("colonia:ROMA");
    expect(params).toEqual(["%roma%"]);
  });

  it("escapes literal % and _ in ':' search terms", () => {
    const { params } = compileFilter('colonia:"50%_off"');
    expect(params).toEqual(["%50\\%\\_off%"]);
  });

  it("rejects ':' on numeric fields", () => {
    expect(() => compileFilter("price:2500000")).toThrow(EvalError);
    expect(() => compileFilter("price:2500000")).toThrow(/not valid for numeric field 'price'/);
  });

  it("rejects a non-numeric value for a numeric field", () => {
    expect(() => compileFilter("price<roma")).toThrow(EvalError);
    expect(() => compileFilter("price<roma")).toThrow(/expects a numeric value/);
  });

  it("accepts a quoted numeric-looking string for a numeric field", () => {
    const { sql, params } = compileFilter('price<"2500000"');
    expect(sql).toBe("price_mxn < ?");
    expect(params).toEqual([2500000]);
  });

  it("compiles a string equality comparison", () => {
    const { sql, params } = compileFilter("type=terreno");
    expect(sql).toBe("type = ?");
    expect(params).toEqual(["terreno"]);
  });

  it("keeps '=' case-sensitive (no lowering) unlike ':'", () => {
    const { params } = compileFilter("type=Terreno");
    expect(params).toEqual(["Terreno"]);
  });

  it("combines and/or into parenthesized SQL with parameters in source order", () => {
    // Exact shape (parenthesization) is pinned precisely in golden.test.ts;
    // here we just check the parameter binding order matches source order.
    const { params } = compileFilter("price<2500000 and colonia:roma or type=terreno");
    expect(params).toEqual([2500000, "%roma%", "terreno"]);
  });

  it("requires quotes for hyphenated 'listed' date values (bare dates don't lex as one token)", () => {
    expect(() => compileFilter("listed>2024-01-01")).toThrow(ParseError);
  });

  it("compiles a quoted 'listed' date comparison as a text comparison", () => {
    const { sql, params } = compileFilter('listed>="2024-01-01"');
    expect(sql).toBe("listed_date >= ?");
    expect(params).toEqual(["2024-01-01"]);
  });
});

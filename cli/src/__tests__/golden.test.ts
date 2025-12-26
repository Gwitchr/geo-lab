import { describe, expect, it } from "vitest";
import { compileFilter } from "../parser/eval.js";

/**
 * Golden cases: expression -> exact SQL WHERE fragment + bound params.
 * These pin the precise shape eval.ts produces, including parenthesization,
 * so a change to precedence or SQL generation is caught explicitly here.
 */
const CASES: Array<{ expr: string; sql: string; params: unknown[] }> = [
  {
    expr: "price<2500000",
    sql: "price_mxn < ?",
    params: [2500000],
  },
  {
    expr: "m2>=80",
    sql: "m2 >= ?",
    params: [80],
  },
  {
    expr: "bedrooms=3",
    sql: "bedrooms = ?",
    params: [3],
  },
  {
    expr: "type=terreno",
    sql: "type = ?",
    params: ["terreno"],
  },
  {
    expr: "colonia:roma",
    sql: "LOWER(colonia) LIKE ? ESCAPE '\\'",
    params: ["%roma%"],
  },
  {
    expr: "colonia:cuauhtémoc",
    sql: "LOWER(colonia) LIKE ? ESCAPE '\\'",
    params: ["%cuauhtémoc%"],
  },
  {
    expr: 'colonia:"Santa Fe"',
    sql: "LOWER(colonia) LIKE ? ESCAPE '\\'",
    params: ["%santa fe%"],
  },
  {
    // the brief's canonical example
    expr: "price<2500000 and colonia:roma or type=terreno",
    sql: "(price_mxn < ? AND LOWER(colonia) LIKE ? ESCAPE '\\') OR type = ?",
    params: [2500000, "%roma%", "terreno"],
  },
  {
    // parentheses flip the grouping relative to the case above
    expr: "price<2500000 and (colonia:roma or type=terreno)",
    sql: "price_mxn < ? AND (LOWER(colonia) LIKE ? ESCAPE '\\' OR type = ?)",
    params: [2500000, "%roma%", "terreno"],
  },
  {
    expr: "municipio=Coyoacán and bedrooms>=3",
    sql: "municipio = ? AND bedrooms >= ?",
    params: ["Coyoacán", 3],
  },
  {
    expr: 'listed>="2024-01-01" and listed<"2024-06-01"',
    sql: "listed_date >= ? AND listed_date < ?",
    params: ["2024-01-01", "2024-06-01"],
  },
  {
    expr: "price<1 and price<2 and price<3",
    sql: "(price_mxn < ? AND price_mxn < ?) AND price_mxn < ?",
    params: [1, 2, 3],
  },
  {
    expr: "price<1 or price<2 or price<3",
    sql: "(price_mxn < ? OR price_mxn < ?) OR price_mxn < ?",
    params: [1, 2, 3],
  },
];

describe("golden expression -> SQL cases", () => {
  it.each(CASES)("$expr", ({ expr, sql, params }) => {
    const compiled = compileFilter(expr);
    expect(compiled.sql).toBe(sql);
    expect(compiled.params).toEqual(params);
  });
});

import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { buildFixtureDb, FIXTURE_ROWS } from "./fixtures/fixtureDb.js";
import type { ListingsDatabase } from "../db.js";
import { runQuery } from "../commands/query.js";
import { runStats } from "../commands/stats.js";
import { runExport } from "../commands/export.js";

describe("runQuery against the fixture db", () => {
  let db: ListingsDatabase;
  beforeEach(() => {
    db = buildFixtureDb();
  });
  afterEach(() => {
    db.close();
  });

  it("returns all rows (within the default limit) when no filter is given", () => {
    const result = runQuery(db, {});
    expect(result.rows).toHaveLength(FIXTURE_ROWS.length);
  });

  it("applies the brief's canonical example filter", () => {
    const result = runQuery(db, { filter: "price<2500000 and colonia:roma or type=terreno" });
    const ids = result.rows.map((r) => r.id).sort();
    // price<2500000 AND colonia contains "roma": L0001 (2,450,000, Roma Norte), L0007 (2,350,000, Roma Norte)
    // OR type=terreno: L0003, L0008
    expect(ids).toEqual(["L0001", "L0003", "L0007", "L0008"]);
  });

  it("respects explicit parentheses differently from default precedence", () => {
    const withoutParens = runQuery(db, { filter: "price<2000000 and colonia:roma or type=terreno" });
    const withParens = runQuery(db, { filter: "price<2000000 and (colonia:roma or type=terreno)" });
    expect(withoutParens.rows.map((r) => r.id).sort()).not.toEqual(
      withParens.rows.map((r) => r.id).sort(),
    );
  });

  it("matches accented colonia values case-insensitively via contains", () => {
    const result = runQuery(db, { filter: "colonia:cuauhtémoc" });
    expect(result.rows.map((r) => r.id)).toEqual(["L0004"]);
  });

  it("matches accented values even when the query differs in ASCII case", () => {
    const result = runQuery(db, { filter: "colonia:CUAUHTÉMOC" });
    expect(result.rows.map((r) => r.id)).toEqual(["L0004"]);
  });

  it("respects --limit 0 as no limit", () => {
    const result = runQuery(db, { limit: 0 });
    expect(result.rows).toHaveLength(FIXTURE_ROWS.length);
  });

  it("respects a positive --limit", () => {
    const result = runQuery(db, { limit: 2 });
    expect(result.rows).toHaveLength(2);
  });

  it("restricts columns with --columns", () => {
    const result = runQuery(db, { columns: "id,price_mxn" });
    expect(result.columns).toEqual(["id", "price_mxn"]);
    expect(Object.keys(result.rows[0] as object).sort()).toEqual(["id", "price_mxn"]);
  });

  it("rejects an unknown column", () => {
    expect(() => runQuery(db, { columns: "id,nope" })).toThrow(/Unknown column 'nope'/);
  });

  it("propagates filter syntax errors", () => {
    expect(() => runQuery(db, { filter: "price<" })).toThrow(/Expected a value/);
  });
});

describe("runStats against the fixture db", () => {
  let db: ListingsDatabase;
  beforeEach(() => {
    db = buildFixtureDb();
  });
  afterEach(() => {
    db.close();
  });

  it("computes overall aggregates over all rows", () => {
    const result = runStats(db, {});
    expect(result.overall.count).toBe(FIXTURE_ROWS.length);
    const prices = FIXTURE_ROWS.map((r) => r.price_mxn);
    expect(result.overall.priceMin).toBe(Math.min(...prices));
    expect(result.overall.priceMax).toBe(Math.max(...prices));
  });

  it("applies a filter before aggregating", () => {
    const result = runStats(db, { filter: "type=departamento" });
    expect(result.overall.count).toBe(FIXTURE_ROWS.filter((r) => r.type === "departamento").length);
  });

  it("groups by a field with --by", () => {
    const result = runStats(db, { by: "municipio" });
    expect(result.groups).toBeDefined();
    const cuauhtemocGroup = result.groups?.find((g) => g.group === "Cuauhtémoc");
    expect(cuauhtemocGroup?.count).toBe(
      FIXTURE_ROWS.filter((r) => r.municipio === "Cuauhtémoc").length,
    );
  });

  it("rejects an unknown --by field", () => {
    expect(() => runStats(db, { by: "nope" })).toThrow(/Unknown --by field 'nope'/);
  });
});

describe("runExport against the fixture db", () => {
  let db: ListingsDatabase;
  beforeEach(() => {
    db = buildFixtureDb();
  });
  afterEach(() => {
    db.close();
  });

  it("exports all matching rows as JSON by default", () => {
    const result = runExport(db, { filter: "type=terreno" });
    expect(result.format).toBe("json");
    const parsed = JSON.parse(result.content);
    expect(parsed).toHaveLength(FIXTURE_ROWS.filter((r) => r.type === "terreno").length);
  });

  it("exports as CSV with a header row when requested", () => {
    const result = runExport(db, { filter: "type=terreno", format: "csv", columns: "id,price_mxn" });
    const lines = result.content.trim().split("\n");
    expect(lines[0]).toBe("id,price_mxn");
    expect(lines).toHaveLength(1 + FIXTURE_ROWS.filter((r) => r.type === "terreno").length);
  });

  it("infers csv format from the --out extension", () => {
    const result = runExport(db, { outPath: "listings.csv" });
    expect(result.format).toBe("csv");
  });

  it("infers json format from the --out extension", () => {
    const result = runExport(db, { outPath: "listings.json" });
    expect(result.format).toBe("json");
  });

  it("quotes CSV fields containing commas or quotes", () => {
    // "id" is not a filter-language field; select the row by its unique price instead.
    const result = runExport(db, { filter: "price=2450000", format: "csv", columns: "id,description" });
    const lines = result.content.trim().split("\n");
    // L0001's description contains a comma ("...del metro, URGE VENDER")
    expect(lines[1]).toContain('"');
    expect(lines[1]?.startsWith("L0001,")).toBe(true);
  });
});

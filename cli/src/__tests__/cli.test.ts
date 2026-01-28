import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { runCli, type CliIO } from "../cli.js";
import { buildFixtureDbFile, FIXTURE_ROWS } from "./fixtures/fixtureDb.js";

function makeIo(): CliIO & { lines: string[]; errLines: string[] } {
  const lines: string[] = [];
  const errLines: string[] = [];
  return {
    lines,
    errLines,
    stdout: (l) => lines.push(l),
    stderr: (l) => errLines.push(l),
  };
}

describe("runCli against a file-backed fixture db", () => {
  let tmpDir: string;
  let dbPath: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "geoq-cli-test-"));
    dbPath = path.join(tmpDir, "fixture.sqlite");
    const db = buildFixtureDbFile(dbPath);
    db.close();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("prints usage and exits 1 with no command", () => {
    const io = makeIo();
    const code = runCli([], io);
    expect(code).toBe(1);
    expect(io.lines.join("\n")).toMatch(/Usage:/);
  });

  it("exits 0 with --help", () => {
    const io = makeIo();
    const code = runCli(["--help"], io);
    expect(code).toBe(0);
  });

  it("errors on an unknown command", () => {
    const io = makeIo();
    const code = runCli(["frobnicate"], io);
    expect(code).toBe(1);
    expect(io.errLines.join("\n")).toMatch(/Unknown command 'frobnicate'/);
  });

  it("runs a query and prints a text table", () => {
    const io = makeIo();
    const code = runCli(["query", "type=terreno", "--db", dbPath], io);
    expect(code).toBe(0);
    const out = io.lines.join("\n");
    expect(out).toMatch(/L0003/);
    expect(out).toMatch(/L0008/);
    expect(out).toMatch(/\(2 rows\)/);
  });

  it("runs a query with --json and produces parseable JSON matching the fixture", () => {
    const io = makeIo();
    const code = runCli(["query", "type=terreno", "--db", dbPath, "--json"], io);
    expect(code).toBe(0);
    const rows = JSON.parse(io.lines.join("\n"));
    expect(rows.map((r: { id: string }) => r.id).sort()).toEqual(["L0003", "L0008"]);
  });

  it("runs the brief's canonical example end to end", () => {
    const io = makeIo();
    const code = runCli(
      ["query", "price<2500000 and colonia:roma or type=terreno", "--db", dbPath, "--json"],
      io,
    );
    expect(code).toBe(0);
    const rows = JSON.parse(io.lines.join("\n"));
    expect(rows.map((r: { id: string }) => r.id).sort()).toEqual(["L0001", "L0003", "L0007", "L0008"]);
  });

  it("reports a syntax error with exit code 1 and no stack noise", () => {
    const io = makeIo();
    const code = runCli(["query", "price<", "--db", dbPath], io);
    expect(code).toBe(1);
    expect(io.errLines.join("\n")).toMatch(/^Error: Expected a value/);
  });

  it("reports an unknown field error", () => {
    const io = makeIo();
    const code = runCli(["query", "surface<10", "--db", dbPath], io);
    expect(code).toBe(1);
    expect(io.errLines.join("\n")).toMatch(/Unknown field 'surface'/);
  });

  it("errors clearly when --db points nowhere", () => {
    const io = makeIo();
    const code = runCli(["query", "price<1", "--db", path.join(tmpDir, "missing.sqlite")], io);
    expect(code).toBe(1);
    expect(io.errLines.join("\n")).toMatch(/Database not found/);
  });

  it("runs stats and reports the overall count", () => {
    const io = makeIo();
    const code = runCli(["stats", "--db", dbPath, "--json"], io);
    expect(code).toBe(0);
    const result = JSON.parse(io.lines.join("\n"));
    expect(result.overall.count).toBe(FIXTURE_ROWS.length);
  });

  it("runs stats --by municipio and groups correctly", () => {
    const io = makeIo();
    const code = runCli(["stats", "--db", dbPath, "--by", "municipio", "--json"], io);
    expect(code).toBe(0);
    const result = JSON.parse(io.lines.join("\n"));
    const cuauhtemoc = result.groups.find((g: { group: string }) => g.group === "Cuauhtémoc");
    expect(cuauhtemoc.count).toBe(FIXTURE_ROWS.filter((r) => r.municipio === "Cuauhtémoc").length);
  });

  it("exports filtered rows to a CSV file", () => {
    const io = makeIo();
    const outPath = path.join(tmpDir, "out.csv");
    const code = runCli(["export", "type=terreno", "--db", dbPath, "--out", outPath], io);
    expect(code).toBe(0);
    expect(io.lines.join("\n")).toMatch(/Exported 2 rows \(csv\)/);
    const content = fs.readFileSync(outPath, "utf8");
    const lines = content.trim().split("\n");
    expect(lines).toHaveLength(3); // header + 2 rows
  });

  it("exports to stdout as JSON when --out is omitted", () => {
    const io = makeIo();
    const code = runCli(["export", "type=terreno", "--db", dbPath], io);
    expect(code).toBe(0);
    const rows = JSON.parse(io.lines.join("\n"));
    expect(rows).toHaveLength(2);
  });
});

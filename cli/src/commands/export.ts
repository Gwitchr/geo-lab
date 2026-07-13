import type { ListingsDatabase } from "../db.js";
import { compileFilter } from "../parser/eval.js";
import { resolveColumns } from "../types.js";
import type { ListingRow } from "../types.js";
import { runExportGeoJson } from "./export-geojson.js";

export type ExportFormat = "json" | "csv" | "geojson";

export interface ExportOptions {
  filter?: string;
  format?: ExportFormat;
  outPath?: string;
  columns?: string;
}

export interface ExportResult {
  sql: string;
  params: readonly unknown[];
  columns: string[];
  rows: Partial<ListingRow>[];
  format: ExportFormat;
  content: string;
  outPath?: string;
}

function inferFormat(outPath: string | undefined): ExportFormat | undefined {
  if (!outPath) return undefined;
  if (outPath.endsWith(".csv")) return "csv";
  if (outPath.endsWith(".geojson")) return "geojson";
  if (outPath.endsWith(".json")) return "json";
  return undefined;
}

function csvField(value: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function toCsv(rows: Partial<ListingRow>[], columns: string[]): string {
  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((c) => csvField((row as Record<string, unknown>)[c])).join(","));
  }
  return lines.join("\n") + "\n";
}

export function runExport(db: ListingsDatabase, options: ExportOptions = {}): ExportResult {
  const format: ExportFormat = options.format ?? inferFormat(options.outPath) ?? "json";

  if (format === "geojson") {
    // export-geojson.ts runs its own query (a fixed column set, not
    // --columns-aware yet), so sql/params/columns/rows are left empty here.
    const collection = runExportGeoJson(db, { filter: options.filter });
    return {
      sql: "",
      params: [],
      columns: [],
      rows: [],
      format,
      content: JSON.stringify(collection, null, 2) + "\n",
      outPath: options.outPath,
    };
  }

  const columns = resolveColumns(options.columns);
  let whereSql = "";
  let params: readonly unknown[] = [];
  if (options.filter !== undefined && options.filter.trim() !== "") {
    const compiled = compileFilter(options.filter);
    whereSql = ` WHERE ${compiled.sql}`;
    params = compiled.params;
  }

  const sql = `SELECT ${columns.join(", ")} FROM listings${whereSql} ORDER BY listed_date DESC`;
  const rows = db.prepare(sql).all(...params) as Partial<ListingRow>[];

  const content = format === "csv" ? toCsv(rows, columns) : JSON.stringify(rows, null, 2) + "\n";

  return { sql, params, columns, rows, format, content, outPath: options.outPath };
}

import type { ListingsDatabase } from "../db.js";
import { compileFilter } from "../parser/eval.js";
import { resolveColumns } from "../types.js";
import type { ListingRow } from "../types.js";

export const DEFAULT_QUERY_LIMIT = 20;

export interface QueryOptions {
  /** Filter language expression; omitted/blank means "no filter". */
  filter?: string;
  /** Max rows to return. 0 (or negative) means "no limit". Default: 20. */
  limit?: number;
  /** Restrict/reorder returned columns; default is all columns. */
  columns?: string;
}

export interface QueryResult {
  sql: string;
  params: readonly unknown[];
  columns: string[];
  rows: Partial<ListingRow>[];
}

export function runQuery(db: ListingsDatabase, options: QueryOptions = {}): QueryResult {
  const columns = resolveColumns(options.columns);
  let whereSql = "";
  let params: readonly unknown[] = [];
  if (options.filter !== undefined && options.filter.trim() !== "") {
    const compiled = compileFilter(options.filter);
    whereSql = ` WHERE ${compiled.sql}`;
    params = compiled.params;
  }

  const limit = options.limit ?? DEFAULT_QUERY_LIMIT;
  const limitSql = limit > 0 ? ` LIMIT ${limit}` : "";
  const sql = `SELECT ${columns.join(", ")} FROM listings${whereSql} ORDER BY listed_date DESC${limitSql}`;
  const rows = db.prepare(sql).all(...params) as Partial<ListingRow>[];

  return { sql, params, columns, rows };
}

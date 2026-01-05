import type { ListingsDatabase } from "../db.js";
import { compileFilter, FIELD_COLUMNS } from "../parser/eval.js";
import { FIELDS, isField, type Field } from "../parser/ast.js";

export const DEFAULT_GROUP_LIMIT = 15;

export interface StatsOptions {
  /** Filter language expression; omitted/blank means "no filter". */
  filter?: string;
  /** Field to group by (any of the filter-language field names). */
  by?: string;
  /** Max groups to return, ordered by count desc. Default: 15. */
  limit?: number;
}

export interface OverallStats {
  count: number;
  priceMin: number | null;
  priceAvg: number | null;
  priceMax: number | null;
  m2Avg: number | null;
  pricePerM2Avg: number | null;
}

export interface GroupStat {
  group: string;
  count: number;
  priceAvg: number | null;
  pricePerM2Avg: number | null;
}

export interface StatsResult {
  overall: OverallStats;
  by?: Field;
  groups?: GroupStat[];
  sql: string;
  params: readonly unknown[];
}

interface RawOverallRow {
  count: number;
  priceMin: number | null;
  priceAvg: number | null;
  priceMax: number | null;
  m2Avg: number | null;
  pricePerM2Avg: number | null;
}

interface RawGroupRow {
  grp: string;
  count: number;
  priceAvg: number | null;
  pricePerM2Avg: number | null;
}

export function runStats(db: ListingsDatabase, options: StatsOptions = {}): StatsResult {
  let whereSql = "";
  let params: readonly unknown[] = [];
  if (options.filter !== undefined && options.filter.trim() !== "") {
    const compiled = compileFilter(options.filter);
    whereSql = ` WHERE ${compiled.sql}`;
    params = compiled.params;
  }

  const overallSql =
    `SELECT COUNT(*) AS count, MIN(price_mxn) AS priceMin, AVG(price_mxn) AS priceAvg, ` +
    `MAX(price_mxn) AS priceMax, AVG(m2) AS m2Avg, ` +
    `AVG(price_mxn * 1.0 / NULLIF(m2, 0)) AS pricePerM2Avg ` +
    `FROM listings${whereSql}`;
  const overallRow = db.prepare(overallSql).get(...params) as RawOverallRow;
  const overall: OverallStats = {
    count: overallRow.count,
    priceMin: overallRow.priceMin,
    priceAvg: overallRow.priceAvg,
    priceMax: overallRow.priceMax,
    m2Avg: overallRow.m2Avg,
    pricePerM2Avg: overallRow.pricePerM2Avg,
  };

  let groups: GroupStat[] | undefined;
  let by: Field | undefined;
  if (options.by !== undefined) {
    const byLower = options.by.toLowerCase();
    if (!isField(byLower)) {
      throw new Error(`Unknown --by field '${options.by}', expected one of: ${FIELDS.join(", ")}`);
    }
    by = byLower;
    const column = FIELD_COLUMNS[by];
    const limit = options.limit ?? DEFAULT_GROUP_LIMIT;
    const groupSql =
      `SELECT ${column} AS grp, COUNT(*) AS count, AVG(price_mxn) AS priceAvg, ` +
      `AVG(price_mxn * 1.0 / NULLIF(m2, 0)) AS pricePerM2Avg ` +
      `FROM listings${whereSql} GROUP BY ${column} ORDER BY count DESC LIMIT ${limit}`;
    const rawGroups = db.prepare(groupSql).all(...params) as RawGroupRow[];
    groups = rawGroups.map((r) => ({
      group: r.grp,
      count: r.count,
      priceAvg: r.priceAvg,
      pricePerM2Avg: r.pricePerM2Avg,
    }));
  }

  return { overall, by, groups, sql: overallSql, params };
}

import fs from "node:fs";
import path from "node:path";

import { openDb, DEFAULT_DB_PATH } from "./db.js";
import { parseArgs, optionString, optionNumber, optionFlag } from "./args.js";
import { runQuery, DEFAULT_QUERY_LIMIT } from "./commands/query.js";
import { runStats } from "./commands/stats.js";
import { runExport, type ExportFormat } from "./commands/export.js";
import { formatTable, formatNumber } from "./format.js";
import { FilterError } from "./parser/errors.js";

export interface CliIO {
  stdout: (line: string) => void;
  stderr: (line: string) => void;
}

function defaultIo(): CliIO {
  return {
    stdout: (line) => {
      process.stdout.write(line + "\n");
    },
    stderr: (line) => {
      process.stderr.write(line + "\n");
    },
  };
}

const USAGE = `geoq - query the geo-lab listings database

Usage:
  geoq query [expr] [--db path] [--limit N] [--columns a,b,c] [--json]
  geoq stats [expr] [--db path] [--by field] [--limit N] [--json]
  geoq export [expr] [--out path] [--db path] [--format json|csv] [--columns a,b,c]

Options:
  --db <path>       Path to the sqlite database (default: ${DEFAULT_DB_PATH}, resolved from the current directory)
  --limit <n>       query: max rows (default ${DEFAULT_QUERY_LIMIT}, 0 = no limit). stats --by: max groups (default 15)
  --columns <list>  Comma-separated column subset (query/export)
  --by <field>      Group stats by a filter-language field (price|m2|bedrooms|type|colonia|municipio|listed)
  --out <path>      export: write to this file instead of stdout; format inferred from extension
  --format <fmt>    export: "json" or "csv" (overrides extension inference)
  --json            query/stats: print machine-readable JSON instead of a text table
  --help            Show this help

Filter expression grammar (see docs/filter-language.md):
  expr    := clause (("and"|"or") clause)*
  clause  := field op value | "(" expr ")"
  field   := price | m2 | bedrooms | type | colonia | municipio | listed
  op      := < | <= | > | >= | = | :   (":" = contains, case-insensitive)
  value   := number | "quoted string" | bare_word
  "and" binds tighter than "or"; use parentheses to override.

Examples:
  geoq query "price<2500000 and colonia:roma or type=terreno"
  geoq stats "type=departamento" --by municipio
  geoq export "m2>=80" --out out.csv
`;

function formatError(err: unknown): string {
  if (err instanceof FilterError) {
    return `Error: ${err.message} (position ${err.position})`;
  }
  if (err instanceof Error) {
    return `Error: ${err.message}`;
  }
  return `Error: ${String(err)}`;
}

export function runCli(argv: readonly string[], io: CliIO = defaultIo()): number {
  const command = argv[0];
  const rest = argv.slice(1);

  if (command === undefined) {
    io.stdout(USAGE);
    return 1;
  }
  if (command === "--help" || command === "-h") {
    io.stdout(USAGE);
    return 0;
  }

  const { positional, options } = parseArgs(rest);

  if (optionFlag(options, "help")) {
    io.stdout(USAGE);
    return 0;
  }

  try {
    switch (command) {
      case "query":
        return runQueryCommand(positional, options, io);
      case "stats":
        return runStatsCommand(positional, options, io);
      case "export":
        return runExportCommand(positional, options, io);
      default:
        io.stderr(`Unknown command '${command}'\n\n${USAGE}`);
        return 1;
    }
  } catch (err) {
    io.stderr(formatError(err));
    return 1;
  }
}

function runQueryCommand(
  positional: readonly string[],
  options: Record<string, string | boolean>,
  io: CliIO,
): number {
  const dbPath = optionString(options, "db") ?? DEFAULT_DB_PATH;
  const filter = positional[0];
  const limit = optionNumber(options, "limit");
  const columns = optionString(options, "columns");
  const asJson = optionFlag(options, "json");

  const db = openDb(dbPath);
  try {
    const result = runQuery(db, { filter, limit, columns });
    if (asJson) {
      io.stdout(JSON.stringify(result.rows, null, 2));
      return 0;
    }
    io.stdout(formatTable(result.rows as Record<string, unknown>[], result.columns));
    const effectiveLimit = limit ?? DEFAULT_QUERY_LIMIT;
    const truncated = effectiveLimit > 0 && result.rows.length === effectiveLimit;
    const countLine = `(${result.rows.length} row${result.rows.length === 1 ? "" : "s"}${
      truncated ? `, showing first ${effectiveLimit} - pass --limit to see more` : ""
    })`;
    io.stdout(countLine);
    return 0;
  } finally {
    db.close();
  }
}

function runStatsCommand(
  positional: readonly string[],
  options: Record<string, string | boolean>,
  io: CliIO,
): number {
  const dbPath = optionString(options, "db") ?? DEFAULT_DB_PATH;
  const filter = positional[0];
  const by = optionString(options, "by");
  const limit = optionNumber(options, "limit");
  const asJson = optionFlag(options, "json");

  const db = openDb(dbPath);
  try {
    const result = runStats(db, { filter, by, limit });
    if (asJson) {
      io.stdout(JSON.stringify(result, null, 2));
      return 0;
    }

    io.stdout(`listings: ${formatNumber(result.overall.count)}`);
    io.stdout(
      `price_mxn: min ${formatNumber(result.overall.priceMin)}  avg ${formatNumber(result.overall.priceAvg)}  max ${formatNumber(result.overall.priceMax)}`,
    );
    io.stdout(`m2: avg ${formatNumber(result.overall.m2Avg, 1)}`);
    io.stdout(`price/m2: avg ${formatNumber(result.overall.pricePerM2Avg, 0)}`);

    if (result.groups && result.by) {
      io.stdout("");
      io.stdout(`by ${result.by}:`);
      const rows = result.groups.map((g) => ({
        [result.by as string]: g.group,
        count: formatNumber(g.count),
        price_avg: formatNumber(g.priceAvg),
        price_per_m2_avg: formatNumber(g.pricePerM2Avg),
      }));
      io.stdout(formatTable(rows, [result.by, "count", "price_avg", "price_per_m2_avg"]));
    }
    return 0;
  } finally {
    db.close();
  }
}

function runExportCommand(
  positional: readonly string[],
  options: Record<string, string | boolean>,
  io: CliIO,
): number {
  const dbPath = optionString(options, "db") ?? DEFAULT_DB_PATH;
  const filter = positional[0];
  const outPath = optionString(options, "out");
  const formatOpt = optionString(options, "format");
  if (formatOpt !== undefined && formatOpt !== "json" && formatOpt !== "csv") {
    throw new Error(`Option --format expects 'json' or 'csv', got '${formatOpt}'`);
  }
  const columns = optionString(options, "columns");

  const db = openDb(dbPath);
  try {
    const result = runExport(db, {
      filter,
      format: formatOpt as ExportFormat | undefined,
      outPath,
      columns,
    });
    if (outPath !== undefined) {
      const resolved = path.resolve(process.cwd(), outPath);
      fs.mkdirSync(path.dirname(resolved), { recursive: true });
      fs.writeFileSync(resolved, result.content, "utf8");
      io.stdout(
        `Exported ${result.rows.length} row${result.rows.length === 1 ? "" : "s"} (${result.format}) -> ${resolved}`,
      );
    } else {
      io.stdout(result.content.replace(/\n$/, ""));
    }
    return 0;
  } finally {
    db.close();
  }
}

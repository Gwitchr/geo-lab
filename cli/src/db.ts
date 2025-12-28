import path from "node:path";
import fs from "node:fs";
import Database from "better-sqlite3";

export type ListingsDatabase = Database.Database;

/** Default --db value, relative to the directory geoq is invoked from (repo root). */
export const DEFAULT_DB_PATH = "data/db.sqlite";

/**
 * Open the listings database read-only. `dbPath` is resolved against the
 * current working directory, so `geoq` is expected to run from the repo
 * root (or with an explicit --db path).
 */
export function openDb(dbPath: string): ListingsDatabase {
  if (dbPath === ":memory:") {
    return new Database(":memory:");
  }
  const resolved = path.resolve(process.cwd(), dbPath);
  if (!fs.existsSync(resolved)) {
    throw new Error(
      `Database not found at '${resolved}'. Pass --db <path> or run from the repo root (default: ${DEFAULT_DB_PATH}).`,
    );
  }
  try {
    return new Database(resolved, { fileMustExist: true, readonly: true });
  } catch (err) {
    throw new Error(
      `Could not open database at '${resolved}': ${(err as Error).message}`,
    );
  }
}

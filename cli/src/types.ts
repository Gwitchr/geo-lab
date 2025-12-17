/** Row shape of the `listings` table (see BRIEF.md for the schema). */
export interface ListingRow {
  id: string;
  title: string;
  description: string;
  price_mxn: number;
  m2: number;
  bedrooms: number;
  type: string;
  colonia: string;
  municipio: string;
  estado: string;
  lat: number;
  lng: number;
  listed_date: string;
  source: string;
}

/** Column names in schema order, used to validate --columns and drive CSV export. */
export const ALL_COLUMNS: readonly (keyof ListingRow)[] = [
  "id",
  "title",
  "description",
  "price_mxn",
  "m2",
  "bedrooms",
  "type",
  "colonia",
  "municipio",
  "estado",
  "lat",
  "lng",
  "listed_date",
  "source",
];

export function isListingColumn(name: string): name is keyof ListingRow {
  return (ALL_COLUMNS as readonly string[]).includes(name);
}

/**
 * Parse a comma-separated --columns value into a validated, deduplicated
 * column list. Returns the full default column list when `raw` is undefined.
 */
export function resolveColumns(raw: string | undefined): (keyof ListingRow)[] {
  if (raw === undefined) return [...ALL_COLUMNS];
  const requested = raw
    .split(",")
    .map((c) => c.trim())
    .filter((c) => c.length > 0);
  if (requested.length === 0) return [...ALL_COLUMNS];
  const seen = new Set<string>();
  const columns: (keyof ListingRow)[] = [];
  for (const name of requested) {
    if (!isListingColumn(name)) {
      throw new Error(
        `Unknown column '${name}', expected one of: ${ALL_COLUMNS.join(", ")}`,
      );
    }
    if (!seen.has(name)) {
      seen.add(name);
      columns.push(name);
    }
  }
  return columns;
}

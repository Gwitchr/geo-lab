export type ListingType = "casa" | "departamento" | "terreno" | "local";

export interface Listing {
  id: string;
  title: string;
  price_mxn: number;
  m2: number;
  bedrooms: number;
  type: ListingType | string;
  colonia: string;
  municipio: string;
  estado: string;
  lat: number;
  lng: number;
  listed_date: string;
}

const TEXT_FIELDS = [
  "title",
  "colonia",
  "municipio",
  "estado",
  "type",
] as const satisfies readonly (keyof Listing)[];

const NUMERIC_FIELDS = {
  price: "price_mxn",
  m2: "m2",
  bedrooms: "bedrooms",
} as const;

type NumericFieldKey = keyof typeof NUMERIC_FIELDS;

/** Strip accents so "cuauhtemoc" matches "Cuauhtémoc". */
function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

/**
 * Loads the listings JSON slice exported by the pipeline (web/public/listings.json
 * in production; overridden in tests). Default URL is built from Vite's
 * configured BASE_URL so it still resolves once GitHub Pages serves this app
 * from a "/geo-lab/" subpath instead of domain root. Throws if the response
 * is not ok or the body is not an array.
 */
export async function loadListings(
  url = `${import.meta.env.BASE_URL}listings.json`,
): Promise<Listing[]> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`failed to load listings from ${url}: ${res.status} ${res.statusText}`);
  }
  const data: unknown = await res.json();
  if (!Array.isArray(data)) {
    throw new Error(`listings payload at ${url} is not an array`);
  }
  return data as Listing[];
}

const COMPARATORS = ["<=", ">=", "<", ">", ":", "="] as const;

interface ParsedToken {
  field: string | null;
  op: (typeof COMPARATORS)[number] | null;
  value: string;
}

/** Splits "price<2000000 colonia:roma" into individual whitespace-separated tokens. */
function tokenize(query: string): string[] {
  return query.trim().split(/\s+/).filter(Boolean);
}

/** Parses a single token into an optional field/operator pair plus the raw value. */
function parseToken(token: string): ParsedToken {
  for (const op of COMPARATORS) {
    const idx = token.indexOf(op);
    if (idx > 0) {
      const field = token.slice(0, idx);
      if (field in NUMERIC_FIELDS || (TEXT_FIELDS as readonly string[]).includes(field)) {
        return { field, op, value: token.slice(idx + op.length) };
      }
    }
  }
  return { field: null, op: null, value: token };
}

function matchesNumeric(listing: Listing, field: NumericFieldKey, op: string, raw: string): boolean {
  const num = Number(raw);
  if (Number.isNaN(num)) return false;
  const actual = listing[NUMERIC_FIELDS[field]] as number;
  switch (op) {
    case "<":
      return actual < num;
    case "<=":
      return actual <= num;
    case ">":
      return actual > num;
    case ">=":
      return actual >= num;
    case "=":
      return actual === num;
    case ":":
      return String(actual).includes(raw);
    default:
      return false;
  }
}

function matchesText(listing: Listing, field: (typeof TEXT_FIELDS)[number], raw: string): boolean {
  const haystack = normalize(String(listing[field]));
  return haystack.includes(normalize(raw));
}

function matchesAnyField(listing: Listing, raw: string): boolean {
  const needle = normalize(raw);
  if (!needle) return true;
  return TEXT_FIELDS.some((field) => normalize(String(listing[field])).includes(needle));
}

function matchesToken(listing: Listing, token: ParsedToken): boolean {
  if (token.field && token.op) {
    if (token.field in NUMERIC_FIELDS) {
      return matchesNumeric(listing, token.field as NumericFieldKey, token.op, token.value);
    }
    if ((TEXT_FIELDS as readonly string[]).includes(token.field)) {
      return matchesText(listing, token.field as (typeof TEXT_FIELDS)[number], token.value);
    }
  }
  return matchesAnyField(listing, token.value);
}

/**
 * Simple client-side filter for the table's filter box. Whitespace-separated
 * tokens are AND-ed together. Each token is either a bare word (substring match,
 * accent-insensitive, across title/colonia/municipio/estado/type) or a
 * "field<op>value" pair, e.g. "price<2000000", "m2>=80", "colonia:roma",
 * "type=casa". Empty query returns all listings.
 */
export function filterListings(listings: Listing[], query: string): Listing[] {
  const tokens = tokenize(query).map(parseToken);
  if (tokens.length === 0) return listings;
  return listings.filter((listing) => tokens.every((token) => matchesToken(listing, token)));
}

export function sortListings(
  listings: Listing[],
  field: keyof Listing,
  direction: "asc" | "desc" = "asc",
): Listing[] {
  const sign = direction === "asc" ? 1 : -1;
  return [...listings].sort((a, b) => {
    const av = a[field];
    const bv = b[field];
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * sign;
    return String(av).localeCompare(String(bv)) * sign;
  });
}

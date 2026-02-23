import { describe, expect, it, vi, afterEach } from "vitest";
import { filterListings, loadListings, sortListings, type Listing } from "../data";

function makeListing(overrides: Partial<Listing>): Listing {
  return {
    id: "L0001",
    title: "Departamento en Roma Norte",
    price_mxn: 2_500_000,
    m2: 80,
    bedrooms: 2,
    type: "departamento",
    colonia: "Roma Norte",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de México",
    lat: 19.42,
    lng: -99.16,
    listed_date: "2025-01-15",
    ...overrides,
  };
}

const listings: Listing[] = [
  makeListing({
    id: "L0001",
    title: "Depa moderno en Roma Norte",
    price_mxn: 2_500_000,
    m2: 80,
    colonia: "Roma Norte",
    municipio: "Cuauhtémoc",
    type: "departamento",
  }),
  makeListing({
    id: "L0002",
    title: "Casa amplia en Coyoacán",
    price_mxn: 5_800_000,
    m2: 220,
    colonia: "Del Carmen",
    municipio: "Coyoacán",
    type: "casa",
    bedrooms: 4,
  }),
  makeListing({
    id: "L0003",
    title: "Terreno en Cuauhtémoc",
    price_mxn: 1_200_000,
    m2: 300,
    colonia: "Cuauhtémoc",
    municipio: "Cuauhtémoc",
    type: "terreno",
    bedrooms: 0,
  }),
  makeListing({
    id: "L0004",
    title: "Local comercial Nápoles",
    price_mxn: 3_100_000,
    m2: 60,
    colonia: "Nápoles",
    municipio: "Benito Juárez",
    type: "local",
    bedrooms: 0,
  }),
];

describe("filterListings", () => {
  it("returns all listings for an empty query", () => {
    expect(filterListings(listings, "")).toHaveLength(4);
    expect(filterListings(listings, "   ")).toHaveLength(4);
  });

  it("matches a bare word across text fields, case-insensitively", () => {
    const result = filterListings(listings, "roma");
    expect(result.map((l) => l.id)).toEqual(["L0001"]);
  });

  it("is accent-insensitive for bare words and colonia field matches", () => {
    const bare = filterListings(listings, "napoles");
    expect(bare.map((l) => l.id)).toEqual(["L0004"]);

    const field = filterListings(listings, "colonia:cuauhtemoc");
    // "Cuauhtémoc" appears both as the colonia name and substring-matches
    // "Cuauhtémoc" municipio-named colonia only, not Roma Norte.
    expect(field.map((l) => l.id)).toEqual(["L0003"]);
  });

  it("supports numeric field filters with comparison operators", () => {
    expect(filterListings(listings, "price<2000000").map((l) => l.id)).toEqual(["L0003"]);
    expect(filterListings(listings, "price>=3000000").map((l) => l.id)).toEqual(["L0002", "L0004"]);
    expect(filterListings(listings, "m2>100").map((l) => l.id)).toEqual(["L0002", "L0003"]);
    expect(filterListings(listings, "bedrooms=4").map((l) => l.id)).toEqual(["L0002"]);
  });

  it("supports the colonia: substring operator", () => {
    expect(filterListings(listings, "colonia:carmen").map((l) => l.id)).toEqual(["L0002"]);
  });

  it("supports the type= exact-field filter", () => {
    expect(filterListings(listings, "type=terreno").map((l) => l.id)).toEqual(["L0003"]);
  });

  it("ANDs multiple whitespace-separated tokens", () => {
    const result = filterListings(listings, "price<4000000 type=departamento");
    expect(result.map((l) => l.id)).toEqual(["L0001"]);
  });

  it("returns an empty array when nothing matches", () => {
    expect(filterListings(listings, "colonia:zzz-no-existe")).toEqual([]);
  });

  it("treats an unparsable numeric value as no match rather than throwing", () => {
    expect(() => filterListings(listings, "price<abc")).not.toThrow();
    expect(filterListings(listings, "price<abc")).toEqual([]);
  });
});

describe("sortListings", () => {
  it("sorts numeric fields ascending and descending without mutating the input", () => {
    const asc = sortListings(listings, "price_mxn", "asc");
    expect(asc.map((l) => l.id)).toEqual(["L0003", "L0001", "L0004", "L0002"]);

    const desc = sortListings(listings, "price_mxn", "desc");
    expect(desc.map((l) => l.id)).toEqual(["L0002", "L0004", "L0001", "L0003"]);

    expect(listings.map((l) => l.id)).toEqual(["L0001", "L0002", "L0003", "L0004"]);
  });

  it("sorts text fields alphabetically", () => {
    const asc = sortListings(listings, "colonia", "asc");
    expect(asc.map((l) => l.colonia)).toEqual(["Cuauhtémoc", "Del Carmen", "Nápoles", "Roma Norte"]);
  });
});

describe("loadListings", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches and returns the parsed JSON array", async () => {
    const payload = [makeListing({ id: "L0099" })];
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(payload), { status: 200 })),
    );

    const result = await loadListings("/listings.json");
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("L0099");
  });

  it("throws a descriptive error on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("not found", { status: 404, statusText: "Not Found" })),
    );

    await expect(loadListings("/missing.json")).rejects.toThrow(/404/);
  });

  it("throws when the payload is not an array", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ oops: true }), { status: 200 })),
    );

    await expect(loadListings("/bad.json")).rejects.toThrow(/not an array/);
  });
});

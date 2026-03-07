import { describe, expect, it } from "vitest";
import {
  computeMedianPricePerM2ByColonia,
  computePriceHistogram,
  renderColoniaPriceChart,
  renderPriceHistogram,
} from "../charts";
import type { Listing } from "../data";

function makeListing(overrides: Partial<Listing>): Listing {
  return {
    id: "L0001",
    title: "Departamento",
    price_mxn: 2_000_000,
    m2: 100,
    bedrooms: 2,
    type: "departamento",
    colonia: "Roma Norte",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de México",
    lat: 19.42,
    lng: -99.16,
    listed_date: "2025-01-01",
    ...overrides,
  };
}

describe("computePriceHistogram", () => {
  it("returns an empty array for an empty dataset", () => {
    expect(computePriceHistogram([], 10)).toEqual([]);
  });

  it("buckets values into the requested number of equal-width bins", () => {
    const listings = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100].map((p) =>
      makeListing({ price_mxn: p * 1000 }),
    );
    const bins = computePriceHistogram(listings, 5);
    expect(bins).toHaveLength(5);
    expect(bins.reduce((sum, b) => sum + b.count, 0)).toBe(listings.length);
    expect(bins[0].binStart).toBe(0);
    expect(bins[bins.length - 1].binEnd).toBe(100_000);
  });

  it("puts the maximum value in the last bin, not overflowing into a phantom bin", () => {
    const listings = [makeListing({ price_mxn: 1_000_000 }), makeListing({ price_mxn: 2_000_000 })];
    const bins = computePriceHistogram(listings, 4);
    const total = bins.reduce((sum, b) => sum + b.count, 0);
    expect(total).toBe(2);
    expect(bins[3].count).toBe(1);
  });

  it("collapses to a single bin when every price is identical", () => {
    const listings = [makeListing({ price_mxn: 1_500_000 }), makeListing({ price_mxn: 1_500_000 })];
    const bins = computePriceHistogram(listings, 10);
    expect(bins).toEqual([{ binStart: 1_500_000, binEnd: 1_500_000, count: 2 }]);
  });
});

describe("computeMedianPricePerM2ByColonia", () => {
  it("computes the median price per m2 within each colonia", () => {
    const listings = [
      makeListing({ colonia: "Roma Norte", municipio: "Cuauhtémoc", price_mxn: 1_000_000, m2: 100 }), // 10000/m2
      makeListing({ colonia: "Roma Norte", municipio: "Cuauhtémoc", price_mxn: 3_000_000, m2: 100 }), // 30000/m2
      makeListing({ colonia: "Roma Norte", municipio: "Cuauhtémoc", price_mxn: 2_000_000, m2: 100 }), // 20000/m2
      makeListing({ colonia: "Iztapalapa Centro", municipio: "Iztapalapa", price_mxn: 500_000, m2: 100 }), // 5000/m2
    ];
    const stats = computeMedianPricePerM2ByColonia(listings, 20);
    const roma = stats.find((s) => s.colonia === "Roma Norte");
    expect(roma?.medianPricePerM2).toBe(20_000);
    expect(roma?.count).toBe(3);
    expect(roma?.municipio).toBe("Cuauhtémoc");
  });

  it("sorts descending by median price per m2 and caps at topN", () => {
    const listings = Array.from({ length: 25 }, (_, i) =>
      makeListing({
        colonia: `Colonia ${i}`,
        municipio: "Municipio X",
        price_mxn: (i + 1) * 100_000,
        m2: 100,
      }),
    );
    const stats = computeMedianPricePerM2ByColonia(listings, 20);
    expect(stats).toHaveLength(20);
    expect(stats[0].colonia).toBe("Colonia 24");
    expect(stats[0].medianPricePerM2).toBeGreaterThan(stats[stats.length - 1].medianPricePerM2);
  });

  it("skips listings with non-positive m2 to avoid infinite price/m2", () => {
    const listings = [
      makeListing({ colonia: "Terreno raro", m2: 0, price_mxn: 1_000_000 }),
      makeListing({ colonia: "Terreno raro", m2: 100, price_mxn: 1_000_000 }),
    ];
    const stats = computeMedianPricePerM2ByColonia(listings, 20);
    const row = stats.find((s) => s.colonia === "Terreno raro");
    expect(row?.count).toBe(1);
  });

  it("returns an empty array for an empty dataset", () => {
    expect(computeMedianPricePerM2ByColonia([], 20)).toEqual([]);
  });
});

describe("renderPriceHistogram", () => {
  it("renders an svg with one bar per bin into the container", () => {
    const container = document.createElement("div");
    const listings = Array.from({ length: 12 }, (_, i) => makeListing({ price_mxn: i * 100_000 }));
    renderPriceHistogram(container, listings, 6);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(container.querySelectorAll("rect.bar")).toHaveLength(6);
  });

  it("shows a message instead of an svg for an empty dataset", () => {
    const container = document.createElement("div");
    renderPriceHistogram(container, [], 6);
    expect(container.querySelector("svg")).toBeNull();
    expect(container.textContent).toMatch(/sin datos/i);
  });
});

describe("renderColoniaPriceChart", () => {
  it("renders one bar per colonia row, capped at topN", () => {
    const container = document.createElement("div");
    const listings = Array.from({ length: 25 }, (_, i) =>
      makeListing({ colonia: `Colonia ${i}`, price_mxn: (i + 1) * 100_000, m2: 100 }),
    );
    renderColoniaPriceChart(container, listings, 10);
    expect(container.querySelectorAll("rect.bar")).toHaveLength(10);
  });
});

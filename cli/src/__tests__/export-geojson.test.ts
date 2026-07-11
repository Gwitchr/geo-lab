import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { buildFixtureDb, FIXTURE_ROWS } from "./fixtures/fixtureDb.js";
import type { ListingsDatabase } from "../db.js";
import { runExportGeoJson } from "../commands/export-geojson.js";

describe("runExportGeoJson against the fixture db", () => {
  let db: ListingsDatabase;
  beforeEach(() => {
    db = buildFixtureDb();
  });
  afterEach(() => {
    db.close();
  });

  it("returns one Feature per row with a Point geometry", () => {
    const collection = runExportGeoJson(db);
    expect(collection.type).toBe("FeatureCollection");
    expect(collection.features).toHaveLength(FIXTURE_ROWS.length);
    for (const feature of collection.features) {
      expect(feature.type).toBe("Feature");
      expect(feature.geometry.type).toBe("Point");
      expect(feature.geometry.coordinates).toHaveLength(2);
    }
  });

  it("coordinates are [lng, lat], not [lat, lng]", () => {
    const collection = runExportGeoJson(db);
    const l0001 = collection.features.find((f) => f.properties.id === "L0001")!;
    const row = FIXTURE_ROWS.find((r) => r.id === "L0001")!;
    expect(l0001.geometry.coordinates).toEqual([row.lng, row.lat]);
  });

  it("applies the same filter language as query/export", () => {
    const collection = runExportGeoJson(db, { filter: "type=terreno" });
    expect(collection.features.map((f) => f.properties.id).sort()).toEqual(["L0003", "L0008"]);
  });

  it("properties carry the listing's non-geometry fields", () => {
    const collection = runExportGeoJson(db, { filter: "colonia:roma norte" });
    const feature = collection.features[0]!;
    expect(feature.properties).toMatchObject({
      id: expect.any(String),
      title: expect.any(String),
      price_mxn: expect.any(Number),
      colonia: "Roma Norte",
    });
    expect(feature.properties).not.toHaveProperty("lat");
    expect(feature.properties).not.toHaveProperty("lng");
  });
});

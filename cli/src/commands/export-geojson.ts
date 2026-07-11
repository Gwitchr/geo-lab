import type { ListingsDatabase } from "../db.js";
import { compileFilter } from "../parser/eval.js";

export interface ExportGeoJsonOptions {
  filter?: string;
}

export interface GeoJsonFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: Record<string, unknown>;
}

export interface GeoJsonFeatureCollection {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

interface GeoRow {
  id: string;
  title: string;
  price_mxn: number;
  m2: number;
  bedrooms: number;
  type: string;
  colonia: string;
  municipio: string;
  lat: number;
  lng: number;
}

// Sketch for a `geoq export --format geojson` mode -- useful for pulling a
// filtered slice straight into QGIS/geojson.io instead of round-tripping
// through the web app. Not wired into cli.ts yet; column set is fixed for
// now, no --columns support.
export function runExportGeoJson(
  db: ListingsDatabase,
  options: ExportGeoJsonOptions = {},
): GeoJsonFeatureCollection {
  let whereSql = "";
  let params: readonly unknown[] = [];
  if (options.filter !== undefined && options.filter.trim() !== "") {
    const compiled = compileFilter(options.filter);
    whereSql = ` WHERE ${compiled.sql}`;
    params = compiled.params;
  }

  const sql = `SELECT id, title, price_mxn, m2, bedrooms, type, colonia, municipio, lat, lng FROM listings${whereSql} ORDER BY listed_date DESC`;
  const rows = db.prepare(sql).all(...params) as GeoRow[];

  const features: GeoJsonFeature[] = rows.map((row) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [row.lng, row.lat] },
    properties: {
      id: row.id,
      title: row.title,
      price_mxn: row.price_mxn,
      m2: row.m2,
      bedrooms: row.bedrooms,
      type: row.type,
      colonia: row.colonia,
      municipio: row.municipio,
    },
  }));

  return { type: "FeatureCollection", features };
}

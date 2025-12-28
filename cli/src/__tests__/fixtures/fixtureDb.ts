import Database from "better-sqlite3";
import type { ListingsDatabase } from "../../db.js";
import type { ListingRow } from "../../types.js";

/**
 * A small, hand-picked fixture: real CDMX colonia/municipio names
 * (including accented ones), a spread of prices/types, and a couple of
 * near-identical rows so filter combinations have something interesting
 * to select. Deliberately not touching data/ - this is an in-memory db
 * built fresh for every test run.
 */
export const FIXTURE_ROWS: ListingRow[] = [
  {
    id: "L0001",
    title: "Depa remodelado en Roma Norte",
    description: "Precioso departamento a unas cuadras del metro, URGE VENDER",
    price_mxn: 2_450_000,
    m2: 65,
    bedrooms: 2,
    type: "departamento",
    colonia: "Roma Norte",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de Mexico",
    lat: 19.4179,
    lng: -99.1626,
    listed_date: "2024-01-15",
    source: "gen",
  },
  {
    id: "L0002",
    title: "Casa amplia en Roma Sur",
    description: "Casa con jardin, ideal para familia grande",
    price_mxn: 6_800_000,
    m2: 210,
    bedrooms: 4,
    type: "casa",
    colonia: "Roma Sur",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de Mexico",
    lat: 19.4102,
    lng: -99.157,
    listed_date: "2024-03-02",
    source: "gen",
  },
  {
    id: "L0003",
    title: "Terreno en Xochimilco",
    description: "TERRENO PLANO listo para construir, buena ubicacion",
    price_mxn: 1_900_000,
    m2: 400,
    bedrooms: 0,
    type: "terreno",
    colonia: "San Gregorio Atlapulco",
    municipio: "Xochimilco",
    estado: "Ciudad de Mexico",
    lat: 19.2646,
    lng: -99.1031,
    listed_date: "2023-11-20",
    source: "gen",
  },
  {
    id: "L0004",
    title: "Depa en Cuauhtemoc centro",
    description: "Estudio pequenio, buena ubicacion, cerca de todo",
    price_mxn: 1_650_000,
    m2: 38,
    bedrooms: 1,
    type: "departamento",
    colonia: "Cuauhtémoc",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de Mexico",
    lat: 19.4361,
    lng: -99.1497,
    listed_date: "2024-05-10",
    source: "gen",
  },
  {
    id: "L0005",
    title: "Local comercial Alvaro Obregon",
    description: "Local en avenida principal, alto trafico peatonal",
    price_mxn: 3_200_000,
    m2: 90,
    bedrooms: 0,
    type: "local",
    colonia: "San Ángel",
    municipio: "Álvaro Obregón",
    estado: "Ciudad de Mexico",
    lat: 19.3467,
    lng: -99.1899,
    listed_date: "2024-02-08",
    source: "gen",
  },
  {
    id: "L0006",
    title: "Casa en Coyoacan con estudio",
    description: "Casa colonial remodelada, acabados de lujo",
    price_mxn: 9_500_000,
    m2: 320,
    bedrooms: 5,
    type: "casa",
    colonia: "Del Carmen",
    municipio: "Coyoacán",
    estado: "Ciudad de Mexico",
    lat: 19.3467,
    lng: -99.1618,
    listed_date: "2023-09-12",
    source: "gen",
  },
  {
    id: "L0007",
    title: "Depa chico en Roma Norte",
    description: "Depa loft, ideal para inversion, RENTA GARANTIZADA",
    price_mxn: 2_350_000,
    m2: 42,
    bedrooms: 1,
    type: "departamento",
    colonia: "Roma Norte",
    municipio: "Cuauhtémoc",
    estado: "Ciudad de Mexico",
    lat: 19.4188,
    lng: -99.1631,
    listed_date: "2024-06-01",
    source: "gen",
  },
  {
    id: "L0008",
    title: "Terreno campestre Xochimilco",
    description: "Terreno con canal, uso mixto, escrituras en regla",
    price_mxn: 2_750_000,
    m2: 600,
    bedrooms: 0,
    type: "terreno",
    colonia: "Santa Cruz Xochitepec",
    municipio: "Xochimilco",
    estado: "Ciudad de Mexico",
    lat: 19.2418,
    lng: -99.1187,
    listed_date: "2024-04-22",
    source: "gen",
  },
];

function seedListings(db: ListingsDatabase): void {
  db.exec(`
    CREATE TABLE listings (
      id TEXT PRIMARY KEY,
      title TEXT,
      description TEXT,
      price_mxn INTEGER,
      m2 INTEGER,
      bedrooms INTEGER,
      type TEXT,
      colonia TEXT,
      municipio TEXT,
      estado TEXT,
      lat REAL,
      lng REAL,
      listed_date TEXT,
      source TEXT
    );
  `);

  const insert = db.prepare(`
    INSERT INTO listings (id, title, description, price_mxn, m2, bedrooms, type, colonia, municipio, estado, lat, lng, listed_date, source)
    VALUES (@id, @title, @description, @price_mxn, @m2, @bedrooms, @type, @colonia, @municipio, @estado, @lat, @lng, @listed_date, @source)
  `);
  const insertAll = db.transaction((rows: ListingRow[]) => {
    for (const row of rows) insert.run(row);
  });
  insertAll(FIXTURE_ROWS);
}

/** In-memory fixture db, used by unit tests that call command functions directly. */
export function buildFixtureDb(): ListingsDatabase {
  const db = new Database(":memory:");
  seedListings(db);
  return db;
}

/** File-backed fixture db, used by tests that exercise the CLI's --db path handling. */
export function buildFixtureDbFile(filePath: string): ListingsDatabase {
  const db = new Database(filePath);
  seedListings(db);
  return db;
}

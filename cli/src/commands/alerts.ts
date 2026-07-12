// Sketch for the "price alerts" board item: save a filter expression, and on
// a later run, report only the listings that are new since the last check.
//
// TODO: figure out where saved alerts live -- a JSON file next to db.sqlite
// is probably fine (~/.geoq/alerts.json?) rather than a new sqlite table,
// this doesn't need to be queryable.
// TODO: "new since last check" needs a persisted cursor per alert (probably
// just the newest listed_date + id seen last run) -- not started.
// TODO: decide the report format (stdout table, like `query`? webhook?).
// Not wired into cli.ts yet.

export interface Alert {
  name: string;
  filter: string;
  createdAt: string;
}

export interface AlertsStore {
  alerts: Alert[];
}

export function createAlert(_name: string, _filter: string): Alert {
  throw new Error("not implemented");
}

export function runAlertsCheck(_store: AlertsStore): never {
  throw new Error("not implemented");
}

// Storage sketch, not wired up: one JSON file, alerts keyed by name.
export const ALERTS_FILE_NAME = "alerts.json";

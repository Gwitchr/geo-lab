/** Render rows as a simple fixed-width text table (no dependency needed). */
export function formatTable(rows: readonly Record<string, unknown>[], columns: readonly string[]): string {
  if (rows.length === 0) return "(no rows)";

  const cellText = (value: unknown): string => (value === null || value === undefined ? "" : String(value));

  const widths = columns.map((c) =>
    Math.max(c.length, ...rows.map((r) => cellText(r[c]).length)),
  );

  const line = (values: readonly string[]): string =>
    values.map((v, i) => v.padEnd(widths[i] as number)).join("  ");

  const header = line(columns);
  const separator = widths.map((w) => "-".repeat(w)).join("  ");
  const body = rows.map((r) => line(columns.map((c) => cellText(r[c])))).join("\n");

  return [header, separator, body].join("\n");
}

/** Format a number with thousands separators; returns "-" for null/undefined/NaN. */
export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

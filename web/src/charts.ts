import type { Listing } from "./data";

export interface HistogramBin {
  binStart: number;
  binEnd: number;
  count: number;
}

/**
 * Buckets price_mxn into `bins` equal-width buckets across the min/max of the
 * dataset. Returns an empty array for an empty dataset. The final bin's
 * `binEnd` is inclusive of the maximum value.
 */
export function computePriceHistogram(listings: Listing[], bins = 10): HistogramBin[] {
  if (listings.length === 0 || bins <= 0) return [];
  const prices = listings.map((l) => l.price_mxn);
  const min = Math.min(...prices);
  const max = Math.max(...prices);

  if (min === max) {
    return [{ binStart: min, binEnd: max, count: listings.length }];
  }

  const width = (max - min) / bins;
  const buckets: HistogramBin[] = Array.from({ length: bins }, (_, i) => ({
    binStart: min + i * width,
    binEnd: min + (i + 1) * width,
    count: 0,
  }));

  for (const price of prices) {
    const idx = Math.min(bins - 1, Math.floor((price - min) / width));
    buckets[idx].count += 1;
  }

  return buckets;
}

export interface ColoniaPriceStat {
  colonia: string;
  municipio: string;
  medianPricePerM2: number;
  count: number;
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
}

/**
 * Groups listings by colonia, computes the median price per m2 within each
 * group (skipping listings with m2 <= 0), and returns the top N colonias by
 * that median, descending. `municipio` on each row is the most common
 * municipio seen for that colonia in the input (colonia names can repeat
 * across municipios).
 */
export function computeMedianPricePerM2ByColonia(listings: Listing[], topN = 20): ColoniaPriceStat[] {
  const groups = new Map<string, { pricesPerM2: number[]; municipios: Map<string, number> }>();

  for (const listing of listings) {
    if (listing.m2 <= 0) continue;
    const key = listing.colonia;
    let group = groups.get(key);
    if (!group) {
      group = { pricesPerM2: [], municipios: new Map() };
      groups.set(key, group);
    }
    group.pricesPerM2.push(listing.price_mxn / listing.m2);
    group.municipios.set(listing.municipio, (group.municipios.get(listing.municipio) ?? 0) + 1);
  }

  const stats: ColoniaPriceStat[] = [];
  for (const [colonia, group] of groups) {
    const topMunicipio = [...group.municipios.entries()].sort((a, b) => b[1] - a[1])[0][0];
    stats.push({
      colonia,
      municipio: topMunicipio,
      medianPricePerM2: median(group.pricesPerM2),
      count: group.pricesPerM2.length,
    });
  }

  stats.sort((a, b) => b.medianPricePerM2 - a.medianPricePerM2);
  return stats.slice(0, topN);
}

const SVG_NS = "http://www.w3.org/2000/svg";

function svgEl<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attrs: Record<string, string | number> = {},
): SVGElementTagNameMap[K] {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs)) {
    el.setAttribute(key, String(value));
  }
  return el;
}

function formatMxnShort(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${Math.round(value / 1000)}k`;
  return String(Math.round(value));
}

/** Renders a bar-chart histogram of listing prices into `container`. */
export function renderPriceHistogram(container: HTMLElement, listings: Listing[], bins = 10): void {
  container.innerHTML = "";
  const data = computePriceHistogram(listings, bins);

  if (data.length === 0) {
    container.textContent = "Sin datos para graficar.";
    return;
  }

  const width = 640;
  const height = 260;
  const margin = { top: 16, right: 12, bottom: 44, left: 44 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const maxCount = Math.max(...data.map((d) => d.count), 1);
  const barGap = 4;
  const barWidth = plotW / data.length - barGap;

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width: "100%",
    role: "img",
    "aria-label": "Histograma de precios",
  });

  const plot = svgEl("g", { transform: `translate(${margin.left},${margin.top})` });

  data.forEach((bin, i) => {
    const barHeight = (bin.count / maxCount) * plotH;
    const x = i * (barWidth + barGap);
    const y = plotH - barHeight;

    const rect = svgEl("rect", {
      x,
      y,
      width: Math.max(barWidth, 1),
      height: barHeight,
      class: "bar",
    });
    const title = svgEl("title");
    title.textContent = `${formatMxnShort(bin.binStart)} - ${formatMxnShort(bin.binEnd)}: ${bin.count} propiedades`;
    rect.appendChild(title);
    plot.appendChild(rect);

    if (i % Math.ceil(data.length / 6 || 1) === 0) {
      const label = svgEl("text", {
        x: x + barWidth / 2,
        y: plotH + 16,
        "text-anchor": "middle",
        class: "axis-label",
      });
      label.textContent = formatMxnShort(bin.binStart);
      plot.appendChild(label);
    }
  });

  const axisTitle = svgEl("text", {
    x: plotW / 2,
    y: plotH + 36,
    "text-anchor": "middle",
    class: "axis-title",
  });
  axisTitle.textContent = "Precio (MXN)";
  plot.appendChild(axisTitle);

  svg.appendChild(plot);
  container.appendChild(svg);
}

/** Renders a horizontal bar chart of median price/m2 by colonia (top N) into `container`. */
export function renderColoniaPriceChart(container: HTMLElement, listings: Listing[], topN = 20): void {
  container.innerHTML = "";
  const data = computeMedianPricePerM2ByColonia(listings, topN);

  if (data.length === 0) {
    container.textContent = "Sin datos para graficar.";
    return;
  }

  const rowHeight = 22;
  const margin = { top: 8, right: 56, bottom: 8, left: 160 };
  const width = 640;
  const plotW = width - margin.left - margin.right;
  const height = data.length * rowHeight + margin.top + margin.bottom;

  const maxVal = Math.max(...data.map((d) => d.medianPricePerM2), 1);

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`,
    width: "100%",
    role: "img",
    "aria-label": "Precio mediano por m2, por colonia",
  });

  data.forEach((row, i) => {
    const y = margin.top + i * rowHeight;
    const barWidth = (row.medianPricePerM2 / maxVal) * plotW;

    const label = svgEl("text", {
      x: margin.left - 8,
      y: y + rowHeight / 2 + 4,
      "text-anchor": "end",
      class: "row-label",
    });
    label.textContent = row.colonia;
    svg.appendChild(label);

    const rect = svgEl("rect", {
      x: margin.left,
      y: y + 2,
      width: Math.max(barWidth, 1),
      height: rowHeight - 6,
      class: "bar",
    });
    const title = svgEl("title");
    title.textContent = `${row.colonia} (${row.municipio}): $${Math.round(row.medianPricePerM2).toLocaleString("es-MX")}/m2, ${row.count} propiedades`;
    rect.appendChild(title);
    svg.appendChild(rect);

    const valueLabel = svgEl("text", {
      x: margin.left + barWidth + 6,
      y: y + rowHeight / 2 + 4,
      class: "value-label",
    });
    valueLabel.textContent = `$${formatMxnShort(row.medianPricePerM2)}`;
    svg.appendChild(valueLabel);
  });

  container.appendChild(svg);
}

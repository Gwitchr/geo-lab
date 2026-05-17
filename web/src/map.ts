import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Listing } from "./data";

const DEFAULT_CENTER: L.LatLngTuple = [19.4326, -99.1332]; // CDMX zocalo
const DEFAULT_ZOOM = 11;
const MAX_MARKERS = 400;

let map: L.Map | null = null;
let markerLayer: L.LayerGroup | null = null;

/**
 * Deterministically samples down to at most `max` listings so the map stays
 * responsive; every listing has an equal-stride chance of appearing rather
 * than always keeping only the head of the array.
 */
export function sampleForMap<T>(listings: T[], max = MAX_MARKERS): T[] {
  if (listings.length <= max) return listings;
  const stride = listings.length / max;
  const sampled: T[] = [];
  for (let i = 0; i < max; i++) {
    sampled.push(listings[Math.floor(i * stride)]);
  }
  return sampled;
}

function formatPrice(mxn: number): string {
  return mxn.toLocaleString("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });
}

function popupHtml(listing: Listing): string {
  const title = document.createElement("div");
  title.className = "popup-title";
  title.textContent = listing.title;

  const meta = document.createElement("div");
  meta.className = "popup-meta";
  meta.textContent = `${listing.colonia}, ${listing.municipio} — ${formatPrice(listing.price_mxn)} — ${listing.m2} m2`;

  const wrap = document.createElement("div");
  wrap.appendChild(title);
  wrap.appendChild(meta);
  return wrap.outerHTML;
}

/**
 * Initializes (or reinitializes) the Leaflet map inside `container` with one
 * marker per listing, capped/sampled at MAX_MARKERS for responsiveness. Safe
 * to call again with a new listing set (e.g. after filtering); it clears and
 * reuses the existing map instance instead of leaking a new one.
 */
export function initMap(container: HTMLElement, listings: Listing[]): L.Map {
  const withCoords = listings.filter(
    (l) => Number.isFinite(l.lat) && Number.isFinite(l.lng) && (l.lat !== 0 || l.lng !== 0),
  );
  const sampled = sampleForMap(withCoords);

  if (!map) {
    map = L.map(container).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);
    markerLayer = L.layerGroup().addTo(map);
  }

  markerLayer?.clearLayers();

  for (const listing of sampled) {
    L.circleMarker([listing.lat, listing.lng], {
      radius: 5,
      weight: 1,
      color: "#2563eb",
      fillColor: "#3b82f6",
      fillOpacity: 0.6,
    })
      .bindPopup(popupHtml(listing))
      .addTo(markerLayer!);
  }

  if (sampled.length > 0) {
    const bounds = L.latLngBounds(sampled.map((l) => [l.lat, l.lng] as L.LatLngTuple));
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 14 });
  }

  // Leaflet needs a nudge to recompute size when its container was hidden
  // (e.g. an inactive tab) at the time of creation.
  setTimeout(() => map?.invalidateSize(), 0);

  return map;
}

export function destroyMap(): void {
  map?.remove();
  map = null;
  markerLayer = null;
}

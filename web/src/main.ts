import "./style.css";
import { loadListings, filterListings, sortListings, type Listing } from "./data";

const TABLE_ROW_CAP = 300;

type SortField = keyof Pick<
  Listing,
  "title" | "price_mxn" | "m2" | "bedrooms" | "type" | "colonia" | "municipio" | "listed_date"
>;

const COLUMNS: { field: SortField; label: string }[] = [
  { field: "title", label: "Título" },
  { field: "price_mxn", label: "Precio (MXN)" },
  { field: "m2", label: "m2" },
  { field: "bedrooms", label: "Recámaras" },
  { field: "type", label: "Tipo" },
  { field: "colonia", label: "Colonia" },
  { field: "municipio", label: "Municipio" },
  { field: "listed_date", label: "Publicado" },
];

const state: {
  all: Listing[];
  query: string;
  sortField: SortField;
  sortDir: "asc" | "desc";
} = {
  all: [],
  query: "",
  sortField: "listed_date",
  sortDir: "desc",
};

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("#app root element not found");

app.innerHTML = `
  <header class="topbar">
    <h1>geo-lab <span class="subtitle">explorador de propiedades</span></h1>
    <input
      id="filter-box"
      type="search"
      placeholder='Filtrar: "roma" o "price&lt;2000000 colonia:roma"'
      aria-label="Filtrar propiedades"
    />
  </header>
  <main>
    <p id="status" class="status" role="status"></p>
    <div class="table-wrap">
      <table id="listings-table">
        <thead><tr></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </main>
`;

const filterBox = app.querySelector<HTMLInputElement>("#filter-box")!;
const statusEl = app.querySelector<HTMLParagraphElement>("#status")!;
const tableHead = app.querySelector<HTMLTableRowElement>("#listings-table thead tr")!;
const tableBody = app.querySelector<HTMLTableSectionElement>("#listings-table tbody")!;

const currencyFmt = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

function renderTableHead(): void {
  tableHead.innerHTML = "";
  for (const col of COLUMNS) {
    const th = document.createElement("th");
    th.textContent = col.label;
    th.dataset.field = col.field;
    th.tabIndex = 0;
    th.setAttribute("role", "button");
    if (col.field === state.sortField) {
      th.classList.add(state.sortDir === "asc" ? "sorted-asc" : "sorted-desc");
    }
    th.addEventListener("click", () => onSortClick(col.field));
    tableHead.appendChild(th);
  }
}

function onSortClick(field: SortField): void {
  if (state.sortField === field) {
    state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
  } else {
    state.sortField = field;
    state.sortDir = "asc";
  }
  render();
}

function getFiltered(): Listing[] {
  return sortListings(filterListings(state.all, state.query), state.sortField, state.sortDir);
}

function renderTable(filtered: Listing[]): void {
  tableBody.innerHTML = "";
  const shown = filtered.slice(0, TABLE_ROW_CAP);

  for (const listing of shown) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(listing.title)}</td>
      <td class="num">${currencyFmt.format(listing.price_mxn)}</td>
      <td class="num">${listing.m2}</td>
      <td class="num">${listing.bedrooms}</td>
      <td>${escapeHtml(listing.type)}</td>
      <td>${escapeHtml(listing.colonia)}</td>
      <td>${escapeHtml(listing.municipio)}</td>
      <td>${escapeHtml(listing.listed_date)}</td>
    `;
    tableBody.appendChild(tr);
  }

  if (filtered.length === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = COLUMNS.length;
    td.className = "empty";
    td.textContent = "Sin resultados para este filtro.";
    tr.appendChild(td);
    tableBody.appendChild(tr);
  }
}

function escapeHtml(value: string): string {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

function renderStatus(filtered: Listing[]): void {
  const total = state.all.length;
  const shownNote = filtered.length > TABLE_ROW_CAP ? ` (mostrando los primeros ${TABLE_ROW_CAP} en la tabla)` : "";
  statusEl.textContent = `${filtered.length} de ${total} propiedades${shownNote}`;
}

function render(): void {
  const filtered = getFiltered();
  renderTableHead();
  renderTable(filtered);
  renderStatus(filtered);
}

let filterDebounce: ReturnType<typeof setTimeout> | undefined;
filterBox.addEventListener("input", () => {
  clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    state.query = filterBox.value;
    render();
  }, 150);
});

async function bootstrap(): Promise<void> {
  statusEl.textContent = "Cargando propiedades…";
  try {
    state.all = await loadListings();
    render();
  } catch (err) {
    statusEl.textContent = `No se pudieron cargar las propiedades: ${(err as Error).message}`;
    console.error(err);
  }
}

void bootstrap();

---
aliases: [Contracts]
tags: [architecture]
---

# Contracts

Five things are relied on **across** component boundaries. Each is owned by one side and consumed by
another, and none of them is enforced by a type system or a build step — a change on one side that
isn't mirrored on the other fails at runtime, or worse, silently. Change these deliberately, and
update every side in the same commit.

If you are about to touch any file named below, read this page first.

---

## 1. The fastgeo import chokepoint — `pipeline/geo_backend.py`

Pipeline code gets `fastgeo` **exclusively** through this module. `dedupe.py:33` and `enrich.py:40`
both do `from geo_backend import fastgeo` and nothing else in `pipeline/*.py` may `import fastgeo`
directly.

```python
if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    from native.fallback import fastgeo_py as fastgeo
else:
    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo
```

- The `try/except ImportError` is what makes the C++ module **optional** — the whole pipeline runs
  with no toolchain. CI's `pipeline-test` job relies on this: it installs only `pytest` and never
  builds the extension.
- **`FASTGEO_FORCE_FALLBACK=1`** forces the pure-Python path even when the compiled module *is*
  installed. It is the mechanism for proving both backends agree, and it must keep working:
  `FASTGEO_FORCE_FALLBACK=1 pytest -q` in `pipeline/` gives `51 passed, 1 skipped`
  (`test_parity.py` skips by design — both sides would be the fallback). The unguarded two-line form
  (`try: import fastgeo / except ImportError: ...`) is *not* sufficient; keep the env check.
- The module also prepends `pipeline/` to `sys.path` so `native.fallback` resolves regardless of CWD
  (`geo_backend.py:32`).
- Consumers that must tolerate `pipeline/native/` being absent entirely should guard with
  `pytest.importorskip("native.fallback.fastgeo_py")`, as `pipeline/tests/test_parity.py` does.

**Invariant:** the parity suite passes both with the compiled module and with
`FASTGEO_FORCE_FALLBACK=1`.

---

## 2. The fastgeo API signatures

Five functions, identical in the C++ module and the pure-Python reference:

```python
point_in_polygon(lat: float, lng: float, ring: list[tuple[float, float]]) -> bool
batch_assign(points: list[Point], polygons: dict[str, Ring]) -> list[str | None]
haversine_matrix(points_a: list[Point], points_b: list[Point]) -> list[list[float]]  # meters
simhash64(text: str) -> int
hamming(a: int, b: int) -> int
```

Changing any signature or any semantic means changing **all five places together**:
`pipeline/native/fastgeo/geo.hpp` + `geo.cpp`, `fastgeo/simhash.hpp` + `simhash.cpp`,
`pipeline/native/bindings.cpp`, `pipeline/native/fallback/fastgeo_py.py`, and
`pipeline/tests/test_parity.py`.

Semantics that are part of the contract, not incidental:

- `ring` is `(lat, lng)` pairs, implicitly closed; `< 3` vertices → `False`.
- **Boundary points are inside**, decided by an exact, epsilon-free cross-product test. Arithmetic
  order is mirrored operation-for-operation across the two implementations for bit-exact parity.
- `batch_assign` resolves ties by **dict insertion order** (the binding walks the `py::dict`
  directly); `None` when no polygon contains the point.
- `haversine_matrix` returns **meters**, mean Earth radius `6371000.0` — the same constant must
  appear in `geo.cpp:11` and `fastgeo_py.py:30`.
- `simhash64` is FNV-1a 64-bit over byte-level tokens; empty/tokenless text hashes to `0`.
- `-ffp-contract=off` in `pipeline/native/CMakeLists.txt` is load-bearing; **never add
  `-ffast-math`**. Full story in [[fastgeo]].

**The pure-Python fallback is the normative spec.** A parity failure is a `fastgeo` bug, never a
reference bug.

---

## 3. The web data shape — `web/public/listings.json`

Produced by `pipeline/export_web.py`, consumed by `web/src/data.ts`'s `Listing` interface. A plain
JSON **array of objects**, **capped at 5,000 rows**, `ORDER BY listed_date DESC`, with
`dup_of IS NOT NULL` excluded.

Exactly 12 fields (`export_web.py:29`, mirrored by `data.ts:3`):

```
id, title, price_mxn, m2, bedrooms, type, colonia, municipio, estado, lat, lng, listed_date
```

Note what is **not** exported: `description`, `source`, `dup_of`, `ageb_id`, `marginacion_grade`,
`marginacion_index`. Adding a field means touching `export_web.py`'s `FIELDS`, `data.ts`'s `Listing`,
and re-running the export — the committed `listings.json` is a build artifact but it is *checked in*,
so the file itself must be regenerated, not just the code.

`MAX_ROWS = 5000` (`export_web.py:27`) is pinned. The web app's `TABLE_ROW_CAP = 300` and
`MAX_MARKERS = 400` ([[web-app]]) are sized against it; raising the export cap means revisiting
whether 400 equal-stride markers and no clustering still hold up.

### Related: `import.meta.env.BASE_URL`

Every asset path in `web/` must go through `import.meta.env.BASE_URL`, because
`web/vite.config.ts` sets `base: "/geo-lab/"` for production builds (GitHub Pages project page) and
`"/"` in dev. `loadListings()` defaults to `` `${import.meta.env.BASE_URL}listings.json` ``. A
hardcoded `/listings.json` works in dev and 404s on Pages — that exact bug was caught and fixed
before the first deploy.

---

## 4. The stats shape — `pipeline/stats.json`

Produced by `pipeline/stats.py`. Aggregates exclude `dup_of IS NOT NULL`.

```json
{
  "generated_at": "<ISO 8601 UTC timestamp>",
  "total_listings": 97508,
  "by_colonia": [{"colonia": "...", "municipio": "...", "count": 0, "median_price_per_m2": 0.0}],
  "histogram":  [{"bucket_max_mxn": 500000, "count": 0}]
}
```

- `by_colonia` is sorted by `(-count, colonia)`; groups with no positive-`m2` rows are omitted.
  Last real run: 97,508 listings, 374 colonias.
- `histogram` buckets are the fixed ladder in `stats.py:33` (500k, 1M, 1.5M, 2M, 3M, 4M, 5M, 7.5M,
  10M, 15M, then a final `None`). **The last bucket's `bucket_max_mxn` is `null`**, meaning
  "everything above the previous bucket" — an explicit null, not a sentinel price. Any consumer must
  handle `null` there.
- Colonia counts are lumpy between CDMX and GDL/MTY (252 curated CDMX colonias vs ~4–17 per municipio
  elsewhere). That's a known shape of the source gazetteers, not a bug — see [[data-notes]].

---

## 5. `geoq`'s `--db` path resolution

`cli/src/db.ts`:

```ts
export const DEFAULT_DB_PATH = "data/db.sqlite";
const resolved = path.resolve(process.cwd(), dbPath);
```

- `--db` (and the default) resolve against **`process.cwd()`** — there is deliberately **no
  repo-root auto-detection**. Run `geoq` from the repo root, or pass `--db` explicitly.
- Hence the README's `cd cli && node dist/index.js query "..." --db ../data/db.sqlite`: the relative
  `../` is doing real work.
- The DB is opened `readonly: true, fileMustExist: true`. `geoq` never writes. A missing file throws
  a message that names both the resolved absolute path and the fix.
- `:memory:` is special-cased (used by the test fixtures) and bypasses resolution entirely.
- `--out` on `geoq export` resolves the same way (`cli/src/cli.ts:204`).

---

## 6. (Implicit) The `listings` schema itself

Not in the original five, but the one everything else hangs off. `pipeline/ingest.py:38` declares it;
these must be kept in sync when a column is added or renamed:

- `cli/src/parser/eval.ts` → `FIELD_COLUMNS` (filter-language field → column)
- `cli/src/types.ts` → `ListingRow` / `ALL_COLUMNS` (drives `--columns` validation and CSV export)
- `cli/src/__tests__/fixtures/fixtureDb.ts` (the in-memory test DB)
- `pipeline/export_web.py` → `FIELDS`, and `web/src/data.ts` → `Listing`, if the field should reach
  the browser
- `docs/filter-language.md`'s field table, if it should be queryable

---

## Invariants that keep all of this true

- `gen_listings.py` output stays byte-identical for the committed seed (`SEED = 20260101`).
- The parity suite passes compiled **and** under `FASTGEO_FORCE_FALLBACK=1`.
- `enrich.py`'s AGEB assignment rate stays **≥ 95%** (currently 99.97%; `enrich.py` warns below).
- The README quickstart works exactly as written from a fresh clone.
- CI's four jobs (`web-test`, `cli-test`, `pipeline-test`, `native-build`) green on main.
- No secrets, no machine-local absolute paths in committed files.
- Data from `gen_listings.py` is **never** labelled as INEGI/CONAPO — only `data/geo/*` is real open
  data ([[data-notes]]).

---

## See also

- ↑ [[ARCHITECTURE]] · [[DATA]]
- [[overview]] · [[pipeline]] · [[fastgeo]] · [[query-engine]] · [[web-app]]
- Reference: [[dev-notes]] · [[data-notes]] · [[filter-language]] · [[ENGINEERING]] · [[TESTING]]
- ↩ [[overview]]

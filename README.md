# geo-lab

A personal "geo lab": start practical — collect and explore property listings —
and grow it into open-data geographic analysis (census areas, marginación
index, business directory) to answer questions like "¿dónde en la CDMX
funcionaría un concierto mediano?" or how marginalization maps onto price per
m². Mexico is the first region, kept region-friendly rather than hardcoded.

Right now this is the listings piece: a Python data pipeline and a
TypeScript web explorer (table + filter). A CLI and the geo-analysis layers
are next.

## Quickstart

`data/db.sqlite` (built artifact, ~100k synthetic listings) is committed, so
the web app works straight off a clone with no Python setup required.

```sh
git clone <this repo> && cd geo-lab
cd web
npm ci
npm run dev      # http://localhost:5173 — table + filter over the listings
```

### Regenerating the data from scratch (optional)

Everything under `data/` is reproducible from `data/gen/gen_listings.py`'s
fixed seed. Only needed if you want to touch the pipeline itself; the
committed `data/db.sqlite` already reflects a full run of this:

```sh
python3 -m venv .venv-pipeline && source .venv-pipeline/bin/activate
pip install pytest              # the only dev dependency; pipeline/*.py is stdlib-only

python3 data/gen/gen_listings.py    # -> data/raw/listings_*.csv (~100k rows)
python3 pipeline/ingest.py          # -> data/db.sqlite

cd pipeline && python3 -m pytest -q
```

## Stack

TypeScript (web), Python 3.11+ (data pipeline). Kept deliberately small:
vitest/pytest for tests, no frameworks beyond what a page needs.

## Roadmap

1. **Listings explorer** (in progress) — collect, clean, dedupe, and browse
   property listings. Web table + filter is up; a CLI query tool is next.
2. **Geo enrichment** — assign listings to their census geography so
   location can be analyzed against real socioeconomic data, not just raw
   lat/lng.
3. **Socio-cultural analysis** — open-ended layer, not scoped yet.

## License

MIT.

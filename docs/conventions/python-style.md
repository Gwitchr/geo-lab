---
aliases: [Python Style]
tags: [convention]
---

# Python Style

Everything under `pipeline/` (plus the generator in `data/gen/`). Python
**3.11+** (`requires-python = ">=3.11"`, and CI's `pipeline-test` job runs
3.11).

## Stdlib only

`pipeline/*.py` is **stdlib + `sqlite3`, nothing else**. `pipeline/pyproject.toml`
declares `dependencies = []`; the sole dev dependency is **pytest**
(`dev = ["pytest>=8.0"]`). The README's setup is literally `pip install pytest`
and nothing more — keep that true.

No pandas, no shapely, no geopandas, no requests. If a script needs geometry it
goes through `fastgeo` (below); if it needs a CSV it uses `csv`; if it needs a
date it uses `datetime`. The one optional native piece (`fastgeo`) is *optional*
by design — the pipeline runs to completion without a C++ toolchain.

## Module conventions

Every module starts with a docstring, then:

```python
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
```

`from __future__ import annotations` is present in every `pipeline/*.py` and in
`data/gen/gen_listings.py`. Paths are `pathlib.Path`, never string
concatenation. Type-annotate function signatures.

## The fastgeo chokepoint

**Never `import fastgeo` directly in pipeline code.** All access goes through
`pipeline/geo_backend.py`, which is the single place that decides which
implementation you get:

```python
if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    from native.fallback import fastgeo_py as fastgeo
else:
    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo
```

`dedupe.py` and `enrich.py` both consume it this way. The
`FASTGEO_FORCE_FALLBACK=1` override exists so both backends can be run against
the same inputs and diffed; it must keep working. See [[fastgeo]] and
[[contracts]].

Exception, deliberate: **`data/gen/gen_listings.py` does not import
`fastgeo`/`geo_backend`** — it carries its own small ray-casting helpers so the
generator doesn't depend on the thing it generates fixtures for.

## Scripts are scripts

Each `pipeline/<script>.py` is runnable as-is from the repo root, and prints a
**short summary line** on completion:

```sh
python3 pipeline/ingest.py       # read 100750 raw rows, kept 100000, dropped 750 {...}
python3 pipeline/enrich.py       # CDMX listings: 50314 / assigned to an AGEB: 50297 (99.97%)
python3 pipeline/export_web.py   # wrote 5000 listings to .../web/public/listings.json
```

Shape to follow: importable functions (`export()`, `run()`, `clean_all()`) plus
an `if __name__ == "__main__":` block that wires `argparse` (`--db`, `--out`,
… with defaults pointing at the real repo paths) and prints the summary. No
logging framework; `print()` is the interface.

## Determinism is a hard requirement

`data/gen/gen_listings.py` is driven by a single `random.Random(SEED)` with
`SEED = 20260101`. **Regenerating must stay byte-identical**:

```sh
python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/a.txt
python3 data/gen/gen_listings.py && sha256sum data/raw/*.csv > /tmp/b.txt
diff /tmp/a.txt /tmp/b.txt && echo BYTE IDENTICAL
```

Any change that perturbs the RNG draw order (adding a `rng.random()` call,
reordering a loop) changes every downstream file. That's allowed, but it's a
deliberate act: re-run the pipeline, re-commit `data/db.sqlite` and
`web/public/listings.json`, and note the new baseline numbers. Never seed from
the clock or the environment. See [[data-notes]] and [[pipeline]].

## Tests

pytest, in `pipeline/tests/`, run from `pipeline/` (`testpaths = ["tests"]`):

```sh
cd pipeline && python3 -m pytest -q                            # 64 passed (with fastgeo built)
cd pipeline && FASTGEO_FORCE_FALLBACK=1 python3 -m pytest -q   # 51 passed, 1 skipped
```

Tests that need the compiled module guard with `pytest.importorskip` so
CI's `pipeline-test` job (which never builds the extension) stays green. Details
in [[TESTING]].

---

## See also

- ↑ [[ENGINEERING]] · [[ARCHITECTURE]]
- [[typescript-style]] · [[cpp-native]] · [[styling-system]] · [[git-and-pr]]
- ↩ [[Home]]

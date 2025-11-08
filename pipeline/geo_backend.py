"""Fastgeo chokepoint, centralized.

dedupe.py and enrich.py both need fastgeo (simhash64/hamming for text
near-duplicate detection, point_in_polygon for AGEB assignment); this module
is the single place that resolves which implementation they get, per
BRIEF.md's pinned interface:

    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo

plus the FASTGEO_FORCE_FALLBACK=1 env override for debugging / verifying both
backends agree. pipeline/native/ (the C++17 extension and the pure-python
fallback it must match) is owned and built separately; this module only
imports from it, never modifies it.

If pipeline/native/ itself doesn't exist yet (e.g. mid-build in a parallel
worktree), both branches raise ModuleNotFoundError and importing this module
fails loudly -- callers that need to tolerate that (this package's own
pytest suite) should guard with
``pytest.importorskip("native.fallback.fastgeo_py")`` before importing
anything that imports this module, the same pattern
pipeline/tests/test_parity.py already uses.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PIPELINE_DIR = Path(__file__).resolve().parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

if os.environ.get("FASTGEO_FORCE_FALLBACK") == "1":
    from native.fallback import fastgeo_py as fastgeo
else:
    try:
        import fastgeo
    except ImportError:
        from native.fallback import fastgeo_py as fastgeo

__all__ = ["fastgeo"]

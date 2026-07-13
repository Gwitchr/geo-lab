---
aliases: [0003 -ffp-contract=off for parity]
tags: [adr]
---

# 0003, Compile fastgeo with `-ffp-contract=off`

## Status

accepted

## Context

[[0002-cpp-fastgeo-via-pybind11|ADR 0002]] made bit-exact agreement between the
C++ module and the Python reference a hard requirement. It broke, sparsely and
confusingly.

`-O3` on Apple Clang (arm64, native FMA hardware) fuses multiply-add/subtract
chains into a single FMA instruction by default. Two such chains sit at the
heart of `point_in_polygon`: the boundary cross-product, and the ray/edge
intersection formula. An FMA rounds **once** where Python's strictly-separate
IEEE754 operations round **twice** — a last-bit difference.

That is invisible almost everywhere. A point well inside or well outside a
polygon does not care about the last bit. A point exactly *on* a polygon
boundary does: the cross-product is compared against `0.0`, and one ulp decides
inside from outside. The parity failures were sparse, appeared only on boundary
points, and took an evening to localize.

The tempting fix is an epsilon tolerance on the boundary test. It does not
work — an epsilon does not remove the cross-language disagreement, it just
relocates it to the epsilon boundary, where two implementations can still land
on opposite sides of `|x| < eps`.

## Decision

Disable FP contraction. `pipeline/native/CMakeLists.txt`:

```cmake
target_compile_options(fastgeo PRIVATE
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-O3 -Wall -Wextra -ffp-contract=off>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /W4>
)
```

Boundary semantics stay exact and epsilon-free: cross-product `== 0.0` plus a
bbox test. A ring's own vertices are algebraically inside in both
implementations.

## Consequences

The flag is **load-bearing**, and it does not look it — exactly the kind of
thing a cleanup pass deletes. Hence the comment above it in `CMakeLists.txt`
and this ADR.

- **Never add `-ffast-math`** or any flag that re-enables contraction. If a
  compiler flag changes, re-run `pipeline/tests/test_parity.py` — including its
  boundary cases (every vertex, every edge midpoint, a random interpolation
  point per edge).
- We give up whatever FMA would have won on the hot loop. Never measured;
  irrelevant next to the ~113x the C++ path already buys.
- **MSVC needs no equivalent flag** — it does not contract by default — but that
  path is **unverified end-to-end**: no Windows toolchain here, no Windows
  runner in CI. It is an assumption, not a result.

---

## See also

- ↑ [[Decisions Index]] · [[ENGINEERING]] · [[ARCHITECTURE]]
- [[fastgeo]] · [[TESTING]] · [[contracts]] · [[dev-notes]]
- ↩ [[Home]]

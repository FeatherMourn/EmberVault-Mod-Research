# ArchitectVoxel (offline)

This package is deliberately independent of Enshrouded, EML, native DLLs,
process handles, and bridge commands. It provides deterministic occupancy
generators, Lua-compatible LSB-first payload packing, and bounded tile planning.

Run from the repository root:

```powershell
$env:PYTHONPATH = 'tools/ArchitectVoxel'
python -m unittest discover -s tools/ArchitectVoxel -p 'test_*.py'
python tools/ArchitectVoxel/generate_reports.py
```

The six baseline predicates and their dimensions are copied as behavior, not
as implementation code: hollow square (8x1x8), filled circle (8x1x8), ring
(8x1x8), sphere (4x4x4), filled cylinder (4x4x4), and hollow cube (4x4x4).
The generated reports explicitly distinguish deterministic local output from
an exact payload export supplied by the game/mod.

`chunk_planner.py` partitions a bounded occupancy set into complete or clipped
8x8x8 tiles, retains empty tiles, and emits local coordinates plus packed
payloads. It performs no allocation or resource/runtime integration beyond
ordinary Python data structures.

Generators accept arbitrary radii, centered even/odd dimensions, hollow
thickness, cylinder axis (`x`, `y`, or `z`), and an optional centered cylinder
height.

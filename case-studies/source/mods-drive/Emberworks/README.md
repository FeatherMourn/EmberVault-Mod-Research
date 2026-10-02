# Emberworks Modular Construction Ecosystem

Independent Enshrouded construction mods managed later by Control Center.
This repository intentionally does not modify or import the Control Center.

## Packages

- `construction_sdk` — shared data contracts and offline operations.
- `blueprint_library` — blueprint storage, validation, search, and revisions.
- `worldwright` — WorldEdit-style selection and transformations.
- `zooping` — procedural walls, floors, columns, bridges, and repeats.
- `builders_wand` — row, column, and plane construction plans.
- `chiselcraft` — 16³ material-aware microstructure editing.
- `framed_architecture` — compatible shapes with inherited parent appearance.
- `restoration` — difference analysis and reversible repair planning.
- `kinetic_works` — belt layouts, network simulation, ratios, and stress checks.

The first milestone is offline/simulated construction. Runtime placement is
disabled until Enshrouded-specific probes verify safe readback and persistence.

## Current capability boundary

All nine modules are implemented, packaged, and tested against the shared
offline construction contracts. Worldwright, Zooping, Builder's Wand,
Chiselcraft, Framed Architecture, Restoration Works, and Kinetic Works can
exchange the shared `Blueprint` format and use simulated undo/redo workflows.

The SDK includes `UnavailableRuntimeAdapter` and
`RuntimeReport.require_verified()` so a future live integration fails clearly
when runtime evidence is absent. The current EML build exposes asset/resource
operations but does not expose verified world, player, entity, or construction
actions. Live capture, placement, copy/paste, and multiplayer behavior remain
explicitly unverified.

See `RUNTIME_FEASIBILITY.md` and `COMPLETION_AUDIT.json` for the evidence record.

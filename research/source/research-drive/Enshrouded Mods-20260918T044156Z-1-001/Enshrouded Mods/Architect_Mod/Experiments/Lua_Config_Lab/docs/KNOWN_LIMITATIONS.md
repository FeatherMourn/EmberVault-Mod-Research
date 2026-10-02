# Known limitations (MVP / v1)

## Scope

This is a **startup configuration tool only**. The following are explicitly out
of scope for v1:

* live editing while Enshrouded is running
* memory scanning, AOB patches, DLL injection, native hooks, hot reload
* ECS runtime editing
* arbitrary Lua console / arbitrary Lua expression execution from profile data
* world/save mutation, multiplayer authority
* automatic KFC modification
* texture/model/audio binary editing
* array insertion/deletion (see below)
* automatic creation of unknown resource types
* automatic replacement of Architect Current

## Schema / data model

* **Resource roots vs embedded classes** — only the 131 KFC root families are
  shown in normal mode as independently patchable resources. Embedded/reflected
  classes appear when traversing fields; the tool does not claim they are
  independently available through `get_resources_by_type(...)`.

* **"757 unique inline/nested classes"** — the project brief lists ~757 as a
  regression expectation. This tool's reachable-nested metric reports **710**
  under its chosen definition (classes reachable transitively from root fields,
  excluding the roots themselves, including reference-only reachable classes).
  The precise definition of "inline/nested" was not fixed by the evidence, so
  this is treated as an approximate, non-permanent figure.

* **Boxed structs** — some reflected structs wrap a single primitive in a
  `.value` field (e.g. `keen.HashKey32 { value u32 }`, `keen.Time { value i64 }`).
  The field tree exposes these as nested classes; select the `.value` leaf to
  edit the scalar. The tool does not auto-unwrap.

## Editable data types

* Supported: booleans, signed/unsigned integers, floats, strings, enums,
  GUIDs, object references, and primitive fields inside nested structs.
* Arrays: **editing an existing element by index** is supported (e.g. `values[1]`).
  Array insertion/deletion/resizing is deliberately unsupported in v1 (they can
  have extra serialization/runtime implications).
* Bitmasks: read/schema display only; editing marked Advanced/Unsupported.
* `Variant<T>`: structure display only; mutation is disabled (fail closed).

## Validation

Invalid values are rejected, never silently clamped. Optional clamp/truncate
behavior is a possible later mode.

## Compatibility

Profiles created against a different `types.lua` hash are flagged
`SCHEMA VERSION MISMATCH` and each edit is revalidated
(`UNCHANGED` / `FIELD MOVED` / `FIELD TYPE CHANGED` / `FIELD MISSING` /
`RESOURCE TYPE MISSING`). The tool does not silently regenerate against changed
types.

## Evidence

`SCHEMA-VALIDATED / RUNTIME EFFECT UNPROVEN` is the default evidence label.
Nothing is reported as "working" merely because Lua generated successfully.
Actual in-game behavior must be observed and recorded by the user before any
field is promoted to `PROVEN_STARTUP_EFFECT`.

## Not verified without launching Enshrouded

* The generated Lua was validated structurally and mirrors known-good Architect
  EML usage, but was **not executed in-game** during this build.
* Whether a specific reflected field produces a particular in-game effect is
  unproven until the user runs the baseline test mod.

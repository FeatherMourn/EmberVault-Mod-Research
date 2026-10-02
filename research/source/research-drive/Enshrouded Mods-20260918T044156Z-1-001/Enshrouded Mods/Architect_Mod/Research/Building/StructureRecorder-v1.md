# Structure Recorder v1

Structure Recorder is a capture-only F8 feature. It consumes the existing
semantic `building_place` stream and never submits placement, transform,
inventory, save, or world commands.

## Workflow

Open F8 → Structure → Start Recording, build normally, then Stop Recording and
Save Blueprint. Load Latest reopens a saved `.architect.json` for inspection;
there is intentionally no replay control.

## Logical placement model

The native observer can emit two raw events for one logical placement. Records
are collapsed only when the existing `correlation.candidateLogicalPlacementId`
and session ID are present. Missing correlation is counted as ambiguous rather
than guessed. Distinct logical IDs remain distinct even when all values match.

Each placement preserves raw signed Q32.32 grid position, quaternion, volume bounds, material,
tracking Item ID, owner ID, and evidence references. Relative position is
derived after integer subtraction from the first committed position and is
reported in normalized world units. Bounds translate each placement volume by
its position before unioning; identity rotations are exact and non-identity
corner transforms are marked inferred. `coordinateSystem` documents the
encoding and scale, while raw arrays remain integer/lossless.

New captures expose `rawEvidence` (grid/bit-level values) separately from a
`canonical` placement (normalized coordinates, orientation, and translated
volumes); the legacy `raw` object remains for v0.29 compatibility.

Provenance separates semantic stream rows from building rows and retained
logical placements: `semanticStreamEventsObserved`,
`buildingRawEventsInRecordingWindow`, `pairedBuildingRawEvents`,
`logicalPlacementsRecorded`, `ambiguousBuildingRawEvents`, and
`ignoredNonBuildingEvents`. Start/end raw sequence and source session delimit
the recording window. Snap-family enrichment remains unresolved unless an
explicit catalog relationship is available.

## File format and safety

Files use schema `architect.structure.v1` and game build `1076226`. The Python
model validates required fields, exact-integral legacy float migration, finite
numeric transforms, build metadata, and array lengths before atomic save/load.
Semantic catalog enrichment is optional;
raw IDs are retained when unresolved. Corrupt JSON or partial JSONL tails are
skipped or rejected with a clear status.

This format represents an **Architect Recorded Structure**, not a vanilla Voxel
Blueprint resource. A future replay interface is documented as
`capture_only_no_replay_backend` and is not implemented in v0.29.

The v0.30 Structure Editor consumes this file as immutable source evidence and
creates a separate `architect.placement_plan.v1`; editing a plan does not
rewrite the recording.

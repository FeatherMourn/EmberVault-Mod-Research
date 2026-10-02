# Structure Editor v1 (offline plan-only)

The Structure Editor derives an `architect.placement_plan.v1` from an
immutable `architect.structure.v1` recording. The source recording is never
edited in memory or on disk; **Reset to Source** reconstructs the working
plan from its captured canonical placements.

## Coordinates and transforms

Plans use double-precision human-scale coordinates. Source raw positions
remain signed Q32.32 evidence (`2^32` scale for the validated build path).
Translation and quarter-turn X/Y/Z rotations operate on a chosen pivot
(recording origin, bounds center, selected placement, or manual point). A
rotation composes the delta quaternion with the placement quaternion and
recomputes all eight volume corners for bounds. The internal quaternion order
is conventional XYZW, but non-identity replay semantics are not validated by
game evidence; edited orientations are `DERIVED_EXPERIMENTAL`.

## Plan operations

Plans support translation, rotation, pivot changes, local-origin rebasing,
enable/disable, duplicate/delete, deterministic reorder, material
substitution, bounded undo/redo, and Reset to Source. Material substitutions
retain `originalMaterial` and `plannedMaterial` and require an indexed ID when
a catalog is supplied. Unknown IDs are rejected rather than silently mapped.

Layout Mirror (Experimental) reflects positions around the selected pivot
plane. A reflection has determinant −1 and cannot generally be represented by
a rigid blueprint quaternion, so `mirrorReplayCompatibility` remains
`UNSOLVED` and mirror output is plan/preview-only.

## Compatibility boundary

Every plan reports `backendStatus=offline_plan_only`,
`replayAvailable=false`, and `worldMutationAvailable=false`. Plan statistics
distinguish total/enabled/disabled/derived/source placements and active bounds;
they are not crafting quantities. The optional F8 Plan tab only invokes the
offline Python editor and displays JSON state. It submits no bridge placement
commands and has no game-process access.

Plans include source recording ID, filename, SHA-256, game build, coordinate
metadata, validation severities, and readiness fields so stale source
provenance is detectable. Saved plans also carry a compact immutable
`sourceSnapshot`; this keeps **Reset to Source** deterministic after a plan is
loaded without requiring the original recording file to be reopened.

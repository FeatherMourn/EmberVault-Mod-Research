# Target Resolver — Static Map v1 (build 1076226)

This milestone is an offline reflection and static-evidence pass. It does not
attach to Enshrouded, read process memory, install hooks, or change the native
runtime. The deployed DLL remains byte-identical (SHA-256
`c3aaf673001cbe08c508f703c0d9219836067a7a9818a4a9473d3ba49f89a801`).

## What is proven

The exported `.cache/types.json` contains reflected target-shaped controls. The
most useful candidates are `keen::ecs::ClientCursor` (primary and secondary
transforms, `hoveredVoxelMaterialId`, `previousSelectedEntityId`, placement
volume, and building offset fields), `keen::ecs::ClientCursorInput`
(`selectObjectAction` and cursor transforms), `CursorSelectObjectAction`
(`selectedObjectId`), `TargetEntity` (`targetId`), `TargetPosition`,
`PlayerFocus`, `ClientPlayerFocus`, and `DebugHitResult` (hit position, normal,
direction, angle, and a hit flag). Their field offsets and type indices are
recorded in `bridge/target_resolver_reflection_candidates.json`.

These are metadata facts. A reflected field is not evidence that its object is
live, that a field is authoritative, or that a function can safely be called.

## Pipeline status

No executable data-flow currently connects one of those reflected controls to a
stable pre-placement target publication function. Generic interaction, ray,
hit, focus, and cursor families are therefore candidate families only. Camera
or aim state is an inference from transform-shaped fields. `hoveredVoxelMaterialId`
is a candidate terrain/material lead, not proof of material authority.

The proven placement edge remains downstream:

* `0x3EBB70` — stable `BuildingPlaceEvent` observation helper;
* `0x3E3505` — direct call site;
* `0xCA90E0` — known blueprint cache lookup in the placement path.

Those RVAs observe a selected placement and cannot identify what the cursor
was targeting before selection/commit. Existing snap and commit maps remain
static-only and are not promoted to a target resolver.

## Observer decision

No new observer is justified. The existing BuildingPlaceEvent observer is
placement-frequency and stable, but is explicitly downstream. A per-frame
cursor writer or generic raycast hook would be high-noise and unsupported by a
validated pointer/lifetime path. The static map consequently records
`install: false` for all new candidates and fails closed on unknowns.

## Target Resolver contract implications

`ArchitectTargetObservation` is now an optional, game-independent contract in
`tools/ArchitectCore`. It carries optional semantic fields (kind, item/entity,
material, transform, bounds, resource and project identity) together with
provenance and a bounded confidence value. Missing evidence stays explicit; it
is never converted into a guessed semantic kind.

## Next boundary

The first unresolved boundary is **live target acquisition and publication of a
stable semantic target before placement**. The next safe step is offline
disassembly of consumers/writers for the reflected cursor/select-object fields,
looking for one low-frequency state-change edge and an independently validated
object lifetime. Until that exists, copy, inspect, measure, eyedropper, and
world-edit capabilities remain blocked or offline-only. No in-game test is
requested by this milestone.

See the machine-readable evidence and safety decisions in
`bridge/target_resolver_static_map.json`.

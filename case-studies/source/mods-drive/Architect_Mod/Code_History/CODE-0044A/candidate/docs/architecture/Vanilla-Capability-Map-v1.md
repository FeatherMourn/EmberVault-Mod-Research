# Vanilla Capability Map v1

**Document type: ARCHITECTURE.** Architect is organized around adapters to
existing Enshrouded systems. Each capability independently records static
semantics, runtime read, and runtime write status; resource existence does not
imply writability.

## Adapter model

The adapters are Build, Terrain, Entity, Inventory, Map, Camera, Movement,
Water, World/Scene, and Resource/Data. The complete capability records,
including unavailable and unknown operations, are in
`bridge/vanilla_capability_map.json`.

## Build pipeline (evidence-weighted)

```
selection → selected identity → runtime blueprint/cache → decoded geometry
→ preview/ghost → placement candidate → snap candidates/result → transform
→ material → validation → commit → BuildingPlaceEvent → world state
```

Known anchors include reflected `CreateBuildingItemAction`, client input
offsets, `0x3E79C0` candidate filtering, `0x3E74B0` record normalization,
`0xCA90E0` candidate lookup, and `0x3E2CD0` commit construction. The arrows
from selected identity to decoded geometry and from decoded geometry to the
final commit are not all proven. The v0.31 negative result specifically
rejects the downstream helper argument as geometry authority.

## Adapter contract fields

Every row answers: player need, vanilla host system, Architect value-add,
known evidence, unknowns, KFC resources, runtime evidence, risk, status, and
proof milestone. The machine-readable map declares these fields in
`capabilityRecordContract`; concise rows inherit neutral values from
`recordDefaults` where a capability has no specialized detail. Query and
validation helpers live in `tools/ArchitectCore`.

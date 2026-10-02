# CODE-0010 — CreateBuildingItemAction dispatch (offline static)

Status: `PARTIAL_STATIC`, `OFFLINE_STATIC_ONLY`. The analysis is locked to
Enshrouded revision `1076226`, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
No process was opened and no hook, detour, debugger, executable write, or game
memory write was performed.

## Reflected layouts

The read-only `.cache/types.json` reflection records prove these layouts:

| type/member | offset | status |
|---|---:|---|
| `ClientPlayerInput.data` | `+0x00` | `PROVEN_STATIC_BUILD_1076226` |
| `ClientPlayerInputData.createBuildingItemAction` | `+0x1B0` | `PROVEN_REFLECTION_ONLY` |
| `CreateBuildingItemAction.versionData` | `+0x00` | `PROVEN_STATIC_BUILD_1076226` |
| `CreateBuildingItemAction.selectedIndex` | `+0x04` | `PROVEN_STATIC_BUILD_1076226` |
| `CreateBuildingItemAction.itemId` | `+0x08` | `PROVEN_STATIC_BUILD_1076226` |
| `ServerConsumedPlayerInput.consumedCreateBuildingItemAction` | `+0x30` | `PROVEN_REFLECTION_ONLY` |
| `UiCreateBuildingItemEvent.playerEntityId` | `+0x08` | `PROVEN_STATIC_BUILD_1076226` |
| `UiCreateBuildingItemEvent.selectedIndex` | `+0x0C` | `PROVEN_STATIC_BUILD_1076226` |
| `UiCreateBuildingItemEvent.itemId` | `+0x10` | `PROVEN_STATIC_BUILD_1076226` |

The client action offset is relative to `ClientPlayerInputData`, which is
embedded at `ClientPlayerInput+0x00`; the server offset is a four-byte
`VersionedData` field, not a complete action payload. These are layout facts,
not proof of live owner pointers.

## Executable candidate audit

The earlier build-locked executable scan found 96 functions with generic
`+0/+4/+8` accesses. A bounded sample is preserved in the machine-readable
map, but every candidate is rejected because it lacks a validated
`ClientPlayerInput` action base, a validated server consumed-version owner, a
version compare/change gate, and same-payload selectedIndex/itemId flow.

No action-qualified version-consume function was identified. In particular,
the existing `InventoryTransferAction` anchor does not establish a
`CreateBuildingItemAction` owner, and the nearby `buildingStockCycleAction`
offset `+0xA4` is retained only as a structural control.

## Forward and convergence results

`selectedIndex` and `itemId` remain reflection-only sources. No first
persistent non-stack write was proven. The known placement R8D path and
`0x3E2CD0` frontier have no continuous data-flow edge from this action.
`UiCreateBuildingItemEvent` has a proven reflected layout but no instruction-
level emission path from the action. Persistent selection/preview, snap
contexts, preview transforms, VoxelBlueprint/cache identity, and VoxelModel
ghost state are all `NOT_PROVEN`.

The first unresolved boundary is the action-specific version-consume dispatch
and its PlayerInput/ConsumedPlayerInput owner relationship. Per the branch
stop condition, this work does not return to generic shape scans or propose a
runtime observer. See
`bridge/create_building_item_dispatch_static_map.json` for the complete
evidence and rejection records.

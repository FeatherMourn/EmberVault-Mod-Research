# Semantic Action Observer v0.22.0 — ClientPlayerInput static milestone

This milestone preserves the proven F7/F8, inventory, and placement behavior.
It is an offline/static investigation only; the deployed native runtime is
unchanged and no new hook is enabled.

## Status

| area | status |
|---|---|
| `InventoryTransferAction` consumer | `PROVEN_BUILD_1076226` |
| `ClientPlayerInput` reflected layout | `PROVEN_STATIC_BUILD_1076226` |
| live `ClientPlayerInput` identity | `UNSOLVED` |
| `CreateBuildingItemAction` reflection | `PROVEN_STATIC_BUILD_1076226` |
| isolated create-action consumer | `UNSOLVED` |
| create action through parent input | `EXPERIMENTAL_NOT_AVAILABLE` |
| `BuildingStockCycleAction` | `STATIC_REFLECTION_ONLY` |
| `UiCreateBuildingItemEvent` connection | `UNSOLVED` |
| action item ID → placement tracking ID | `UNSOLVED` |

## Findings

Reflection gives the exact parent shape: `ClientPlayerInput.data` is at
`+0x00`; inside it, InventoryTransferAction is at `+0x000`,
BuildingStockCycleAction at `+0x0A4`, and CreateBuildingItemAction at `+0x1B0`.
The server consumed record has version-only fields at `+0x20`, `+0x30`, and
`+0x40` for those actions.

The proven native inventory consumer instead loads `RSI=[RDX+0x10]` at
`0x37182C` and consumes an action payload at `RSI+0x08`. That chain is real and
build-locked, but no static producer/copy edge establishes that RDX or RSI is
the reflected ClientPlayerInput object. The first unresolved transition is
therefore the `dispatch-context + 0x10` load, not the reflection offsets.

## Safety decision

The v0.22 scanner emits `bridge/client_player_input_static_map.json` from the
on-disk PE, local reflection cache, and existing static map. It performs no
process access, pointer scanning, game-function invocation, memory write, or
detour installation. Because multi-field live validation cannot be performed
from static evidence, the parent observer remains disabled/fail-closed.

The capture analyzer accepts a future bounded parent snapshot schema and
reports create/building-stock fields without asserting ownership or causality.

## Next evidence (not performed)

A later build may consider an observer only after a uniquely identified,
signature-validated producer or parent pointer is found. It must validate the
InventoryTransferAction plus independent `+0x1B0` and `+0x0A4` fields, use a
bounded worker queue, and avoid file I/O on a sensitive hook path. No live test
is requested for this static milestone.


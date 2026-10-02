# ClientPlayerInput Static Map v1

## Scope and safety

This is an offline/static milestone for Enshrouded revision `1076226` with
executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The scanner reads only the on-disk executable, the installed read-only
`.cache/types.json` reflection cache, and the previously generated inventory
static map. It does not attach to Enshrouded, inspect process memory, install a
detour, invoke a game function, or write game data.

## Reflected layout (PROVEN_STATIC_BUILD_1076226)

The exact reflection source is
`H:\SteamLibrary\steamapps\common\Enshrouded\.cache\types.json`.
`keen::ecs::ClientPlayerInput` is a 1392-byte, 8-byte-aligned dynamic ECS
record. Its visible `data` member is a `ClientPlayerInputData` at `+0x00`;
the additional members are hidden input/configuration records.

`ClientPlayerInputData` is 808 bytes, aligned to 8. Relevant embedded actions
are:

| member | offset | reflected type | size |
|---|---:|---|---:|
| `inventoryTransferAction` | `+0x000` | `InventoryTransferAction` | `0x20` |
| `buildingStockCycleAction` | `+0x0A4` | `BuildingStockCycleAction` | `0x14` |
| `createBuildingItemAction` | `+0x1B0` | `CreateBuildingItemAction` | `0x0C` |

The action definitions are also exact reflection records:

* `InventoryTransferAction` (`0x20`): version `+0x00`, source entity
  `+0x04`, target entity `+0x08`, source slot `+0x0C`, target slot `+0x14`,
  type `+0x1C`, flags `+0x1D`, amount `+0x1E`.
* `CreateBuildingItemAction` (`0x0C`): version `+0x00`, selected index
  `+0x04`, item ID `+0x08`.
* `BuildingStockCycleAction` (`0x14`): version `+0x00`, terrain material
  `+0x04`, default blueprint material `+0x08`, roof material `+0x0C`,
  overgrowth material `+0x10`.
* `VersionedData` is four bytes with `version` at `+0x00`.

The `keen::ds::ecs` reflection records repeat the same action/data offsets and
sizes. The reflected wrapper `keen::ds::ecs::ClientPlayerInput` is also 1392
bytes and has `data` at `+0x00`. These are type-layout facts, not live address
proof.

`ServerConsumedPlayerInput` is a separate 216-byte server-only record. Its
version fields include `consumedInventoryTransferAction` at `+0x20`,
`consumedCreateBuildingItemAction` at `+0x30`, and
`consumedBuildingStockCycleAction` at `+0x40`. No live owner is assigned from
these offsets.

## Proven InventoryTransferAction anchor

The existing build-locked analysis identifies a consumer spanning
`0x371810..0x37229F`:

```text
0x37182C  mov rsi,[rdx+0x10]
0x371830  mov r12,rcx
0x37184D  mov rcx,[rdx+0x38]
0x371842  mov eax,[rsi+0x08]
0x371869  mov [rcx+0x20],eax
```

The action-shaped payload is `RSI+0x08` and matches every reflected
`InventoryTransferAction` field. Its source/target slots and amount flow into
the already validated inventory handlers. This is
`PROVEN_BUILD_1076226` evidence for the action consumer, not proof that RSI is
`ClientPlayerInput`.

## Backward data-flow and unresolved transition

The strongest static chain is:

```text
dispatch-context (RDX)
  +0x10 -> RSI (envelope/action area)
  +0x08 -> InventoryTransferAction-shaped payload
  +0x38 -> downstream consumed-record-like object
```

The first unresolved pointer transition is at `0x37182C`, where
`[RDX+0x10]` becomes RSI. No action-specific producer/copy site ties that
dispatch context to `ClientPlayerInput.data` or proves that the payload is
embedded at `candidateBase + 0x00`. The existing static evidence also does not
prove a concrete dispatch edge into `0x371810`.

Consequently there is no promoted `ClientPlayerInput*` candidate. A valid
future candidate must independently satisfy at least:

```text
candidateBase + 0x000 == exact observed InventoryTransferAction
candidateBase + 0x1B0 == coherent CreateBuildingItemAction
candidateBase + 0x0A4 == coherent BuildingStockCycleAction
```

One action-shaped pointer is intentionally insufficient.

## Observer decision

No parent observer, CreateBuildingItemAction observer, or BuildingStockCycle
observer is installed in v0.22. No safe pointer/producer boundary was proven,
and the static-first rule therefore requires a fail-closed result. The
analyzer is schema-ready for a future `client_player_input_snapshot` record,
but it reports such records neutrally and does not promote ownership.

`UiCreateBuildingItemEvent` remains unresolved: its reflected client-only
record is not statically connected to the parent input chain. The relationship
between a create action item ID and `BuildingPlaceEvent.trackingItemId` also
remains unvalidated.


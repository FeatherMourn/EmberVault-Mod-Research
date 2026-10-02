# Architect Toolkit native knowledge base

This file is an evidence ledger for Enshrouded **0.9.1.2 / revision 1076226
(Hotfix #42 family)**. Historical entries are documentation-only; the current
v0.31 milestone is explicitly experimental and may be deployed only for the
disposable test-world procedure documented below.

## Proven placement path

The stable placement observation is `0x280F86 -> call 0x3E2CD0`, followed by
the direct `BuildingPlaceEvent` helper call at `0x3E3505 -> 0x3EBB70`.
The helper's fifth argument is stack-passed at `[rsp+0x20]`; the proven chain
is `0x3E34E1 mov eax,[r12]`, `0x3E34F1 mov [rsp+0x20],eax`, then
`0x3E3505 call 0x3EBB70`. In the enclosing path `0x3E2D47 -> 0xCB4B50`
and `0x3E2D4C mov r12,rax`, so the returned record's first dword becomes the
tracking item ID.

The placement cache lookup at `0xCA90E0` is an open-addressed, power-of-two
table: guard `+0x84`, capacity `+0x40`, occupancy bitmap `+0x38`, uint32 key
array `+0x58`, and qword value array `+0x70`. It masks the key, checks the
bitmap, compares keys, linearly probes, and returns the value-slot record.
Ring registration was proven in prior live work (`1458989991`), but no new
runtime experiment is part of this batch.

The current runtime geometry consumer is approximately
`0x3E40D0..0x3E4838`, with parallel descriptor preparation in `0x3E74B0`.
It resolves a record through `0xCA90E0`, reads dimensions at `+0x04/+0x0C`,
derives a relative payload pointer from `+0x10`, byte length from `+0x14`,
and reads compression at `+0x18`. Final compressed-bit decoding was not
proven by the static pass.

## Rejected or unsafe hook locations

* `0xCB4B50` resolver detour: caused an access violation during boot and is
  permanently disabled.
* Function-entry detour at `0x3E2CD0`: rejected after a trampoline corrupted
  RAX following the original prologue.
* Conditional selector detour around `0x280F86/0x280F8B`: disabled after an
  access violation before a substitution completed.

The direct `BuildingPlaceEvent` observation was the last known stable hook.
No new hook, selector relay, resolver detour, or placement mutation is being
added by this offline batch.

## Native ItemInfo resolver

The Item-ID keyed resolver is structurally an open-addressed hash table as
described above. Functional Ring proof found key `1458989991` and a record
whose first dword matched that ID; this does not establish reflected-resource
pointer identity. The proven lookup path uses a placement state/context field
at `+0xF0`.

## Reflected VoxelBlueprint layouts

Proven reflection offsets:

| Type/field | Offset/status |
| --- | --- |
| `keen::VoxelBlueprintItem.itemId` | `+0x00`, PROVEN |
| `keen::VoxelBlueprintItem.size` | `+0x04`, PROVEN |
| `keen::VoxelBlueprintItem.data` | `+0x10`, PROVEN member relationship |
| `keen::VoxelBlueprintItem.isDataCompressed` | `+0x18`, PROVEN |
| `keen::VoxelBlueprintItemRegistryResource.blueprintItems` | `+0x00`, PROVEN |
| `keen::ds::VoxelBlueprintItem` size | `0x40`, PROVEN |
| ds `itemId/size/data/compressed` | `+0x00/+0x04/+0x10/+0x38`, PROVEN |
| `DsArray<uint8>` data/length/capacity | `+0x00/+0x08/+0x10`, PROVEN |
| `DsArray<VoxelBlueprintItem>` stride | `0x40`, PROVEN |

The non-ds reflected `BlobArray` header semantics and a legitimate live
resource-manager pointer endpoint remain UNKNOWN. The ds copy/clone routines
prove data/length/capacity for the ds representation only. The placement cache
record has a separate, proven relative-offset/length representation.

## Context-to-cache relationship

The recovered static path proves that lookup consumers load a cache from
`RSI + 0xF0` (`0x3E2D30`, `0x3E4154`, `0x3E60CC`, and `0x3E7C92`). It does **not**
prove that the `context` pointer passed to `BuildingPlaceEvent` is the same
object as that RSI base, nor that a fixed context-to-state offset reaches it.
The helper call occurs later in the `0x3E2CD0` path, but the available static
slice has no identity-preserving assignment that establishes aliasing. Similar
runtime values would not be sufficient evidence. A future read-only build may
use the existing stable hook only after a build-validated capture proves that
traversal.

## Placement record formula

For the record returned by `0xCA90E0`, the payload address is proven as:

```
(record + 0x10) + sign_extend(*(int32 *)(record + 0x10))
```

The length is `uint32(record+0x14)` and compression is the byte at `record+0x18`.
The helper returns the record pointer loaded from the hash table's value array,
not the address of that value slot. Expected offline payload signatures are
recorded in `bridge/voxel_blueprint_native_layout.json`.

## VoxelModelResource and decoder status

Static reflection recovery identifies `keen::VoxelModelResource` at descriptor
RVA `0x1B51450`, with member table `0x1708390`: `size` (`uint3`) at `+0x00`,
`data` (`BlobArray<uint8>`) at `+0x0C`, and `isTerrain` at `+0x14`.
The ds variant is descriptor `0x15D7F90`, size `0x40`, with `size +0x00`,
`DsArray<uint8> data +0x10`, and `isTerrain +0x38`. BlobArray pointer/length/
capacity semantics and a native Hammer ghost renderer remain unresolved.

The placement consumers prove payload extraction but not final bit decoding:
`0x3E40D0`, `0x3E74B0`, and `0x3E7C92` carry payload pointer, length, and
compression into downstream routines (`0x3E79C0` among them). Native bit order,
compressed/uncompressed branches, and malformed-payload handling remain UNKNOWN.

## Current unknowns

* final compressed voxel occupancy decoder and its exact call path;
* direct ds-to-runtime resource conversion;
* native loaded `VoxelBlueprintItemRegistryResource*` manager endpoint;
* capacity semantics for the reflected non-ds `BlobArray`;
* whether the placement cache record is the reflected resource object.

## DO NOT HOOK / DO NOT MUTATE

Do not hook `0xCB4B50`, `0xCA5BC0/0xCA90E0`, `0x3E2CD0`, or
`0x280F86/0x280F8B` without a separately reviewed, build-validated design.
Do not write resolver keys, occupancy bitmaps, value slots, ItemInfo records,
context child fields, selector state, or blueprint payloads. The v0.31 carrier
exception is limited to its documented local fifth-argument substitution and
immediate local restoration; all other diagnostic builds remain read-only.
Preserve fingerprint/signature validation and unload restoration in future
native work.

## Semantic Action Observer v0.22 static map

The read-only reflection cache confirms `keen::ecs::ClientPlayerInput` is a
1392-byte record whose `data` member is at `+0x00`; its `ClientPlayerInputData`
embeds `InventoryTransferAction` at `+0x000`, `BuildingStockCycleAction` at
`+0x0A4`, and `CreateBuildingItemAction` at `+0x1B0`. The corresponding
server-consumed version fields are at `+0x20`, `+0x40`, and `+0x30`.

The proven inventory consumer at `0x371810..0x37229F` loads `RSI=[RDX+0x10]`
(`0x37182C`) and consumes an action payload at `RSI+0x08`; `RDX+0x38` feeds a
downstream consumed-record-like object. This does not prove that RDX/RSI is a
reflected `ClientPlayerInput` instance. The first unresolved pointer
transition is `dispatchContext+0x10 -> RSI`, and no parent observer is enabled.
See `bridge/client_player_input_static_map.json` and
`docs/research/ClientPlayerInput-StaticMap-v1.md` for the build-locked
evidence and fail-closed decision.

## Building commit transform context (v0.28, static-only)

The supported-build function `0x3E2CD0..0x3E354E` copies its second argument
(`RDX`) to `R15` at `0x3E2CEF` and placement state (`RCX`) to `RSI` at
`0x3E2CF6`. A bounded pseudo-layout of the incoming R15 structure is recorded
in `bridge/building_commit_transform_static_map.json`; only offsets actually
read by machine code are listed. The event field flow is proven: integerized
position comes from the caller RDX temporary, orientation from its +0x18..+0x24
lanes, volume bounds from the caller R8 temporary, material from `0xCAEC50`,
tracking ID from `[R12+0]`, and owner from placement state `RSI+0x134`.

No observer was installed. Runtime frequency and a safe pre-processing window
for `0x3E2CD0` are not established, so this remains offline evidence only.

## v0.31 single-placement carrier (EXPERIMENTAL)

Build identity: `0.31.0` / `architect-v031-single-placement-carrier-20260915-a` /
`experimental_single_placement_carrier`. The only new behavior is an
explicitly armed, one-shot substitution of the local fifth argument at the
stable `BuildingPlaceEvent` helper entry. The initial gate accepts only ItemId
`950598916` and requires one enabled plan placement plus the supported build and
observer signatures. It waits up to 10 seconds for the first event, then
accepts at most two matching raw events within 250 ms. Any mismatch, timeout,
unexpected caller, or overflow fails closed.

The original helper call receives the substituted local argument and all other
arguments unchanged; the local value is restored immediately after return.
No resolver table, context field, ItemInfo, material, position, orientation,
volume, owner, or selector state is written. World authority is **UNSOLVED**:
the event argument is upstream of the helper body, but only an in-game visual
result can establish that committed geometry follows it. Ordinary `place`
remains observe-only. The rejected resolver/selector detours remain disabled.

### v0.31 authority result (PROVEN/DISPROVEN)

The disposable-world wall-versus-foundation test armed desired ID `950598916`
while the player committed wall ID `948722226`. Both raw events were inside
the waiting window; both received the substituted local argument and both were
restored successfully. The placed geometry remained the wall. Consequently,
local `BuildingPlaceEvent.trackingItemId` substitution authority for geometry
is **DISPROVEN_BUILD_1076226**, while the ability to substitute the forwarded
argument is **PROVEN_BUILD_1076226**. Do not repeat that mutation. The
context `+0x48` child and its duplicate `+0x1C/+0x30` IDs are observation-only
anchors with unresolved type and authority.

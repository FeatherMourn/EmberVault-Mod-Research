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
context child fields, selector state, blueprint payloads, or placement
arguments. The v0.31 carrier exception is historical only and is retired after
the documented negative result; all current and future diagnostic builds are
read-only unless separately approved.
Preserve fingerprint/signature validation and unload restoration in future
native work.

## CODE-0006 snap winner / preview writeback (offline static only)

The post-filter consumer family at `0x3EB810..0x3EB8C3` iterates an accepted
record collection whose count is loaded from `[RDX+0x08]`, storage from `[RDX]`,
and element stride is `0x50` (`0x3EB89F`).  Each accepted element is tested by
`0x99ECF0`, then processed through `0x8CD2C0` and `0x3E5480`; the element field
at `+0x48` is loaded at `0x3EB857`.  No retained score, best index, min/max
comparison, or candidate-to-candidate winner write is present in this bounded
function.  The other family, `0x99F970..0x99FD29`, loads one caller-provided
record from `[RBP+0x1C8]`, reads its fields (`+0x14`, `+0x1C`, `+0x20`,
`+0x28`, `+0x2C`, `+0x34`, `+0x38`, `+0x40`), and performs arithmetic/output
preparation; it likewise contains no collection traversal or winner choice.

Accordingly, winner selection is `NO_WINNER_SELECTION_IN_BOUNDED_PATH` and
persistent preview/commit writeback remains unresolved.  The only observed
candidate output is a stack-local object at `[RSP+0x90]` passed to `0x3E5480`;
its owner and lifetime are callee-dependent.  No static edge was established
from either family to the preview owner, `CreateBuildingItemAction`, or the
placement commit path.  CODE-0006 therefore reports `PARTIAL_STATIC` and keeps
observer installation unauthorized (`OFFLINE_STATIC_ONLY`, no process access,
hooks, writes, or deployment).

## CODE-0005A observer infrastructure (offline/staging only)

CODE-0005A adds an offline whole-instruction relocation planner and synthetic
native transaction/ring harness. The planner hashes site RVA, exact original
bytes, decoded instructions, continuation, and relocation recipe; it never
opens a process or patches an executable image. Ordinary non-RIP-relative
copies are harness-proven. RIP-relative operands and direct relative
CALL/JMP/Jcc remain `UNSUPPORTED_FAIL_CLOSED` because no semantics-preserving
emitter has been reviewed. The staging transaction verifies expected bytes,
rejects duplicate installs, and restores an exact backup only in owned
synthetic buffers.

The diagnostic producer is a fixed 64-event single-producer/single-consumer
scalar ring with drop-newest overflow accounting and no I/O, allocation,
blocking, formatting, or game calls. Generic wrapper ABI/RFLAGS/vector,
unwind, reentrancy, site lifetime, and a production drain host remain
unresolved. The CODE-0005A capability map therefore remains `PARTIAL_HARNESS`,
`infrastructureReadyForSiteRequalification=false`, and
`gameHookInstallAuthorized=false`; CODE-0005 remains
`NO_SAFE_OBSERVER_SITE`. No runtime hook or experiment was installed.

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

## v0.32 upstream placement identity authority research

Build identity: `0.32.0` /
`architect-v032-identity-authority-20260915-a` /
`observe_only_placement_blueprint_authority`. The legacy
`single_placement_carrier_arm` command is recognized but fails closed with
`disprovenForWorldGeometryAuthority`; it cannot arm or alter the local helper
argument. The stable `BuildingPlaceEvent` observer remains installed.

The v0.31 result is recorded as `localTrackingItemArgumentWrite:
PROVEN_MUTABLE_BUILD_1076226`, but
`localTrackingItemArgumentGeometryAuthority:
DISPROVEN_FOR_WORLD_GEOMETRY_AUTHORITY_BUILD_1076226`. Upstream identity,
runtime blueprint authority, and the first producer coupling blueprint
occupancy to commit volume remain `UNSOLVED`. See
`bridge/building_identity_authority_static_map.json` and
`docs/research/BuildingIdentityAuthority-StaticMap-v1.md`.

## CODE-0005E relay safety closure (offline/staging only)

CODE-0005E models bounded eight-slot relay publication with monotonic
generations, per-slot coherence, consume-once matching, and drop/reject on
contention or ambiguity. The matcher requires the existing frame equations,
the `0x280F8B` marker, same-stack allocation identity, guarded buffer reads,
and unchanged generation after reads. Synthetic tests reject stale,
cross-stack, nested, concurrent, zero-candidate, and multi-candidate cases.
Downstream `+0x38/+0x78` values remain stability-unknown. The helper's first
flag-defining compare occurs after the copied relay-entry prologue, giving only
a site-specific conditional RFLAGS contract. Unwind/exception proof and
production drain integration remain unresolved; result is
`PARTIAL_STATIC_OR_HARNESS`, with installation and runtime authorization false.

## CODE-0007 returned-pointer ownership (offline static only)

`0x3E5480` (`0x3E5480..0x3E5604`) calls `0x3ED1A0` at `0x3E5578` with
`RCX=[RDI+0xD8]`, `RDX=[RDI+0xE0]`, `R8B=5`, and `R9D=EBX`. The returned
pointer is copied to `RDX` and written at offsets `+0x00`, `+0x08`, `+0x10`,
`+0x14`, `+0x1C`, `+0x20`, `+0x28`, `+0x2C`, `+0x34`, `+0x38`, and `+0x3C`.

`0x3ED1A0` is split across adjacent `.pdata` chunks
`0x3ED1A0..0x3ED1DB`, `0x3ED1DB..0x3ED296`, and cold failure code
`0x3ED296..0x3ED2B8`. It obtains storage by passing `ownerRoot+0xA10` to
`0x7AEDA0`, checks owner-rooted count/capacity fields `+0xA28/+0xA38`, uses
`+0xA3C` as an element stride, and initializes returned-slot `+0x48/+0x4C`.
The pointer is therefore an owner-rooted container slot, not a proven global or
stack alias; allocator reuse versus allocation is unknown.

In the `0x3EB810` path the owner root is shared across candidate iterations,
while the input pointer at `[RSP+0x90]` is candidate-derived. No post-loop read
of returned records and no instruction-backed edge to preview state,
`0x3E2CD0`, the `[RSI+0xF0/+0x110]` snap state, or
`CreateBuildingItemAction` was found. CODE-0007 remains `PARTIAL_STATIC` with
`PERSISTENCE_UNRESOLVED`; observer installation and current-source designation
remain unauthorized.

## CODE-0008 owner-rooted container family (offline static only)

The four direct callers of `0x3ED1A0` are `0x3E262B`, `0x3E2919`,
`0x3E52BD`, and `0x3E5578`. They pass owner fields `+0xD8/+0xE0`, with
`R8B` constants `1/6/0/5`; this supports a discriminator role but not a
semantic type name. `R9D` is copied to returned slot `+0x48`, with key/index/
generation semantics unresolved.

The helper `0x7AEDA0` is proven to pop a nonzero free-list head at control
block `+0x10`, otherwise append while `+0x30 < +0x28` using base `+0x00` and
stride `+0x2C`, updating counters `+0x18/+0x1C/+0x20`; it returns null on
exhaustion. `0x3EDDE0` is a connected bucket/bookkeeping growth path called
from `0x3ED223`, with owner bucket count `+0xA08`, bucket reset fields
`+0x100/+0x108`, and bookkeeping allocation through `0x263470`.

On the `0x3EB810` path the owner root is shared across candidate iterations,
but returned slots may be reused or appended and no post-loop winner reader is
present. No instruction-backed reader connects this family to preview state,
`0x3E2CD0`, snap cache fields, `CreateBuildingItemAction`, or VoxelBlueprint
identity. CODE-0008 remains `PARTIAL_STATIC` / `PERSISTENCE_UNRESOLVED`; no
runtime observer is authorized.

## CODE-0005B helper-entry contract (offline only)

For build 1076226, `0x8D5CA0` has an exact 12-byte entry span
(`push rdi; sub rsp,0x10; mov r9,[rcx]; mov rdi,rdx`) and continuation
`0x8D5CAC`. Plan identity is
`78f1c9ad4e04328b8b585a891d613e64cfa79103bdc6acf7913f857f558d1641`.
The span uses only the CODE-0005A ordinary-copy class; no game installation is
authorized. Known callers `0x2807C8` and `0x2810A3` pass RCX=R15, RDX=RBP-0x30,
and R8D=0x100; R9 remains unresolved. A/R/B sources are `[r9+0x498]` byte,
`[r9+0x4A0]` word, and `[r9+0x4A2]` word. Output bounds, conditional entry
reads, wrapper ABI/flags/unwind, thread/reentrancy, and production drain remain
unresolved. CODE-0005B remains `PARTIAL_STATIC` with installation disabled.

## CODE-0009 owner-rooted slot dispatcher (offline static only)

Build-locked to revision `1076226`, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
CODE-0009 is an offline-only analysis; it adds no hook, detour, process access,
executable write, or game-memory write. The deployed DLL remains untouched.

`0x3ED1A0` is split across `.pdata` ranges `0x3ED1A0..0x3ED1DB`,
`0x3ED1DB..0x3ED296`, and cold `0x3ED296..0x3ED2B8`. It copies RCX to the
owner root, allocates/reuses from `owner+0xA10` through `0x7AEDA0`, clears the
returned 0x50-byte slot, stores incoming R8B at slot `+0x4C` (`0x3ED260`),
stores incoming R9D at slot `+0x48` (`0x3ED266`), and records the computed
secondary index at `0x3ED27E`. Direct callers pass discriminator constants
1, 6, 0, and 5 at `0x3E262B`, `0x3E2919`, `0x3E52BD`, and `0x3E5578`.

The same family has an anchored consumer/dispatcher at
`0x3E5A60..0x3E5D98`. It walks the secondary range, calls `0x3EE0C0` at
`0x3E5AC2` to resolve `owner+0xA10 + index*[owner+0xA3C]`, reads the slot
discriminator at `+0x4C` (`0x3E5ACA`), and dispatches through the table at
`0x3E5D70`. Every handler receives RCX=owner, RDX=slot, and R8D=`[slot+0x48]`.
Discriminator 5 reaches `0x3E27B0`; that handler reads the produced slot's
fields through `+0x3C`, calls `0x87A2E0`/`0x879D70`, and can emit a new kind-6
slot via `0x3ED1A0`. Its semantic role is unresolved.

`0x7AEDA0` proves free-list reuse or bounded append (control fields
`+0x00,+0x10,+0x18,+0x1C,+0x20,+0x28,+0x2C,+0x30`); exhaustion returns zero.
`0x3EDDE0` grows/drains secondary bucket bookkeeping. A concrete release that
writes a returned slot back to the free-list head was not found, so lifetime is
`MIXED_LIFETIME_UNRESOLVED`.

No instruction-backed convergence from discriminator 5 to preview/ghost state,
snap caches, `0x3E2CD0`, CreateBuildingItemAction, or VoxelBlueprint identity
was proven. CODE-0009 therefore remains `PARTIAL_STATIC`, with the first
unresolved boundary at the helper callees and any later kind-6 consumer. See
`bridge/owner_rooted_slot_dispatch_static_map.json` and
`docs/research/OwnerRootedSlotDispatch-StaticMap-v1.md`.

## CODE-0010 CreateBuildingItemAction dispatch (offline static only)

Build-locked to revision `1076226` and executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The `.cache/types.json` reflection records prove
`ClientPlayerInput.data +0x00`,
`ClientPlayerInputData.createBuildingItemAction +0x1B0`, and action fields
`versionData +0x00`, `selectedIndex +0x04`, `itemId +0x08`.
`ServerConsumedPlayerInput.consumedCreateBuildingItemAction +0x30` is a
four-byte consumed-version field. `UiCreateBuildingItemEvent` is reflected at
`playerEntityId +0x08`, `selectedIndex +0x0C`, and `itemId +0x10`.

These are reflection offsets only; no native owner pointer is assigned. The
build-locked executable scan found generic `+0/+4/+8` shape candidates but no
function that simultaneously proves the PlayerInput action base, the server
consumed-version pair, and same-payload field flow. All such candidates are
explicitly rejected. `selectedIndex`/`itemId` therefore remain reflection-only,
with no proven persistent write, UI-event bridge, preview/selection convergence,
or connection to placement R8D/`0x3E2CD0`.

CODE-0010 is `PARTIAL_STATIC`; the branch is fail-closed and no observer or
detour is authorized. The next distinct boundary is the independently
identified preview/ghost producer path, not another generic action-shape scan.
See `bridge/create_building_item_dispatch_static_map.json` and
`docs/research/CreateBuildingItemDispatch-StaticMap-v1.md`.

## CODE-0011 selection/preview authority convergence sweep (offline static only)

Build-locked to revision `1076226` and executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
This sweep is strictly offline/static: it performs no process access, hook,
detour, executable write, or game-memory write. It is a bounded comparison of
four independently anchored fronts and does not authorize a runtime observer.

Front A (VoxelModel/ghost) is `PARKED_NO_ANCHORED_GHOST_PRODUCER`: the static
resource relationship is visible, but no building-specific VoxelModel or ghost
producer is anchored within the permitted two-hop search. Generic render paths
remain parked. Front B is `STRUCTURAL_OWNER_ONLY`: candidate filter `0x3E79C0`
reads snap state from `[RSI+0xF0]` and `[RSI+0x110]`, with cache lookup at
`0x3E7C92 -> 0xCA90E0`; the accepted collection's owner/caller persistence is
not proven. Front C is `COMMIT_FRONTIER_OWNER_UNRESOLVED`: the direct selector
call `0x280F86 -> 0x3E2CD0` and return `0x280F8B` are anchored, and
`0x280F75` loads `R8D` from `[RBX]`, but no stable semantic source or shared
owner is established. Front D is `RESOURCE_ONLY_CONVERGENCE`: ItemInfo,
VoxelBlueprintItem, and VoxelModel relationships are resource evidence only.

The resulting convergence graph is `NO_CONVERGENCE`. A shared RSI value is
recorded only as a rejected coincidence because no instruction-backed edge
joins the snap, commit, and preview fronts. The proposed CreateBuildingItem
action-to-`R8D` edge is likewise rejected; CODE-0009's owner-rooted slot
dispatcher and CODE-0010's action dispatch remain parked branches. No
candidate owner survives the evidence gates, so the observer decision remains
`install=false`, `installNow=false`, and `gameHookInstallAuthorized=false`.
The machine-readable result is
`bridge/selection_preview_authority_convergence_static_map.json`, with the
research narrative in
`docs/research/SelectionPreviewAuthorityConvergence-StaticMap-v1.md`.

## CODE-0012 blueprint/ghost product-path staging (offline only)

The working-tree `src/mod.lua` contains the accepted Architect-owned resource
path: clone `keen::ItemInfo`; append a bounded, same-dimension
`VoxelBlueprintItem`; clone a private `VoxelModelResource` with preview values
18/0; create its same-GUID `keen::RenderModel` companion; and link the validated
ItemInfo through `ItemRegistryResource.itemRefs`. The source also enforces
`MAX_SAFE_EML_PLACEMENT_BYTES = 8`, so larger nested-array payloads remain
fail-closed. These are source anchors, not permission to invoke EML or mutate
the game in this milestone.

`tools/ArchitectProductPath/product_path_staging.py` is an offline planner for
that path. It emits four deterministic 4x4x4 canaries using two private
patterns: CONTROL (final A/ghost A), GHOST_VARIANT (A/B), FINAL_VARIANT (B/A),
and private-only CROSS_WIRED (A/B). Candidate IDs and UUIDs are explicitly
symbolic staging identities; no asset allocation, registry publication, or
resource write occurs. Missing source anchors produce
`BLOCKED_MISSING_PROVEN_SOURCE`. The manifest is
`bridge/blueprint_ghost_identity_perturbation_manifest.json` and the manual
preview/disposable-world procedure is documented in
`docs/research/BlueprintGhostProductPath-PreviewRunbook-v1.md`.

## CODE-0013 preview-only product-path package (offline preparation)

CODE-0013 adds no native capability and does not load or alter the current mod.
`runtime/staging/ArchitectProductPathPreview.lua` is generated directly from
the CODE-0012 manifest, defaults to `enabled=false`, exposes an explicit
`activate()` entry point, and contains no placement automation. If separately
enabled in a staging mod, it reuses only the source-anchored EML operations:
private ItemInfo/VoxelModel/RenderModel cloning, 4x4x4 eight-byte blueprint
payload copying, and private links after validation. Missing templates, ID
collisions, payload-size violations, or a missing RenderModel companion fail
closed. Runtime preview behavior remains unconfirmed until a user-run preview
test supplies evidence; the deployed DLL and `Architect_Mod/Current` remain
outside this package.

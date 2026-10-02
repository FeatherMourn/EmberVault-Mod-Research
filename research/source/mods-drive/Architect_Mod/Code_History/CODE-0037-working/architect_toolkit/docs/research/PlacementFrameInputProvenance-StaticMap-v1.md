# Placement Frame-Input Provenance — Static Map v1

**Scope:** Enshrouded revision 1076226; executable SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
Static/offline only. No process access, runtime observer, game-memory mutation, executable patch, or deployed-DLL change.

## Parent CODE-0001 frontier

CODE-0001 remains PARTIAL_STATIC: `0x28089E -> 0xCB4B50`, `0x280F75` loads R8D from `[RBX]`, and `0x280F86 -> 0x3E2CD0`. Common owner, action-item write into the placement source, and VoxelBlueprint/cache connection remain unproven. The observer gate remains disabled.

## Containing function and RBP/frame model

Logical chained function range: `0x280790..0x2810E8`. RBP model: **PROVEN_MANUAL_STACK_ANCHOR_NOT_UNWIND_FRAME_REGISTER**. The primary prologue and unwind data show `RBP = entryRSP - 0x76D8`; after the fixed `0x77C8` allocation, current RSP is `RBP-0x100`. Thus `RBP+0x08` is `currentRSP+0x108` and `RBP+0x48` is `currentRSP+0x148`, both inside the local allocation. These are not incoming stack arguments.

Prologue/unwind evidence:

- `0x280790` `push rbp` (`40 55`).
- `0x280792` `push r15` (`41 57`).
- `0x280794` `lea rbp, [rsp - 0x76c8]` (`48 8D AC 24 38 89 FF FF`).
- `0x28079C` `mov eax, 0x77c8` (`B8 C8 77 00 00`).
- `0x2807A1` `call 0x1221710` (`E8 6A 0F FA 00`).
- `0x2807A6` `sub rsp, rax` (`48 2B E0`).

## RBP+0x08 provenance

Classification: **FUNCTION_LOCAL_STACK_SLOT**; normalized as `entryRSP-0x76d0 = currentRSP+0x108`. It aliases `localBuffer+0x38` where the local buffer base is `[RBP-0x30]`. The resolver path loads this qword at `0x280897`, then reads dword `[RCX+0x30]` at `0x28089B` into ECX.
Last field-specific producer: unresolved. CFG may-reaching helper calls: 0x2807B6, 0x2807C8, 0x2810A3. These are possible writes through a target-containing output buffer, not proven field-level stores; no fixed store to this exact field is proven.
First unresolved boundary: 0x28089E reads the field from the function-local buffer, but the exact byte/field producer inside the variable-offset helper output at RBP-0x30 is not statically isolated; caller/dispatcher provenance is not established.

## RBP+0x48 provenance

Classification: **FUNCTION_LOCAL_STACK_SLOT**; normalized as `entryRSP-0x7690 = currentRSP+0x148`. It aliases `localBuffer+0x78`; `0x28088B` loads it into RDX for the resolver call.
Last field-specific producer: unresolved. CFG may-reaching helper calls: 0x2807B6, 0x2807C8, 0x2810A3. These are possible writes through a target-containing output buffer, not proven field-level stores; exact field offset/value source is not isolated.
First unresolved boundary: 0x28089E reads the field from the function-local buffer, but the exact byte/field producer inside the variable-offset helper output at RBP-0x30 is not statically isolated; caller/dispatcher provenance is not established.

## Direct caller traces

No direct relative-call references to the logical function entry `0x280790` were found. The incoming register value copied from RCX to R15 at `0x2807B3` is passed to the helper builders, but its caller/indirect dispatcher is unresolved. No incoming stack-argument mapping was claimed.

## Resolver call contract at 0x28089E

- ECX is a key-like scalar: `[RBP+0x08]` is dereferenced at `+0x30`; `0xCB4B50` saves/tests ECX and passes its address to `0xCA5BC0`.
- RDX is a container/owner-like input: `0xCB4B50` derives a lookup root at `RDX+0x38` and passes it to `0xCA5BC0`.
- The resolver result flows RAX → RBX (`0x2808A3`) → `[RBX]` to R8D (`0x280F75`) → placement call `0x280F86`.
These roles do not establish semantic ownership or identify the returned record as a VoxelBlueprint/cache record.

## Cross-system correlation

- **createBuildingItem:** NOT_CONNECTED. No connected pointer/dataflow edge from this stack buffer to CreateBuildingItemAction.itemId or selectedIndex.
- **clientPlayerInput:** NOT_CONNECTED. No pointer identity or caller producer connects the local buffer to ClientPlayerInput.data.
- **serverConsumedPlayerInput:** NOT_CONNECTED. No common base accesses the relevant consumed version and these frame slots.
- **semanticActionDispatcher:** NOT_CONNECTED. No CreateBuildingItemAction dispatch edge reaches this function or its input buffer.
- **snapPreview:** NOT_CONNECTED. No register/base identity links either local-buffer field to the accepted snap arrays or preview writeback.
- **blueprintCache:** RESOLVER_RETURN_CONNECTED_CACHE_OWNERSHIP_UNPROVEN. CB4B50 is an Item-ID lookup helper and its returned record's semantic type is not proven to be VoxelBlueprintItem or the CA90E0 placement cache.

## Convergence delta versus CODE-0001

Both frame locations normalize to local stack slots; neither longer-lived owner is proven. Selection connection: `False`. Preview/snap connection: `False`. VoxelBlueprint/cache connection: `False`. The separate resolver-return pointer connection to RBX is proven. Common owner: `False`. Overall: **PARTIAL_STATIC**.

## PROVEN_STATIC / INFERRED / UNSOLVED

- **PROVEN_STATIC:** chained `.pdata` relationship; unwind/prologue stack arithmetic; both RBP displacements lie in the local frame; both locations alias offsets `+0x38/+0x78` in the local buffer; RCX/RDX expressions at the resolver; resolver return path to RBX and R8D.
- **INFERRED:** the local buffer is populated from the entry RCX/R15 source by helper routines, based on their argument setup and destination writes. This does not prove which source member writes either target field.
- **UNSOLVED:** exact field writers and source members; indirect function-entry caller; semantic owner; action/player-input/preview/cache identity.

## Rejected interpretations

Positive RBP displacements are not treated as incoming arguments: unwind/prologue arithmetic places them inside the local frame. Similar offsets, resolver use, or a connected resolver-return pointer do not prove player, selection, preview, or VoxelBlueprint ownership. The staging object is not used as evidence.

## Exact next static boundary

- CODE-0003 should statically map the data-dependent output layout written by 0x8DA7C0 and 0x8D5CA0, then prove or reject which source writes localBuffer+0x38 and localBuffer+0x78.
- Find the indirect entry/dispatch reference to the logical function 0x280790..0x2810E8 and recover its RCX source without assuming a semantic type.
- Only after a concrete owner/base is recovered, compare instruction-connected edges against CreateBuildingItemAction, ClientPlayerInput, preview/snap, and CA90E0 consumers.

**No runtime hook, game-memory mutation, executable patch, or native DLL change was added.**

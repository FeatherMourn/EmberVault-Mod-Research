# Blueprint Selection Authority — Static Map v1

**Scope / build:** Enshrouded revision 1076226, executable SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
Static/offline only. No process access, runtime observer, native mutation, or deployed-DLL change.

## Existing evidence carried forward

CreateBuildingItemAction is PROVEN_STATIC (0x0C; selectedIndex +0x04, itemId +0x08), but its action-specific native consumer and UI event connection remain UNSOLVED. The downstream placement path starts at `0x280F86 -> 0x3E2CD0`; its local resolver result feeds R8D, then a separate resolver/cache/event chain. The late BuildingPlaceEvent argument is not geometry authority. `0xCA90E0` remains a placement/cache lookup, not selection authority.

## Backward trace from placement R8D

Containing .pdata range: `0x2807D5..0x2810E8`. At `0x280F75`, `mov r8d, dword ptr [rbx]` loads the call argument from a record candidate at +0. RBX is defined at `0x2808A3` from RAX returned by `0xCB4B50` at `0x28089E`. The resolver ECX key comes from `[qword ptr [RBP+0x08] + 0x30]`; this does not identify the object semantically.

Instruction-level slice:

- `0x280F75` `mov r8d, dword ptr [rbx]` — source `[RBX]`, destination `R8D (zero-extended into R8)` (PROVEN_STATIC_BUILD_1076226).
- `0x2808A3` `mov rbx, rax` — source `RAX`, destination `RBX (record pointer candidate)` (PROVEN_STATIC_BUILD_1076226).
- `0x28089B` `mov ecx, dword ptr [rcx + 0x30]` — source `[RCX+0x30]`, destination `ECX` (PROVEN_STATIC_BUILD_1076226).
- `0x280897` `mov rcx, qword ptr [rbp + 8]` — source `[RBP+0x8]`, destination `RCX` (PROVEN_STATIC_BUILD_1076226).
- `0x28089E` `call 0xcb4b50` — source `return value from resolver using ECX/RDX inputs`, destination `RAX (resolver return)` (PROVEN_CALL_SITE; RETURNED_RECORD_CONTENTS_UNRESOLVED).

**First unresolved boundary:** resolver return boundary: returned record depends on the resolver's container argument and runtime contents; the RDX frame-slot owner/value semantics and returned mapping are unresolved

Additional unresolved input: resolver ECX key is dword ptr [qword ptr [RBP+0x08] + 0x30], and resolver RDX is qword ptr [RBP+0x48]; the RBP-relative object owner/type and resolver container contents remain unidentified.

## Forward trace from CreateBuildingItemAction

The imported map reports consumer status `UNSOLVED` and 96 generic shape candidates. None has action-pointer provenance, complete field flow, a CreateBuilding consumed-version relation, or a proven placement connection. The InventoryTransferAction dispatcher remains a reference pattern only.

**First unresolved boundary:** CreateBuildingItemAction's transient/native dispatch consumer and action-pointer owner; the current evidence has no complete itemId/selectedIndex/version flow or write to the placement resolver source.

## Snap/preview winner-writeback investigation

### Filter caller `0x3E377D`
Collection local `[RBP+0x190]`; first collection-data call `0x3EB810`; prior map classification `forwarded-to-secondary-candidate-processing`.
Post-return: `0x3E3782 test al, al` → `0x3E3784 je 0x3e3c2e` → `0x3E378A mov rax, qword ptr [r14 + 0x430]` → `0x3E3791 or rax, qword ptr [r14 + 0x428]` → `0x3E3798 je 0x3e37ab` → `0x3E379A movzx eax, byte ptr [r14 + 0x438]` → `0x3E37A2 dec al` → `0x3E37A4 cmp al, 0x7e` → `0x3E37A6 setbe al` → `0x3E37A9 jmp 0x3e37bf` → `0x3E37AB mov rcx, qword ptr [rdi + 0xf8]` → `0x3E37B2 mov rdx, r14` → `0x3E37B5 call 0xcc0040`.
Frontier: 0x3EB810: accepted-collection local data reaches this call; callee selection/writeback semantics remain unresolved.

### Filter caller `0x3E4347`
Collection local `[RBP+0x1B0]`; first collection-data call `0x99F970`; prior map classification `forwarded-to-transform-or-commit-helper`.
Post-return: `0x3E434C mov r12, qword ptr [rsp + 0x1bb0]` → `0x3E4354 test al, al` → `0x3E4356 je 0x3e47c3`.
Frontier: 0x99F970: accepted-collection local data reaches this call; callee selection/writeback semantics remain unresolved.

### Filter caller `0x3E6C9C`
Collection local `[RBP+0xD0]`; first collection-data call `0x99F970`; prior map classification `forwarded-to-placement-helper`.
Post-return: `0x3E6CA1 test al, al` → `0x3E6CA3 je 0x3e6d5a` → `0x3E6CA9 mov r8, r14` → `0x3E6CAC lea rcx, [rbp - 0x30]` → `0x3E6CB0 mov rdx, rsi` → `0x3E6CB3 call 0x3eab80`.
Accepted collection use: `0x3E6CB8 mov rax, qword ptr [rbp + 0xd0]` → `0x3E6CBF lea r9, [rsp + 0x50]` → `0x3E6CC4 mov r8, qword ptr [rsi + 0x30]` → `0x3E6CC8 xor edx, edx` → `0x3E6CCA mov rcx, qword ptr [rsi + 0x118]` → `0x3E6CD1 mov qword ptr [rsp + 0x60], rax` → `0x3E6CD6 mov rax, qword ptr [rbp + 0xd8]` → `0x3E6CDD mov qword ptr [rsp + 0x68], rax` → `0x3E6CE2 lea rax, [rbp - 0x30]` → `0x3E6CE6 movaps xmm0, xmmword ptr [rsp + 0x60]` → `0x3E6CEB mov qword ptr [rsp + 0x70], rax` → `0x3E6CF0 lea rax, [rbp + 0x1500]` → `0x3E6CF7 mov qword ptr [rsp + 0x50], rax` → `0x3E6CFC lea rax, [rsp + 0x60]` → `0x3E6D01 mov byte ptr [rsp + 0x40], 1` → `0x3E6D06 mov byte ptr [rsp + 0x38], 0` → `0x3E6D0B mov qword ptr [rsp + 0x30], rax` → `0x3E6D10 lea rax, [rbp - 0x80]` → `0x3E6D14 mov qword ptr [rsp + 0x28], rax` → `0x3E6D19 lea rax, [rsp + 0x70]` → `0x3E6D1E mov qword ptr [rsp + 0x78], 0x100` → `0x3E6D27 movaps xmm1, xmmword ptr [rsp + 0x70]` → `0x3E6D2C mov qword ptr [rsp + 0x58], 0x100` → `0x3E6D35 movdqa xmmword ptr [rsp + 0x60], xmm0` → `0x3E6D3B movaps xmm0, xmmword ptr [rsp + 0x50]` → `0x3E6D40 mov qword ptr [rsp + 0x20], rax` → `0x3E6D45 movdqa xmmword ptr [rsp + 0x70], xmm1` → `0x3E6D4B movdqa xmmword ptr [rsp + 0x50], xmm0` → `0x3E6D51 call 0x99f970`.
Frontier: 0x99F970: accepted-collection local data reaches this call; callee selection/writeback semantics remain unresolved.

### Filter caller `0x3EB297`
Collection local `[RBP+0x3D0]`; first collection-data call `0x3EB810`; prior map classification `forwarded-to-secondary-candidate-processing`.
Post-return: `0x3EB29C test al, al` → `0x3EB29E je 0x3eb5df` → `0x3EB2A4 lea rax, [rbp + 0x1800]` → `0x3EB2AB mulss xmm9, xmm6` → `0x3EB2B0 mov qword ptr [rsp + 0x40], rax` → `0x3EB2B5 mulss xmm7, xmm6` → `0x3EB2B9 mov qword ptr [rsp + 0x48], 0x1000` → `0x3EB2C2 cvttss2si rcx, xmm9` → `0x3EB2C7 mov dword ptr [rsp + 0x60], r12d` → `0x3EB2CC mov dword ptr [rsp + 0x64], r13d` → `0x3EB2D1 mov dword ptr [rsp + 0x68], edi` → `0x3EB2D5 mov dword ptr [rsp + 0x5c], 6` → `0x3EB2DD cvttss2si rax, xmm7` → `0x3EB2E2 mov dword ptr [rsp + 0x58], ecx` → `0x3EB2E6 mulss xmm8, xmm6` → `0x3EB2EB mov dword ptr [rsp + 0x54], eax` → `0x3EB2EF imul ecx, eax` → `0x3EB2F2 cvttss2si rdx, xmm8` → `0x3EB2F7 imul ecx, edx` → `0x3EB2FA mov dword ptr [rsp + 0x50], edx` → `0x3EB2FE cmp ecx, 0x1000` → `0x3EB304 ja 0x3eb5df` → `0x3EB30A mov rdx, qword ptr [r14 + 0x118]` → `0x3EB311 lea rax, [rsp + 0x40]` → `0x3EB316 mov edi, 1` → `0x3EB31B mov qword ptr [rsp + 0x30], rax` → `0x3EB320 lea rcx, [rsp + 0x30]` → `0x3EB325 mov qword ptr [rsp + 0x38], rdi` → `0x3EB32A call 0xe81920`.
Accepted collection use: `0x3EB588 mov rax, qword ptr [rbp + 0x3d0]` → `0x3EB58F lea rdx, [rsp + 0x30]` → `0x3EB594 mov qword ptr [rsp + 0x30], rax` → `0x3EB599 mov rcx, r14` → `0x3EB59C mov rax, qword ptr [rbp + 0x3d8]` → `0x3EB5A3 mov qword ptr [rsp + 0x38], rax` → `0x3EB5A8 call 0x3eb810`.
Frontier: 0x3EB810: accepted-collection local data reaches this call; callee selection/writeback semantics remain unresolved.

The `0x3EB810` helper iterates accepted entries by stride `0x50` and forwards qualifying candidates to `0x3E5480`. `0x3E5480` invokes `0x3ED1A0`, then writes candidate-derived values through the returned pointer. The output owner/lifetime and relation to persistent preview or a single selected winner are not proven.

## Convergence result

Status: **PARTIAL_STATIC**. Common selection/placement owner proven: `False`. CreateBuilding item write to placement source proven: `False`. Blueprint-record connection proven: `False`.

## PROVEN_STATIC / INFERRED / UNSOLVED

- **PROVEN_STATIC:** reflected action layout; `0x280F86` call; R8D load from `[RBX]`; RBX receives the result of the resolver call at `0x28089E`; snap accepted-record stride/caller set; per-candidate helper data flow noted above.
- **INFERRED:** R8D is a candidate item/record identity because its source is a resolver-returned record's first dword and downstream build analysis uses this argument as a placement resolver key. This does not prove selection-action origin.
- **UNSOLVED:** action consumer/owner; common selection-placement base; persistent selected blueprint/preview owner; winner selection from accepted snap candidates; target preview lifetime.

## Rejected interpretations

Numeric ItemId equality, generic +0/+4/+8 shape, proximity to snap/preview code, a call to `0xCA90E0`, or temporal ordering do not establish action identity or authority. `0xCB4B50`, `0xCA90E0`, `0x3E2CD0`, and the rejected selector detour are not observer candidates. The v0.31 late helper argument mutation remains disproven for geometry.

## Safe next experiment

Continue static analysis from the exact RBP-relative key source and the unknown resolver-container owner; separately inspect caller-specific consumers beginning at the frontiers above. Any runtime observer requires a separately reviewed change after a low-frequency writer, pointer provenance, and lifetime are established.

**No runtime hook, game-memory mutation, or native DLL change was added.**

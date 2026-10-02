# Placement Helper Buffer Field Provenance — Static Map v1

Scope: Enshrouded revision 1076226; executable SHA-256 AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781.
Offline/static only. No process access, hooks, executable patching, game-memory writes, or deployed-DLL changes.

## Parent CODE-0002 frontier

CODE-0002 remains PARTIAL_STATIC; its frame model maps RBP+0x08 to localBuffer+0x38 and RBP+0x48 to localBuffer+0x78.

## Helper callsite-to-target map

- 0x2807B6 -> 0x8DA7C0; buffer alias True; reaches resolver True; entry/straight-line path.
- 0x2807C8 -> 0x8D5CA0; buffer alias True; reaches resolver True; entry/straight-line path.
- 0x2810A3 -> 0x8D5CA0; buffer alias True; reaches resolver True; conditional or loop path; predicates unnamed.

## Helper 0x8DA7C0

Range 0x8DA7C0..0x8DA9DE. Output mapping PROVEN_STATIC.
Fixed writes 0; dynamic output candidates 1; nested callees 8.

- 0x8DA8AC mov qword ptr [rdi], rbx -> [0x0, 0x8); width 8; +0x38 False; +0x78 False; PROVEN_STATIC.
- 0x8DA992 mov qword ptr [rcx], rdx -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.

## Helper 0x8D5CA0

Range 0x8D5CA0..0x8D5E73. Output mapping PROVEN_STATIC.
Fixed writes 0; dynamic output candidates 7; nested callees 0.

- 0x8D5D35 mov qword ptr [r14 + rcx + 8], r9 -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5D77 mov qword ptr [rdx], rax -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5DA3 mov qword ptr [rdx + rdi], rax -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5DCC mov qword ptr [rax + rsi], rdx -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5DF7 add qword ptr [rcx], rax -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5E25 add qword ptr [rcx + rdi], rax -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.
- 0x8D5E46 add qword ptr [rdx + rsi], rcx -> unknown/dynamic; width 8; +0x38 None; +0x78 None; UNSOLVED_DYNAMIC_DESTINATION.

## localBuffer+0x38

Status UNSOLVED. Fixed reaching writers 0; dynamic unresolved candidates 8.
Last proven writer none.
First unresolved boundary: No fixed destination write to this field was found; indexed/register-computed helper writes remain unresolved.

## localBuffer+0x78

Status UNSOLVED. Fixed reaching writers 0; dynamic unresolved candidates 8.
Last proven writer none.
First unresolved boundary: No fixed destination write to this field was found; indexed/register-computed helper writes remain unresolved.

## Cross-system correlation

- createBuildingItem: NOT_ESTABLISHED; pointer identity NOT_ESTABLISHED.
- clientPlayerInput: NOT_ESTABLISHED; pointer identity NOT_ESTABLISHED.
- selectionFrontier: NOT_ESTABLISHED; pointer identity NOT_ESTABLISHED.
- snapPreview: NOT_ESTABLISHED; pointer identity NOT_ESTABLISHED.
- blueprintCache: NOT_ESTABLISHED; pointer identity NOT_ESTABLISHED.

## Convergence delta versus CODE-0002

Field +0x38 writer False; field +0x78 writer False; incoming R15 False; common owner False; overall PARTIAL_STATIC.

## Findings

PROVEN_STATIC: executable callsite targets, helper ranges, RDX-to-RDI output aliases, and fixed/dynamic write classification.
INFERRED: helpers can populate the caller-provided buffer.
UNSOLVED: exact target-field writers, source values, semantic owner, and cross-system identity.

## Exact next static boundary

- Resolve indexed destination arithmetic in 0x8D5CA0 and variable-size nested writes from 0x8DA7C0.
- If a writer is recovered, backward-slice only direct aliases/direct callees and keep semantic ownership separate.
- Keep opaque/indirect boundaries explicit; no runtime instrumentation is justified by this map.

No runtime hook, mutation, executable patch, or native DLL change was added.

# Placement Computed-Destination Arithmetic — CODE-0004

## Scope / build / executable SHA

- Mode: `OFFLINE_STATIC_ONLY`; revision `1076226`.
- Executable SHA-256: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
- No process access, executable writes, game-memory writes, or runtime hooks.

## Parent CODE-0003 frontier

The parent map remains `PARTIAL_STATIC`; its fixed-writer frontier did not resolve either target.

## Target byte-range derivation

- +0x38: `mov rcx, qword ptr [rbp + 8]`, width 8, range `[56, 64]`.
- +0x78: `mov rdx, qword ptr [rbp + 0x48]`, width 8, range `[120, 128]`.

## 0x8D5CA0 parent-callsite map

- 0x2807C8 and 0x2810A3 are retained separately; their runtime inputs are not assumed equivalent.

## Per-write arithmetic results

| RVA | normalized expression | width | +0x38 | +0x78 |
|---|---|---:|---|---|
| `0x8D5D35` | `output + 8 + 8*j` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5D77` | `output + 8 + 8*A + 8*j` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5DA3` | `output + 8 + 8*A + 8*R + 16*k` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5DCC` | `output + 16 + 8*A + 8*R + 16*k` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5DF7` | `output + 8 + 8*A + 8*R + 8*j` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5E25` | `output + 8 + 8*A + 8*R + 16*k` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |
| `0x8D5E46` | `output + 16 + 8*A + 8*R + 16*k` | 8 | CAN_HIT_TARGET | CAN_HIT_TARGET |

## Induction/index models

A is a zero-extended byte load, R/C are zero-extended word loads, and B is the unsigned loop bound. Loop indices start at zero and increment by one; the stride in the output address is explicit in each expression.

## +0x38 and +0x78 reachability

All seven primary writes are `CAN_HIT_TARGET` under their recorded runtime domains. Each result carries a concrete witness; this is arithmetic reachability only and does not promote an actual reaching writer.

## 0x8DA992 / nested variable-size writes

0x8DA992 reduces to an output-relative affine expression but stops at the unbounded qword G loaded from `[r9+0x1A8]`; both targets therefore remain `UNRESOLVED`. Direct zero-fill/copy callees are documented with destination and size expressions but are not promoted to field writers.

## Reaching-writer and source-provenance delta

The arithmetic frontier is narrowed to computed families, but no unique actual reaching writer or stored-value source is proven. No semantic owner is inferred.

## First unresolved boundary / CODE-0005

CODE-0005: recover runtime domains/loop inputs and path-specific execution evidence for the seven affine writers; resolve qword G or prove it cannot alias the output buffer.

## Rejected interpretations

A broad interval or a matching field offset is not treated as proof of execution, ownership, or last-writer status.

## Explicit safety statement

CODE-0004 is offline/static-only; observer installation is disabled and fail-closed.

# Snap candidate collection and selection — v0.27 offline map

This document records static evidence from the supported Enshrouded executable
(revision 1076226, SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`). The
analysis is read-only: no process access, detours, or game-memory writes were
used.

## Candidate filter and accepted collection

`0x3E79C0` receives an output collection in `RCX`. It obtains a temporary
candidate array from `[RSI+0x110]` through `0x8EF920`; the temporary records are
0x20 bytes and the loop advances `R14` by 0x20. Candidates are rejected by the
branches at `0x3E7B21`, `0x3E7B3A`, `0x3E7C43`, `0x3E7C49`, `0x3E7C52`, and
`0x3E7C80`. A surviving candidate resolves its `+0x08` key through
`0xCA90E0` (`RCX=[RSI+0xF0]`, `EDX=[candidate+0x08]`). Null results are skipped
at `0x3E7C9D`.

The destination collection is caller-owned and has the following observed
header:

| offset | evidence-backed use |
|---|---|
| +0x00 | element storage pointer |
| +0x08 | logical count (read before append; incremented at `0x3E7D99`) |
| +0x10 | capacity/end bound |
| +0x18 | grow callback (`0x3E7CC6` when full) |

Append addressing at `0x3E7D5D` computes `storage + count * 0x50`; therefore the
accepted element stride is **0x50**, not the 0x20-byte source stride. The append
copies the normalized record payload pointer/length/compression and dimensions,
then candidate-derived packed/vector fields and the source `+0x00` auxiliary
value. Their semantic names are intentionally unresolved.

## Callers and forward boundary

Direct callers are `0x3E377D`, `0x3E4347`, `0x3E6C9C`, and `0x3EB297`. They pass
stack-backed collections at (respectively) `[RBP+0x190]`, `[RBP+0x1B0]`,
`[RBP+0xD0]`, and `[RBP+0x3D0]`. The boolean return is tested immediately, but
the function does not return a winner. Post-return consumers include
`0x3EB810`, `0x3E5480`, `0x3EAB80`, and `0xE81920`; the first instruction that
selects one accepted element is not yet proven.

No score accumulator, sort, min/max comparison, or selected-candidate pointer
exists in the bounded `0x3E79C0` path. Consequently no selection semantics are
claimed in v0.27.

## Observer decision

No runtime observer was installed. The candidate append site is potentially
high-frequency and the caller collections are short-lived locals; a safe,
low-frequency observation boundary has not been established. The generated
`bridge/snap_candidate_selection_static_map.json` is the authoritative machine-
readable record.

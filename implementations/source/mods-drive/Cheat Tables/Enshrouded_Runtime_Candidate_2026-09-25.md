# Runtime candidate evidence — screenshot only

Source: user-provided Memory Viewer screenshot, captured against `enshrouded.exe`.

## Visible candidate

- Memory Viewer location label: approximately `enshrouded.exe+1F3014`
- Visible instruction: `mov [rcx+rbx*4], eax`
- Visible nearby operations include `sub rdi,10`, `sub rbx,1`, `ins`, and loads from `[rsp+...]`.
- Visible memory pane: readable/writable allocation beginning around `0x7FF6B38AE000`, size `0x8000`.

Independent on-disk disassembly of the current executable confirms:

```text
RVA+0x001F300A: 8b 4e 08                 mov ecx, dword ptr [rsi + 8]
RVA+0x001F300D: 8b 44 24 64              mov eax, dword ptr [rsp + 0x64]
RVA+0x001F3011: 48 03 ce                 add rcx, rsi
RVA+0x001F3014: 89 04 99                 mov dword ptr [rcx + rbx*4], eax
RVA+0x001F3017: 48 83 ef 10              sub rdi, 0x10
RVA+0x001F301B: 48 83 eb 01              sub rbx, 1
RVA+0x001F301F: 79 80                    jns 0x1401f2fa1
```

Static interpretation: this is a loop writing a 32-bit value from `[rsp+0x64]` into an array-like location based on `rsi + [rsi+8]` and an index in `rbx`. It resembles bulk record/attribute population, but no requested feature can be assigned from this alone.

## Evidence classification

Status: **Needs evidence**.

The screenshot does not establish:

- Which requested feature triggered the write.
- Whether `[rcx+rbx*4]` is authoritative gameplay state, a cache, UI data, or a temporary buffer.
- The exact instruction bytes and complete instruction boundary.
- The values of `rcx`, `rbx`, and `eax` during repeated actions.
- Whether this location has exactly one independent AOB match.
- Register/flag/stack preservation requirements or a safe return path.

The exact three-byte instruction is confirmed statically, but a hook signature and implementation remain intentionally absent. The screenshot's live allocation address is not treated as a persistent pointer.

## Candidate signature uniqueness check

A context pattern assembled from the verified neighboring instructions:

`8B 4E 08 8B 44 24 64 48 03 CE 89 04 99 48 83 EF 10 48 83 EB 01 79 80`

was scanned in the current executable's `.text` section. It matched twice, at RVAs `0x1F300A` and `0x26D94A`. Therefore it fails the exactly-one-match gate and is rejected as an implementation signature. No additional wildcard tuning is being used to force uniqueness without feature/runtime evidence.

## Required follow-up

Repeat one offline action while breaking on this write, record the effective destination and source value, then repeat with an unrelated action. Capture the full disassembly bytes, register state, call stack, and whether the destination changes with the requested feature. Do not patch this instruction or derive a table entry from the screenshot alone.

## Mana correlation update

The user identified the screenshot write as the Mana path. This establishes feature correlation, but not authoritative-state proof. A longer independently derived routine signature from the current executable, beginning at RVA `0x1F2F50` and ending before the conditional branch after the write, is 185 bytes and matched exactly once at RVA `0x1F2F50`.

Static status for Mana: **Needs evidence**.

Still required before implementation:

- Live `rcx`, `rbx`, and `eax` capture at the write.
- Effective destination and before/after value capture.
- Repeated spell-cost or Mana-change correlation.
- Proof that the destination is authoritative state rather than a cache or temporary attribute array.
- Full feature-specific preservation and disable test.

The unique routine match is static evidence only. No Auto Assembler hook was created.

## Mana scan evidence update

The user-provided Cheat Engine scan shows:

- Scan type: `Value between...`
- Value type: `4 Bytes`
- Remaining results: `17`
- Candidate manually added as `Mana`: address `0x3006EF1EFA4`
- Current value: `197`
- Previous value: `290`
- First-scan value shown: `365`

This is strong candidate-value evidence that Mana changed from 290 to 197, but it is not yet a stable pointer or authoritative-state proof. The address is a dynamic process address and must not be embedded in a table. The next required capture is `Find out what accesses this address` and `Find out what writes to this address` while casting the same spell repeatedly, followed by a pointer/structure trace across reload or respawn.

Status remains **Needs evidence**.

## Mana access-trace evidence update

The user-provided access dialog reports 1,655 hits for the candidate address and these visible instructions:

| Runtime instruction | Bytes | Operation | Interpretation |
|---|---|---|---|
| `7FF6B1BB1C1D` | `43 8B 04 BC` | `mov eax,[r12+r15*4]` | 32-bit read from an indexed array |
| `7FF6B1BC3014` | `89 04 99` | `mov [rcx+rbx*4],eax` | 32-bit write; matches static RVA `0x1F3014` |
| `7FF6B164D908` | `44 8B 0C 88` | `mov r9d,[rax+rcx*4]` | 32-bit read from an indexed array |
| `7FF6B1C043FA` | `44 8B 2C 91` | `mov r13d,[rcx+rdx*4]` | 32-bit read from an indexed array |
| `7FF6B1BC8783` | `8B 1C 91` | `mov ebx,[rcx+rdx*4]` | 32-bit read from an indexed array |
| `7FF6B1C72041` | shown as `vmovdqu` | vector read | Bulk/packed data access |
| `7FF6B1C721A1` | shown as `vmovdqu` | vector read | Bulk/packed data access |

The write address maps exactly to the previously disassembled routine, strengthening the Mana correlation. However, the 1,655-hit count and multiple read sites show that this address is part of a shared indexed data flow. The trace does not yet prove that the write is the authoritative persistent Mana field rather than a derived attribute/cache population step.

Status remains **Needs evidence**. Required next evidence is a register capture at the write (`rcx`, `rbx`, `eax`, effective destination), plus a before/after value trace during repeated identical spell casts and a pointer-lifetime check after reload/respawn.

## Mana write-trace evidence update

The user-provided write dialog reports these writers for `0x3006EF1EFA4`:

| Count | Runtime address | Module RVA | Instruction |
|---:|---|---:|---|
| 11,996 | `7FF6B1BC3014` | `0x1F3014` | `mov [rcx+rbx*4],eax` |
| 3 | `7FF6B1BBD068` | `0x1ED068` | `add [rcx+rdx*4],edi` |
| 3 | `7FF6B1BB1095` | `0x1E1095` | `mov [rcx+rbx*4],eax` |
| 173 | `7FF6B1BC89FA` | `0x1F89FA` | `add [r8+rcx*4],eax` |

This distribution strongly prioritizes the primary writer at RVA `0x1F3014` for further investigation. It still does not prove that the destination is the authoritative Mana field: the same address is written by multiple code paths, and the write dialog does not show the source values or effective base/index registers.

Status: **Needs evidence**, with primary-writer candidate identified. Do not patch any writer yet.

## Mana primary-writer register capture

The user-provided debugger capture is explicitly **after** `mov [rcx+rbx*4], eax`:

| Register | Value | Relevance |
|---|---|---|
| `RCX` | `0x3006EF1EFA4` | Base/effective destination shown by the capture |
| `RBX` | `0x0` | Index; effective destination is `RCX + RBX*4 = 0x3006EF1EFA4` |
| `RAX/EAX` | `0x16D` / `365` | Value written by the instruction |
| `RSI` | `0x3006EF1EE80` | Structure/base input used by the preceding `add rcx,rsi` path |
| `RDX` | `0x10` | Nearby loop/context value |
| `RSP` | `0xB07D75A370` | Stack sample at the breakpoint |
| `RIP` | `0x7FF6B1BC3017` | Instruction after the write, consistent with post-execution capture |

This confirms one concrete write event and the effective address calculation. It does **not** yet prove whether `365` is current Mana, maximum Mana, a normalized/base attribute, or a cached/stat-population value. The earlier scan showed current `197`, so the source/destination role must be tested during a controlled spell cast and during passive regeneration separately.

Status remains **Needs evidence**. The next safe capture is the same breakpoint during a spell-cost event with `EAX`, destination, and the surrounding call context recorded before and after the write.

## Semantic clarification

The user confirms that `365` is both the current full Mana value and the character's current maximum Mana capacity at the time of capture. Therefore this candidate is presently classified as a **maximum/full-Mana attribute record**. It must not yet be treated as the consumable current-Mana field: a spell-cast capture is still needed to determine whether the same destination changes to a lower value or whether another field holds current Mana.

The observed structure relation is consistent with the preceding code: `RCX = RSI + dword ptr [RSI+8]`, and with `RBX=0` the write targets the first element of that derived array. This is runtime evidence for one instance only, not a stable pointer or table address.

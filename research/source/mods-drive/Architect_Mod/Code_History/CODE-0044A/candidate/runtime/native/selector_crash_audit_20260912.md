# Conditional selector crash audit — 2026-09-12

Source dump: `H:\SteamLibrary\steamapps\common\Enshrouded\crash_dumps\enshrouded_20260912_204228\enshrouded.dmp`.

## Outcome

The conditional selector detour is unsafe and is disabled in build
`architect-v013-selectoroff-20260912-j`. The Ring ItemRegistry link and the
stable `BuildingPlaceEvent` hook are unaffected.

The failure is not evidence against the Ring key or its resolver record. The
dump preserves `R8D = 0x56F66BA7` (`1458989991`) at the fault, but the fault is
caused before the normal resolver path can complete.

## Dump evidence

No WinDbg/CDB executable is installed on this machine, so the minidump's
standard Exception, Thread, Module, and MemoryList streams were decoded
offline. The exception context is unambiguous.

| Field | Value |
|---|---|
| Exception | `0xC0000005` (`ACCESS_VIOLATION`) |
| Fault RIP | `enshrouded.exe+0x3E2CEB` (`0x7FF764192CEB`) |
| Crash thread | `5424` (`GameServer`) |
| Dump exception metadata | access type `0` (read), reported address `0xFFFFFFFFFFFFFFFF` |
| Architectural fault instruction | `0F 29 70 B8` — `movaps xmmword ptr [rax-0x48], xmm6` |
| RAX | `0x7FF764192CE4` |
| Effective store address | `0x7FF764192C9C` (unaligned code address) |
| R8D | `0x56F66BA7` = Ring Item ID `1458989991` |
| RSP / RBP | `0x000000EDC31D2730` / `0x000000EDC31D2830` |
| RBX / RSI / RDI | `0x0000020019ABC9C0` / `0x00000200223A9000` / `0x0000030067E29D48` |
| R12 / R13 / R14 / R15 | `1` / `2` / `0` / `0x000000EDC31DA2C0` |

The dump's generic read/address fields conflict with the decoded `movaps`
store. The instruction and registers nevertheless prove an invalid,
misaligned SIMD destination: `RAX-0x48` is inside the executable code page and
is not 16-byte aligned. That is sufficient to explain the access violation.

## Original code and installed patch

The unmodified on-disk function at `0x3E2CD0` starts with this complete,
instruction-aligned 20-byte window:

```asm
3E2CD0  48 8B C4                    mov rax,rsp
3E2CD3  55                          push rbp
3E2CD4  53                          push rbx
3E2CD5  56                          push rsi
3E2CD6  57                          push rdi
3E2CD7  41 54                       push r12
3E2CD9  41 56                       push r14
3E2CDB  41 57                       push r15
3E2CDD  48 8D A8 88 FD FF FF        lea rbp,[rax-0x278]
3E2CE4  48 81 EC 40 03 00 00        sub rsp,0x340
3E2CEB  0F 29 70 B8                 movaps [rax-0x48],xmm6
```

The dump recorded the installed target patch:

```asm
3E2CD0  48 B8 90 25 48 36 FB 7F 00 00  mov rax,0x7FFB36482590
3E2CDA  FF E0                          jmp rax
3E2CDC  90 90 90 90 90 90 90 90        nop x8
```

The generated trampoline copied the first 20 bytes, then appended:

```asm
mov rax,0x7FF764192CE4
jmp rax
```

The window was not split and the original caller return address at
`0x280F8B` was preserved. The selector C stub's prologue (`push rsi`, `push
r13`, `push r15`, `sub rsp,0x30`) provides correctly aligned call sites and
32 bytes of shadow space. It does not need to preserve volatile `RAX` for its
own calls. The trampoline does need to preserve it for the resumed game
prologue, however.

## Root cause

High confidence: the trampoline continuation jump clobbers `RAX` after the
copied original prologue has deliberately set it to the original stack
pointer. The game continuation at `0x3E2CEB` uses that `RAX` value as the base
for aligned XMM saves. Instead it sees `0x7FF764192CE4`, the resume address,
and faults while storing `xmm6`.

The crash is therefore a trampoline state-preservation defect, not a failed
Ring resolver lookup. The saved context also shows the intended Ring key in
`R8D`; that observation does not make the selection experiment safe to resume.

Unwind metadata is absent for the dynamically allocated trampoline. It did
not cause this first fault, but it is another reason not to re-enable this
approach without a deliberately designed unwind-safe thunk.

## Safest next strategy

Do not patch the callee entry or the global resolver. First use only the
stable `BuildingPlaceEvent` hook and existing read-only diagnostics. If a
future interception is justified, it should be a reviewed call-site-specific
mechanism that preserves all live state without replaying a prologue through a
register-clobbering absolute jump, has explicit Windows x64 unwind handling,
and is tested without altering the selection key. No such interception is
included in this corrective build.

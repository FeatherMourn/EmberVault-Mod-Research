# Static call-site relay design — not enabled

This design is for the proven direct call only:

```text
enshrouded.exe+0x280F86: E8 45 1D 16 00    call 0x3E2CD0
enshrouded.exe+0x280F8B:                   continuation / return address
```

The linked runtime remains selector-disabled. `ArchitectSelectorCallRelay.asm`
is a standalone static artifact and is not linked, allocated, or referenced by
the runtime.

## Relay

```asm
cmp  dword ptr [rip+enabled], 1
jne  forward
mov  r8d, dword ptr [rip+replacementItemId]
forward:
mov  r11, qword ptr [rip+originalTarget]
jmp  r11
```

Expected emitted instruction layout (RIP-relative displacements are resolved
when the island is built):

```text
83 3D xx xx xx xx 01       cmp dword ptr [rip+enabled],1
75 07                      jne forward
44 8B 05 xx xx xx xx       mov r8d,dword ptr [rip+replacementItemId]
4C 8B 1D xx xx xx xx       mov r11,qword ptr [rip+originalTarget]
41 FF E3                   jmp r11
```

The state layout is `DWORD enabled`, `DWORD replacementItemId`, `QWORD
originalTarget`. A future installer would initialize `originalTarget` to the
real `enshrouded.exe+0x3E2CD0`; this static build performs no initialization or
patching.

## Call and stack behavior

Replacing only the five-byte original CALL with `E8 rel32(relay)` preserves
the hardware-pushed return address `0x280F8B`. The relay neither pushes nor
pops and makes no CALL. Its final JMP enters the real `0x3E2CD0` entry, so the
game's untouched prologue runs byte-for-byte and its ordinary RET returns to
`0x280F8B`.

There is no replayed prologue, no use of RAX, no relay stack frame, no shadow
space requirement, and no unwind frame. FLAGS may change, which is permitted
across the original CALL boundary. No XMM register is read or written.

| Register/state | Relay behavior |
|---|---|
| RCX, RDX, R9 | untouched |
| R8D | unchanged unless `enabled == 1`; then replaced from relay state |
| RAX | untouched |
| RBX, RBP, RSI, RDI, R12–R15 | untouched |
| R10 | untouched |
| R11 | overwritten with original callee target; ABI-volatile |
| RSP / return address | untouched; remains the CALL-produced `0x280F8B` |
| XMM / non-GPR state | untouched |

## Installation prerequisites and reachability

No installer is included. Any future installer must fail closed unless all of
the following are true:

1. fingerprint is supported;
2. bytes at `0x280F86` are exactly `E8 45 1D 16 00` and decode to
   `0x3E2CD0`;
3. the real target is exactly `imageBase + 0x3E2CD0`;
4. client and server Ring resolver proofs are complete;
5. the Ring record is non-null and `record[0] == 1458989991`;
6. an executable island is allocated within signed rel32 range of
   `imageBase + 0x280F8B`.

The patch is `E8 <signed 32-bit (relay - (callSite + 5))>`. The allocator must
search committed/free candidate regions within ±2 GB of the call-site return
address and verify the signed delta before writing. Failure to allocate a
reachable island is a hard stop, not a reason to use an absolute jump or a
longer patch.

## Restoration and static tests

A future implementation must retain the exact five original bytes, write the
patch only while code pages are writable, flush the instruction cache, and on
unload restore exactly those five bytes before freeing the island. It must not
unload while another thread can be executing the island.

Static checks performed for this artifact:

- MASM x64 assembly succeeds;
- emitted relay disassembly has one conditional R8D move and one `jmp r11`;
- no `call`, `push`, `pop`, `sub rsp`, `add rsp`, `rax`, or XMM instruction is
  emitted in the relay;
- the on-disk game bytes at `0x280F86` are the expected five-byte CALL and
  resolve to `0x3E2CD0`.

This is a design verification only. It makes no in-game claim and does not
permit relay installation.

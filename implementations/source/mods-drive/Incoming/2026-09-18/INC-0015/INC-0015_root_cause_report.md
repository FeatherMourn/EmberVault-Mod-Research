# INC-0015 Runtime Root-Cause Report

Date: 2026-09-18
Game build: 1076226
Input archive SHA-256: 2cd5c1a80de9a55d2c512d94d4fab8b40fabcb615167843bb0f4345ab3775bbd
Input archive size: 40,115,025 bytes
Native DLL SHA-256: ddc016bcaaac7c3551ab8beb07fe00de51e77ddada65396e308d2559af441202

## Runtime observation
User reports that the player is still launched/flying out of the map during world load after the teleport path at RVA 0x2C6863 was fully disarmed.

## Root cause — PROVEN FROM SOURCE
`write_abs_jump()` in `runtime/native/source/ArchitectNativeRuntime.c` installs a 12-byte absolute detour as:

```
mov rax, imm64
jmp rax
```

This destroys the game's incoming RAX value before the hook entry receives control.

`cheat_correlation_initialize()` automatically calls `cheat_correlation_begin()` for supported build 1076226. Therefore the cheat-correlation hooks are installed during native runtime startup before any F7 user action.

The movement hook at RVA 0x23AE34 overwrites this 16-byte vanilla block:

```
mulss xmm3,xmm9
add rcx,rax
add qword ptr [rdx],rcx
cvttss2si rax,xmm6
```

`architect_cheat_movement_entry` correctly replays these instructions, but it receives RAX already replaced by the detour destination address. Thus `add rcx,rax` adds the hook code address rather than the original movement operand; the corrupted value is then accumulated into `[rdx]`. This directly explains an enormous player/world-space displacement when movement code executes, including during world load.

This failure occurs even when `g_cheatSuperSpeed == 0` and speedMultiplier == 1.0.

## Independent corroboration
The bundled `bridge/cheat_correlation_status.json` reports:
- active = true
- superSpeed = false
- speedMultiplier = 1.00
- no command ID/action

So the problematic hook set can be active with no cheat command and no speed feature enabled.

## Other affected hooks
The same detour primitive is used by additional hook sites. At minimum:

- Day/time hook RVA 0xCE518A: displaced instructions use incoming RAX in `mov [rdi+48h],rax`; therefore the hook writes the detour destination address when time lock is OFF. This is a second directly unsafe site.
- Mana, jump, craft and skills displaced blocks do not restore/overwrite RAX before continuation, so the current detour violates register transparency and may corrupt downstream behavior.
- Inventory/observer hooks using `write_abs_jump()` must also be audited for whether RAX is live across the patched span. Do not assume safety merely because the hook is observe-only.

## Teleport assessment
The INC-0014 teleport remediation is present in this archive:
- transformInstalled = FALSE
- teleport state zeroed
- native teleport command rejected
- C# coordinate writes disabled

Therefore current runtime evidence disproves teleport as the cause of the world-load displacement.

## Immediate fail-closed remediation
1. Remove automatic `cheat_correlation_begin()` from `cheat_correlation_initialize()`.
2. Do not auto-start the entire hook set from generic command dispatch.
3. Until detour infrastructure is repaired, reject/disable all F7 features that require a `cc_install_one()` trampoline.
4. Keep byte-patch-only features separately gated if and only if their patch path is independently validated and does not install the unsafe hook set.

## Correct detour repair
For patched spans >=14 bytes, use a register-preserving absolute indirect jump:

```
FF 25 00 00 00 00
<8-byte destination>
```

This is `jmp qword ptr [rip+0]` and does not clobber a general-purpose register.

For sites with <14 bytes (for example the 12-byte craft hook), fail closed until a validated near-relay/trampoline strategy exists. Do not fall back to `mov rax,imm64 / jmp rax` unless the site contract proves RAX is dead.

Do not globally replace every `write_abs_jump()` call without auditing each site's overwrite length and contract; introduce a distinct register-preserving helper for the cheat hooks first.

## Required offline regression tests
- Synthetic detour transparency test: seed RAX/RCX/RDX with known sentinels, take the detour with feature disabled, and prove the continuation sees exact vanilla register/memory effects.
- Movement-specific synthetic test must prove `add rcx,rax` uses the original seeded RAX, not the hook target address.
- Day/time synthetic test must prove `[rdi+48]` receives the original RAX when time lock is false.
- Reject any hook site whose overwrite span is too short for the chosen register-preserving detour.

## Required runtime test
In a disposable test world:
1. Native DLL loads with cheat-correlation auto-install disabled.
2. World loads with no displacement.
3. Confirm status reports the mutation hook set inactive/uninstalled.
4. Only after this passes, test one repaired hook at a time with its feature OFF first, then ON, then OFF/revert.

## Evidence state
- Teleport as root cause: DISPROVEN for this regression.
- Startup cheat-correlation hook set: PROVEN active from source; corroborated by bundled status.
- `write_abs_jump()` clobbers RAX: PROVEN from source.
- Movement hook consumes original RAX after detour: PROVEN from source.
- Movement-hook RAX corruption explains launch/out-of-map symptom: PROVEN mechanism with direct runtime-consistent symptom; next discriminating A/B is world load with cheat-correlation hooks not installed.

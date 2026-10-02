# INC-0031 — Exact uploaded ZIP root-cause audit

Date: 2026-09-19
Game build: 1076226
Uploaded ZIP SHA-256: 98e443257cb5682209906246c540b1badcd22ab8589b6c99d51cab436575d9e0
Bundled native DLL SHA-256: f92cacf26161eeb04e8ca88873a3005c858f7bdaf11c5fd3b5b150e9eacc2175

## Runtime evidence
`bridge/cheat_correlation_status.json` records the failed live command:
- action `cheat.world.glider_stamina`
- accepted = true
- applied = false
- verified = false
- success = false
- gliderStamina = false
- patchGliderStaminaReady = true
- mutationBackendReady = true
- lastFailure = NOT_STARTED

This proves the earlier Skills dependency leak did not recur in this run, but the direct patch still failed after acceptance.

## PROVEN source root cause
`runtime/native/source/ArchitectPatchEngine.c` defines:
- `g_arch_VirtualProtect = 0`
- `g_arch_memcpy = 0`
- `g_arch_FlushInstructionCache = 0`

A complete source search finds no runtime assignments to these callbacks. The only assignments are inside `tests/test_patch_engine.c`.

`safe_patch_record()` therefore cannot enter the executable write path in the real DLL:
- `g_arch_memcpy` is null, so `savedOriginalBytes` is not copied,
- `savedOriginalValid` is nevertheless set to 1,
- `g_arch_VirtualProtect` is null, so `enableProtect = 0`,
- install fails before any patch write,
- because the target still contains vanilla bytes while `savedOriginalBytes` remains zeroed, the failed-install branch can set `recoveryRequired = 1`.

The dispatcher itself is correctly decoupled from `cheat_correlation_begin()` for `cheat.world.glider_stamina`: it sees `patchGliderStaminaReady`, accepts the command, calls `cheat_toggle_glider_stamina()`, and that toggle returns false because `safe_patch_record()` cannot execute.

## Secondary truthfulness defects
1. `mutationBackendReady` is assigned from `g_cc.buildSupported` only. It reports true even though the patch engine callbacks are unbound and no direct patch can mutate memory.
2. `patch*Ready` treats exact vanilla bytes as ready without requiring `!record.recoveryRequired`. After a failed attempt sets `recoveryRequired`, readiness can still remain true as long as the target bytes remain vanilla.
3. The dispatcher only logs a specific failure before entering the toggle. A failure inside `safe_patch_record()` falls through to generic `CheatCorrelation command rejected fail closed.` The status schema has no populated `lastCommandFailureReason`, causing the UI to show generic `Rejected by native backend`.

## Why offline tests missed it
- `tests/test_patch_engine.c` explicitly assigns the injected callbacks to test doubles, so patch-engine behavioral tests never cover production runtime binding.
- The integrated command-routing test is structural source inspection; it does not execute the runtime initialization path or a real direct patch through production callback binding.

## Minimal correction
Do not change any patch RVA/signature or hook ASM.

1. Add an explicit production binding step before `cheat_correlation_initialize()` in the worker startup path.
2. Use a no-CRT adapter for memcpy, e.g. a wrapper around existing `mem_copy` that returns `dest`.
3. Add `architect_patch_engine_bound()` (or equivalent) that requires all three callbacks non-null.
4. Set `mutationBackendReady = buildSupported && patchEngineBound`.
5. Require `!record.recoveryRequired` for the vanilla branch of every `patch*Ready` calculation.
6. Make `safe_patch_record()` fail immediately if the engine is unbound before setting `savedOriginalValid`.
7. Publish a specific command failure reason for patch-engine-unbound / patch-install failure.
8. Add a production-initialization regression that executes the real startup/bind path and asserts the three callback pointers are non-null before direct-patch readiness becomes true.
9. Add a true executable command regression: clean runtime state + glider vanilla bytes -> dispatch -> patch bytes -> verified active -> dispatch again -> exact vanilla bytes restored.

## Evidence status
- Direct-patch hook-framework independence: PROVEN for this run (lastFailure remained NOT_STARTED; hook framework inactive).
- Direct-patch production mutation backend binding: DISPROVEN in this package.
- Glider patch gameplay semantics: UNSOLVED; mutation never occurred.
- Patch RVAs/signatures: not challenged by this failure; target qualification reported ready and source failure occurs before write.

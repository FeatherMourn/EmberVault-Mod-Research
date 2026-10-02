# INC-0016 Deep Dive — F7 Commands Show ON but Do Not Affect Enshrouded

Date: 2026-09-18 (America/Los_Angeles)
Game build scope: Enshrouded revision 1076226 / executable SHA-256 `af2f5a1227911d8aa06b3908d6bd0211838211cae14ea91099cb57d0df990781`
Uploaded archive SHA-256: `e084d96716d02dc7601588df655d7b9ba603fedb1bf7f40edcc2ccb4eb76b142`
Uploaded EML log SHA-256: `9d1327dcd04bdf914209dd4408d00b34587c5c986a27b7a9baa503358fd21645`
Native DLL SHA-256: `86b0b16496f88d8c2fd59405b53c66342d86dfb32ed6fa62b7c8f86e6e3cb665`
Native DLL manifest: MATCHES
Archive file count after extraction: 4,498

## Executive diagnosis

The current build is a diagnostic hook-off build while the normal F7 mutation UI remains enabled.

The INC-0015 hotfix changed only two relevant source locations:

1. `CheatCorrelationHarness.c::cheat_correlation_initialize()` no longer auto-calls `cheat_correlation_begin()`.
2. `ArchitectNativeRuntime.c::parse_cheat_correlation_command()` no longer auto-calls `cheat_correlation_begin()` before ordinary cheat commands.

Those changes were correct as an emergency A/B isolation measure after the unsafe `write_abs_jump()` RAX-clobber finding. However, the rest of the product was not capability-gated around that diagnostic state. The dispatcher continues accepting hook-dependent commands, setting internal booleans, and publishing them as ON even when the required hook is absent.

This exactly explains the user's current behavior: commands can say ON while no Enshrouded-owned state changes.

## PROVEN finding 1 — Hook-dependent cheats are accepted even when their enforcement hooks are not installed

`parse_cheat_correlation_command()` currently accepts these actions without checking `g_cc.active` or the corresponding `*Installed` flag:

- `cheat.godmode.toggle` -> flips `g_cheatGodMode`
- `cheat.health.fill` -> arms `g_cheatFillHealthPending`
- `cheat.mana.toggle` / `cheat.mana.fill`
- `cheat.stamina.toggle` / `cheat.stamina.fill`
- `cheat.freecraft.toggle` -> flips `g_cheatFreeCraft`
- `cheat.speed.toggle` / `cheat.speed.set`
- `cheat.jump.toggle` / `cheat.jump.set`
- `cheat.skills.toggle` / `cheat.skills.set`
- `cheat.time.toggle` / `cheat.time.set`

These values only affect the game through the corresponding trampoline handlers. With automatic `cheat_correlation_begin()` intentionally disabled, a command can set the variable and return `ok=TRUE` while the game never executes the handler.

Required dependency mapping:

- God mode / health fill -> `healthInstalled`
- Infinite mana / mana fill -> `manaInstalled`
- Infinite stamina / stamina fill -> `staminaInstalled`
- Free crafting -> `craftInstalled`
- Movement speed -> `movementInstalled`
- Jump multiplier -> `jumpInstalled`
- Skill points -> `skillsInstalled`
- Time set/lock -> `daytimeInstalled`

Current code does not enforce those dependencies.

## PROVEN finding 2 — `cheat_correlation_begin()` lies about partial installation

The current runtime status included in the archive reports:

- `active: true`
- `hooksInstalled: 6`
- `lastFailure: "NONE"`
- `lastCommandAction: "cheatcorrelation.begin"`
- `lastCommandSuccess: true`

But `cheat_correlation_begin()` has eight required hooks after teleport was removed. It correctly detects `< 8` and sets:

`HOOK_INSTALL_PARTIAL_FAIL_CLOSED`

Then immediately continues and executes:

- `g_cc.active = TRUE`
- `g_cc.lastFailure = "NONE"`
- phase = `ACTIVE`
- `return TRUE`

Therefore a 6/8 partial installation is reported as fully active and successful. This is a direct false-positive state.

Correct behavior must be transactional: if any required hook fails, uninstall every hook installed during that attempt, keep `active=FALSE`, preserve a detailed failure reason and return FALSE.

## PROVEN finding 3 — The old unsafe detour primitive is still present

`write_abs_jump()` remains:

- `mov rax, imm64`
- `jmp rax`

This clobbers live RAX before the hook entry. INC-0015 already proved this is not transparent at the movement site. The current build did not replace this primitive; it only stopped automatic hook installation.

Therefore manually invoking `cheatcorrelation.begin` is still unsafe and should not be presented as a recovery step. The status in this archive shows it was invoked and six hooks installed, so the diagnostic build can still re-enter the unsafe path manually.

## PROVEN finding 4 — F7 badges represent internal intent/state, not authoritative game effect

`Update-AdminCheatBadges()` computes ON as:

- C# `NativeMemoryEngine.IsPatchActive(key)` OR
- `cheat_correlation_status.json` boolean

The native status booleans are mostly copied directly from control variables such as `g_cheatGodMode`, `g_cheatInfiniteMana`, and `g_cheatSuperSpeed`. They do not indicate that the corresponding hook installed, that the hook executed for the local player, or that an Enshrouded-owned value/readback changed.

This makes the UI semantically incorrect: ON currently means "Architect requested/armed this state," not "effect active in Enshrouded."

Recommended state model:

- UNSUPPORTED
- AVAILABLE
- QUEUED
- ACTIVE_PENDING_READBACK
- ACTIVE_VERIFIED
- FAILED_DEPENDENCY
- FAILED_WRITE
- FAILED_READBACK

Never render ON from a control boolean alone.

## PROVEN finding 5 — At least 25 literal enabled F7 actions have no matching native action

Static enumeration of literal `Send-CheatCommand` calls found 45 distinct actions. After applying the PowerShell aliases, only 20 map to an action recognized by the current native parser.

Examples still published without a matching native implementation include:

- `player.recovery.set`
- `player.attributes.set`
- `player.scaling.set`
- `movement.gravity`
- `movement.hover` -> mapped to unsupported `glider.flying`
- `movement.autorun`
- `glider.speed_mul`
- `glider.lift_mul`
- `item.autoloot`
- `item.clear`
- `item.give`
- `crafting.recipe_unlock`
- `gamesettings.production_time`
- `progression.player_level`
- `progression.combat_xp`
- `progression.xp_mul`
- `world.time_pause`
- `terrain.flatten`
- `terrain.dig`
- `prop.rotate`
- `prop.clone`
- `entity.kill`
- `entity.despawn`
- `build.instant_dismantle`
- `player.recover_items`

Several of their UI handlers immediately print success-like messages such as "applied", "unlocked", "spawned", "set", or "activated" without a backend ACK/readback.

## PROVEN finding 6 — C# fallback cannot save these commands while the native DLL is loaded

`NativeMemoryEngine` correctly yields byte-mutation ownership when `ArchitectNativeRuntime.dll` is present. That was an intentional safety fix.

Consequently, for current sessions the C# path generally does not provide a second functional implementation for the F7 commands. Some setter functions still update only C# local variables; some patch methods return "managed by native runtime"; and unsupported actions are still published to native afterward.

This makes the native runtime the authoritative path. When native hooks are intentionally uninstalled or an action is unsupported, the feature is inert despite the UI text.

## PROVEN finding 7 — Direct byte-patch cheats are not evidence-qualified

The native harness also contains direct byte-patch features for shroud, durability, fall damage, stealth, oxygen, cold, parry, skill reset, altar area/far, build range, plant growth and glider stamina.

Their target RVAs appear only inside `CheatCorrelationHarness.c`; no project mapping/evidence file references those RVAs. `patch_bytes()`:

- does not validate expected original bytes,
- does not enforce a signature match at the target,
- does not perform post-write readback,
- records whatever bytes happen to be present as "original",
- and callers such as `cheat_toggle_shroud()` return TRUE even if `patch_bytes()` fails.

These paths therefore do not meet the project's fail-closed mutation contract and cannot be called PROVEN.

## PROVEN finding 8 — Current runtime diagnostics contradict the mutation implementation

`native_status.json` says:

- mode = `observe_only_cheat_correlation`
- `targetGameMutation = false`
- `targetGameMutationScope = none_observe_only`

`backend_capabilities.json` says:

- mutationMasterGate = false
- registeredTargets = 0
- writableTargets = 0
- runtimeMutationStatus = `NOT_PROVEN`

Yet `parse_cheat_correlation_command()` performs mutation commands directly outside that capability framework.

This is architectural split-brain: the safety/capability system says mutation is blocked, while a separate native dispatcher bypasses it.

## PROVEN finding 9 — Existing tests do not test the behavior they claim

`tools/CheatCorrelation/tests/test_native_harness.py::test_no_game_mutation` only checks that the text `cheat_correlation_get_state` and `cheat_correlation_take_next` exist in the header. It does not assert absence of mutation code, patch calls, write APIs, or active mutation dispatch.

Therefore the suite can report PASS while the harness contains many mutation paths.

The current local run produced:

- CheatCorrelation: 14/14 PASS
- CheatSprint: 2 PASS, 1 skipped because the game executable is unavailable
- AdminConsole pure tests mostly pass; PowerShell-dependent tests cannot run in the Linux analysis environment

These passing tests do not contradict the runtime failure.

## Runtime/log evidence

The supplied EML log shows current build 1076226 loading successfully and Architect Toolkit registering its resources. It also shows EMBER active in the same sessions and modifying GameSettings, mana costs, recipes, building restrictions and other resources. EMBER is a test confound for individual gameplay effects but does not explain the Architect command-bridge false-positive state.

The archive's `native_runtime.log` repeatedly contains:

`CheatCorrelation command rejected fail closed.`

without logging the action, commandId or rejection reason. This makes field debugging unnecessarily difficult.

## Evidence conflict with prior project state

`bridge/first_cheat_sprint.json` explicitly records:

- primaryResult = `NO_SAFE_MUTATION_CANDIDATE_FOUND`
- movement 0x23AE34 REJECTED
- stamina 0x23423F REJECTED
- mana candidate REJECTED
- durability candidate REJECTED
- mutationMasterGateChanged = false
- runtimeBehaviorChanged = false

The current runtime later converted several of these research candidates into mutation controls without obtaining the required local-player correlation, owner/readback model or restoration proof. This violates the project's evidence ordering and explains why compile/pipeline passes did not translate into working gameplay features.

## Recommended repair sequence

### 1. Keep all unsafe trampoline-backed mutations disabled

Do not re-enable `cheat_correlation_begin()` as the fix. `write_abs_jump()` is still register-clobbering.

Mark God Mode, infinite mana/stamina, speed, jump, free craft, skill points and time hook features UNSUPPORTED until a register-transparent hook primitive is qualified and each feature's site has independent runtime proof.

### 2. Make command availability dependency-driven

Every command definition must declare its backend dependency. A command requiring `healthInstalled` must reject if it is false. No state boolean should be toggled on rejection.

### 3. Make hook installation transactional

For a requested hook set:

- validate each signature and overwrite contract,
- install one by one,
- if any required hook fails, uninstall all hooks installed in that transaction,
- leave active FALSE,
- publish per-hook status and the exact failure.

### 4. Remove UI-local success claims

Buttons should display QUEUED after publication. Only matching native ACK + independent readback can promote to ACTIVE/COMPLETE.

### 5. Disable every action not accepted by an authoritative backend

The current UI contains many still-enabled actions with no native implementation. Disable them visibly rather than sending commands that are guaranteed to reject.

### 6. Bring direct byte patches under the named-target capability framework

For each target require:

- exact build fingerprint,
- unique signature or exact independently justified RVA,
- expected original bytes,
- scoped write,
- immediate readback,
- session original preservation,
- verified revert,
- runtime behavior test in a disposable world.

Until then the direct patch buttons should remain disabled.

### 7. Repair diagnostics

On every native command record:

- commandId
- action
- accepted/rejected
- dependency state
- hook/target used
- write result
- readback result
- explicit rejection reason

Expose all eight hook booleans in `cheat_correlation_status.json`; a single `hooksInstalled` count is insufficient.

### 8. Update tests to verify semantics, not text presence

Add tests for:

- hook-off command -> rejected and control variable remains unchanged
- missing per-feature hook -> rejected
- partial begin -> rollback + active false
- disabled hook transparency
- exact expected bytes + readback for each direct patch
- UI does not show ON from intent/control state alone
- every enabled F7 action maps to an authoritative backend action
- no success wording before ACK/readback

## Bottom line

The current "commands ON but nothing happens" behavior is not a mystery and is not primarily an EML problem. It is a predictable consequence of INC-0015 diagnostic hook-off mode being combined with a mutation UI/dispatcher that was left enabled and still treats internal booleans as effect state.

The safest next build should reduce the enabled surface rather than trying to force all features on. First make capability/status truthfully match what is proven. Then reintroduce one mutation at a time behind a verified backend and readback contract.

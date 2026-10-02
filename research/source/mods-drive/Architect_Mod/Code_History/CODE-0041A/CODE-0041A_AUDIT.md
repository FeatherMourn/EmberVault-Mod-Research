# CODE-0041A — Safety-restoration follow-up audit

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: user-provided Architect Toolkit 0.42.0 / INC-0062
Current ArchitectRuntime.ps1 SHA-256: 10a3a1253e5dc4fda8ee818e46b30490f974afac25fc53e1213802d98a2cb561
Current admin_action_registry.json SHA-256: 092b83c5146a0a2ab7c63306534a5f0c5938729999e60980be2619dde194c8b3
Status: SOURCE-AUDITED / DO NOT RUNTIME TEST YET

## Confirmed restored
- `Invoke-PlayerTeleport` is fail-closed and performs no coordinate write.
- `Send-CheatCommand` rejects teleport action IDs before mutation.
- `movement.hover` / glider flight direct F7 mutation is rejected.
- `loot.auto` / `cheat.autoloot.toggle` is rejected as `STARTUP_CANARY_ONLY` before live mutation.
- `Bind-AdminActionControl` and responsive helper definitions remain present.

## Remaining critical blocker — mutation occurs before capability gating
`Send-CheatCommand` still contains direct C# mutation paths before the authoritative capability check:
- `movement.gravity` -> `NativeMemoryEngine::TogglePatch("gravityZero")`
- `cheat.survival.enable_all` -> `NativeMemoryEngine::EnableAllSurvival()`
- `cheat.survival.disable_all` -> `NativeMemoryEngine::DisableAllSurvival()`
- generic `$patchKeyMap` -> `NativeMemoryEngine::TogglePatch($pKey)` for shroud, durability, fall damage, stealth, oxygen, cold, free craft, parry, altar area/far, build range, plant growth, glider stamina, fog area, crypt area

The authoritative `Get-AdminCapabilities` fail-closed check runs only *after* this generic patch block. Therefore an action can mutate through the C# path before the UI/backend capability layer rejects it. This violates CODE-0036 mutation ownership and the fail-closed contract.

## Additional direct UI bypasses
- Mobility page Zero-G button directly calls `NativeMemoryEngine::TogglePatch("gravityZero")`.
- Combat page Easy Parry button directly calls `NativeMemoryEngine::TogglePatch("easyParry")` and then also calls `Send-CheatCommand`.
- Home/Settings panic/reset handlers directly call `NativeMemoryEngine::DisableAllSurvival()` before dispatching the canonical reset action.

These bypass canonical action identity and authoritative backend ownership.

## Registry / layout state
- `admin_action_registry.json` remains at 20 actions.
- `Bind-AdminActionControl` has definition-only occurrence; no executable control call sites.
- `New-AdminPageRoot`, `New-AdminSection`, and `New-AdminResponsiveGrid` also remain definition-only.
- Page internals remain fixed-position/fixed-size.

## Required next repair
Before responsive migration, remove all F7-owned direct C# mutation calls. `Send-CheatCommand` must capability-gate first and dispatch only through the canonical authoritative backend. UI handlers must not call `NativeMemoryEngine` mutation APIs directly.

Do not runtime test until this mutation-before-gate problem is eliminated and statically verified.

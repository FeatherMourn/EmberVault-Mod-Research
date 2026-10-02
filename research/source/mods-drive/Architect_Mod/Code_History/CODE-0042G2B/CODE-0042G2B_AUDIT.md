# CODE-0042G2B — Crafting / Progression event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 4b5076222b865cc2be45126c93021ff12ee27c7d6d014896e8b40679dfe616b8
Current admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G2B EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G2B

`Render-CraftingProgressionPage` now contains:

- raw `Register-SafeUiEvent`: 0
- raw `.Add_Click(...)`: 0
- source-level `Register-AdminActionEvent` sites: 3

Canonical runtime EventIds:

- `f7.crafting.skillPoints.apply.click` -> `cheat.skills.set`
- `f7.crafting.skillPoints.preset.10.click` -> `cheat.skills.set`
- `f7.crafting.skillPoints.preset.50.click` -> `cheat.skills.set`
- `f7.crafting.skillPoints.preset.114.click` -> `cheat.skills.set`
- `f7.crafting.skillPoints.preset.999.click` -> `cheat.skills.set`
- `f7.crafting.skillReset.click` -> `cheat.skills.reset`

The preset source uses invariant integer formatting and closure-safe handlers.

Unsupported level/XP/free-crafting/workbench placeholders remain handler-free.

`Send-CheatCommand` now rejects both unsupported mutation actions before native publication:

- `cheat.skills.set` -> `SKILL_POINTS_UNSOLVED`
- `cheat.skills.reset` -> `SKILL_RESET_UNSOLVED`

The canonical registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:

- real registry import: 55 unique actions
- lifecycle fixture: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- prohibited mutation scan: clean

The lifecycle fixture remains in the user's temporary reconstructed workspace and is not independently source-audited from Drive in this pass.

## G2C source inventory — Combat & AI

`Render-CombatAIPage` currently has exactly 12 raw `.Add_Click(...)` source registration sites and zero `Register-SafeUiEvent` sites.

Only one is a real canonical action:

- Easy Parry -> `cheat.parry.toggle`

The other 11 raw registration sites are disabled unsupported placeholders whose handlers only report unsupported status:

1. Player Damage multiplier loop
2. Enemy Damage multiplier loop
3. Critical Chance loop
4. Attack Speed
5. Super Knockback
6. Freeze Enemy AI
7. Disable Enemy Aggro
8. Kill Enemies in Radius
9. Despawn Enemies in Radius
10. Boss Health multiplier loop
11. Boss Damage multiplier loop

Those placeholder handlers should be removed rather than assigned fake action identities.

Canonical `cheat.parry.toggle` state:
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

Current `Send-CheatCommand` still maps `combat.parry` / `cheat.parry.toggle` to the native action publication path. G2C should add an explicit fail-closed rejection for both aliases before publication.

## Remaining G2 raw source counts

After G2B:
- Combat / AI: 12
- World / Camera: 9
- Building / Entities: 3

Total remaining G2 raw source sites: 24.

Responsive migration remains deferred.

# CODE-0042G2A — Inventory & Items event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 4e025f56061882412289b3b815f967e541606143ed5c914de73aa5ae03f55837
Current admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G2A EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G2A

`Render-InventoryItemsPage` now contains:

- raw `Register-SafeUiEvent`: 0
- raw `.Add_Click(...)`: 0

Canonical Inventory EventIds:

- `f7.items.reroll.click` -> ACTION -> `cheat.item.reroll`
- `f7.items.spawn.category.changed` -> UI_ONLY
- `f7.items.spawn.search.changed` -> UI_ONLY

The category/search handlers preserve their closure behavior with `GetNewClosure()`.

The four unsupported placeholders have no event handlers:

- Duplicate Item
- Repair Item
- Repair All
- Auto-Sort

The separate unsupported controls for Auto-Loot Aura, Clear Backpack, and Spawn Item also remain disabled/presentation-only.

Registry count remains 55. `cheat.item.reroll` remains canonically disabled/unqualified; `Register-AdminActionEvent` therefore keeps the reroll control fail-closed even if local pointer/capability diagnostics suggest a candidate item pointer.

G1 closure remains intact.

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

## Next target: Crafting / Progression

`Render-CraftingProgressionPage` has exactly 3 remaining raw source-level registrations:

1. APPLY SKILL POINTS
   - dispatches `cheat.skills.set`
2. Skill-point preset loop
   - one source registration site creates 4 runtime buttons: 10 / 50 / 114 / 999
   - dispatches `cheat.skills.set`
3. FREE SKILL RESET
   - dispatches `cheat.skills.reset`

Current canonical registry state:

`cheat.skills.set`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

`cheat.skills.reset`
- enabled: false
- evidenceStatus: `UNSOLVED`
- backend: `NONE`
- runtimeMode: `UNAVAILABLE`
- authority: `unknown`
- risk: `mutation`

Therefore G2B must preserve canonical disabled state even if `Get-AdminCapabilities` reports `skillPoints` or `skillReset` as executable.

## Dispatch defense-in-depth

Current `Send-CheatCommand` has no explicit hard rejection for `cheat.skills.set` or `cheat.skills.reset`.

It relies on the capability model before native command publication.

Because the canonical registry says both actions are disabled / backend NONE / UNSOLVED, G2B should add explicit fail-closed rejection branches before publication. This prevents a programmatic/direct call from bypassing UI canonical gating if the capability map becomes optimistic.

This is a narrow safety hardening for these two unsupported mutation actions, not a new backend.

## Remaining G2 raw source counts

- Crafting / Progression: 3
- Combat / AI: 12
- World / Camera: 9
- Building / Entities: 3

Total remaining G2 raw source sites after G2A: 27.

Responsive migration remains deferred.

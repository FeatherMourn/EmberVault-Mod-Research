# CODE-0042G3B — Settings / Developer event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: c044fe4bab992fa776eddd9b2e733365f0f3436a9ab7c80e269d657830703ab7
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3B EVENT MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3B

`Render-SettingsDevPage` now has:

- raw `.Add_Click(...)`: 0
- raw `Register-SafeUiEvent`: 0

Canonical event definitions:

- `f7.settings.subnav.presets.click` — UI_ONLY
- `f7.settings.subnav.diagnostics.click` — UI_ONLY
- `f7.settings.panicReset.click` — ACTION -> `cheat.survival.disable_all`
- `f7.settings.hotkeys.save.click` — UI_ONLY
- `f7.settings.preferences.apply.click` — UI_ONLY

The Role Presets and Native Diagnostics subnav handlers preserve `Clear-AdminContent` before rendering their target subview.

The Panic Reset handler is now truth-preserving:
- it routes through canonical `cheat.survival.disable_all`;
- canonical binding keeps the button disabled because the action remains disabled / UNSOLVED / backend NONE / runtime UNAVAILABLE;
- if invoked directly, the handler reports the returned failure and does not claim that Vanilla state was restored.

The Save Keybindings and Apply Preferences handlers use closure-safe handlers and remain local Architect configuration persistence rather than gameplay AdminActions.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:

- Settings/Developer raw `.Add_Click`: 0
- raw `Register-SafeUiEvent`: 0
- Panic Reset canonical gating preserved
- failed Panic Reset reports returned failure only
- keybinding/preference handlers closure-safe
- real registry import: 55 unique
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- G1/G2/G3A closure preserved
- prohibited mutation scan: clean

The temporary lifecycle fixture remains in the user's reconstructed local workspace and is not independently source-audited from Drive in this pass.

## G3C source inventory — Multiplayer / Quests

`Render-MultiplayerQuestsPage` currently contains exactly 4 raw `.Add_Click(...)` source sites:

1. global quest-quarantine toggle
2. category-filter loop
3. per-quest quarantine toggle
4. per-quest mark-complete/reset toggle

All four write only Architect-local state/preferences or rerender UI. No source evidence shows these handlers modifying Enshrouded quest state, multiplayer authority, or quest replication.

### Truthfulness issue

Current page copy overstates the behavior of the local tracker flag:

- title/subtitle say it protects storyline progression from remote server triggers;
- badge says `[PROTECTED] QUEST PROGRESSION QUARANTINE: ACTIVE`;
- hint says remote co-op completions are blocked;
- Home telemetry says `QUARANTINE: ACTIVE/OFF`.

Source search shows `quest_quarantine_enabled` is only:
- initialized/loaded/saved as an Architect preference;
- displayed in Home and the quest page;
- toggled by the quest page.

No runtime consumer was found that blocks Enshrouded quest synchronization or remote progression events.

Therefore G3C should migrate the 4 event families as UI_ONLY local tracker operations and correct the UI copy to explicitly say LOCAL TRACKER ONLY / no in-game quest-sync effect.

This is a source-truthfulness correction, not gameplay proof and not a quest backend implementation.

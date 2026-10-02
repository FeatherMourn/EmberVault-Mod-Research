# CODE-0042G3A — Role Presets event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 030cf856b4632b5f45dbb8cb126f725775050186c80227555e58cdbd6bd53132
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3A CORE MIGRATION / ONE FAIL-CLOSED PRESENTATION GAP / NO RUNTIME CLAIM

## Source-verified G3A

`Render-RolePresetsPage` now contains:

- raw `.Add_Click(...)`: 0
- raw `Register-SafeUiEvent`: 0

Canonical preset Apply bindings use:

`f7.presets.apply.<presetId>.click -> admin.preset.apply`

with:
- Page = `Presets`
- LifetimeScope = `PAGE`

Custom preset save is UI-only:

`f7.presets.save.click`

and the save path performs:

`Clear-AdminContent`
then
`Render-RolePresetsPage`

so the page does not append a duplicate control tree on refresh.

`Invoke-ArchitectPreset` now checks `admin.preset.apply` at the shared helper boundary and returns:

`PRESET_APPLY_UNAVAILABLE: canonical preset orchestration is disabled.`

before dispatching child actions when the canonical action is disabled.

`Send-CheatCommand "admin.preset.apply"` also rejects before native publication.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Remaining G3A gap

The migration correctly refuses to invent an EventId when a preset has no stable non-empty `id`.

However the current code does not explicitly disable that malformed preset's Apply button.

Current shape:

```powershell
$btnApply = New-Button ...
$btnApply.Tag = $p
$presetId = [string]$p.id
if (-not [string]::IsNullOrWhiteSpace($presetId)) {
    Register-AdminActionEvent ...
}
$pnl.Controls.Add($btnApply)
```

For a missing/blank preset id:
- no handler is registered;
- no fallback EventId is invented;
- but the button can remain visually enabled because canonical binding never runs.

This is not a mutation bypass, but it violates the requested fail-closed presentation rule and can present a clickable-looking dead control.

Required repair:
- in the missing-id branch, set `Enabled = $false`;
- use disabled styling consistent with other unsupported controls;
- add a truthful tooltip/accessibility reason if available;
- do not invent an EventId or ActionId.

No registry/source architecture change is required.

## Test provenance

Reported by user/Codex:
- real registry import: 55 unique
- lifecycle fixture: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- prohibited mutation scan: clean

The temporary lifecycle fixture remains local to the reconstructed workspace and is not independently source-audited from Drive in this pass.

## Next sequence

Close the missing-id fail-closed presentation gap first with a tiny G3A1 repair.

Then proceed to G3B `Render-SettingsDevPage`, which currently has 5 raw `.Add_Click(...)` sites:
- Role Presets subnav — UI_ONLY
- Native Diagnostics subnav — UI_ONLY
- Panic Reset — ACTION -> `cheat.survival.disable_all`
- Save Keybindings — UI_ONLY/local config persistence
- Apply Preferences — UI_ONLY/local config persistence

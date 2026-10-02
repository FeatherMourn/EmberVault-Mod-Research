# CODE-0042G3F — Blueprint Browser audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 9c7436572ebd1f9185d283d63e52e44482b36f6509d02d7b9b3e2dc3851ffbc3
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3F BLUEPRINT BROWSER MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3F

`Show-BlueprintBrowser` now uses canonical shared event registration for all Browser events.

DIALOG EventIds:
- `f8.blueprints.openFolder.click`
- `f8.blueprints.close.click`
- `f8.blueprints.selection.changed`
- `f8.blueprints.filter.text.changed`
- `f8.blueprints.filter.category.changed`
- `f8.blueprints.escape.keyDown`

DETAIL EventIds:
- `f8.blueprints.detail.select.click`
- `f8.blueprints.detail.delete.click`

Current source contains no raw:
- `Register-SafeUiEvent`
- `.Add_Click(...)`
- `.Add_KeyDown(...)`

inside `Show-BlueprintBrowser`.

The inspector removes only `Blueprint Library` + `DETAIL` active bindings before rebuild.

After the modal dialog closes, active `Blueprint Library` DIALOG/DETAIL bindings are removed and the Browser-owned scriptblock captures are cleared:
- `$script:loadBlueprintsFromDisk`
- `$script:applyBpFilter`
- `$script:renderBlueprintDetails`

## Truthfulness

The old placement claim has been removed.

The select button now says:
`SELECT BLUEPRINT (LOCAL)`

Selection:
- sets `$script:selectedBlueprint`
- updates local status/HUD only
- explicitly states runtime placement is not wired from the dialog
- does not call gameplay/native dispatch or world mutation

Delete fails closed when `FilePath` is blank, and reports a missing-on-disk file without claiming deletion success.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:
- raw `Register-SafeUiEvent`: 3 -> 0
- raw `.Add_Click`: 4 -> 0
- raw `.Add_KeyDown`: 1 -> 0
- lifecycle fixture: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- prohibited mutation scan: clean
- source-consolidation catalog preserved

No runtime/gameplay proof is established.

## Pre-G4 finding

The product/event migration slices are now source-clean, but `Get-F7DirectEventAudit` is still narrower than the actual event surface.

Current implementation:
- only searches a fixed function list;
- only counts `Register-SafeUiEvent` and `.Add_Click(...)`;
- omits helper/detail functions such as `Update-CodexDetails` and `Update-WaypointDetails`;
- cannot detect direct `.Add_TextChanged`, `.Add_KeyDown`, `.Add_FormClosing`, `.Add_SelectedIndexChanged`, `.Add_ValueChanged`, or other `Add_*` event registrations.

Therefore G4 should harden the audit itself and run repeated 11-page lifecycle traversal before responsive-layout work begins.

# CODE-0042G3E — Map / Wayfinder audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 20ad682518eed8a38dcfcaaac6d5ba277c7179f91a974512041d8a3f2e0b0b7e
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3E WAYFINDER MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3E

The Current Drive runtime matches the user-reported overlay SHA-256:

`20ad682518eed8a38dcfcaaac6d5ba277c7179f91a974512041d8a3f2e0b0b7e`

`Update-WaypointDetails`
- raw `.Add_Click(...)`: 0
- raw `.Add_TextChanged(...)`: 0
- raw `Register-SafeUiEvent`: 0
- canonical `Register-F7UiEvent`: 2

`Render-MapWayfinderPage`
- raw `.Add_Click(...)`: 0
- raw `.Add_TextChanged(...)`: 0
- raw `Register-SafeUiEvent`: 0
- canonical `Register-F7UiEvent`: 10

Canonical Wayfinder EventIds:

PAGE
- `f7.wayfinder.folder.selection.changed`
- `f7.wayfinder.waypoint.selection.changed`
- `f7.wayfinder.search.text.changed`
- `f7.wayfinder.save.click`
- `f7.wayfinder.addWaypoint.open.click`
- `f7.wayfinder.addFolder.open.click`

DETAIL
- `f7.wayfinder.detail.notes.changed`
- `f7.wayfinder.detail.delete.click`

DIALOG
- `f7.wayfinder.dialog.waypoint.save.click`
- `f7.wayfinder.dialog.waypoint.cancel.click`
- `f7.wayfinder.dialog.folder.create.click`
- `f7.wayfinder.dialog.folder.cancel.click`

The old undefined scriptblock helper references are gone:
- `$script:saveWaypointsToDisk`
- `$script:refreshFolders`
- `$script:refreshWaypoints`

The implementation now uses concrete local helpers:
- `Save-WaypointsFile`
- `Update-WaypointFolders`
- `Update-WaypointsList`

Teleport remains disabled and handler-free.

The local Wayfinder remains a local JSON/UI feature; this audit establishes no Enshrouded teleport or transform authority.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:
- Wayfinder raw direct events: 11 -> 0
- 12 canonical EventIds
- deterministic DETAIL/DIALOG pruning
- Save File canonical UI binding
- malformed waypoint-id Delete fail-close
- Teleport disabled/unbound
- stable definitions contain no live Control references
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- source-consolidation catalog preserved
- prohibited direct mutation scan: PASS
- repeated Home traversal: static lifecycle invariants PASS; full runtime traversal still requires WinForms harness

No runtime/gameplay proof is established.

## G3F source inventory — Blueprint Browser

`Show-BlueprintBrowser` currently has exactly 8 direct registration sites:
- 3 raw `Register-SafeUiEvent`
- 4 raw `.Add_Click(...)`
- 1 raw `.Add_KeyDown(...)`

The dialog is opened from the F8 BLUEPRINTS workspace, so the next slice should preserve F8 product identity even though it uses the shared event registry helpers.

The four click sites are:
- Open Folder
- Close
- blueprint Select/Equip
- Delete

The three SafeUi sites are:
- blueprint list selection
- filter text
- category filter

The KeyDown site closes the dialog on Escape.

### Truthfulness issue

Current blueprint Select/Equip handler:
- only assigns `$script:selectedBlueprint`
- updates UI/status
- closes the dialog

Current source contains no other consumer of `$script:selectedBlueprint`.

Therefore the dialog currently overstates behavior with:
- `EQUIP TO ARCHITECT'S WAND`
- `Click in world to place!`

G3F should relabel this as a LOCAL BLUEPRINT SELECTION and explicitly state that runtime placement is not wired from this dialog.

### Lifecycle issue

The blueprint inspector repeatedly clears/rebuilds `$pnlInspect`, so detail controls need a narrow DETAIL binding cleanup like Codex/Wayfinder.

The modal form also needs DIALOG binding cleanup after `ShowDialog()` returns.

No registry or gameplay backend changes are required.

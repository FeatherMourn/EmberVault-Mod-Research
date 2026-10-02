# CODE-0042G3D — Codex event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 9dcc3d94cca1eaa108ba4475b28c318c98694bc6f55fd8e59172a6d438febf3f
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3D CODEX MIGRATION / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3D

`Update-CodexDetails`:
- raw `.Add_Click(...)`: 0
- raw `Register-SafeUiEvent`: 0

`Render-CodexWikiPage`:
- raw `Register-SafeUiEvent`: 0
- raw `.Add_Click(...)`: 0

Fixed PAGE EventIds:
- `f7.codex.results.selection.changed`
- `f7.codex.search.text.changed`
- `f7.codex.category.changed`
- `f7.codex.view.player.click`
- `f7.codex.view.developer.click`

Fixed DETAIL UI EventIds:
- `f7.codex.detail.wiki.click`
- `f7.codex.detail.copyCommand.click`

Dynamic canonical ACTION EventIds:
- `f7.codex.player.action.<ActionId>.click`
- `f7.codex.developer.action.<ActionId>.click`

Both Player and Developer command controls:
- resolve canonical registry definitions;
- render disabled/unavailable when missing, unregistered, or disabled;
- bind enabled canonical actions with `Register-AdminActionEvent`;
- dispatch through `Dispatch-AdminCommand`;
- report returned state/message rather than unconditional success.

The detail rebuild now removes active bindings only when:
- `Page == "Codex & Commands"`
- `LifetimeScope == "DETAIL"`

before clearing/rebuilding the detail panel.

Stable event definitions are retained for audit history.

The stale fixed-count Codex source comment is now count-free:
`Index canonical admin actions into the searchable catalog`.

Registry remains 55 / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:
- real importer: 55 unique
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- G1/G2/G3A/G3B/G3C closure preserved
- prohibited mutation scan: clean

No runtime/gameplay proof is established.

## G3E source inventory — Map / Wayfinder

Current remaining direct registrations:

`Update-WaypointDetails`
- 1 direct `.Add_TextChanged(...)`
- 1 direct `.Add_Click(...)`

`Render-MapWayfinderPage`
- 3 raw `Register-SafeUiEvent`
- 6 raw `.Add_Click(...)`

Total source-level direct registrations across the Wayfinder slice: 11.

All are Architect-local waypoint UI/state/persistence operations.
The visible Teleport control is disabled and has no handler.

### Two source issues to fix during G3E

1. The detail pane is rebuilt with `$pnlDetail.Controls.Clear()` without DETAIL binding cleanup. G3E should mirror the narrow Codex DETAIL cleanup for `Page = "Map & Wayfinder"` and `LifetimeScope = "DETAIL"`.

2. Add Waypoint / Add Folder dialog save handlers call:
- `$script:saveWaypointsToDisk`
- `$script:refreshFolders`
- `$script:refreshWaypoints`

No assignment for those scriptblocks was found in the current source. Existing concrete helpers already exist:
- `Save-WaypointsFile`
- `Update-WaypointFolders`
- `Update-WaypointsList`

G3E should use those concrete helpers directly instead of relying on undefined scriptblock globals.

### Additional truthfulness / usability issue

The waypoint detail empty-state says:
`Select a waypoint to view coordinates & fast travel.`

Teleport is explicitly unsupported/disabled, so G3E should change that copy to local waypoint details/coordinates/notes and not imply working fast travel.

The visible `Save File` button currently has no handler. G3E should bind it as a UI_ONLY local persistence action.

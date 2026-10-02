# CODE-0042G4A — F7 audit-boundary repair review

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 9a058c3941a1b5fbe0aa66088cf84cc340e8dce0fd3d7ca6adf81ad9ee107116
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: SOURCE-VERIFIED STATIC ZERO-GAP AUDIT REPAIR / WINFORMS TRAVERSAL STILL SKIPPED / NO GAMEPLAY CLAIM

## Source-verified G4A

The runtime contains exactly one semantic F7/F8 boundary comment:

`# F7 EVENT AUDIT BOUNDARY: F8 SHELL BEGINS`

It is placed immediately before the existing F8 form-shell direct registrations.

`Get-F7DirectEventAudit` now:
- parses PowerShell tokens and AST;
- resolves the boundary only from a parser Comment token whose trimmed text exactly matches the semantic marker;
- fails closed unless exactly one matching comment token exists;
- uses the comment token `Extent.StartOffset` as the F7 audit boundary;
- reports `boundaryLine`, `boundaryMarkerCount`, and `boundaryKind`.

The old raw source `IndexOf(...)` boundary lookup is gone.

Current source reports the semantic marker at line 5591 and leaves the two F8 form-shell direct registrations after that boundary.

## Reported static audit result

User/Codex reported:

- boundaryMarkerCount = 1
- boundaryKind = COMMENT_TOKEN
- boundaryLine = 5591
- fullF7 = 0
- legacySafeUiCount = 0
- directAddEventCount = 0
- sites.Count = 0

The fixture also verifies that marker text can occur elsewhere in source without being mistaken for the semantic boundary, because only Comment tokens are accepted.

## Static event-definition instrumentation

`Get-F7ActionBindingAudit` continues to expose:

- stableDefinitionControlReferences
- stableDefinitionHandlerReferences
- activeShellBindings
- activePageBindings
- activeDetailBindings
- activeDialogBindings

Stable definitions remain metadata-only by construction.

## Test provenance

Reported by user/Codex:

- PowerShell parse: PASS
- lifecycle/static fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- registry unchanged: 55 / 17 / 38

The requested 11-page x3 WinForms traversal was explicitly not available and remains:

`SKIPPED_NO_WINFORMS_HARNESS`

Therefore this pass establishes source/static zero-gap only. It does not establish repeated live WinForms page lifecycle proof or gameplay/runtime behavior.

## Next responsive target

The F7 shell is already structurally responsive at the outer level:

- sizable form
- docked header/main/nav/body
- `adminContent` is a top-down `FlowLayoutPanel`
- `Resize-AdminPageChildren` expands top-level non-label page children to the usable width

The remaining responsiveness problem is inside page renderers, where cards and their child controls still use fixed pixel X/Y/W/H layout.

`Render-DashboardPage` is an appropriate first migration slice because:
- it is bounded;
- it exercises headers, status cards, a multi-column preset row, a multi-button action row, a hotkey strip, and a full-width action;
- it can establish the reusable responsive-card/grid pattern before touching denser admin pages.

Recommended next slice: CODE-0042G5A — responsive foundation + Home page only.

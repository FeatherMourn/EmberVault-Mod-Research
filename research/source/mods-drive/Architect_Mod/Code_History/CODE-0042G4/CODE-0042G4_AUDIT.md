# CODE-0042G4 — Full F7 zero-gap audit review

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 5208600eb5e4261f1edfdee58f3f35f3e76ace59395ecd229d79bd92a8297e24
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: G4 AUDIT INSTRUMENTATION BUG FOUND / ZERO-GAP RESULT NOT YET VALID / NO RUNTIME CLAIM

## What is source-verified

The G4 source does implement:
- AST-based `Register-SafeUiEvent` detection;
- generic direct `.Add_<Event>(...)` detection;
- structured site reporting;
- stable-definition Control/Handler reference metrics;
- active SHELL/PAGE/DETAIL/DIALOG counts.

The user/Codex-reported standard static tests passed, and the requested 11-page x3 WinForms traversal was correctly reported as skipped rather than passed.

## Critical boundary defect

`Get-F7DirectEventAudit` currently computes the source boundary with:

`$ast.Extent.Text.IndexOf('# F8 BUILDER HUD - THE CREATIVE WORKSPACE OVERLAY')`

However that exact marker text also appears earlier inside `Get-F7DirectEventAudit` itself as a string literal.

Current source occurrence order:

1. line ~369 — marker text inside the audit function string literal
2. line ~5604 — actual F8 banner comment

`IndexOf(...)` therefore selects the earlier string-literal occurrence.

That causes the comprehensive audit to stop near the audit function itself and skip nearly the entire F7 implementation.

Therefore the reported:

- `fullF7 = 0`
- `legacySafeUiCount = 0`
- `directAddEventCount = 0`

does NOT currently prove pre-F8/F7 zero-gap coverage.

## Independent source sanity check

A separate plain-source scan to the actual F8 banner finds only:
- canonical-registration infrastructure references; and
- two raw F8 form-shell registrations immediately before the banner:
  - `$form.Add_KeyDown(...)`
  - `$form.Add_FormClosing(...)`

Those two controls belong to the F8 Builder HUD shell, not F7.

This is encouraging evidence that the migrated F7 surface is likely clean, but it is NOT a substitute for the intended AST audit.

## Required repair

Add an explicit unique comment boundary immediately before the F8 form-shell registrations, for example:

`# F7 EVENT AUDIT BOUNDARY: F8 SHELL BEGINS`

Then locate that boundary from parser COMMENT TOKENS, not by raw source `IndexOf`.

The audit must fail closed when:
- the boundary comment is absent;
- more than one matching boundary comment exists.

After repair, rerun the comprehensive static audit.

Expected F7 result:
- `fullF7 = 0`
- `legacySafeUiCount = 0`
- `directAddEventCount = 0`
- `sites.Count = 0`

The 11-page x3 WinForms traversal remains `SKIPPED_NO_WINFORMS_HARNESS` unless a real harness is actually available.

Responsive-layout work remains blocked until this audit-boundary repair is complete.

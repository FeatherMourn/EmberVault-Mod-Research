# CODE-0042G3D0 — Global Canonical Enabled Gate audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 469f7584d25e6a14ba29ec55aa047af196d13b5b1b375f36f79cc039a57e73a3
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED COMMAND-BOUNDARY HARDENING / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3D0

`Send-CheatCommand` now applies a generic canonical enabled-state gate after alias/native-action resolution and before:
- capability-based execution approval,
- pending-command creation,
- native command publication.

It resolves the canonical definition from the requested ActionId, then the mapped native ActionId when needed. A canonical definition with `enabled != true` returns:

`CANONICAL_ACTION_DISABLED: <commandId>: <failureReason>`

with no pending command and no publication.

Existing detailed fail-closed branches remain earlier in the function, preserving specific provenance such as:
- ADM-TEST-0002
- PRESET_APPLY_UNAVAILABLE
- AOB_SCANNER_UNSOLVED
- skill/parry/world/building-specific unresolved errors.

`Dispatch-AdminCommand` now gates immediately after the existing teleport special-case and before every publisher/backend route.

It rejects:
- unregistered actions -> `CANONICAL_ACTION_UNREGISTERED`
- registered disabled actions -> `CANONICAL_ACTION_DISABLED: <commandId>: <failureReason>`

The gate occurs before:
- cheat-correlation publication,
- player discovery publication,
- GameSettings observer publication,
- Entity Inspector publication,
- item lookup,
- backend adapter invocation.

This closes the prior registered-disabled and unknown-`cheat.*` prefix bypass at the dispatcher boundary.

Registry remains unchanged at 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:
- real importer: 55 unique
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- G1/G2/G3A/G3B/G3C raw closure preserved
- prohibited mutation scan: clean
- command-boundary logic statically verified

No runtime/gameplay proof is established.

## G3D Codex source inventory

The Codex has 9 remaining raw source registration sites across two functions.

`Update-CodexDetails`:
- 4 direct `.Add_Click(...)`
  1. Player command execution
  2. Open official wiki
  3. Developer command dispatch
  4. Copy command

`Render-CodexWikiPage`:
- 5 raw `Register-SafeUiEvent`
  1. results selection
  2. search text
  3. category filter
  4. Player view
  5. Developer view

Important lifecycle detail:
`Update-CodexDetails` clears and rebuilds the detail panel repeatedly without calling `Clear-AdminContent`. Dynamic command EventIds therefore need detail-scope binding cleanup before the detail control tree is replaced, otherwise stale active bindings can accumulate.

Important dispatch detail:
The Player command button currently uses `Send-CheatCommand` for arbitrary canonical AdminActions. The generic F7 dispatcher is `Dispatch-AdminCommand`; G3D should normalize both Player and Developer Codex command buttons to that canonical dispatcher.

## G3D target

- migrate all 9 raw sites to canonical F7 event registration;
- use PAGE scope for the 5 main Codex controls;
- use a bounded DETAIL scope for controls rebuilt by `Update-CodexDetails`;
- remove stale detail bindings before clearing/rebuilding the detail panel;
- canonicalize dynamic command controls by ActionId;
- disabled canonical actions remain visibly unavailable;
- enabled canonical actions remain routable through `Dispatch-AdminCommand`;
- local wiki/clipboard operations remain UI_ONLY;
- no registry changes;
- no responsive-layout work yet.

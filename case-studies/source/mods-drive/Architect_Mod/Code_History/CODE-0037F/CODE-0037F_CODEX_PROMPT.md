# CODE-0037F — Unify F7 Admin into One Canonical Action Registry

Working tree:

`H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit`

Target Enshrouded build: `1076226`.

Do **not** modify or replace:

`Architect_Mod\Current`

This task is an approved architecture cleanup required to unblock F7 truthfulness qualification.

## Problem to fix

The current F7 Admin architecture has two competing sources of truth:

1. `runtime\admin_action_registry.json`
   - currently contains only about 20 diagnostic/item actions
2. a larger compatibility/action ledger inside `runtime\ArchitectRuntime.ps1`
   - contains or implies mutation routes such as Health, Mana, Movement, Auto Loot, Free Craft, Teleport, and others

Later in startup, `$adminCommandRegistry` is overwritten by the JSON catalog, which means the full F7 UI/action surface cannot be bound to one canonical action definition.

This blocks:
- stable action-ID -> UI-control binding
- truthful enable/disable behavior
- route consistency
- behavior-based F7 truthfulness tests

## Objective

Make **one canonical registry** own the full F7 Admin action surface.

Preferred canonical source:

`runtime\admin_action_registry.json`

After this task, every executable F7 Admin control must resolve to exactly one canonical action definition from that registry.

The registry must include both:
- supported/implemented actions
- unsupported/unresolved actions

Unsupported actions must remain visible only if the current UI intentionally exposes them, but they must be explicitly unavailable/fail-closed.

This task must **not** enable new gameplay functionality.

---

# Non-negotiable rules

1. Do not invent action IDs.
2. Do not infer action IDs from labels/button text.
3. Recover IDs only from existing production command strings, dispatch routes, registry entries, or canonical action metadata.
4. Do not create a second registry.
5. Do not keep two independent authoritative compatibility ledgers.
6. Do not enable any action that is currently unsupported/unproven.
7. Preserve all current fail-closed behavior.
8. Do not add new Enshrouded offsets/signatures/pointers/APIs.
9. Do not alter `Architect_Mod\Current`.
10. Do not package a runtime candidate unless every authoritative offline suite is green.
11. Compilation/offline tests are not runtime proof.

---

# Part A — inventory the existing action surface before editing

Build an exact inventory of every current F7 executable action.

Inspect at minimum:

- `runtime\admin_action_registry.json`
- `runtime\ArchitectRuntime.ps1`
- F7 UI construction helpers
- command-dispatch helpers
- `Send-CheatCommand`
- `Send-AdminCommand`
- `Invoke-*` action handlers
- native command/action routing
- backend capability publication
- existing action metadata/compatibility structures
- truthfulness tests

For each executable F7 action record:

- exact current action/command ID
- display name
- category/page
- current backend type
- current production route
- current readiness/capability gate
- current UI control location/helper
- current support state:
  - supported
  - readiness-gated
  - unsupported
  - unresolved
- whether the ID already exists in `admin_action_registry.json`
- whether the route currently uses a literal string elsewhere

Do not edit until this inventory is complete.

STOP if an executable action cannot be tied to an exact existing production route without guessing.

---

# Part B — define the canonical registry contract

Expand `runtime\admin_action_registry.json` so it can represent the entire existing F7 action surface.

Use the existing schema wherever possible.

If additional fields are required, extend the schema minimally and update loader/tests together.

The canonical action record must be able to represent, using existing project terminology where possible:

- canonical action ID
- label/display metadata
- category
- backend type
- route/handler identity
- support/readiness state
- required capability/readiness flags
- unavailable reason
- authority/risk metadata if already part of the current model
- readback/revert requirements where applicable
- whether the action is mutation/read-only
- any existing evidence/status metadata already used by F7

Do not put raw memory addresses, signatures, or guessed pointers into the UI registry unless the existing architecture already does so. Build-specific technical details belong in their existing backend/build-profile layers.

The registry should describe **what action exists and what backend/readiness contract it uses**, not duplicate low-level patch implementation details.

---

# Part C — migrate the larger PowerShell compatibility ledger

The larger compatibility ledger in `ArchitectRuntime.ps1` must stop being an independent authority.

For each entry:

- map it to the canonical registry action
- preserve current support/readiness state exactly
- preserve existing unavailable reasons where useful
- preserve current backend route
- preserve current safety gating

After migration, one of these is acceptable:

A. remove the duplicate ledger entirely and derive runtime metadata from the canonical JSON registry

OR

B. keep a runtime cache/object only if it is **derived exclusively from the canonical registry at load time** and cannot diverge independently

Not acceptable:
- two manually maintained lists
- JSON for some actions and PowerShell literals for others
- fallback to hidden action definitions outside the canonical registry

Add tests proving there is one authoritative source.

---

# Part D — preserve exact current feature states

The migration must preserve current behavior.

## Teleport

Must remain unavailable/fail-closed.

Canonical registry should represent it explicitly as unsupported/unavailable.

Required:
- UI disabled/unavailable
- dispatch rejected/not-proven
- no coordinate write
- no `WritePlayerCoordinates`
- no queued-success fallback
- no guessed local-player transform

## Free Craft

Approved native direct-patch candidate.

Canonical registry must represent the actual direct-patch route and readiness contract.

Required:
- mutation backend readiness
- Free Craft patch readiness
- no hook-framework dependency
- no raw fallback write
- state becomes enabled only after actual apply/readback in production runtime

Offline registry/UI tests may validate route/gating only; they must not claim gameplay proof.

## Auto Loot

Current approved state:
- vanilla/resource composition path
- canary scope
- gather tuning disabled
- no simulated E-key/timer path

Registry must not imply full-scope runtime proof.

## Always Flying

Must remain unavailable.

## Infinite Glider Stamina

Must remain unavailable as a truthful infinite-stamina feature.

The prior `0x39E73C` behavior was user-disproven for that semantic.

## Health / Mana / Stamina / God / other unresolved player mutations

Do not enable them merely because they now exist in the registry.

If no approved ready backend exists:
- canonical action exists
- support/readiness remains unavailable/false
- UI remains disabled
- dispatch fails closed

## Other actions

Preserve every current production readiness state exactly.
This migration is architectural, not a feature activation pass.

---

# Part E — route all UI through canonical action definitions

After the registry covers the full action surface:

1. UI construction must resolve a canonical action definition.
2. The actual executable control must carry the canonical action ID as inert metadata, preferably `Control.Tag`.
3. Maintain one action-control map derived from canonical IDs:
   - action ID -> one or more controls
4. Event handlers must dispatch using that canonical action ID.
5. Remove duplicated literal action strings from UI/event code where the same ID is already canonical in the registry.
6. Do not infer IDs from labels.

If an action has multiple controls, all must bind to the same canonical ID and be explicitly enumerated.

Non-executable UI chrome must not be forced into the action map.

---

# Part F — canonical dispatcher

Unify dispatch lookup around the same canonical registry.

Required properties:

- incoming action ID must resolve to exactly one canonical action
- backend route comes from/through that canonical action definition
- unsupported action -> explicit rejected/not-proven result
- readiness false -> explicit rejected/not-ready result
- no implicit fallback backend
- no optimistic success
- no hidden literal route outside canonical registry
- current command lifecycle/ACK/history semantics preserved

Do not rewrite the working patch engine, native backend, bridge, or hook framework.

This task should change ownership/routing metadata, not reimplement feature backends.

---

# Part G — add registry integrity tests

Add tests that fail on:

- duplicate canonical action IDs
- executable UI route absent from registry
- canonical action with no valid backend/support classification
- enabled control without canonical action binding
- bound action absent from registry
- handler dispatch ID != bound canonical action ID
- literal action IDs in UI/handler layers outside the canonical registry where they should have been migrated
- unsupported action exposed as enabled
- implicit backend fallback
- registry/cache divergence

Also verify:

- every existing executable F7 action is represented
- diagnostic/read-only actions remain represented
- mutation actions are represented even when unsupported
- no action changed readiness merely due to migration

---

# Part H — rebuild F7 Truthfulness tests

Once the canonical registry and UI binding are complete, replace the 31 legacy source-pattern assertions one-for-one with behavior-based assertions.

For each old assertion provide:
- old assertion
- action/control it protected
- canonical action ID
- new behavior assertion
- why the safety property is equal or stricter

Truthfulness suite must validate:

1. every executable F7 control has canonical action binding
2. no enabled executable control is unbound
3. unsupported actions are disabled
4. unsupported direct dispatch rejects
5. supported/readiness-gated actions follow their actual capability state
6. Free Craft uses direct-patch readiness
7. Teleport remains fail-closed
8. Always Flying remains unavailable
9. Infinite Glider Stamina remains unavailable
10. Auto Loot remains canary/resource-path only
11. no simulated-E route exists
12. actual handler route matches bound canonical action ID

The suite must no longer depend on brittle source formatting such as specific nearby `$button.Enabled = $false` strings.

---

# Part I — compatibility and migration safety

Do not break existing saved/config/UI behavior unnecessarily.

If action IDs already exist in literal command routes, preserve those exact IDs as the canonical IDs.

Do not rename action IDs for cleanliness unless there is no existing stable ID. If a true conflict exists, STOP and report it rather than silently renaming.

If old registry entries and PowerShell ledger entries conflict:
- prefer actual current production route identity
- preserve the conflict in the report
- do not silently choose a new semantic meaning

---

# Part J — final qualification

After the last production/test edit:

1. run canonical-registry integrity tests
2. run F7 Truthfulness alone
3. require 100% green
4. run complete master suite
5. require 100% green
6. if production source changed, synchronize identity to:
   - version: `0.41.0`
   - buildId: `architect-v041-f7-canonical-registry-code0037f-20260919`
   - retain currently approved runtime mode
7. freeze source
8. rerun complete master suite once more after identity synchronization
9. only if fully green:
   - build DLL
   - package ZIP
   - verify nested ZIP count = 0
   - extract ZIP cleanly
   - rerun extracted-package verification
10. no source/test edits after the final green master run

If any authoritative test remains red:
- STOP
- do not package as qualified
- report exact remaining blocker

---

# Final deliverable

Return:

`CODE-0037F_qualification_report.md`

It must contain:

1. full pre-change F7 action inventory
2. old canonical registry coverage
3. migrated full canonical registry coverage
4. exact actions added to registry
5. exact PowerShell compatibility-ledger entries retired/derived
6. exact UI helpers changed
7. exact handler literal IDs removed/migrated
8. proof no action readiness state changed unintentionally
9. registry integrity test results
10. mapping of all 31 old truthfulness assertions to new behavior tests
11. F7 Truthfulness results
12. complete master suite breakdown
13. final version/buildId/mode
14. DLL SHA256 + byte size
15. ZIP SHA256 as one uninterrupted 64-character lowercase hex string + byte size
16. nested ZIP count
17. extracted-package verification results
18. explicit statement that `Architect_Mod\Current` was not replaced
19. runtime-test instructions only if every offline gate is green

Do not claim runtime proof from compilation or offline tests.

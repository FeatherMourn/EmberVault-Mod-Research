# CODE-0042G5B — Responsive Player audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 3a6ca587f2eef08c82d317a72e54433b76874ec178a84b904e8ae9bda4f9de88
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: RESPONSIVE PLAYER STRUCTURE PRESENT / SOURCE REGRESSIONS FOUND / GEOMETRY HARNESS SKIPPED / NO GAMEPLAY CLAIM

## What is source-verified

`Render-PlayerVitalsPage` was converted to the responsive-card/table model.

The current source preserves:
- fixed Player EventIds/ActionIds;
- dynamic `f7.player.survival.<Key>.click`;
- the existing fill-command handlers/status strings;
- native attribute/scaling reads;
- disabled/unbound unsupported attribute/scaling controls.

A byte-level comparison against the archived G5A1 source also confirms:
- `Render-DashboardPage` is unchanged by G5B;
- `Render-MobilityTravelPage` is unchanged by G5B.

Registry remains unchanged at 55 / 17 / 38.

## Geometry proof status

Responsive geometry validation remains:

`SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

No runtime claim is made about clipping, horizontal scrolling, or actual Player render geometry.

## Source regressions found

### 1. Player survival mass-enable gating was dropped

G5A1 had:

- `$canEnableAll = ($canHeal -and $canStam -and $canMana)`
- `$enableAllBtn.Enabled = $canEnableAll`
- disabled styling and tooltip when required capabilities were not active.

The G5B source creates the Enable All button but no longer reapplies this gating after `canHeal/canStam/canMana` are known.

This violates the layout-only requirement and must be restored.

### 2. Recovery row is structurally broken

G5B constructs recovery NumericUpDown controls inside a loop but never adds them to the recovery table.

The loop only adds each label:

`$recovery.Controls.Add($l, ...)`

and never adds `$n`.

It also does not retain `$numHpRec`, `$numStamRec`, or `$numManaRec`.

All three labels resolve to the same column expression, so the labels can collide in one cell.

Required repair:
- use explicit/nested responsive groups;
- restore all three numeric controls and NativeMemoryEngine values.

### 3. Zero Spell Cost presentation changed

G5A1 created the checkbox from `[NativeMemoryEngine]::ZeroSpellCost` and did not force it disabled.

G5B adds:

`$zero.Enabled=$false`

That is semantic/presentation drift in a layout-only pass.

Restore the pre-G5B checkbox state/presentation exactly; do not add a new handler.

### 4. Primary-vital text changed

G5A1 displayed:
- `Max HP`
- `Max Stam`
- no new `Mana refill` descriptor

G5B changes those group descriptors to:
- `Health refill`
- `Stamina refill`
- `Mana refill`

Restore the pre-G5B visible labels while retaining responsive layout.

### 5. Survival active-state logic drifted

G5A1 first used:

`$status -and [bool]$status.($c.Key)`

then, only if inactive:
- Auto Loot special read through `[NativeMemoryEngine]::IsAutoLootActive`
- otherwise `GetPatchStatus($c.Key)`

G5B removed the status-first path and Auto Loot special case, using only `GetPatchStatus`.

Restore the exact pre-G5B active-state calculation.

### 6. Survival badge presentation drifted

G5A1 preserved distinct unavailable/active badge presentation:
- BackColor
- TextAlign
- BorderStyle
- Cursor
- ON/OFF ForeColor
- disabled unavailable state
- tooltip reason

G5B drops several of those properties and uses a fixed OFF-like foreground color even when active.

Restore the pre-G5B badge presentation while keeping responsive row/table layout.

### 7. Alternating survival row presentation was lost

G5A1 alternated row background colors.
G5B creates transparent/default nested tables and drops that row distinction.

Restore the existing alternating row backgrounds in the responsive row container.

### 8. `New-F7ResponsiveTable` row-height contract is violated

The shared helper currently accepts:
- hashtable only for `Type='Percent'`;
- otherwise a numeric absolute row height.

G5B passes hashtables such as:

`@{Type='Absolute';Value=22}`

for the survival card row heights.

That is not a supported input shape for the current helper and can fail when it casts the hashtable to `[float]`.

Use numeric absolute row heights instead, e.g. `22` and `20`, or extend the helper only if that change is separately justified. For this repair, numeric row heights are preferred.

## Test provenance

Reported by user/Codex:
- PowerShell parse: PASS
- lifecycle/static fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- G4A zero-gap: PASS
- registry: 55 / 17 / 38
- no `[scriptblock]::Create`, `$listY`, or `$attrX` in Player
- geometry harness: SKIPPED_NO_WINFORMS_LAYOUT_HARNESS

Those tests did not detect the semantic/layout regressions above.

No gameplay/runtime behavior is established.

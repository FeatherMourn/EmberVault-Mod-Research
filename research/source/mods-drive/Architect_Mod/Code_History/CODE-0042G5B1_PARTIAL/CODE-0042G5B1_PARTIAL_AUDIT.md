# CODE-0042G5B1 — Player semantic-parity repair audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 68e8f9fd38bd7a5044f42fd9879191a454e7792bd64c2cc728205c1e9d9932b7
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: PARTIAL IMPLEMENTATION / ONLY ENABLE-ALL GATING LANDED / G5C BLOCKED

## Source verification

Current `Render-PlayerVitalsPage` differs from the archived G5B snapshot only in the Enable-All gating block.

The following G5B1 repair items are source-verified as present:

- `$canEnableAll = ($canHeal -and $canStam -and $canMana)`
- `$enableAllBtn.Enabled = $canEnableAll`
- exact disabled colors
- exact tooltip:
  `Survival overrides cannot be mass-enabled: required native hooks not active.`

## Required repairs still missing

1. Recovery controls are still broken:
   - no `$numHpRec`
   - no `$numStamRec`
   - no `$numManaRec`
   - numeric controls are created as `$n` but never added
   - label placement still uses `IndexOf` logic

2. Zero Spell Cost is still force-disabled:
   - `$zero.Enabled = $false`

3. Primary-vital labels still read:
   - `Health refill`
   - `Stamina refill`
   - `Mana refill`
   rather than the pre-G5B visible labels.

4. Survival state logic is still simplified:
   - no `$status`-first active-state lookup
   - no Auto Loot `IsAutoLootActive` special path
   - only `GetPatchStatus` is used

5. Survival badge presentation is still incomplete:
   - missing baseline BackColor/TextAlign/BorderStyle/Cursor parity
   - ON color is not restored

6. Alternating survival row background colors remain absent.

7. Survival row heights still use unsupported hashtable values:
   - `@{Type='Absolute';Value=22}`
   - `@{Type='Absolute';Value=20}`

8. Unsupported-control styling parity remains incomplete.

## Preserved

- responsive Player structure remains present
- fixed Player EventIds/ActionIds remain present
- dynamic `f7.player.survival.<Key>.click` remains present
- Home is unchanged from G5A1
- Mobility is unchanged
- registry remains 55 / 17 / 38

## Test provenance

User/Codex reported:
- PowerShell parse PASS
- lifecycle/static fixture PASS
- F7 truthfulness 53/53 PASS
- UI smoke 28/28 PASS
- UI errors 0
- CT catalog 224
- G4A zero-gap PASS
- geometry harness SKIPPED

These tests did not detect the remaining Player parity defects above.

No runtime/gameplay proof is established.

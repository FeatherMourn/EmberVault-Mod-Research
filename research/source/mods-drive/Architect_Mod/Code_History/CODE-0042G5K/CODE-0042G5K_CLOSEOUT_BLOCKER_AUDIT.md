# CODE-0042G5K — Independent closeout blocker audit

Date: 2026-09-21
Build: Enshrouded 1076226

Disposition:
`G5K closeout is BLOCKED pending one semantic repair.`

## Independently verified Current

- Length: 449765 bytes
- SHA-256: `0CCE15A6FC9C8DF2DDA6B40CE86809A1A72B5F5B962D905651C2981477EF5E48`

G5J baseline:
- Length: 449835 bytes
- SHA-256: `D510D65A3A25FB4080DC3BC466AD9D0736661FF0E2F3F291989721437F366EF8`

Registry:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

## Independent function diff

Exactly one top-level function differs between archived G5J and Current:

- `Render-RolePresetsPage`
  - before hash:
    `4F85385E794C0C487840103DEE28B390A9A3A273F093F6B1EDDF2069E55449E2`
  - current hash:
    `4DCF11B4DABC79F17DE8BD035AADA820A75BC9613EEC9B97B183D0D2BC6382B2`

Preset helpers are source-identical:
- `Load-ArchitectPresets`
- `Save-ArchitectPresets`
- `Invoke-ArchitectPreset`

Protected G5A–G5J renderers/helpers are source-identical under the same extractor.

## Blocker

The active responsive renderer changed the built-in WORLD EXPLORER fallback description.

G5J baseline:
`Shroud Immunity, Underwater Breathing, Cold Immunity, Infinite Stamina, 2.5x Movement Speed.`

G5K candidate:
`Shroud Immunity, Underwater Breathing, Cold Immunity, 2.5x Movement Speed.`

The phrase `Infinite Stamina` was dropped.

The G5K autonomous goal explicitly required the fallback definitions and descriptions to remain exact, so this is semantic drift rather than a layout-only difference.

Because the reported G5K parity fixture passed despite this change, the fixture must be hardened to compare exact active-AST fallback fields.

## Required repair

- Restore the exact WORLD EXPLORER description.
- Change no other product function.
- Harden TEMP parity to exact active-function fallback assertions.
- Rerun the full regression.
- Do not mark G5K closed until the corrected Current is independently verified.

No gameplay/runtime proof is established.

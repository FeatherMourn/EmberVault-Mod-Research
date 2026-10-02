# CODE-0042G5E — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of F7 `Render-CombatAIPage`.

Authoritative starting source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting identity:
- Length: 396725 bytes
- SHA-256: `8CEBE9F8B3C273005A433031399663C130187AA92B5BDFDEA8FE50905B762228`

Verified registry baseline:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Current Combat evidence:
- `Render-CombatAIPage` remains fixed-pixel.
- G2C previously reduced Combat to exactly one canonical action binding:
  `f7.combat.parry.toggle.click` -> `cheat.parry.toggle`.
- Unsupported Combat/AI placeholders are disabled and unbound.
- `cheat.parry.toggle` remains canonical-disabled / UNSOLVED / backend NONE / runtime UNAVAILABLE.
- `Send-CheatCommand` rejects both `combat.parry` and `cheat.parry.toggle` with `PARRY_UNSOLVED`.
- Combat/AI runtime authority remains unmapped/planned; G5E must not implement gameplay mechanisms.

Closed baselines to preserve:
- G5B Player
- G5C Mobility
- G5D Items & Progression

This goal gives Codex autonomous permission to iterate inside `Render-CombatAIPage` and TEMP-only verification infrastructure, returning only for genuine product/safety blockers.

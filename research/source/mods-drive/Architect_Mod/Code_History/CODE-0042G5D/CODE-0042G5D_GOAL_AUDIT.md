# CODE-0042G5D — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of the complete F7 `Items & Progression` page.

Authoritative start:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting SHA-256:
`0E856F05E1B079C5528B14783CB5C93391B962CDB650B4BC2D590D4B5DFDAC90`

Verified registry:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Scope:
- `Render-InventoryItemsPage`
- `Render-CraftingProgressionPage`

Preserved boundaries:
- item reroll remains canonical-disabled/unqualified
- skill set/reset remain canonical-disabled and direct-dispatch fail-closed
- item spawner mutation remains unsupported
- unsupported inventory/crafting/progression placeholders remain disabled and unbound
- category/search are UI_ONLY
- G5B Player and G5C Mobility are closed baselines and must remain source-identical
- H: remains absent
- no runtime/gameplay proof is implied

This goal gives Codex autonomous permission to iterate within the two renderers and TEMP-only verification infrastructure, with user handoff only for genuine product/safety blockers.

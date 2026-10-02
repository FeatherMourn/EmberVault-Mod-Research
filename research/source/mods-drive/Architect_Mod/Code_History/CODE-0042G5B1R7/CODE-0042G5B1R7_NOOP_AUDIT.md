# CODE-0042G5B1R7 — No-op / splice-guard audit

Date: 2026-09-21
Build scope: Enshrouded 1076226

Status: NO SOURCE CHANGE / UNIQUE SURVIVAL LOOP FOUND / FINAL SPLICE GUARD BLOCKED WRITE / G5C BLOCKED

## Verified source identity

Authoritative Current:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Synced Google Drive Current:
- Length: 367681 bytes
- SHA-256: `165ee6ed8a78460fa246ccd48a2c008823f3ae3f60f751aefd2056019ffe758e`

The Drive-backed snapshot matches the authoritative I: snapshot used by the prior pass.

## R7 result

Preflight succeeded:
- exact source identity matched;
- `Render-PlayerVitalsPage` was found;
- exactly one survival-row `ForStatementAst` candidate was found;
- candidate line was reported as 2642;
- old-loop hash was recorded.

The final AST-offset splice/write guard did not pass, so no write was performed.

## Current Player state

Already landed and preserved:
- `Max HP`;
- `Max Stam`;
- empty Mana trailing label;
- numeric survival row heights (`$rowHeights=@(22)` / `$rowHeights+=20`);
- recovery NumericUpDown controls;
- restored Zero Spell Cost styling;
- Enable-All gating.

Still incomplete:
- survival state initialization from `$status`;
- Auto Loot `IsAutoLootActive` fallback;
- qualified/unavailable badge styling parity;
- alternating survival row colors;
- unsupported ATTR/SCALING button style parity;
- 18 Player parity assertions;
- final regression/G4A rerun.

## Next safer method

Use the AST only to identify the unique survival loop. Then take `$loop.Extent.Text` itself as the exact dynamic source token and locate that token uniquely in the full source with ordinal `IndexOf`/`LastIndexOf`.

This avoids both fragile hard-coded loop text and reliance on AST StartOffset/EndOffset splicing.

No gameplay/runtime proof is established.

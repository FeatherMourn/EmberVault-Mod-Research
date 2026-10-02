# Localization tag-only live smoke test — 2026-09-27

## Scope

Validate the safe default localization probe on EML/game build `1076226` with
the stable Mod Hub module enabled. The probe intentionally skips localization
collection mutation.

## Session

- Session boundary: `research/probe_sessions/localization_tag_only_1076226_session.json`
- Probe: `research/probes/localization_tag_only_1076226_v2`
- Live log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`
- Boundary report: `research/localization_boundary_reports/tag_only_live_20260927.json`

## Observed result

The fresh session emitted, in order:

- `[CC-LOCALIZATION] TAG|ok=true|...`
- `[CC-LOCALIZATION] COLLECTION|skipped=safe_default_requires_explicit_opt_in`
- `[CC-LOCALIZATION] WARNING|UI_consumption_requires_controlled_validation`

The game remained running during observation. No panic or loader error was
observed. The report remains `review_required` because this probe does not test
game-facing UI consumption.

## Recovery

- The game process was closed after observation.
- Only the owned research probe was removed.
- Final live preflight: one stable module, zero research-only modules, zero
  unclassified modules, isolation ready.

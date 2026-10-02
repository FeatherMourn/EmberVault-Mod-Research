# Combined localized bed live smoke — 2026-09-27

- Build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`
- Probe: `combined_localized_bed_probe_1076226`
- Fresh session timestamp: `2026-09-27T22:57:19Z`
- `LOCALIZATION_TAG|ok=true`
- `LOCALIZATION_COLLECTION|ok=true`
- Game process remained alive during the observation window.
- Stable `enshrouded_mod_hub` was restored after the run.
- Final live state: one stable module, zero research-only modules, zero
  unclassified modules.

This verifies same-build runtime registration of the new localization tag and
collection. It does not verify that the game UI consumed the new label; no
visual UI claim is made.

## Retry confirmation

A second isolated run at `2026-09-27T23:02:07Z` produced the same two successful
markers and again stopped before `REGISTERED|`, `CLONED_ITEM|`, or
`REGISTERED_RECIPE|`. The probe was then removed and the stable profile was
restored. This repeat result makes the current boundary reproducible rather
than attributable to the first run's observation window.

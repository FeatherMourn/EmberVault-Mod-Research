# FbUiBundle catalog-preview structure verdict — 2026-09-29

## Scope

The read-only `fb_ui_bundle_structure_probe_20260928` ran in a fresh EML session against game build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.

## Runtime evidence

- One `keen::FbUiBundle` resource was enumerated.
- The bundle exposed `icons`, `menu`, and `itemSlot` as Lua `userdata`.
- `menu.crafting`, `menu.crafting.recipes`, and `menu.crafting.recipes.trees` were also exposed as Lua `userdata`.
- The probe completed with the explicit read-only warning and no panic.
- The probe was removed after the session and the game was stopped.

## Verdict

**Partial / research-only.** A separate UI graph exists beyond `ItemInfo`, so the blank catalog tile may depend on `FbUiBundle` data. The current Lua reflection surface does not expose the userdata contents for safe inspection or mutation. The Control Center must not present UI-entry preview/icon editing as supported until a typed metadata or native API route is found and verified.

## Evidence files

- `R36_FbUiBundle_INSTALL.json`
- `R36_FbUiBundle_SESSION.json`
- `R36_FbUiBundle_LAUNCH.json`
- `R36_FbUiBundle_REMOVE.json`

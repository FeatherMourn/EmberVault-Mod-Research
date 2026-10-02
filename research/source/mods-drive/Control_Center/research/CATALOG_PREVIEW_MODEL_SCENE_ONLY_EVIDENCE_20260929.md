# Catalog preview model/scene-only probe — 2026-09-29

## Result

The isolated candidate launched in a fresh EML session on build
`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z` without a
panic. The clone began with both `iconModel` and `iconScene` cleared, and the
runtime log recorded successful clone discovery and registration.

The typed catalog-image assignment itself returned successfully, but the
candidate's post-state still reports `hasIconImage=true`; therefore this run
does not prove a true model/scene-only catalog rendering path. It proves only
that the runtime accepts the registration sequence without crashing.

## Cleanup

The game was stopped before cleanup. The research probe was removed successfully
and the stable live profile remained `enshrouded_mod_hub` plus `flight_mod`.

Runtime records:

- `research/probe_sessions/catalog_preview_model_scene_only_20260929_install.json`
- `research/probe_sessions/catalog_preview_model_scene_only_20260929_launch.json`
- `research/probe_sessions/catalog_preview_model_scene_only_20260929_remove.json`

## Classification

`research-only`: no panic and clone registration verified; a visible catalog tile,
item-info view, placed-object rendering, and save persistence remain unverified.

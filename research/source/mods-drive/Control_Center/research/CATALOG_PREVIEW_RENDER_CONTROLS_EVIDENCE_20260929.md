# Catalog preview render-control probe — 2026-09-29

## Result

The isolated candidate launched in a fresh EML session on build
`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z` without a
panic. With icon fallbacks cleared, the runtime accepted:

`CATALOG_RENDER_CONTROL|field=iconRenderGlobalScale|ok=true|error=|value=1.25`

Clone discovery and registration also succeeded. The post-state still reports
`hasIconImage=true`, so this is not proof of a model/scene-only rendering path
or of a visible scale change in the catalog.

## Cleanup

The game was stopped before cleanup. The probe was removed successfully. The
stable live profile remains `enshrouded_mod_hub` plus `flight_mod`.

Runtime records:

- `research/probe_sessions/catalog_preview_render_controls_20260929_install.json`
- `research/probe_sessions/catalog_preview_render_controls_20260929_launch.json`
- `research/probe_sessions/catalog_preview_render_controls_20260929_remove.json`

## Classification

`research-only`: typed render-scale assignment is runtime-accepted; catalog,
item-info, placement, and save-persistence visual evidence remain unverified.

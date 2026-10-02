# Catalog preview image-only probe — 2026-09-29

## Result

The isolated image-only candidate loaded in a fresh EML session on game build
`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z` without a
panic. The probe registered its cloned item and emitted:

- `CATALOG_PREVIEW|candidate=image_only_donor_preview|ok=true`
- `CATALOG_PREVIEW_AFTER|hasIconImage=true|modelPreserved=true|scenePreserved=true`
- `DISCOVERED_CLONE|true`

This proves the typed `iconImage` assignment and clone registration reached the
runtime API. It does **not** prove that the catalog tile or placed item visibly
renders the image; screenshots are still required before promotion.

## Cleanup

The game was stopped before cleanup. The research probe was removed successfully
and the stable live profile was restored to `enshrouded_mod_hub` and `flight_mod`.

Runtime records:

- `research/probe_sessions/catalog_preview_image_only_20260929_r2_install.json`
- `research/probe_sessions/catalog_preview_image_only_20260929_r2_launch.json`
- `research/probe_sessions/catalog_preview_image_only_20260929_r2_remove.json`

## Classification

`research-only`: runtime API boundary verified; catalog, item-info, placement,
and save-persistence visuals remain unverified.

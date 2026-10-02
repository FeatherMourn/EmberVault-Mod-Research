# Catalog preview exposure probe — 2026-09-29

## Result

The probe was generated with a verified `CATALOG_RENDER_CONTROL` insertion for
`overrideSceneExposure`, passed installer validation, and launched in a fresh
session. The runtime reached `CATALOG_PREVIEW_AFTER`, but no subsequent
`CATALOG_RENDER_CONTROL`, registration, or completion marker was emitted. The
session therefore stopped making progress immediately after the exposure-field
assignment block. No visible catalog result can be claimed.

This is classified as a runtime stall boundary, not a successful field
assignment. The absence of a panic marker means the evidence does not identify
whether the field is unsupported or the loader stopped while handling it.

## Cleanup

The game was stopped before cleanup and the research probe was removed
successfully. The stable profile remained unchanged.

Runtime records:

- `research/probe_sessions/catalog_preview_exposure_20260929_install.json`
- `research/probe_sessions/catalog_preview_exposure_20260929_launch.json`
- `research/probe_sessions/catalog_preview_exposure_20260929_remove.json`

## Classification

`research-only`: exposure assignment is not verified; the field remains
quarantined from stable workflows pending a smaller boundary probe or stronger
loader diagnostics.

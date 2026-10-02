# Material and texture assignment boundary — 2026-09-29

## Finding

The current build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z` exposes these visual fields on `keen::ItemInfo`:

- `iconImage`
- `iconModel`
- `iconScene`
- `iconRenderOffset`
- `iconRenderCookingScale`
- `iconRenderGlobalScale`
- `itemColorCombinationSetup`
- `materialInteraction`

There are no direct `material`, `texture`, or `color` fields on `ItemInfo`. Material and texture GUIDs are dependencies of the render-model graph, not direct item properties.

## Probe result

The material-substitution probe was safely installed in an isolated session with an available render-material dependency. It loaded but produced no material-assignment or registration marker. The probe was removed and the game was stopped. This is not evidence of a successful material change.

## Authoring rule

Control Center must not present direct material/texture/color assignment as a supported `ItemInfo` edit. Future visual-material work must operate on a verified `RenderModel`/`RenderMaterialResource` dependency graph, or remain explicitly research-only. Color-combination editing is a separate `itemColorCombinationSetup` investigation and must not be conflated with texture replacement.

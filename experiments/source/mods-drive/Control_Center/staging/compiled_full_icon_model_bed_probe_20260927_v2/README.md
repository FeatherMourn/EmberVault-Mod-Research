# Full Icon Model Bed Probe v2

Control Center content project: `full_icon_model_bed_probe_20260927_v2`  
Namespace: `control_center_visual_v1`

This project is generated for EML runtime registration. It is research-only by
default. Validate donor resources and the generated package before enabling it.

## Layout

- `mod.json` — module manifest and capabilities.
- `src/mod.lua` — runtime entry point.
- `src/kfc_content_registry.lua` — packaged reusable registration helper.
- `src/kfc_localization_registry.lua` — research-only binary localization registry helper.
- `src/localization_payload.lua` — deterministic custom localization payload scaffold.
- `content/content.json` — content entries to be added by the author.
- `assets/icons/` — validated PNG icons imported through Content Studio.
- `assets.json` — hashed asset inventory and reference metadata.

Use Content Studio's **Import Custom Icon** action (or
`ContentProjectGenerator.import_icon`) to add an icon safely. Packaging an icon
only proves that the project contains a valid, integrity-tracked PNG; assigning
it to a live `keen::ItemInfo.iconImage` and confirming visible rendering remains
build-specific research work and must be verified with an EML log plus fresh
in-game evidence.

The generator does not alter the vanilla game installation.
